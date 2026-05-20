function shortDate(value) {
  if (!value) return ''
  const parts = String(value).split('-')
  return parts.length === 3 ? `${parts[1]}.${parts[2]}` : value
}

function shortStatusLabel(status, label) {
  if (status === 'pre_signup') return '待报名'
  if (status === 'signup_closed') return '待开始'
  return label
}

Page({
  data: {
    summary: {},
    statusDistribution: [],
    checkinTrend: [],
    checkinAverage: 0,
    checkinAverageTop: 0,
    topActivities: []
  },

  onLoad() {
    this.fetchDashboard()
  },

  onShow() {
    this.fetchDashboard()
  },

  fetchDashboard() {
    const app = getApp()
    app.request({
      url: '/admin/dashboard'
    }).then((res) => {
      const statusMax = Math.max(...(res.statusDistribution || []).map(item => item.count || 0), 1)
      const trendMax = Math.max(...(res.checkinTrend || []).map(item => item.count || 0), 1)
      const checkinTrendRaw = res.checkinTrend || []
      const totalCheckins = checkinTrendRaw.reduce((sum, item) => sum + Number(item.count || 0), 0)
      const checkinAverage = checkinTrendRaw.length ? Math.round((totalCheckins / checkinTrendRaw.length) * 10) / 10 : 0
      const chartHeight = 120
      const minBarHeight = 12
      const averageHeight = checkinAverage > 0 ? Math.max(minBarHeight, Math.round((checkinAverage / trendMax) * chartHeight)) : minBarHeight
      this.setData({
        summary: res.summaryCards || {},
        statusDistribution: (res.statusDistribution || []).map(item => ({
          ...item,
          label: shortStatusLabel(item.status, item.label),
          percent: Math.round(((item.count || 0) / statusMax) * 100)
        })),
        checkinTrend: checkinTrendRaw.map(item => ({
          ...item,
          shortDate: shortDate(item.date),
          height: Math.max(minBarHeight, Math.round(((item.count || 0) / trendMax) * chartHeight))
        })),
        checkinAverage,
        checkinAverageTop: chartHeight - averageHeight,
        topActivities: res.topActivities || []
      })
    }).catch((err) => {
      console.error('获取后台看板失败', err)
      wx.showToast({ title: '获取后台看板失败', icon: 'none' })
    })
  },

  goBack() {
    wx.navigateBack()
  },

  goCreate() {
    wx.navigateTo({ url: '/pages/admin-activity-form/admin-activity-form' })
  },

  goList() {
    wx.navigateTo({ url: '/pages/admin-activities/admin-activities' })
  },

  goRedeem() {
    wx.navigateTo({ url: '/pages/admin-redeem/admin-redeem' })
  },

  goEdit(e) {
    const id = e.currentTarget.dataset.id
    if (!id) return
    wx.navigateTo({ url: `/pages/admin-activity-form/admin-activity-form?id=${id}` })
  }
})
