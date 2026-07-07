import { defineStore } from 'pinia'
import { ref } from 'vue'
import { ratingApi } from '@/api/rating'
import type { RatingEntry, RatingDistribution, RatingTrend } from '@/types'

export const useRatingStore = defineStore('rating', () => {
  const ratings = ref<RatingEntry[]>([])
  const userRating = ref<RatingEntry | null>(null)
  const averageData = ref({ average: 0, count: 0 })
  const isLoading = ref(false)
  // spec rating-system-enhancement
  const distribution = ref<RatingDistribution | null>(null)
  const trend = ref<RatingTrend | null>(null)

  async function submitRating(eventId: string, score: number, comment?: string, eventName?: string) {
    isLoading.value = true
    try {
      const res = await ratingApi.createRating({ event_id: eventId, score, comment, event_name: eventName || eventId })
      userRating.value = res.data
      await fetchAverage(eventId)
      return res.data
    } finally {
      isLoading.value = false
    }
  }

  async function fetchRatingsByEvent(eventId: string, page = 1) {
    isLoading.value = true
    try {
      const res = await ratingApi.getRatingsByEvent(eventId, page)
      ratings.value = res.data.items || []
      return res.data
    } finally {
      isLoading.value = false
    }
  }

  async function fetchAverage(eventId: string) {
    const res = await ratingApi.getAverageRating(eventId)
    const d = res.data
    averageData.value = {
      average: d.average ?? d.avg_score ?? 0,
      count: d.count || 0
    }
    return averageData.value
  }

  async function fetchUserRating(eventId: string) {
    const res = await ratingApi.getUserRating(eventId)
    userRating.value = res.data
    return res.data
  }

  // spec rating-system-enhancement: 分布 + 趋势
  async function fetchDistribution(eventId: string) {
    const res = await ratingApi.getDistribution(eventId)
    distribution.value = res.data
    return res.data
  }

  async function fetchTrend(eventId: string, days = 7) {
    const res = await ratingApi.getTrend(eventId, days)
    trend.value = res.data
    return res.data
  }

  return {
    ratings,
    userRating,
    averageData,
    isLoading,
    distribution,
    trend,
    submitRating,
    fetchRatingsByEvent,
    fetchAverage,
    fetchUserRating,
    fetchDistribution,
    fetchTrend,
  }
})
