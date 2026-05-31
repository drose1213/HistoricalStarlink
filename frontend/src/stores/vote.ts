import { defineStore } from 'pinia'
import { ref } from 'vue'
import { voteApi } from '@/api/vote'
import type { VoteStats } from '@/types'

export const useVoteStore = defineStore('vote', () => {
  const voteStats = ref<VoteStats | null>(null)
  const topEvents = ref<{ event_id: string; total_votes: number }[]>([])
  const isLoading = ref(false)

  async function submitVote(eventId: string, voteType: 'up' | 'down' | 'star', eventName?: string) {
    isLoading.value = true
    try {
      await voteApi.createVote({ event_id: eventId, vote_type: voteType, event_name: eventName || eventId })
      await fetchVoteStats(eventId)
    } finally {
      isLoading.value = false
    }
  }

  async function fetchVoteStats(eventId: string) {
    const res = await voteApi.getVoteStats(eventId)
    voteStats.value = res.data
    return res.data
  }

  async function fetchTopEvents(limit = 10) {
    isLoading.value = true
    try {
      const res = await voteApi.getTopVotedEvents(limit)
      topEvents.value = res.data
      return res.data
    } finally {
      isLoading.value = false
    }
  }

  return {
    voteStats,
    topEvents,
    isLoading,
    submitVote,
    fetchVoteStats,
    fetchTopEvents
  }
})
