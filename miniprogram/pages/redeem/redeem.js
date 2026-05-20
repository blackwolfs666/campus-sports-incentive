const app = getApp()
const { BASE_URL } = require('../../config/api')

const STATUS_TEXT = {
  pending: '待领取',
  claimed: '待核销',
  redeemed: '已核销'
}

const PRIZE_IMAGES = {
  first: '/images/prizes/thermos.svg',
  second: '/images/prizes/stationery.svg',
  third: '/images/prizes/coffee-card.svg',
  honorable: '/images/prizes/medal.svg'
}

function normalizeRemoteUrl(url) {
  if (!url) return ''
  if (/^https?:\/\//.test(url)) return url
  return `${BASE_URL}${url.startsWith('/') ? url : `/${url}`}`
}

Page({
  data: {
    winnerId: null,
    winner: null,
    prize: null,
    code: '',
    qrCodeUrl: '',
    expireDate: '',
    statusText: '',
    isLoading: false
  },

  onLoad(options) {
    this.setData({ winnerId: options.id })
    this.fetchData()
  },

  onPullDownRefresh() {
    this.fetchData().finally(() => wx.stopPullDownRefresh())
  },

  fetchData() {
    const winnerId = this.data.winnerId
    if (!winnerId) {
      wx.showToast({ title: '缺少奖品记录', icon: 'none' })
      return Promise.resolve()
    }

    this.setData({ isLoading: true })
    wx.showLoading({ title: '加载中...' })

    return app.request({
      url: `/prizes/detail/${winnerId}`
    }).then((winner) => {
      this.applyWinner(winner)
      return app.request({
        url: `/prizes/${winner.prize_id}`
      })
    }).then((prize) => {
      this.setData({
        prize: {
          ...prize,
          image: prize.image_url || prize.image || PRIZE_IMAGES[prize.prize_type] || '/images/prizes/medal.svg',
          rank_name: this.buildRankName(this.data.winner)
        }
      })
    }).catch((err) => {
      console.error('获取奖品兑换数据失败', err)
      wx.showToast({ title: '获取奖品失败', icon: 'none' })
    }).finally(() => {
      this.setData({ isLoading: false })
      wx.hideLoading()
    })
  },

  applyWinner(winner) {
    const code = winner.claim_code || ''
    this.setData({
      winner,
      code,
      qrCodeUrl: normalizeRemoteUrl(winner.claim_qrcode),
      expireDate: this.formatDate(winner.claim_deadline),
      statusText: STATUS_TEXT[winner.status] || winner.status || '未知状态'
    })
  },

  buildRankName(winner) {
    if (!winner || !winner.rank) return '获奖奖励'
    return `第 ${winner.rank} 名奖励`
  },

  copyCode() {
    const code = (this.data.code || '').replace(/ /g, '')
    if (!code) {
      wx.showToast({ title: '暂无兑换码', icon: 'none' })
      return
    }

    wx.setClipboardData({
      data: code,
      success: () => {
        wx.showToast({ title: '兑换码已复制', icon: 'success' })
      }
    })
  },

  claimPrize() {
    const winnerId = this.data.winnerId
    if (!winnerId || this.data.isLoading) return

    this.setData({ isLoading: true })
    wx.showLoading({ title: '生成中...' })

    app.request({
      url: `/prizes/claim/${winnerId}`,
      method: 'POST'
    }).then((winner) => {
      this.applyWinner(winner)
      wx.showToast({ title: '兑换码已生成', icon: 'success' })
    }).catch((err) => {
      console.error('生成兑换码失败', err)
      wx.showToast({ title: '生成失败', icon: 'none' })
    }).finally(() => {
      this.setData({ isLoading: false })
      wx.hideLoading()
    })
  },

  refreshStatus() {
    this.fetchData()
  },

  goBack() {
    wx.navigateBack()
  },

  formatDate(value) {
    if (!value) return '未设置'
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) return '未设置'

    const year = date.getFullYear()
    const month = `${date.getMonth() + 1}`.padStart(2, '0')
    const day = `${date.getDate()}`.padStart(2, '0')
    const hours = `${date.getHours()}`.padStart(2, '0')
    const minutes = `${date.getMinutes()}`.padStart(2, '0')
    return `${year}.${month}.${day} ${hours}:${minutes}`
  }
})
