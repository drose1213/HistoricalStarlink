import { defineStore } from 'pinia'
import { ref } from 'vue'
import { voteApi } from '@/api/vote'
import type { VoteEntry, VoteStats } from '@/types'

type VoteChoice = 'up' | 'down' | 'star'

export const useVoteStore = defineStore('vote', () => {
  const voteStats = ref<VoteStats | null>(null)
  const topEvents = ref<{ event_id: string; total_votes: number }[]>([])
  const isLoading = ref(false)

  const agreeCount = ref(0)
  const disagreeCount = ref(0)
  const favoriteCount = ref(0)
  const myVote = ref<number>(0)

  function toNumericVote(vote: VoteEntry['vote_type'] | number | null | undefined): number {
    if (vote === 'up' || vote === 1) return 1
    if (vote === 'down' || vote === -1) return -1
    if (vote === 'star' || vote === 2) return 2
    return 0
  }

  function applyStats(data: VoteStats | null | undefined) {
    voteStats.value = data ?? null
    if (!data) return

    agreeCount.value = data.up_count ?? agreeCount.value
    disagreeCount.value = data.down_count ?? disagreeCount.value
    favoriteCount.value = data.favorite_count ?? data.star_count ?? favoriteCount.value
    myVote.value = typeof data.my_vote === 'number' ? data.my_vote : myVote.value
  }

  async function submitVote(eventId: string, voteType: VoteChoice, eventName?: string) {
    isLoading.value = true
    try {
      const res = await voteApi.createVote({
        event_id: eventId,
        vote_type: voteType,
        event_name: eventName || eventId,
      })

      const data = res.data
      if (data) {
        agreeCount.value = data.agree_count ?? agreeCount.value
        disagreeCount.value = data.disagree_count ?? disagreeCount.value
        favoriteCount.value = data.favorite_count ?? favoriteCount.value
        myVote.value = typeof data.my_vote === 'number' ? data.my_vote : toNumericVote(data.vote_type)
      }

      await fetchVoteStats(eventId)
    } finally {
      isLoading.value = false
    }
  }

  async function fetchVoteStats(eventId: string) {
    const res = await voteApi.getVoteStats(eventId)
    applyStats(res.data)
    return res.data
  }

  async function fetchMyVote(eventId: string) {
    const res = await voteApi.getUserVote(eventId)
    myVote.value = toNumericVote(res.data?.vote_type)
    return myVote.value
  }

  async function fetchTopEvents() {
    topEvents.value = []
    return topEvents.value
  }

  function resetLocal() {
    voteStats.value = null
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
