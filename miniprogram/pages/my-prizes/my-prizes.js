const STATUS_TEXT = {
  pending: '待生成',
  claimed: '待核销',
  redeemed: '已领取',
  expired: '已过期'
}

function isExpired(item) {
  if (!item.claim_deadline) return false
  const deadline = new Date(item.claim_deadline)
  if (Number.isNaN(deadline.getTime())) return false
  return deadline.getTime() < Date.now()
}

function normalizePrize(item) {
  let viewStatus = item.status

  if (item.status === 'claimed' && isExpired(item)) {
    viewStatus = 'expired'
  }

  if (item.status === 'pending' || item.status === 'claimed') {
    viewStatus = 'pending'
  }

  return {
    ...item,
    viewStatus,
    statusText: STATUS_TEXT[item.status] || STATUS_TEXT[viewStatus] || item.status || '未知状态',
    actionText: item.status === 'pending' ? '生成兑换码' : '查看凭证'
  }
}

Page({
  data: {
    activeTab: 'pending',
    hasLoaded: false,
    tabs: [
      { key: 'pending', text: '待核销' },
      { key: 'redeemed', text: '已领取' },
      { key: 'expired', text: '已过期' }
    ],
    prizes: [],
    filteredPrizes: []
  },

  onLoad() {
    this.fetchPrizes()
  },

  onShow() {
    if (this.data.hasLoaded) {
      this.fetchPrizes({ silent: true })
    }
  },

  onPullDownRefresh() {
    this.fetchPrizes().finally(() => wx.stopPullDownRefresh())
  },

  fetchPrizes(options = {}) {
    if (!options.silent) {
      wx.showLoading({ title: '加载中...' })
    }
    const app = getApp()
    return app.request({
      url: '/prizes/my/list'
    }).then((res) => {
      const prizes = (res || []).map(normalizePrize)
      this.setData({
        prizes,
        hasLoaded: true
      })
      this.applyFilter()
    }).catch((err) => {
      console.error('获取我的奖品失败', err)
      wx.showToast({
        title: '获取奖品失败',
        icon: 'none'
      })
    }).finally(() => {
      if (!options.silent) {
        wx.hideLoading()
      }
    })
  },

  switchTab(e) {
    this.setData({ activeTab: e.currentTarget.dataset.key })
    this.applyFilter()
  },

  applyFilter() {
    const { activeTab, prizes } = this.data
    const filteredPrizes = prizes.filter(item => item.viewStatus === activeTab)
    this.setData({ filteredPrizes })
  },

  goToRedeem(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/redeem/redeem?id=${id}`
    })
  },

  goBack() {
    wx.navigateBack()
  },

  goActivities() {
    wx.switchTab({
      url: '/pages/activities/activities'
    })
  }
})
