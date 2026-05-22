<template>
  <div class="min-h-screen pb-32">
    <!-- 顶部导航 -->
    <header class="sticky top-0 z-40 bg-surface-container-low shadow-sm">
      <div class="flex items-center justify-between px-6 h-16">
        <div class="flex items-center gap-3">
          <router-link to="/prizes" class="text-primary">
            <span class="material-symbols-outlined">arrow_back</span>
          </router-link>
          <h1 class="font-headline font-bold text-xl text-primary">学术奖品</h1>
        </div>
        <span class="material-symbols-outlined text-primary">share</span>
      </div>
    </header>

    <main class="max-w-md mx-auto px-6 pt-4 space-y-8">
      <!-- 奖品信息 -->
      <section class="relative overflow-visible">
        <div class="bg-surface-container-low rounded-xl p-8 flex flex-col items-center text-center relative overflow-hidden">
          <div class="absolute -top-10 -right-10 w-32 h-32 bg-primary-container/30 rounded-full blur-2xl"></div>
          <div class="absolute -bottom-10 -left-10 w-24 h-24 bg-tertiary-container/20 rounded-full blur-xl"></div>
          
          <!-- 奖品图片 -->
          <div class="relative z-10 mb-6">
            <div class="absolute inset-0 bg-primary/5 rounded-full scale-110 blur-md"></div>
            <div class="w-48 h-48 rounded-full bg-tertiary-container flex items-center justify-center bubbly-shadow border-4 border-surface-container-lowest">
              <span class="material-symbols-outlined text-on-tertiary-container text-7xl">emoji_events</span>
            </div>
            <div class="absolute -bottom-2 -right-2 bg-tertiary-container text-on-tertiary-container p-3 rounded-full shadow-lg">
              <span class="material-symbols-outlined">military_tech</span>
            </div>
          </div>
          
          <div class="space-y-2 relative z-10">
            <span class="inline-block px-4 py-1 bg-secondary-container text-on-secondary-container rounded-full text-xs font-bold tracking-wider">
              {{ getLabel(prize?.prize_type) }}
            </span>
            <h2 class="font-headline font-extrabold text-2xl text-primary tracking-tight">{{ prize?.name }}</h2>
            <p class="text-on-surface-variant text-sm px-4">{{ prize?.description }}</p>
          </div>
        </div>
      </section>

      <!-- 获奖名单 -->
      <section class="space-y-4">
        <div class="flex items-center justify-between">
          <h3 class="font-headline font-bold text-lg text-secondary px-2">获奖老师名单</h3>
          <span class="text-xs font-medium text-on-surface-variant bg-surface-container-high px-3 py-1 rounded-full">
            共 {{ winners.length }} 位
          </span>
        </div>
        
        <div class="space-y-3">
          <div 
            v-for="winner in winners" 
            :key="winner.id"
            class="bg-surface-container-lowest rounded-lg p-4 flex items-center justify-between bubbly-shadow"
          >
            <div class="flex items-center gap-4">
              <div class="w-12 h-12 rounded-full overflow-hidden border-2 border-primary-container bg-primary-container flex items-center justify-center">
                <img v-if="winner.user_avatar" :src="winner.user_avatar" alt="" class="w-full h-full object-cover">
                <span v-else class="text-primary font-bold text-lg">{{ winner.user_name?.charAt(0) }}</span>
              </div>
              <div>
                <div class="font-bold text-on-surface">{{ winner.user_name }}</div>
                <div class="text-xs text-on-surface-variant">{{ winner.department_name }}</div>
              </div>
            </div>
            <div class="text-right">
              <div class="text-primary font-headline font-bold">{{ winner.steps.toLocaleString() }}</div>
              <div class="text-[10px] text-on-surface-variant uppercase tracking-tighter">累计步数</div>
            </div>
          </div>
        </div>
      </section>

      <!-- 领取说明 -->
      <section class="bg-tertiary-container/10 border-2 border-dashed border-tertiary-container rounded-lg p-6">
        <div class="flex items-start gap-3">
          <span class="material-symbols-outlined text-tertiary mt-1">info</span>
          <div class="space-y-2">
            <h4 class="font-bold text-tertiary">如何领取</h4>
            <p class="text-sm text-on-surface-variant leading-relaxed">
              请获奖老师持本人校园卡，于本周五 17:00 前往 
              <span class="font-bold text-secondary">活动方指定地点</span> 领取。逾期将自动转入下一期奖池。
            </p>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { prizesApi } from '@/api'

const route = useRoute()
const prize = ref(null)
const winners = ref([])

const getLabel = (type) => {
  const labels = {
    first: '第一名奖励',
    second: '第二名奖励',
    third: '第三名奖励',
    honorable: '优胜奖'
  }
  return labels[type] || '优胜奖'
}

const fetchData = async () => {
  try {
    const prizeId = route.params.id
    const [prizeRes, winnersRes] = await Promise.all([
      prizesApi.getDetail(prizeId),
      prizesApi.getWinners(prizeId)
    ])
    prize.value = prizeRes
    winners.value = winnersRes
  } catch (e) {
    console.error('获取数据失败', e)
  }
}

onMounted(() => {
  fetchData()
})
</script>
