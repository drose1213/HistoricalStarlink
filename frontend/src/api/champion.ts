import { get, post, del } from './request'
import type {
  ApiResponse,
  ChampionCard,
  PaginatedResponse
} from '@/types'

export const championApi = {
  getChampionCards(page = 1, pageSize = 20): Promise<ApiResponse<PaginatedResponse<ChampionCard>>> {
    return get('/api/champion', { page, page_size: pageSize })
  },

  getChampionByEvent(eventId: string): Promise<ApiResponse<ChampionCard | null>> {
    return get('/api/champion', { event_id: eventId }).then(res => {
      const items = (res as any).data?.items || (res as any).data || []
      return { ...res, data: items.length > 0 ? items[0] : null } as any
    })
  },

  unlockChampion(eventId: string): Promise<ApiResponse<ChampionCard>> {
    return post('/api/champion', { event_id: eventId })
  },

  getUserChampions(): Promise<ApiResponse<ChampionCard[]>> {
    return get('/api/champion') as any
  },

  getChampionById(id: number): Promise<ApiResponse<ChampionCard>> {
    return get(`/api/champion/${id}`)
  },

  getChampionsByRarity(rarity: string): Promise<ApiResponse<ChampionCard[]>> {
    return get('/api/champion', { rarity }) as any
  }
}
