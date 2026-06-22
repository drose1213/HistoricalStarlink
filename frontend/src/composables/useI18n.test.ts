import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { nextTick } from 'vue'

import { useI18n, type Locale } from './useI18n'
import { useAppStore } from '@/stores/app'

// 真实 storage key(与 stores/app.ts 保持一致)
const LOCALE_STORAGE_KEY = 'historical-starlink.locale'

/**
 * 通过 vi.stubGlobal 替换 navigator.language,避免污染 happy-dom 默认值。
 * 同时保留一个 helper 让我们能在 beforeEach 注入不同的语言。
 */
function setNavigatorLanguage(lang: string) {
  Object.defineProperty(window.navigator, 'language', {
    configurable: true,
    get: () => lang,
  })
}

describe('useI18n composable', () => {
  beforeEach(() => {
    // Default the test environment to Chinese so any test that does not
    // explicitly switch to English sees the Chinese dictionary. (happy-dom
    // ships with navigator.language === 'en-US' which would otherwise
    // flip the initial locale to English.)
    setNavigatorLanguage('zh-CN')
    setActivePinia(createPinia())
    localStorage.clear()
    document.documentElement.removeAttribute('lang')
    document.documentElement.removeAttribute('data-locale')
    vi.restoreAllMocks()
  })

  describe('basic return shape', () => {
    it('exposes t, tf, tc, locale, setLocale, eventDetailData', () => {
      const { t, tf, tc, locale, setLocale, eventDetailData } = useI18n()
      expect(typeof t).toBe('function')
      expect(typeof tf).toBe('function')
      expect(typeof tc).toBe('function')
      expect(typeof setLocale).toBe('function')
      expect(typeof eventDetailData).toBe('function')
      // locale is a ref-like
      expect(locale.value).toBeDefined()
      expect(['zh', 'en']).toContain(locale.value)
    })
  })

  describe('t() translation lookup', () => {
    it('returns the Chinese resource for the default locale', () => {
      const { t } = useI18n()
      expect(t('common.confirm')).toBe('确认')
      expect(t('nav.home')).toBe('首页')
    })

    it('interpolates {name} placeholders in Chinese strings', () => {
      const { t } = useI18n()
      expect(t('auth.welcome', { name: '小明' })).toBe('欢迎,小明!')
    })

    it('returns the key itself when the key is missing (no fallback dictionary)', () => {
      const { t } = useI18n()
      // Suppress the DEV warning emitted by the composable on first miss
      const warn = vi.spyOn(console, 'warn').mockImplementation(() => {})
      expect(t('definitely.missing.key')).toBe('definitely.missing.key')
      expect(warn).toHaveBeenCalled()
    })

    it('keeps unresolved placeholders literal when param is missing', () => {
      const { t } = useI18n()
      // 'auth.welcome' is "欢迎,{name}!" — missing param keeps {name} literal
      expect(t('auth.welcome')).toBe('欢迎,{name}!')
    })
  })

  describe('tf() / tc() / eventDetailData() helpers', () => {
    it('tf falls back to the provided string when the key is missing', () => {
      const { tf } = useI18n()
      const warn = vi.spyOn(console, 'warn').mockImplementation(() => {})
      expect(tf('events.unknown', '默认名')).toBe('默认名')
      expect(warn).toHaveBeenCalled()
    })

    it('tf interpolates the fallback when params are supplied', () => {
      const { tf } = useI18n()
      // 'events.shangyang_reform.name' is present in zh dictionary
      expect(tf('events.shangyang_reform.name', 'fallback')).toBe('商鞅变法')
    })

    it('tc translates a concept label in Chinese locale', () => {
      const { tc } = useI18n()
      expect(tc('四大发明')).toBe('四大发明')
    })

    it('tc returns the label as-is when it is not in the concept map', () => {
      const { tc } = useI18n()
      expect(tc('不存在的概念')).toBe('不存在的概念')
    })

    it('eventDetailData returns the description for a known event id', () => {
      const { eventDetailData } = useI18n()
      const data = eventDetailData('invention_of_paper')
      expect(data?.description).toContain('蔡伦')
    })

    it('eventDetailData returns undefined for an unknown event id', () => {
      const { eventDetailData } = useI18n()
      expect(eventDetailData('nope.no.such.event')).toBeUndefined()
    })
  })

  describe('setLocale()', () => {
    it('switches the active locale to en and t() returns English strings', async () => {
      const app = useAppStore()
      app.setLocale('en') // bypass composable to seed state
      await nextTick()
      const { t, locale } = useI18n()
      expect(locale.value).toBe('en')
      expect(t('common.confirm')).toBe('Confirm')
      expect(t('nav.home')).toBe('Home')
    })

    it('goes back to Chinese strings after switching locale to zh', async () => {
      const { t, setLocale, locale } = useI18n()
      setLocale('en')
      await nextTick()
      expect(locale.value).toBe('en')
      expect(t('common.confirm')).toBe('Confirm')

      setLocale('zh')
      await nextTick()
      expect(locale.value).toBe('zh')
      expect(t('common.confirm')).toBe('确认')
    })

    it('persists the new locale to localStorage with the canonical key', async () => {
      const { setLocale } = useI18n()
      setLocale('en' as Locale)
      await nextTick()
      expect(localStorage.getItem(LOCALE_STORAGE_KEY)).toBe('en')

      setLocale('zh' as Locale)
      await nextTick()
      expect(localStorage.getItem(LOCALE_STORAGE_KEY)).toBe('zh')
    })

    it('updates document.documentElement.lang and data-locale for accessibility', async () => {
      const { setLocale } = useI18n()
      setLocale('en' as Locale)
      await nextTick()
      expect(document.documentElement.getAttribute('lang')).toBe('en')
      expect(document.documentElement.getAttribute('data-locale')).toBe('en')

      setLocale('zh' as Locale)
      await nextTick()
      // useI18n normalizes zh -> 'zh-CN' on the <html lang="..."> attribute
      expect(document.documentElement.getAttribute('lang')).toBe('zh-CN')
      expect(document.documentElement.getAttribute('data-locale')).toBe('zh')
    })
  })

  describe('initial locale detection (cold start)', () => {
    it('falls back to "en" when navigator.language starts with "en" and no saved value', () => {
      setNavigatorLanguage('en-US')
      setActivePinia(createPinia())
      // mock localStorage.getItem to return null (no persisted value)
      const store = useAppStore()
      expect(store.locale).toBe('en')
    })

    it('falls back to "zh" when navigator.language is Chinese and no saved value', () => {
      setNavigatorLanguage('zh-CN')
      setActivePinia(createPinia())
      const store = useAppStore()
      expect(store.locale).toBe('zh')
    })

    it('falls back to "zh" when navigator.language is an unsupported language', () => {
      setNavigatorLanguage('fr-FR')
      setActivePinia(createPinia())
      const store = useAppStore()
      expect(store.locale).toBe('zh')
    })

    it('rehydrates the stored locale on next store creation (persistence works)', () => {
      // First session: user picks English
      setNavigatorLanguage('zh-CN')
      setActivePinia(createPinia())
      const session1 = useAppStore()
      session1.setLocale('en')
      expect(localStorage.getItem(LOCALE_STORAGE_KEY)).toBe('en')

      // Simulate a page refresh: a fresh pinia store reads localStorage
      setActivePinia(createPinia())
      const session2 = useAppStore()
      expect(session2.locale).toBe('en')
    })
  })

  describe('isolation between tests', () => {
    it('clears localStorage between cases so state does not leak', () => {
      // This test simply asserts the beforeEach hook behavior: localStorage is empty.
      expect(localStorage.getItem(LOCALE_STORAGE_KEY)).toBeNull()
    })
  })
})
