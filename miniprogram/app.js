const { API_BASE_URL } = require('./config/api')

App({
  globalData: {
    userInfo: null,
    token: null,
    // 开发模式：true=使用模拟数据，false=连接后端
    devMode: false,
    baseUrl: API_BASE_URL,
    activityStatusFilter: 'signup',
    activityJoinFilter: 'all',
    lastStepSyncDate: ''
  },

  onLaunch() {
    // 检查登录状态
    const token = wx.getStorageSync('token')
    this.globalData.lastStepSyncDate = wx.getStorageSync('lastStepSyncDate') || ''
    if (token) {
      this.globalData.token = token
      this.getUserInfo()
    }
  },

  // 获取用户信息
  getUserInfo() {
    return new Promise((resolve, reject) => {
      wx.request({
        url: `${this.globalData.baseUrl}/auth/me`,
        header: {
          'Authorization': `Bearer ${this.globalData.token}`
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

  // 登录
  login() {
    return new Promise((resolve, reject) => {
      wx.login({
        success: (res) => {
          if (res.code) {
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
          } else {
            reject(res)
          }
        },
        fail: reject
      })
    })
  },

  // 封装请求
  request(options) {
    // 开发模式直接返回模拟数据
    console.log('devMode:', this.globalData.devMode)
    if (this.globalData.devMode) {
      console.log('使用模拟数据:', options.url)
      return this.mockRequest(options)
    }
    
    return new Promise((resolve, reject) => {
      // 构建请求头，如果没有token则不发送Authorization
      const header = {
        'Content-Type': 'application/json'
      }
      if (this.globalData.token) {
        header['Authorization'] = `Bearer ${this.globalData.token}`
      }
      
      wx.request({
        url: `${this.globalData.baseUrl}${options.url}`,
        method: options.method || 'GET',
        data: options.data || {},
        header: header,
        success: (res) => {
          if (res.statusCode === 401) {
            if (options._retriedAfterLogin) {
              reject(res)
              return
            }
            // token过期或未登录，尝试重新登录
            this.login().then(() => {
              // 重试请求
              this.request({
                ...options,
                _retriedAfterLogin: true
              }).then(resolve).catch(reject)
            }).catch(reject)
          } else if (res.statusCode === 200) {
            resolve(res.data)
          } else {
            reject(res)
          }
        },
        fail: reject
      })
    })
  },

  // 模拟请求（开发模式）
  mockRequest(options) {
    return new Promise((resolve) => {
      setTimeout(() => {
        const url = options.url
        
        // 首页数据
        if (url === '/steps/home') {
          resolve({
            today_steps: 8432,
            daily_goal: 10000,
            total_steps: 124000,
            total_distance: 87,
            streak_days: 12,
            health_level: 14,
            department_name: '计算机科学学院',
            last_sync_time: '10:00',
            week_challenge: {
              week_total: 52340
            }
          })
        }
        // 同步步数
        else if (url === '/steps/sync') {
          resolve({ success: true, steps: options.data.steps || 8500 })
        }
        // 排行榜
        else if (url === '/ranking') {
          resolve({
            items: [
              { user_id: 1, name: 'Bloom 博士', avatar: '', department_name: '领军人才', steps: 15800, rank: 1 },
              { user_id: 2, name: 'Greene 教授', avatar: '', department_name: '资深学者', steps: 12400, rank: 2 },
              { user_id: 3, name: 'Birch 老师', avatar: '', department_name: '优秀导师', steps: 10900, rank: 3 },
              { user_id: 4, name: 'Samuel Oak 教授', avatar: '', department_name: '生物系', steps: 9432, rank: 4 },
              { user_id: 5, name: 'Sarah Willow 博士', avatar: '', department_name: '物理系', steps: 8901, rank: 5 },
              { user_id: 6, name: 'Julian Elm 教授', avatar: '', department_name: '数学系', steps: 8112, rank: 6 }
            ],
            my_rank: { rank: 12, name: 'Parker 教授', steps: 4328 }
          })
        }
        // 奖品列表
        else if (url === '/prizes') {
          resolve([
            { id: 1, name: '定制学术恒温杯', prize_type: 'first', description: '限量木纹设计' },
            { id: 2, name: '博雅文具礼盒', prize_type: 'second', description: '含钢笔与手工笔记本' },
            { id: 3, name: '校园咖啡季卡', prize_type: 'third', description: '全校5家门店通用' },
            { id: 4, name: '数字勋章与积分', prize_type: 'honorable', description: '额外奖励 500 积分' }
          ])
        }
        // 我的奖品
        else if (url === '/prizes/my/list') {
          resolve([
            { id: 1, prize_name: '定制学术恒温杯', period_name: '2024年第12周', status: 'pending', prize_type: 'first' },
            { id: 2, prize_name: '博雅文具礼盒', period_name: '2024年第10周', status: 'redeemed', prize_type: 'second' }
          ])
        }
        // 默认返回空对象
        else {
          resolve({})
        }
      }, 300) // 模拟网络延迟
    })
  }
})
