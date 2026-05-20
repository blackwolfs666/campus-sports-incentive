Component({
  data: {
    selected: 0,
    list: [
      {
        pagePath: "/pages/index/index",
        text: "首页",
        icon: "/images/icons/home.svg",
        activeIcon: "/images/icons/home.svg"
      },
      {
        pagePath: "/pages/ranking/ranking",
        text: "排行",
        icon: "/images/icons/leaderboard.svg",
        activeIcon: "/images/icons/leaderboard.svg"
      },
      {
        pagePath: "/pages/prizes/prizes",
        text: "奖品",
        icon: "/images/icons/emoji_events.svg",
        activeIcon: "/images/icons/emoji_events.svg"
      },
      {
        pagePath: "/pages/profile/profile",
        text: "我的",
        icon: "/images/icons/person.svg",
        activeIcon: "/images/icons/person.svg"
      }
    ]
  },

  methods: {
    switchTab(e) {
      const data = e.currentTarget.dataset
      const url = data.path
      
      wx.switchTab({ url })
      this.setData({
        selected: data.index
      })
    }
  }
})
