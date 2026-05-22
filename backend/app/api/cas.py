import base64
import random
import re
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urljoin, urlparse
from xml.etree import ElementTree

import httpx
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.api.auth import get_current_user_sync
from app.core.config import settings
from app.core.database import engine, get_db
from app.models.models import Department, User
from app.schemas.schemas import CasBindRequest, CasBindResponse, CasLoginRequest, CasLoginResponse, CasStatusResponse

router = APIRouter(prefix="/cas", tags=["CAS认证"])

_AES_CHARS = "ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678"
_bind_tokens: dict[str, dict] = {}
_cas_columns_ready = False


def ensure_cas_columns() -> None:
    global _cas_columns_ready
    if _cas_columns_ready:
        return

    inspector = inspect(engine)
    columns = {item["name"] for item in inspector.get_columns("users")}
    with engine.begin() as conn:
        if "employee_id" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN employee_id VARCHAR(50) NULL COMMENT '工号/学号(CAS)'"))
            conn.execute(text("CREATE UNIQUE INDEX idx_users_employee_id ON users (employee_id)"))
        if "cas_binded" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN cas_binded TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否已绑定CAS'"))
        if "edu_person_type" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN edu_person_type VARCHAR(20) NULL COMMENT '身份类型'"))
        if "daily_step_goal" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN daily_step_goal INT NULL COMMENT 'User daily step goal'"))
        if "daily_goal_reset_date" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN daily_goal_reset_date DATE NULL COMMENT 'Daily goal reset date'"))
    _cas_columns_ready = True


def _random_string(length: int) -> str:
    return "".join(random.choice(_AES_CHARS) for _ in range(length))


def _encrypt_password(password: str, salt: str) -> str:
    key = salt.encode("utf-8")
    if len(key) not in (16, 24, 32):
        key = (key + b"\x00" * 16)[:16]
    iv = _random_string(16).encode("utf-8")
    plaintext = (_random_string(64) + password).encode("utf-8")
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    padder = PKCS7(128).padder()
    padded = padder.update(plaintext) + padder.finalize()
    encryptor = cipher.encryptor()
    encrypted = encryptor.update(padded) + encryptor.finalize()
    return base64.b64encode(encrypted).decode("ascii")


def _field_value(html: str, name_or_id: str) -> str | None:
    patterns = [
        rf'name=["\']{re.escape(name_or_id)}["\'][^>]*value=["\']([^"\']+)["\']',
        rf'id=["\']{re.escape(name_or_id)}["\'][^>]*value=["\']([^"\']+)["\']',
        rf'value=["\']([^"\']+)["\'][^>]*(?:name|id)=["\']{re.escape(name_or_id)}["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, html, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def _extract_ticket(location: str) -> str | None:
    if not location:
        return None
    query = parse_qs(urlparse(location).query)
    values = query.get("ticket")
    return values[0] if values else None


def _server_url(path: str) -> str:
    base = settings.CAS_SERVER_URL.rstrip("/") + "/"
    return urljoin(base, path.lstrip("/"))


async def _cas_browser_login(username: str, password: str) -> str:
    login_url = _server_url("login")
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    async with httpx.AsyncClient(timeout=15, follow_redirects=False, headers=headers) as client:
        login_page = await client.get(login_url, params={"service": settings.CAS_SERVICE_URL})
        if login_page.status_code >= 400:
            raise HTTPException(status_code=502, detail="无法获取CAS登录页面")

        html = login_page.text
        execution = _field_value(html, "execution")
        salt = _field_value(html, "pwdEncryptSalt")
        if not execution or not salt:
            raise HTTPException(status_code=502, detail="无法解析CAS登录页面，请检查应用是否已注册")

        data = {
            "username": username,
            "password": _encrypt_password(password, salt),
            "execution": execution,
            "_eventId": "submit",
            "geolocation": "",
            "dllt": _field_value(html, "dllt") or "generalLogin",
            "cllt": _field_value(html, "cllt") or "userNameLogin",
            "rememberMe": "true",
        }
        response = await client.post(login_url, params={"service": settings.CAS_SERVICE_URL}, data=data)
        ticket = _extract_ticket(response.headers.get("location", ""))
        if ticket:
            return ticket
        if response.status_code in {401, 403} or "错误" in response.text or "失败" in response.text:
            raise HTTPException(status_code=401, detail="学号/工号或密码错误")
        raise HTTPException(status_code=401, detail="CAS登录失败，请检查账号密码")


def _parse_validation_response(text_value: str) -> dict:
    try:
        root = ElementTree.fromstring(text_value)
    except ElementTree.ParseError:
        return {}

    ns = {"cas": "http://www.yale.edu/tp/cas"}
    success = root.find(".//cas:authenticationSuccess", ns)
    if success is None:
        success = root.find(".//authenticationSuccess")
    if success is None:
        return {}

    user_node = success.find("cas:user", ns)
    if user_node is None:
        user_node = success.find("user")
    data = {"employee_id": user_node.text.strip() if user_node is not None and user_node.text else ""}
    attrs = success.find("cas:attributes", ns)
    if attrs is None:
        attrs = success.find("attributes")
    if attrs is not None:
        for child in list(attrs):
            key = child.tag.split("}", 1)[-1]
            data[key] = child.text.strip() if child.text else ""
    return data


async def _validate_ticket(ticket: str) -> dict:
    validate_url = _server_url("serviceValidate")
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(validate_url, params={"service": settings.CAS_SERVICE_URL, "ticket": ticket})
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail="CAS票据验证失败")
    data = _parse_validation_response(response.text)
    if not data.get("employee_id"):
        raise HTTPException(status_code=401, detail="CAS票据无效或已过期")
    return data


def _cas_attr(data: dict, *keys: str) -> str | None:
    for key in keys:
        value = data.get(key)
        if value:
            return str(value).strip()
    return None


def _get_or_create_department(db: Session, name: str | None) -> Department | None:
    if not name:
        return None
    department = db.query(Department).filter(Department.name == name).first()
    if department:
        return department
    department = Department(name=name)
    db.add(department)
    db.flush()
    return department


def _bind_cas_user(db: Session, current_user: User, attrs: dict) -> CasBindResponse:
    employee_id = _cas_attr(attrs, "employee_id", "uid", "user", "account", "employeeNumber")
    if not employee_id:
        raise HTTPException(status_code=422, detail="CAS未返回学号/工号")

    existing = db.query(User).filter(User.employee_id == employee_id, User.id != current_user.id).first()
    if existing:
        raise HTTPException(status_code=409, detail="该学号/工号已被其他微信账号绑定")

    name = _cas_attr(attrs, "cn", "name", "displayName", "realName") or current_user.name
    department_name = _cas_attr(attrs, "department", "departmentName", "deptName", "orgName")
    edu_type = _cas_attr(attrs, "eduPersonType", "personType", "identityType", "userType")
    department = _get_or_create_department(db, department_name)

    current_user.name = name
    current_user.employee_id = employee_id
    current_user.cas_binded = True
    current_user.edu_person_type = edu_type
    if department:
        current_user.department_id = department.id
    db.commit()
    db.refresh(current_user)

    return CasBindResponse(
        success=True,
        name=current_user.name,
        employee_id=current_user.employee_id,
        department_name=department.name if department else None,
        edu_person_type=current_user.edu_person_type,
    )


def _clean_expired_tokens() -> None:
    now = datetime.now()
    expired = [key for key, value in _bind_tokens.items() if value["expires_at"] <= now]
    for key in expired:
        _bind_tokens.pop(key, None)


@router.post("/login", response_model=CasLoginResponse)
async def cas_login(
    payload: CasLoginRequest,
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    get_current_user_sync(authorization, db)
    ensure_cas_columns()
    username = payload.username.strip()
    password = payload.password
    if not username or not password:
        raise HTTPException(status_code=422, detail="请填写学号/工号和密码")

    ticket = await _cas_browser_login(username, password)
    _clean_expired_tokens()
    bind_token = _random_string(40)
    _bind_tokens[bind_token] = {
        "ticket": ticket,
        "expires_at": datetime.now() + timedelta(seconds=settings.CAS_TOKEN_EXPIRE_SECONDS),
    }
    return CasLoginResponse(bind_token=bind_token, expires_in=settings.CAS_TOKEN_EXPIRE_SECONDS)


@router.post("/bind", response_model=CasBindResponse)
async def cas_bind(
    payload: CasBindRequest,
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    current_user = get_current_user_sync(authorization, db)
    ensure_cas_columns()
    _clean_expired_tokens()
    token_data = _bind_tokens.pop(payload.bind_token, None)
    if not token_data:
        raise HTTPException(status_code=401, detail="绑定令牌无效或已过期")
    attrs = await _validate_ticket(token_data["ticket"])
    return _bind_cas_user(db, current_user, attrs)


@router.get("/status", response_model=CasStatusResponse)
async def cas_status(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    current_user = get_current_user_sync(authorization, db)
    ensure_cas_columns()
    department = db.query(Department).filter(Department.id == current_user.department_id).first() if current_user.department_id else None
    return CasStatusResponse(
        cas_binded=bool(current_user.cas_binded),
        employee_id=current_user.employee_id,
        name=current_user.name,
        department_name=department.name if department else None,
        edu_person_type=current_user.edu_person_type,
    )


@router.get("/callback")
async def cas_callback(ticket: str | None = None):
    return {"ticket": ticket, "message": "CAS callback endpoint is available"}
