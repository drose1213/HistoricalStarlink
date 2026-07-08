import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { collectionApi } from '@/api/collection'
import type { UserCardCollection } from '@/types'
import { getSessionId } from '@/utils/session'

export const useCollectionStore = defineStore('collection', () => {
  const items = ref<UserCardCollection[]>([])
  const total = ref(0)
  const isLoading = ref(false)

  const highRatedItems = computed(() => items.value.filter(i => i.is_high_rated))

  async function load(userSessionId?: string, isHighRated?: boolean, page = 1, pageSize = 20) {
    isLoading.value = true
    try {
      const sid = userSessionId || getSessionId()
      const res = await collectionApi.list({
        user_session_id: sid,
        is_high_rated: isHighRated,
        page,
        page_size: pageSize
      })
      items.value = res.data.items || []
      total.value = res.data.total || 0
      return items.value
    } finally {
      isLoading.value = false
    }
  }

  async function add(payload: { card_id: number; source?: 'explore' | 'auction' | 'system' }) {
    const sid = getSessionId()
    const res = await collectionApi.add({ user_session_id: sid, card_id: payload.card_id, source: payload.source || 'explore' })
    // 增量插入（避免重复）
    if (!items.value.find(i => i.card_id === res.data.card_id)) {
      items.value.unshift(res.data)
      total.value += 1
    }
    return res.data
  }

  async function remove(collectionId: number) {
    await collectionApi.remove(collectionId)
    items.value = items.value.filter(i => i.id !== collectionId)
    total.value = Math.max(0, total.value - 1)
  }

  return {
    items,
    total,
    isLoading,
    highRatedItems,
    load,
    add,
    remove
  }
})
