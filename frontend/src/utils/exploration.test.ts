import { describe, it, expect, beforeEach, vi } from 'vitest'
import {
  recordExploration,
  getExplorationCount,
  getAllExplorationCounts,
} from './exploration'

describe('exploration utilities', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('counts a single recordExploration as 1', () => {
    recordExploration('evt1')
    expect(getExplorationCount('evt1')).toBe(1)
  })

  it('increments count across multiple recordExploration calls', () => {
    recordExploration('evt1')
    recordExploration('evt1')
    expect(getExplorationCount('evt1')).toBe(2)
  })

  it('returns 0 for unknown event ids', () => {
    expect(getExplorationCount('unknown')).toBe(0)
  })

  it('getAllExplorationCounts returns every recorded entry', () => {
    recordExploration('evt1')
    recordExploration('evt2')
    recordExploration('evt2')
    const all = getAllExplorationCounts()
    expect(all).toEqual({ evt1: 1, evt2: 2 })
  })

  it('returns {} when localStorage.getItem throws', () => {
    const spy = vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('storage broken')
    })
    try {
      expect(getAllExplorationCounts()).toEqual({})
      expect(getExplorationCount('evt1')).toBe(0)
    } finally {
      spy.mockRestore()
    }
  })

  it('isolates counts across test cases (beforeEach clear)', () => {
    expect(getExplorationCount('evt1')).toBe(0)
    expect(getAllExplorationCounts()).toEqual({})
  })
})
