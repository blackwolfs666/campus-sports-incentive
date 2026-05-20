const activities = [
  {
    id: 'campus-spring-2026',
    name: '春季步数接力挑战赛',
    status: 'active',
    statusText: '进行中',
    coverTone: 'green',
    startDate: '2026.03.01',
    endDate: '2026.05.31',
    signupStart: '2026.03.01',
    signupEnd: '2026.03.15',
    targetGroup: '全体本科生',
    participants: 328,
    maxParticipants: 500,
    isRegistered: true,
    rulesShort: '每日10000步 / 积分排名制',
    rewardShort: '前10名可领奖',
    description: '加入全校运动热潮，用脚步迈向胜利。',
    tags: ['校园活动', '高能挑战'],
    rules: [
      '每日步数至少达到 10,000 步，至少坚持 20 天。',
      '积分排名前 10 名可获得专属奖品。',
      '每天通过首页同步微信运动步数，系统保留最新一次同步结果。'
    ],
    prizes: [
      { id: 'p1', rank: '第1名', name: '校园咖啡季卡', icon: '☕' },
      { id: 'p2', rank: '第2-3名', name: '校园书城50元券', icon: '📚' },
      { id: 'p3', rank: '第4-10名', name: '定制运动水壶', icon: '💧' }
    ],
    myRank: 28,
    myPoints: 1250,
    totalSteps: 186420,
    topTenGap: 320
  },
  {
    id: 'library-marathon-2026',
    name: '图书馆马拉松周',
    status: 'signup',
    statusText: '报名中',
    coverTone: 'blue',
    startDate: '2026.06.01',
    endDate: '2026.06.30',
    signupStart: '2026.05.01',
    signupEnd: '2026.05.31',
    targetGroup: '全校师生',
    participants: 890,
    maxParticipants: 1000,
    isRegistered: false,
    rulesShort: '每日8000步 / 打卡满7天',
    rewardShort: '参与即有奖',
    description: '从宿舍到图书馆，把学习路线变成健康路线。',
    tags: ['全校活动', '打卡挑战'],
    rules: [
      '每日步数至少达到 8,000 步。',
      '连续打卡满 7 天可获得完成奖励。',
      '积分前 20 名可获得文创奖品。'
    ],
    prizes: [
      { id: 'p4', rank: '前20名', name: '博雅文具礼盒', icon: '✏️' },
      { id: 'p5', rank: '完成任务', name: '图书馆借阅积分', icon: '📖' }
    ]
  },
  {
    id: 'evening-walk-2026',
    name: '晚霞健步赛',
    status: 'active',
    statusText: '进行中',
    coverTone: 'orange',
    startDate: '2026.04.10',
    endDate: '2026.05.31',
    signupStart: '2026.04.05',
    signupEnd: '2026.04.10',
    targetGroup: '全体学生',
    participants: 2105,
    maxParticipants: 3000,
    isRegistered: true,
    rulesShort: '每日6000步 / 每步得积分',
    rewardShort: '前30名可领奖',
    description: '傍晚散步也能累计积分，轻量参与校园运动。',
    tags: ['休闲活动', '全民健步'],
    rules: [
      '每日步数至少达到 6,000 步。',
      '每步计 0.001 积分，日上限 1000 积分。',
      '积分前 30 名可获得相应奖品。'
    ],
    prizes: [
      { id: 'p6', rank: '第1-10名', name: '健身房月卡', icon: '💪' },
      { id: 'p7', rank: '第11-30名', name: '运动毛巾', icon: '🏃' }
    ],
    myRank: 45,
    myPoints: 820,
    totalSteps: 132780,
    topTenGap: 780
  },
  {
    id: 'lab-health-2026',
    name: '实验楼健康挑战',
    status: 'active',
    statusText: '进行中',
    coverTone: 'blue',
    startDate: '2026.05.01',
    endDate: '2026.05.31',
    signupStart: '2026.04.20',
    signupEnd: '2026.04.30',
    targetGroup: '理工类学院学生',
    participants: 420,
    maxParticipants: 800,
    isRegistered: false,
    rulesShort: '每日7000步 / 总步数排名',
    rewardShort: '前20名可领奖',
    description: '围绕教学楼与实验楼路线开展健步挑战，鼓励课间主动运动。',
    tags: ['学院活动', '健步挑战'],
    rules: [
      '活动期间每日步数达到 7,000 步计为有效打卡。',
      '总步数排名前 20 名可获得活动奖品。',
      '仅已报名用户可参与排名和发布打卡动态。'
    ],
    prizes: [
      { id: 'p10', rank: '前10名', name: '校园运动礼包', image: '/images/prizes/medal.svg' },
      { id: 'p11', rank: '第11-20名', name: '定制运动水壶', image: '/images/prizes/thermos.svg' }
    ]
  },
  {
    id: 'green-campus-2026',
    name: '绿色校园健走季',
    status: 'active',
    statusText: '进行中',
    coverTone: 'green',
    startDate: '2026.05.05',
    endDate: '2026.06.05',
    signupStart: '2026.04.20',
    signupEnd: '2026.05.04',
    targetGroup: '全校学生',
    participants: 760,
    maxParticipants: 1200,
    isRegistered: false,
    rulesShort: '每日9000步 / 积分排名制',
    rewardShort: '前15名可领奖',
    description: '以校园绿色路线为主题，鼓励学生在日常通勤中完成运动目标。',
    tags: ['校园活动', '绿色健走'],
    rules: [
      '每日步数达到 9,000 步可获得活动积分。',
      '活动按总积分排名，前 15 名可获得奖品。',
      '活动期间可在详情页同步步数并查看排名。'
    ],
    prizes: [
      { id: 'p12', rank: '第1名', name: '校园咖啡季卡', image: '/images/prizes/coffee-card.svg' },
      { id: 'p13', rank: '第2-15名', name: '运动文创套装', image: '/images/prizes/stationery.svg' }
    ]
  },
  {
    id: 'winter-run-2026',
    name: '冬季晨跑挑战赛',
    status: 'ended',
    statusText: '已结束',
    coverTone: 'gray',
    startDate: '2025.12.01',
    endDate: '2026.01.31',
    signupStart: '2025.11.25',
    signupEnd: '2025.11.30',
    targetGroup: '全体本科生',
    participants: 560,
    maxParticipants: 600,
    isRegistered: true,
    rulesShort: '每日8000步 / 积分排名制',
    rewardShort: '前15名可领奖',
    description: '历史活动展示数据，暂未接入活动接口。',
    tags: ['校园活动', '冬季挑战'],
    rules: [
      '活动已结束，仅用于展示。',
      '获奖记录以我的奖品页面为准。'
    ],
    prizes: [
      { id: 'p8', rank: '第1-5名', name: '校园咖啡季卡', icon: '☕' },
      { id: 'p9', rank: '第6-15名', name: '定制保温杯', icon: '🥤' }
    ],
    myFinalRank: 5,
    hadPrize: true,
    wonPrizeName: '校园咖啡季卡'
  }
]

function getActivityById(id) {
  return activities.find(item => item.id === id) || activities[0]
}

function getActiveRegisteredActivity() {
  return activities.find(item => item.status === 'active' && item.isRegistered) || null
}

module.exports = {
  activities,
  getActivityById,
  getActiveRegisteredActivity
}
