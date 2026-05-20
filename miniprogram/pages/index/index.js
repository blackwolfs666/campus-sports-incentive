const { activities } = require('../../data/mock-activities')

const DAY_LABELS = ['日', '一', '二', '三', '四', '五', '六']
const SYNC_DATE_KEY = 'lastStepSyncDate'
const STEP_HISTORY_KEY = 'stepHistoryMap'

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

function normalizeDateKey(value) {
  if (!value) return ''
  if (typeof value === 'string') {
    const match = value.match(/\d{4}-\d{2}-\d{2}/)
    if (match) return match[0]
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  const year = date.getFullYear()
  const month = `${date.getMonth() + 1}`.padStart(2, '0')
  const day = `${date.getDate()}`.padStart(2, '0')
  return `${year}-${month}-${day}`
}

Page({
  data: {
    userInfo: null,
    todaySteps: 0,
    todayStepsText: '0',
    totalSteps: 0,
    totalDistance: 0,
    streakDays: 0,
    healthLevel: 1,
    dailyGoal: 10000,
    dailyGoalText: '10,000',
    remainingStepsText: '10,000',
    departmentName: '',
    lastSyncTime: '',
    weekTotal: 0,
    progressPercent: 0,
    statusBarHeight: 0,
    isSyncing: false,
    activeActivity: null,
    activeActivityIndex: 0,
    joinedActivities: [],
    joinedActivityCount: 0,
    dayLabels: DAY_LABELS,
    stepHistoryMap: {},
    calendarCells: []
  },

  onLoad() {
    const systemInfo = wx.getSystemInfoSync()
    const joinedActivities = activities.filter(item => item.isRegistered && item.status === 'active')
    const stepHistoryMap = wx.getStorageSync(STEP_HISTORY_KEY) || {}
    this.setData({
      statusBarHeight: systemInfo.statusBarHeight || 20,
      joinedActivities,
      joinedActivityCount: joinedActivities.length,
      activeActivity: joinedActivities[0] || null,
      stepHistoryMap,
      calendarCells: this.buildCalendarCells(0, 10000, stepHistoryMap)
    })
    this.fetchJoinedActivities()
    this.fetchHomeData()
  },

  onShow() {
    this.fetchJoinedActivities()
    this.fetchHomeData()
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 0 })
    }
  },

  fetchJoinedActivities() {
    const app = getApp()
    app.request({
      url: '/activities/my'
    }).then((res) => {
      const joinedActivities = (res.items || []).filter(item => item.status === 'active')
      const activeActivityIndex = Math.min(this.data.activeActivityIndex || 0, Math.max(joinedActivities.length - 1, 0))
      this.setData({
        joinedActivities,
        joinedActivityCount: joinedActivities.length,
        activeActivityIndex,
        activeActivity: joinedActivities[activeActivityIndex] || null
      })
    }).catch((err) => {
      console.warn('获取我参与的活动失败，使用本地活动配置', err)
      const joinedActivities = activities.filter(item => item.isRegistered && item.status === 'active')
      this.setData({
        joinedActivities,
        joinedActivityCount: joinedActivities.length,
        activeActivity: joinedActivities[this.data.activeActivityIndex || 0] || joinedActivities[0] || null
      })
    })
  },

  fetchHomeData() {
    const app = getApp()
    app.request({
      url: '/steps/home'
    }).then(res => {
      const todaySteps = Number(res.today_steps || 0)
      const dailyGoal = Number(res.daily_goal || 10000)
      const progressPercent = Math.min(Math.round((todaySteps / dailyGoal) * 100), 100)
      const remainingSteps = Math.max(dailyGoal - todaySteps, 0)

      let lastSyncTime = ''
      if (res.last_sync_time) {
        const date = new Date(res.last_sync_time)
        lastSyncTime = `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
        if (isTodayDateTime(res.last_sync_time)) {
          this.markSyncedToday()
        }
      }

      this.setData({
        todaySteps,
        todayStepsText: this.formatNumber(todaySteps),
        totalSteps: res.total_steps || 0,
        totalDistance: res.total_distance || 0,
        streakDays: res.streak_days || 0,
        healthLevel: res.health_level || 1,
        dailyGoal,
        dailyGoalText: this.formatNumber(dailyGoal),
        remainingStepsText: this.formatNumber(remainingSteps),
        departmentName: res.department_name || '',
        lastSyncTime,
        weekTotal: res.week_challenge?.week_total || 0,
        progressPercent,
        userInfo: app.globalData.userInfo,
        calendarCells: this.buildCalendarCells(todaySteps, dailyGoal, this.data.stepHistoryMap)
      })
      this.fetchStepHistory(dailyGoal, todaySteps)
    }).catch(err => {
      console.error('获取首页数据失败', err)
      this.setData({
        calendarCells: this.buildCalendarCells(this.data.todaySteps || 0, this.data.dailyGoal || 10000, this.data.stepHistoryMap)
      })
    })
  },

  formatNumber(num) {
    return Number(num || 0).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
  },

  formatShortSteps(num) {
    if (!num) return ''
    if (num >= 10000) return `${(num / 1000).toFixed(1).replace('.0', '')}k`
    if (num >= 1000) return `${(num / 1000).toFixed(1)}k`
    return String(num)
  },

  fetchStepHistory(dailyGoal, todaySteps) {
    const app = getApp()
    app.request({
      url: '/steps/history',
      data: { days: 45 }
    }).then(records => {
      const history = {}
      ;(records || []).forEach(record => {
        const dateKey = normalizeDateKey(record.record_date)
        if (dateKey) {
          history[dateKey] = Number(record.steps || 0)
        }
      })
      wx.setStorageSync(STEP_HISTORY_KEY, history)
      this.setData({
        stepHistoryMap: history,
        calendarCells: this.buildCalendarCells(todaySteps, dailyGoal, history)
      })
    }).catch(err => {
      console.warn('获取运动日历失败', err)
      this.setData({
        calendarCells: this.buildCalendarCells(todaySteps, dailyGoal, this.data.stepHistoryMap)
      })
    })
  },

  buildCalendarCells(todaySteps, dailyGoal, history = {}) {
    const today = new Date()
    const year = today.getFullYear()
    const month = today.getMonth()
    const todayDate = today.getDate()
    const daysInMonth = new Date(year, month + 1, 0).getDate()
    const firstDay = new Date(year, month, 1).getDay()
    const cells = []

    for (let i = 0; i < firstDay; i += 1) {
      cells.push({ key: `empty-${i}`, empty: true })
    }

    for (let day = 1; day <= daysInMonth; day += 1) {
      const isToday = day === todayDate
      const isFuture = day > todayDate
      const dateKey = `${year}-${`${month + 1}`.padStart(2, '0')}-${`${day}`.padStart(2, '0')}`
      const steps = isToday ? todaySteps : Number(history[dateKey] || 0)
      const hitTarget = steps >= dailyGoal
      cells.push({
        key: `day-${day}`,
        day,
        isToday,
        isFuture,
        hasSteps: steps > 0,
        missed: !isFuture && !isToday && steps <= 0,
        hitTarget,
        stepsLabel: this.formatShortSteps(steps)
      })
    }

    return cells
  },

  syncSteps() {
    const app = getApp()

    if (this.data.isSyncing) return

    if (app.globalData.devMode) {
      wx.showToast({ title: '当前为模拟数据模式', icon: 'none' })
      return
    }

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
              wx.showToast({ title: `同步成功 ${syncRes.steps} 步`, icon: 'success' })
              this.fetchHomeData()
            }).catch(err => {
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

  markSyncedToday() {
    const todayKey = getTodayKey()
    const app = getApp()
    app.globalData.lastStepSyncDate = todayKey
    wx.setStorageSync(SYNC_DATE_KEY, todayKey)
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
    return '同步失败'
  },

  goToActivities() {
    wx.switchTab({ url: '/pages/activities/activities' })
  },

  goToProfile() {
    wx.switchTab({ url: '/pages/profile/profile' })
  },

  goToActivityDetail() {
    const activity = this.data.activeActivity
    if (!activity) {
      this.goToActivities()
      return
    }
    wx.navigateTo({
      url: `/pages/activity-detail/activity-detail?id=${activity.id}`
    })
  },

  switchActivity(e) {
    const direction = e.currentTarget.dataset.direction
    const { joinedActivities, activeActivityIndex } = this.data
    if (!joinedActivities.length) return

    const offset = direction === 'next' ? 1 : -1
    const nextIndex = (activeActivityIndex + offset + joinedActivities.length) % joinedActivities.length
    this.setData({
      activeActivityIndex: nextIndex,
      activeActivity: joinedActivities[nextIndex]
    })
  },

  noop() {},

  goToRanking() {
    const activity = this.data.activeActivity
    wx.navigateTo({
      url: `/pages/ranking/ranking${activity ? `?activityId=${activity.id}` : ''}`
    })
  },

  goToNotifications() {
    wx.showToast({ title: '暂无通知', icon: 'none' })
  }
})
