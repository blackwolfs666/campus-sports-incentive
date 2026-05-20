from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, inspect, text
from datetime import datetime, date, timedelta
from typing import Optional
from pathlib import Path
import random
import string

from app.core.database import engine, get_db
from app.models.models import Activity, ActivityAdmin, Department, Prize, Period, Setting, User, Winner, WinnerStatus
from app.schemas.schemas import (
    PrizeResponse, WinnerResponse, WinnerWithDetails,
    MyPrizeItem, RedeemRequest, RedeemResponse, MessageResponse
)
from app.api.auth import get_current_user_sync
from app.services.activity_awards import ensure_activity_prize_mappings

router = APIRouter(prefix="/prizes", tags=["奖品"])
QRCODE_DIR = Path(__file__).resolve().parents[2] / "static" / "uploads" / "qrcodes"
_winner_activity_column_ready = False


def ensure_winner_activity_column() -> None:
    global _winner_activity_column_ready
    if _winner_activity_column_ready:
        return

    Winner.__table__.create(bind=engine, checkfirst=True)
    inspector = inspect(engine)
    columns = {item["name"] for item in inspector.get_columns("winners")}
    has_activities = inspector.has_table("activities")
    with engine.begin() as conn:
        if "activity_id" not in columns:
            conn.execute(text("ALTER TABLE winners ADD COLUMN activity_id VARCHAR(100) NULL COMMENT 'Activity ID'"))
            conn.execute(text("CREATE INDEX idx_winner_activity ON winners (activity_id)"))
        if has_activities:
            conn.execute(text(
                "UPDATE winners SET activity_id = 'campus-spring-2026' "
                "WHERE activity_id IS NULL AND id IN (1, 2, 3, 4) "
                "AND EXISTS (SELECT 1 FROM activities WHERE id = 'campus-spring-2026')"
            ))
    _winner_activity_column_ready = True


def normalize_activity_id(value) -> str | None:
    if value is None:
        return None
    text_value = str(value).strip()
    return text_value or None


def require_winner_activity_id(winner: Winner) -> str:
    activity_id = normalize_activity_id(winner.activity_id)
    if not activity_id:
        raise HTTPException(status_code=409, detail="获奖记录缺少活动ID，无法核销")
    return activity_id


def normalize_claim_code(claim_code: str) -> str:
    return "".join(ch for ch in claim_code if ch.isdigit())


def gf_mul(x: int, y: int) -> int:
    result = 0
    while y:
        if y & 1:
            result ^= x
        x <<= 1
        if x & 0x100:
            x ^= 0x11D
        y >>= 1
    return result


def rs_generator_poly(degree: int) -> list[int]:
    poly = [1]
    root = 1
    for _ in range(degree):
        next_poly = [0] * (len(poly) + 1)
        for i, coef in enumerate(poly):
            next_poly[i] ^= gf_mul(coef, root)
            next_poly[i + 1] ^= coef
        poly = next_poly
        root = gf_mul(root, 2)
    return poly


def rs_remainder(data: list[int], degree: int) -> list[int]:
    gen = rs_generator_poly(degree)
    rem = [0] * degree
    for byte in data:
        factor = byte ^ rem[0]
        rem = rem[1:] + [0]
        for i in range(degree):
            rem[i] ^= gf_mul(gen[i + 1], factor)
    return rem


def append_bits(bits: list[int], value: int, width: int) -> None:
    for i in range(width - 1, -1, -1):
        bits.append((value >> i) & 1)


def encode_numeric_qr_codewords(code: str) -> list[int]:
    bits: list[int] = []
    append_bits(bits, 0b0001, 4)
    append_bits(bits, len(code), 10)
    for i in range(0, len(code), 3):
        part = code[i:i + 3]
        append_bits(bits, int(part), 10 if len(part) == 3 else 7 if len(part) == 2 else 4)

    capacity_bits = 19 * 8
    append_bits(bits, 0, min(4, capacity_bits - len(bits)))
    while len(bits) % 8:
        bits.append(0)

    data = []
    for i in range(0, len(bits), 8):
        value = 0
        for bit in bits[i:i + 8]:
            value = (value << 1) | bit
        data.append(value)

    pad = [0xEC, 0x11]
    pad_index = 0
    while len(data) < 19:
        data.append(pad[pad_index % 2])
        pad_index += 1

    return data + rs_remainder(data, 7)


def format_bits() -> int:
    # Error correction level L plus mask 0.
    data = 0b01000
    value = data << 10
    generator = 0b10100110111
    for i in range(14, 9, -1):
        if (value >> i) & 1:
            value ^= generator << (i - 10)
    return ((data << 10) | value) ^ 0b101010000010010


def make_qr_matrix(code: str) -> list[list[bool]]:
    size = 21
    modules: list[list[Optional[bool]]] = [[None for _ in range(size)] for _ in range(size)]
    reserved = [[False for _ in range(size)] for _ in range(size)]

    def set_module(x: int, y: int, value: bool, reserve: bool = True) -> None:
        if 0 <= x < size and 0 <= y < size:
            modules[y][x] = value
            if reserve:
                reserved[y][x] = True

    def draw_finder(x: int, y: int) -> None:
        for dy in range(-1, 8):
            for dx in range(-1, 8):
                xx = x + dx
                yy = y + dy
                if not (0 <= xx < size and 0 <= yy < size):
                    continue
                if dx in (-1, 7) or dy in (-1, 7):
                    set_module(xx, yy, False)
                    continue
                is_border = dx in (0, 6) or dy in (0, 6)
                is_center = 2 <= dx <= 4 and 2 <= dy <= 4
                set_module(xx, yy, is_border or is_center)

    draw_finder(0, 0)
    draw_finder(size - 7, 0)
    draw_finder(0, size - 7)

    for i in range(8, size - 8):
        value = i % 2 == 0
        set_module(i, 6, value)
        set_module(6, i, value)

    set_module(8, size - 8, True)

    # Reserve format information areas before writing data.
    for i in range(9):
        reserved[8][i] = True
        reserved[i][8] = True
    for i in range(8):
        reserved[8][size - 1 - i] = True
        reserved[size - 1 - i][8] = True

    bits = []
    for byte in encode_numeric_qr_codewords(code):
        append_bits(bits, byte, 8)

    bit_index = 0
    upward = True
    x = size - 1
    while x > 0:
        if x == 6:
            x -= 1
        y_range = range(size - 1, -1, -1) if upward else range(size)
        for y in y_range:
            for xx in (x, x - 1):
                if reserved[y][xx]:
                    continue
                bit = bits[bit_index] if bit_index < len(bits) else 0
                bit_index += 1
                if (xx + y) % 2 == 0:
                    bit ^= 1
                set_module(xx, y, bool(bit))
        upward = not upward
        x -= 2

    fmt = format_bits()
    fmt_positions_1 = (
        [(8, i) for i in range(6)] +
        [(8, 7), (8, 8), (7, 8)] +
        [(5 - i, 8) for i in range(6)]
    )
    fmt_positions_2 = (
        [(size - 1 - i, 8) for i in range(8)] +
        [(8, size - 7 + i) for i in range(7)]
    )
    for i, (xx, yy) in enumerate(fmt_positions_1):
        set_module(xx, yy, bool((fmt >> i) & 1))
    for i, (xx, yy) in enumerate(fmt_positions_2):
        set_module(xx, yy, bool((fmt >> i) & 1))

    return [[bool(value) for value in row] for row in modules]


def render_qr_svg(matrix: list[list[bool]]) -> str:
    border = 4
    size = len(matrix)
    view_size = size + border * 2
    rects = []
    for y, row in enumerate(matrix):
        for x, value in enumerate(row):
            if value:
                rects.append(f"M{x + border},{y + border}h1v1h-1z")
    path = " ".join(rects)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {view_size} {view_size}" '
        f'shape-rendering="crispEdges">'
        f'<path fill="#fff" d="M0 0h{view_size}v{view_size}H0z"/>'
        f'<path fill="#000" d="{path}"/>'
        f'</svg>'
    )


def generate_claim_qrcode(claim_code: str) -> str:
    """生成给后台扫码核销使用的二维码，返回可通过 /static 访问的相对 URL。"""

    code = normalize_claim_code(claim_code)
    if len(code) != 12:
        raise HTTPException(status_code=500, detail="兑换码格式异常，无法生成二维码")

    QRCODE_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"claim-{code}.svg"
    target = QRCODE_DIR / filename
    target.write_text(render_qr_svg(make_qr_matrix(code)), encoding="utf-8")

    return f"/static/uploads/qrcodes/{filename}"


def local_qrcode_missing(url: str | None) -> bool:
    if not url:
        return True
    prefix = "/static/uploads/qrcodes/"
    if not url.startswith(prefix):
        return False
    filename = Path(url).name
    return not (QRCODE_DIR / filename).exists()


@router.get("", response_model=list[PrizeResponse])
async def get_prizes(
    is_active: bool = True,
    activity_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取奖品列表"""
    if activity_id:
        activity = db.query(Activity).filter(Activity.id == activity_id).first()
        if not activity:
            raise HTTPException(status_code=404, detail="活动不存在")
        prize_ids = [
            item.get("prize_id")
            for item in ensure_activity_prize_mappings(db, activity, persist=True)
            if item.get("prize_id")
        ]
        prizes = db.query(Prize).filter(Prize.id.in_(prize_ids)).order_by(Prize.sort_order).all() if prize_ids else []
        return [PrizeResponse.model_validate(p) for p in prizes]

    query = db.query(Prize)
    if is_active:
        query = query.filter(Prize.is_active == True)
    
    prizes = query.order_by(Prize.sort_order).all()
    return [PrizeResponse.model_validate(p) for p in prizes]


@router.get("/{prize_id}", response_model=PrizeResponse)
async def get_prize(
    prize_id: int,
    db: Session = Depends(get_db)
):
    """获取奖品详情"""
    prize = db.query(Prize).filter(Prize.id == prize_id).first()
    if not prize:
        raise HTTPException(status_code=404, detail="奖品不存在")
    return PrizeResponse.model_validate(prize)


@router.get("/winners/{prize_id}", response_model=list[WinnerWithDetails])
async def get_prize_winners(
    prize_id: int,
    period_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取奖品获奖名单"""
    ensure_winner_activity_column()
    query = db.query(
        Winner,
        Prize.name.label("prize_name"),
        Prize.image_url.label("prize_image"),
        Prize.prize_type.label("prize_type"),
        Period.name.label("period_name"),
        Activity.name.label("activity_name"),
        User.name.label("user_name"),
        User.avatar.label("user_avatar"),
        Department.name.label("department_name")
    ).join(
        Prize, Winner.prize_id == Prize.id
    ).join(
        Period, Winner.period_id == Period.id
    ).join(
        Activity, Winner.activity_id == Activity.id, isouter=True
    ).join(
        User, Winner.user_id == User.id
    ).join(
        Department, User.department_id == Department.id, isouter=True
    ).filter(
        Winner.prize_id == prize_id
    )
    
    if period_id:
        query = query.filter(Winner.period_id == period_id)
    
    results = query.order_by(desc(Winner.rank)).all()
    
    winners = []
    for r in results:
        winners.append(WinnerWithDetails(
            id=r.Winner.id,
            user_id=r.Winner.user_id,
            prize_id=r.Winner.prize_id,
            period_id=r.Winner.period_id,
            rank=r.Winner.rank,
            steps=r.Winner.steps,
            status=r.Winner.status,
            claim_code=r.Winner.claim_code,
            claim_qrcode=r.Winner.claim_qrcode,
            claim_deadline=r.Winner.claim_deadline,
            claimed_at=r.Winner.claimed_at,
            redeemed_at=r.Winner.redeemed_at,
            created_at=r.Winner.created_at,
            prize_name=r.prize_name,
            prize_image=r.prize_image,
            prize_type=r.prize_type,
            period_name=r.period_name,
            activity_id=r.Winner.activity_id,
            activity_name=r.activity_name,
            user_name=r.user_name,
            user_avatar=r.user_avatar,
            department_name=r.department_name
        ))
    
    return winners


@router.get("/my/list", response_model=list[MyPrizeItem])
async def get_my_prizes(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    authorization: str = Header(None)
):
    """获取我的奖品"""
    ensure_winner_activity_column()
    current_user = get_current_user_sync(authorization, db)
    
    query = db.query(
        Winner,
        Prize.name.label("prize_name"),
        Prize.image_url.label("prize_image"),
        Prize.prize_type.label("prize_type"),
        Period.name.label("period_name"),
        Activity.name.label("activity_name")
    ).join(
        Prize, Winner.prize_id == Prize.id
    ).join(
        Period, Winner.period_id == Period.id
    ).join(
        Activity, Winner.activity_id == Activity.id, isouter=True
    ).filter(
        Winner.user_id == current_user.id
    )
    
    if status:
        query = query.filter(Winner.status == status)
    
    results = query.order_by(desc(Winner.created_at)).all()
    
    items = []
    for r in results:
        items.append(MyPrizeItem(
            id=r.Winner.id,
            activity_id=r.Winner.activity_id,
            activity_name=r.activity_name,
            prize_id=r.Winner.prize_id,
            prize_name=r.prize_name,
            prize_image=r.prize_image,
            prize_type=r.prize_type,
            period_name=r.period_name,
            rank=r.Winner.rank,
            steps=r.Winner.steps,
            status=r.Winner.status,
            claim_code=r.Winner.claim_code,
            claim_deadline=r.Winner.claim_deadline,
            created_at=r.Winner.created_at
        ))
    
    return items


@router.post("/claim/{winner_id}", response_model=WinnerResponse)
async def claim_prize(
    winner_id: int,
    db: Session = Depends(get_db),
    authorization: str = Header(None)
):
    """领取奖品（生成兑换码）"""
    ensure_winner_activity_column()
    current_user = get_current_user_sync(authorization, db)
    
    winner = db.query(Winner).filter(
        Winner.id == winner_id,
        Winner.user_id == current_user.id
    ).first()
    
    if not winner:
        raise HTTPException(status_code=404, detail="获奖记录不存在")
    
    if winner.status != WinnerStatus.pending:
        raise HTTPException(status_code=400, detail="奖品已领取或已兑换")
    
    # 生成兑换码
    code = ''.join(random.choices(string.digits, k=12))
    claim_code = f"{code[:4]} {code[4:8]} {code[8:12]}"
    
    # 获取兑换截止天数
    deadline_days = db.query(Setting).filter(
        Setting.setting_key == "redeem_deadline_days"
    ).first()
    days = int(deadline_days.setting_value) if deadline_days else 30
    
    winner.claim_code = claim_code
    winner.claim_qrcode = generate_claim_qrcode(claim_code)
    winner.claim_deadline = datetime.now() + timedelta(days=days)
    winner.status = WinnerStatus.claimed
    winner.claimed_at = datetime.now()
    
    db.commit()
    db.refresh(winner)
    
    return WinnerResponse.model_validate(winner)


@router.post("/redeem", response_model=RedeemResponse)
async def redeem_prize(
    request: RedeemRequest,
    db: Session = Depends(get_db),
    authorization: str = Header(None)
):
    """用户端不允许自助核销，必须由后台管理员扫码或输入兑换码核销。"""
    get_current_user_sync(authorization, db)
    raise HTTPException(status_code=403, detail="奖品只能由后台管理员核销")


@router.post("/admin/redeem", response_model=RedeemResponse)
async def admin_redeem_prize(
    request: RedeemRequest,
    db: Session = Depends(get_db),
    authorization: str = Header(None)
):
    """后台核销奖品：工作人员扫码或输入兑换码后核销。"""
    from app.api.admin import bootstrap_local_owners, ensure_admin_tables

    ensure_admin_tables()
    ensure_winner_activity_column()
    current_user = get_current_user_sync(authorization, db)
    bootstrap_local_owners(db, current_user.id)
    is_activity_admin = db.query(ActivityAdmin.id).filter(
        ActivityAdmin.user_id == current_user.id
    ).first()
    if not is_activity_admin:
        raise HTTPException(status_code=403, detail="只有活动管理员可以核销奖品")

    code = "".join(ch for ch in request.claim_code if ch.isdigit())
    if len(code) < 12:
        raise HTTPException(status_code=422, detail="请输入完整的12位兑换码")

    winner = db.query(Winner).filter(
        Winner.claim_code.contains(code[:4]),
        Winner.claim_code.contains(code[4:8]),
        Winner.claim_code.contains(code[8:12])
    ).first()

    if not winner:
        raise HTTPException(status_code=404, detail="兑换码无效")

    if winner.status == WinnerStatus.redeemed:
        raise HTTPException(status_code=400, detail="奖品已核销")

    if winner.status != WinnerStatus.claimed:
        raise HTTPException(status_code=400, detail="奖品尚未生成兑换码")

    if winner.claim_deadline and datetime.now() > winner.claim_deadline:
        raise HTTPException(status_code=400, detail="兑换码已过期")

    activity_id = require_winner_activity_id(winner)
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="获奖记录所属活动不存在")

    is_activity_admin = db.query(ActivityAdmin.id).filter(
        ActivityAdmin.activity_id == activity_id,
        ActivityAdmin.user_id == current_user.id
    ).first()
    if not is_activity_admin:
        raise HTTPException(status_code=403, detail="只能核销自己管理活动的奖品")

    prize = db.query(Prize).filter(Prize.id == winner.prize_id).first()
    winner.status = WinnerStatus.redeemed
    winner.redeemed_at = datetime.now()
    db.commit()

    return RedeemResponse(
        success=True,
        message="核销成功",
        prize_name=prize.name if prize else None,
        activity_id=activity.id,
        activity_name=activity.name,
        user_name=winner.user.name if winner.user else None,
        status=winner.status
    )


@router.get("/detail/{winner_id}", response_model=WinnerResponse)
async def get_winner_detail(
    winner_id: int,
    db: Session = Depends(get_db),
    authorization: str = Header(None)
):
    """获取获奖详情"""
    ensure_winner_activity_column()
    current_user = get_current_user_sync(authorization, db)
    
    winner = db.query(Winner).filter(
        Winner.id == winner_id,
        Winner.user_id == current_user.id
    ).first()
    
    if not winner:
        raise HTTPException(status_code=404, detail="获奖记录不存在")

    if winner.status in {WinnerStatus.claimed, WinnerStatus.redeemed} and winner.claim_code and local_qrcode_missing(winner.claim_qrcode):
        winner.claim_qrcode = generate_claim_qrcode(winner.claim_code)
        db.commit()
        db.refresh(winner)
    
    return WinnerResponse.model_validate(winner)
