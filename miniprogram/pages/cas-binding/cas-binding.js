const app = getApp()

Page({
  data: {
    username: '',
    password: '',
    loading: false,
    status: null
  },

  onLoad() {
    this.fetchStatus()
  },

  onShow() {
    this.fetchStatus()
  },

  fetchStatus() {
    app.request({
      url: '/cas/status'
    }).then(res => {
      this.setData({ status: res })
    }).catch(err => {
      console.error('获取CAS绑定状态失败', err)
    })
  },

  onInput(e) {
    const field = e.currentTarget.dataset.field
    this.setData({ [field]: e.detail.value })
  },

  submitBind() {
    const username = this.data.username.trim()
    const password = this.data.password
    if (!username || !password) {
      wx.showToast({ title: '请填写学号/工号和密码', icon: 'none' })
      return
    }
    if (this.data.loading) return

    this.setData({ loading: true })
    wx.showLoading({ title: '认证中' })
    app.request({
      url: '/cas/login',
      method: 'POST',
      data: { username, password }
    }).then(loginRes => {
      return app.request({
        url: '/cas/bind',
        method: 'POST',
        data: { bind_token: loginRes.bind_token }
      })
    }).then(bindRes => {
      wx.showToast({ title: '绑定成功', icon: 'success' })
      const userInfo = {
        ...(app.globalData.userInfo || {}),
        name: bindRes.name,
        employee_id: bindRes.employee_id,
        cas_binded: true,
        edu_person_type: bindRes.edu_person_type,
        department_name: bindRes.department_name
      }
      app.globalData.userInfo = userInfo
      this.setData({
        password: '',
        status: {
          cas_binded: true,
          employee_id: bindRes.employee_id,
          name: bindRes.name,
          department_name: bindRes.department_name,
          edu_person_type: bindRes.edu_person_type
        }
      })
      setTimeout(() => wx.navigateBack(), 700)
    }).catch(err => {
      const detail = err?.data?.detail || '绑定失败，请检查账号密码'
      wx.showToast({ title: String(detail).slice(0, 20), icon: 'none' })
    }).finally(() => {
      wx.hideLoading()
      this.setData({ loading: false })
    })
  },

  goBack() {
    wx.navigateBack()
  }
})
