import { get, post, del } from './request'
import { normalizePaginatedResponse } from './pagination'
import type {
  ApiResponse,
  PaginatedResponse,
  UserCardCollection
} from '@/types'

export const collectionApi = {
  list(params: { user_session_id?: string; is_high_rated?: boolean; page?: number; page_size?: number } = {}): Promise<ApiResponse<PaginatedResponse<UserCardCollection>>> {
    return get<UserCardCollection[]>('/api/collection', params).then(normalizePaginatedResponse)
  },

  add(payload: { user_session_id: string; card_id: number; source?: 'explore' | 'auction' | 'system' }): Promise<ApiResponse<UserCardCollection>> {
    return post('/api/collection', payload)
  },

  remove(collectionId: number): Promise<ApiResponse<null>> {
    return del('/api/collection/' + collectionId)
  }
}
