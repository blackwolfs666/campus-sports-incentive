USE step_counter;

ALTER TABLE activities
  ADD COLUMN IF NOT EXISTS poster_url VARCHAR(500) NULL COMMENT '活动海报',
  ADD COLUMN IF NOT EXISTS scope_text VARCHAR(200) NULL COMMENT '活动范围',
  ADD COLUMN IF NOT EXISTS score_rule_json TEXT NULL COMMENT '积分规则JSON',
  ADD COLUMN IF NOT EXISTS award_rules_json TEXT NULL COMMENT '获奖规则JSON',
  ADD COLUMN IF NOT EXISTS checkin_post_visible TINYINT(1) NOT NULL DEFAULT 1 COMMENT '打卡动态是否可见',
  ADD COLUMN IF NOT EXISTS created_by BIGINT NULL COMMENT '创建人用户ID';

ALTER TABLE winners
  ADD COLUMN IF NOT EXISTS activity_id VARCHAR(100) NULL COMMENT 'Activity ID';

CREATE TABLE IF NOT EXISTS activity_admins (
  id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '活动管理员ID',
  activity_id VARCHAR(100) NOT NULL COMMENT '活动ID',
  user_id BIGINT NOT NULL COMMENT '用户ID',
  role VARCHAR(20) NOT NULL DEFAULT 'admin' COMMENT 'owner/admin',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  UNIQUE KEY uk_activity_admin_user (activity_id, user_id),
  KEY idx_activity_admin_activity (activity_id),
  KEY idx_activity_admin_user (user_id),
  CONSTRAINT fk_activity_admin_activity FOREIGN KEY (activity_id) REFERENCES activities(id),
  CONSTRAINT fk_activity_admin_user FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS activity_prizes (
  id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '活动奖品ID',
  activity_id VARCHAR(100) NOT NULL COMMENT '活动ID',
  prize_id BIGINT NOT NULL COMMENT '奖品ID',
  rank_label VARCHAR(100) NOT NULL DEFAULT '' COMMENT '名次/规则标签',
  rank_start INT NULL COMMENT '起始名次',
  rank_end INT NULL COMMENT '结束名次',
  quantity INT NULL COMMENT '奖品数量',
  sort_order INT NOT NULL DEFAULT 0 COMMENT '排序',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  UNIQUE KEY uk_activity_prize_sort (activity_id, sort_order),
  KEY idx_activity_prize_activity (activity_id),
  KEY idx_activity_prize_prize (prize_id),
  CONSTRAINT fk_activity_prizes_activity FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE,
  CONSTRAINT fk_activity_prizes_prize FOREIGN KEY (prize_id) REFERENCES prizes(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
