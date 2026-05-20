const { BASE_URL } = require('../../config/api')

function normalizeRemoteUrl(url) {
  if (!url) return ''
  if (/^https?:\/\//.test(url)) return url
  if (url.startsWith('/static/')) return `${BASE_URL}${url}`
  return url
}

Page({
  data: {
    keyword: '',
    activeTab: 'signup',
    joinFilter: 'all',
    activities: [],
    filteredActivities: []
  },

  onLoad() {
    this.fetchActivities()
  },

  onShow() {
    const app = getApp()
    this.setData({
      activeTab: app.globalData.activityStatusFilter || 'signup',
      joinFilter: app.globalData.activityJoinFilter || 'all'
    })
    this.fetchActivities()

    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 1 })
    }
  },

  fetchActivities() {
    const app = getApp()
    app.request({
      url: '/activities'
    }).then((res) => {
      this.setData({ activities: res.items || [] })
      this.applyFilters()
    }).catch((err) => {
      console.error('获取活动列表失败', err)
      wx.showToast({ title: '获取活动失败', icon: 'none' })
      this.setData({ activities: [] })
      this.applyFilters()
    })
  },

  onSearchInput(e) {
    this.setData({ keyword: e.detail.value || '' })
    this.applyFilters()
  },

  switchStatus(e) {
    const activeTab = e.currentTarget.dataset.status
    const app = getApp()
    app.globalData.activityStatusFilter = activeTab
    this.setData({ activeTab })
    this.applyFilters()
  },

  switchJoinFilter(e) {
    const joinFilter = e.currentTarget.dataset.filter
    const app = getApp()
    app.globalData.activityJoinFilter = joinFilter
    this.setData({ joinFilter })
    this.applyFilters()
  },

  applyFilters() {
    const { keyword, activeTab, joinFilter, activities: source } = this.data
    const normalized = keyword.trim()
    const filteredActivities = source.filter(item => {
      const matchStatus = item.status === activeTab
      const matchJoin = joinFilter === 'joined'
        ? item.isRegistered
        : joinFilter === 'notJoined'
          ? !item.isRegistered
          : true
      const matchKeyword = !normalized || item.name.includes(normalized)
      return matchStatus && matchJoin && matchKeyword
    }).map(item => ({
      ...item,
      posterUrl: normalizeRemoteUrl(item.posterUrl || item.poster_url),
      displayName: this.truncateTitle(item.name)
    }))

    this.setData({ filteredActivities })
  },

  getStatusText(status) {
    return {
      signup: '报名中',
      active: '进行中',
      ended: '已结束'
    }[status] || ''
  },

  truncateTitle(title) {
    if (!title) return ''
    return title.length > 10 ? `${title.slice(0, 10)}...` : title
  },

  goDetail(e) {
    const id = e.currentTarget.dataset.id
    if (!id) {
      wx.showToast({ title: '活动不存在', icon: 'none' })
      return
    }
    const activity = this.data.activities.find(item => item.id === id) || null
    getApp().globalData.currentActivity = activity
    wx.navigateTo({
      url: `/pages/activity-detail/activity-detail?id=${id}`
    })
  },

  goToProfile() {
    wx.switchTab({ url: '/pages/profile/profile' })
  },

  goToNotifications() {
    wx.showToast({ title: '暂无通知', icon: 'none' })
  }
})
