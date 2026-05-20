import { defineStore } from 'pinia'
import { ref } from 'vue'
import { authApi } from '@/api'

export const useUserStore = defineStore('user', () => {
  const user = ref(null)
  const token = ref(localStorage.getItem('token') || '')

  const login = async (code) => {
    const res = await authApi.login(code)
    token.value = res.token
    user.value = res.user
    localStorage.setItem('token', res.token)
    return res
  }

  const fetchUser = async () => {
    if (!token.value) return null
    try {
      const res = await authApi.getMe()
      user.value = res
      return res
    } catch (e) {
      logout()
      throw e
    }
  }

  const updateUser = async (data) => {
    const res = await authApi.updateMe(data)
    user.value = res
    return res
  }

  const logout = () => {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
  }

  return {
    user,
    token,
    login,
    fetchUser,
    updateUser,
    logout
  }
})
