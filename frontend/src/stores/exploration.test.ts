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
import type { ApiResponse, ExplorationRecord, PaginatedResponse } from '@/types'
import { getExplorationCount } from '@/utils/exploration'

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

const makeResponse = <T>(data: T): ApiResponse<T> => ({
  code: 200,
  message: 'ok',
  data,
})

describe('useExplorationStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.resetAllMocks()
  })

  it('addRecord (startExploration) first call: appends eventId to history and stores currentRecord', async () => {
    mockedApi.startExploration.mockResolvedValueOnce(makeResponse(makeRecord('evt-a', 100)))

    const store = useExplorationStore()
    const result = await store.startExploration('evt-a', 'Event A')

    expect(result).toEqual(makeRecord('evt-a', 100))
    expect(store.currentRecord).toEqual(makeRecord('evt-a', 100))
    expect(store.exploreHistory).toEqual(['evt-a'])
    expect(mockedApi.startExploration).toHaveBeenCalledTimes(1)
  })

  it('addRecord (startExploration) is idempotent on the same eventId: history does not duplicate', async () => {
    mockedApi.startExploration.mockResolvedValueOnce(makeResponse(makeRecord('evt-dup', 1)))
    mockedApi.startExploration.mockResolvedValueOnce(makeResponse(makeRecord('evt-dup', 2)))

    const store = useExplorationStore()

    await store.startExploration('evt-dup', 'Dup')
    expect(store.exploreHistory).toEqual(['evt-dup'])

    // Second start for the same active event must reuse the current record.
    await store.startExploration('evt-dup', 'Dup')
    expect(store.exploreHistory).toEqual(['evt-dup'])
    expect(mockedApi.startExploration).toHaveBeenCalledTimes(1)
  })

  it('startExploration reuses an active record for the same event', async () => {
    const activeRecord = makeRecord('evt-active', 9)
    mockedApi.startExploration.mockResolvedValueOnce({
      code: 200,
      message: 'ok',
      data: activeRecord,
    })

    const store = useExplorationStore()

    const first = await store.startExploration('evt-active', 'Active')
    const second = await store.startExploration('evt-active', 'Active')

    expect(first).toEqual(activeRecord)
    expect(second).toEqual(activeRecord)
    expect(store.currentRecord).toEqual(activeRecord)
    expect(store.exploreHistory).toEqual(['evt-active'])
    expect(mockedApi.startExploration).toHaveBeenCalledTimes(1)
  })

  it('startExploration records local exploration count only when a session starts', async () => {
    mockedApi.startExploration.mockResolvedValueOnce({
      code: 200,
      message: 'ok',
      data: makeRecord('evt-counted', 11),
    })

    const store = useExplorationStore()

    expect(getExplorationCount('evt-counted')).toBe(0)
    await store.startExploration('evt-counted', 'Counted')

    expect(getExplorationCount('evt-counted')).toBe(1)
  })

  it('records ref is populated by fetchRecords and rendered as a list', async () => {
    const page: PaginatedResponse<ExplorationRecord> = {
      items: [makeRecord('evt-a', 1), makeRecord('evt-b', 2), makeRecord('evt-c', 3)],
      total: 3,
      page: 1,
      page_size: 20,
    }
    mockedApi.getExplorationRecords.mockResolvedValueOnce(makeResponse(page))

    const store = useExplorationStore()
    expect(store.records).toEqual([])

    const res = await store.fetchRecords(1, 20)

    expect(res).toEqual(page)
    expect(store.records).toHaveLength(3)
    expect(store.records.map(r => r.event_id)).toEqual(['evt-a', 'evt-b', 'evt-c'])
  })

  it('endExploration: clears currentRecord after ending a session', async () => {
    mockedApi.startExploration.mockResolvedValueOnce(makeResponse(makeRecord('evt-e', 50)))
    mockedApi.endExploration.mockResolvedValueOnce(makeResponse(makeRecord('evt-e', 50)))

    const store = useExplorationStore()
    await store.startExploration('evt-e')
    expect(store.currentRecord).not.toBeNull()

    await store.endExploration(50, 30, 2, 'done')
    expect(store.currentRecord).toBeNull()
  })
})
