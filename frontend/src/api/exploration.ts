import { get, post } from './request'
import { getSessionId } from '@/utils/session'
import type {
  ApiResponse,
  ExplorationRecord,
  PaginatedResponse,
  ExploreStartRequest,
  ExploreEndRequest
} from '@/types'

export const explorationApi = {
  startExploration(data: ExploreStartRequest): Promise<ApiResponse<ExplorationRecord>> {
    return post('/api/exploration/start', {
      event_id: data.event_id,
      session_id: data.session_id || getSessionId(),
      event_name: data.event_name || data.event_id,
    })
  },

  endExploration(data: ExploreEndRequest): Promise<ApiResponse<ExplorationRecord>> {
    return post('/api/exploration/end', data)
  },

  getExplorationRecords(page = 1, pageSize = 20): Promise<ApiResponse<PaginatedResponse<ExplorationRecord>>> {
    return get('/api/exploration/records', { page, page_size: pageSize })
  },

  getExplorationByEvent(eventId: string): Promise<ApiResponse<ExplorationRecord[]>> {
    return get(`/api/exploration/event/${eventId}`)
  },

  getExplorationStats(): Promise<ApiResponse<Record<string, unknown>>> {
    return get('/api/exploration/stats')
  }
}
