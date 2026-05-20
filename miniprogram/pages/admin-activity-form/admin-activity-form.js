const { BASE_URL, API_BASE_URL } = require('../../config/api')

const emptyForm = {
  name: '',
  description: '',
  posterUrl: '',
  registerStartTime: '',
  registerEndTime: '',
  activityStartTime: '',
  activityEndTime: '',
  scopeText: '',
  maxParticipants: '',
  scoreRule: [],
  awardRules: [],
  prizes: [{ name: '', quantity: '', image: '' }]
}

function clone(value) {
  return JSON.parse(JSON.stringify(value))
}

function toNumberOrNull(value) {
  if (value === '' || value === null || value === undefined) return null
  const num = Number(value)
  return Number.isFinite(num) ? num : null
}

function normalizePrize(prize) {
  return {
    name: prize.name || '',
    quantity: prize.quantity || '',
    image: prize.image || ''
  }
}

const scoreRuleOptions = [
  { type: 'daily_step_target', label: '单日步数目标', desc: '用于判断用户当天是否达标，例如设置 10000，达到 10000 步才算完成目标。' },
  { type: 'base_score', label: '达标基础积分', desc: '用户当天达到单日步数目标后，获得这部分固定积分。' },
  { type: 'extra_step_score', label: '超额步数加分', desc: '用户超过单日目标后，每多走指定步数，额外增加指定积分。' },
  { type: 'max_daily_score', label: '每日积分上限', desc: '限制用户每天最多可获得的积分，避免异常高步数造成积分失真。' }
]

function scoreRuleLabel(type) {
  const option = scoreRuleOptions.find(item => item.type === type)
  return option ? option.label : '选择规则'
}

function scoreRuleDesc(type) {
  const option = scoreRuleOptions.find(item => item.type === type)
  return option ? option.desc : ''
}

function normalizeScoreRules(raw) {
  if (Array.isArray(raw)) {
    return raw
      .filter(item => item && item.type)
      .map(item => ({
        type: item.type,
        label: item.label || scoreRuleLabel(item.type),
        desc: item.desc || scoreRuleDesc(item.type),
        optionIndex: Math.max(0, scoreRuleOptions.findIndex(option => option.type === item.type)),
        value: item.value === null || item.value === undefined ? '' : String(item.value),
        stepUnit: item.stepUnit === null || item.stepUnit === undefined ? '' : String(item.stepUnit),
        score: item.score === null || item.score === undefined ? '' : String(item.score)
      }))
  }
  if (!raw || typeof raw !== 'object') return []
  const rules = []
  if (raw.dailyStepTarget) {
    rules.push({ type: 'daily_step_target', label: scoreRuleLabel('daily_step_target'), desc: scoreRuleDesc('daily_step_target'), optionIndex: 0, value: String(raw.dailyStepTarget), stepUnit: '', score: '' })
  }
  if (raw.baseScore !== null && raw.baseScore !== undefined) {
    rules.push({ type: 'base_score', label: scoreRuleLabel('base_score'), desc: scoreRuleDesc('base_score'), optionIndex: 1, value: String(raw.baseScore), stepUnit: '', score: '' })
  }
  if (raw.extraStepUnit && raw.extraScore !== null && raw.extraScore !== undefined) {
    rules.push({ type: 'extra_step_score', label: scoreRuleLabel('extra_step_score'), desc: scoreRuleDesc('extra_step_score'), optionIndex: 2, value: '', stepUnit: String(raw.extraStepUnit), score: String(raw.extraScore) })
  }
  if (raw.maxDailyScore) {
    rules.push({ type: 'max_daily_score', label: scoreRuleLabel('max_daily_score'), desc: scoreRuleDesc('max_daily_score'), optionIndex: 3, value: String(raw.maxDailyScore), stepUnit: '', score: '' })
  }
  return rules
}

function hasDuplicateScoreRule(rules) {
  const types = rules.map(item => item.type).filter(Boolean)
  return new Set(types).size !== types.length
}

const awardRuleOptions = [
  { type: 'participation', label: '参与就有奖', desc: '用户报名参与活动即可获得对应奖品资格，不需要填写规则数值。', needValue: false },
  { type: 'target_days', label: '累计达成目标', desc: '用户累计完成单日步数目标达到 X 次后，可获得奖品资格。', needValue: true },
  { type: 'score_rank', label: '积分排行榜', desc: '活动结束后，总积分排行榜前 X 名可获得奖品资格。', needValue: true },
  { type: 'steps_rank', label: '步数总榜', desc: '活动结束后，总步数排行榜前 X 名可获得奖品资格。', needValue: true },
  { type: 'streak_days', label: '连续达成目标', desc: '用户连续完成单日步数目标达到 X 天后，可获得奖品资格。', needValue: true },
  { type: 'checkin_post_days', label: '累计发布打卡动态', desc: '用户累计发布打卡动态达到 X 天后，可获得奖品资格。', needValue: true }
]

function awardRuleOption(type) {
  return awardRuleOptions.find(item => item.type === type)
}

function awardRuleLabel(type) {
  const option = awardRuleOption(type)
  return option ? option.label : '选择规则'
}

function awardRuleDesc(type) {
  const option = awardRuleOption(type)
  return option ? option.desc : ''
}

function awardRuleNeedValue(type) {
  const option = awardRuleOption(type)
  return option ? option.needValue : true
}

function normalizeAwardRules(raw) {
  if (!Array.isArray(raw)) return []
  return raw
    .filter(item => item && item.type)
    .map(item => {
      const optionIndex = awardRuleOptions.findIndex(option => option.type === item.type)
      const type = optionIndex >= 0 ? item.type : 'score_rank'
      const index = Math.max(0, awardRuleOptions.findIndex(option => option.type === type))
      return {
        type,
        label: item.label || awardRuleLabel(type),
        desc: item.desc || awardRuleDesc(type),
        needValue: awardRuleNeedValue(type),
        optionIndex: index,
        value: item.value === null || item.value === undefined ? '' : String(item.value)
      }
    })
}

function hasDuplicateAwardRule(rules) {
  const types = rules.map(item => item.type).filter(Boolean)
  return new Set(types).size !== types.length
}

function normalizeImageUrl(url) {
  if (!url) return ''
  if (/^https?:\/\//.test(url)) return url
  return `${BASE_URL}${url.startsWith('/') ? url : `/${url}`}`
}

function splitScopeText(scopeText) {
  return String(scopeText || '')
    .split(/[、,，/／\s]+/)
    .map(item => item.trim())
    .filter(Boolean)
}

const datetimeFields = ['registerStartTime', 'registerEndTime', 'activityStartTime', 'activityEndTime']

function pad2(value) {
  return String(value).padStart(2, '0')
}

function numberOptions(length) {
  return Array.from({ length }, (_, index) => pad2(index))
}

function normalizeDateTime(value) {
  if (!value) return ''
  const text = String(value).replace('T', ' ').replace(/\.\d+.*$/, '').replace(/Z$/, '').trim()
  if (/^\d{4}-\d{2}-\d{2}$/.test(text)) return `${text} 00:00:00`
  if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/.test(text)) return `${text}:00`
  if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(text)) return text
  return text
}

function splitDateTime(value) {
  const normalized = normalizeDateTime(value)
  const match = normalized.match(/^(\d{4}-\d{2}-\d{2}) (\d{2}):(\d{2}):(\d{2})$/)
  if (!match) {
    return { date: '', hour: '00', minute: '00', second: '00', hourIndex: 0, minuteIndex: 0, secondIndex: 0 }
  }
  const hourIndex = Number(match[2])
  const minuteIndex = Number(match[3])
  const secondIndex = Number(match[4])
  return {
    date: match[1],
    hour: match[2],
    minute: match[3],
    second: match[4],
    hourIndex,
    minuteIndex,
    secondIndex
  }
}

function buildDateTimeParts(form) {
  return datetimeFields.reduce((result, field) => {
    result[field] = splitDateTime(form[field])
    return result
  }, {})
}

function composeDateTime(parts) {
  if (!parts.date) return ''
  return `${parts.date} ${parts.hour || '00'}:${parts.minute || '00'}:${parts.second || '00'}`
}

function toApiDateTime(value) {
  const normalized = normalizeDateTime(value)
  return normalized ? normalized.replace(' ', 'T') : ''
}

function getDateOrderError(form, requireComplete) {
  const values = {
    registerStartTime: normalizeDateTime(form.registerStartTime),
    registerEndTime: normalizeDateTime(form.registerEndTime),
    activityStartTime: normalizeDateTime(form.activityStartTime),
    activityEndTime: normalizeDateTime(form.activityEndTime)
  }
  const allValues = Object.values(values)
  const filledValues = allValues.filter(Boolean)
  if (filledValues.some(item => !/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(item))) {
    return '请完整选择日期和时分秒'
  }
  const toTime = value => value ? new Date(value.replace(' ', 'T')).getTime() : null
  const registerStart = toTime(values.registerStartTime)
  const registerEnd = toTime(values.registerEndTime)
  const activityStart = toTime(values.activityStartTime)
  const activityEnd = toTime(values.activityEndTime)

  if (registerStart !== null && registerEnd !== null && registerStart >= registerEnd) {
    return '报名开始时间必须早于报名结束时间'
  }
  if (registerEnd !== null && activityStart !== null && activityStart < registerEnd) {
    return '活动开始时间不能早于报名结束时间'
  }
  if (activityStart !== null && activityEnd !== null && activityStart >= activityEnd) {
    return '活动开始时间必须早于活动结束时间'
  }
  if (registerEnd !== null && activityEnd !== null && registerEnd > activityEnd) {
    return '报名结束时间不能晚于活动结束时间'
  }
  if (requireComplete && allValues.some(item => !item)) {
    return '请完整选择日期和时分秒'
  }
  return ''
}

Page({
  data: {
    id: '',
    isEdit: false,
    status: '',
    statusText: '',
    readonly: false,
    canEditBasic: true,
    canEditFull: true,
    canEditMax: true,
    enableMaxParticipants: false,
    originalMaxParticipants: 0,
    form: clone(emptyForm),
    dateTimeParts: buildDateTimeParts(emptyForm),
    timeError: '',
    hourOptions: numberOptions(24),
    minuteOptions: numberOptions(60),
    secondOptions: numberOptions(60),
    scoreRuleOptions,
    scoreRuleOptionLabels: scoreRuleOptions.map(item => item.label),
    awardRuleOptions,
    awardRuleOptionLabels: awardRuleOptions.map(item => item.label),
    departments: [],
    showDepartmentPicker: false
  },

  onLoad(options) {
    this.fetchDepartments()
    if (options.id) {
      this.setData({ id: options.id, isEdit: true, readonly: options.readonly === '1' })
      this.fetchActivity()
    }
  },

  fetchDepartments() {
    const app = getApp()
    app.request({
      url: '/admin/departments'
    }).then((res) => {
      const items = Array.isArray(res.items) ? res.items : []
      const departments = items.map(item => ({
        id: item.id,
        name: item.name,
        selected: false
      }))
      this.setData({
        departments: this.markSelectedDepartments(departments, this.data.form.scopeText)
      })
    }).catch((err) => {
      console.error('获取部门列表失败', err)
      this.setData({
        departments: this.markSelectedDepartments([
          { id: 0, name: '全校学生', selected: false },
          { id: -1, name: '计算机科学学院', selected: false },
          { id: -2, name: '软件学院', selected: false },
          { id: -3, name: '网络空间安全学院', selected: false }
        ], this.data.form.scopeText)
      })
    })
  },

  markSelectedDepartments(departments, scopeText) {
    const selectedNames = splitScopeText(scopeText)
    return departments.map(item => ({
      ...item,
      selected: selectedNames.includes(item.name)
    }))
  },

  syncScopeFromDepartments(departments) {
    const selectedNames = departments.filter(item => item.selected).map(item => item.name)
    this.setData({
      departments,
      'form.scopeText': selectedNames.join('、')
    })
  },

  fetchActivity() {
    const app = getApp()
    app.request({
      url: `/admin/activities/${this.data.id}`
    }).then((activity) => {
      const form = {
        ...clone(emptyForm),
        name: activity.name || '',
        description: activity.description || '',
        posterUrl: activity.posterUrl || '',
        registerStartTime: normalizeDateTime(activity.registerStartTime),
        registerEndTime: normalizeDateTime(activity.registerEndTime),
        activityStartTime: normalizeDateTime(activity.activityStartTime),
        activityEndTime: normalizeDateTime(activity.activityEndTime),
        scopeText: activity.scopeText || '',
        maxParticipants: activity.maxParticipants || '',
        scoreRule: normalizeScoreRules(activity.scoreRule),
        awardRules: normalizeAwardRules(activity.awardRules),
        prizes: (activity.prizes || []).length ? activity.prizes.map(normalizePrize) : [{ name: '', quantity: '', image: '' }]
      }
      const readonly = this.data.readonly || !activity.canEdit
      const canEditBasic = !readonly && activity.status !== 'ended'
      const canEditFull = !this.data.isEdit
      const canEditMax = !readonly && ['pre_signup', 'signup'].includes(activity.status)
      const originalMaxParticipants = Number(activity.maxParticipants || 0)
      this.setData({
        form,
        dateTimeParts: buildDateTimeParts(form),
        status: activity.status,
        statusText: activity.statusText,
        canEditBasic,
        canEditFull: !readonly && canEditFull,
        canEditMax,
        originalMaxParticipants,
        enableMaxParticipants: activity.maxParticipants !== null && activity.maxParticipants !== undefined && activity.maxParticipants !== '',
        departments: this.markSelectedDepartments(this.data.departments, form.scopeText)
      })
    }).catch((err) => {
      console.error('获取活动详情失败', err)
      wx.showToast({ title: '获取活动详情失败', icon: 'none' })
    })
  },

  onInput(e) {
    const field = e.currentTarget.dataset.field
    this.setData({ [`form.${field}`]: e.detail.value })
  },

  onNestedInput(e) {
    const group = e.currentTarget.dataset.group
    const field = e.currentTarget.dataset.field
    this.setData({ [`form.${group}.${field}`]: e.detail.value })
  },

  onDateChange(e) {
    if (!this.data.canEditFull) return
    const field = e.currentTarget.dataset.field
    const current = this.data.dateTimeParts[field] || splitDateTime('')
    const parts = { ...current, date: e.detail.value }
    const value = composeDateTime(parts)
    this.updateDateTimeField(field, value)
  },

  onTimePartChange(e) {
    if (!this.data.canEditFull) return
    const field = e.currentTarget.dataset.field
    const part = e.currentTarget.dataset.part
    const index = Number(e.detail.value)
    const current = this.data.dateTimeParts[field] || splitDateTime('')
    if (!current.date) {
      wx.showToast({ title: '请先选择日期', icon: 'none' })
      return
    }
    const optionMap = {
      hour: this.data.hourOptions,
      minute: this.data.minuteOptions,
      second: this.data.secondOptions
    }
    const parts = { ...current, [part]: optionMap[part][index] || '00' }
    const value = composeDateTime(parts)
    this.updateDateTimeField(field, value)
  },

  updateDateTimeField(field, value) {
    const nextForm = {
      ...this.data.form,
      [field]: value
    }
    const message = getDateOrderError(nextForm, false)
    this.setData({
      [`form.${field}`]: value,
      [`dateTimeParts.${field}`]: splitDateTime(value),
      timeError: message
    })
    if (message) {
      wx.showToast({ title: message, icon: 'none' })
    }
  },

  checkDateOrderFeedback() {
    if (!this.data.canEditFull) return
    const message = getDateOrderError(this.data.form, false)
    this.setData({ timeError: message })
    if (message) {
      wx.showToast({ title: message, icon: 'none' })
    }
  },

  toggleMaxParticipants() {
    if (!this.data.canEditMax) return
    const next = !this.data.enableMaxParticipants
    const original = Number(this.data.originalMaxParticipants || 0)
    if (this.data.isEdit && next && original <= 0) {
      wx.showToast({ title: '原活动未设置人数上限，不能改为设置上限', icon: 'none' })
      return
    }
    this.setData({
      enableMaxParticipants: next,
      'form.maxParticipants': next ? (this.data.form.maxParticipants || (original > 0 ? String(original) : '100')) : ''
    })
  },

  stepMaxParticipants(e) {
    if (!this.data.canEditMax || !this.data.enableMaxParticipants) return
    const delta = Number(e.currentTarget.dataset.delta)
    const current = Number(this.data.form.maxParticipants || 0)
    const min = this.data.isEdit && Number(this.data.originalMaxParticipants || 0) > 0
      ? Number(this.data.originalMaxParticipants)
      : 1
    const next = Math.max(min, current + delta)
    if (current + delta < min) {
      wx.showToast({ title: `不能低于原设置的 ${min} 人`, icon: 'none' })
    }
    this.setData({ 'form.maxParticipants': String(next) })
  },

  toggleDepartmentPicker() {
    if (!this.data.canEditFull) return
    this.setData({ showDepartmentPicker: !this.data.showDepartmentPicker })
  },

  toggleDepartment(e) {
    if (!this.data.canEditFull) return
    const index = Number(e.currentTarget.dataset.index)
    const departments = this.data.departments.map((item, idx) => (
      idx === index ? { ...item, selected: !item.selected } : item
    ))
    this.syncScopeFromDepartments(departments)
  },

  choosePoster() {
    if (!this.data.canEditBasic) return
    if (this.data.form.posterUrl) {
      wx.showModal({
        title: '只能上传 1 张海报',
        content: '继续上传会替换当前海报。',
        confirmText: '替换',
        success: (res) => {
          if (res.confirm) this.openPosterChooser()
        }
      })
      return
    }
    this.openPosterChooser()
  },

  openPosterChooser() {
    if (wx.chooseMedia) {
      wx.chooseMedia({
        count: 1,
        mediaType: ['image'],
        sourceType: ['album', 'camera'],
        sizeType: ['compressed'],
        success: (res) => {
          const filePath = res.tempFiles && res.tempFiles[0] && res.tempFiles[0].tempFilePath
          if (filePath) this.uploadPosterFile(filePath)
        }
      })
      return
    }

    wx.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        const filePath = res.tempFilePaths && res.tempFilePaths[0]
        if (filePath) this.uploadPosterFile(filePath)
      }
    })
  },

  uploadPosterFile(filePath) {
    this.uploadImageFile(filePath, (url) => {
      this.setData({ 'form.posterUrl': url })
    })
  },

  uploadImageFile(filePath, onSuccess) {
    const app = getApp()
    const token = app.globalData.token || wx.getStorageSync('token')
    if (!token) {
      app.login().then(() => this.uploadImageFile(filePath, onSuccess)).catch(() => {
        wx.showToast({ title: '请先登录后上传', icon: 'none' })
      })
      return
    }

    wx.showLoading({ title: '上传中' })
    wx.uploadFile({
      url: `${API_BASE_URL}/admin/upload`,
      filePath,
      name: 'file',
      header: {
        Authorization: `Bearer ${token}`
      },
      success: (res) => {
        if (res.statusCode < 200 || res.statusCode >= 300) {
          wx.showToast({ title: '上传失败', icon: 'none' })
          return
        }
        let data = {}
        try {
          data = JSON.parse(res.data || '{}')
        } catch (err) {
          console.error('解析上传结果失败', err)
        }
        if (!data.url) {
          wx.showToast({ title: '上传失败', icon: 'none' })
          return
        }
        onSuccess(normalizeImageUrl(data.url))
        wx.showToast({ title: '上传成功', icon: 'success' })
      },
      fail: (err) => {
        console.error('上传海报失败', err)
        wx.showToast({ title: '上传失败', icon: 'none' })
      },
      complete: () => {
        wx.hideLoading()
      }
    })
  },

  removePoster() {
    if (!this.data.canEditBasic) return
    this.setData({ 'form.posterUrl': '' })
  },

  previewPoster() {
    if (!this.data.form.posterUrl) return
    wx.previewImage({
      urls: [this.data.form.posterUrl],
      current: this.data.form.posterUrl
    })
  },

  choosePrizeImage(e) {
    if (!this.data.canEditFull) return
    const index = Number(e.currentTarget.dataset.index)
    const prize = this.data.form.prizes[index]
    if (!prize) return
    if (prize.image) {
      wx.showModal({
        title: '只能上传 1 张图片',
        content: '继续上传会替换当前奖品图片。',
        confirmText: '替换',
        success: (res) => {
          if (res.confirm) this.openPrizeImageChooser(index)
        }
      })
      return
    }
    this.openPrizeImageChooser(index)
  },

  openPrizeImageChooser(index) {
    if (wx.chooseMedia) {
      wx.chooseMedia({
        count: 1,
        mediaType: ['image'],
        sourceType: ['album', 'camera'],
        sizeType: ['compressed'],
        success: (res) => {
          const filePath = res.tempFiles && res.tempFiles[0] && res.tempFiles[0].tempFilePath
          if (filePath) this.uploadPrizeImageFile(index, filePath)
        }
      })
      return
    }

    wx.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        const filePath = res.tempFilePaths && res.tempFilePaths[0]
        if (filePath) this.uploadPrizeImageFile(index, filePath)
      }
    })
  },

  uploadPrizeImageFile(index, filePath) {
    this.uploadImageFile(filePath, (url) => {
      this.setData({ [`form.prizes[${index}].image`]: url })
    })
  },

  removePrizeImage(e) {
    if (!this.data.canEditFull) return
    const index = Number(e.currentTarget.dataset.index)
    this.setData({ [`form.prizes[${index}].image`]: '' })
  },

  previewPrizeImage(e) {
    const index = Number(e.currentTarget.dataset.index)
    const image = this.data.form.prizes[index] && this.data.form.prizes[index].image
    if (!image) return
    wx.previewImage({
      urls: [image],
      current: image
    })
  },

  addScoreRule() {
    if (!this.data.canEditFull) return
    const usedTypes = this.data.form.scoreRule.map(item => item.type)
    const nextType = this.data.scoreRuleOptions.find(item => !usedTypes.includes(item.type))
    if (!nextType) {
      wx.showToast({ title: '已添加全部规则类型', icon: 'none' })
      return
    }
    this.setData({
      'form.scoreRule': this.data.form.scoreRule.concat([{
        type: nextType.type,
        label: nextType.label,
        desc: nextType.desc,
        optionIndex: this.data.scoreRuleOptions.findIndex(item => item.type === nextType.type),
        value: '',
        stepUnit: '',
        score: ''
      }])
    })
  },

  onScoreRuleTypeChange(e) {
    if (!this.data.canEditFull) return
    const index = Number(e.currentTarget.dataset.index)
    const optionIndex = Number(e.detail.value)
    const option = this.data.scoreRuleOptions[optionIndex]
    if (!option) return
    const rules = this.data.form.scoreRule.map((item, idx) => (
      idx === index ? { ...item, type: option.type, label: option.label, desc: option.desc, optionIndex, value: '', stepUnit: '', score: '' } : item
    ))
    if (hasDuplicateScoreRule(rules)) {
      wx.showToast({ title: '不能重复添加同种积分规则', icon: 'none' })
      return
    }
    this.setData({ 'form.scoreRule': rules })
  },

  onScoreRuleInput(e) {
    const index = Number(e.currentTarget.dataset.index)
    const field = e.currentTarget.dataset.field
    this.setData({ [`form.scoreRule[${index}].${field}`]: e.detail.value })
  },

  removeScoreRule(e) {
    if (!this.data.canEditFull) return
    const index = Number(e.currentTarget.dataset.index)
    this.setData({
      'form.scoreRule': this.data.form.scoreRule.filter((_, idx) => idx !== index)
    })
  },

  addAwardRule() {
    if (!this.data.canEditFull) return
    const usedTypes = this.data.form.awardRules.map(item => item.type)
    const nextType = this.data.awardRuleOptions.find(item => !usedTypes.includes(item.type))
    if (!nextType) {
      wx.showToast({ title: '已添加全部规则类型', icon: 'none' })
      return
    }
    this.setData({
      'form.awardRules': this.data.form.awardRules.concat([{
        type: nextType.type,
        label: nextType.label,
        desc: nextType.desc,
        needValue: nextType.needValue,
        optionIndex: this.data.awardRuleOptions.findIndex(item => item.type === nextType.type),
        value: ''
      }])
    })
  },

  onAwardRuleTypeChange(e) {
    if (!this.data.canEditFull) return
    const index = Number(e.currentTarget.dataset.index)
    const optionIndex = Number(e.detail.value)
    const option = this.data.awardRuleOptions[optionIndex]
    if (!option) return
    const rules = this.data.form.awardRules.map((item, idx) => (
      idx === index ? { ...item, type: option.type, label: option.label, desc: option.desc, needValue: option.needValue, optionIndex, value: '' } : item
    ))
    if (hasDuplicateAwardRule(rules)) {
      wx.showToast({ title: '不能重复添加同种获奖规则', icon: 'none' })
      return
    }
    this.setData({ 'form.awardRules': rules })
  },

  onAwardRuleInput(e) {
    const index = Number(e.currentTarget.dataset.index)
    this.setData({ [`form.awardRules[${index}].value`]: e.detail.value })
  },

  removeAwardRule(e) {
    if (!this.data.canEditFull) return
    const index = Number(e.currentTarget.dataset.index)
    this.setData({
      'form.awardRules': this.data.form.awardRules.filter((_, idx) => idx !== index)
    })
  },

  onPrizeInput(e) {
    const index = Number(e.currentTarget.dataset.index)
    const field = e.currentTarget.dataset.field
    this.setData({ [`form.prizes[${index}].${field}`]: e.detail.value })
  },

  stepPrizeQuantity(e) {
    if (!this.data.canEditFull) return
    const index = Number(e.currentTarget.dataset.index)
    const delta = Number(e.currentTarget.dataset.delta)
    const current = Number(this.data.form.prizes[index]?.quantity || 0)
    const next = Math.max(1, current + delta)
    this.setData({ [`form.prizes[${index}].quantity`]: String(next) })
  },

  addPrize() {
    if (!this.data.canEditFull) return
    this.setData({ 'form.prizes': this.data.form.prizes.concat([{ name: '', quantity: '', image: '' }]) })
  },

  removePrize(e) {
    if (!this.data.canEditFull || this.data.form.prizes.length <= 1) return
    const index = Number(e.currentTarget.dataset.index)
    const prizes = this.data.form.prizes.filter((_, idx) => idx !== index)
    this.setData({ 'form.prizes': prizes.length ? prizes : [{ name: '', quantity: '', image: '' }] })
  },

  buildPayload() {
    const form = this.data.form

    const payload = {
      name: form.name.trim(),
      description: form.description.trim(),
      posterUrl: form.posterUrl.trim(),
      maxParticipants: this.data.enableMaxParticipants ? toNumberOrNull(form.maxParticipants) : null
    }

    if (!this.data.isEdit) {
      Object.assign(payload, {
        registerStartTime: form.registerStartTime,
        registerEndTime: form.registerEndTime,
        activityStartTime: form.activityStartTime,
        activityEndTime: form.activityEndTime,
        scopeText: form.scopeText.trim(),
        scoreRule: form.scoreRule.map(item => ({
          type: item.type,
          label: item.label || scoreRuleLabel(item.type),
          desc: item.desc || scoreRuleDesc(item.type),
          value: item.type === 'extra_step_score' ? null : toNumberOrNull(item.value),
          stepUnit: item.type === 'extra_step_score' ? toNumberOrNull(item.stepUnit) : null,
          score: item.type === 'extra_step_score' ? toNumberOrNull(item.score) : null
        })).filter(item => item.type),
        awardRules: form.awardRules.map(item => ({
          type: item.type,
          label: item.label || awardRuleLabel(item.type),
          desc: item.desc || awardRuleDesc(item.type),
          value: item.needValue === false ? null : toNumberOrNull(item.value)
        })).filter(item => item.type),
        prizes: form.prizes
          .map(item => ({
            name: (item.name || '').trim(),
            quantity: toNumberOrNull(item.quantity),
            image: (item.image || '').trim()
          }))
          .filter(item => item.name)
      })
    }

    if (this.data.isEdit && this.data.status === 'active') {
      return {
        name: payload.name,
        description: payload.description,
        posterUrl: payload.posterUrl
      }
    }
    return payload
  },

  validate(payload) {
    if (!payload.name) return '请填写活动名称'
    if (!payload.description) return '请填写活动描述'
    if (!this.data.isEdit) {
      const dateMessage = getDateOrderError(payload, true)
      if (dateMessage) return dateMessage
      if (!payload.scopeText) return '请选择活动范围'
      if (hasDuplicateScoreRule(payload.scoreRule)) return '不能重复配置同一种积分规则'
      for (const rule of payload.scoreRule) {
        if (!rule.type) return '请选择积分规则类型'
        if (rule.type === 'extra_step_score') {
          if (!rule.stepUnit || rule.stepUnit <= 0) return '请填写有效的超额步数'
          if (!rule.score || rule.score <= 0) return '请填写有效的额外积分'
        } else if (!rule.value || rule.value <= 0) {
          return `请填写有效的${rule.label || '积分规则数值'}`
        }
      }
      if (hasDuplicateAwardRule(payload.awardRules)) return '不能重复配置同一种获奖规则'
      for (const rule of payload.awardRules) {
        if (!rule.type) return '请选择获奖规则类型'
        if (awardRuleNeedValue(rule.type) && (!rule.value || rule.value <= 0)) {
          return `请填写有效的${rule.label || '获奖规则数值'}`
        }
      }
    }
    if (this.data.enableMaxParticipants && (payload.maxParticipants === null || payload.maxParticipants === undefined)) {
      return '请填写最大报名人数'
    }
    if (payload.maxParticipants !== null && payload.maxParticipants !== undefined && payload.maxParticipants <= 0) {
      return '最大报名人数必须大于 0'
    }
    if (this.data.isEdit && this.data.canEditMax) {
      const original = Number(this.data.originalMaxParticipants || 0)
      if (original <= 0 && this.data.enableMaxParticipants) {
        return '原活动未设置人数上限，不能改为设置上限'
      }
      if (original > 0 && this.data.enableMaxParticipants && payload.maxParticipants < original) {
        return `最大报名人数不能低于原设置的 ${original} 人`
      }
    }
    return ''
  },

  submitForm() {
    if (this.data.readonly || (this.data.isEdit && !this.data.canEditBasic)) {
      wx.showToast({ title: '当前只能查看活动信息', icon: 'none' })
      return
    }
    const app = getApp()
    const payload = this.buildPayload()
    const message = this.validate(payload)
    if (message) {
      wx.showToast({ title: message, icon: 'none' })
      return
    }
    if (!this.data.isEdit) {
      payload.registerStartTime = toApiDateTime(payload.registerStartTime)
      payload.registerEndTime = toApiDateTime(payload.registerEndTime)
      payload.activityStartTime = toApiDateTime(payload.activityStartTime)
      payload.activityEndTime = toApiDateTime(payload.activityEndTime)
    }

    app.request({
      url: this.data.isEdit ? `/admin/activities/${this.data.id}` : '/admin/activities',
      method: this.data.isEdit ? 'PUT' : 'POST',
      data: payload
    }).then(() => {
      wx.showToast({ title: this.data.isEdit ? '保存成功' : '发布成功', icon: 'success' })
      setTimeout(() => {
        wx.redirectTo({ url: '/pages/admin-activities/admin-activities' })
      }, 600)
    }).catch((err) => {
      const detail = err?.data?.detail || '保存失败'
      wx.showToast({ title: String(detail).slice(0, 18), icon: 'none' })
    })
  },

  goBack() {
    wx.navigateBack()
  }
})
