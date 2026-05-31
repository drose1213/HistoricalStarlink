import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi, type UserInfo } from '@/api/auth'

const TOKEN_KEY = 'auth_token'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(localStorage.getItem(TOKEN_KEY) || '')
  const user = ref<UserInfo | null>(null)
  const isLoggedIn = computed(() => !!token.value && !!user.value)
  const displayName = computed(() => user.value?.nickname || user.value?.username || '')
  const userInitial = computed(() => {
    const name = displayName.value
    return name ? name.charAt(0).toUpperCase() : '?'
  })

  function setToken(t: string) {
    token.value = t
    localStorage.setItem(TOKEN_KEY, t)
  }

  function clearAuth() {
    token.value = ''
    user.value = null
    localStorage.removeItem(TOKEN_KEY)
  }

  async function fetchUser() {
    if (!token.value) return
    try {
      const res = await authApi.getMe()
      if (res.code === 200 && res.data) {
        user.value = res.data
      } else {
        clearAuth()
      }
    } catch {
      clearAuth()
    }
  }

  async function login(username: string, password: string) {
    const res = await authApi.login({ username, password })
    if (res.code === 200 && res.data?.token) {
      setToken(res.data.token)
      user.value = res.data.user
      return { success: true }
    }
    return { success: false, message: res.message || '登录失败' }
  }

  async function sendCode(email: string) {
    return await authApi.sendCode(email)
  }

  async function register(username: string, email: string, email_code: string, password: string, nickname?: string) {
    const res = await authApi.register({ username, email, email_code, password, nickname })
    if (res.code === 200 && res.data?.token) {
      setToken(res.data.token)
      user.value = res.data.user
      return { success: true }
    }
    return { success: false, message: res.message || '注册失败' }
  }

  function logout() {
    clearAuth()
  }

  async function init() {
    if (token.value) {
      await fetchUser()
    }
  }

  return {
    token,
    user,
    isLoggedIn,
    displayName,
    userInitial,
    login,
    register,
    sendCode,
    logout,
    fetchUser,
    init,
    setToken,
    clearAuth
  }
})
