-- 插入模拟数据脚本
-- 运行前请确保已执行数据库创建脚本

USE step_counter;

-- 插入基础部门
INSERT INTO departments (id, name, icon, sort_order) VALUES
(1, '计算机科学学院', 'school', 1),
(2, '资深学者', 'auto_stories', 2),
(3, '优秀导师', 'history_edu', 3),
(4, '生物系', 'potted_plant', 4),
(5, '物理系', 'bolt', 5),
(6, '数学系', 'flag', 6)
ON DUPLICATE KEY UPDATE
  name=VALUES(name),
  icon=VALUES(icon),
  sort_order=VALUES(sort_order);

-- 插入系统配置
INSERT INTO settings (setting_key, setting_value, description) VALUES
('daily_step_goal', '10000', '每日目标步数'),
('redeem_deadline_days', '30', '奖品领取后的兑换有效天数')
ON DUPLICATE KEY UPDATE
  setting_value=VALUES(setting_value),
  description=VALUES(description);

-- 插入奖品
INSERT INTO prizes (id, name, description, image_url, prize_type, stock, points, sort_order, is_active) VALUES
(1, '定制学术保温杯', '限量木纹设计', NULL, 'first', 10, 1000, 1, TRUE),
(2, '博雅文具礼盒', '含钢笔与手工笔记本', NULL, 'second', 20, 700, 2, TRUE),
(3, '校园咖啡季卡', '全校门店通用', NULL, 'third', 30, 500, 3, TRUE),
(4, '数字勋章与积分', '额外奖励 500 积分', NULL, 'honorable', 100, 500, 4, TRUE)
ON DUPLICATE KEY UPDATE
  name=VALUES(name),
  description=VALUES(description),
  prize_type=VALUES(prize_type),
  stock=VALUES(stock),
  points=VALUES(points),
  sort_order=VALUES(sort_order),
  is_active=VALUES(is_active);

-- 插入测试用户
INSERT INTO users (id, openid, name, avatar, department_id, total_steps, total_distance, streak_days, health_level) VALUES
(1, 'test_openid_1', 'Bloom 博士', NULL, 1, 158000, 110.6, 15, 20),
(2, 'test_openid_2', 'Greene 教授', NULL, 2, 124000, 86.8, 12, 18),
(3, 'test_openid_3', 'Birch 老师', NULL, 3, 109000, 76.3, 10, 15),
(4, 'test_openid_4', 'Samuel Oak 教授', NULL, 4, 94320, 66.0, 8, 12),
(5, 'test_openid_5', 'Sarah Willow 博士', NULL, 5, 89010, 62.3, 7, 11),
(6, 'test_openid_6', 'Julian Elm 教授', NULL, 6, 81120, 56.8, 6, 10),
(7, 'test_openid_7', 'Parker 教授', NULL, 1, 43280, 30.3, 4, 8)
ON DUPLICATE KEY UPDATE name=VALUES(name);

-- 晚霞健步赛排行榜演示用户
INSERT INTO users (id, openid, name, avatar, department_id, total_steps, total_distance, streak_days, health_level) VALUES
(101, 'evening_rank_openid_01', 'Evening Runner 01', NULL, 1, 146800, 102.76, 8, 12),
(102, 'evening_rank_openid_02', 'Evening Runner 02', NULL, 2, 139500, 97.65, 8, 12),
(103, 'evening_rank_openid_03', 'Evening Runner 03', NULL, 3, 128300, 89.81, 8, 12),
(104, 'evening_rank_openid_04', 'Evening Runner 04', NULL, 4, 116900, 81.83, 8, 12),
(105, 'evening_rank_openid_05', 'Evening Runner 05', NULL, 5, 104200, 72.94, 8, 12),
(106, 'evening_rank_openid_06', 'Evening Runner 06', NULL, 6, 93700, 65.59, 8, 12),
(107, 'evening_rank_openid_07', 'Evening Runner 07', NULL, 1, 81200, 56.84, 8, 12),
(108, 'evening_rank_openid_08', 'Evening Runner 08', NULL, 2, 74500, 52.15, 8, 12),
(109, 'evening_rank_openid_09', 'Evening Runner 09', NULL, 3, 68100, 47.67, 8, 12),
(110, 'evening_rank_openid_10', 'Evening Runner 10', NULL, 4, 60200, 42.14, 8, 12)
ON DUPLICATE KEY UPDATE
  name=VALUES(name),
  department_id=VALUES(department_id),
  total_steps=VALUES(total_steps),
  total_distance=VALUES(total_distance),
  streak_days=VALUES(streak_days),
  health_level=VALUES(health_level);

CREATE TABLE IF NOT EXISTS activities (
  id VARCHAR(100) PRIMARY KEY COMMENT '活动ID',
  name VARCHAR(100) NOT NULL COMMENT '活动名称',
  status VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT '状态',
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO activities (
  id, name, status, status_text, cover_tone, start_date, end_date, signup_start, signup_end,
  target_group, participants, max_participants, rules_short, reward_short, description,
  tags_json, rules_json, prizes_json
) VALUES
('campus-spring-2026', '春季步数接力挑战赛', 'active', '进行中', 'green', '2026-03-01', '2026-05-31', '2026-03-01', '2026-03-15', '全体本科生', 328, 500, '每日10000步 / 积分排名制', '前10名可领奖', '加入全校运动热潮，用脚步迈向胜利。', '["校园活动","高能挑战"]', '["每日步数至少达到 10,000 步，至少坚持 20 天。","积分排名前 10 名可获得专属奖品。","每天通过首页同步微信运动步数，系统保留最新一次同步结果。"]', '[{"id":"p1","rank":"第1名","name":"校园咖啡季卡","image":"/images/prizes/coffee-card.svg"},{"id":"p2","rank":"第2-3名","name":"校园书城50元券","image":"/images/prizes/stationery.svg"},{"id":"p3","rank":"第4-10名","name":"定制运动水壶","image":"/images/prizes/thermos.svg"}]'),
('library-marathon-2026', '图书馆马拉松周', 'signup', '报名中', 'blue', '2026-06-01', '2026-06-30', '2026-05-01', '2026-05-31', '全校师生', 890, 1000, '每日8000步 / 打卡满7天', '参与即有奖', '从宿舍到图书馆，把学习路线变成健康路线。', '["全校活动","打卡挑战"]', '["每日步数至少达到 8,000 步。","连续打卡满 7 天可获得完成奖励。","积分前 20 名可获得文创奖品。"]', '[{"id":"p4","rank":"前20名","name":"博雅文具礼盒","image":"/images/prizes/stationery.svg"},{"id":"p5","rank":"完成任务","name":"图书馆借阅积分","image":"/images/prizes/medal.svg"}]'),
('evening-walk-2026', '晚霞健步赛', 'active', '进行中', 'orange', '2026-04-10', '2026-05-31', '2026-04-05', '2026-04-10', '全体学生', 2105, 3000, '每日6000步 / 每步得积分', '前30名可领奖', '傍晚散步也能累计积分，轻量参与校园运动。', '["休闲活动","全民健步"]', '["每日步数至少达到 6,000 步。","每 100 步计 1 积分。","积分前 30 名可获得相应奖品。"]', '[{"id":"p6","rank":"第1-10名","name":"健身房月卡","image":"/images/prizes/medal.svg"},{"id":"p7","rank":"第11-30名","name":"运动毛巾","image":"/images/prizes/thermos.svg"}]'),
('lab-health-2026', '实验楼健康挑战', 'active', '进行中', 'blue', '2026-05-01', '2026-05-31', '2026-04-20', '2026-04-30', '理工类学院学生', 420, 800, '每日7000步 / 总步数排名', '前20名可领奖', '围绕教学楼与实验楼路线开展健步挑战，鼓励课间主动运动。', '["学院活动","健步挑战"]', '["活动期间每日步数达到 7,000 步计为有效打卡。","总步数排名前 20 名可获得活动奖品。","仅已报名用户可参与排名和发布打卡动态。"]', '[{"id":"p10","rank":"前10名","name":"校园运动礼包","image":"/images/prizes/medal.svg"},{"id":"p11","rank":"第11-20名","name":"定制运动水壶","image":"/images/prizes/thermos.svg"}]'),
('green-campus-2026', '绿色校园健走季', 'active', '进行中', 'green', '2026-05-05', '2026-06-05', '2026-04-20', '2026-05-04', '全校学生', 760, 1200, '每日9000步 / 积分排名制', '前15名可领奖', '以校园绿色路线为主题，鼓励学生在日常通勤中完成运动目标。', '["校园活动","绿色健走"]', '["每日步数达到 9,000 步可获得活动积分。","活动按总积分排名，前 15 名可获得奖品。","活动期间可在详情页同步步数并查看排名。"]', '[{"id":"p12","rank":"第1名","name":"校园咖啡季卡","image":"/images/prizes/coffee-card.svg"},{"id":"p13","rank":"第2-15名","name":"运动文创套装","image":"/images/prizes/stationery.svg"}]'),
('winter-run-2026', '冬季晨跑挑战赛', 'ended', '已结束', 'gray', '2025-12-01', '2026-01-31', '2025-11-25', '2025-11-30', '全体本科生', 560, 600, '每日8000步 / 积分排名制', '前15名可领奖', '历史活动展示数据，活动已结束。', '["校园活动","冬季挑战"]', '["活动已结束，仅用于历史数据展示。","获奖记录以我的奖品页面为准。"]', '[{"id":"p8","rank":"第1-5名","name":"校园咖啡季卡","image":"/images/prizes/coffee-card.svg"},{"id":"p9","rank":"第6-15名","name":"定制保温杯","image":"/images/prizes/thermos.svg"}]')
ON DUPLICATE KEY UPDATE
  name=VALUES(name),
  status=VALUES(status),
  status_text=VALUES(status_text),
  cover_tone=VALUES(cover_tone),
  start_date=VALUES(start_date),
  end_date=VALUES(end_date),
  signup_start=VALUES(signup_start),
  signup_end=VALUES(signup_end),
  target_group=VALUES(target_group),
  participants=VALUES(participants),
  max_participants=VALUES(max_participants),
  rules_short=VALUES(rules_short),
  reward_short=VALUES(reward_short),
  description=VALUES(description),
  tags_json=VALUES(tags_json),
  rules_json=VALUES(rules_json),
  prizes_json=VALUES(prizes_json);

-- 插入活动参与演示数据。排行榜只依赖活动参与和步数/积分，不依赖打卡动态。
CREATE TABLE IF NOT EXISTS activity_participants (
  id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '活动参与ID',
  activity_id VARCHAR(100) NOT NULL COMMENT '活动ID',
  user_id BIGINT NOT NULL COMMENT '用户ID',
  joined_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '参与时间',
  UNIQUE KEY uk_activity_user (activity_id, user_id),
  INDEX idx_activity_participant_activity (activity_id),
  INDEX idx_activity_participant_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO activity_participants (activity_id, user_id) VALUES
('campus-spring-2026', 1),
('campus-spring-2026', 2),
('campus-spring-2026', 3),
('campus-spring-2026', 7),
('library-marathon-2026', 2),
('library-marathon-2026', 4),
('library-marathon-2026', 5),
('evening-walk-2026', 1),
('evening-walk-2026', 6),
('evening-walk-2026', 7),
('lab-health-2026', 2),
('lab-health-2026', 4),
('green-campus-2026', 3),
('green-campus-2026', 5),
('winter-run-2026', 3),
('winter-run-2026', 7)
ON DUPLICATE KEY UPDATE joined_at=joined_at;

INSERT INTO activity_participants (activity_id, user_id) VALUES
('evening-walk-2026', 101),
('evening-walk-2026', 102),
('evening-walk-2026', 103),
('evening-walk-2026', 104),
('evening-walk-2026', 105),
('evening-walk-2026', 106),
('evening-walk-2026', 107),
('evening-walk-2026', 108),
('evening-walk-2026', 109),
('evening-walk-2026', 110)
ON DUPLICATE KEY UPDATE joined_at=joined_at;

-- 插入当前周期
INSERT INTO periods (id, name, period_type, start_date, end_date, status) VALUES
(1, CONCAT(YEAR(CURDATE()), '年第', WEEK(CURDATE(), 1), '周'), 'weekly', DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY), DATE_ADD(DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY), INTERVAL 6 DAY), 'active')
ON DUPLICATE KEY UPDATE
  name=VALUES(name),
  start_date=VALUES(start_date),
  end_date=VALUES(end_date),
  status=VALUES(status);

-- 插入今日步数记录
INSERT INTO step_records (user_id, steps, distance, record_date, source) VALUES
(1, 15800, 11.06, CURDATE(), 'wechat'),
(2, 12400, 8.68, CURDATE(), 'wechat'),
(3, 10900, 7.63, CURDATE(), 'wechat'),
(4, 9432, 6.60, CURDATE(), 'wechat'),
(5, 8901, 6.23, CURDATE(), 'wechat'),
(6, 8112, 5.68, CURDATE(), 'wechat'),
(7, 4328, 3.03, CURDATE(), 'wechat')
ON DUPLICATE KEY UPDATE steps=VALUES(steps);

-- 插入昨日步数记录
INSERT INTO step_records (user_id, steps, distance, record_date, source) VALUES
(1, 14500, 10.15, DATE_SUB(CURDATE(), INTERVAL 1 DAY), 'wechat'),
(2, 13200, 9.24, DATE_SUB(CURDATE(), INTERVAL 1 DAY), 'wechat'),
(3, 11500, 8.05, DATE_SUB(CURDATE(), INTERVAL 1 DAY), 'wechat'),
(4, 8900, 6.23, DATE_SUB(CURDATE(), INTERVAL 1 DAY), 'wechat'),
(5, 9200, 6.44, DATE_SUB(CURDATE(), INTERVAL 1 DAY), 'wechat'),
(6, 7500, 5.25, DATE_SUB(CURDATE(), INTERVAL 1 DAY), 'wechat'),
(7, 5100, 3.57, DATE_SUB(CURDATE(), INTERVAL 1 DAY), 'wechat')
ON DUPLICATE KEY UPDATE steps=VALUES(steps);

-- 插入前天步数记录
INSERT INTO step_records (user_id, steps, distance, record_date, source) VALUES
(1, 16200, 11.34, DATE_SUB(CURDATE(), INTERVAL 2 DAY), 'wechat'),
(2, 11800, 8.26, DATE_SUB(CURDATE(), INTERVAL 2 DAY), 'wechat'),
(3, 10100, 7.07, DATE_SUB(CURDATE(), INTERVAL 2 DAY), 'wechat'),
(4, 10200, 7.14, DATE_SUB(CURDATE(), INTERVAL 2 DAY), 'wechat'),
(5, 8500, 5.95, DATE_SUB(CURDATE(), INTERVAL 2 DAY), 'wechat'),
(6, 9000, 6.30, DATE_SUB(CURDATE(), INTERVAL 2 DAY), 'wechat'),
(7, 6200, 4.34, DATE_SUB(CURDATE(), INTERVAL 2 DAY), 'wechat')
ON DUPLICATE KEY UPDATE steps=VALUES(steps);

-- 插入本周其他天数的步数记录
INSERT INTO step_records (user_id, steps, distance, record_date, source) VALUES
(1, 15000, 10.50, DATE_SUB(CURDATE(), INTERVAL 3 DAY), 'wechat'),
(2, 12000, 8.40, DATE_SUB(CURDATE(), INTERVAL 3 DAY), 'wechat'),
(3, 9800, 6.86, DATE_SUB(CURDATE(), INTERVAL 3 DAY), 'wechat'),
(4, 8700, 6.09, DATE_SUB(CURDATE(), INTERVAL 3 DAY), 'wechat'),
(5, 9100, 6.37, DATE_SUB(CURDATE(), INTERVAL 3 DAY), 'wechat'),
(6, 7800, 5.46, DATE_SUB(CURDATE(), INTERVAL 3 DAY), 'wechat'),
(7, 5500, 3.85, DATE_SUB(CURDATE(), INTERVAL 3 DAY), 'wechat')
ON DUPLICATE KEY UPDATE steps=VALUES(steps);

INSERT INTO step_records (user_id, steps, distance, record_date, source) VALUES
(1, 14000, 9.80, DATE_SUB(CURDATE(), INTERVAL 4 DAY), 'wechat'),
(2, 11000, 7.70, DATE_SUB(CURDATE(), INTERVAL 4 DAY), 'wechat'),
(3, 10500, 7.35, DATE_SUB(CURDATE(), INTERVAL 4 DAY), 'wechat'),
(4, 9500, 6.65, DATE_SUB(CURDATE(), INTERVAL 4 DAY), 'wechat'),
(5, 8800, 6.16, DATE_SUB(CURDATE(), INTERVAL 4 DAY), 'wechat'),
(6, 8200, 5.74, DATE_SUB(CURDATE(), INTERVAL 4 DAY), 'wechat'),
(7, 4800, 3.36, DATE_SUB(CURDATE(), INTERVAL 4 DAY), 'wechat')
ON DUPLICATE KEY UPDATE steps=VALUES(steps);

INSERT INTO step_records (user_id, steps, distance, record_date, source) VALUES
(1, 15500, 10.85, DATE_SUB(CURDATE(), INTERVAL 5 DAY), 'wechat'),
(2, 12800, 8.96, DATE_SUB(CURDATE(), INTERVAL 5 DAY), 'wechat'),
(3, 11200, 7.84, DATE_SUB(CURDATE(), INTERVAL 5 DAY), 'wechat'),
(4, 9100, 6.37, DATE_SUB(CURDATE(), INTERVAL 5 DAY), 'wechat'),
(5, 8700, 6.09, DATE_SUB(CURDATE(), INTERVAL 5 DAY), 'wechat'),
(6, 7600, 5.32, DATE_SUB(CURDATE(), INTERVAL 5 DAY), 'wechat'),
(7, 5200, 3.64, DATE_SUB(CURDATE(), INTERVAL 5 DAY), 'wechat')
ON DUPLICATE KEY UPDATE steps=VALUES(steps);

INSERT INTO step_records (user_id, steps, distance, record_date, source) VALUES
(1, 16000, 11.20, DATE_SUB(CURDATE(), INTERVAL 6 DAY), 'wechat'),
(2, 13500, 9.45, DATE_SUB(CURDATE(), INTERVAL 6 DAY), 'wechat'),
(3, 12000, 8.40, DATE_SUB(CURDATE(), INTERVAL 6 DAY), 'wechat'),
(4, 10000, 7.00, DATE_SUB(CURDATE(), INTERVAL 6 DAY), 'wechat'),
(5, 9300, 6.51, DATE_SUB(CURDATE(), INTERVAL 6 DAY), 'wechat'),
(6, 8000, 5.60, DATE_SUB(CURDATE(), INTERVAL 6 DAY), 'wechat'),
(7, 6000, 4.20, DATE_SUB(CURDATE(), INTERVAL 6 DAY), 'wechat')
ON DUPLICATE KEY UPDATE steps=VALUES(steps);

-- 晚霞健步赛排行榜演示步数
INSERT INTO step_records (user_id, steps, distance, record_date, source) VALUES
(101, 146800, 102.76, '2026-05-18', 'seed'),
(102, 139500, 97.65, '2026-05-18', 'seed'),
(103, 128300, 89.81, '2026-05-18', 'seed'),
(104, 116900, 81.83, '2026-05-18', 'seed'),
(105, 104200, 72.94, '2026-05-18', 'seed'),
(106, 93700, 65.59, '2026-05-18', 'seed'),
(107, 81200, 56.84, '2026-05-18', 'seed'),
(108, 74500, 52.15, '2026-05-18', 'seed'),
(109, 68100, 47.67, '2026-05-18', 'seed'),
(110, 60200, 42.14, '2026-05-18', 'seed')
ON DUPLICATE KEY UPDATE
  steps=VALUES(steps),
  distance=VALUES(distance),
  source=VALUES(source);

-- 按步数记录回填总积分榜数据：每 100 步计 1 分；重复执行只更新，不重复新增。
UPDATE points_records pr
JOIN step_records sr ON pr.user_id = sr.user_id
  AND pr.type = 'challenge'
  AND pr.reference_id = sr.id
SET
  pr.points = FLOOR(sr.steps / 100),
  pr.description = CONCAT(sr.record_date, ' 步数同步积分');

INSERT INTO points_records (user_id, points, type, reference_id, description)
SELECT
  sr.user_id,
  FLOOR(sr.steps / 100),
  'challenge',
  sr.id,
  CONCAT(sr.record_date, ' 步数同步积分')
FROM step_records sr
LEFT JOIN points_records pr ON pr.user_id = sr.user_id
  AND pr.type = 'challenge'
  AND pr.reference_id = sr.id
WHERE pr.id IS NULL;

-- 插入奖品领取演示数据
INSERT INTO winners (id, user_id, activity_id, prize_id, period_id, `rank`, steps, status, claim_code, claim_deadline) VALUES
(1, 7, 'campus-spring-2026', 4, 1, 12, 43280, 'pending', NULL, NULL),
(2, 1, 'campus-spring-2026', 1, 1, 1, 158000, 'claimed', '1234 5678 9012', DATE_ADD(NOW(), INTERVAL 30 DAY)),
(3, 2, 'campus-spring-2026', 2, 1, 2, 124000, 'pending', NULL, NULL),
(4, 3, 'campus-spring-2026', 3, 1, 3, 109000, 'pending', NULL, NULL)
ON DUPLICATE KEY UPDATE
  activity_id=VALUES(activity_id),
  `rank`=VALUES(`rank`),
  steps=VALUES(steps),
  status=VALUES(status),
  claim_code=VALUES(claim_code),
  claim_deadline=VALUES(claim_deadline);

-- 查看结果
SELECT '用户数据' as type, COUNT(*) as count FROM users
UNION ALL
SELECT '步数记录' as type, COUNT(*) as count FROM step_records
UNION ALL
SELECT '奖品数据' as type, COUNT(*) as count FROM prizes
UNION ALL
SELECT '获奖记录' as type, COUNT(*) as count FROM winners;

SELECT '=== 今日排行榜 ===' as info;
SELECT u.name, d.name as department, sr.steps 
FROM step_records sr 
JOIN users u ON sr.user_id = u.id 
LEFT JOIN departments d ON u.department_id = d.id 
WHERE sr.record_date = CURDATE() 
ORDER BY sr.steps DESC;
