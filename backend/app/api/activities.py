from datetime import date
import json
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.auth import get_current_user_sync
from app.core.database import get_db, engine
from app.models.models import Activity, ActivityParticipant, Prize, StepRecord, User, Department, Winner
from app.schemas.schemas import ActivityJoinResponse, ActivityListResponse, ActivityPrizeItem, ActivityResponse
from app.services.activity_awards import ensure_activity_prize_mappings

router = APIRouter(prefix="/activities", tags=["活动"])

_tables_ready = False
_defaults_ready = False

ACTIVITY_STATUS_TEXT = {
    "signup": "报名中",
    "active": "进行中",
    "ended": "已结束",
}

DEFAULT_ACTIVITIES = [
    {
        "id": "campus-spring-2026",
        "name": "春季步数接力挑战赛",
        "status": "active",
        "status_text": "进行中",
        "cover_tone": "green",
        "start_date": date(2026, 3, 1),
        "end_date": date(2026, 5, 31),
        "signup_start": date(2026, 3, 1),
        "signup_end": date(2026, 3, 15),
        "target_group": "全体本科生",
        "participants": 328,
        "max_participants": 500,
        "rules_short": "每日10000步 / 积分排名制",
        "reward_short": "前10名可领奖",
        "description": "加入全校运动热潮，用脚步迈向胜利。",
        "tags": ["校园活动", "高能挑战"],
        "rules": [
            "每日步数至少达到 10,000 步，至少坚持 20 天。",
            "积分排名前 10 名可获得专属奖品。",
            "每天通过首页同步微信运动步数，系统保留最新一次同步结果。"
        ],
        "prizes": [
            {"id": "p1", "rank": "第1名", "name": "校园咖啡季卡", "image": "/images/prizes/coffee-card.svg"},
            {"id": "p2", "rank": "第2-3名", "name": "校园书城50元券", "image": "/images/prizes/stationery.svg"},
            {"id": "p3", "rank": "第4-10名", "name": "定制运动水壶", "image": "/images/prizes/thermos.svg"}
        ],
    },
    {
        "id": "library-marathon-2026",
        "name": "图书馆马拉松周",
        "status": "signup",
        "status_text": "报名中",
        "cover_tone": "blue",
        "start_date": date(2026, 6, 1),
        "end_date": date(2026, 6, 30),
        "signup_start": date(2026, 5, 1),
        "signup_end": date(2026, 5, 31),
        "target_group": "全校师生",
        "participants": 890,
        "max_participants": 1000,
        "rules_short": "每日8000步 / 打卡满7天",
        "reward_short": "参与即有奖",
        "description": "从宿舍到图书馆，把学习路线变成健康路线。",
        "tags": ["全校活动", "打卡挑战"],
        "rules": [
            "每日步数至少达到 8,000 步。",
            "连续打卡满 7 天可获得完成奖励。",
            "积分前 20 名可获得文创奖品。"
        ],
        "prizes": [
            {"id": "p4", "rank": "前20名", "name": "博雅文具礼盒", "image": "/images/prizes/stationery.svg"},
            {"id": "p5", "rank": "完成任务", "name": "图书馆借阅积分", "image": "/images/prizes/medal.svg"}
        ],
    },
    {
        "id": "evening-walk-2026",
        "name": "晚霞健步赛",
        "status": "active",
        "status_text": "进行中",
        "cover_tone": "orange",
        "start_date": date(2026, 4, 10),
        "end_date": date(2026, 5, 31),
        "signup_start": date(2026, 4, 5),
        "signup_end": date(2026, 4, 10),
        "target_group": "全体学生",
        "participants": 2105,
        "max_participants": 3000,
        "rules_short": "每日6000步 / 每步得积分",
        "reward_short": "前30名可领奖",
        "description": "傍晚散步也能累计积分，轻量参与校园运动。",
        "tags": ["休闲活动", "全民健步"],
        "rules": [
            "每日步数至少达到 6,000 步。",
            "每 100 步计 1 积分。",
            "积分前 30 名可获得相应奖品。"
        ],
        "prizes": [
            {"id": "p6", "rank": "第1-10名", "name": "健身房月卡", "image": "/images/prizes/medal.svg"},
            {"id": "p7", "rank": "第11-30名", "name": "运动毛巾", "image": "/images/prizes/thermos.svg"}
        ],
    },
    {
        "id": "lab-health-2026",
        "name": "实验楼健康挑战",
        "status": "active",
        "status_text": "进行中",
        "cover_tone": "blue",
        "start_date": date(2026, 5, 1),
        "end_date": date(2026, 5, 31),
        "signup_start": date(2026, 4, 20),
        "signup_end": date(2026, 4, 30),
        "target_group": "理工类学院学生",
        "participants": 420,
        "max_participants": 800,
        "rules_short": "每日7000步 / 总步数排名",
        "reward_short": "前20名可领奖",
        "description": "围绕教学楼与实验楼路线开展健步挑战，鼓励课间主动运动。",
        "tags": ["学院活动", "健步挑战"],
        "rules": [
            "活动期间每日步数达到 7,000 步计为有效打卡。",
            "总步数排名前 20 名可获得活动奖品。",
            "仅已报名用户可参与排名和发布打卡动态。"
        ],
        "prizes": [
            {"id": "p10", "rank": "前10名", "name": "校园运动礼包", "image": "/images/prizes/medal.svg"},
            {"id": "p11", "rank": "第11-20名", "name": "定制运动水壶", "image": "/images/prizes/thermos.svg"}
        ],
    },
    {
        "id": "green-campus-2026",
        "name": "绿色校园健走季",
        "status": "active",
        "status_text": "进行中",
        "cover_tone": "green",
        "start_date": date(2026, 5, 5),
        "end_date": date(2026, 6, 5),
        "signup_start": date(2026, 4, 20),
        "signup_end": date(2026, 5, 4),
        "target_group": "全校学生",
        "participants": 760,
        "max_participants": 1200,
        "rules_short": "每日9000步 / 积分排名制",
        "reward_short": "前15名可领奖",
        "description": "以校园绿色路线为主题，鼓励学生在日常通勤中完成运动目标。",
        "tags": ["校园活动", "绿色健走"],
        "rules": [
            "每日步数达到 9,000 步可获得活动积分。",
            "活动按总积分排名，前 15 名可获得奖品。",
            "活动期间可在详情页同步步数并查看排名。"
        ],
        "prizes": [
            {"id": "p12", "rank": "第1名", "name": "校园咖啡季卡", "image": "/images/prizes/coffee-card.svg"},
            {"id": "p13", "rank": "第2-15名", "name": "运动文创套装", "image": "/images/prizes/stationery.svg"}
        ],
    },
    {
        "id": "winter-run-2026",
        "name": "冬季晨跑挑战赛",
        "status": "ended",
        "status_text": "已结束",
        "cover_tone": "gray",
        "start_date": date(2025, 12, 1),
        "end_date": date(2026, 1, 31),
        "signup_start": date(2025, 11, 25),
        "signup_end": date(2025, 11, 30),
        "target_group": "全体本科生",
        "participants": 560,
        "max_participants": 600,
        "rules_short": "每日8000步 / 积分排名制",
        "reward_short": "前15名可领奖",
        "description": "历史活动展示数据，活动已结束。",
        "tags": ["校园活动", "冬季挑战"],
        "rules": [
            "活动已结束，仅用于历史数据展示。",
            "获奖记录以我的奖品页面为准。"
        ],
        "prizes": [
            {"id": "p8", "rank": "第1-5名", "name": "校园咖啡季卡", "image": "/images/prizes/coffee-card.svg"},
            {"id": "p9", "rank": "第6-15名", "name": "定制保温杯", "image": "/images/prizes/thermos.svg"}
        ],
    },
]

DEFAULT_PARTICIPANTS = [
    ("campus-spring-2026", 1),
    ("campus-spring-2026", 2),
    ("campus-spring-2026", 3),
    ("campus-spring-2026", 7),
    ("evening-walk-2026", 1),
    ("evening-walk-2026", 6),
    ("evening-walk-2026", 7),
    ("lab-health-2026", 2),
    ("lab-health-2026", 4),
    ("green-campus-2026", 3),
    ("green-campus-2026", 5),
    ("winter-run-2026", 3),
    ("winter-run-2026", 7),
]


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
    _tables_ready = True


def ensure_default_activities(db: Session) -> None:
    global _defaults_ready
    if _defaults_ready:
        return

    for item in DEFAULT_ACTIVITIES:
        activity = db.query(Activity).filter(Activity.id == item["id"]).first()
        values = {
            "name": item["name"],
            "status": item["status"],
            "status_text": ACTIVITY_STATUS_TEXT.get(item["status"], item["status_text"]),
            "cover_tone": item["cover_tone"],
            "start_date": item["start_date"],
            "end_date": item["end_date"],
            "signup_start": item["signup_start"],
            "signup_end": item["signup_end"],
            "target_group": item["target_group"],
            "participants": item["participants"],
            "max_participants": item["max_participants"],
            "rules_short": item["rules_short"],
            "reward_short": item["reward_short"],
            "description": item["description"],
            "tags_json": dumps(item["tags"]),
            "rules_json": dumps(item["rules"]),
            "prizes_json": dumps(item["prizes"]),
        }
        if activity:
            for key, value in values.items():
                setattr(activity, key, value)
        else:
            activity = Activity(id=item["id"], **values)
            db.add(activity)
        ensure_activity_prize_mappings(db, activity)

    for activity_id, user_id in DEFAULT_PARTICIPANTS:
        exists = db.query(ActivityParticipant.id).filter(
            ActivityParticipant.activity_id == activity_id,
            ActivityParticipant.user_id == user_id
        ).first()
        if not exists:
            db.add(ActivityParticipant(activity_id=activity_id, user_id=user_id))

    db.commit()
    _defaults_ready = True


def format_date(value: date) -> str:
    return value.strftime("%Y.%m.%d")


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
        status=activity.status,
        statusText=activity.status_text,
        coverTone=activity.cover_tone,
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
        myFinalRank=winner_rank or (my_rank if activity.status == "ended" else None),
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
    ensure_default_activities(db)

    query = db.query(Activity)
    if status_filter == "signup":
        query = query.filter(Activity.status == "signup")
    elif status_filter == "active":
        query = query.filter(Activity.status == "active")
    elif status_filter == "ended":
        query = query.filter(Activity.status == "ended")
    keyword_text = keyword if isinstance(keyword, str) else ""
    if keyword_text.strip():
        query = query.filter(Activity.name.contains(keyword_text.strip()))

    activities = query.order_by(Activity.status.asc(), Activity.start_date.desc()).all()
    items = [serialize_activity(db, item, current_user.id) for item in activities]
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
    ensure_default_activities(db)
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
    ensure_default_activities(db)
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
    ensure_default_activities(db)
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="活动不存在")
    if activity.status != "signup":
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
