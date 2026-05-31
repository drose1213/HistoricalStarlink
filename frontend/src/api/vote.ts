import { get, post, del } from './request'
import { getSessionId } from '@/utils/session'
import type {
  ApiResponse,
  VoteEntry,
  VoteStats,
  VoteCreateRequest
} from '@/types'

const VOTE_TYPE_MAP: Record<string, number> = { up: 1, down: -1, star: 1 }

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
    return get(`/api/vote/stats/${eventId}`)
  },

  getUserVote(eventId: string): Promise<ApiResponse<VoteEntry | null>> {
    return get('/api/vote/my') as any
  },

  deleteVote(voteId: number): Promise<ApiResponse<null>> {
    return del(`/api/vote/${voteId}`)
  },

  getTopVotedEvents(limit = 10): Promise<ApiResponse<{ event_id: string; total_votes: number }[]>> {
    return get('/api/vote/batch-stats', { limit })
  }
}
