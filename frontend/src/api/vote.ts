import { get, post, del } from './request'
import { getSessionId } from '@/utils/session'
import type {
  ApiResponse,
  VoteEntry,
  VoteStats,
  VoteCreateRequest
} from '@/types'

const VOTE_TYPE_MAP: Record<VoteCreateRequest['vote_type'], 1 | -1 | 2> = {
  up: 1,
  down: -1,
  star: 2,
}

export const voteApi = {
  createVote(data: VoteCreateRequest): Promise<ApiResponse<VoteEntry>> {
    return post('/api/vote', {
      event_id: data.event_id,
      event_name: data.event_name || data.event_id,
      session_id: data.session_id || getSessionId(),
      vote_type: VOTE_TYPE_MAP[data.vote_type] ?? 1,
    })
  },

  getVoteStats(eventId: string): Promise<ApiResponse<VoteStats>> {
    return get(`/api/vote/stats/${eventId}`, { session_id: getSessionId() })
  },

  async getUserVote(eventId: string): Promise<ApiResponse<VoteEntry | null>> {
    const res = await get<VoteEntry[]>('/api/vote/my', {
      session_id: getSessionId(),
      event_id: eventId,
    })

    return {
      ...res,
      data: res.data[0] ?? null,
    }
  },

  deleteVote(voteId: number): Promise<ApiResponse<null>> {
    return del(`/api/vote/${voteId}`)
  },

  async getBatchVoteStats(eventIds: string[]): Promise<ApiResponse<Record<string, VoteStats>>> {
    if (eventIds.length === 0) {
      return { code: 200, message: 'success', data: {} }
    }
    return get('/api/vote/batch-stats', { event_ids: eventIds.join(',') })
  }
}
