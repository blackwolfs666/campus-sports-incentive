Page({
  data: {
    prizes: []
  },

  onLoad() {
    this.fetchPrizes()
  },

  onShow() {
    this.fetchPrizes()
    // 更新TabBar选中状态
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 2 })
    }
  },

  fetchPrizes() {
    const app = getApp()
    app.request({
      url: '/prizes'
    }).then(res => {
      this.setData({ prizes: res })
    }).catch(err => {
      console.error('获取奖品失败', err)
    })
  },

  goToWinners(e) {
    const prizeId = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/prize-winners/prize-winners?id=${prizeId}`
    })
  },

  getPrizeIcon(type) {
    const icons = {
      first: '🏆',
      second: '📚',
      third: '☕',
      honorable: '🎖️'
    }
    return icons[type] || '🎁'
  },

  getPrizeLabel(type) {
    const labels = {
      first: '第一名',
      second: '第二名',
      third: '第三名',
      honorable: '优胜奖'
    }
    return labels[type] || '奖品'
  },

  getBorderClass(type) {
    const classes = {
      first: 'border-tertiary',
      second: 'border-surface',
      third: 'border-secondary',
      honorable: 'border-outline'
    }
    return classes[type] || 'border-outline'
  }
})
