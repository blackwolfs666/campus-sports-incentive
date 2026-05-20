from datetime import date, datetime, timedelta
import json
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile, status
from sqlalchemy import func, inspect, text
from sqlalchemy.orm import Session

from app.api.auth import get_current_user_sync
from app.core.database import engine, get_db
from app.models.models import Activity, ActivityAdmin, ActivityParticipant, ActivityPrize, CheckinPost, Department, Prize, StepRecord, User
from app.schemas.schemas import (
    ActivityAdminAddRequest,
    ActivityAdminItem,
    ActivityAdminListResponse,
    AdminActivityCreate,
    AdminActivityItem,
    AdminActivityListResponse,
    AdminActivityUpdate,
    AdminDashboardResponse,
    AdminUserItem,
)
from app.services.activity_awards import ensure_activity_prize_mappings, ensure_activity_winners

router = APIRouter(prefix="/admin", tags=["活动后台"])
UPLOAD_DIR = Path(__file__).resolve().parents[2] / "static" / "uploads" / "admin"

_tables_ready = False

STATUS_LABELS = {
    "pre_signup": "未开始报名",
    "signup": "报名中",
    "signup_closed": "报名已结束，活动未开始",
    "active": "进行中",
    "ended": "已结束",
}

SCORE_RULE_LABELS = {
    "daily_step_target": "单日步数目标",
    "base_score": "达标基础积分",
    "extra_step_score": "超额步数加分",
    "max_daily_score": "每日积分上限",
}

AWARD_RULE_LABELS = {
    "participation": "参与就有奖",
    "target_days": "累计达成目标",
    "score_rank": "积分排行榜",
    "steps_rank": "步数总榜",
    "streak_days": "连续达成目标",
    "checkin_post_days": "累计发布打卡动态",
}


def ensure_admin_tables() -> None:
    global _tables_ready
    if _tables_ready:
        return

    Activity.__table__.create(bind=engine, checkfirst=True)
    ActivityAdmin.__table__.create(bind=engine, checkfirst=True)
    Prize.__table__.create(bind=engine, checkfirst=True)
    ActivityPrize.__table__.create(bind=engine, checkfirst=True)

    inspector = inspect(engine)
    columns = {item["name"] for item in inspector.get_columns("activities")}
    additions = {
        "poster_url": "ALTER TABLE activities ADD COLUMN poster_url VARCHAR(500) NULL COMMENT '活动海报'",
        "scope_text": "ALTER TABLE activities ADD COLUMN scope_text VARCHAR(200) NULL COMMENT '活动范围'",
        "score_rule_json": "ALTER TABLE activities ADD COLUMN score_rule_json TEXT NULL COMMENT '积分规则JSON'",
        "award_rules_json": "ALTER TABLE activities ADD COLUMN award_rules_json TEXT NULL COMMENT '获奖规则JSON'",
        "checkin_post_visible": "ALTER TABLE activities ADD COLUMN checkin_post_visible TINYINT(1) NOT NULL DEFAULT 1 COMMENT '打卡动态是否可见'",
        "created_by": "ALTER TABLE activities ADD COLUMN created_by BIGINT NULL COMMENT '创建人用户ID'",
    }
    with engine.begin() as conn:
        for column, sql in additions.items():
            if column not in columns:
                conn.execute(text(sql))
        if {"signup_start", "signup_end", "start_date", "end_date"}.issubset(columns):
            conn.execute(text("ALTER TABLE activities MODIFY signup_start DATETIME NOT NULL"))
            conn.execute(text("ALTER TABLE activities MODIFY signup_end DATETIME NOT NULL"))
            conn.execute(text("ALTER TABLE activities MODIFY start_date DATETIME NOT NULL"))
            conn.execute(text("ALTER TABLE activities MODIFY end_date DATETIME NOT NULL"))

    activity_prize_columns = {item["name"] for item in inspector.get_columns("activity_prizes")}
    if "image_url" not in activity_prize_columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE activity_prizes ADD COLUMN image_url VARCHAR(500) NULL COMMENT '活动奖品展示图片'"))

    _tables_ready = True


def ensure_upload_dir() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def loads(raw, fallback):
    if not raw:
        return fallback
    try:
        value = json.loads(raw)
        return value if value is not None else fallback
    except json.JSONDecodeError:
        return fallback


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def normalize_stored_image_url(value: str | None) -> str:
    text_value = str(value or "").strip()
    marker = "/static/uploads/"
    index = text_value.find(marker)
    return text_value[index:] if index >= 0 else text_value


def format_user_code(user_id: int) -> str:
    return f"U{int(user_id):07d}"


def parse_user_code(value: str) -> int | None:
    text = str(value or "").strip().upper()
    if text.startswith("U"):
        text = text[1:]
    if not text.isdigit():
        return None
    return int(text)


def as_date(value) -> date:
    if isinstance(value, datetime):
        return value.date()
    return value


def activity_status(activity: Activity) -> tuple[str, str]:
    now = datetime.now()
    if now < activity.signup_start:
        key = "pre_signup"
    elif activity.signup_start <= now <= activity.signup_end:
        key = "signup"
    elif activity.signup_end < now < activity.start_date:
        key = "signup_closed"
    elif activity.start_date <= now <= activity.end_date:
        key = "active"
    else:
        key = "ended"
    return key, STATUS_LABELS[key]


def legacy_status(status_key: str) -> tuple[str, str]:
    if status_key == "active":
        return "active", "进行中"
    if status_key == "ended":
        return "ended", "已结束"
    if status_key == "signup":
        return "signup", "报名中"
    return "signup", STATUS_LABELS[status_key]


def participant_count(db: Session, activity_id: str) -> int:
    return int(db.query(func.count(ActivityParticipant.id)).filter(
        ActivityParticipant.activity_id == activity_id
    ).scalar() or 0)


def managed_activity_query(db: Session, user_id: int):
    return db.query(Activity, ActivityAdmin.role).join(
        ActivityAdmin, ActivityAdmin.activity_id == Activity.id
    ).filter(ActivityAdmin.user_id == user_id)


def bootstrap_local_owners(db: Session, user_id: int) -> None:
    # Local development data was created before activity_admins existed.
    # If there is no admin record at all, make the current user owner of
    # existing activities so the mobile backend can be opened immediately.
    admin_count = db.query(func.count(ActivityAdmin.id)).scalar() or 0
    if admin_count:
        return
    for activity in db.query(Activity).all():
        activity.created_by = user_id
        db.add(ActivityAdmin(activity_id=activity.id, user_id=user_id, role="owner"))
    db.commit()


def get_admin_role(db: Session, activity_id: str, user_id: int) -> str | None:
    row = db.query(ActivityAdmin).filter(
        ActivityAdmin.activity_id == activity_id,
        ActivityAdmin.user_id == user_id,
    ).first()
    return row.role if row else None


def require_admin(db: Session, activity_id: str, user_id: int) -> str:
    role = get_admin_role(db, activity_id, user_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无活动管理权限")
    return role


def require_owner(db: Session, activity_id: str, user_id: int) -> None:
    if get_admin_role(db, activity_id, user_id) != "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅根管理员可以操作")


def require_not_ended(activity: Activity) -> None:
    status_key, _ = activity_status(activity)
    if status_key == "ended":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="活动已结束，不能调整管理员")


def validate_dates(payload) -> None:
    if payload.registerStartTime >= payload.registerEndTime:
        raise HTTPException(status_code=422, detail="报名开始时间必须早于报名结束时间")
    if payload.activityStartTime < payload.registerEndTime:
        raise HTTPException(status_code=422, detail="活动开始时间不能早于报名结束时间")
    if payload.activityStartTime >= payload.activityEndTime:
        raise HTTPException(status_code=422, detail="活动开始时间必须早于活动结束时间")
    if payload.registerEndTime > payload.activityEndTime:
        raise HTTPException(status_code=422, detail="报名结束时间不能晚于活动结束时间")


def validate_rules(payload) -> None:
    max_participants = payload.maxParticipants
    if max_participants is not None and max_participants <= 0:
        raise HTTPException(status_code=422, detail="最大报名人数必须为大于 0 的整数")

    score_types = []
    for rule in payload.scoreRule:
        rule_type = rule.type
        if not rule_type or rule_type not in SCORE_RULE_LABELS:
            raise HTTPException(status_code=422, detail="请选择有效的积分规则类型")
        if rule_type in score_types:
            raise HTTPException(status_code=422, detail="不能重复配置同一种积分规则")
        score_types.append(rule_type)

        if rule_type in {"daily_step_target", "base_score", "max_daily_score"}:
            if rule.value is None or rule.value <= 0:
                raise HTTPException(status_code=422, detail=f"{SCORE_RULE_LABELS[rule_type]}必须大于 0")
        if rule_type == "extra_step_score":
            if rule.stepUnit is None or rule.stepUnit <= 0:
                raise HTTPException(status_code=422, detail="超额步数必须大于 0")
            if rule.score is None or rule.score <= 0:
                raise HTTPException(status_code=422, detail="额外积分必须大于 0")

    award_types = []
    for rule in payload.awardRules:
        if not rule.type or rule.type not in AWARD_RULE_LABELS:
            raise HTTPException(status_code=422, detail="请选择有效的获奖规则类型")
        if rule.type in award_types:
            raise HTTPException(status_code=422, detail="不能重复配置同一种获奖规则")
        award_types.append(rule.type)
        if rule.type != "participation" and (rule.value is None or rule.value <= 0):
            raise HTTPException(status_code=422, detail=f"{AWARD_RULE_LABELS[rule.type]}规则数值必须大于 0")
    for prize in payload.prizes:
        if prize.quantity is not None and prize.quantity <= 0:
            raise HTTPException(status_code=422, detail="奖品数量必须大于 0")


def normalize_score_rules(raw) -> list[dict]:
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict) and item.get("type")]
    if not isinstance(raw, dict):
        return []

    rules = []
    if raw.get("dailyStepTarget"):
        rules.append({
            "type": "daily_step_target",
            "label": SCORE_RULE_LABELS["daily_step_target"],
            "value": raw.get("dailyStepTarget"),
        })
    if raw.get("baseScore") is not None:
        rules.append({
            "type": "base_score",
            "label": SCORE_RULE_LABELS["base_score"],
            "value": raw.get("baseScore"),
        })
    if raw.get("extraStepUnit") and raw.get("extraScore") is not None:
        rules.append({
            "type": "extra_step_score",
            "label": SCORE_RULE_LABELS["extra_step_score"],
            "stepUnit": raw.get("extraStepUnit"),
            "score": raw.get("extraScore"),
        })
    if raw.get("maxDailyScore"):
        rules.append({
            "type": "max_daily_score",
            "label": SCORE_RULE_LABELS["max_daily_score"],
            "value": raw.get("maxDailyScore"),
        })
    return rules


def score_rule_text(score_rules) -> str:
    rules = normalize_score_rules(score_rules)
    if not rules:
        return "自定义积分规则"
    first = rules[0]
    label = first.get("label") or SCORE_RULE_LABELS.get(first.get("type"), "积分规则")
    if first.get("type") == "extra_step_score":
        return f"{label}：每 {first.get('stepUnit')} 步 +{first.get('score')} 分"
    return f"{label}：{first.get('value')}"


def normalize_award_rules(raw) -> list[dict]:
    if not isinstance(raw, list):
        return []
    rules = []
    used = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        rule_type = item.get("type")
        if rule_type not in AWARD_RULE_LABELS:
            # Legacy custom text is still shown, but not treated as an editable
            # predefined rule type in new submissions.
            rule_type = "custom"
        if rule_type in used and rule_type != "custom":
            continue
        used.add(rule_type)
        label = item.get("label") or AWARD_RULE_LABELS.get(rule_type, "自定义获奖规则")
        rules.append({
            "type": rule_type,
            "label": label,
            "desc": item.get("desc") or "",
            "value": item.get("value"),
        })
    return rules


def award_rule_text(rules: list[dict]) -> str:
    rules = normalize_award_rules(rules)
    if not rules:
        return "自定义获奖规则"
    first = rules[0]
    label = first.get("label") or first.get("type") or "获奖规则"
    value = first.get("value")
    return f"{label}{value or ''}"


def readable_rules(score_rules, award_rules: list[dict]) -> list[str]:
    rules = []
    for score in normalize_score_rules(score_rules):
        rule_type = score.get("type")
        if rule_type == "daily_step_target":
            rules.append(f"单日步数目标 {score.get('value')} 步。")
        elif rule_type == "base_score":
            rules.append(f"达到目标后获得基础积分 {score.get('value')} 分。")
        elif rule_type == "extra_step_score":
            rules.append(f"超过目标后，每多 {score.get('stepUnit')} 步额外增加 {score.get('score')} 分。")
        elif rule_type == "max_daily_score":
            rules.append(f"每日积分上限 {score.get('value')} 分。")
    for item in normalize_award_rules(award_rules):
        if item.get("label"):
            rules.append(item["label"])
    return rules or ["活动规则由组织方配置。"]


def serialize_prizes(prizes: list[dict]) -> list[dict]:
    result = []
    for index, prize in enumerate(prizes):
        name = (prize.get("name") or f"活动奖品{index + 1}").strip()
        item = {
            "id": prize.get("id") or f"p{index + 1}",
            "rank": prize.get("rank") or f"奖品{index + 1}",
            "name": name,
            "image": normalize_stored_image_url(prize.get("image")) or "/images/prizes/medal.svg",
            "quantity": prize.get("quantity"),
        }
        if prize.get("prize_id") is not None:
            item["prize_id"] = prize.get("prize_id")
        result.append(item)
    return result


def serialize_activity(db: Session, activity: Activity, role: str) -> AdminActivityItem:
    status_key, status_text = activity_status(activity)
    count = participant_count(db, activity.id)
    max_participants = activity.max_participants or None
    return AdminActivityItem(
        id=activity.id,
        name=activity.name,
        description=activity.description or "",
        posterUrl=activity.poster_url or "",
        status=status_key,
        statusText=status_text,
        registerStartTime=activity.signup_start,
        registerEndTime=activity.signup_end,
        activityStartTime=activity.start_date,
        activityEndTime=activity.end_date,
        scopeText=activity.scope_text or activity.target_group or "",
        currentParticipants=count,
        maxParticipants=max_participants,
        scoreRule=normalize_score_rules(loads(activity.score_rule_json, [])),
        awardRules=normalize_award_rules(loads(activity.award_rules_json, [])),
        prizes=ensure_activity_prize_mappings(db, activity, persist=True),
        checkinPostVisible=bool(activity.checkin_post_visible),
        myAdminRole=role,
        canManageAdmins=role == "owner",
        canEdit=role == "owner" and status_key != "ended",
        canGenerateWinners=role == "owner" and status_key == "ended",
        createdBy=activity.created_by,
    )


def apply_payload(activity: Activity, payload, include_dates: bool) -> None:
    score = [item.model_dump(exclude_none=True) for item in payload.scoreRule]
    award_rules = [item.model_dump(exclude_none=True) for item in payload.awardRules]
    prizes = serialize_prizes([item.model_dump(exclude_none=True) for item in payload.prizes])

    if payload.name is not None:
        activity.name = payload.name.strip()
    if payload.description is not None:
        activity.description = payload.description.strip()
    if payload.posterUrl is not None:
        activity.poster_url = normalize_stored_image_url(payload.posterUrl)
    if payload.scopeText is not None:
        activity.scope_text = payload.scopeText.strip()
        activity.target_group = payload.scopeText.strip() or "全体学生"
    if payload.maxParticipants is not None:
        activity.max_participants = payload.maxParticipants or 0
    elif hasattr(payload, "maxParticipants"):
        activity.max_participants = 0
    if payload.checkinPostVisible is not None:
        activity.checkin_post_visible = bool(payload.checkinPostVisible)

    if include_dates:
        activity.signup_start = payload.registerStartTime
        activity.signup_end = payload.registerEndTime
        activity.start_date = payload.activityStartTime
        activity.end_date = payload.activityEndTime

    activity.score_rule_json = dumps(score)
    activity.award_rules_json = dumps(award_rules)
    activity.prizes_json = dumps(prizes)
    activity.rules_short = score_rule_text(score)
    activity.reward_short = award_rule_text(award_rules)
    activity.rules_json = dumps(readable_rules(score, award_rules))
    status_key, status_text = activity_status(activity)
    activity.status, activity.status_text = legacy_status(status_key)


@router.get("/departments")
async def list_departments(db: Session = Depends(get_db), authorization: str = Header(None)):
    get_current_user_sync(authorization, db)
    rows = db.query(Department).order_by(Department.sort_order.asc(), Department.id.asc()).all()
    if not rows:
        return {
            "items": [
                {"id": 0, "name": "全校学生"},
                {"id": -1, "name": "计算机科学学院"},
                {"id": -2, "name": "软件学院"},
                {"id": -3, "name": "网络空间安全学院"},
            ]
        }
    return {"items": [{"id": row.id, "name": row.name} for row in rows]}


@router.post("/upload")
async def upload_admin_image(
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

    data = await file.read()
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="图片不能超过 5MB")

    filename = f"{uuid4().hex}{ext}"
    target = UPLOAD_DIR / filename
    target.write_bytes(data)
    return {"url": f"/static/uploads/admin/{filename}"}


@router.get("/dashboard", response_model=AdminDashboardResponse)
async def dashboard(db: Session = Depends(get_db), authorization: str = Header(None)):
    current_user = get_current_user_sync(authorization, db)
    ensure_admin_tables()
    bootstrap_local_owners(db, current_user.id)

    rows = managed_activity_query(db, current_user.id).all()
    activities = [row.Activity for row in rows]
    status_counts = {key: 0 for key in STATUS_LABELS}
    total_participants = 0
    total_checkins = 0
    total_steps = 0
    top = []
    for activity in activities:
        status_key, status_text = activity_status(activity)
        status_counts[status_key] += 1
        count = participant_count(db, activity.id)
        total_participants += count
        checkins = db.query(func.count(CheckinPost.id)).filter(CheckinPost.activity_id == activity.id).scalar() or 0
        steps = db.query(func.sum(StepRecord.steps)).filter(
            StepRecord.record_date >= as_date(activity.start_date),
            StepRecord.record_date <= as_date(activity.end_date),
        ).scalar() or 0
        total_checkins += int(checkins)
        total_steps += int(steps)
        top.append({
            "activityId": activity.id,
            "title": activity.name,
            "status": status_key,
            "statusText": status_text,
            "currentParticipants": count,
            "maxParticipants": activity.max_participants or None,
        })

    top.sort(key=lambda item: item["currentParticipants"], reverse=True)
    today = date.today()
    trend_days = [today - timedelta(days=offset) for offset in range(6, -1, -1)]

    return AdminDashboardResponse(
        summaryCards={
            "totalActivities": len(activities),
            "activeActivities": status_counts["active"],
            "totalParticipants": total_participants,
            "totalCheckins": total_checkins,
            "totalSteps": total_steps,
        },
        statusDistribution=[
            {"status": key, "label": label, "count": status_counts[key]}
            for key, label in STATUS_LABELS.items()
        ],
        registrationTrend=[{"date": item.isoformat(), "count": 0} for item in trend_days],
        checkinTrend=[
            {
                "date": item.isoformat(),
                "count": int(db.query(func.count(CheckinPost.id)).filter(CheckinPost.record_date == item).scalar() or 0),
            }
            for item in trend_days
        ],
        topActivities=top[:5],
    )


@router.get("/activities", response_model=AdminActivityListResponse)
async def list_admin_activities(db: Session = Depends(get_db), authorization: str = Header(None)):
    current_user = get_current_user_sync(authorization, db)
    ensure_admin_tables()
    bootstrap_local_owners(db, current_user.id)
    rows = managed_activity_query(db, current_user.id).order_by(Activity.created_at.desc()).all()
    return AdminActivityListResponse(
        items=[serialize_activity(db, row.Activity, row.role) for row in rows],
        total=len(rows),
    )


@router.post("/activities", response_model=AdminActivityItem)
async def create_activity(payload: AdminActivityCreate, db: Session = Depends(get_db), authorization: str = Header(None)):
    current_user = get_current_user_sync(authorization, db)
    ensure_admin_tables()
    validate_dates(payload)
    validate_rules(payload)
    if not payload.name.strip():
        raise HTTPException(status_code=422, detail="活动名称必填")
    if not payload.description.strip():
        raise HTTPException(status_code=422, detail="活动描述必填")

    activity_id = f"admin-{uuid4().hex[:12]}"
    activity = Activity(
        id=activity_id,
        name=payload.name.strip(),
        status="signup",
        status_text="报名中",
        cover_tone="green",
        start_date=payload.activityStartTime,
        end_date=payload.activityEndTime,
        signup_start=payload.registerStartTime,
        signup_end=payload.registerEndTime,
        target_group=payload.scopeText or "全体学生",
        participants=0,
        max_participants=payload.maxParticipants or 0,
        created_by=current_user.id,
    )
    apply_payload(activity, payload, include_dates=True)
    db.add(activity)
    db.add(ActivityAdmin(activity_id=activity_id, user_id=current_user.id, role="owner"))
    db.flush()
    ensure_activity_prize_mappings(db, activity)
    db.commit()
    db.refresh(activity)
    return serialize_activity(db, activity, "owner")


@router.get("/activities/{activity_id}", response_model=AdminActivityItem)
async def get_admin_activity(activity_id: str, db: Session = Depends(get_db), authorization: str = Header(None)):
    current_user = get_current_user_sync(authorization, db)
    ensure_admin_tables()
    role = require_admin(db, activity_id, current_user.id)
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="活动不存在")
    return serialize_activity(db, activity, role)


@router.post("/activities/{activity_id}/winners/generate")
async def generate_activity_winners(activity_id: str, db: Session = Depends(get_db), authorization: str = Header(None)):
    current_user = get_current_user_sync(authorization, db)
    ensure_admin_tables()
    role = require_admin(db, activity_id, current_user.id)
    if role != "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅根管理员可以生成获奖记录")
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="活动不存在")
    return ensure_activity_winners(db, activity)


@router.put("/activities/{activity_id}", response_model=AdminActivityItem)
async def update_activity(activity_id: str, payload: AdminActivityUpdate, db: Session = Depends(get_db), authorization: str = Header(None)):
    current_user = get_current_user_sync(authorization, db)
    ensure_admin_tables()
    role = require_admin(db, activity_id, current_user.id)
    if role != "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="普通管理员只能查看活动信息")
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="活动不存在")

    status_key, _ = activity_status(activity)
    touched_fields = getattr(payload, "model_fields_set", getattr(payload, "__fields_set__", set()))
    max_participants_touched = "maxParticipants" in touched_fields
    if status_key == "ended":
        raise HTTPException(status_code=403, detail="活动已结束，不允许编辑")
    if status_key in {"active"}:
        illegal_fields = [
            payload.registerStartTime,
            payload.registerEndTime,
            payload.activityStartTime,
            payload.activityEndTime,
            payload.scopeText,
            [item.model_dump(exclude_none=True) for item in payload.scoreRule] if payload.scoreRule else None,
            payload.awardRules,
            payload.prizes,
            max_participants_touched,
        ]
        if any(bool(item) for item in illegal_fields):
            raise HTTPException(status_code=403, detail="活动进行中只能修改名称、描述、海报和打卡动态可见性")
    if status_key in {"pre_signup", "signup"}:
        if max_participants_touched:
            old_max = int(activity.max_participants or 0)
            new_max = int(payload.maxParticipants or 0)
            if old_max <= 0 and new_max > 0:
                raise HTTPException(status_code=422, detail="原活动未设置人数上限，不能改为设置上限")
            if old_max > 0 and new_max > 0 and new_max < old_max:
                raise HTTPException(status_code=422, detail="最大报名人数不能低于原设置的人数")
            current_count = participant_count(db, activity_id)
            if new_max and new_max < current_count:
                raise HTTPException(status_code=422, detail="最大报名人数不能小于当前已报名人数")
        if any([
            payload.registerStartTime,
            payload.registerEndTime,
            payload.activityStartTime,
            payload.activityEndTime,
            payload.scopeText,
            [item.model_dump(exclude_none=True) for item in payload.scoreRule] if payload.scoreRule else None,
            payload.awardRules,
            payload.prizes,
        ]):
            raise HTTPException(status_code=403, detail="报名开始后不能修改时间、范围、积分规则、获奖规则和奖品规则")

    # Build a partial update without touching immutable JSON fields unless the
    # activity has not started registration and all date fields are present.
    if payload.name is not None:
        activity.name = payload.name.strip()
    if payload.description is not None:
        activity.description = payload.description.strip()
    if payload.posterUrl is not None:
        activity.poster_url = normalize_stored_image_url(payload.posterUrl)
    if max_participants_touched:
        activity.max_participants = payload.maxParticipants or 0
    if payload.checkinPostVisible is not None:
        activity.checkin_post_visible = bool(payload.checkinPostVisible)
    db.commit()
    db.refresh(activity)
    return serialize_activity(db, activity, role)


@router.get("/activities/{activity_id}/admins", response_model=ActivityAdminListResponse)
async def list_activity_admins(activity_id: str, db: Session = Depends(get_db), authorization: str = Header(None)):
    current_user = get_current_user_sync(authorization, db)
    ensure_admin_tables()
    role = require_admin(db, activity_id, current_user.id)
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="活动不存在")
    status_key, status_text = activity_status(activity)
    rows = db.query(ActivityAdmin, User, Department.name.label("department_name")).join(
        User, ActivityAdmin.user_id == User.id
    ).join(
        Department, User.department_id == Department.id, isouter=True
    ).filter(ActivityAdmin.activity_id == activity_id).order_by(ActivityAdmin.role.desc(), ActivityAdmin.id.asc()).all()
    return ActivityAdminListResponse(
        activityId=activity_id,
        activityStatus=status_key,
        activityStatusText=status_text,
        currentUserRole=role,
        canManage=role == "owner" and status_key != "ended",
        items=[
            ActivityAdminItem(
                id=row.ActivityAdmin.id,
                userId=row.User.id,
                displayUserId=format_user_code(row.User.id),
                name=row.User.name,
                avatar=row.User.avatar,
                departmentName=row.department_name,
                role=row.ActivityAdmin.role,
                roleText="根管理员" if row.ActivityAdmin.role == "owner" else "普通管理员",
                isOwner=row.ActivityAdmin.role == "owner",
            )
            for row in rows
        ],
    )


@router.post("/activities/{activity_id}/admins", response_model=ActivityAdminItem)
async def add_activity_admin(activity_id: str, payload: ActivityAdminAddRequest, db: Session = Depends(get_db), authorization: str = Header(None)):
    current_user = get_current_user_sync(authorization, db)
    ensure_admin_tables()
    require_owner(db, activity_id, current_user.id)
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="活动不存在")
    require_not_ended(activity)
    user = db.query(User).filter(User.id == payload.userId).first()
    if not user:
        raise HTTPException(status_code=404, detail="未找到该用户")
    exists = db.query(ActivityAdmin).filter(
        ActivityAdmin.activity_id == activity_id,
        ActivityAdmin.user_id == payload.userId,
    ).first()
    if exists:
        raise HTTPException(status_code=409, detail="该用户已是管理员")
    admin = ActivityAdmin(activity_id=activity_id, user_id=payload.userId, role="admin")
    db.add(admin)
    db.commit()
    db.refresh(admin)
    department = db.query(Department).filter(Department.id == user.department_id).first() if user.department_id else None
    return ActivityAdminItem(
        id=admin.id,
        userId=user.id,
        displayUserId=format_user_code(user.id),
        name=user.name,
        avatar=user.avatar,
        departmentName=department.name if department else None,
        role="admin",
        roleText="普通管理员",
        isOwner=False,
    )


@router.delete("/activities/{activity_id}/admins/{user_id}")
async def remove_activity_admin(activity_id: str, user_id: int, db: Session = Depends(get_db), authorization: str = Header(None)):
    current_user = get_current_user_sync(authorization, db)
    ensure_admin_tables()
    require_owner(db, activity_id, current_user.id)
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="活动不存在")
    require_not_ended(activity)
    target = db.query(ActivityAdmin).filter(
        ActivityAdmin.activity_id == activity_id,
        ActivityAdmin.user_id == user_id,
    ).first()
    if not target:
        raise HTTPException(status_code=404, detail="管理员不存在")
    if target.role == "owner":
        raise HTTPException(status_code=403, detail="根管理员不能被移除")
    db.delete(target)
    db.commit()
    return {"success": True}


@router.get("/users/{user_code}", response_model=AdminUserItem)
async def get_user_for_admin(user_code: str, db: Session = Depends(get_db), authorization: str = Header(None)):
    get_current_user_sync(authorization, db)
    user_id = parse_user_code(user_code)
    if user_id is None:
        raise HTTPException(status_code=404, detail="未找到该用户")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="未找到该用户")
    department = db.query(Department).filter(Department.id == user.department_id).first() if user.department_id else None
    return AdminUserItem(
        id=user.id,
        displayUserId=format_user_code(user.id),
        name=user.name,
        avatar=user.avatar,
        departmentName=department.name if department else None,
    )
