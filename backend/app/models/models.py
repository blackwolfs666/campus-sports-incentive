from sqlalchemy import Column, BigInteger, String, Integer, Text, DECIMAL, Date, DateTime, Enum, Boolean, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class PrizeType(enum.Enum):
    first = "first"
    second = "second"
    third = "third"
    honorable = "honorable"


class PeriodType(enum.Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    yearly = "yearly"


class PeriodStatus(enum.Enum):
    pending = "pending"
    active = "active"
    finished = "finished"


class WinnerStatus(enum.Enum):
    pending = "pending"
    claimed = "claimed"
    redeemed = "redeemed"


class PointsType(enum.Enum):
    prize = "prize"
    streak = "streak"
    challenge = "challenge"
    manual = "manual"


class ChallengeType(enum.Enum):
    department = "department"
    personal = "personal"


class AdminRole(enum.Enum):
    super_admin = "super"
    admin = "admin"
    operator = "operator"


class User(Base):
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="用户ID")
    openid = Column(String(100), nullable=False, unique=True, comment="微信OpenID")
    union_id = Column(String(100), nullable=True, comment="微信UnionID")
    name = Column(String(50), nullable=False, comment="姓名")
    avatar = Column(String(500), nullable=True, comment="头像URL")
    phone = Column(String(20), nullable=True, comment="手机号")
    department_id = Column(BigInteger, ForeignKey("departments.id"), nullable=True, comment="所属部门ID")
    employee_id = Column(String(50), nullable=True, unique=True, comment="工号/学号(CAS)")
    cas_binded = Column(Boolean, default=False, nullable=False, comment="是否已绑定CAS")
    edu_person_type = Column(String(20), nullable=True, comment="身份类型")
    total_steps = Column(BigInteger, default=0, comment="累计步数")
    total_distance = Column(DECIMAL(10, 2), default=0.00, comment="累计里程(km)")
    streak_days = Column(Integer, default=0, comment="连续达标天数")
    daily_step_goal = Column(Integer, nullable=True, comment="User daily step goal")
    daily_goal_reset_date = Column(Date, nullable=True, comment="Daily goal reset date")
    health_level = Column(Integer, default=1, comment="健康等级")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    department = relationship("Department", back_populates="users")
    step_records = relationship("StepRecord", back_populates="user")
    winners = relationship("Winner", back_populates="user")
    checkin_posts = relationship("CheckinPost", back_populates="user")
    
    __table_args__ = (
        Index("idx_openid", "openid"),
        Index("idx_department", "department_id"),
        Index("idx_employee_id", "employee_id"),
    )


class Department(Base):
    __tablename__ = "departments"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="部门ID")
    name = Column(String(100), nullable=False, unique=True, comment="部门名称")
    icon = Column(String(100), nullable=True, comment="图标")
    sort_order = Column(Integer, default=0, comment="排序")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    
    users = relationship("User", back_populates="department")


class StepRecord(Base):
    __tablename__ = "step_records"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="记录ID")
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, comment="用户ID")
    steps = Column(Integer, nullable=False, default=0, comment="步数")
    distance = Column(DECIMAL(10, 2), default=0.00, comment="里程(km)")
    record_date = Column(Date, nullable=False, comment="记录日期")
    target_steps = Column(Integer, nullable=True, comment="Daily goal snapshot")
    source = Column(String(20), default="wechat", comment="数据来源")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    user = relationship("User", back_populates="step_records")
    
    __table_args__ = (
        UniqueConstraint("user_id", "record_date", name="uk_user_date"),
        Index("idx_user", "user_id"),
        Index("idx_date", "record_date"),
    )


class Prize(Base):
    __tablename__ = "prizes"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="奖品ID")
    name = Column(String(100), nullable=False, comment="奖品名称")
    description = Column(Text, nullable=True, comment="奖品描述")
    image_url = Column(String(500), nullable=True, comment="奖品图片")
    prize_type = Column(Enum(PrizeType), default=PrizeType.honorable, comment="奖品等级")
    stock = Column(Integer, default=0, comment="库存数量")
    points = Column(Integer, default=0, comment="奖励积分")
    sort_order = Column(Integer, default=0, comment="排序")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    winners = relationship("Winner", back_populates="prize")
    
    __table_args__ = (
        Index("idx_type", "prize_type"),
        Index("idx_active", "is_active"),
    )


class Period(Base):
    __tablename__ = "periods"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="周期ID")
    name = Column(String(100), nullable=False, comment="周期名称")
    period_type = Column(Enum(PeriodType), default=PeriodType.weekly, comment="周期类型")
    start_date = Column(Date, nullable=False, comment="开始日期")
    end_date = Column(Date, nullable=False, comment="结束日期")
    status = Column(Enum(PeriodStatus), default=PeriodStatus.pending, comment="状态")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    
    winners = relationship("Winner", back_populates="period")
    
    __table_args__ = (
        Index("idx_type", "period_type"),
        Index("idx_status", "status"),
        Index("idx_date_range", "start_date", "end_date"),
    )


class Winner(Base):
    __tablename__ = "winners"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="获奖ID")
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, comment="用户ID")
    activity_id = Column(String(100), ForeignKey("activities.id"), nullable=True, comment="活动ID")
    prize_id = Column(BigInteger, ForeignKey("prizes.id"), nullable=False, comment="奖品ID")
    period_id = Column(BigInteger, ForeignKey("periods.id"), nullable=False, comment="周期ID")
    rank = Column(Integer, default=0, comment="排名")
    steps = Column(Integer, default=0, comment="获奖时步数")
    status = Column(Enum(WinnerStatus), default=WinnerStatus.pending, comment="状态")
    claim_code = Column(String(20), nullable=True, comment="兑换码")
    claim_qrcode = Column(String(500), nullable=True, comment="二维码URL")
    claim_deadline = Column(DateTime, nullable=True, comment="兑换截止时间")
    claimed_at = Column(DateTime, nullable=True, comment="领取时间")
    redeemed_at = Column(DateTime, nullable=True, comment="兑换时间")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    user = relationship("User", back_populates="winners")
    prize = relationship("Prize", back_populates="winners")
    period = relationship("Period", back_populates="winners")
    
    __table_args__ = (
        UniqueConstraint("user_id", "period_id", "prize_id", name="uk_user_period_prize"),
        Index("idx_user", "user_id"),
        Index("idx_activity", "activity_id"),
        Index("idx_period", "period_id"),
        Index("idx_status", "status"),
        Index("idx_claim_code", "claim_code"),
    )


class PointsRecord(Base):
    __tablename__ = "points_records"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="记录ID")
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    points = Column(Integer, nullable=False, comment="积分变动")
    type = Column(Enum(PointsType), default=PointsType.manual, comment="类型")
    reference_id = Column(BigInteger, nullable=True, comment="关联ID")
    description = Column(String(200), nullable=True, comment="描述")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    
    __table_args__ = (
        Index("idx_user", "user_id"),
        Index("idx_type", "type"),
    )


class Challenge(Base):
    __tablename__ = "challenges"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="挑战ID")
    title = Column(String(100), nullable=False, comment="挑战标题")
    description = Column(Text, nullable=True, comment="挑战描述")
    challenge_type = Column(Enum(ChallengeType), default=ChallengeType.department, comment="挑战类型")
    target_steps = Column(Integer, default=10000, comment="目标步数")
    start_date = Column(Date, nullable=False, comment="开始日期")
    end_date = Column(Date, nullable=False, comment="结束日期")
    status = Column(Enum(PeriodStatus), default=PeriodStatus.pending, comment="状态")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    
    participants = relationship("ChallengeParticipant", back_populates="challenge")
    
    __table_args__ = (
        Index("idx_status", "status"),
        Index("idx_date_range", "start_date", "end_date"),
    )


class ChallengeParticipant(Base):
    __tablename__ = "challenge_participants"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="参与ID")
    challenge_id = Column(BigInteger, ForeignKey("challenges.id"), nullable=False, comment="挑战ID")
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    department_id = Column(BigInteger, nullable=True, comment="部门ID")
    total_steps = Column(Integer, default=0, comment="累计步数")
    joined_at = Column(DateTime, server_default=func.now(), comment="参与时间")
    
    challenge = relationship("Challenge", back_populates="participants")
    
    __table_args__ = (
        UniqueConstraint("challenge_id", "user_id", name="uk_challenge_user"),
        Index("idx_challenge", "challenge_id"),
        Index("idx_department", "department_id"),
    )


class Setting(Base):
    __tablename__ = "settings"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="配置ID")
    setting_key = Column(String(100), nullable=False, unique=True, comment="配置键")
    setting_value = Column(Text, nullable=True, comment="配置值")
    description = Column(String(200), nullable=True, comment="配置描述")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")


class Admin(Base):
    __tablename__ = "admins"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="管理员ID")
    username = Column(String(50), nullable=False, unique=True, comment="用户名")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    name = Column(String(50), nullable=False, comment="姓名")
    role = Column(Enum(AdminRole), default=AdminRole.operator, comment="角色")
    is_active = Column(Boolean, default=True, comment="是否启用")
    last_login_at = Column(DateTime, nullable=True, comment="最后登录时间")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")


class ActivityParticipant(Base):
    __tablename__ = "activity_participants"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="活动参与ID")
    activity_id = Column(String(100), nullable=False, comment="活动ID")
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, comment="用户ID")
    joined_at = Column(DateTime, server_default=func.now(), comment="参与时间")

    __table_args__ = (
        UniqueConstraint("activity_id", "user_id", name="uk_activity_user"),
        Index("idx_activity_participant_activity", "activity_id"),
        Index("idx_activity_participant_user", "user_id"),
    )


class Activity(Base):
    __tablename__ = "activities"

    id = Column(String(100), primary_key=True, comment="活动ID")
    name = Column(String(100), nullable=False, comment="活动名称")
    status = Column(String(20), nullable=False, default="active", comment="状态")
    status_text = Column(String(20), nullable=False, default="进行中", comment="状态文案")
    cover_tone = Column(String(20), nullable=False, default="green", comment="封面色调")
    start_date = Column(DateTime, nullable=False, comment="活动开始时间")
    end_date = Column(DateTime, nullable=False, comment="活动结束时间")
    signup_start = Column(DateTime, nullable=False, comment="报名开始时间")
    signup_end = Column(DateTime, nullable=False, comment="报名结束时间")
    target_group = Column(String(100), nullable=False, default="全体学生", comment="面向对象")
    participants = Column(Integer, nullable=False, default=0, comment="展示参与人数")
    max_participants = Column(Integer, nullable=False, default=0, comment="人数上限")
    rules_short = Column(String(100), nullable=False, default="", comment="规则摘要")
    reward_short = Column(String(100), nullable=False, default="", comment="奖励摘要")
    description = Column(Text, nullable=True, comment="活动描述")
    tags_json = Column(Text, nullable=True, comment="标签JSON")
    rules_json = Column(Text, nullable=True, comment="规则JSON")
    prizes_json = Column(Text, nullable=True, comment="奖品JSON")
    poster_url = Column(String(500), nullable=True, comment="活动海报")
    scope_text = Column(String(200), nullable=True, comment="活动范围")
    score_rule_json = Column(Text, nullable=True, comment="积分规则JSON")
    award_rules_json = Column(Text, nullable=True, comment="获奖规则JSON")
    checkin_post_visible = Column(Boolean, default=True, nullable=False, comment="打卡动态是否可见")
    created_by = Column(BigInteger, ForeignKey("users.id"), nullable=True, comment="创建人用户ID")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    scope_department_ids_json = Column(Text, nullable=True, comment="Activity scope department IDs JSON")

    __table_args__ = (
        Index("idx_activity_status", "status"),
        Index("idx_activity_date_range", "start_date", "end_date"),
    )


class ActivityPrize(Base):
    __tablename__ = "activity_prizes"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="活动奖品ID")
    activity_id = Column(String(100), ForeignKey("activities.id"), nullable=False, comment="活动ID")
    prize_id = Column(BigInteger, ForeignKey("prizes.id"), nullable=False, comment="奖品ID")
    rank_label = Column(String(100), nullable=False, default="", comment="名次/规则标签")
    rank_start = Column(Integer, nullable=True, comment="起始名次")
    rank_end = Column(Integer, nullable=True, comment="结束名次")
    quantity = Column(Integer, nullable=True, comment="奖品数量")
    award_rule_type = Column(String(50), nullable=True, comment="Bound award rule type")
    image_url = Column(String(500), nullable=True, comment="活动奖品展示图片")
    sort_order = Column(Integer, nullable=False, default=0, comment="排序")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    __table_args__ = (
        Index("idx_activity_prize_activity", "activity_id"),
        Index("idx_activity_prize_prize", "prize_id"),
        Index("idx_activity_prize_sort", "activity_id", "sort_order"),
    )


class ActivityAdmin(Base):
    __tablename__ = "activity_admins"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="活动管理员ID")
    activity_id = Column(String(100), ForeignKey("activities.id"), nullable=False, comment="活动ID")
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, comment="用户ID")
    role = Column(String(20), nullable=False, default="admin", comment="owner/admin")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")

    __table_args__ = (
        UniqueConstraint("activity_id", "user_id", name="uk_activity_admin_user"),
        Index("idx_activity_admin_activity", "activity_id"),
        Index("idx_activity_admin_user", "user_id"),
    )


class CheckinPost(Base):
    __tablename__ = "checkin_posts"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="打卡动态ID")
    activity_id = Column(String(100), nullable=False, comment="活动ID")
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, comment="用户ID")
    content = Column(Text, nullable=True, comment="想说的话")
    image_urls = Column(Text, nullable=True, comment="展示风采图片，JSON数组")
    steps = Column(Integer, nullable=False, default=0, comment="今日打卡步数")
    streak_days = Column(Integer, nullable=False, default=0, comment="连续打卡天数")
    record_date = Column(Date, nullable=False, comment="打卡日期")
    cheer_count = Column(Integer, nullable=False, default=0, comment="为TA加油数")
    is_visible = Column(Boolean, default=True, nullable=False, comment="是否可见")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    user = relationship("User", back_populates="checkin_posts")
    likes = relationship("CheckinLike", back_populates="post")

    __table_args__ = (
        Index("idx_checkin_activity", "activity_id"),
        Index("idx_checkin_user", "user_id"),
        Index("idx_checkin_date", "record_date"),
        Index("idx_checkin_visible", "is_visible"),
    )


class CheckinLike(Base):
    __tablename__ = "checkin_likes"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="加油记录ID")
    post_id = Column(BigInteger, ForeignKey("checkin_posts.id"), nullable=False, comment="动态ID")
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, comment="用户ID")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")

    post = relationship("CheckinPost", back_populates="likes")

    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="uk_checkin_like_post_user"),
        Index("idx_checkin_like_post", "post_id"),
        Index("idx_checkin_like_user", "user_id"),
    )
