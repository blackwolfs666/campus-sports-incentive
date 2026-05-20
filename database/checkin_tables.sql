USE step_counter;

CREATE TABLE IF NOT EXISTS checkin_posts (
  id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '打卡动态ID',
  activity_id VARCHAR(100) NOT NULL COMMENT '活动ID',
  user_id BIGINT NOT NULL COMMENT '用户ID',
  content TEXT NULL COMMENT '想说的话',
  image_urls TEXT NULL COMMENT '展示风采图片，JSON数组',
  steps INT NOT NULL DEFAULT 0 COMMENT '今日打卡步数',
  streak_days INT NOT NULL DEFAULT 0 COMMENT '连续打卡天数',
  record_date DATE NOT NULL COMMENT '打卡日期',
  cheer_count INT NOT NULL DEFAULT 0 COMMENT '为TA加油数',
  is_visible TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否可见',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  KEY idx_checkin_activity (activity_id),
  KEY idx_checkin_user (user_id),
  KEY idx_checkin_date (record_date),
  KEY idx_checkin_visible (is_visible),
  CONSTRAINT fk_checkin_posts_user FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='活动打卡动态';

CREATE TABLE IF NOT EXISTS checkin_likes (
  id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '加油记录ID',
  post_id BIGINT NOT NULL COMMENT '动态ID',
  user_id BIGINT NOT NULL COMMENT '用户ID',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  UNIQUE KEY uk_checkin_like_post_user (post_id, user_id),
  KEY idx_checkin_like_post (post_id),
  KEY idx_checkin_like_user (user_id),
  CONSTRAINT fk_checkin_likes_post FOREIGN KEY (post_id) REFERENCES checkin_posts(id) ON DELETE CASCADE,
  CONSTRAINT fk_checkin_likes_user FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='打卡动态加油记录';
