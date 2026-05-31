import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAppStore = defineStore('app', () => {
  const currentFilter = ref<'all' | 'china' | 'foreign'>('all')
  const currentView = ref<'chart' | 'starlink'>('chart')
  const isLoading = ref(false)
  const toasts = ref<{ id: number; type: 'success' | 'error'; message: string }[]>([])

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

  function showToast(type: 'success' | 'error', message: string, duration = 3000) {
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
    toasts,
    filterLabel,
    setFilter,
    setView,
    setLoading,
    showToast,
    removeToast
  }
})
