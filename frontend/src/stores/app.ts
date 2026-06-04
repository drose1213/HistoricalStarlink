import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export type AppLocale = 'zh' | 'en'

const LOCALE_STORAGE_KEY = 'historical-starlink.locale'

function detectInitialLocale(): AppLocale {
  if (typeof window === 'undefined') return 'zh'
  try {
    const saved = window.localStorage.getItem(LOCALE_STORAGE_KEY)
    if (saved === 'zh' || saved === 'en') return saved
  } catch (_) {
    /* localStorage unavailable */
  }
  const navLang = (window.navigator?.language || '').toLowerCase()
  if (navLang.startsWith('en')) return 'en'
  return 'zh'
}

export const useAppStore = defineStore('app', () => {
  const currentFilter = ref<'all' | 'china' | 'foreign'>('all')
  const currentView = ref<'chart' | 'starlink'>('chart')
  const isLoading = ref(false)
  const locale = ref<AppLocale>(detectInitialLocale())
  const toasts = ref<{ id: number; type: 'success' | 'error' | 'warning'; message: string }[]>([])

  let toastId = 0

  const filterLabel = computed(() => {
    const map = { all: '全部', china: '东方', foreign: '西方' }
    return map[currentFilter.value]
  })

  function setFilter(filter: 'all' | 'china' | 'foreign') {
    currentFilter.value = filter
  }

  function setView(view: 'chart' | 'starlink') {
    currentView.value = view
  }

  function setLoading(value: boolean) {
    isLoading.value = value
  }

  function setLocale(next: AppLocale) {
    locale.value = next
    if (typeof window !== 'undefined') {
      try {
        window.localStorage.setItem(LOCALE_STORAGE_KEY, next)
      } catch (_) {
        /* ignore */
      }
      document.documentElement.setAttribute('lang', next === 'zh' ? 'zh-CN' : 'en')
      document.documentElement.setAttribute('data-locale', next)
    }
  }

  function showToast(type: 'success' | 'error' | 'warning', message: string, duration = 3000) {
    const id = ++toastId
    toasts.value.push({ id, type, message })
    setTimeout(() => {
      toasts.value = toasts.value.filter(t => t.id !== id)
    }, duration)
  }

  function removeToast(id: number) {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }

  return {
    currentFilter,
    currentView,
    isLoading,
    locale,
    toasts,
    filterLabel,
    setFilter,
    setView,
    setLoading,
    setLocale,
    showToast,
    removeToast
  }
})
