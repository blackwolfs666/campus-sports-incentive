function formatDateTime(value) {
  if (!value) return ''
  const text = String(value).replace('T', ' ').replace(/\.\d+.*$/, '').replace(/Z$/, '').trim()
  if (/^\d{4}-\d{2}-\d{2}$/.test(text)) return `${text} 00:00:00`
  if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/.test(text)) return `${text}:00`
  return text
}

function normalizeActivity(item) {
  return {
    ...item,
    registerStartTime: formatDateTime(item.registerStartTime),
    registerEndTime: formatDateTime(item.registerEndTime),
    activityStartTime: formatDateTime(item.activityStartTime),
    activityEndTime: formatDateTime(item.activityEndTime)
  }
}

Page({
  data: {
    activities: [],
    filteredActivities: [],
    statusFilter: 'signup',
    statusFilters: [
      { key: 'signup', label: '报名中' },
      { key: 'active', label: '进行中' },
      { key: 'ended', label: '已结束' }
    ]
  },

  onLoad() {
    this.fetchActivities()
  },

  onShow() {
    this.fetchActivities()
  },

  fetchActivities() {
    const app = getApp()
    app.request({
      url: '/admin/activities'
    }).then((res) => {
      const activities = (res.items || []).map(normalizeActivity)
      this.setData({ activities }, () => {
        this.applyFilter()
      })
    }).catch((err) => {
      console.error('获取后台活动失败', err)
      wx.showToast({ title: '获取后台活动失败', icon: 'none' })
    })
  },

  applyFilter() {
    const filteredActivities = this.data.activities.filter(item => item.status === this.data.statusFilter)
    this.setData({ filteredActivities })
  },

  changeStatusFilter(e) {
    const statusFilter = e.currentTarget.dataset.status
    this.setData({ statusFilter }, () => {
      this.applyFilter()
    })
  },

  goBack() {
    wx.navigateBack()
  },

  goCreate() {
    wx.navigateTo({ url: '/pages/admin-activity-form/admin-activity-form' })
  },

  goEdit(e) {
    const id = e.currentTarget.dataset.id
    const canEdit = e.currentTarget.dataset.canEdit === true || e.currentTarget.dataset.canEdit === 'true'
    wx.navigateTo({ url: `/pages/admin-activity-form/admin-activity-form?id=${id}${canEdit ? '' : '&readonly=1'}` })
  },

  goAdmins(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: `/pages/admin-activity-admins/admin-activity-admins?id=${id}` })
  }
})
