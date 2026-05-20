function formatDisplayUserId(value) {
  const num = Number(value)
  if (!Number.isFinite(num) || num <= 0) return ''
  return `U${String(num).padStart(7, '0')}`
}

function normalizeAdmin(item) {
  return {
    ...item,
    displayUserId: item.displayUserId || formatDisplayUserId(item.userId)
  }
}

function normalizeUser(user) {
  if (!user) return null
  return {
    ...user,
    displayUserId: user.displayUserId || formatDisplayUserId(user.id)
  }
}

Page({
  data: {
    activityId: '',
    activityStatus: '',
    activityStatusText: '',
    admins: [],
    canManage: false,
    searchUserId: '',
    candidate: null
  },

  onLoad(options) {
    if (!options.id) {
      wx.showToast({ title: '活动不存在', icon: 'none' })
      setTimeout(() => wx.navigateBack(), 600)
      return
    }
    this.setData({ activityId: options.id })
    this.fetchAdmins()
  },

  fetchAdmins() {
    const app = getApp()
    app.request({
      url: `/admin/activities/${this.data.activityId}/admins`
    }).then((res) => {
      this.setData({
        admins: (res.items || []).map(normalizeAdmin),
        canManage: !!res.canManage,
        activityStatus: res.activityStatus || '',
        activityStatusText: res.activityStatusText || ''
      })
    }).catch((err) => {
      console.error('获取管理员列表失败', err)
      wx.showToast({ title: '获取管理员失败', icon: 'none' })
    })
  },

  onSearchInput(e) {
    this.setData({ searchUserId: e.detail.value, candidate: null })
  },

  searchUser() {
    if (!this.data.canManage) return
    const userCode = String(this.data.searchUserId || '').trim()
    if (!userCode) {
      wx.showToast({ title: '请输入用户ID', icon: 'none' })
      return
    }
    const app = getApp()
    app.request({
      url: `/admin/users/${encodeURIComponent(userCode)}`
    }).then((user) => {
      this.setData({ candidate: normalizeUser(user) })
    }).catch((err) => {
      const detail = err?.data?.detail || '未找到该用户'
      wx.showToast({ title: String(detail), icon: 'none' })
    })
  },

  confirmAdd() {
    if (!this.data.canManage || !this.data.candidate) return
    const app = getApp()
    app.request({
      url: `/admin/activities/${this.data.activityId}/admins`,
      method: 'POST',
      data: { userId: this.data.candidate.id }
    }).then(() => {
      wx.showToast({ title: '添加成功', icon: 'success' })
      this.setData({ candidate: null, searchUserId: '' })
      this.fetchAdmins()
    }).catch((err) => {
      const detail = err?.data?.detail || '添加失败'
      wx.showToast({ title: String(detail).slice(0, 18), icon: 'none' })
    })
  },

  removeAdmin(e) {
    if (!this.data.canManage) return
    const userId = Number(e.currentTarget.dataset.userId)
    const admin = this.data.admins.find(item => Number(item.userId) === userId)
    const displayUserId = admin ? admin.displayUserId : `U${String(userId).padStart(7, '0')}`
    wx.showModal({
      title: '移出管理员',
      content: `确认移出用户 ${displayUserId} 吗？`,
      success: (res) => {
        if (!res.confirm) return
        const app = getApp()
        app.request({
          url: `/admin/activities/${this.data.activityId}/admins/${userId}`,
          method: 'DELETE'
        }).then(() => {
          wx.showToast({ title: '已移出', icon: 'success' })
          this.fetchAdmins()
        }).catch((err) => {
          const detail = err?.data?.detail || '移出失败'
          wx.showToast({ title: String(detail).slice(0, 18), icon: 'none' })
        })
      }
    })
  },

  goBack() {
    wx.navigateBack()
  }
})
