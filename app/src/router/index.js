import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { title: '首页' }
  },
  {
    path: '/ranking',
    name: 'Ranking',
    component: () => import('@/views/Ranking.vue'),
    meta: { title: '排行榜' }
  },
  {
    path: '/prizes',
    name: 'Prizes',
    component: () => import('@/views/Prizes.vue'),
    meta: { title: '奖品' }
  },
  {
    path: '/prizes/:id/winners',
    name: 'PrizeWinners',
    component: () => import('@/views/PrizeWinners.vue'),
    meta: { title: '获奖名单' }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/Profile.vue'),
    meta: { title: '我的' }
  },
  {
    path: '/redeem/:id',
    name: 'Redeem',
    component: () => import('@/views/Redeem.vue'),
    meta: { title: '兑换奖品' }
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  
  if (to.name !== 'Login' && !token) {
    next({ name: 'Login' })
  } else {
    next()
  }
})

export default router
