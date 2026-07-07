import { get, post, del } from './request'
import { getSessionId } from '@/utils/session'
import { normalizePaginatedResponse } from './pagination'
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
    return get<RatingEntry[]>('/api/rating', { event_id: eventId, page, page_size: pageSize })
      .then(normalizePaginatedResponse)
  },

  getAverageRating(eventId: string): Promise<ApiResponse<{ average?: number; avg_score?: number; count: number }>> {
    return get(`/api/rating/stats/${eventId}`)
  },

  getUserRating(eventId: string): Promise<ApiResponse<RatingEntry | null>> {
    return get<RatingEntry[]>('/api/rating', { event_id: eventId }).then(res => {
      const items = Array.isArray(res.data) ? res.data : []
      return {
        code: res.code,
        message: res.message,
        data: items.length > 0 ? items[0] : null,
      }
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
