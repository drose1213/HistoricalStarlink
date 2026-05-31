import { createRouter, createWebHashHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

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
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router
