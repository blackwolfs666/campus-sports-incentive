from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from enum import Enum


# 枚举类型
class PrizeType(str, Enum):
    first = "first"
    second = "second"
    third = "third"
    honorable = "honorable"


class PeriodType(str, Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    yearly = "yearly"


class WinnerStatus(str, Enum):
    pending = "pending"
    claimed = "claimed"
    redeemed = "redeemed"


# 用户相关
class UserBase(BaseModel):
    name: str
    avatar: Optional[str] = None
    phone: Optional[str] = None
    department_id: Optional[int] = None


class UserCreate(UserBase):
    openid: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    avatar: Optional[str] = None
    phone: Optional[str] = None
    department_id: Optional[int] = None


class UserResponse(UserBase):
    id: int
    openid: str
    employee_id: Optional[str] = None
    cas_binded: bool = False
    edu_person_type: Optional[str] = None
    total_steps: int = 0
    total_distance: float = 0.0
    streak_days: int = 0
    health_level: int = 1
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserWithDepartment(UserResponse):
    department_name: Optional[str] = None


# 部门相关
class DepartmentBase(BaseModel):
    name: str
    icon: Optional[str] = None
    sort_order: int = 0


class DepartmentResponse(DepartmentBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# 步数记录
class StepRecordBase(BaseModel):
    steps: int
    distance: Optional[float] = 0.0
    record_date: date
    source: str = "wechat"


class StepRecordCreate(StepRecordBase):
    pass


class StepRecordResponse(StepRecordBase):
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class StepSyncRequest(BaseModel):
    steps: Optional[int] = None
    distance: Optional[float] = 0.0
    record_date: Optional[date] = None
    code: Optional[str] = None
    encryptedData: Optional[str] = None
    iv: Optional[str] = None


class StepSyncResponse(BaseModel):
    success: bool
    steps: int
    total_steps: int
    streak_days: int
    message: str = ""


# 排行榜
class RankingItem(BaseModel):
    rank: int
    user_id: int
    name: str
    avatar: Optional[str] = None
    department_name: Optional[str] = None
    steps: int
    points: int = 0


class RankingResponse(BaseModel):
    items: List[RankingItem]
    my_rank: Optional[RankingItem] = None
    total: int


class ActivityPrizeItem(BaseModel):
    id: str
    prize_id: Optional[int] = None
    rank: str
    rank_label: Optional[str] = None
    rank_start: Optional[int] = None
    rank_end: Optional[int] = None
    name: str
    icon: Optional[str] = None
    image: Optional[str] = None
    image_url: Optional[str] = None
    prize_type: Optional[str] = None
    quantity: Optional[int] = None
    sort_order: Optional[int] = None


class ActivityResponse(BaseModel):
    id: str
    name: str
    status: str
    statusText: str
    coverTone: str
    startDate: str
    endDate: str
    signupStart: str
    signupEnd: str
    targetGroup: str
    participants: int
    maxParticipants: int
    isRegistered: bool = False
    rulesShort: str
    rewardShort: str
    description: str = ""
    tags: List[str] = Field(default_factory=list)
    rules: List[str] = Field(default_factory=list)
    prizes: List[ActivityPrizeItem] = Field(default_factory=list)
    totalSteps: int = 0
    myPoints: int = 0
    myRank: Optional[int] = None
    topTenGap: Optional[int] = None
    myFinalRank: Optional[int] = None
    hadPrize: bool = False
    wonPrizeName: Optional[str] = None


class ActivityListResponse(BaseModel):
    items: List[ActivityResponse]
    total: int


class ActivityJoinResponse(BaseModel):
    success: bool
    activity: ActivityResponse


class AdminScoreRule(BaseModel):
    type: Optional[str] = None
    label: Optional[str] = None
    value: Optional[int] = None
    stepUnit: Optional[int] = None
    score: Optional[int] = None
    # Legacy fields kept so old clients/data can still be parsed.
    dailyStepTarget: Optional[int] = None
    baseScore: Optional[int] = None
    extraStepUnit: Optional[int] = None
    extraScore: Optional[int] = None
    maxDailyScore: Optional[int] = None


class AdminAwardRule(BaseModel):
    type: str
    value: Optional[int] = None
    label: Optional[str] = None
    desc: Optional[str] = None


class AdminPrizeConfig(BaseModel):
    prize_id: Optional[int] = None
    name: str = ""
    quantity: Optional[int] = None
    image: Optional[str] = None


class AdminActivityBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = ""
    posterUrl: Optional[str] = ""
    registerStartTime: Optional[datetime] = None
    registerEndTime: Optional[datetime] = None
    activityStartTime: Optional[datetime] = None
    activityEndTime: Optional[datetime] = None
    scopeText: Optional[str] = ""
    maxParticipants: Optional[int] = None
    scoreRule: List[AdminScoreRule] = Field(default_factory=list)
    awardRules: List[AdminAwardRule] = Field(default_factory=list)
    prizes: List[AdminPrizeConfig] = Field(default_factory=list)
    checkinPostVisible: Optional[bool] = True


class AdminActivityCreate(AdminActivityBase):
    name: str
    description: str
    registerStartTime: datetime
    registerEndTime: datetime
    activityStartTime: datetime
    activityEndTime: datetime


class AdminActivityUpdate(AdminActivityBase):
    pass


class AdminActivityItem(BaseModel):
    id: str
    name: str
    description: str = ""
    posterUrl: str = ""
    status: str
    statusText: str
    registerStartTime: datetime
    registerEndTime: datetime
    activityStartTime: datetime
    activityEndTime: datetime
    scopeText: str = ""
    currentParticipants: int = 0
    maxParticipants: Optional[int] = None
    scoreRule: List[dict] = Field(default_factory=list)
    awardRules: List[dict] = Field(default_factory=list)
    prizes: List[dict] = Field(default_factory=list)
    checkinPostVisible: bool = True
    myAdminRole: str
    canManageAdmins: bool = False
    canEdit: bool = True
    canGenerateWinners: bool = False
    createdBy: Optional[int] = None


class AdminActivityListResponse(BaseModel):
    items: List[AdminActivityItem]
    total: int


class AdminUserItem(BaseModel):
    id: int
    displayUserId: str
    name: str
    avatar: Optional[str] = None
    departmentName: Optional[str] = None


class ActivityAdminItem(BaseModel):
    id: int
    userId: int
    displayUserId: str
    name: str
    avatar: Optional[str] = None
    departmentName: Optional[str] = None
    role: str
    roleText: str
    isOwner: bool


class ActivityAdminListResponse(BaseModel):
    activityId: str
    activityStatus: str
    activityStatusText: str
    currentUserRole: str
    canManage: bool
    items: List[ActivityAdminItem]


class ActivityAdminAddRequest(BaseModel):
    userId: int


class AdminDashboardResponse(BaseModel):
    summaryCards: dict
    statusDistribution: List[dict]
    registrationTrend: List[dict]
    checkinTrend: List[dict]
    topActivities: List[dict]


# 奖品
class PrizeBase(BaseModel):
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    prize_type: PrizeType = PrizeType.honorable
    stock: int = 0
    points: int = 0
    sort_order: int = 0


class PrizeResponse(PrizeBase):
    id: int
    is_active: bool
    
    class Config:
        from_attributes = True


# 获奖记录
class WinnerBase(BaseModel):
    user_id: int
    activity_id: Optional[str] = None
    prize_id: int
    period_id: int
    rank: int = 0
    steps: int = 0


class WinnerResponse(WinnerBase):
    id: int
    status: WinnerStatus
    claim_code: Optional[str] = None
    claim_qrcode: Optional[str] = None
    claim_deadline: Optional[datetime] = None
    claimed_at: Optional[datetime] = None
    redeemed_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class WinnerWithDetails(WinnerResponse):
    prize_name: str
    prize_image: Optional[str] = None
    prize_type: PrizeType
    period_name: str
    activity_name: Optional[str] = None
    user_name: str
    user_avatar: Optional[str] = None
    department_name: Optional[str] = None


# 我的奖品
class MyPrizeItem(BaseModel):
    id: int
    activity_id: Optional[str] = None
    activity_name: Optional[str] = None
    prize_id: int
    prize_name: str
    prize_image: Optional[str] = None
    prize_type: PrizeType
    period_name: str
    rank: int
    steps: int
    status: WinnerStatus
    claim_code: Optional[str] = None
    claim_deadline: Optional[datetime] = None
    created_at: datetime


# 认证
class WechatLoginRequest(BaseModel):
    code: str


class WechatLoginResponse(BaseModel):
    token: str
    user: UserResponse
    is_new_user: bool = False
    needs_binding: bool = False


class CasLoginRequest(BaseModel):
    username: str
    password: str


class CasLoginResponse(BaseModel):
    bind_token: str
    expires_in: int


class CasBindRequest(BaseModel):
    bind_token: str


class CasBindResponse(BaseModel):
    success: bool
    name: str
    employee_id: str
    department_name: Optional[str] = None
    edu_person_type: Optional[str] = None


class CasStatusResponse(BaseModel):
    cas_binded: bool
    employee_id: Optional[str] = None
    name: Optional[str] = None
    department_name: Optional[str] = None
    edu_person_type: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# 周期
class PeriodBase(BaseModel):
    name: str
    period_type: PeriodType = PeriodType.weekly
    start_date: date
    end_date: date


class PeriodResponse(PeriodBase):
    id: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# 首页数据
class HomeDataResponse(BaseModel):
    today_steps: int
    total_steps: int
    total_distance: float
    streak_days: int
    health_level: int
    daily_goal: int
    department_name: Optional[str] = None
    last_sync_time: Optional[datetime] = None
    week_challenge: Optional[dict] = None


class CheckinCreate(BaseModel):
    activity_id: str = Field(..., min_length=1, max_length=100)
    content: Optional[str] = Field(default="", max_length=500)
    image_urls: List[str] = Field(default_factory=list, max_length=9)


class CheckinItem(BaseModel):
    id: int
    activity_id: str
    user_id: int
    user_name: str
    user_avatar: Optional[str] = None
    department_name: Optional[str] = None
    content: Optional[str] = ""
    image_urls: List[str] = Field(default_factory=list)
    steps: int
    streak_days: int
    record_date: date
    cheer_count: int = 0
    has_cheered: bool = False
    is_mine: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None


class CheckinListResponse(BaseModel):
    items: List[CheckinItem]
    total: int


class CheckinCheerResponse(BaseModel):
    success: bool
    cheer_count: int
    has_cheered: bool


# 兑换
class RedeemRequest(BaseModel):
    claim_code: str


class RedeemResponse(BaseModel):
    success: bool
    message: str
    prize_name: Optional[str] = None
    activity_id: Optional[str] = None
    activity_name: Optional[str] = None
    user_name: Optional[str] = None
    status: Optional[WinnerStatus] = None


# 通用响应
class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    detail: str
