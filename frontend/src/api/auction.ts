import { get, post } from './request'
import { normalizePaginatedResponse } from './pagination'
import type {
  ApiResponse,
  CardAuction,
  CardBid,
  CardReview,
  AuctionDetail,
  PaginatedResponse
} from '@/types'

export const auctionApi = {
  list(params: {
    status?: string
    event_id?: string
    seller_session_id?: string
    min_price?: number
    max_price?: number
    page?: number
    page_size?: number
  } = {}): Promise<ApiResponse<PaginatedResponse<CardAuction>>> {
    return get<CardAuction[]>('/api/auction', params).then(normalizePaginatedResponse)
  },

  detail(auctionId: number): Promise<ApiResponse<AuctionDetail>> {
    return get(`/api/auction/${auctionId}`)
  },

  create(payload: {
    card_id: number
    seller_session_id: string
    start_price: number
    min_increment?: number
    duration_hours?: number
    description?: string
  }): Promise<ApiResponse<CardAuction>> {
    return post('/api/auction', payload)
  },

  bid(payload: { auction_id: number; bidder_session_id: string; amount: number }): Promise<ApiResponse<CardBid>> {
    return post('/api/auction/bid', payload)
  },

  cancel(auctionId: number, sellerSessionId: string): Promise<ApiResponse<null>> {
    return post(`/api/auction/${auctionId}/cancel`, undefined, { params: { seller_session_id: sellerSessionId } })
  },

  review(payload: { auction_id: number; reviewer_session_id: string; stars: number; comment?: string }): Promise<ApiResponse<CardReview>> {
    return post('/api/auction/review', payload)
  }
}
