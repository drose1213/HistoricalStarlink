import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import {
  ANALYTICS_EVENTS,
  trackEvent,
  trackEventIfEnabled,
  type AnalyticsPayload,
} from './analytics'

/** Helper: stub fetch + return parsed body from the call */
function stubFetchOk() {
  const calls: { url: string; init: RequestInit }[] = []
  const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
    calls.push({ url: String(url), init: init || {} })
    return { ok: true, status: 200, json: async () => ({}) } as Response
  })
  vi.stubGlobal('fetch', fetchMock)
  return { fetchMock, calls }
}

function stubFetchReject(reason = new Error('boom')) {
  const fetchMock = vi.fn(async () => {
    throw reason
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

function setLocationSearch(search: string) {
  Object.defineProperty(window, 'location', {
    value: { ...window.location, search },
    writable: true,
    configurable: true,
  })
}

describe('analytics utilities', () => {
  beforeEach(() => {
    // Reset window.location.search between tests
    setLocationSearch('')
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    setLocationSearch('')
  })

  describe('ANALYTICS_EVENTS constants', () => {
    it('exposes stable event names', () => {
      expect(ANALYTICS_EVENTS.APP_ENTER).toBe('app_enter')
      expect(ANALYTICS_EVENTS.DIALOGUE_COMPLETED).toBe('dialogue_completed')
      expect(ANALYTICS_EVENTS.PAYWALL_CLICKED).toBe('paywall_clicked')
      expect(ANALYTICS_EVENTS.FEEDBACK_SUBMITTED).toBe('feedback_submitted')
      expect(ANALYTICS_EVENTS.DIALOGUE_SHARE_CLICKED).toBe('dialogue_share_clicked')
    })
  })

  describe('trackEvent', () => {
    it('POSTs to /api/analytics/event with the event_name', async () => {
      const { fetchMock, calls } = stubFetchOk()
      await trackEvent('app_enter')
      expect(fetchMock).toHaveBeenCalledTimes(1)
      const call = calls[0]
      expect(call.url).toBe('/api/analytics/event')
      expect(call.init.method).toBe('POST')
      const body = JSON.parse(String(call.init.body))
      expect(body.event_name).toBe('app_enter')
    })

    it('lifts `topic` to top level and keeps remaining keys under payload', async () => {
      const { calls } = stubFetchOk()
      const payload: AnalyticsPayload = {
        topic: '贞观之治',
        duration: 12.5,
        step: 3,
      }
      await trackEvent('dialogue_completed', payload)
      const body = JSON.parse(String(calls[0].init.body))
      expect(body.topic).toBe('贞观之治')
      expect(body.payload).toEqual({ duration: 12.5, step: 3 })
      // topic must NOT appear inside payload
      expect(body.payload).not.toHaveProperty('topic')
    })

    it('attaches navigator.userAgent as user_agent', async () => {
      // happy-dom provides a default navigator.userAgent
      const { calls } = stubFetchOk()
      await trackEvent('feedback_submitted')
      const body = JSON.parse(String(calls[0].init.body))
      expect(body.user_agent).toBe(navigator.userAgent)
    })

    it('only warns on fetch failure (does not throw)', async () => {
      stubFetchReject(new Error('network down'))
      const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
      // Should resolve (catch is internal), not throw
      await expect(trackEvent('app_enter')).resolves.toBeUndefined()
      expect(warnSpy).toHaveBeenCalled()
      warnSpy.mockRestore()
    })
  })

  describe('trackEventIfEnabled', () => {
    it('sends the request when analytics is enabled (default)', async () => {
      const { fetchMock } = stubFetchOk()
      await trackEventIfEnabled('app_enter')
      expect(fetchMock).toHaveBeenCalledTimes(1)
    })

    it('skips the request when ?analytics=off', async () => {
      setLocationSearch('?analytics=off')
      const { fetchMock } = stubFetchOk()
      await trackEventIfEnabled('app_enter')
      expect(fetchMock).not.toHaveBeenCalled()
    })

    it('skips the request when ?analytics=OFF (case insensitive)', async () => {
      setLocationSearch('?analytics=OFF')
      const { fetchMock } = stubFetchOk()
      await trackEventIfEnabled('app_enter')
      expect(fetchMock).not.toHaveBeenCalled()
    })
  })
})
