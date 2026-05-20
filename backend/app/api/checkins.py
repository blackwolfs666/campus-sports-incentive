from datetime import date, datetime
import json
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Header, HTTPException, Query, UploadFile, status
from sqlalchemy import desc, inspect, text
from sqlalchemy.orm import Session

from app.api.auth import get_current_user_sync
from app.core.database import get_db, engine
from app.models.models import CheckinLike, CheckinPost, Department, StepRecord, User
from app.schemas.schemas import CheckinCheerResponse, CheckinCreate, CheckinItem, CheckinListResponse

router = APIRouter(prefix="/checkins", tags=["打卡动态"])
UPLOAD_DIR = Path(__file__).resolve().parents[2] / "static" / "uploads" / "checkins"

_tables_ready = False


def ensure_checkin_tables() -> None:
    global _tables_ready
    if _tables_ready:
        return
    # The original local project does not use Alembic. Create only the new
    # check-in tables lazily so the backend can still start before MySQL is up.
    CheckinPost.__table__.create(bind=engine, checkfirst=True)
    CheckinLike.__table__.create(bind=engine, checkfirst=True)
    inspector = inspect(engine)
    indexes = {item["name"] for item in inspector.get_indexes("checkin_posts")}
    if "uk_checkin_activity_user_date" in indexes:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE checkin_posts DROP INDEX uk_checkin_activity_user_date"))
    _tables_ready = True


def ensure_upload_dir() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def parse_image_urls(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item]


def serialize_post(row, current_user_id: int, cheered_ids: set[int]) -> CheckinItem:
    post = row.CheckinPost
    return CheckinItem(
        id=post.id,
        activity_id=post.activity_id,
        user_id=post.user_id,
        user_name=row.user_name or "用户",
        user_avatar=row.user_avatar,
        department_name=row.department_name,
        content=post.content or "",
        image_urls=parse_image_urls(post.image_urls),
        steps=post.steps,
        streak_days=post.streak_days,
        record_date=post.record_date,
        cheer_count=post.cheer_count or 0,
        has_cheered=post.id in cheered_ids,
        is_mine=post.user_id == current_user_id,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


@router.get("", response_model=CheckinListResponse)
async def list_checkins(
    activity_id: str = Query(..., min_length=1, max_length=100),
    scope: str = Query("all", pattern="^(all|mine)$"),
    db: Session = Depends(get_db),
    authorization: str = Header(None),
):
    current_user = get_current_user_sync(authorization, db)
    ensure_checkin_tables()

    query = db.query(
        CheckinPost,
        User.name.label("user_name"),
        User.avatar.label("user_avatar"),
        Department.name.label("department_name"),
    ).join(
        User, CheckinPost.user_id == User.id
    ).join(
        Department, User.department_id == Department.id, isouter=True
    ).filter(
        CheckinPost.activity_id == activity_id,
        CheckinPost.is_visible == True,
    )

    if scope == "mine":
        query = query.filter(CheckinPost.user_id == current_user.id)

    rows = query.order_by(desc(CheckinPost.created_at)).all()
    post_ids = [row.CheckinPost.id for row in rows]
    liked_rows = []
    if post_ids:
        liked_rows = db.query(CheckinLike.post_id).filter(
            CheckinLike.user_id == current_user.id,
            CheckinLike.post_id.in_(post_ids),
        ).all()
    cheered_ids = {row.post_id for row in liked_rows}

    items = [serialize_post(row, current_user.id, cheered_ids) for row in rows]
    return CheckinListResponse(items=items, total=len(items))


@router.post("", response_model=CheckinItem)
async def create_checkin(
    payload: CheckinCreate,
    db: Session = Depends(get_db),
    authorization: str = Header(None),
):
    current_user = get_current_user_sync(authorization, db)
    ensure_checkin_tables()
    today = date.today()

    today_record = db.query(StepRecord).filter(
        StepRecord.user_id == current_user.id,
        StepRecord.record_date == today,
    ).first()
    if not today_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="今天还没有同步步数，请先同步今日步数后再发布动态",
        )

    content = (payload.content or "").strip()
    image_urls = [url for url in payload.image_urls if url][:9]
    if not content and not image_urls:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="请填写想说的话或选择展示风采图片",
        )

    post = CheckinPost(
        activity_id=payload.activity_id,
        user_id=current_user.id,
        content=content,
        image_urls=json.dumps(image_urls, ensure_ascii=False),
        steps=today_record.steps,
        streak_days=current_user.streak_days or 0,
        record_date=today,
        cheer_count=0,
        is_visible=True,
    )
    db.add(post)

    db.commit()
    db.refresh(post)

    row = db.query(
        CheckinPost,
        User.name.label("user_name"),
        User.avatar.label("user_avatar"),
        Department.name.label("department_name"),
    ).join(
        User, CheckinPost.user_id == User.id
    ).join(
        Department, User.department_id == Department.id, isouter=True
    ).filter(
        CheckinPost.id == post.id
    ).first()

    return serialize_post(row, current_user.id, set())


@router.post("/upload")
async def upload_checkin_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    authorization: str = Header(None),
):
    get_current_user_sync(authorization, db)
    ensure_upload_dir()

    content_type = file.content_type or ""
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="只能上传图片")

    ext = Path(file.filename or "").suffix.lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
        ext = ".jpg"

    filename = f"{uuid4().hex}{ext}"
    target = UPLOAD_DIR / filename
    data = await file.read()
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="图片不能超过 5MB")

    target.write_bytes(data)
    return {"url": f"/static/uploads/checkins/{filename}"}


@router.post("/{post_id}/cheer", response_model=CheckinCheerResponse)
async def cheer_checkin(
    post_id: int,
    db: Session = Depends(get_db),
    authorization: str = Header(None),
):
    current_user = get_current_user_sync(authorization, db)
    ensure_checkin_tables()
    post = db.query(CheckinPost).filter(
        CheckinPost.id == post_id,
        CheckinPost.is_visible == True,
    ).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="动态不存在")

    existing = db.query(CheckinLike).filter(
        CheckinLike.post_id == post_id,
        CheckinLike.user_id == current_user.id,
    ).first()

    if existing:
        db.delete(existing)
        post.cheer_count = max((post.cheer_count or 0) - 1, 0)
        has_cheered = False
    else:
        db.add(CheckinLike(post_id=post_id, user_id=current_user.id))
        post.cheer_count = (post.cheer_count or 0) + 1
        has_cheered = True

    db.commit()
    return CheckinCheerResponse(
        success=True,
        cheer_count=post.cheer_count or 0,
        has_cheered=has_cheered,
    )
