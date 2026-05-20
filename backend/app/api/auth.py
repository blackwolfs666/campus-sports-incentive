from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from sqlalchemy import func, inspect, text
from typing import Optional
import httpx
from datetime import datetime, date, timedelta

from app.core.database import engine, get_db
from app.core.config import settings
from app.core.security import create_access_token, decode_access_token
from app.models.models import User, Department, StepRecord, Setting
from app.schemas.schemas import (
    WechatLoginRequest, WechatLoginResponse, UserResponse, 
    UserUpdate, MessageResponse
)

router = APIRouter(prefix="/auth", tags=["认证"])

_user_cas_columns_ready = False


def ensure_user_cas_columns() -> None:
    global _user_cas_columns_ready
    if _user_cas_columns_ready:
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
    _user_cas_columns_ready = True


def get_current_user_sync(
    authorization: str = None,
    db: Session = Depends(get_db)
) -> User:
    """同步版本的用户认证依赖"""
    ensure_user_cas_columns()
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌"
        )
    
    # 提取Bearer token
    if authorization.startswith("Bearer "):
        token = authorization[7:]
    else:
        token = authorization
    
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌内容"
        )
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )
    
    return user


async def get_wechat_session_key(code: str) -> dict:
    """通过微信code获取openid和session_key"""
    if not settings.WECHAT_APPID or not settings.WECHAT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="微信登录配置缺失"
        )

    url = "https://api.weixin.qq.com/sns/jscode2session"
    params = {
        "appid": settings.WECHAT_APPID,
        "secret": settings.WECHAT_SECRET,
        "js_code": code,
        "grant_type": "authorization_code"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        data = response.json()
    
    if "errcode" in data and data["errcode"] != 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"微信登录失败: {data.get('errmsg', '未知错误')}"
        )
    
    return data


@router.post("/login", response_model=WechatLoginResponse)
async def wechat_login(request: WechatLoginRequest, db: Session = Depends(get_db)):
    """微信登录"""
    ensure_user_cas_columns()
    # 获取微信用户信息
    wechat_data = await get_wechat_session_key(request.code)
    openid = wechat_data.get("openid")
    
    if not openid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="获取微信用户信息失败"
        )
    
    # 查找或创建用户
    user = db.query(User).filter(User.openid == openid).first()
    is_new_user = False
    
    if not user:
        # 创建新用户
        user = User(
            openid=openid,
            name="新用户",
            union_id=wechat_data.get("unionid")
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        is_new_user = True
    elif wechat_data.get("unionid") and user.union_id != wechat_data["unionid"]:
        user.union_id = wechat_data["unionid"]
        db.commit()
        db.refresh(user)
    
    # 生成token
    token = create_access_token({"sub": str(user.id), "openid": user.openid})
    
    return WechatLoginResponse(
        token=token,
        user=UserResponse.model_validate(user),
        is_new_user=is_new_user,
        needs_binding=not bool(user.cas_binded)
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """获取当前用户信息"""
    current_user = get_current_user_sync(authorization, db)
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """更新当前用户信息"""
    current_user = get_current_user_sync(authorization, db)
    update_data = user_update.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(current_user, key, value)
    
    db.commit()
    db.refresh(current_user)
    
    return UserResponse.model_validate(current_user)
