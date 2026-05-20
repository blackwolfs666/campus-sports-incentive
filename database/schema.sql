-- 邮青步纪数据库初始化脚本
-- 运行顺序：
-- 1. 执行本文件创建库表和基础配置
-- 2. 执行“插入模拟数据.sql”写入可演示数据

CREATE DATABASE IF NOT EXISTS step_counter
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE step_counter;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS departments (
  id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '部门ID',
  name VARCHAR(100) NOT NULL UNIQUE COMMENT '部门名称',
  icon VARCHAR(100) NULL COMMENT '图标',
  sort_order INT DEFAULT 0 COMMENT '排序',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  INDEX idx_department_sort (sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS users (
  id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
  openid VARCHAR(100) NOT NULL UNIQUE COMMENT '微信OpenID',
  union_id VARCHAR(100) NULL COMMENT '微信UnionID',
  name VARCHAR(50) NOT NULL COMMENT '姓名',
  avatar VARCHAR(500) NULL COMMENT '头像URL',
  phone VARCHAR(20) NULL COMMENT '手机号',
  department_id BIGINT NULL COMMENT '所属部门ID',
  total_steps BIGINT DEFAULT 0 COMMENT '累计步数',
  total_distance DECIMAL(10,2) DEFAULT 0.00 COMMENT '累计里程(km)',
  streak_days INT DEFAULT 0 COMMENT '连续达标天数',
  health_level INT DEFAULT 1 COMMENT '健康等级',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  CONSTRAINT fk_users_department FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL,
  INDEX idx_openid (openid),
  INDEX idx_department (department_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS step_records (
  id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '记录ID',
  user_id BIGINT NOT NULL COMMENT '用户ID',
  steps INT NOT NULL DEFAULT 0 COMMENT '步数',
  distance DECIMAL(10,2) DEFAULT 0.00 COMMENT '里程(km)',
  record_date DATE NOT NULL COMMENT '记录日期',
  source VARCHAR(20) DEFAULT 'wechat' COMMENT '数据来源',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  CONSTRAINT fk_step_records_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  UNIQUE KEY uk_user_date (user_id, record_date),
  INDEX idx_user (user_id),
  INDEX idx_date (record_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS prizes (
  id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '奖品ID',
  name VARCHAR(100) NOT NULL COMMENT '奖品名称',
  description TEXT NULL COMMENT '奖品描述',
  image_url VARCHAR(500) NULL COMMENT '奖品图片',
  prize_type ENUM('first', 'second', 'third', 'honorable') DEFAULT 'honorable' COMMENT '奖品等级',
  stock INT DEFAULT 0 COMMENT '库存数量',
  points INT DEFAULT 0 COMMENT '奖励积分',
  sort_order INT DEFAULT 0 COMMENT '排序',
  is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  INDEX idx_type (prize_type),
  INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS periods (
  id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '周期ID',
  name VARCHAR(100) NOT NULL COMMENT '周期名称',
  period_type ENUM('daily', 'weekly', 'monthly', 'yearly') DEFAULT 'weekly' COMMENT '周期类型',
  start_date DATE NOT NULL COMMENT '开始日期',
  end_date DATE NOT NULL COMMENT '结束日期',
  status ENUM('pending', 'active', 'finished') DEFAULT 'pending' COMMENT '状态',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  INDEX idx_type (period_type),
  INDEX idx_status (status),
  INDEX idx_date_range (start_date, end_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS winners (
  id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '获奖ID',
  user_id BIGINT NOT NULL COMMENT '用户ID',
  activity_id VARCHAR(100) NULL COMMENT '活动ID',
  prize_id BIGINT NOT NULL COMMENT '奖品ID',
  period_id BIGINT NOT NULL COMMENT '周期ID',
  `rank` INT DEFAULT 0 COMMENT '排名',
  steps INT DEFAULT 0 COMMENT '获奖时步数',
  status ENUM('pending', 'claimed', 'redeemed') DEFAULT 'pending' COMMENT '状态',
  claim_code VARCHAR(20) NULL COMMENT '兑换码',
  claim_qrcode VARCHAR(500) NULL COMMENT '二维码URL',
  claim_deadline DATETIME NULL COMMENT '兑换截止时间',
  claimed_at DATETIME NULL COMMENT '领取时间',
  redeemed_at DATETIME NULL COMMENT '兑换时间',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  CONSTRAINT fk_winners_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_winners_prize FOREIGN KEY (prize_id) REFERENCES prizes(id) ON DELETE CASCADE,
  CONSTRAINT fk_winners_period FOREIGN KEY (period_id) REFERENCES periods(id) ON DELETE CASCADE,
  UNIQUE KEY uk_user_period_prize (user_id, period_id, prize_id),
  INDEX idx_user (user_id),
  INDEX idx_winner_activity (activity_id),
  INDEX idx_period (period_id),
  INDEX idx_status (status),
  INDEX idx_claim_code (claim_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS points_records (
  id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '记录ID',
  user_id BIGINT NOT NULL COMMENT '用户ID',
  points INT NOT NULL COMMENT '积分变动',
  type ENUM('prize', 'streak', 'challenge', 'manual') DEFAULT 'manual' COMMENT '类型',
  reference_id BIGINT NULL COMMENT '关联ID',
  description VARCHAR(200) NULL COMMENT '描述',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  INDEX idx_user (user_id),
  INDEX idx_type (type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS challenges (
  id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '挑战ID',
  title VARCHAR(100) NOT NULL COMMENT '挑战标题',
  description TEXT NULL COMMENT '挑战描述',
  challenge_type ENUM('department', 'personal') DEFAULT 'department' COMMENT '挑战类型',
  target_steps INT DEFAULT 10000 COMMENT '目标步数',
  start_date DATE NOT NULL COMMENT '开始日期',
  end_date DATE NOT NULL COMMENT '结束日期',
  status ENUM('pending', 'active', 'finished') DEFAULT 'pending' COMMENT '状态',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  INDEX idx_status (status),
  INDEX idx_date_range (start_date, end_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS challenge_participants (
  id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '参与ID',
  challenge_id BIGINT NOT NULL COMMENT '挑战ID',
  user_id BIGINT NOT NULL COMMENT '用户ID',
  department_id BIGINT NULL COMMENT '部门ID',
  total_steps INT DEFAULT 0 COMMENT '累计步数',
  joined_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '参与时间',
  CONSTRAINT fk_challenge_participants_challenge FOREIGN KEY (challenge_id) REFERENCES challenges(id) ON DELETE CASCADE,
  UNIQUE KEY uk_challenge_user (challenge_id, user_id),
  INDEX idx_challenge (challenge_id),
  INDEX idx_department (department_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS activities (
  id VARCHAR(100) PRIMARY KEY COMMENT '活动ID',
  name VARCHAR(100) NOT NULL COMMENT '活动名称',
  status VARCHAR(20) NOT NULL DEFAULT 'signup' COMMENT '状态：signup=报名中，active=进行中，ended=已结束',
  status_text VARCHAR(20) NOT NULL DEFAULT '进行中' COMMENT '状态文案',
  cover_tone VARCHAR(20) NOT NULL DEFAULT 'green' COMMENT '封面色调',
  start_date DATE NOT NULL COMMENT '开始日期',
  end_date DATE NOT NULL COMMENT '结束日期',
  signup_start DATE NOT NULL COMMENT '报名开始日期',
  signup_end DATE NOT NULL COMMENT '报名结束日期',
  target_group VARCHAR(100) NOT NULL DEFAULT '全体学生' COMMENT '面向对象',
  participants INT NOT NULL DEFAULT 0 COMMENT '展示参与人数',
  max_participants INT NOT NULL DEFAULT 0 COMMENT '人数上限',
  rules_short VARCHAR(100) NOT NULL DEFAULT '' COMMENT '规则摘要',
  reward_short VARCHAR(100) NOT NULL DEFAULT '' COMMENT '奖励摘要',
  description TEXT NULL COMMENT '活动描述',
  tags_json TEXT NULL COMMENT '标签JSON',
  rules_json TEXT NULL COMMENT '规则JSON',
  prizes_json TEXT NULL COMMENT '奖品JSON',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  INDEX idx_activity_status (status),
  INDEX idx_activity_date_range (start_date, end_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS activity_participants (
  id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '活动参与ID',
  activity_id VARCHAR(100) NOT NULL COMMENT '活动ID',
  user_id BIGINT NOT NULL COMMENT '用户ID',
  joined_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '参与时间',
  CONSTRAINT fk_activity_participants_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  UNIQUE KEY uk_activity_user (activity_id, user_id),
  INDEX idx_activity_participant_activity (activity_id),
  INDEX idx_activity_participant_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS settings (
  id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '配置ID',
  setting_key VARCHAR(100) NOT NULL UNIQUE COMMENT '配置键',
  setting_value TEXT NULL COMMENT '配置值',
  description VARCHAR(200) NULL COMMENT '配置描述',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS admins (
  id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '管理员ID',
  username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
  password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
  name VARCHAR(50) NOT NULL COMMENT '姓名',
  role ENUM('super', 'admin', 'operator') DEFAULT 'operator' COMMENT '角色',
  is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
  last_login_at DATETIME NULL COMMENT '最后登录时间',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;
