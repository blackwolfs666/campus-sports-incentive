const { getActivityById } = require('../../data/mock-activities')

function formatDateTime(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  const month = `${date.getMonth() + 1}`.padStart(2, '0')
  const day = `${date.getDate()}`.padStart(2, '0')
  const hour = `${date.getHours()}`.padStart(2, '0')
  const minute = `${date.getMinutes()}`.padStart(2, '0')
  return `${month}.${day} ${hour}:${minute}`
}

function normalizePost(item) {
  return {
    ...item,
    createdText: formatDateTime(item.created_at),
    images: Array.isArray(item.image_urls) ? item.image_urls : []
  }
}

Page({
  data: {
    activity: null,
    activityId: '',
    scope: 'all',
    posts: [],
    isLoading: false,
    isEnded: false
  },

  onLoad(options) {
    const activityId = options.activityId || options.id || ''
    const activity = getActivityById(activityId)

    if (!activityId) {
      wx.showToast({ title: '活动不存在', icon: 'none' })
      setTimeout(() => wx.navigateBack(), 600)
      return
    }

    this.setData({
      activity,
      activityId,
      isEnded: activity?.status === 'ended'
    })
    this.fetchActivity()
    this.fetchPosts()
  },

  fetchActivity() {
    const app = getApp()
    app.request({
      url: `/activities/${this.data.activityId}`
    }).then((activity) => {
      if (!activity.isRegistered) {
        wx.showToast({ title: '报名后才能查看打卡动态', icon: 'none' })
        setTimeout(() => wx.navigateBack(), 600)
        return
      }
      if (activity.status !== 'active') {
        wx.showToast({ title: '只有进行中的活动才能查看打卡动态', icon: 'none' })
        setTimeout(() => wx.navigateBack(), 600)
        return
      }
      this.setData({
        activity,
        isEnded: false
      })
    }).catch((err) => {
      console.warn('获取活动状态失败，使用本地活动配置', err)
      if (!this.data.activity || !this.data.activity.isRegistered) {
        wx.showToast({ title: '报名后才能查看打卡动态', icon: 'none' })
        setTimeout(() => wx.navigateBack(), 600)
      }
    })
  },

  onShow() {
    if (this.data.activityId) {
      this.fetchPosts()
    }
  },

  switchScope(e) {
    const scope = e.currentTarget.dataset.scope
    if (!scope || scope === this.data.scope) return
    this.setData({ scope }, () => this.fetchPosts())
  },

  fetchPosts() {
    const app = getApp()
    this.setData({ isLoading: true })

    app.request({
      url: `/checkins?activity_id=${encodeURIComponent(this.data.activityId)}&scope=${this.data.scope}`
    }).then((res) => {
      this.setData({
        posts: (res.items || []).map(normalizePost),
        isLoading: false
      })
    }).catch((err) => {
      console.error('获取打卡动态失败', err)
      this.setData({ isLoading: false })
      wx.showToast({ title: '获取动态失败', icon: 'none' })
    })
  },

  cheerPost(e) {
    const id = Number(e.currentTarget.dataset.id)
    if (!id) return

    const app = getApp()
    app.request({
      url: `/checkins/${id}/cheer`,
      method: 'POST'
    }).then((res) => {
      const posts = this.data.posts.map((item) => {
        if (item.id !== id) return item
        return {
          ...item,
          cheer_count: res.cheer_count,
          has_cheered: res.has_cheered
        }
      })
      this.setData({ posts })
    }).catch((err) => {
      console.error('加油失败', err)
      wx.showToast({ title: '操作失败', icon: 'none' })
    })
  },

  previewImage(e) {
    const current = e.currentTarget.dataset.src
    const postId = Number(e.currentTarget.dataset.postId)
    const post = this.data.posts.find(item => item.id === postId)
    const urls = post ? post.images : []
    if (!current || !urls.length) return
    wx.previewImage({ current, urls })
  },

  goBack() {
    wx.navigateBack()
  },

  goCheckin() {
    if (this.data.isEnded) {
      wx.showToast({ title: '活动已结束，不能打卡', icon: 'none' })
      return
    }
    wx.navigateBack()
  }
})
