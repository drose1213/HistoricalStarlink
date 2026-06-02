import { createRouter, createWebHashHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/HomeView.vue')
  },
  {
    path: '/event/:id',
    name: 'EventDetail',
    component: () => import('@/views/EventDetailView.vue'),
    props: true
  },
  {
    path: '/explore',
    redirect: { name: 'Profile', query: { tab: 'explore' } }
  },
  {
    path: '/champions',
    name: 'Champions',
    component: () => import('@/views/ChampionsView.vue')
  },
  {
    path: '/dialogue/:eventId',
    name: 'Dialogue',
    component: () => import('@/components/DialogueExplorer.vue'),
    props: route => ({
      eventId: route.params.eventId,
      eventName: (route.query.eventName as string) || ''
    })
  },
  {
    path: '/leaderboard',
    name: 'Leaderboard',
    component: () => import('@/views/LeaderboardView.vue')
  },
  {
    path: '/trends',
    redirect: { name: 'Profile', query: { tab: 'trends' } }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/ProfileView.vue')
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/AuthView.vue')
  },
  {
    path: '/knowledge-base',
    name: 'KnowledgeBase',
    component: () => import('@/views/KnowledgeBaseView.vue'),
    meta: { requiresAdmin: true }
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

router.beforeEach((to, _from, next) => {
  if (to.meta?.requiresAdmin) {
    const auth = useAuthStore()
    if (!auth.isLoggedIn) {
      return next({ name: 'Login' })
    }
    if (!auth.user?.is_admin) {
      try {
        const app = useAppStore()
        app.showToast('warning', '无访问权限, 仅管理员可访问知识库')
      } catch (_) {
        // app store 不可用时静默
      }
      return next({ name: 'Home' })
    }
  }
  next()
})

export default router
