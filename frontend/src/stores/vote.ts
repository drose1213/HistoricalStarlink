import { defineStore } from 'pinia'
import { ref } from 'vue'
import { voteApi } from '@/api/vote'
import type { VoteStats } from '@/types'

export const useVoteStore = defineStore('vote', () => {
  const voteStats = ref<VoteStats | null>(null)
  const topEvents = ref<{ event_id: string; total_votes: number }[]>([])
  const isLoading = ref(false)

  // spec rating-system-enhancement: 三态计数 + 当前会话投票状态
  const agreeCount = ref(0)
  const disagreeCount = ref(0)
  const favoriteCount = ref(0)
  const myVote = ref<number>(0)  // 1 / -1 / 0

  async function submitVote(eventId: string, voteType: 'up' | 'down' | 'star', eventName?: string) {
    isLoading.value = true
    try {
      const res = (await voteApi.createVote({
        event_id: eventId,
        vote_type: voteType,
        event_name: eventName || eventId,
      })) as any
      const data = res.data
      if (data) {
        if (typeof data.agree_count === 'number') agreeCount.value = data.agree_count
        if (typeof data.disagree_count === 'number') disagreeCount.value = data.disagree_count
        if (typeof data.favorite_count === 'number') favoriteCount.value = data.favorite_count
        if (typeof data.my_vote === 'number') myVote.value = data.my_vote
      }
      // 同步拉一次 stats，确保 ui 数字与全局一致
      await fetchVoteStats(eventId)
    } finally {
      isLoading.value = false
    }
  }

  async function fetchVoteStats(eventId: string) {
    const res = await voteApi.getVoteStats(eventId)
    const data = (res as any).data
    voteStats.value = data
    // 把 up_count/down_count 同步到三态计数（无 favorite 后端时 fallback）
    if (data) {
      agreeCount.value = data.up_count ?? agreeCount.value
      disagreeCount.value = data.down_count ?? disagreeCount.value
    }
    return data
  }

  async function fetchMyVote(eventId: string) {
    const res = (await voteApi.getUserVote(eventId)) as any
    const data = res.data
    if (data && Array.isArray(data) && data.length) {
      myVote.value = (data[0].vote_type === 'up' || data[0].vote_type === 'star' || data[0].vote_type === 1) ? 1 : -1
    } else if (data && !Array.isArray(data)) {
      myVote.value = data.vote_type === 'up' || data.vote_type === 'star' ? 1 : (data.vote_type === 'down' ? -1 : 0)
    } else {
      myVote.value = 0
    }
    return myVote.value
  }

  async function fetchTopEvents(limit = 10) {
    isLoading.value = true
    try {
      const res = await voteApi.getTopVotedEvents(limit)
      topEvents.value = (res as any).data || []
      return topEvents.value
    } finally {
      isLoading.value = false
    }
  }

  function resetLocal() {
    agreeCount.value = 0
    disagreeCount.value = 0
    favoriteCount.value = 0
    myVote.value = 0
  }

  return {
    voteStats,
    topEvents,
    isLoading,
    agreeCount,
    disagreeCount,
    favoriteCount,
    myVote,
    submitVote,
    fetchVoteStats,
    fetchMyVote,
    fetchTopEvents,
    resetLocal,
  }
})
