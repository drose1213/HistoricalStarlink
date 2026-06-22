import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('@/api/exploration', () => ({
  explorationApi: {
    startExploration: vi.fn(),
    endExploration: vi.fn(),
    getExplorationRecords: vi.fn(),
    getExplorationByEvent: vi.fn(),
    getExplorationStats: vi.fn(),
  },
}))

import { explorationApi } from '@/api/exploration'
import { useExplorationStore } from './exploration'
import type { ExplorationRecord, PaginatedResponse } from '@/types'

const mockedApi = vi.mocked(explorationApi)

const makeRecord = (eventId: string, id: number): ExplorationRecord => ({
  id,
  user_id: 1,
  event_id: eventId,
  explored_at: '2026-01-01T00:00:00Z',
  duration_seconds: 10,
  path_depth: 1,
  notes: '',
})

describe('useExplorationStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('addRecord (startExploration) first call: appends eventId to history and stores currentRecord', async () => {
    mockedApi.startExploration.mockResolvedValueOnce({
      code: 200,
      message: 'ok',
      data: makeRecord('evt-a', 100),
    } as any)

    const store = useExplorationStore()
    const result = await store.startExploration('evt-a', 'Event A')

    expect(result).toEqual(makeRecord('evt-a', 100))
    expect(store.currentRecord).toEqual(makeRecord('evt-a', 100))
    expect(store.exploreHistory).toEqual(['evt-a'])
    expect(mockedApi.startExploration).toHaveBeenCalledTimes(1)
  })

  it('addRecord (startExploration) is idempotent on the same eventId: history does not duplicate', async () => {
    mockedApi.startExploration.mockResolvedValueOnce({
      code: 200,
      message: 'ok',
      data: makeRecord('evt-dup', 1),
    } as any)
    mockedApi.startExploration.mockResolvedValueOnce({
      code: 200,
      message: 'ok',
      data: makeRecord('evt-dup', 2),
    } as any)

    const store = useExplorationStore()

    await store.startExploration('evt-dup', 'Dup')
    expect(store.exploreHistory).toEqual(['evt-dup'])

    // Second add for the same eventId: exploreHistory must not grow
    await store.startExploration('evt-dup', 'Dup')
    expect(store.exploreHistory).toEqual(['evt-dup'])
    // The store does call the API for a fresh record, but the local "count" via exploreHistory
    // is the idempotency surface — it must not duplicate.
    expect(mockedApi.startExploration).toHaveBeenCalledTimes(2)
  })

  it('records ref is populated by fetchRecords and rendered as a list', async () => {
    const page: PaginatedResponse<ExplorationRecord> = {
      items: [makeRecord('evt-a', 1), makeRecord('evt-b', 2), makeRecord('evt-c', 3)],
      total: 3,
      page: 1,
      page_size: 20,
    }
    mockedApi.getExplorationRecords.mockResolvedValueOnce({
      code: 200,
      message: 'ok',
      data: page,
    } as any)

    const store = useExplorationStore()
    expect(store.records).toEqual([])

    const res = await store.fetchRecords(1, 20)

    expect(res).toEqual(page)
    expect(store.records).toHaveLength(3)
    expect(store.records.map(r => r.event_id)).toEqual(['evt-a', 'evt-b', 'evt-c'])
  })

  it('endExploration: clears currentRecord after ending a session', async () => {
    mockedApi.startExploration.mockResolvedValueOnce({
      code: 200,
      message: 'ok',
      data: makeRecord('evt-e', 50),
    } as any)
    mockedApi.endExploration.mockResolvedValueOnce({
      code: 200,
      message: 'ok',
      data: makeRecord('evt-e', 50),
    } as any)

    const store = useExplorationStore()
    await store.startExploration('evt-e')
    expect(store.currentRecord).not.toBeNull()

    await store.endExploration(50, 30, 2, 'done')
    expect(store.currentRecord).toBeNull()
  })
})
