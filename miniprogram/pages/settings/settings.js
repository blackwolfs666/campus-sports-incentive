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
    casStatus: null,
    werunAuthorized: false
  },

  onLoad() {
    this.refreshData()
  },

  onShow() {
    this.refreshData()
  },

  hasLoginToken() {
    const storedToken = wx.getStorageSync('token')
    if (!app.globalData.token && storedToken) {
      app.globalData.token = storedToken
    }
    return !!app.globalData.token
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

  handleAuthError(err) {
    if (err && err.statusCode === 401 && app.clearAuth) {
      app.clearAuth()
      this.setData({
        userInfo: null,
        displayUserId: '',
        casStatus: null
      })
      return true
    }
    return false
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

  refreshData() {
    if (this.hasLoginToken()) {
      this.refreshUserInfo()
      this.fetchCasStatus()
    } else {
      this.setData({
        userInfo: null,
        displayUserId: '',
        casStatus: null
      })
    }
    this.fetchAuthSetting()
  },

  fetchCasStatus() {
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

  fetchAuthSetting() {
    wx.getSetting({
      success: (res) => {
        this.setData({
          werunAuthorized: !!res.authSetting['scope.werun']
        })
      }
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
      success: () => wx.showToast({ title: '用户ID已复制', icon: 'success' })
    })
  },

  goCasBinding() {
    const casStatus = this.data.casStatus
    if (casStatus && casStatus.cas_binded) {
      wx.showModal({
        title: '学校账号已绑定',
        content: `当前已绑定 ${casStatus.employee_id || '学校账号'}，是否换绑？`,
        confirmText: '换绑',
        cancelText: '取消',
        success: (res) => {
          if (res.confirm) {
            wx.navigateTo({ url: '/pages/cas-binding/cas-binding?rebind=1' })
          }
        }
      })
      return
    }

    wx.navigateTo({ url: '/pages/cas-binding/cas-binding' })
  },

  openAuthSetting() {
    wx.openSetting({
      success: () => this.fetchAuthSetting()
    })
  },

  clearLocalCache() {
    wx.showModal({
      title: '清理本地缓存',
      content: '将清除本机保存的同步日期等临时数据，服务器数据不会被删除。',
      confirmText: '清理',
      success: (res) => {
        if (!res.confirm) return
        wx.removeStorageSync('lastStepSyncDate')
        app.globalData.lastStepSyncDate = ''
        wx.showToast({ title: '已清理', icon: 'success' })
      }
    })
  },

  goBack() {
    wx.navigateBack()
  }
})
