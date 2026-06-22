import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { formatDateTime, formatDate, formatRelativeTime } from './datetime'

describe('datetime utilities', () => {
  describe('formatDateTime', () => {
    it('formats explicit UTC timestamp (with Z suffix)', () => {
      const out = formatDateTime('2026-06-05T01:43:42Z')
      expect(out).not.toBe('')
      expect(out).toContain('2026-06-05')
    })

    it('parses naive datetime (no Z suffix) by treating it as UTC', () => {
      const out = formatDateTime('2026-06-05T01:43:42')
      expect(out).not.toBe('')
      // Date object should have been constructed — hour component is present
      expect(out).toMatch(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/)
    })

    it('returns empty string for null', () => {
      expect(formatDateTime(null)).toBe('')
    })

    it('returns empty string for undefined', () => {
      expect(formatDateTime(undefined)).toBe('')
    })

    it('returns empty string for empty string', () => {
      expect(formatDateTime('')).toBe('')
    })

    it('returns empty string for invalid date string', () => {
      expect(formatDateTime('not-a-date')).toBe('')
    })
  })

  describe('formatDate', () => {
    it('returns the local date portion only', () => {
      const out = formatDate('2026-06-05T01:43:42Z')
      expect(out).toMatch(/^\d{4}-\d{2}-\d{2}$/)
      expect(out.length).toBe(10)
    })

    it('returns empty string for invalid input', () => {
      expect(formatDate(null)).toBe('')
      expect(formatDate(undefined)).toBe('')
      expect(formatDate('')).toBe('')
    })
  })

  describe('formatRelativeTime', () => {
    beforeEach(() => {
      vi.useFakeTimers()
      // Pin "now" to a stable instant: 2026-06-10T12:00:00Z
      vi.setSystemTime(new Date('2026-06-10T12:00:00Z'))
    })

    afterEach(() => {
      vi.useRealTimers()
    })

    it('returns 刚刚 when within 60 seconds', () => {
      // 30 seconds ago
      const ts = new Date('2026-06-10T11:59:30Z').toISOString()
      expect(formatRelativeTime(ts)).toBe('刚刚')
    })

    it('returns X 分钟前 when between 60s and 1h', () => {
      // 5 minutes ago
      const ts = new Date('2026-06-10T11:55:00Z').toISOString()
      expect(formatRelativeTime(ts)).toBe('5 分钟前')
    })

    it('returns X 小时前 when between 1h and 1 day', () => {
      // 3 hours ago
      const ts = new Date('2026-06-10T09:00:00Z').toISOString()
      expect(formatRelativeTime(ts)).toBe('3 小时前')
    })

    it('returns X 天前 when between 1 day and 30 days', () => {
      // 5 days ago
      const ts = new Date('2026-06-05T12:00:00Z').toISOString()
      expect(formatRelativeTime(ts)).toBe('5 天前')
    })

    it('returns formatted date for times older than 30 days', () => {
      // 60 days ago
      const ts = new Date('2026-04-11T12:00:00Z').toISOString()
      const out = formatRelativeTime(ts)
      // Should be a local date string (10 chars, YYYY-MM-DD)
      expect(out).toMatch(/^\d{4}-\d{2}-\d{2}$/)
    })

    it('falls back to formatDateTime for future timestamps', () => {
      // 1 hour in the future
      const ts = new Date('2026-06-10T13:00:00Z').toISOString()
      const out = formatRelativeTime(ts)
      expect(out).toMatch(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/)
    })

    it('returns empty string for invalid input', () => {
      expect(formatRelativeTime(null)).toBe('')
      expect(formatRelativeTime('')).toBe('')
    })
  })
})
