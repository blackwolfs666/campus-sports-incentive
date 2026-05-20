<template>
  <div class="min-h-screen bg-background flex flex-col items-center justify-center px-6">
    <!-- Logo -->
    <div class="w-24 h-24 rounded-full bg-primary-container flex items-center justify-center mb-8 shadow-lg">
      <span class="material-symbols-outlined text-primary text-5xl">park</span>
    </div>
    
    <h1 class="font-headline text-3xl font-extrabold text-primary mb-2">邮青步纪</h1>
    <p class="text-on-surface-variant mb-12">步履不停，共建绿色校园</p>

    <!-- 登录按钮 -->
    <button 
      @click="handleLogin"
      :disabled="loading"
      class="w-full max-w-xs bg-primary text-on-primary py-4 rounded-full font-bold text-lg shadow-lg hover:bg-primary-dim transition-colors active:scale-95 disabled:opacity-50"
    >
      <span v-if="loading">登录中...</span>
      <span v-else class="flex items-center justify-center gap-2">
        <span class="material-symbols-outlined">login</span>
        微信一键登录
      </span>
    </button>

    <!-- 用户协议 -->
    <p class="text-xs text-on-surface-variant mt-8 text-center max-w-xs">
      登录即表示同意
      <a href="#" class="text-primary">用户协议</a>
      和
      <a href="#" class="text-primary">隐私政策</a>
    </p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)

const handleLogin = async () => {
  loading.value = true
  try {
    // 模拟微信登录 - 实际项目中需要调用微信SDK获取code
    // wx.login({
    //   success: async (res) => {
    //     await userStore.login(res.code)
    //     router.push('/')
    //   }
    // })
    
    // 开发环境模拟登录
    const mockCode = 'mock_wx_code_' + Date.now()
    await userStore.login(mockCode)
    router.push('/')
  } catch (e) {
    console.error('登录失败', e)
    alert('登录失败，请重试')
  } finally {
    loading.value = false
  }
}
</script>
