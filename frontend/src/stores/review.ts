import { defineStore } from 'pinia'
import { ref } from 'vue'
import { reviewApi } from '@/api/review'
import { useAppStore } from '@/stores/app'
import type { ReviewItem } from '@/types'

export const useReviewStore = defineStore('review', () => {
  const appStore = useAppStore()
  const reviews = ref<ReviewItem[]>([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const isLoading = ref(false)
  const minStars = ref<number | null>(null)
  const maxStars = ref<number | null>(null)
  const submitting = ref(false)

  async function load(cardId: number) {
    isLoading.value = true
    try {
      const params: Record<string, unknown> = {
        page: page.value,
        page_size: pageSize.value,
      }
      if (minStars.value != null) params.min_stars = minStars.value
      if (maxStars.value != null) params.max_stars = maxStars.value
      const res = await reviewApi.listReviews(cardId, params)
      reviews.value = res.data.items
      total.value = res.data.total
      page.value = res.data.page
      pageSize.value = res.data.page_size
    } finally {
      isLoading.value = false
    }
  }

  async function create(payload: {
    card_id: number
    stars: number
    comment?: string
    parent_review_id?: number
  }) {
    submitting.value = true
    try {
      const res = await reviewApi.createReview(payload)
      appStore.showToast('success', '评价已提交')
      return res.data
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '评价失败'
      appStore.showToast('error', msg)
      throw e
    } finally {
      submitting.value = false
    }
  }

  async function toggleLike(reviewId: number) {
    // 乐观更新
    const target = findReview(reviews.value, reviewId)
    if (target) {
      target.liked_by_me = !target.liked_by_me
      target.likes_count += target.liked_by_me ? 1 : -1
    }
    try {
      const res = await reviewApi.likeReview(reviewId)
      const data = res.data
      if (target && data) {
        target.liked_by_me = !!data.liked
        target.likes_count = data.likes_count ?? target.likes_count
      }
      return data
    } catch (e: unknown) {
      // 回滚
      if (target) {
        target.liked_by_me = !target.liked_by_me
        target.likes_count += target.liked_by_me ? 1 : -1
      }
      const msg = e instanceof Error ? e.message : '操作失败'
      appStore.showToast('error', msg)
      throw e
    }
  }

  function findReview(list: ReviewItem[], id: number): ReviewItem | null {
    for (const r of list) {
      if (r.id === id) return r
      if (r.replies && r.replies.length) {
        const found = findReview(r.replies, id)
        if (found) return found
      }
    }
    return null
  }

  function setStarsFilter(min: number | null, max: number | null) {
    minStars.value = min
    maxStars.value = max
    page.value = 1
  }

  function reset() {
    reviews.value = []
    total.value = 0
    page.value = 1
    minStars.value = null
    maxStars.value = null
  }

  return {
    reviews,
    total,
    page,
    pageSize,
    isLoading,
    minStars,
    maxStars,
    submitting,
    load,
    create,
    toggleLike,
    setStarsFilter,
    reset,
  }
})
