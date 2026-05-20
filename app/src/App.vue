<template>
  <div class="min-h-screen bg-background pb-20">
    <router-view v-slot="{ Component }">
      <keep-alive>
        <component :is="Component" />
      </keep-alive>
    </router-view>
    
    <!-- 底部导航栏 -->
    <nav v-if="showNav" class="fixed bottom-0 left-0 right-0 z-50 bg-surface-container-low/80 backdrop-blur-xl rounded-t-3xl shadow-lg">
      <div class="flex justify-around items-center px-4 pb-6 pt-3">
        <router-link 
          v-for="item in navItems" 
          :key="item.path"
          :to="item.path"
          class="flex flex-col items-center py-2 px-5 rounded-full transition-all duration-300"
          :class="isActive(item.path) 
            ? 'bg-primary-container text-primary scale-110' 
            : 'text-secondary hover:bg-surface-container-high'"
        >
          <span class="material-symbols-outlined" :style="isActive(item.path) ? 'font-variation-settings: FILL 1' : ''">
            {{ item.icon }}
          </span>
          <span class="text-[11px] font-bold mt-1">{{ item.label }}</span>
        </router-link>
      </div>
    </nav>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const navItems = [
  { path: '/', label: '首页', icon: 'home' },
  { path: '/ranking', label: '排行', icon: 'leaderboard' },
  { path: '/prizes', label: '奖品', icon: 'emoji_events' },
  { path: '/profile', label: '我的', icon: 'person' }
]

const showNav = computed(() => {
  const hiddenRoutes = ['Login', 'Redeem', 'PrizeWinners']
  return !hiddenRoutes.includes(route.name)
})

const isActive = (path) => {
  return route.path === path || route.path.startsWith(path + '/')
}
</script>
