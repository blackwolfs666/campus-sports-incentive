const app = getApp()

Page({
  data: {
    prizeId: null,
    prize: null,
    winners: []
  },

  onLoad(options) {
    this.setData({ prizeId: options.id })
    this.fetchData()
  },

  fetchData() {
    const prizeId = this.data.prizeId

    // 获取奖品详情
    app.request({
      url: `/prizes/${prizeId}`
    }).then(res => {
      this.setData({ prize: res })
    })

    // 获取获奖名单
    app.request({
      url: `/prizes/winners/${prizeId}`
    }).then(res => {
      this.setData({ winners: res })
    })
  },

  // 返回上一页
  goBack() {
    wx.navigateBack()
  }
})
