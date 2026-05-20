from datetime import date, datetime
import json
import re
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.models import (
    Activity,
    ActivityPrize,
    ActivityParticipant,
    CheckinPost,
    Period,
    PeriodStatus,
    PeriodType,
    Prize,
    PrizeType,
    StepRecord,
    User,
    Winner,
    WinnerStatus,
)


PRIZE_TYPES = [PrizeType.first, PrizeType.second, PrizeType.third, PrizeType.honorable]
DEFAULT_PRIZE_IMAGE = "/images/prizes/medal.svg"


def dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def loads(raw: str | None, fallback):
    if not raw:
        return fallback
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return fallback
    return value if isinstance(value, type(fallback)) else fallback


def as_date(value) -> date:
    if isinstance(value, datetime):
        return value.date()
    return value


def to_int(value, fallback: int | None = None) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def parse_rank_range(value: str | None) -> tuple[int, int] | None:
    text = str(value or "")
    numbers = [int(item) for item in re.findall(r"\d+", text)]
    if not numbers:
        return None
    if "前" in text or "鍓" in text:
        return 1, numbers[0]
    if len(numbers) >= 2:
        return numbers[0], numbers[1]
    return numbers[0], numbers[0]


def prize_type_for_index(index: int) -> PrizeType:
    return PRIZE_TYPES[index] if index < len(PRIZE_TYPES) else PrizeType.honorable


def next_sort_order(db: Session) -> int:
    return int(db.query(func.max(Prize.sort_order)).scalar() or 0) + 1


def find_prize_for_config(db: Session, item: dict, index: int) -> Prize:
    prize_id = to_int(item.get("prize_id") or item.get("prizeId"))
    if prize_id:
        prize = db.query(Prize).filter(Prize.id == prize_id).first()
        if prize:
            if not prize.image_url and (item.get("image_url") or item.get("image")):
                prize.image_url = item.get("image_url") or item.get("image")
            return prize

    name = str(item.get("name") or f"活动奖品{index + 1}").strip()
    prize = db.query(Prize).filter(Prize.name == name).order_by(Prize.id.asc()).first()
    if prize:
        if not prize.image_url and (item.get("image_url") or item.get("image")):
            prize.image_url = item.get("image_url") or item.get("image")
        return prize

    quantity = to_int(item.get("quantity"), 0) or 0
    prize = Prize(
        name=name,
        description=str(item.get("rank") or "活动奖品"),
        image_url=item.get("image_url") or item.get("image") or DEFAULT_PRIZE_IMAGE,
        prize_type=prize_type_for_index(index),
        stock=quantity,
        points=0,
        sort_order=next_sort_order(db) + index,
        is_active=True,
    )
    db.add(prize)
    db.flush()
    return prize


def serialize_activity_prize_row(row: ActivityPrize, prize: Prize, index: int) -> dict:
    image = prize.image_url or DEFAULT_PRIZE_IMAGE
    rank = row.rank_label or f"奖品{index + 1}"
    item = {
        "id": f"ap{row.id}",
        "prize_id": prize.id,
        "rank": rank,
        "rank_label": rank,
        "name": prize.name,
        "image": image,
        "image_url": image,
        "prize_type": prize.prize_type.value if hasattr(prize.prize_type, "value") else str(prize.prize_type),
        "sort_order": row.sort_order,
    }
    if row.quantity is not None:
        item["quantity"] = row.quantity
    if row.rank_start is not None:
        item["rank_start"] = row.rank_start
    if row.rank_end is not None:
        item["rank_end"] = row.rank_end
    return item


def sync_legacy_prizes_json(activity: Activity, normalized: list[dict]) -> None:
    value = dumps(normalized)
    if activity.prizes_json != value:
        activity.prizes_json = value


def ensure_activity_prize_mappings(db: Session, activity: Activity, persist: bool = False) -> list[dict]:
    Prize.__table__.create(bind=db.get_bind(), checkfirst=True)
    ActivityPrize.__table__.create(bind=db.get_bind(), checkfirst=True)
    table_rows = db.query(ActivityPrize, Prize).join(
        Prize, ActivityPrize.prize_id == Prize.id
    ).filter(
        ActivityPrize.activity_id == activity.id
    ).order_by(ActivityPrize.sort_order.asc(), ActivityPrize.id.asc()).all()
    if table_rows:
        normalized = [
            serialize_activity_prize_row(row.ActivityPrize, row.Prize, index)
            for index, row in enumerate(table_rows)
        ]
        sync_legacy_prizes_json(activity, normalized)
        db.flush()
        if persist:
            db.commit()
        return normalized

    prizes = loads(activity.prizes_json, [])
    if not isinstance(prizes, list):
        prizes = []

    normalized = []
    changed = False
    for index, raw_item in enumerate(prizes):
        item = dict(raw_item) if isinstance(raw_item, dict) else {}
        prize = find_prize_for_config(db, item, index)
        rank = item.get("rank") or f"奖品{index + 1}"
        image = item.get("image") or item.get("image_url") or prize.image_url or DEFAULT_PRIZE_IMAGE
        quantity = to_int(item.get("quantity"))
        if quantity is None:
            rank_range = parse_rank_range(rank)
            quantity = rank_range[1] - rank_range[0] + 1 if rank_range else None

        mapped = {
            **item,
            "id": str(item.get("id") or f"p{index + 1}"),
            "prize_id": prize.id,
            "rank": rank,
            "name": item.get("name") or prize.name,
            "image": image,
            "image_url": prize.image_url or image,
            "prize_type": prize.prize_type.value if hasattr(prize.prize_type, "value") else str(prize.prize_type),
        }
        if quantity is not None:
            mapped["quantity"] = quantity
        rank_range = parse_rank_range(rank)
        db.add(ActivityPrize(
            activity_id=activity.id,
            prize_id=prize.id,
            rank_label=rank,
            rank_start=rank_range[0] if rank_range else None,
            rank_end=rank_range[1] if rank_range else None,
            quantity=quantity,
            sort_order=index + 1,
        ))
        normalized.append(mapped)
        if mapped != raw_item:
            changed = True

    if normalized or changed:
        sync_legacy_prizes_json(activity, normalized)
    db.flush()
    if persist:
        db.commit()
    return normalized


def get_daily_step_target(activity: Activity) -> int:
    for rule in loads(activity.score_rule_json, []):
        if isinstance(rule, dict) and rule.get("type") == "daily_step_target":
            return to_int(rule.get("value"), 0) or 0
    for text in loads(activity.rules_json, []):
        match = re.search(r"([\d,]+)\s*步", str(text))
        if match:
            return int(match.group(1).replace(",", ""))
    return 0


def get_award_rules(activity: Activity) -> list[dict]:
    rules = loads(activity.award_rules_json, [])
    return [item for item in rules if isinstance(item, dict)]


def get_max_winners(activity: Activity, prize_configs: list[dict]) -> int:
    values = []
    for rule in get_award_rules(activity):
        if rule.get("type") in {"score_rank", "steps_rank", "target_days", "streak_days", "checkin_post_days"}:
            value = to_int(rule.get("value"))
            if value:
                values.append(value)
    for prize in prize_configs:
        rank_range = parse_rank_range(prize.get("rank"))
        if rank_range:
            values.append(rank_range[1])
        elif to_int(prize.get("quantity")):
            values.append(to_int(prize.get("quantity")) or 0)
    return max(values) if values else len(prize_configs)


def max_streak(values: list[date]) -> int:
    if not values:
        return 0
    dates = sorted(set(values))
    best = current = 1
    for previous, item in zip(dates, dates[1:]):
        if (item - previous).days == 1:
            current += 1
        else:
            current = 1
        best = max(best, current)
    return best


def get_or_create_activity_period(db: Session, activity: Activity) -> Period:
    start = as_date(activity.start_date)
    end = as_date(activity.end_date)
    name = f"{activity.name}获奖周期"
    period = db.query(Period).filter(
        Period.name == name,
        Period.start_date == start,
        Period.end_date == end,
    ).first()
    if period:
        return period

    period = Period(
        name=name,
        period_type=PeriodType.yearly,
        start_date=start,
        end_date=end,
        status=PeriodStatus.finished,
    )
    db.add(period)
    db.flush()
    return period


def get_ranked_participants(db: Session, activity: Activity) -> list[dict]:
    start = as_date(activity.start_date)
    end = as_date(activity.end_date)
    target = get_daily_step_target(activity)

    totals = {
        row.user_id: {
            "total_steps": int(row.total_steps or 0),
            "valid_days": int(row.record_days or 0),
        }
        for row in db.query(
            StepRecord.user_id,
            func.sum(StepRecord.steps).label("total_steps"),
            func.count(func.distinct(StepRecord.record_date)).label("record_days"),
        ).filter(
            StepRecord.record_date >= start,
            StepRecord.record_date <= end,
        ).group_by(StepRecord.user_id).all()
    }

    valid_dates_by_user: dict[int, list[date]] = {}
    if target:
        for row in db.query(StepRecord.user_id, StepRecord.record_date).filter(
            StepRecord.record_date >= start,
            StepRecord.record_date <= end,
            StepRecord.steps >= target,
        ).all():
            valid_dates_by_user.setdefault(row.user_id, []).append(row.record_date)
        for user_id, dates in valid_dates_by_user.items():
            totals.setdefault(user_id, {"total_steps": 0, "valid_days": 0})["valid_days"] = len(set(dates))

    checkins = {
        row.user_id: int(row.days or 0)
        for row in db.query(
            CheckinPost.user_id,
            func.count(func.distinct(CheckinPost.record_date)).label("days"),
        ).filter(
            CheckinPost.activity_id == activity.id,
            CheckinPost.record_date >= start,
            CheckinPost.record_date <= end,
        ).group_by(CheckinPost.user_id).all()
    }

    user_ids = [
        item.user_id
        for item in db.query(ActivityParticipant.user_id).filter(ActivityParticipant.activity_id == activity.id).all()
    ]
    users = {item.id: item for item in db.query(User).filter(User.id.in_(user_ids)).all()} if user_ids else {}
    rows = []
    for user_id in user_ids:
        metrics = totals.get(user_id, {"total_steps": 0, "valid_days": 0})
        rows.append({
            "user_id": user_id,
            "total_steps": metrics["total_steps"],
            "points": metrics["total_steps"] // 100,
            "valid_days": metrics["valid_days"],
            "streak_days": max_streak(valid_dates_by_user.get(user_id, [])) if target else int(users[user_id].streak_days if user_id in users else 0),
            "checkin_post_days": checkins.get(user_id, 0),
        })
    rows.sort(key=lambda item: (item["total_steps"], item["points"]), reverse=True)
    for index, item in enumerate(rows, 1):
        item["rank"] = index
    return rows


def is_eligible(row: dict, activity: Activity) -> bool:
    rules = get_award_rules(activity)
    if not rules:
        return True

    for rule in rules:
        rule_type = rule.get("type")
        value = to_int(rule.get("value"), 0) or 0
        if rule_type == "participation":
            return True
        if rule_type in {"score_rank", "steps_rank"} and value and row["rank"] <= value:
            return True
        if rule_type == "target_days" and row["valid_days"] >= value:
            return True
        if rule_type == "streak_days" and row["streak_days"] >= value:
            return True
        if rule_type == "checkin_post_days" and row["checkin_post_days"] >= value:
            return True
    return False


def prize_for_rank(rank: int, prize_configs: list[dict]) -> dict | None:
    cursor = 1
    fallback = None
    for prize in prize_configs:
        rank_range = parse_rank_range(prize.get("rank"))
        if rank_range and rank_range[0] <= rank <= rank_range[1]:
            return prize
        quantity = to_int(prize.get("quantity"))
        if quantity:
            start, end = cursor, cursor + quantity - 1
            if start <= rank <= end:
                return prize
            cursor = end + 1
        if fallback is None:
            fallback = prize
    return fallback if rank == 1 else None


def ensure_activity_winners(db: Session, activity: Activity) -> dict:
    Period.__table__.create(bind=db.get_bind(), checkfirst=True)
    Winner.__table__.create(bind=db.get_bind(), checkfirst=True)
    if date.today() <= as_date(activity.end_date) and activity.status != "ended":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="活动尚未结束，不能生成获奖记录")

    prize_configs = ensure_activity_prize_mappings(db, activity)
    if not prize_configs:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="活动未配置奖品，不能生成获奖记录")

    period = get_or_create_activity_period(db, activity)
    max_winners = get_max_winners(activity, prize_configs)
    ranked = [item for item in get_ranked_participants(db, activity) if is_eligible(item, activity)]
    selected = ranked[:max_winners]

    created = 0
    updated = 0
    skipped = 0
    for item in selected:
        prize_config = prize_for_rank(item["rank"], prize_configs)
        prize_id = to_int(prize_config.get("prize_id")) if prize_config else None
        if not prize_id:
            skipped += 1
            continue

        winner = db.query(Winner).filter(
            Winner.user_id == item["user_id"],
            Winner.period_id == period.id,
            Winner.prize_id == prize_id,
        ).first()
        if winner:
            winner.activity_id = activity.id
            winner.rank = item["rank"]
            winner.steps = item["total_steps"]
            updated += 1
        else:
            db.add(Winner(
                user_id=item["user_id"],
                activity_id=activity.id,
                prize_id=prize_id,
                period_id=period.id,
                rank=item["rank"],
                steps=item["total_steps"],
                status=WinnerStatus.pending,
            ))
            created += 1

    db.commit()
    return {
        "success": True,
        "activity_id": activity.id,
        "period_id": period.id,
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "total": created + updated,
    }
