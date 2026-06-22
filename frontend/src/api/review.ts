import { get, post, del } from './request'
import { getSessionId } from '@/utils/session'
import type { ApiResponse, PaginatedResponse, ReviewItem } from '@/types'

export const reviewApi = {
  /** 评价列表（顶级评价 + 嵌入回复） */
  listReviews(
    cardId: number,
    params: { min_stars?: number; max_stars?: number; page?: number; page_size?: number } = {}
  ): Promise<ApiResponse<PaginatedResponse<ReviewItem>>> {
    return get('/api/review/list', {
      card_id: cardId,
      session_id: getSessionId(),
      ...params,
    }) as any
  },

  /** 创建卡牌评价（stars + comment，可选 parent_review_id） */
  createReview(data: {
    card_id: number
    stars: number
    comment?: string
    parent_review_id?: number
    reviewer_session_id?: string
  }): Promise<ApiResponse<ReviewItem>> {
    return post('/api/review', {
      ...data,
      reviewer_session_id: data.reviewer_session_id || getSessionId(),
    })
  },

  /** 点赞 toggle */
  likeReview(reviewId: number): Promise<ApiResponse<{ review_id: number; liked: boolean; likes_count: number }>> {
    return post(`/api/review/${reviewId}/like`, null, { params: { user_session_id: getSessionId() } })
  },

  /** 删除自己的评价 */
  deleteReview(reviewId: number): Promise<ApiResponse<null>> {
    return del(`/api/review/${reviewId}?user_session_id=${encodeURIComponent(getSessionId())}`)
  },
}
