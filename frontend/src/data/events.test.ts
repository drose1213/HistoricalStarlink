import { beforeEach, describe, expect, it, vi } from 'vitest'

const { getAllMock } = vi.hoisted(() => ({
  getAllMock: vi.fn(),
}))

vi.mock('@/api/events', () => ({
  eventsApi: {
    getAll: getAllMock,
  },
}))

async function freshEventsModule(): Promise<typeof import('./events')> {
  vi.resetModules()
  return await import('./events')
}

describe('events data loader', () => {
  beforeEach(() => {
    getAllMock.mockReset()
  })

  it('uses local fallback events when the backend event request fails', async () => {
    const networkError = new Error('Network Error') as Error & { code: string }
    networkError.code = 'ERR_NETWORK'
    getAllMock.mockRejectedValueOnce(networkError)

    const eventsModule = await freshEventsModule()

    await eventsModule.loadEvents()

    expect(eventsModule.backendAvailable.value).toBe(false)
    expect(eventsModule.loadError.value).toContain('后端服务未启动')
    expect(eventsModule.allEvents.length).toBeGreaterThan(0)
    expect(eventsModule.getEventById('qin_unification')).toMatchObject({
      id: 'qin_unification',
      related: {
        causes: expect.arrayContaining([{ id: 'shangyang_reform', weight: 9 }]),
      },
    })
  })
})
