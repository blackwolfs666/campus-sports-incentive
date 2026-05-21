const app = getApp()

function formatDisplayUserId(userInfo) {
  if (!userInfo) return ''
  if (userInfo.displayUserId) return userInfo.displayUserId
  if (userInfo.display_user_id) return userInfo.display_user_id
  const id = userInfo.id || userInfo.user_id || userInfo.userId
  if (!id) return ''
  return `U${String(id).padStart(7, '0')}`
}

function normalizeUserInfo(userInfo) {
  if (!userInfo) return null
  return app.normalizeUserInfo ? app.normalizeUserInfo(userInfo) : userInfo
}

Page({
  data: {
    userInfo: null,
    displayUserId: '',
    todaySteps: 0,
    totalDistance: 0,
    streakDays: 0,
    healthLevel: 1,
    myPrizes: [],
    pendingPrizeCount: 0,
    unreadMessageCount: 0,
    casStatus: null
  },

  onLoad() {
    this.fetchData()
  },

  onShow() {
    this.fetchData()
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 2 })
    }
  },

  hasLoginToken() {
    const storedToken = wx.getStorageSync('token')
    if (!app.globalData.token && storedToken) {
      app.globalData.token = storedToken
    }
    return !!app.globalData.token
  },

  resetGuestData() {
    this.setData({
      userInfo: null,
      displayUserId: '',
      todaySteps: 0,
      totalDistance: 0,
      streakDays: 0,
      healthLevel: 1,
      myPrizes: [],
      pendingPrizeCount: 0,
      casStatus: null
    })
  },

  handleAuthError(err) {
    if (err && err.statusCode === 401 && app.clearAuth) {
      app.clearAuth()
      this.resetGuestData()
      return true
    }
    return false
  },

  setUserInfo(userInfo) {
    const normalized = normalizeUserInfo(userInfo)
    if (!normalized) return
    app.globalData.userInfo = normalized
    this.setData({
      userInfo: normalized,
      displayUserId: formatDisplayUserId(normalized)
    })
  },

  refreshUserInfo() {
    if (app.globalData.userInfo) {
      this.setUserInfo(app.globalData.userInfo)
    }

    if (!formatDisplayUserId(app.globalData.userInfo)) {
      app.getUserInfo().then(userInfo => {
        this.setUserInfo(userInfo)
      }).catch(err => {
        if (this.handleAuthError(err)) return
        console.error('刷新用户信息失败', err)
      })
    }
  },

  fetchData() {
    if (!this.hasLoginToken()) {
      this.resetGuestData()
      return
    }

    this.refreshUserInfo()

    app.request({
      url: '/steps/home',
      skipLoginRetry: true
    }).then(res => {
      this.setData({
        todaySteps: res.today_steps,
        totalDistance: res.total_distance,
        streakDays: res.streak_days,
        healthLevel: res.health_level
      })
    }).catch(err => {
      if (this.handleAuthError(err)) return
      console.error('获取个人步数数据失败', err)
    })

    app.request({
      url: '/prizes/my/list',
      skipLoginRetry: true
    }).then(res => {
      const myPrizes = res || []
      this.setData({
        myPrizes,
        pendingPrizeCount: myPrizes.filter(item => item.status === 'pending').length
      })
    }).catch(err => {
      if (this.handleAuthError(err)) return
      console.error('获取我的奖品失败', err)
    })

    app.request({
      url: '/cas/status',
      skipLoginRetry: true
    }).then(res => {
      this.setData({ casStatus: res })
      if (res.cas_binded) {
        const baseUserInfo = this.data.userInfo || app.globalData.userInfo || {}
        const userInfo = {
          ...baseUserInfo,
          name: res.name || baseUserInfo.name,
          employee_id: res.employee_id,
          cas_binded: true,
          edu_person_type: res.edu_person_type,
          department_name: res.department_name
        }
        this.setUserInfo(userInfo)
      }
    }).catch(err => {
      if (this.handleAuthError(err)) return
      console.error('获取CAS绑定状态失败', err)
    })
  },

  copyUserId() {
    const id = this.data.displayUserId
    if (!id) {
      wx.showToast({ title: '暂无用户ID', icon: 'none' })
      return
    }
    wx.setClipboardData({
      data: id,
      success: () => {
        wx.showToast({ title: '用户ID已复制', icon: 'success' })
      }
    })
  },

  goToRedeem(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/redeem/redeem?id=${id}`
    })
  },

  goToMyPrizes() {
    wx.navigateTo({
      url: '/pages/my-prizes/my-prizes'
    })
  },

  goToActivities() {
    app.globalData.activityJoinFilter = 'joined'
    wx.switchTab({
      url: '/pages/activities/activities'
    })
  },

  goAdminDashboard() {
    wx.navigateTo({
      url: '/pages/admin-dashboard/admin-dashboard'
    })
  },

  goCalendar() {
    wx.switchTab({
      url: '/pages/index/index'
    })
  },

  goToProfile() {
    wx.switchTab({ url: '/pages/profile/profile' })
  },

  goSettings() {
    wx.navigateTo({
      url: '/pages/settings/settings'
    })
  },

  logout() {
    wx.showToast({ title: '退出登录功能待完善', icon: 'none' })
  },

  goToNotifications() {
    wx.showToast({ title: '消息功能待完善', icon: 'none' })
  }
})
