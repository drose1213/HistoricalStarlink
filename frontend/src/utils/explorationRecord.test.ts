import { describe, expect, it } from 'vitest'
import {
  getExplorationDepth,
  getExplorationDuration,
  getExplorationNotes,
  getExplorationTimestamp,
  getExplorationTitle,
} from './explorationRecord'

describe('exploration record display helpers', () => {
  it('prefers backend exploration fields and falls back to legacy fields', () => {
    const backendRecord = {
      event_id: 'qin_unification',
      event_name: 'Qin unification',
      depth: 3,
      stay_duration: 42,
      created_at: '2026-07-05T01:02:03Z',
      notes: 'Centralized rule -> unified law',
    }

    expect(getExplorationTitle(backendRecord)).toBe('Qin unification')
    expect(getExplorationDepth(backendRecord)).toBe(3)
    expect(getExplorationDuration(backendRecord)).toBe(42)
    expect(getExplorationTimestamp(backendRecord)).toBe('2026-07-05T01:02:03Z')
    expect(getExplorationNotes(backendRecord)).toBe('Centralized rule -> unified law')

    const legacyRecord = {
      event_id: 'han_empire',
      path_depth: 2,
      duration_seconds: 30,
      explored_at: '2026-01-01T00:00:00Z',
      notes: '',
    }

    expect(getExplorationTitle(legacyRecord)).toBe('han_empire')
    expect(getExplorationDepth(legacyRecord)).toBe(2)
    expect(getExplorationDuration(legacyRecord)).toBe(30)
    expect(getExplorationTimestamp(legacyRecord)).toBe('2026-01-01T00:00:00Z')
    expect(getExplorationNotes(legacyRecord)).toBe('')
  })
})
