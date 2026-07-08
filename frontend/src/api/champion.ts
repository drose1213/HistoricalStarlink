import { get, post, del } from './request'
import { normalizePaginatedResponse } from './pagination'
import type {
  ApiResponse,
  ChampionCard,
  PaginatedResponse
} from '@/types'

export const championApi = {
  getChampionCards(page = 1, pageSize = 20): Promise<ApiResponse<PaginatedResponse<ChampionCard>>> {
    return get<ChampionCard[]>('/api/champion', { page, page_size: pageSize })
      .then(normalizePaginatedResponse)
  },

  getChampionByEvent(eventId: string): Promise<ApiResponse<ChampionCard | null>> {
    return get<ChampionCard[]>('/api/champion', { event_id: eventId }).then(res => {
      const items = Array.isArray(res.data) ? res.data : []
      return {
        code: res.code,
        message: res.message,
        data: items.length > 0 ? items[0] : null,
      }
    })
  },

  unlockChampion(eventId: string): Promise<ApiResponse<ChampionCard>> {
    return post('/api/champion', { event_id: eventId })
  },

  getUserChampions(): Promise<ApiResponse<ChampionCard[]>> {
    return get<ChampionCard[]>('/api/champion').then(res => ({
      code: res.code,
      message: res.message,
      data: Array.isArray(res.data) ? res.data : [],
    }))
  },

  getChampionById(id: number): Promise<ApiResponse<ChampionCard>> {
    return get(`/api/champion/${id}`)
  },

  getChampionsByRarity(rarity: string): Promise<ApiResponse<ChampionCard[]>> {
    return get<ChampionCard[]>('/api/champion', { rarity }).then(res => ({
      code: res.code,
      message: res.message,
      data: Array.isArray(res.data) ? res.data : [],
    }))
  }
}
