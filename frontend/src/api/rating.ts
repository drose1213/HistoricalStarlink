import { get, post, del } from './request'
import { getSessionId } from '@/utils/session'
import type {
  ApiResponse,
  RatingEntry,
  PaginatedResponse,
  RatingCreateRequest,
  RatingDistribution,
  RatingTrend,
} from '@/types'

export const ratingApi = {
  createRating(data: RatingCreateRequest): Promise<ApiResponse<RatingEntry>> {
    return post('/api/rating', {
      event_id: data.event_id,
      event_name: data.event_name || data.event_id,
      session_id: data.session_id || getSessionId(),
      score: data.score,
      comment: data.comment,
    })
  },

  getRatingsByEvent(eventId: string, page = 1, pageSize = 20): Promise<ApiResponse<PaginatedResponse<RatingEntry>>> {
    return get('/api/rating', { event_id: eventId, page, page_size: pageSize })
  },

  getAverageRating(eventId: string): Promise<ApiResponse<{ average: number; count: number }>> {
    return get(`/api/rating/stats/${eventId}`)
  },

  getUserRating(eventId: string): Promise<ApiResponse<RatingEntry | null>> {
    return get('/api/rating', { event_id: eventId }).then(res => {
      const items = (res as any).data?.items || (res as any).data || []
      return { ...res, data: items.length > 0 ? items[0] : null } as any
    })
  },

  /** 0-5 评分分布（spec rating-system-enhancement） */
  getDistribution(eventId: string): Promise<ApiResponse<RatingDistribution>> {
    return get('/api/rating/distribution', { event_id: eventId })
  },

  /** 评分趋势（spec rating-system-enhancement） */
  getTrend(eventId: string, days = 7): Promise<ApiResponse<RatingTrend>> {
    return get('/api/rating/trend', { event_id: eventId, days })
  },

  deleteRating(ratingId: number): Promise<ApiResponse<null>> {
    return del(`/api/rating/${ratingId}`)
  }
}
