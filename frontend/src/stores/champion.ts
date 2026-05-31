import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { championApi } from '@/api/champion'
import type { ChampionCard } from '@/types'

export const useChampionStore = defineStore('champion', () => {
  const champions = ref<ChampionCard[]>([])
  const userChampions = ref<ChampionCard[]>([])
  const currentChampion = ref<ChampionCard | null>(null)
  const isLoading = ref(false)

  const rarityOrder = { legendary: 4, epic: 3, rare: 2, common: 1 }

  const sortedChampions = computed(() => {
    return [...userChampions.value].sort(
      (a, b) => (rarityOrder[b.rarity] || 0) - (rarityOrder[a.rarity] || 0)
    )
  })

  const rarityStats = computed(() => {
    const stats = { common: 0, rare: 0, epic: 0, legendary: 0 }
    userChampions.value.forEach(c => {
      stats[c.rarity]++
    })
    return stats
  })

  async function fetchChampions(page = 1) {
    isLoading.value = true
    try {
      const res = await championApi.getChampionCards(page)
      champions.value = res.data.items
      return res.data
    } finally {
      isLoading.value = false
    }
  }

  async function fetchUserChampions() {
    isLoading.value = true
    try {
      const res = await championApi.getUserChampions()
      userChampions.value = res.data
      return res.data
    } finally {
      isLoading.value = false
    }
  }

  async function fetchByEvent(eventId: string) {
    const res = await championApi.getChampionByEvent(eventId)
    currentChampion.value = res.data
    return res.data
  }

  async function unlockChampion(eventId: string) {
    isLoading.value = true
    try {
      const res = await championApi.unlockChampion(eventId)
      currentChampion.value = res.data
      userChampions.value.push(res.data)
      return res.data
    } finally {
      isLoading.value = false
    }
  }

  return {
    champions,
    userChampions,
    currentChampion,
    isLoading,
    sortedChampions,
    rarityStats,
    fetchChampions,
    fetchUserChampions,
    fetchByEvent,
    unlockChampion
  }
})
