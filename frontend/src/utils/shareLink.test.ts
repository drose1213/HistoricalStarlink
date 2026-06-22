import { describe, expect, it, beforeEach, afterEach, vi } from 'vitest'
import {
  encodeTopic,
  decodeTopic,
  generateShareLink,
  parseShareLink,
  parseShareLinkFromUrl,
} from './shareLink'

describe('shareLink utilities', () => {
  describe('encodeTopic / decodeTopic', () => {
    it('round-trips plain ASCII strings', () => {
      const topic = 'Industrial Revolution'
      expect(decodeTopic(encodeTopic(topic))).toBe(topic)
    })

    it('round-trips Chinese characters', () => {
      const topic = '如果秦始皇没有焚书坑儒'
      const encoded = encodeTopic(topic)
      expect(encoded.length).toBeGreaterThan(0)
      // base64url 字符集: A-Z / a-z / 0-9 / - / _, 不含 = 填充
      expect(encoded).toMatch(/^[A-Za-z0-9_-]+$/)
      expect(decodeTopic(encoded)).toBe(topic)
    })

    it('handles mixed CJK + emoji + ASCII', () => {
      const topic = '三国演义 ⚔️ AI 时代'
      expect(decodeTopic(encodeTopic(topic))).toBe(topic)
    })

    it('returns empty string for empty input', () => {
      expect(encodeTopic('')).toBe('')
      expect(decodeTopic('')).toBe('')
    })

    it('returns empty string for invalid base64', () => {
      expect(decodeTopic('!!!not-base64!!!')).toBe('')
    })
  })

  describe('generateShareLink', () => {
    it('returns origin + /landing?d=... format', () => {
      // 在 happy-dom 环境下，window.location.origin 为 'http://localhost:3000'
      const link = generateShareLink('商鞅变法')
      expect(link).toContain('/landing?d=')
      // 编码部分应可解码回原 topic
      const encoded = link.split('?d=')[1]
      expect(decodeTopic(encoded)).toBe('商鞅变法')
    })

    it('handles empty topic gracefully', () => {
      const link = generateShareLink('')
      expect(link).toContain('/landing?d=')
    })
  })

  describe('parseShareLinkFromUrl (pure function)', () => {
    it('extracts and decodes topic from URL', () => {
      const topic = '甲午战争'
      const encoded = encodeTopic(topic)
      const url = `https://example.com/landing?d=${encoded}`
      expect(parseShareLinkFromUrl(url)).toBe(topic)
    })

    it('returns null when ?d= is missing', () => {
      expect(parseShareLinkFromUrl('https://example.com/landing')).toBeNull()
    })

    it('returns null when ?d= is empty', () => {
      expect(parseShareLinkFromUrl('https://example.com/landing?d=')).toBeNull()
    })

    it('returns null for invalid base64 in ?d=', () => {
      expect(parseShareLinkFromUrl('https://example.com/landing?d=@@@')).toBeNull()
    })
  })

  describe('parseShareLink (window-based)', () => {
    beforeEach(() => {
      // 设置一个可被 jsdom 解析的 URL
      Object.defineProperty(window, 'location', {
        value: { origin: 'http://localhost:3000', search: '' },
        writable: true,
        configurable: true,
      })
    })

    it('returns null when no ?d= in current URL', () => {
      window.location.search = ''
      expect(parseShareLink()).toBeNull()
    })

    it('decodes ?d= from current URL', () => {
      const encoded = encodeTopic('大唐盛世')
      window.location.search = `?d=${encoded}`
      expect(parseShareLink()).toBe('大唐盛世')
    })
  })

  describe('generate → parse closed loop', () => {
    it('preserves Chinese topic end-to-end', () => {
      const original = '贞观之治：如果唐太宗没有玄武门之变'
      const link = generateShareLink(original)
      // 从生成的链接中提取编码部分，再用纯函数解析
      const encoded = link.split('?d=')[1]
      const reconstructed = parseShareLinkFromUrl(
        `https://example.com/landing?d=${encoded}`,
      )
      expect(reconstructed).toBe(original)
    })
  })
})
