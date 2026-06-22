import { describe, it, expect, beforeEach } from 'vitest'
import { getSessionId } from './session'

const SESSION_KEY = 'explorer_session_id'

describe('session utility', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('first call generates an id matching session_<digits>_<base36> and stores it', () => {
    const id = getSessionId()
    expect(id.length).toBeGreaterThan(0)
    expect(id).toMatch(/^session_\d+_[a-z0-9]+$/)
    expect(localStorage.getItem(SESSION_KEY)).toBe(id)
  })

  it('returns the same id on subsequent calls (no regeneration)', () => {
    const first = getSessionId()
    const second = getSessionId()
    const third = getSessionId()
    expect(second).toBe(first)
    expect(third).toBe(first)
    // Only one entry in storage
    expect(localStorage.getItem(SESSION_KEY)).toBe(first)
  })

  it('returned id has positive length', () => {
    expect(getSessionId().length).toBeGreaterThan(0)
  })

  it('uses a pre-existing localStorage value if present', () => {
    localStorage.setItem(SESSION_KEY, 'session_1234567890_abcdefgh')
    const id = getSessionId()
    expect(id).toBe('session_1234567890_abcdefgh')
  })
})
