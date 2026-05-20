const app = getApp()

Page({
  data: {
    loading: false
  },

  handleLogin() {
    if (this.data.loading) return
    
    this.setData({ loading: true })
    
    app.login().then(() => {
      wx.switchTab({ url: '/pages/index/index' })
    }).catch(err => {
      console.error('登录失败', err)
      wx.showToast({ title: '登录失败，请重试', icon: 'none' })
    }).finally(() => {
      this.setData({ loading: false })
    })
  }
})
