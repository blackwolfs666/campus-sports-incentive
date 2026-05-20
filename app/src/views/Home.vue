<template>
  <div class="min-h-screen">
    <!-- 顶部导航 -->
    <header class="sticky top-0 z-50 bg-surface-container-low shadow-sm">
      <div class="flex justify-between items-center px-6 py-4">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-full bg-primary-container flex items-center justify-center overflow-hidden">
            <img v-if="userStore.user?.avatar" :src="userStore.user.avatar" alt="头像" class="w-full h-full object-cover">
            <span v-else class="material-symbols-outlined text-primary">account_circle</span>
          </div>
          <h1 class="text-primary font-headline font-bold text-lg">邮青步纪</h1>
        </div>
        <button class="text-primary hover:opacity-80 transition-opacity">
          <span class="material-symbols-outlined">notifications</span>
        </button>
      </div>
    </header>

    <main class="max-w-md mx-auto px-6 pt-8 pb-32">
      <!-- 步数圆环 -->
      <section class="relative flex flex-col items-center mb-10">
        <div class="absolute -top-6 left-1/2 -translate-x-1/2 z-10">
          <span class="bg-tertiary-container text-on-tertiary-container px-4 py-1 rounded-full font-bold text-xs tracking-widest shadow-sm">
            {{ userStore.user?.name || '新用户' }}
          </span>
        </div>
        
        <!-- 圆环 -->
        <div class="relative w-72 h-72 flex items-center justify-center">
          <svg class="absolute inset-0 w-full h-full -rotate-90" viewBox="0 0 100 100">
            <circle class="text-surface-container-high" cx="50" cy="50" fill="none" r="45" stroke="currentColor" stroke-width="8" />
            <circle 
              class="vine-stroke" 
              cx="50" cy="50" fill="none" r="45" 
              stroke="url(#vineGradient)" 
              stroke-width="10"
              :stroke-dashoffset="1000 - (homeData.today_steps / homeData.daily_goal) * 750"
            />
            <defs>
              <linearGradient id="vineGradient" x1="0%" x2="100%" y1="0%" y2="100%">
                <stop offset="0%" style="stop-color:#176a21" />
                <stop offset="100%" style="stop-color:#9df197" />
              </linearGradient>
            </defs>
          </svg>
          
          <!-- 中心内容 -->
          <div class="z-10 text-center flex flex-col items-center">
            <span class="text-secondary font-bold text-sm mb-1">今日步数</span>
            <h2 class="text-primary font-black text-6xl tracking-tighter leading-none mb-2">
              {{ homeData.today_steps.toLocaleString() }}
            </h2>
            <div class="flex items-center gap-1 text-on-surface-variant font-medium text-sm">
              <span class="material-symbols-outlined text-sm">flag</span>
              <span>目标: {{ homeData.daily_goal.toLocaleString() }} 步</span>
            </div>
          </div>
          
          <!-- 装饰叶子 -->
          <div class="absolute -top-4 right-12 w-16 h-16 bg-primary rounded-[2rem_2rem_0_2rem] rotate-12 shadow-lg flex items-center justify-center">
            <span class="material-symbols-outlined text-on-primary text-3xl">eco</span>
          </div>
        </div>
        
        <p class="mt-6 text-center text-secondary font-semibold">
          "步履不停，共建绿色校园！"
        </p>
      </section>

      <!-- Bento Grid -->
      <div class="grid grid-cols-2 gap-4">
        <!-- 部门卡片 -->
        <div class="col-span-2 bg-surface-container-low p-6 rounded-xl flex items-center gap-4 transition-all hover:bg-surface-container-high group bubbly-shadow">
          <div class="w-12 h-12 rounded-lg bg-primary-container flex items-center justify-center text-primary group-hover:scale-110 transition-transform">
            <span class="material-symbols-outlined text-2xl">school</span>
          </div>
          <div>
            <span class="block text-xs font-bold text-on-surface-variant uppercase tracking-wider">所属部门</span>
            <h3 class="font-headline font-bold text-on-surface">{{ homeData.department_name || '未设置' }}</h3>
          </div>
        </div>

        <!-- 同步步数 -->
        <button @click="syncSteps" class="bg-tertiary-container p-5 rounded-xl flex flex-col justify-between aspect-square hover:shadow-lg transition-all group active:scale-95">
          <div class="flex justify-between items-start">
            <div class="w-10 h-10 bg-on-tertiary-container/10 rounded-full flex items-center justify-center">
              <span class="material-symbols-outlined text-on-tertiary-container">cloud_sync</span>
            </div>
            <span class="material-symbols-outlined text-on-tertiary-container/30 group-hover:text-on-tertiary-container transition-colors">arrow_outward</span>
          </div>
          <div>
            <h4 class="font-headline font-bold text-on-tertiary-container leading-tight mb-1">同步步数</h4>
            <p class="text-[10px] font-bold text-on-tertiary-container/70">
              {{ homeData.last_sync_time ? '最后同步: ' + formatTime(homeData.last_sync_time) : '点击同步' }}
            </p>
          </div>
        </button>

        <!-- 运动连胜 -->
        <div class="bg-surface-container-highest p-5 rounded-xl flex flex-col justify-between aspect-square">
          <div class="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center">
            <span class="material-symbols-outlined text-primary">bolt</span>
          </div>
          <div>
            <h4 class="font-headline font-bold text-on-surface-variant leading-tight mb-1">运动连胜</h4>
            <div class="flex items-baseline gap-1">
              <span class="text-2xl font-black text-primary">{{ homeData.streak_days }}</span>
              <span class="text-xs font-bold text-on-surface-variant">天</span>
            </div>
          </div>
        </div>

        <!-- 周挑战 -->
        <div class="col-span-2 relative overflow-hidden bg-primary text-on-primary p-6 rounded-xl mt-2 group bubbly-shadow">
          <div class="relative z-10">
            <h4 class="font-headline font-extrabold text-xl mb-1">周挑战</h4>
            <p class="text-sm opacity-90 max-w-[70%]">
              本周累计 {{ homeData.week_challenge?.week_total?.toLocaleString() || 0 }} 步，继续加油！
            </p>
            <router-link to="/ranking" class="mt-4 inline-block bg-primary-container text-on-primary-container px-4 py-2 rounded-full text-sm font-bold hover:bg-white transition-colors">
              查看排行
              <span class="material-symbols-outlined text-sm align-middle">chevron_right</span>
            </router-link>
          </div>
          <div class="absolute -right-8 -bottom-8 w-40 h-40 bg-primary-dim rounded-full opacity-50 group-hover:scale-110 transition-transform"></div>
          <span class="absolute right-4 top-4 material-symbols-outlined text-6xl opacity-20 rotate-12">forest</span>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { stepsApi } from '@/api'

const userStore = useUserStore()

const homeData = ref({
  today_steps: 0,
  total_steps: 0,
  total_distance: 0,
  streak_days: 0,
  health_level: 1,
  daily_goal: 10000,
  department_name: '',
  last_sync_time: null,
  week_challenge: null
})

const loading = ref(false)

const fetchHomeData = async () => {
  try {
    const res = await stepsApi.getHome()
    homeData.value = res
  } catch (e) {
    console.error('获取首页数据失败', e)
  }
}

const syncSteps = async () => {
  loading.value = true
  try {
    if (!window.wx?.login || !window.wx?.getWeRunData) {
      throw new Error('当前环境无法获取微信运动数据')
    }
    const code = await new Promise((resolve, reject) => {
      window.wx.login({
        success: (res) => res.code ? resolve(res.code) : reject(new Error('微信登录失败')),
        fail: reject
      })
    })
    const runData = await new Promise((resolve, reject) => {
      window.wx.getWeRunData({
        success: resolve,
        fail: reject
      })
    })
    await stepsApi.sync({
      code,
      encryptedData: runData.encryptedData,
      iv: runData.iv
    })
    await fetchHomeData()
  } catch (e) {
    console.error('同步步数失败', e)
  } finally {
    loading.value = false
  }
}

const formatTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

onMounted(() => {
  fetchHomeData()
})
</script>
