const app = getApp()

function extractClaimCode(value) {
  const text = String(value || '')
  const queryMatch = text.match(/[?&](?:claim_code|code)=([^&]+)/)
  const raw = queryMatch ? decodeURIComponent(queryMatch[1]) : text
  return raw.replace(/\D/g, '').slice(0, 12)
}

Page({
  data: {
    claimCode: '',
    codePreview: '',
    loading: false,
    result: null
  },

  onInput(e) {
    const claimCode = extractClaimCode(e.detail.value)
    this.setData({
      claimCode,
      codePreview: this.formatCode(claimCode),
      result: null
    })
  },

  scanCode() {
    if (this.data.loading) return
    wx.scanCode({
      onlyFromCamera: false,
      scanType: ['qrCode', 'barCode'],
      success: (res) => {
        const claimCode = extractClaimCode(res.result)
        if (!claimCode) {
          wx.showToast({ title: '未识别到兑换码', icon: 'none' })
          return
        }
        this.setData({ claimCode, codePreview: this.formatCode(claimCode), result: null })
        this.confirmRedeem()
      },
      fail: (err) => {
        if (err.errMsg && err.errMsg.includes('cancel')) return
        wx.showToast({ title: '扫码失败', icon: 'none' })
      }
    })
  },

  confirmRedeem() {
    const claimCode = extractClaimCode(this.data.claimCode)
    if (claimCode.length !== 12) {
      wx.showToast({ title: '请输入12位兑换码', icon: 'none' })
      return
    }
    wx.showModal({
      title: '确认核销',
      content: `确定核销兑换码 ${claimCode.slice(0, 4)} ${claimCode.slice(4, 8)} ${claimCode.slice(8, 12)} 吗？`,
      confirmText: '核销',
      success: (res) => {
        if (res.confirm) this.redeem(claimCode)
      }
    })
  },

  redeem(claimCode) {
    if (this.data.loading) return
    this.setData({ loading: true, result: null })
    wx.showLoading({ title: '核销中' })
    app.request({
      url: '/prizes/admin/redeem',
      method: 'POST',
      data: { claim_code: claimCode }
    }).then(res => {
      const result = {
        success: true,
        message: res.message || '核销成功',
        prizeName: res.prize_name || '',
        activityName: res.activity_name || '',
        userName: res.user_name || '',
        status: res.status || ''
      }
      this.setData({ result, claimCode: '', codePreview: '' })
      wx.showToast({ title: '核销成功', icon: 'success' })
    }).catch(err => {
      const detail = err?.data?.detail || '核销失败'
      this.setData({
        result: {
          success: false,
          message: String(detail),
          prizeName: '',
          activityName: '',
          userName: '',
          status: ''
        }
      })
      wx.showToast({ title: String(detail).slice(0, 18), icon: 'none' })
    }).finally(() => {
      wx.hideLoading()
      this.setData({ loading: false })
    })
  },

  clearCode() {
    this.setData({ claimCode: '', codePreview: '', result: null })
  },

  formatCode(code) {
    if (!code) return ''
    return [code.slice(0, 4), code.slice(4, 8), code.slice(8, 12)].filter(Boolean).join(' ')
  },

  goBack() {
    wx.navigateBack()
  }
})
