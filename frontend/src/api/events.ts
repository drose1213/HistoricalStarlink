import { get } from './request'
import type { ApiResponse, HistoryEvent } from '@/types'

interface EventsListResponse {
  list: HistoryEvent[]
  total: number
  page: number
  page_size: number
}

export const eventsApi = {
  async getAll(params?: { region?: string; min_importance?: number; tag?: string }) {
    const res = await get<EventsListResponse>('/api/events', params)
    return res
  },

  async getById(id: string) {
    const res = await get<HistoryEvent>(`/api/events/${id}`)
    return res
  },

  async search(q: string) {
    const res = await get<HistoryEvent[]>('/api/events/search', { q })
    return res
  }
}
