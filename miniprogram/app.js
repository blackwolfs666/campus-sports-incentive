const { API_BASE_URL } = require('./config/api')

App({
  globalData: {
    userInfo: null,
    token: null,
    baseUrl: API_BASE_URL,
    activityStatusFilter: 'signup',
    activityJoinFilter: 'all',
    lastStepSyncDate: '',
    currentActivity: null
  },

  onLaunch() {
    const token = wx.getStorageSync('token')
    this.globalData.lastStepSyncDate = wx.getStorageSync('lastStepSyncDate') || ''
    if (token) {
      this.globalData.token = token
      this.getUserInfo()
    }
  },

  getUserInfo() {
    return new Promise((resolve, reject) => {
      wx.request({
        url: `${this.globalData.baseUrl}/auth/me`,
        header: {
          Authorization: `Bearer ${this.globalData.token}`
        },
        success: (res) => {
          if (res.statusCode === 200) {
            this.globalData.userInfo = res.data
            resolve(res.data)
          } else {
            reject(res)
          }
        },
        fail: reject
      })
    })
  },

  login() {
    return new Promise((resolve, reject) => {
      wx.login({
        success: (res) => {
          if (!res.code) {
            reject(res)
            return
          }

          wx.request({
            url: `${this.globalData.baseUrl}/auth/login`,
            method: 'POST',
            data: { code: res.code },
            success: (response) => {
              if (response.statusCode === 200) {
                this.globalData.token = response.data.token
                this.globalData.userInfo = response.data.user
                wx.setStorageSync('token', response.data.token)
                resolve(response.data)
              } else {
                reject(response)
              }
            },
            fail: reject
          })
        },
        fail: reject
      })
    })
  },

  request(options) {
    return new Promise((resolve, reject) => {
      const header = {
        'Content-Type': 'application/json'
      }
      if (this.globalData.token) {
        header.Authorization = `Bearer ${this.globalData.token}`
      }

      wx.request({
        url: `${this.globalData.baseUrl}${options.url}`,
        method: options.method || 'GET',
        data: options.data || {},
        header,
        success: (res) => {
          if (res.statusCode === 401) {
            if (options._retriedAfterLogin) {
              reject(res)
              return
            }

            this.login().then(() => {
              this.request({
                ...options,
                _retriedAfterLogin: true
              }).then(resolve).catch(reject)
            }).catch(reject)
            return
          }

          if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve(res.data)
            return
          }

          reject(res)
        },
        fail: reject
      })
    })
  }
})
