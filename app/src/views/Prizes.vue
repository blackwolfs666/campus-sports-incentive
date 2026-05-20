<template>
  <div class="min-h-screen pb-32">
    <!-- 顶部导航 -->
    <header class="sticky top-0 z-50 bg-surface-container-low shadow-sm">
      <div class="flex items-center justify-between px-6 h-16">
        <div class="flex items-center gap-3">
          <span class="material-symbols-outlined text-primary">park</span>
          <h1 class="font-headline font-bold text-xl text-primary">学术奖品</h1>
        </div>
        <span class="material-symbols-outlined text-primary opacity-80">notifications</span>
      </div>
    </header>

    <main class="max-w-md mx-auto px-6 pt-6 space-y-8">
      <!-- 标题 -->
      <section class="relative">
        <div class="absolute -top-4 -right-2 opacity-20">
          <span class="material-symbols-outlined text-9xl text-primary">eco</span>
        </div>
        <h2 class="font-headline text-4xl font-extrabold tracking-tight text-primary mb-2">本周奖励</h2>
        <p class="text-on-surface-variant font-medium">勤学进取，硕果累累</p>
      </section>

      <!-- 奖品列表 -->
      <div class="space-y-6">
        <div 
          v-for="(prize, idx) in prizes" 
          :key="prize.id"
          @click="goToWinners(prize.id)"
          class="group bg-surface-container-low rounded-xl p-5 flex items-center gap-5 transition-all duration-300 hover:scale-[1.02] hover:bg-surface-container-high bubbly-shadow cursor-pointer"
          :class="'border-l-8 ' + getBorderClass(prize.prize_type)"
        >
          <div 
            class="w-20 h-20 rounded-lg flex items-center justify-center relative overflow-hidden flex-shrink-0"
            :class="getIconBgClass(prize.prize_type)"
          >
            <span class="material-symbols-outlined text-4xl" :class="getIconColor(prize.prize_type)">
              {{ getIcon(prize.prize_type) }}
            </span>
          </div>
          <div class="flex-grow">
            <span class="font-bold text-sm tracking-widest block mb-1" :class="getLabelColor(prize.prize_type)">
              {{ getLabel(prize.prize_type) }}
            </span>
            <h3 class="text-lg font-bold text-on-surface leading-tight">{{ prize.name }}</h3>
            <p class="text-xs text-on-surface-variant mt-2 font-medium">{{ prize.description }}</p>
          </div>
          <span class="material-symbols-outlined text-outline-variant group-hover:text-primary transition-colors">
            chevron_right
          </span>
        </div>
      </div>

      <!-- 如何赢取 -->
      <div class="bg-tertiary-container rounded-lg p-6 flex items-center justify-between relative overflow-hidden group">
        <div class="z-10">
          <h4 class="font-headline font-bold text-on-tertiary-container">如何赢取？</h4>
          <p class="text-on-tertiary-container text-sm opacity-90 mt-1">保持每日步数排名前10%即可入围</p>
          <button class="mt-4 bg-primary text-on-primary px-6 py-2 rounded-full font-bold text-sm transition-transform active:scale-95">
            查看规则
          </button>
        </div>
        <div class="absolute -right-4 -bottom-4 transform group-hover:scale-110 transition-transform duration-500">
          <span class="material-symbols-outlined text-8xl text-on-tertiary-container opacity-20">emoji_events</span>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { prizesApi } from '@/api'

const router = useRouter()
const prizes = ref([])

const getBorderClass = (type) => {
  const classes = {
    first: 'border-tertiary-container',
    second: 'border-surface-container-highest',
    third: 'border-secondary-fixed',
    honorable: 'border-outline-variant'
  }
  return classes[type] || classes.honorable
}

const getIconBgClass = (type) => {
  const classes = {
    first: 'bg-tertiary-container',
    second: 'bg-primary-container',
    third: 'bg-secondary-container',
    honorable: 'bg-surface-variant'
  }
  return classes[type] || classes.honorable
}

const getIconColor = (type) => {
  const colors = {
    first: 'text-on-tertiary-container',
    second: 'text-primary',
    third: 'text-secondary',
    honorable: 'text-on-surface-variant'
  }
  return colors[type] || colors.honorable
}

const getIcon = (type) => {
  const icons = {
    first: 'workspace_premium',
    second: 'book_2',
    third: 'local_cafe',
    honorable: 'military_tech'
  }
  return icons[type] || 'military_tech'
}

const getLabel = (type) => {
  const labels = {
    first: '第一名',
    second: '第二名',
    third: '第三名',
    honorable: '优胜奖'
  }
  return labels[type] || '优胜奖'
}

const getLabelColor = (type) => {
  const colors = {
    first: 'text-tertiary',
    second: 'text-secondary',
    third: 'text-secondary-dim',
    honorable: 'text-on-surface-variant'
  }
  return colors[type] || colors.honorable
}

const goToWinners = (prizeId) => {
  router.push(`/prizes/${prizeId}/winners`)
}

const fetchPrizes = async () => {
  try {
    const res = await prizesApi.getList()
    prizes.value = res
  } catch (e) {
    console.error('获取奖品列表失败', e)
  }
}

onMounted(() => {
  fetchPrizes()
})
</script>
