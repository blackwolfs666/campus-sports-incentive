from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, date, timedelta
from typing import Optional
import base64
import json

from app.core.database import get_db
from app.core.config import settings
from app.models.models import User, Department, StepRecord, Setting, PointsRecord, PointsType
from app.schemas.schemas import (
    StepSyncRequest, StepSyncResponse, StepRecordResponse,
    HomeDataResponse, MessageResponse
)
from app.api.auth import get_current_user_sync, get_wechat_session_key
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

router = APIRouter(prefix="/steps", tags=["步数"])


def decrypt_wechat_run_data(session_key: str, encrypted_data: str, iv: str) -> dict:
    """解密微信运动数据。"""
    try:
        session_key_bytes = base64.b64decode(session_key)
        encrypted_data_bytes = base64.b64decode(encrypted_data)
        iv_bytes = base64.b64decode(iv)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="微信运动加密数据格式无效"
        )

    if len(session_key_bytes) not in (16, 24, 32) or len(iv_bytes) != 16:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="微信运动解密参数无效"
        )

    try:
        cipher = Cipher(algorithms.AES(session_key_bytes), modes.CBC(iv_bytes))
        decryptor = cipher.decryptor()
        padded = decryptor.update(encrypted_data_bytes) + decryptor.finalize()
        pad_len = padded[-1]
        if pad_len < 1 or pad_len > 16:
            raise ValueError("invalid padding")
        raw = padded[:-pad_len]
        data = json.loads(raw.decode("utf-8"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="微信运动数据解密失败，请确认 AppID、AppSecret 与当前小程序一致"
        )

    watermark = data.get("watermark") or {}
    if watermark.get("appid") and watermark.get("appid") != settings.WECHAT_APPID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="微信运动数据不属于当前小程序"
        )

    return data


def get_step_records_from_wechat_data(data: dict) -> list[tuple[int, date]]:
    step_info_list = data.get("stepInfoList")
    if not isinstance(step_info_list, list):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="微信运动数据中缺少 stepInfoList"
        )

    latest_by_date = {}
    for item in step_info_list:
        timestamp = item.get("timestamp")
        steps = item.get("step")
        if timestamp is None or steps is None:
            continue
        record_date = datetime.fromtimestamp(int(timestamp)).date()
        current = latest_by_date.get(record_date)
        if current is None or int(timestamp) > current[0]:
            latest_by_date[record_date] = (int(timestamp), int(steps))

    if not latest_by_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="微信运动数据中没有可同步的步数"
        )

    return [
        (steps, record_date)
        for record_date, (_, steps) in sorted(latest_by_date.items(), key=lambda item: item[0])
    ]


def get_today_steps_from_wechat_records(records: list[tuple[int, date]]) -> tuple[int, date]:
    today = date.today()
    for steps, record_date in records:
        if record_date == today:
            return steps, today
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="微信运动数据中没有今天的步数"
    )


def upsert_step_and_points(
    db: Session,
    user_id: int,
    steps: int,
    record_date: date,
    distance: Optional[float] = None
) -> StepRecord:
    distance_value = float(distance) if distance is not None else round(steps * 0.0007, 2)
    step_record = db.query(StepRecord).filter(
        StepRecord.user_id == user_id,
        StepRecord.record_date == record_date
    ).first()

    if step_record:
        step_record.steps = steps
        step_record.distance = distance_value
        step_record.source = "wechat"
    else:
        step_record = StepRecord(
            user_id=user_id,
            steps=steps,
            distance=distance_value,
            record_date=record_date,
            source="wechat"
        )
        db.add(step_record)

    db.flush()

    sync_points = max(int(steps) // 100, 0)
    points_record = db.query(PointsRecord).filter(
        PointsRecord.user_id == user_id,
        PointsRecord.type == PointsType.challenge,
        PointsRecord.reference_id == step_record.id
    ).first()

    if points_record:
        points_record.points = sync_points
        points_record.description = f"{record_date.isoformat()} 步数同步积分"
    else:
        db.add(PointsRecord(
            user_id=user_id,
            points=sync_points,
            type=PointsType.challenge,
            reference_id=step_record.id,
            description=f"{record_date.isoformat()} 步数同步积分"
        ))

    return step_record


def resolve_step_sync_payload(request: StepSyncRequest) -> tuple[int, float, date]:
    if request.encryptedData or request.iv or request.code:
        raise RuntimeError("wechat_payload")

    if request.steps is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="同步步数需要提供 steps，或提供 code/encryptedData/iv 进行微信运动解密"
        )

    steps = int(request.steps)
    record_date = request.record_date or date.today()
    distance = request.distance if request.distance is not None else steps * 0.0007
    return steps, float(distance), record_date


@router.post("/sync", response_model=StepSyncResponse)
async def sync_steps(
    request: StepSyncRequest,
    db: Session = Depends(get_db),
    authorization: str = Header(None)
):
    """同步步数"""
    current_user = get_current_user_sync(authorization, db)
    records_to_sync = []

    try:
        steps, distance, record_date = resolve_step_sync_payload(request)
        records_to_sync = [(steps, record_date, distance)]
    except RuntimeError:
        if not request.code or not request.encryptedData or not request.iv:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="微信运动同步需要同时提供 code、encryptedData、iv"
            )
        if not settings.WECHAT_APPID or not settings.WECHAT_SECRET:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="微信运动解密未配置：请在后端 .env 中配置 WECHAT_APPID 和 WECHAT_SECRET"
            )

        wechat_data = await get_wechat_session_key(request.code)
        session_key = wechat_data.get("session_key")
        if not session_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="微信登录未返回 session_key，无法解密微信运动数据"
            )

        run_data = decrypt_wechat_run_data(session_key, request.encryptedData, request.iv)
        wechat_records = get_step_records_from_wechat_data(run_data)
        steps, record_date = get_today_steps_from_wechat_records(wechat_records)
        distance = round(steps * 0.0007, 2)
        records_to_sync = [
            (item_steps, item_date, round(item_steps * 0.0007, 2))
            for item_steps, item_date in wechat_records
        ]

    for item_steps, item_date, item_distance in records_to_sync:
        upsert_step_and_points(db, current_user.id, item_steps, item_date, item_distance)
    
    # 更新用户总步数
    current_user.total_steps = db.query(func.sum(StepRecord.steps)).filter(
        StepRecord.user_id == current_user.id
    ).scalar() or 0
    
    current_user.total_distance = db.query(func.sum(StepRecord.distance)).filter(
        StepRecord.user_id == current_user.id
    ).scalar() or 0
    
    # 计算连续达标天数
    daily_goal = int(db.query(Setting).filter(
        Setting.setting_key == "daily_step_goal"
    ).first().setting_value or 10000)
    
    streak_days = calculate_streak_days(db, current_user.id, daily_goal)
    current_user.streak_days = streak_days
    
    db.commit()
    
    return StepSyncResponse(
        success=True,
        steps=steps,
        total_steps=current_user.total_steps,
        streak_days=streak_days,
        message="步数同步成功"
    )


def calculate_streak_days(db: Session, user_id: int, daily_goal: int) -> int:
    """计算连续达标天数"""
    streak = 0
    check_date = date.today()
    
    while True:
        record = db.query(StepRecord).filter(
            StepRecord.user_id == user_id,
            StepRecord.record_date == check_date
        ).first()
        
        if record and record.steps >= daily_goal:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break
    
    return streak


@router.get("/today", response_model=StepRecordResponse)
async def get_today_steps(
    db: Session = Depends(get_db),
    authorization: str = Header(None)
):
    """获取今日步数"""
    current_user = get_current_user_sync(authorization, db)
    
    today = date.today()
    record = db.query(StepRecord).filter(
        StepRecord.user_id == current_user.id,
        StepRecord.record_date == today
    ).first()
    
    if not record:
        return StepRecordResponse(
            id=0,
            user_id=current_user.id,
            steps=0,
            distance=0.0,
            record_date=today,
            source="wechat",
            created_at=datetime.now()
        )
    
    return StepRecordResponse.model_validate(record)


@router.get("/history", response_model=list[StepRecordResponse])
async def get_step_history(
    days: int = 7,
    db: Session = Depends(get_db),
    authorization: str = Header(None)
):
    """获取历史步数"""
    current_user = get_current_user_sync(authorization, db)
    
    start_date = date.today() - timedelta(days=days)
    
    records = db.query(StepRecord).filter(
        StepRecord.user_id == current_user.id,
        StepRecord.record_date >= start_date
    ).order_by(desc(StepRecord.record_date)).all()
    
    return [StepRecordResponse.model_validate(r) for r in records]


@router.get("/home", response_model=HomeDataResponse)
async def get_home_data(
    db: Session = Depends(get_db),
    authorization: str = Header(None)
):
    """获取首页数据"""
    current_user = get_current_user_sync(authorization, db)
    
    # 获取今日步数
    today = date.today()
    today_record = db.query(StepRecord).filter(
        StepRecord.user_id == current_user.id,
        StepRecord.record_date == today
    ).first()
    
    today_steps = today_record.steps if today_record else 0
    last_sync_time = today_record.updated_at if today_record else None
    
    # 获取每日目标
    daily_goal_setting = db.query(Setting).filter(
        Setting.setting_key == "daily_step_goal"
    ).first()
    daily_goal = int(daily_goal_setting.setting_value) if daily_goal_setting else 10000
    
    # 获取部门名称
    department_name = None
    if current_user.department_id:
        dept = db.query(Department).filter(Department.id == current_user.department_id).first()
        department_name = dept.name if dept else None
    
    # 获取周挑战信息
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    week_total = db.query(func.sum(StepRecord.steps)).filter(
        StepRecord.user_id == current_user.id,
        StepRecord.record_date >= week_start,
        StepRecord.record_date <= week_end
    ).scalar() or 0
    
    return HomeDataResponse(
        today_steps=today_steps,
        total_steps=current_user.total_steps,
        total_distance=float(current_user.total_distance),
        streak_days=current_user.streak_days,
        health_level=current_user.health_level,
        daily_goal=daily_goal,
        department_name=department_name,
        last_sync_time=last_sync_time,
        week_challenge={
            "week_total": week_total,
            "week_start": str(week_start),
            "week_end": str(week_end)
        }
    )
