// Lightweight i18n composable
// Uses a global reactive `locale` ref (provided by app store) and flat-key lookups.

import { computed } from 'vue'
import { useAppStore } from '@/stores/app'
import zh from '@/locales/zh'
import en from '@/locales/en'

export type Locale = 'zh' | 'en'
export type MessageSchema = Record<string, any>

const messages: Record<Locale, MessageSchema> = { zh, en }

/**
 * Resolve a dot-path like "nav.home" or "knowledge.tabs.overview"
 * against a nested message object. Returns undefined if any segment is missing.
 */
function resolvePath(obj: MessageSchema, path: string): string | undefined {
  const segments = path.split('.')
  let cur: any = obj
  for (const seg of segments) {
    if (cur && typeof cur === 'object' && seg in cur) {
      cur = cur[seg]
    } else {
      return undefined
    }
  }
  return typeof cur === 'string' ? cur : undefined
}

/** Replace `{name}` style placeholders in a translation string. */
function interpolate(template: string, params?: Record<string, string | number>): string {
  if (!params) return template
  return template.replace(/\{(\w+)\}/g, (_m, key) => {
    const v = params[key]
    return v == null ? `{${key}}` : String(v)
  })
}

const warnedKeys = new Set<string>()

export function useI18n() {
  const appStore = useAppStore()

  const locale = computed<Locale>(() => appStore.locale)

  function t(key: string, params?: Record<string, string | number>): string {
    const dict = messages[locale.value] ?? messages.zh
    const text = resolvePath(dict, key)
    if (text == null) {
      if (import.meta.env.DEV && !warnedKeys.has(key)) {
        warnedKeys.add(key)
        // eslint-disable-next-line no-console
        console.warn(`[i18n] missing key: ${key}`)
      }
      return key
    }
    return interpolate(text, params)
  }

  /**
   * Translate a key, falling back to a provided default string when the key
   * is missing in the current locale dictionary. Use this for data-driven
   * nodes (events / figures) whose source name is the Chinese authoritative
   * string: `tf(\`events.\${id}.name\`, event.name)`.
   */
  function tf(key: string, fallback: string, params?: Record<string, string | number>): string {
    const dict = messages[locale.value] ?? messages.zh
    const text = resolvePath(dict, key)
    if (text == null) {
      if (import.meta.env.DEV && !warnedKeys.has(key)) {
        warnedKeys.add(key)
        // eslint-disable-next-line no-console
        console.warn(`[i18n] missing key: ${key}`)
      }
      return interpolate(fallback, params)
    }
    return interpolate(text, params)
  }

  /** Translate a concept/tag string using the `concepts` map. */
  function tc(label: string): string {
    const dict = messages[locale.value] ?? messages.zh
    const concepts = dict.concepts as Record<string, string> | undefined
    if (concepts && label in concepts) {
      return concepts[label]
    }
    return label
  }

  /** Retrieve event detail data (description / causes / consequences) by event id. */
  function eventDetailData(eventId: string): { description?: string; causes?: string[]; consequences?: string[] } | undefined {
    const dict = messages[locale.value] ?? messages.zh
    const data = dict.eventData as Record<string, { description?: string; causes?: string[]; consequences?: string[] }> | undefined
    return data?.[eventId]
  }

  function setLocale(next: Locale) {
    appStore.setLocale(next)
    // Sync <html lang="..."> for accessibility / SEO.
    if (typeof document !== 'undefined') {
      document.documentElement.setAttribute('lang', next === 'zh' ? 'zh-CN' : 'en')
      document.documentElement.setAttribute('data-locale', next)
    }
  }

  return { locale, t, tf, tc, eventDetailData, setLocale }
}
