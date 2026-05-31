import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'
import router from '@/router'

export function requireAuth(): boolean {
  const authStore = useAuthStore()
  if (authStore.isLoggedIn) return true

  const appStore = useAppStore()
  appStore.showToast('error', '请先登录后再操作')

  router.push({ name: 'Login' })
  return false
}
