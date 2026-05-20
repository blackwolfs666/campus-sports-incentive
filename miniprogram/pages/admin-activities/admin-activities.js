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
    activityEndTime: formatDateTime(item.activityEndTime),
    canGenerateWinners: item.canGenerateWinners === true || (item.myAdminRole === 'owner' && item.status === 'ended')
  }
}

Page({
  data: {
    activities: [],
    filteredActivities: [],
    generatingMap: {},
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
  },

  generateWinners(e) {
    const id = e.currentTarget.dataset.id
    const canGenerate = e.currentTarget.dataset.canGenerate === true || e.currentTarget.dataset.canGenerate === 'true'
    if (!canGenerate) {
      wx.showToast({ title: '活动结束后根管理员可生成', icon: 'none' })
      return
    }
    if (this.data.generatingMap[id]) return

    wx.showModal({
      title: '生成获奖记录',
      content: '将按当前活动规则生成或更新获奖记录，是否继续？',
      confirmText: '生成',
      success: (res) => {
        if (!res.confirm) return
        const app = getApp()
        this.setData({ [`generatingMap.${id}`]: true })
        wx.showLoading({ title: '生成中' })
        app.request({
          url: `/admin/activities/${id}/winners/generate`,
          method: 'POST'
        }).then((result) => {
          wx.showModal({
            title: '生成完成',
            content: `新增：${result.created || 0}\n更新：${result.updated || 0}\n跳过：${result.skipped || 0}\n总数：${result.total || 0}`,
            showCancel: false
          })
        }).catch((err) => {
          const detail = err?.data?.detail || '生成获奖记录失败'
          wx.showToast({ title: String(detail).slice(0, 18), icon: 'none' })
        }).finally(() => {
          wx.hideLoading()
          this.setData({ [`generatingMap.${id}`]: false })
        })
      }
    })
  }
})
