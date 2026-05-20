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
