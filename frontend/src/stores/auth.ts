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
      return { success: true as const }
    }
    // 失败时统一抛出错误对象, 由调用方 (AuthView) 决定如何提示用户
    const message = res.message || '登录失败'
    throw new Error(message)
  }

  async function sendCode(email: string) {
    return await authApi.sendCode(email)
  }

  async function sendPasswordResetCode(email: string) {
    return await authApi.sendPasswordResetCode(email)
  }

  async function resetPassword(email: string, emailCode: string, newPassword: string) {
    const res = await authApi.resetPassword({
      email,
      email_code: emailCode,
      new_password: newPassword,
    })
    if (res.code === 200) {
      return { success: true as const, message: res.message || '密码已重置' }
    }
    throw new Error(res.message || '密码重置失败')
  }

  async function register(username: string, email: string, email_code: string, password: string, nickname?: string) {
    const res = await authApi.register({ username, email, email_code, password, nickname })
    if (res.code === 200 && res.data?.token) {
      setToken(res.data.token)
      user.value = res.data.user
      return { success: true as const }
    }
    throw new Error(res.message || '注册失败')
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
    sendPasswordResetCode,
    resetPassword,
    logout,
    fetchUser,
    init,
    setToken,
    clearAuth
  }
})
