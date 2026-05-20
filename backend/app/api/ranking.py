from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from datetime import date, timedelta
from typing import Optional

from app.core.database import get_db, engine
from app.models.models import User, Department, StepRecord, PointsRecord, ActivityParticipant, Activity
from app.schemas.schemas import RankingItem, RankingResponse
from app.api.auth import get_current_user_sync

router = APIRouter(prefix="/ranking", tags=["排行榜"])

ACTIVITY_DATE_RANGES = {
    "campus-spring-2026": (date(2026, 3, 1), date(2026, 5, 31)),
    "library-marathon-2026": (date(2026, 4, 15), date(2026, 5, 22)),
    "evening-walk-2026": (date(2026, 4, 10), date(2026, 5, 31)),
    "winter-run-2026": (date(2025, 12, 1), date(2026, 1, 31)),
}

_activity_participant_table_ready = False


def ensure_activity_participant_table() -> None:
    global _activity_participant_table_ready
    if _activity_participant_table_ready:
        return
    ActivityParticipant.__table__.create(bind=engine, checkfirst=True)
    _activity_participant_table_ready = True


def ensure_current_activity_participant(db: Session, activity_id: str, user_id: int) -> None:
    exists = db.query(ActivityParticipant.id).filter(
        ActivityParticipant.activity_id == activity_id,
        ActivityParticipant.user_id == user_id
    ).first()
    if not exists:
        db.add(ActivityParticipant(activity_id=activity_id, user_id=user_id))
        db.flush()
        db.commit()


def get_activity_date_range(activity_id: str) -> tuple[date, date]:
    # Kept as a local fallback for databases initialized before the activities
    # table existed. New data should come from the activities API/table.
    return ACTIVITY_DATE_RANGES.get(activity_id, (date(1970, 1, 1), date(2999, 12, 31)))


@router.get("", response_model=RankingResponse)
async def get_ranking(
    period_type: str = "total_steps",  # points, total_steps, daily, weekly, monthly, yearly
    scope: str = "all",  # all, department
    activity_id: Optional[str] = None,
    department_id: Optional[int] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    authorization: str = Header(None)
):
    """获取排行榜"""
    current_user = get_current_user_sync(authorization, db)

    if activity_id:
        ensure_activity_participant_table()
        ensure_current_activity_participant(db, activity_id, current_user.id)
        activity = db.query(Activity).filter(Activity.id == activity_id).first()
        if activity:
            start_date, end_date = activity.start_date, activity.end_date
        else:
            start_date, end_date = get_activity_date_range(activity_id)

        step_totals = db.query(
            StepRecord.user_id.label("user_id"),
            func.sum(StepRecord.steps).label("total_steps")
        ).filter(
            StepRecord.record_date >= start_date,
            StepRecord.record_date <= end_date
        ).group_by(
            StepRecord.user_id
        ).subquery()

        query = db.query(
            ActivityParticipant.user_id,
            User.name,
            User.avatar,
            Department.name.label("department_name"),
            func.coalesce(step_totals.c.total_steps, 0).label("total_steps")
        ).join(
            User, ActivityParticipant.user_id == User.id
        ).join(
            Department, User.department_id == Department.id, isouter=True
        ).outerjoin(
            step_totals, step_totals.c.user_id == ActivityParticipant.user_id
        ).filter(
            ActivityParticipant.activity_id == activity_id
        )

        ranked_rows = []
        for row in query.all():
            total_steps = int(row.total_steps or 0)
            ranked_rows.append({
                "user_id": row.user_id,
                "name": row.name,
                "avatar": row.avatar,
                "department_name": row.department_name,
                "steps": total_steps,
                "points": total_steps // 100
            })

        score_key = "points" if period_type == "points" else "steps"
        ranked_rows.sort(key=lambda item: item[score_key], reverse=True)

        all_items = [
            RankingItem(
                rank=idx,
                user_id=row["user_id"],
                name=row["name"],
                avatar=row["avatar"],
                department_name=row["department_name"],
                steps=row["steps"],
                points=row["points"]
            )
            for idx, row in enumerate(ranked_rows, 1)
        ]

        return RankingResponse(
            items=all_items[:limit],
            my_rank=next((item for item in all_items if item.user_id == current_user.id), None),
            total=len(all_items)
        )

    if period_type == "points":
        query = db.query(
            PointsRecord.user_id,
            User.name,
            User.avatar,
            Department.name.label("department_name"),
            func.sum(PointsRecord.points).label("total_points")
        ).join(
            User, PointsRecord.user_id == User.id
        ).join(
            Department, User.department_id == Department.id, isouter=True
        ).group_by(
            PointsRecord.user_id
        ).order_by(
            desc("total_points")
        )

        results = query.limit(limit).all()
        items = []
        for idx, r in enumerate(results, 1):
            items.append(RankingItem(
                rank=idx,
                user_id=r.user_id,
                name=r.name,
                avatar=r.avatar,
                department_name=r.department_name,
                steps=0,
                points=r.total_points or 0
            ))

        my_rank = next((item for item in items if item.user_id == current_user.id), None)
        if not my_rank:
            my_total = db.query(func.sum(PointsRecord.points)).filter(
                PointsRecord.user_id == current_user.id
            ).scalar() or 0

            if my_total > 0:
                rank_query = db.query(func.count()).select_from(
                    db.query(PointsRecord.user_id, func.sum(PointsRecord.points).label("p")).group_by(
                        PointsRecord.user_id
                    ).having(
                        func.sum(PointsRecord.points) > my_total
                    ).subquery()
                )
                my_rank = RankingItem(
                    rank=rank_query.scalar() + 1,
                    user_id=current_user.id,
                    name=current_user.name,
                    avatar=current_user.avatar,
                    department_name=None,
                    steps=0,
                    points=my_total
                )

        return RankingResponse(
            items=items,
            my_rank=my_rank,
            total=len(items)
        )
    
    # 计算日期范围
    today = date.today()
    if period_type == "total_steps":
        start_date = date.min
        end_date = date.max
    elif period_type == "daily":
        start_date = today
        end_date = today
    elif period_type == "weekly":
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
    elif period_type == "monthly":
        start_date = today.replace(day=1)
        end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    else:  # yearly
        start_date = today.replace(month=1, day=1)
        end_date = today.replace(month=12, day=31)
    
    # 构建查询
    if scope == "department" and current_user.department_id:
        target_dept_id = department_id or current_user.department_id
        query = db.query(
            StepRecord.user_id,
            User.name,
            User.avatar,
            Department.name.label("department_name"),
            func.sum(StepRecord.steps).label("total_steps")
        ).join(
            User, StepRecord.user_id == User.id
        ).join(
            Department, User.department_id == Department.id, isouter=True
        ).filter(
            StepRecord.record_date >= start_date,
            StepRecord.record_date <= end_date,
            User.department_id == target_dept_id
        ).group_by(
            StepRecord.user_id
        ).order_by(
            desc("total_steps")
        )
    else:
        query = db.query(
            StepRecord.user_id,
            User.name,
            User.avatar,
            Department.name.label("department_name"),
            func.sum(StepRecord.steps).label("total_steps")
        ).join(
            User, StepRecord.user_id == User.id
        ).join(
            Department, User.department_id == Department.id, isouter=True
        ).filter(
            StepRecord.record_date >= start_date,
            StepRecord.record_date <= end_date
        ).group_by(
            StepRecord.user_id
        ).order_by(
            desc("total_steps")
        )
    
    results = query.limit(limit).all()
    
    # 构建排行榜列表
    items = []
    for idx, r in enumerate(results, 1):
        items.append(RankingItem(
            rank=idx,
            user_id=r.user_id,
            name=r.name,
            avatar=r.avatar,
            department_name=r.department_name,
            steps=r.total_steps
        ))
    
    # 查找当前用户排名
    my_rank = None
    for item in items:
        if item.user_id == current_user.id:
            my_rank = item
            break
    
    # 如果用户不在前N名，单独查询
    if not my_rank:
        my_total = db.query(func.sum(StepRecord.steps)).filter(
            StepRecord.user_id == current_user.id,
            StepRecord.record_date >= start_date,
            StepRecord.record_date <= end_date
        ).scalar() or 0
        
        if my_total > 0:
            # 计算排名
            rank_query = db.query(func.count()).select_from(
                db.query(StepRecord.user_id, func.sum(StepRecord.steps).label("s")).filter(
                    StepRecord.record_date >= start_date,
                    StepRecord.record_date <= end_date
                ).group_by(StepRecord.user_id).having(
                    func.sum(StepRecord.steps) > my_total
                ).subquery()
            )
            my_rank_num = rank_query.scalar() + 1
            
            my_rank = RankingItem(
                rank=my_rank_num,
                user_id=current_user.id,
                name=current_user.name,
                avatar=current_user.avatar,
                department_name=None,
                steps=my_total
            )
    
    return RankingResponse(
        items=items,
        my_rank=my_rank,
        total=len(items)
    )


@router.get("/department", response_model=list)
async def get_department_ranking(
    period_type: str = "weekly",
    limit: int = 10,
    db: Session = Depends(get_db),
    authorization: str = Header(None)
):
    """获取部门排行榜"""
    current_user = get_current_user_sync(authorization, db)
    
    today = date.today()
    if period_type == "daily":
        start_date = today
    elif period_type == "weekly":
        start_date = today - timedelta(days=today.weekday())
    elif period_type == "monthly":
        start_date = today.replace(day=1)
    else:
        start_date = today.replace(month=1, day=1)
    
    results = db.query(
        Department.id,
        Department.name,
        func.sum(StepRecord.steps).label("total_steps")
    ).join(
        User, Department.id == User.department_id
    ).join(
        StepRecord, User.id == StepRecord.user_id
    ).filter(
        StepRecord.record_date >= start_date
    ).group_by(
        Department.id
    ).order_by(
        desc("total_steps")
    ).limit(limit).all()
    
    return [
        {
            "rank": idx,
            "department_id": r.id,
            "department_name": r.name,
            "total_steps": r.total_steps
        }
        for idx, r in enumerate(results, 1)
    ]
