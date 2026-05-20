Page({
  data: {
    rankType: 'points',
    activityId: '',
    activity: null,
    pageTitle: '排行榜',
    ruleHint: '按累计积分排名',
    topThree: [],
    leaderboard: [],
    myRank: null,
    myValue: 0,
    myValueLabel: '积分',
    userInfo: null
  },

  onLoad(options = {}) {
    const activityId = options.activityId || options.id || ''
    this.setData({
      activityId,
      activity: null,
      pageTitle: '排行榜',
      ruleHint: this.getRuleHint(activityId, this.data.rankType)
    })
    this.fetchActivity()
    this.fetchRanking()
  },

  fetchActivity() {
    if (!this.data.activityId) return
    const app = getApp()
    app.request({
      url: `/activities/${this.data.activityId}`
    }).then((activity) => {
      if (!activity.isRegistered || activity.status !== 'active') {
        wx.showToast({ title: '进行中的已报名活动才能查看排行榜', icon: 'none' })
        setTimeout(() => wx.navigateBack(), 600)
        return
      }
      this.setData({
        activity,
        pageTitle: `${activity.name}：排行榜`
      })
    }).catch((err) => {
      console.error('获取排行榜活动信息失败', err)
    })
  },

  onShow() {
    this.fetchRanking()
  },

  filterChange(e) {
    const rankType = e.currentTarget.dataset.type
    this.setData({
      rankType,
      ruleHint: this.getRuleHint(this.data.activityId, rankType)
    })
    this.fetchRanking()
  },

  getRuleHint(activityId, rankType) {
    if (activityId) {
      return rankType === 'points' ? '按当前活动累计积分排名' : '按当前活动累计步数排名'
    }
    return rankType === 'points' ? '按累计积分排名' : '按累计步数排名'
  },

  getValue(item) {
    if (this.data.rankType === 'points') {
      return item.points ?? item.total_points ?? item.steps ?? 0
    }
    return item.total_steps ?? item.steps ?? 0
  },

  formatRankItems(items) {
    const unit = this.data.rankType === 'points' ? '分' : '步'
    return items.map(item => ({
      ...item,
      department: item.department_name || item.department,
      rankValue: this.getValue(item),
      rankUnit: unit
    }))
  },

  fetchRanking() {
    const app = getApp()
    const requestData = {
      period_type: this.data.rankType === 'points' ? 'points' : 'total_steps',
      scope: 'all',
      limit: 50
    }

    if (this.data.activityId) {
      requestData.activity_id = this.data.activityId
    }

    app.request({
      url: '/ranking',
      data: requestData
    }).then(res => {
      const allItems = this.formatRankItems(res.items || [])
      const myValue = this.data.rankType === 'points'
        ? (res.my_rank?.points ?? res.my_rank?.steps ?? 0)
        : (res.my_rank?.total_steps ?? res.my_rank?.steps ?? 0)

      this.setData({
        topThree: allItems.slice(0, 3),
        leaderboard: allItems.slice(3),
        myRank: res.my_rank?.rank || null,
        myValue,
        myValueLabel: this.data.rankType === 'points' ? '积分' : '步',
        userInfo: app.globalData.userInfo || null
      })
    }).catch(err => {
      console.error('获取排行榜失败', err)
    })
  },

  goBack() {
    wx.navigateBack()
  }
})
