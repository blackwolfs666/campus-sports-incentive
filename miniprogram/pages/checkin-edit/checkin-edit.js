const { BASE_URL, API_BASE_URL } = require('../../config/api')

Page({
  data: {
    activity: null,
    activityId: '',
    content: '',
    images: [],
    steps: 0,
    streakDays: 0,
    isSubmitting: false
  },

  onLoad(options) {
    const activityId = options.activityId || options.id || ''

    if (!activityId) {
      wx.showToast({ title: '活动不存在', icon: 'none' })
      setTimeout(() => wx.navigateBack(), 600)
      return
    }

    this.setData({
      activity: null,
      activityId,
      steps: Number(options.steps || 0),
      streakDays: Number(options.streakDays || 0)
    })
    this.fetchActivity()

    if (!this.data.steps) {
      this.fetchTodaySteps()
    }
  },

  fetchActivity() {
    const app = getApp()
    app.request({
      url: `/activities/${this.data.activityId}`
    }).then((activity) => {
      if (!activity.isRegistered) {
        wx.showToast({ title: '报名后才能发布打卡动态', icon: 'none' })
        setTimeout(() => wx.navigateBack(), 600)
        return
      }
      if (activity.status !== 'active') {
        wx.showToast({ title: '只有进行中的活动才能打卡', icon: 'none' })
        setTimeout(() => wx.navigateBack(), 600)
        return
      }
      this.setData({ activity })
    }).catch((err) => {
      console.error('获取活动状态失败', err)
      wx.showToast({ title: '获取活动失败', icon: 'none' })
      setTimeout(() => wx.navigateBack(), 600)
    })
  },

  fetchTodaySteps() {
    const app = getApp()
    app.request({
      url: '/steps/home'
    }).then((res) => {
      this.setData({
        steps: Number(res.today_steps || 0),
        streakDays: Number(res.streak_days || 0)
      })
    }).catch((err) => {
      console.error('获取今日步数失败', err)
    })
  },

  onContentInput(e) {
    this.setData({ content: e.detail.value })
  },

  chooseImages() {
    const remain = 3 - this.data.images.length
    if (remain <= 0) {
      wx.showToast({ title: '最多选择 3 张图片', icon: 'none' })
      return
    }

    wx.chooseMedia({
      count: remain,
      mediaType: ['image'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        const paths = (res.tempFiles || []).map(item => item.tempFilePath).filter(Boolean)
        this.setData({ images: this.data.images.concat(paths).slice(0, 3) })
      }
    })
  },

  removeImage(e) {
    const index = Number(e.currentTarget.dataset.index)
    const images = this.data.images.filter((_, idx) => idx !== index)
    this.setData({ images })
  },

  previewImage(e) {
    const current = e.currentTarget.dataset.src
    if (!current) return
    wx.previewImage({
      current,
      urls: this.data.images
    })
  },

  submitPost() {
    const content = this.data.content.trim()
    if (!content && this.data.images.length === 0) {
      wx.showToast({ title: '请填写想说的话或选择图片', icon: 'none' })
      return
    }

    if (!this.data.steps) {
      wx.showToast({ title: '请先同步今日步数', icon: 'none' })
      return
    }

    if (this.data.isSubmitting) return

    const app = getApp()
    this.setData({ isSubmitting: true })
    wx.showLoading({ title: '发布中...' })

    Promise.resolve().then(() => {
      return Promise.all(this.data.images.map(path => this.uploadImage(path)))
    }).then((imageUrls) => {
      return app.request({
        url: '/checkins',
        method: 'POST',
        data: {
          activity_id: this.data.activityId,
          content,
          image_urls: imageUrls
        }
      })
    }).then(() => {
      wx.hideLoading()
      this.setData({ isSubmitting: false })
      wx.redirectTo({
        url: `/pages/checkin-feed/checkin-feed?activityId=${this.data.activityId}`
      })
    }).catch((err) => {
      wx.hideLoading()
      this.setData({ isSubmitting: false })
      const detail = err?.data?.detail || '发布失败'
      wx.showToast({ title: String(detail).slice(0, 18), icon: 'none' })
    })
  },

  uploadImage(path) {
    if (/^https?:\/\//.test(path)) {
      return Promise.resolve(path)
    }

    const app = getApp()
    return new Promise((resolve, reject) => {
      wx.uploadFile({
        url: `${API_BASE_URL}/checkins/upload`,
        filePath: path,
        name: 'file',
        header: app.globalData.token
          ? { Authorization: `Bearer ${app.globalData.token}` }
          : {},
        success: (res) => {
          if (res.statusCode !== 200) {
            reject(res)
            return
          }

          try {
            const data = JSON.parse(res.data || '{}')
            const url = data.url || ''
            resolve(url.startsWith('/') ? `${BASE_URL}${url}` : url)
          } catch (err) {
            reject(err)
          }
        },
        fail: reject
      })
    })
  },

  goBack() {
    wx.navigateBack()
  }
})
