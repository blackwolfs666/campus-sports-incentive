Component({
  data: {
    selected: 0,
    list: [
      {
        pagePath: '/pages/index/index',
        text: '首页',
        icon: 'home'
      },
      {
        pagePath: '/pages/activities/activities',
        text: '活动',
        icon: 'flag'
      },
      {
        pagePath: '/pages/profile/profile',
        text: '我的',
        icon: 'person'
      }
    ]
  },

  methods: {
    switchTab(e) {
      const url = e.currentTarget.dataset.path
      const app = getApp()

      if (url === '/pages/activities/activities') {
        app.globalData.activityJoinFilter = 'all'
      }

      wx.switchTab({
        url,
        fail: (err) => {
          console.error('switchTab失败', err)
        }
      })
    }
  }
})
