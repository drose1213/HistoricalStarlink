import { get, post } from './request'
import { normalizePaginatedResponse } from './pagination'
import { getSessionId } from '@/utils/session'
import { useAuthStore } from '@/stores/auth'
import type {
  ApiResponse,
  ExplorationRecord,
  PaginatedResponse,
  ExploreStartRequest,
  ExploreEndRequest
} from '@/types'

export const explorationApi = {
  startExploration(data: ExploreStartRequest): Promise<ApiResponse<ExplorationRecord>> {
    const auth = useAuthStore()
    return post('/api/exploration/start', {
      event_id: data.event_id,
      session_id: data.session_id || getSessionId(),
      event_name: data.event_name || data.event_id,
      user_id: auth.user?.id ?? null,
    })
  },

  endExploration(data: ExploreEndRequest): Promise<ApiResponse<ExplorationRecord>> {
    return post('/api/exploration/end', data)
  },

  /**
   * 直调 end 接口, 用于组件 unmount / tab 关闭场景 (可配合 sendBeacon).
   */
  endByRecordId(
    recordId: number,
    payload: { duration_seconds: number; path_depth?: number; notes?: string }
  ): Promise<ApiResponse<ExplorationRecord>> {
    return post('/api/exploration/end', { record_id: recordId, ...payload })
  },

  getExplorationRecords(page = 1, pageSize = 20): Promise<ApiResponse<PaginatedResponse<ExplorationRecord>>> {
    return get<ExplorationRecord[]>('/api/exploration/records', { page, page_size: pageSize })
      .then(normalizePaginatedResponse)
  },

  getExplorationByEvent(eventId: string): Promise<ApiResponse<ExplorationRecord[]>> {
    return get(`/api/exploration/event/${eventId}`)
  },

  getExplorationStats(): Promise<ApiResponse<Record<string, unknown>>> {
    return get('/api/exploration/stats')
  }
}
