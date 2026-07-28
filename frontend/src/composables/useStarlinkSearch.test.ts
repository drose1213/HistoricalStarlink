import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { defineComponent, h, nextTick } from 'vue'
import { mount } from '@vue/test-utils'

// Mock @/api/rag so tests do not depend on a real backend
const { ragApiMock } = vi.hoisted(() => ({
  ragApiMock: {
    hybridSearch: vi.fn(),
    search: vi.fn(),
  },
}))
vi.mock('@/api/rag', () => ({
  ragApi: ragApiMock,
}))

// Provide a tiny in-memory event table so searchEvents works in tests
vi.mock('@/data/events', () => ({
  allEvents: [
    { id: 'e1', name: '春秋战国', year: -500, region: 'china', importance: 9, description: '百家争鸣' },
    { id: 'e2', name: '工业革命', year: 1760, region: 'foreign', importance: 10, description: '蒸汽机' },
    { id: 'e3', name: 'AI 发展史', year: 1950, region: 'foreign', importance: 8, description: '人工智能起源' },
  ],
  searchEvents: (q: string) => {
    const norm = q.trim().toLowerCase().replace(/\s+/g, '')
    return [
      { id: 'e1', name: '春秋战国', year: -500, region: 'china', importance: 9, description: '百家争鸣' },
      { id: 'e2', name: '工业革命', year: 1760, region: 'foreign', importance: 10, description: '蒸汽机' },
      { id: 'e3', name: 'AI 发展史', year: 1950, region: 'foreign', importance: 8, description: '人工智能起源' },
    ].filter(e => e.name.toLowerCase().includes(norm))
  },
}))

import { useStarlinkSearch } from './useStarlinkSearch'

function withSetup<T>(fn: () => T): { result: T; unmount: () => void } {
  let captured!: T
  const Wrapper = defineComponent({
    setup() {
      captured = fn()
      return () => h('div')
    },
  })
  const wrapper = mount(Wrapper)
  return { result: captured, unmount: () => wrapper.unmount() }
}

describe('useStarlinkSearch', () => {
  beforeEach(() => {
    ragApiMock.hybridSearch.mockReset()
    ragApiMock.search.mockReset()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('returns empty results when query is empty', () => {
    const { result, unmount } = withSetup(() => useStarlinkSearch())
    expect(result.results.length).toBe(0)
    expect(result.showDropdown).toBe(false)
    unmount()
  })

  it('returns local matches immediately when query has text', async () => {
    const { result, unmount } = withSetup(() => useStarlinkSearch())
    result.query = '工业'
    await nextTick()
    expect(result.results.length).toBeGreaterThan(0)
    expect(result.results[0].id).toBe('e2')
    unmount()
  })

  it('triggers debounced RAG search on onInput', async () => {
    ragApiMock.hybridSearch.mockResolvedValue({
      code: 200,
      data: [
        { id: 'e2', name: '工业革命', score: 0.9, source: 'rag' },
      ],
    })

    vi.useFakeTimers()
    const { result, unmount } = withSetup(() => useStarlinkSearch({ debounceMs: 100 }))

    result.query = '工业'
    result.onInput()

    expect(ragApiMock.hybridSearch).not.toHaveBeenCalled()

    await vi.advanceTimersByTimeAsync(150)
    await nextTick()

    expect(ragApiMock.hybridSearch).toHaveBeenCalledWith({ query: '工业', top_k: 5 })
    unmount()
  })

  it('falls back to pure RAG search when hybrid search throws', async () => {
    ragApiMock.hybridSearch.mockRejectedValue(new Error('hybrid down'))
    ragApiMock.search.mockResolvedValue({
      code: 200,
      data: [
        { id: 'e3', name: 'AI 发展史', score: 0.7, source: 'rag' },
      ],
    })

    vi.useFakeTimers()
    const { result, unmount } = withSetup(() => useStarlinkSearch({ debounceMs: 50 }))

    result.query = 'AI'
    result.onInput()

    await vi.advanceTimersByTimeAsync(80)
    await nextTick()

    expect(ragApiMock.hybridSearch).toHaveBeenCalled()
    expect(ragApiMock.search).toHaveBeenCalledWith({ query: 'AI', top_k: 5 })
    unmount()
  })

  it('cleans up timers on unmount (no setState on unmounted)', async () => {
    vi.useFakeTimers()
    const { result, unmount } = withSetup(() => useStarlinkSearch({ debounceMs: 100 }))

    result.query = '工业'
    result.onInput()
    unmount()
    // advancing timers after unmount should not throw
    await vi.advanceTimersByTimeAsync(200)
  })

  it('onSelect clears the search state and returns whether the id exists', () => {
    const { result, unmount } = withSetup(() => useStarlinkSearch())
    result.query = 'something'
    result.showDropdown = true
    const ok = result.onSelect('e1')
    expect(ok).toBe(true)
    expect(result.query).toBe('')
    expect(result.showDropdown).toBe(false)
    unmount()
  })

  it('onEnter returns the first result id when results exist', async () => {
    const { result, unmount } = withSetup(() => useStarlinkSearch())
    result.query = '工业'
    await nextTick()
    const id = result.onEnter()
    expect(id).toBe('e2')
    unmount()
  })
})
