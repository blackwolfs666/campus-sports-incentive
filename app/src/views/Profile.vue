<template>
  <div class="min-h-screen pb-32">
    <!-- 顶部导航 -->
    <header class="fixed top-0 left-0 right-0 z-50 bg-surface-container-low shadow-sm">
      <div class="flex justify-between items-center px-6 py-4">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-full bg-primary-container flex items-center justify-center overflow-hidden">
            <img v-if="userStore.user?.avatar" :src="userStore.user.avatar" alt="" class="w-full h-full object-cover">
            <span v-else class="material-symbols-outlined text-primary">account_circle</span>
          </div>
          <h1 class="font-headline font-bold text-lg text-primary">我的</h1>
        </div>
        <button class="text-primary hover:opacity-80 transition-opacity">
          <span class="material-symbols-outlined">settings</span>
        </button>
      </div>
    </header>

    <main class="pt-24 px-6 space-y-8">
      <!-- 个人信息卡片 -->
      <section class="relative">
        <div class="bg-surface-container-low rounded-xl p-8 bubbly-shadow overflow-hidden relative">
          <div class="absolute -top-10 -right-10 w-40 h-40 bg-primary-container/20 rounded-full blur-3xl"></div>
          <div class="absolute -bottom-10 -left-10 w-32 h-32 bg-secondary-container/20 rounded-full blur-2xl"></div>
          
          <div class="relative z-10 flex flex-col items-center text-center">
            <div class="w-24 h-24 rounded-full p-1 bg-gradient-to-tr from-primary to-secondary mb-4">
              <div class="w-full h-full rounded-full bg-surface-container-lowest overflow-hidden border-4 border-surface-container-low flex items-center justify-center">
                <img v-if="userStore.user?.avatar" :src="userStore.user.avatar" alt="" class="w-full h-full object-cover">
                <span v-else class="text-primary font-black text-3xl">{{ userStore.user?.name?.charAt(0) || '新' }}</span>
              </div>
            </div>
            <h2 class="font-headline text-2xl font-extrabold text-primary mb-1">{{ userStore.user?.name || '新用户' }}</h2>
            <p class="text-on-surface-variant font-medium flex items-center gap-2">
              <span class="material-symbols-outlined text-sm">school</span>
              {{ userStore.user?.department_name || '未设置部门' }}
            </p>
            
            <div class="mt-6 flex gap-4 w-full">
              <div class="flex-1 bg-surface-container-lowest rounded-lg p-4 text-center">
                <span class="block text-xs font-bold text-secondary uppercase tracking-wider mb-1">今日步数</span>
                <span class="block font-headline text-2xl font-black text-primary">{{ homeData.today_steps.toLocaleString() }}</span>
              </div>
              <div class="flex-1 bg-surface-container-lowest rounded-lg p-4 text-center">
                <span class="block text-xs font-bold text-secondary uppercase tracking-wider mb-1">总里程</span>
                <span class="block font-headline text-2xl font-black text-primary">{{ homeData.total_distance.toFixed(1) }}<small class="text-sm font-bold ml-1">km</small></span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 我的获奖记录 -->
      <section class="space-y-4">
        <div class="flex justify-between items-end px-2">
          <h3 class="font-headline text-xl font-extrabold text-primary flex items-center gap-2">
            <span class="material-symbols-outlined text-tertiary">workspace_premium</span>
            我的获奖记录
          </h3>
          <span class="text-xs font-bold text-on-surface-variant/60">共 {{ myPrizes.length }} 件</span>
        </div>
        
        <div class="grid gap-4">
          <div 
            v-for="prize in myPrizes" 
            :key="prize.id"
            class="bg-surface-container-low rounded-lg p-5 flex items-center justify-between bubbly-shadow relative group"
          >
            <div class="flex items-center gap-4">
              <div 
                class="w-16 h-16 rounded-md flex items-center justify-center"
                :class="getIconBgClass(prize.prize_type)"
              >
                <span class="material-symbols-outlined text-3xl" :class="getIconColor(prize.prize_type)">
                  {{ getIcon(prize.prize_type) }}
                </span>
              </div>
              <div>
                <h4 class="font-bold text-on-surface leading-tight mb-1">{{ prize.prize_name }}</h4>
                <p class="text-xs font-medium text-on-surface-variant">{{ prize.period_name }} · 步数达标奖</p>
              </div>
            </div>
            
            <router-link 
              v-if="prize.status === 'pending'"
              :to="`/redeem/${prize.id}`"
              class="bg-gradient-to-r from-primary to-primary-dim text-on-primary px-5 py-2 rounded-full font-bold text-sm hover:scale-105 transition-transform active:scale-90"
            >
              去兑换
            </router-link>
            <button 
              v-else-if="prize.status === 'claimed'"
              @click="goToRedeem(prize.id)"
              class="bg-tertiary-container text-on-tertiary-container px-5 py-2 rounded-full font-bold text-sm"
            >
              查看码
            </button>
            <span 
              v-else
              class="bg-surface-container-highest text-on-surface-variant px-5 py-2 rounded-full font-bold text-sm opacity-50"
            >
              已兑换
            </span>
          </div>
        </div>
      </section>

      <!-- 统计卡片 -->
      <section class="grid grid-cols-2 gap-4">
        <div class="bg-secondary-container/30 rounded-lg p-6 flex flex-col justify-between h-40 overflow-hidden relative">
          <span class="material-symbols-outlined absolute -bottom-4 -right-4 text-8xl text-secondary/10">potted_plant</span>
          <span class="font-bold text-secondary">健康等级</span>
          <div>
            <span class="block text-3xl font-black text-secondary">Lv.{{ homeData.health_level }}</span>
            <span class="text-xs font-bold text-secondary/60">绿意盎然</span>
          </div>
        </div>
        <div class="bg-tertiary-container/20 rounded-lg p-6 flex flex-col justify-between h-40 overflow-hidden relative">
          <span class="material-symbols-outlined absolute -bottom-4 -right-4 text-8xl text-tertiary/10">history_edu</span>
          <span class="font-bold text-tertiary">连续达标</span>
          <div>
            <span class="block text-3xl font-black text-tertiary">{{ homeData.streak_days }}<small class="text-sm ml-1">天</small></span>
            <span class="text-xs font-bold text-tertiary/60">超越 94% 教师</span>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { stepsApi, prizesApi } from '@/api'

const router = useRouter()
const userStore = useUserStore()

const homeData = ref({
  today_steps: 0,
  total_distance: 0,
  streak_days: 0,
  health_level: 1
})

const myPrizes = ref([])

const getIconBgClass = (type) => {
  const classes = {
    first: 'bg-tertiary-container',
    second: 'bg-secondary-container',
    third: 'bg-primary-container',
    honorable: 'bg-surface-variant'
  }
  return classes[type] || classes.honorable
}

const getIconColor = (type) => {
  const colors = {
    first: 'text-on-tertiary-container',
    second: 'text-on-secondary-container',
    third: 'text-primary',
    honorable: 'text-on-surface-variant'
  }
  return colors[type] || colors.honorable
}

const getIcon = (type) => {
  const icons = {
    first: 'local_cafe',
    second: 'auto_stories',
    third: 'card_membership',
    honorable: 'military_tech'
  }
  return icons[type] || 'military_tech'
}

const goToRedeem = (id) => {
  router.push(`/redeem/${id}`)
}

const fetchData = async () => {
  try {
    const [homeRes, prizesRes] = await Promise.all([
      stepsApi.getHome(),
      prizesApi.getMyPrizes()
    ])
    homeData.value = homeRes
    myPrizes.value = prizesRes
  } catch (e) {
    console.error('获取数据失败', e)
  }
}

onMounted(() => {
  fetchData()
})
</script>
