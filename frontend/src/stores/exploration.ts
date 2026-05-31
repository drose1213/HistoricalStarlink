import { defineStore } from 'pinia'
import { ref } from 'vue'
import { explorationApi } from '@/api/exploration'
import type { ExplorationRecord } from '@/types'

export const useExplorationStore = defineStore('exploration', () => {
  const records = ref<ExplorationRecord[]>([])
  const currentRecord = ref<ExplorationRecord | null>(null)
  const exploreHistory = ref<string[]>([])
  const stats = ref<Record<string, unknown>>({})
  const isLoading = ref(false)

  async function startExploration(eventId: string, eventName?: string) {
    isLoading.value = true
    try {
      const res = await explorationApi.startExploration({ event_id: eventId, event_name: eventName || eventId })
      currentRecord.value = res.data
      if (!exploreHistory.value.includes(eventId)) {
        exploreHistory.value.push(eventId)
      }
      return res.data
    } finally {
      isLoading.value = false
    }
  }

  async function endExploration(recordId: number, duration: number, depth: number, notes?: string) {
    isLoading.value = true
    try {
      const res = await explorationApi.endExploration({
        record_id: recordId,
        duration_seconds: duration,
        path_depth: depth,
        notes
      })
      currentRecord.value = null
      return res.data
    } finally {
      isLoading.value = false
    }
  }

  async function fetchRecords(page = 1, pageSize = 20) {
    isLoading.value = true
    try {
      const res = await explorationApi.getExplorationRecords(page, pageSize)
      records.value = res.data.items
      return res.data
    } finally {
      isLoading.value = false
    }
  }

  async function fetchStats() {
    const res = await explorationApi.getExplorationStats()
    stats.value = res.data
    return res.data
  }

  function clearHistory() {
    exploreHistory.value = []
    currentRecord.value = null
  }

  return {
    records,
    currentRecord,
    exploreHistory,
    stats,
    isLoading,
    startExploration,
    endExploration,
    fetchRecords,
    fetchStats,
    clearHistory
  }
})
