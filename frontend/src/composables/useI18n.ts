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
const warnedKeyPrefix = '__historical_starlink_i18n_warned__'

function warnMissingKey(key: string) {
  // 在所有环境下都警告: 缺失翻译属于 bug, 沉默返回 key 会让用户直接看到 key 字面量.
  // 使用 Set + sessionStorage 二次去重, 避免重复刷新刷屏.
  if (warnedKeys.has(key)) return
  warnedKeys.add(key)
  if (typeof sessionStorage !== 'undefined') {
    const flag = sessionStorage.getItem(warnedKeyPrefix)
    const cache: Record<string, true> = flag ? JSON.parse(flag) : {}
    if (cache[key]) return
    cache[key] = true
    try {
      sessionStorage.setItem(warnedKeyPrefix, JSON.stringify(cache))
    } catch {
      // sessionStorage 不可用时静默
    }
  }
  // eslint-disable-next-line no-console
  console.warn(`[i18n] missing key: ${key}`)
}

export function useI18n() {
  const appStore = useAppStore()

  const locale = computed<Locale>(() => appStore.locale)

  function t(key: string, params?: Record<string, string | number>): string {
    const dict = messages[locale.value] ?? messages.zh
    const text = resolvePath(dict, key)
    if (text == null) {
      warnMissingKey(key)
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
      warnMissingKey(key)
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
