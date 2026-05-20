const SYNC_DATE_KEY = 'lastStepSyncDate'
const PRIZE_PLACEHOLDERS = [
  '/images/prizes/thermos.svg',
  '/images/prizes/stationery.svg',
  '/images/prizes/coffee-card.svg',
  '/images/prizes/medal.svg'
]

const PRIZE_TYPE_IMAGES = {
  first: '/images/prizes/thermos.svg',
  second: '/images/prizes/stationery.svg',
  third: '/images/prizes/coffee-card.svg',
  honorable: '/images/prizes/medal.svg'
}

function normalizeRemoteUrl(url) {
  if (!url) return ''
  if (/^https?:\/\//.test(url)) return url
  if (url.startsWith('/static/')) {
    const { BASE_URL } = require('../../config/api')
    return `${BASE_URL}${url}`
  }
  return url
}

function getTodayKey() {
  const now = new Date()
  const year = now.getFullYear()
  const month = `${now.getMonth() + 1}`.padStart(2, '0')
  const date = `${now.getDate()}`.padStart(2, '0')
  return `${year}-${month}-${date}`
}

function isTodayDateTime(value) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return false
  return `${date.getFullYear()}-${`${date.getMonth() + 1}`.padStart(2, '0')}-${`${date.getDate()}`.padStart(2, '0')}` === getTodayKey()
}

function normalizePrize(prize, index) {
  return {
    ...prize,
    image: normalizeRemoteUrl(prize.image_url || prize.image) || PRIZE_TYPE_IMAGES[prize.prize_type] || PRIZE_PLACEHOLDERS[index % PRIZE_PLACEHOLDERS.length]
  }
}

function normalizeActivity(activity) {
  if (!activity) return null
  return {
    ...activity,
    posterUrl: normalizeRemoteUrl(activity.posterUrl || activity.poster_url),
    prizes: (activity.prizes || []).map(normalizePrize)
  }
}

Page({
  data: {
    activity: null,
    hasSyncedToday: false,
    isSyncing: false
  },

  onLoad(options) {
    const activityId = options.id || ''
    if (!activityId) {
      wx.showToast({ title: '活动不存在', icon: 'none' })
      setTimeout(() => wx.navigateBack(), 600)
      return
    }

    const currentActivity = getApp().globalData.currentActivity
    const activity = currentActivity?.id === activityId ? normalizeActivity(currentActivity) : null
    this.setData({ activity })
    this.fetchActivity(activityId)
    this.refreshSyncState()
    this.fetchSyncStateFromHome()
  },

  onShow() {
    this.refreshSyncState()
    this.fetchSyncStateFromHome()
    if (this.data.activity?.id) {
      this.fetchActivity(this.data.activity.id)
    }
  },

  refreshSyncState() {
    const app = getApp()
    const todayKey = getTodayKey()
    const syncedDate = app.globalData.lastStepSyncDate || wx.getStorageSync(SYNC_DATE_KEY)
    this.setData({ hasSyncedToday: syncedDate === todayKey })
  },

  fetchSyncStateFromHome() {
    const app = getApp()

    app.request({
      url: '/steps/home'
    }).then((res) => {
      if (res.last_sync_time && isTodayDateTime(res.last_sync_time)) {
        this.markSyncedToday()
      }
    }).catch((err) => {
      console.warn('获取今日同步状态失败', err)
    })
  },

  fetchActivity(id) {
    if (!id) return
    const app = getApp()
    app.request({
      url: `/activities/${id}`
    }).then((res) => {
      const activity = normalizeActivity(res)
      getApp().globalData.currentActivity = activity
      this.setData({ activity })
    }).catch((err) => {
      console.error('获取活动详情失败', err)
      wx.showToast({ title: '获取活动失败', icon: 'none' })
    })
  },

  markSyncedToday() {
    const todayKey = getTodayKey()
    const app = getApp()
    app.globalData.lastStepSyncDate = todayKey
    wx.setStorageSync(SYNC_DATE_KEY, todayKey)
    this.setData({ hasSyncedToday: true })
  },

  registerActivity() {
    if (!this.data.activity) return
    if (this.data.activity.status !== 'signup') {
      wx.showToast({ title: '当前活动不能报名', icon: 'none' })
      return
    }

    const app = getApp()
    app.request({
      url: `/activities/${this.data.activity.id}/join`,
      method: 'POST'
    }).then((res) => {
      const activity = normalizeActivity(res.activity)
      getApp().globalData.currentActivity = activity
      this.setData({ activity })
      wx.showToast({
        title: '报名成功',
        icon: 'success'
      })
    }).catch((err) => {
      console.error('报名活动失败', err)
      wx.showToast({
        title: err?.data?.detail || '报名失败',
        icon: 'none'
      })
    })
  },

  goSyncSteps() {
    const app = getApp()
    const activity = this.data.activity

    if (!activity || !activity.isRegistered || activity.status !== 'active') {
      wx.showToast({ title: '进行中的已报名活动才能同步', icon: 'none' })
      return
    }

    if (this.data.isSyncing) return

    wx.getSetting({
      success: (res) => {
        if (res.authSetting['scope.werun'] === true) {
          this.getWeRunData()
        } else if (res.authSetting['scope.werun'] === false) {
          wx.showModal({
            title: '提示',
            content: '需要授权微信运动数据才能同步步数，是否前往设置开启？',
            success: (modalRes) => {
              if (modalRes.confirm) {
                wx.openSetting({
                  success: (settingRes) => {
                    if (settingRes.authSetting['scope.werun']) {
                      this.getWeRunData()
                    }
                  }
                })
              }
            }
          })
        } else {
          wx.authorize({
            scope: 'scope.werun',
            success: () => this.getWeRunData(),
            fail: () => {
              wx.showModal({
                title: '提示',
                content: '需要授权微信运动数据才能同步步数，是否前往设置开启？',
                success: (modalRes) => {
                  if (modalRes.confirm) {
                    wx.openSetting({
                      success: (settingRes) => {
                        if (settingRes.authSetting['scope.werun']) {
                          this.getWeRunData()
                        }
                      }
                    })
                  }
                }
              })
            }
          })
        }
      },
      fail: () => {
        wx.authorize({
          scope: 'scope.werun',
          success: () => this.getWeRunData(),
          fail: () => {
            wx.showToast({ title: '授权失败，请手动开启', icon: 'none' })
          }
        })
      }
    })
  },

  getWeRunData() {
    const app = getApp()
    this.setData({ isSyncing: true })
    wx.showLoading({ title: '同步中...' })

    const ensureLogin = app.globalData.token ? Promise.resolve() : app.login()
    ensureLogin.then(() => this.requestWeRunSync()).catch((err) => {
      this.finishSync()
      console.error('同步前登录失败', err)
      wx.showToast({ title: '登录失败，请重试', icon: 'none' })
    })
  },

  requestWeRunSync() {
    const app = getApp()

    wx.login({
      success: (loginRes) => {
        if (!loginRes.code) {
          this.finishSync()
          wx.showToast({ title: '微信登录失败', icon: 'none' })
          return
        }

        wx.getWeRunData({
          success: (runRes) => {
            app.request({
              url: '/steps/sync',
              method: 'POST',
              data: {
                code: loginRes.code,
                encryptedData: runRes.encryptedData,
                iv: runRes.iv
              }
            }).then((syncRes) => {
              this.markSyncedToday()
              this.finishSync()
              if (this.data.activity?.id) {
                this.fetchActivity(this.data.activity.id)
              }
              this.promptPublishCheckin(syncRes)
            }).catch((err) => {
              this.finishSync()
              console.error('同步步数失败', err.statusCode, err.data || err)
              wx.showToast({ title: this.getSyncErrorMessage(err), icon: 'none' })
            })
          },
          fail: (err) => {
            this.finishSync()
            console.error('获取微信运动数据失败', err)
            wx.showToast({ title: '获取微信运动数据失败', icon: 'none' })
          }
        })
      },
      fail: (err) => {
        this.finishSync()
        console.error('微信登录失败', err)
        wx.showToast({ title: '微信登录失败', icon: 'none' })
      }
    })
  },

  finishSync() {
    wx.hideLoading()
    this.setData({ isSyncing: false })
  },

  promptPublishCheckin(syncRes) {
    wx.showModal({
      title: '同步成功',
      content: '是否要发布打卡动态？',
      confirmText: '确认',
      cancelText: '暂不',
      success: (modalRes) => {
        if (!modalRes.confirm || !this.data.activity) return

        wx.navigateTo({
          url: `/pages/checkin-edit/checkin-edit?activityId=${this.data.activity.id}&steps=${syncRes.steps || 0}&streakDays=${syncRes.streak_days || 0}`
        })
      }
    })
  },

  getSyncErrorMessage(err) {
    const detail = err?.data?.detail || err?.detail || ''
    if (typeof detail === 'string' && detail) {
      if (detail.includes('微信运动解密未配置')) return '微信运动解密未配置'
      if (detail.includes('AppID') || detail.includes('AppSecret')) return '微信配置不匹配'
      if (detail.includes('session_key')) return '微信登录态无效'
      if (detail.includes('解密失败')) return '微信运动解密失败'
      return detail.slice(0, 18)
    }
    return '同步失败，请检查后端'
  },

  goRanking() {
    const activity = this.data.activity
    if (!activity || !activity.isRegistered || activity.status !== 'active') {
      wx.showToast({ title: '进行中的已报名活动才能查看排行榜', icon: 'none' })
      return
    }
    wx.navigateTo({
      url: `/pages/ranking/ranking${activity ? `?activityId=${activity.id}` : ''}`
    })
  },

  goCheckinFeed() {
    const activity = this.data.activity
    if (!activity) return

    if (!activity.isRegistered) {
      wx.showToast({ title: '报名后才能查看打卡动态', icon: 'none' })
      return
    }

    if (activity.status !== 'active') {
      wx.showToast({ title: '进行中的活动才能查看打卡动态', icon: 'none' })
      return
    }

    wx.navigateTo({
      url: `/pages/checkin-feed/checkin-feed?activityId=${activity.id}`
    })
  },

  goSignupActivities() {
    const app = getApp()
    app.globalData.activityStatusFilter = 'signup'
    app.globalData.activityJoinFilter = 'notJoined'
    wx.switchTab({
      url: '/pages/activities/activities'
    })
  },

  goBack() {
    wx.navigateBack()
  },

  goMyPrizes() {
    wx.navigateTo({
      url: '/pages/my-prizes/my-prizes'
    })
  },

  shareActivity() {
    wx.showToast({
      title: '暂未配置分享',
      icon: 'none'
    })
  }
})
