from datetime import date, datetime, time
import json
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.auth import get_current_user_sync
from app.core.database import get_db, engine
from app.models.models import Activity, ActivityParticipant, ActivityPrize, Prize, StepRecord, User, Department, Winner
from app.schemas.schemas import ActivityJoinResponse, ActivityListResponse, ActivityPrizeItem, ActivityResponse
from app.services.activity_awards import ensure_activity_prize_mappings

router = APIRouter(prefix="/activities", tags=["活动"])

_tables_ready = False

ACTIVITY_STATUS_TEXT = {
    "signup": "报名中",
    "active": "进行中",
    "ended": "已结束",
}



def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def loads(raw: str | None, fallback):
    if not raw:
        return fallback
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return fallback
    return value if isinstance(value, type(fallback)) else fallback


def ensure_activity_tables() -> None:
    global _tables_ready
    if _tables_ready:
        return
    Activity.__table__.create(bind=engine, checkfirst=True)
    ActivityParticipant.__table__.create(bind=engine, checkfirst=True)
    Prize.__table__.create(bind=engine, checkfirst=True)
    ActivityPrize.__table__.create(bind=engine, checkfirst=True)
    _tables_ready = True



def format_date(value: date) -> str:
    return value.strftime("%Y.%m.%d")


def as_datetime(value, end_of_day: bool = False) -> datetime:
    if isinstance(value, datetime):
        return value
    boundary = time.max if end_of_day else time.min
    return datetime.combine(value, boundary)


def current_activity_status(activity: Activity) -> tuple[str, str]:
    now = datetime.now()
    activity_start = as_datetime(activity.start_date)
    activity_end = as_datetime(activity.end_date, end_of_day=True)

    if activity_start <= now <= activity_end:
        key = "active"
    elif now > activity_end:
        key = "ended"
    else:
        key = "signup"
    return key, ACTIVITY_STATUS_TEXT[key]


def get_activity_steps(db: Session, activity: Activity, user_id: int) -> int:
    return int(db.query(func.sum(StepRecord.steps)).filter(
        StepRecord.user_id == user_id,
        StepRecord.record_date >= activity.start_date,
        StepRecord.record_date <= activity.end_date
    ).scalar() or 0)


def get_activity_rank(db: Session, activity: Activity, user_id: int, my_steps: int) -> Optional[int]:
    participant_user_ids = select(ActivityParticipant.user_id).where(
        ActivityParticipant.activity_id == activity.id
    )
    totals = db.query(
        StepRecord.user_id.label("user_id"),
        func.sum(StepRecord.steps).label("total_steps")
    ).filter(
        StepRecord.record_date >= activity.start_date,
        StepRecord.record_date <= activity.end_date,
        StepRecord.user_id.in_(participant_user_ids)
    ).group_by(StepRecord.user_id).subquery()
    better_count = db.query(func.count()).select_from(totals).filter(
        totals.c.total_steps > my_steps
    ).scalar() or 0
    participant_exists = db.query(ActivityParticipant.id).filter(
        ActivityParticipant.activity_id == activity.id,
        ActivityParticipant.user_id == user_id
    ).first()
    return int(better_count) + 1 if participant_exists else None


def get_activity_first_steps(db: Session, activity: Activity) -> int:
    participant_user_ids = select(ActivityParticipant.user_id).where(
        ActivityParticipant.activity_id == activity.id
    )
    totals = db.query(
        func.sum(StepRecord.steps).label("total_steps")
    ).filter(
        StepRecord.record_date >= activity.start_date,
        StepRecord.record_date <= activity.end_date,
        StepRecord.user_id.in_(participant_user_ids)
    ).group_by(StepRecord.user_id).subquery()
    return int(db.query(func.max(totals.c.total_steps)).scalar() or 0)


def serialize_activity(db: Session, activity: Activity, current_user_id: int) -> ActivityResponse:
    status_key, status_text = current_activity_status(activity)
    is_registered = db.query(ActivityParticipant.id).filter(
        ActivityParticipant.activity_id == activity.id,
        ActivityParticipant.user_id == current_user_id
    ).first() is not None
    participant_count = db.query(func.count(ActivityParticipant.id)).filter(
        ActivityParticipant.activity_id == activity.id
    ).scalar() or 0
    my_steps = get_activity_steps(db, activity, current_user_id) if is_registered else 0
    my_points = my_steps // 100
    my_rank = get_activity_rank(db, activity, current_user_id, my_steps) if is_registered else None
    first_steps = get_activity_first_steps(db, activity) if is_registered else 0
    first_points = first_steps // 100
    first_gap = max(first_points - my_points, 0) if is_registered else None
    prize_configs = ensure_activity_prize_mappings(db, activity, persist=True)
    winner = db.query(Winner, Prize.name.label("prize_name")).join(
        Prize, Winner.prize_id == Prize.id
    ).filter(
        Winner.activity_id == activity.id,
        Winner.user_id == current_user_id
    ).order_by(Winner.rank.asc(), Winner.id.asc()).first()
    winner_rank = winner.Winner.rank if winner else None
    winner_name = winner.prize_name if winner else None

    return ActivityResponse(
        id=activity.id,
        name=activity.name,
        status=status_key,
        statusText=status_text,
        coverTone=activity.cover_tone,
        posterUrl=activity.poster_url or "",
        startDate=format_date(activity.start_date),
        endDate=format_date(activity.end_date),
        signupStart=format_date(activity.signup_start),
        signupEnd=format_date(activity.signup_end),
        targetGroup=activity.target_group,
        participants=max(activity.participants or 0, int(participant_count)),
        maxParticipants=activity.max_participants,
        isRegistered=is_registered,
        rulesShort=activity.rules_short,
        rewardShort=activity.reward_short,
        description=activity.description or "",
        tags=loads(activity.tags_json, []),
        rules=loads(activity.rules_json, []),
        prizes=[ActivityPrizeItem(**item) for item in prize_configs],
        totalSteps=my_steps,
        myPoints=my_points,
        myRank=my_rank,
        topTenGap=first_gap,
        myFinalRank=winner_rank or (my_rank if status_key == "ended" else None),
        hadPrize=bool(winner),
        wonPrizeName=winner_name,
    )


@router.get("", response_model=ActivityListResponse)
async def list_activities(
    status_filter: Optional[str] = Query(None, alias="status"),
    join_filter: str = Query("all"),
    keyword: str = Query(""),
    db: Session = Depends(get_db),
    authorization: str = Header(None),
):
    current_user = get_current_user_sync(authorization, db)
    ensure_activity_tables()

    query = db.query(Activity)
    keyword_text = keyword if isinstance(keyword, str) else ""
    if keyword_text.strip():
        query = query.filter(Activity.name.contains(keyword_text.strip()))

    activities = query.order_by(Activity.status.asc(), Activity.start_date.desc()).all()
    items = [serialize_activity(db, item, current_user.id) for item in activities]
    if status_filter in {"signup", "active", "ended"}:
        items = [item for item in items if item.status == status_filter]
    if join_filter == "joined":
        items = [item for item in items if item.isRegistered]
    elif join_filter == "notJoined":
        items = [item for item in items if not item.isRegistered]

    return ActivityListResponse(items=items, total=len(items))


@router.get("/my", response_model=ActivityListResponse)
async def list_my_activities(
    db: Session = Depends(get_db),
    authorization: str = Header(None),
):
    current_user = get_current_user_sync(authorization, db)
    ensure_activity_tables()
    activity_ids = [
        row.activity_id
        for row in db.query(ActivityParticipant.activity_id).filter(
            ActivityParticipant.user_id == current_user.id
        ).all()
    ]
    activities = db.query(Activity).filter(Activity.id.in_(activity_ids)).order_by(Activity.start_date.desc()).all() if activity_ids else []
    items = [serialize_activity(db, item, current_user.id) for item in activities]
    return ActivityListResponse(items=items, total=len(items))


@router.get("/{activity_id}", response_model=ActivityResponse)
async def get_activity(
    activity_id: str,
    db: Session = Depends(get_db),
    authorization: str = Header(None),
):
    current_user = get_current_user_sync(authorization, db)
    ensure_activity_tables()
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="活动不存在")
    return serialize_activity(db, activity, current_user.id)


@router.post("/{activity_id}/join", response_model=ActivityJoinResponse)
async def join_activity(
    activity_id: str,
    db: Session = Depends(get_db),
    authorization: str = Header(None),
):
    current_user = get_current_user_sync(authorization, db)
    ensure_activity_tables()
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="活动不存在")
    status_key, _ = current_activity_status(activity)
    if status_key != "signup":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="只有报名中的活动可以报名")

    exists = db.query(ActivityParticipant.id).filter(
        ActivityParticipant.activity_id == activity_id,
        ActivityParticipant.user_id == current_user.id
    ).first()
    if not exists:
        db.add(ActivityParticipant(activity_id=activity_id, user_id=current_user.id))
        db.commit()

    return ActivityJoinResponse(
        success=True,
        activity=serialize_activity(db, activity, current_user.id)
    )
