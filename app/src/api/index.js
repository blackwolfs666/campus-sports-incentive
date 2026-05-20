import axios from 'axios'
import { useUserStore } from '@/stores/user'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// 认证API
export const authApi = {
  login: (code) => api.post('/auth/login', { code }),
  getMe: () => api.get('/auth/me'),
  updateMe: (data) => api.put('/auth/me', data)
}

// 步数API
export const stepsApi = {
  sync: (data) => api.post('/steps/sync', data),
  getToday: () => api.get('/steps/today'),
  getHistory: (days = 7) => api.get(`/steps/history?days=${days}`),
  getHome: () => api.get('/steps/home')
}

// 排行榜API
export const rankingApi = {
  getRanking: (params) => api.get('/ranking', { params }),
  getDepartmentRanking: (params) => api.get('/ranking/department', { params })
}

// 奖品API
export const prizesApi = {
  getList: () => api.get('/prizes'),
  getDetail: (id) => api.get(`/prizes/${id}`),
  getWinners: (prizeId, periodId) => api.get(`/prizes/winners/${prizeId}`, { params: { period_id: periodId } }),
  getMyPrizes: (status) => api.get('/prizes/my/list', { params: { status } }),
  claimPrize: (winnerId) => api.post(`/prizes/claim/${winnerId}`),
  redeemPrize: (claimCode) => api.post('/prizes/redeem', { claim_code: claimCode }),
  getWinnerDetail: (winnerId) => api.get(`/prizes/detail/${winnerId}`)
}

export default api
