<template>
  <div class="min-h-screen flex flex-col bg-background">
    <!-- 顶部导航 -->
    <header class="sticky top-0 z-50 bg-surface-container-low shadow-sm">
      <div class="flex justify-between items-center px-6 py-4">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-full bg-primary-container flex items-center justify-center overflow-hidden">
            <span class="material-symbols-outlined text-primary">account_circle</span>
          </div>
          <h1 class="font-headline font-bold text-lg text-primary">奖品兑换</h1>
        </div>
        <button class="text-primary hover:opacity-80 transition-opacity">
          <span class="material-symbols-outlined">settings</span>
        </button>
      </div>
    </header>

    <main class="flex-grow px-6 pt-4 pb-32 max-w-2xl mx-auto w-full space-y-8">
      <!-- 奖品信息 -->
      <section class="relative overflow-visible">
        <div class="bg-surface-container-low rounded-xl p-8 flex flex-col items-center text-center relative overflow-hidden">
          <div class="absolute -top-10 -right-10 w-32 h-32 bg-primary-container/30 rounded-full blur-2xl"></div>
          <div class="absolute -bottom-10 -left-10 w-24 h-24 bg-tertiary-container/20 rounded-full blur-xl"></div>
          
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
              {{ getLabel(winner?.prize_type) }}
            </span>
            <h2 class="font-headline font-extrabold text-2xl text-primary tracking-tight">{{ prize?.name }}</h2>
            <p class="text-on-surface-variant text-sm px-4">恭喜本阶段健步达标的各位优秀教师</p>
          </div>
        </div>
      </section>

      <!-- 二维码区域 -->
      <section class="bg-surface-container-lowest rounded-xl p-8 flex flex-col items-center text-center shadow-lg border border-outline-variant/10">
        <div class="mb-4">
          <p class="font-headline font-bold text-on-surface tracking-wide uppercase text-sm opacity-60">核销二维码</p>
          <p class="text-xs text-secondary mt-1">Verification QR Code</p>
        </div>
        
        <div class="relative p-6 bg-white rounded-lg border-2 border-surface-container-highest">
          <!-- 简化的二维码显示 -->
          <div class="w-48 h-48 bg-white flex items-center justify-center">
            <div class="w-full h-full border-4 border-on-surface rounded p-4 flex flex-col gap-2">
              <div class="flex gap-2">
                <div class="w-12 h-12 border-4 border-on-surface"></div>
                <div class="flex-1 grid grid-cols-4 gap-1">
                  <div v-for="i in 16" :key="i" class="bg-on-surface" :class="Math.random() > 0.5 ? 'opacity-100' : 'opacity-0'"></div>
                </div>
              </div>
              <div class="flex-1 grid grid-cols-8 gap-1">
                <div v-for="i in 32" :key="i" class="bg-on-surface" :class="Math.random() > 0.5 ? 'opacity-100' : 'opacity-0'"></div>
              </div>
              <div class="flex gap-2">
                <div class="flex-1 grid grid-cols-4 gap-1">
                  <div v-for="i in 16" :key="i" class="bg-on-surface" :class="Math.random() > 0.5 ? 'opacity-100' : 'opacity-0'"></div>
                </div>
                <div class="w-12 h-12 border-4 border-on-surface"></div>
              </div>
            </div>
          </div>
          
          <!-- 四角装饰 -->
          <div class="absolute -top-2 -left-2 w-6 h-6 border-t-4 border-l-4 border-primary rounded-tl-md"></div>
          <div class="absolute -top-2 -right-2 w-6 h-6 border-t-4 border-r-4 border-primary rounded-tr-md"></div>
          <div class="absolute -bottom-2 -left-2 w-6 h-6 border-b-4 border-l-4 border-primary rounded-bl-md"></div>
          <div class="absolute -bottom-2 -right-2 w-6 h-6 border-b-4 border-r-4 border-primary rounded-br-md"></div>
        </div>
        
        <div class="mt-8 flex flex-col gap-2 w-full">
          <div class="bg-surface-container-low py-3 px-4 rounded-md flex justify-between items-center group">
            <span class="text-on-surface-variant text-sm">券码：{{ winner?.claim_code || 'XXXX XXXX XXXX' }}</span>
            <button @click="copyCode" class="material-symbols-outlined text-primary text-lg cursor-pointer group-active:scale-90 transition-transform">
              content_copy
            </button>
          </div>
          <p class="text-[11px] text-on-surface-variant italic mt-2">
            有效至：{{ formatDate(winner?.claim_deadline) }}
          </p>
        </div>
      </section>

      <!-- 兑换说明 -->
      <section class="bg-tertiary-container/10 rounded-lg p-8 flex flex-col items-center text-center border border-tertiary-container/20">
        <div class="w-12 h-12 rounded-full bg-tertiary-container flex items-center justify-center flex-shrink-0">
          <span class="material-symbols-outlined text-on-tertiary-container">info</span>
        </div>
        <div class="mt-4 w-full">
          <h3 class="font-bold text-on-tertiary-container">兑换说明</h3>
          <ul class="text-sm text-on-tertiary-container/80 space-y-2 leading-relaxed mt-2 text-left">
            <li>• 请向校工会管理人员出示此二维码进行兑换。</li>
            <li>• 奖品：<span class="font-bold">{{ prize?.name }}</span></li>
            <li>• 此凭证仅限本人在工作日（8:30-17:30）使用。</li>
            <li>• 核销完成后，奖品将从您的库存中移除。</li>
          </ul>
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
const winner = ref(null)
const prize = ref(null)

const getLabel = (type) => {
  const labels = {
    first: '第一名奖励',
    second: '第二名奖励',
    third: '第三名奖励',
    honorable: '优胜奖'
  }
  return labels[type] || '优胜奖'
}

const formatDate = (date) => {
  if (!date) return '未知'
  const d = new Date(date)
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日 ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

const copyCode = () => {
  if (winner.value?.claim_code) {
    navigator.clipboard.writeText(winner.value.claim_code.replace(/ /g, ''))
    alert('兑换码已复制')
  }
}

const fetchData = async () => {
  try {
    const winnerId = route.params.id
    
    // 如果状态是pending，先领取奖品
    const detail = await prizesApi.getWinnerDetail(winnerId)
    
    if (detail.status === 'pending') {
      const claimed = await prizesApi.claimPrize(winnerId)
      winner.value = claimed
    } else {
      winner.value = detail
    }
    
    // 获取奖品详情
    prize.value = await prizesApi.getDetail(winner.value.prize_id)
  } catch (e) {
    console.error('获取数据失败', e)
  }
}

onMounted(() => {
  fetchData()
})
</script>
