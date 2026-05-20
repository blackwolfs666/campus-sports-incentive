<template>
  <div class="min-h-screen pb-32">
    <!-- 顶部导航 -->
    <header class="sticky top-0 z-50 bg-surface-container-low shadow-sm">
      <div class="flex justify-between items-center px-6 py-4">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-full bg-primary-container flex items-center justify-center border-2 border-primary">
            <span class="material-symbols-outlined text-primary">park</span>
          </div>
          <h1 class="text-primary font-headline font-bold text-lg">学术之林</h1>
        </div>
        <button class="text-primary hover:opacity-80 transition-opacity">
          <span class="material-symbols-outlined">notifications</span>
        </button>
      </div>
    </header>

    <main class="max-w-2xl mx-auto px-4 mt-6">
      <!-- 切换按钮 -->
      <div class="bg-surface-container-low rounded-xl p-1.5 mb-6 flex items-center">
        <button 
          @click="scope = 'all'"
          class="flex-1 py-3 px-4 rounded-xl font-bold text-sm transition-all"
          :class="scope === 'all' ? 'bg-primary text-on-primary shadow-sm' : 'text-on-surface-variant'"
        >
          全校
        </button>
        <button 
          @click="scope = 'department'"
          class="flex-1 py-3 px-4 rounded-xl font-bold text-sm transition-all"
          :class="scope === 'department' ? 'bg-primary text-on-primary shadow-sm' : 'text-on-surface-variant'"
        >
          部门
        </button>
      </div>

      <!-- 时间筛选 -->
      <div class="flex gap-3 overflow-x-auto hide-scrollbar mb-8 pb-2">
        <button 
          v-for="period in periodTypes" 
          :key="period.value"
          @click="periodType = period.value"
          class="flex-shrink-0 px-6 py-2 rounded-md font-bold text-sm flex items-center gap-2 transition-all"
          :class="periodType === period.value 
            ? 'bg-secondary-container text-on-secondary-container' 
            : 'bg-surface-container-highest text-on-surface-variant'"
        >
          <span class="material-symbols-outlined text-[18px]">{{ period.icon }}</span>
          {{ period.label }}
        </button>
      </div>

      <!-- 前三名领奖台 -->
      <div class="flex items-end justify-center gap-4 mb-10 mt-12">
        <!-- 第二名 -->
        <div v-if="ranking[1]" class="flex flex-col items-center flex-1 max-w-[100px]">
          <div class="relative mb-4">
            <div class="w-16 h-16 rounded-full bg-surface-container-highest border-4 border-outline-variant overflow-hidden">
              <img v-if="ranking[1].avatar" :src="ranking[1].avatar" alt="" class="w-full h-full object-cover">
              <span v-else class="w-full h-full flex items-center justify-center text-secondary font-bold text-xl">
                {{ ranking[1].name.charAt(0) }}
              </span>
            </div>
            <div class="absolute -bottom-2 -right-2 bg-slate-300 w-8 h-8 rounded-full flex items-center justify-center text-slate-800 font-bold shadow-lg border-2 border-white text-xs">
              2
            </div>
          </div>
          <p class="font-bold text-xs text-center truncate w-full">{{ ranking[1].name }}</p>
          <p class="font-black text-secondary text-sm">{{ ranking[1].steps.toLocaleString() }}</p>
        </div>

        <!-- 第一名 -->
        <div v-if="ranking[0]" class="flex flex-col items-center flex-1 max-w-[120px] -mt-8">
          <div class="relative mb-4">
            <div class="absolute -top-6 left-1/2 -translate-x-1/2 text-tertiary-container">
              <span class="material-symbols-outlined text-4xl">military_tech</span>
            </div>
            <div class="w-24 h-24 rounded-full bg-primary-container border-4 border-tertiary-container overflow-hidden shadow-xl">
              <img v-if="ranking[0].avatar" :src="ranking[0].avatar" alt="" class="w-full h-full object-cover">
              <span v-else class="w-full h-full flex items-center justify-center text-primary font-black text-2xl">
                {{ ranking[0].name.charAt(0) }}
              </span>
            </div>
            <div class="absolute -bottom-3 -right-3 bg-tertiary-container w-10 h-10 rounded-full flex items-center justify-center text-on-tertiary-container font-black text-lg shadow-lg border-4 border-white">
              1
            </div>
          </div>
          <p class="font-black text-sm text-center truncate w-full">{{ ranking[0].name }}</p>
          <p class="font-black text-primary text-base">{{ ranking[0].steps.toLocaleString() }}</p>
        </div>

        <!-- 第三名 -->
        <div v-if="ranking[2]" class="flex flex-col items-center flex-1 max-w-[100px]">
          <div class="relative mb-4">
            <div class="w-16 h-16 rounded-full bg-surface-container-highest border-4 border-orange-300 overflow-hidden">
              <img v-if="ranking[2].avatar" :src="ranking[2].avatar" alt="" class="w-full h-full object-cover">
              <span v-else class="w-full h-full flex items-center justify-center text-secondary font-bold text-xl">
                {{ ranking[2].name.charAt(0) }}
              </span>
            </div>
            <div class="absolute -bottom-2 -right-2 bg-orange-400 w-8 h-8 rounded-full flex items-center justify-center text-orange-950 font-bold shadow-lg border-2 border-white text-xs">
              3
            </div>
          </div>
          <p class="font-bold text-xs text-center truncate w-full">{{ ranking[2].name }}</p>
          <p class="font-black text-secondary text-sm">{{ ranking[2].steps.toLocaleString() }}</p>
        </div>
      </div>

      <!-- 排行榜列表 -->
      <div class="space-y-4 mb-8">
        <div 
          v-for="(item, idx) in ranking.slice(3)" 
          :key="item.user_id"
          class="bg-surface-container-low p-4 rounded-lg flex items-center gap-4 hover:bg-surface-container-high transition-all bubbly-shadow"
        >
          <div class="w-10 text-center font-black text-outline italic text-lg">
            {{ String(idx + 4).padStart(2, '0') }}
          </div>
          <div class="w-12 h-12 rounded-full bg-surface-variant overflow-hidden">
            <img v-if="item.avatar" :src="item.avatar" alt="" class="w-full h-full object-cover">
            <span v-else class="w-full h-full flex items-center justify-center text-secondary font-bold">
              {{ item.name.charAt(0) }}
            </span>
          </div>
          <div class="flex-1">
            <h4 class="font-bold text-sm">{{ item.name }}</h4>
            <p class="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">
              {{ item.department_name || '未知部门' }}
            </p>
          </div>
          <div class="text-right">
            <p class="font-black text-secondary">{{ item.steps.toLocaleString() }}</p>
            <p class="text-[10px] text-outline font-bold">步</p>
          </div>
        </div>
      </div>
    </main>

    <!-- 当前用户排名卡片 -->
    <div v-if="myRank" class="fixed bottom-[88px] left-0 right-0 px-4 z-40">
      <div class="max-w-2xl mx-auto bg-primary-container p-5 rounded-lg flex items-center gap-4 shadow-lg border-t-2 border-white/50">
        <div class="w-10 text-center font-black text-primary italic text-lg">{{ myRank.rank }}</div>
        <div class="w-14 h-14 rounded-full bg-primary border-4 border-on-primary-container overflow-hidden">
          <img v-if="myRank.avatar" :src="myRank.avatar" alt="" class="w-full h-full object-cover">
          <span v-else class="w-full h-full flex items-center justify-center text-on-primary font-bold text-xl">
            {{ myRank.name.charAt(0) }}
          </span>
        </div>
        <div class="flex-1">
          <h4 class="font-black text-primary text-base">你 ({{ myRank.name }})</h4>
          <p class="text-[10px] font-black text-primary/70 uppercase tracking-widest flex items-center gap-1">
            继续加油！ <span class="material-symbols-outlined text-[12px]">trending_up</span>
          </p>
        </div>
        <div class="text-right">
          <p class="font-black text-primary text-lg leading-tight">{{ myRank.steps.toLocaleString() }}</p>
          <p class="text-[10px] text-primary/70 font-black">步</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { rankingApi } from '@/api'

const scope = ref('all')
const periodType = ref('daily')
const ranking = ref([])
const myRank = ref(null)

const periodTypes = [
  { value: 'daily', label: '日榜', icon: 'energy_savings_leaf' },
  { value: 'weekly', label: '周榜', icon: 'calendar_week' },
  { value: 'monthly', label: '月榜', icon: 'calendar_month' },
  { value: 'yearly', label: '年榜', icon: 'event' }
]

const fetchRanking = async () => {
  try {
    const res = await rankingApi.getRanking({
      period_type: periodType.value,
      scope: scope.value,
      limit: 50
    })
    ranking.value = res.items
    myRank.value = res.my_rank
  } catch (e) {
    console.error('获取排行榜失败', e)
  }
}

watch([scope, periodType], () => {
  fetchRanking()
})

onMounted(() => {
  fetchRanking()
})
</script>
