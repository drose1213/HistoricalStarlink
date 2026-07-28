import { ref, reactive, computed, onBeforeUnmount } from 'vue'
import { ragApi } from '@/api/rag'
import { allEvents as historyEvents, searchEvents } from '@/data/events'
import type { HistoryEvent } from '@/types'

/**
 * 星链搜索 composable
 *
 * 职责:
 * - 合并本地事件表 (searchEvents) + RAG 知识库 (hybridSearch → search) 搜索结果
 * - 防抖 + 加载状态管理 (避免每次按键都触发 API)
 * - 暴露 onUnmounted 时自动清理的 timer, 杜绝 setState-on-unmounted 警告
 *
 * 返回值:
 * - query / showDropdown / isLoading: 双向绑定的状态
 * - results: 计算属性, 合并 + 去重 + 排序后的最终结果
 * - onInput / onEnter / onSelect / onBlur: 给搜索框的回调
 */
export interface LocalSearchResult {
  id: string
  name: string
  year: number | null
  region: 'china' | 'foreign'
  importance: number
  description?: string
  score: number
  source?: string
}

interface UseStarlinkSearchOptions {
  /** 防抖触发 RAG 搜索的延迟 (ms), 默认 300 */
  debounceMs?: number
  /** 关闭 loading 提示的延迟 (ms), 默认 600 */
  loadingResetMs?: number
  /** 最终展示的结果数量上限, 默认 6 */
  resultLimit?: number
  /** 本地匹配的最大数量, 默认 8 */
  localLimit?: number
  /** RAG top_k, 默认 5 */
  topK?: number
}

function normalizeSearchText(value: string): string {
  return value.trim().toLowerCase().replace(/\s+/g, '')
}

function buildSearchResult(
  event: HistoryEvent,
  score: number,
  source: string,
  description?: string,
): LocalSearchResult {
  return {
    id: event.id,
    name: event.name,
    year: event.year,
    region: event.region,
    importance: event.importance,
    description: description || event.description,
    score,
    source,
  }
}

function dedupeSearchResults(results: LocalSearchResult[]): LocalSearchResult[] {
  const deduped = new Map<string, LocalSearchResult>()
  for (const result of results) {
    const existing = deduped.get(result.id)
    if (!existing || result.score > existing.score) {
      deduped.set(result.id, result)
    }
  }
  return [...deduped.values()]
}

function sortSearchResults(results: LocalSearchResult[], query: string): LocalSearchResult[] {
  const normalizedQuery = normalizeSearchText(query)
  return [...results].sort((a, b) => {
    const aName = normalizeSearchText(a.name)
    const bName = normalizeSearchText(b.name)
    const aExact = aName === normalizedQuery ? 3 : aName.startsWith(normalizedQuery) ? 2 : aName.includes(normalizedQuery) ? 1 : 0
    const bExact = bName === normalizedQuery ? 3 : bName.startsWith(normalizedQuery) ? 2 : bName.includes(normalizedQuery) ? 1 : 0
    if (aExact !== bExact) return bExact - aExact
    if (a.score !== b.score) return b.score - a.score
    if (a.importance !== b.importance) return b.importance - b.importance
    return a.year === b.year ? a.name.localeCompare(b.name, 'zh-CN') : (b.year || 0) - (a.year || 0)
  })
}

function isSearchRelevant(candidate: Partial<LocalSearchResult> & { title?: string }, query: string): boolean {
  const normalizedQuery = normalizeSearchText(query)
  if (!normalizedQuery) return true
  const haystacks = [candidate.name, candidate.title, candidate.description]
    .filter((value): value is string => Boolean(value))
    .map(value => normalizeSearchText(value))
  return haystacks.some(value => value.includes(normalizedQuery))
}

export function useStarlinkSearch(options: UseStarlinkSearchOptions = {}) {
  const debounceMs = options.debounceMs ?? 300
  const loadingResetMs = options.loadingResetMs ?? 600
  const resultLimit = options.resultLimit ?? 6
  const localLimit = options.localLimit ?? 8
  const topK = options.topK ?? 5

  const query = ref('')
  const showDropdown = ref(false)
  const isLoading = ref(false)
  const ragResults = ref<LocalSearchResult[]>([])

  // 模块级 timer id, 在 dispose 时统一清理
  let loadingTimer: ReturnType<typeof setTimeout> | null = null
  let abortTimer: ReturnType<typeof setTimeout> | null = null
  let lastAbortToken = 0
  let disposed = false

  const eventById = computed(() => new Map(historyEvents.map(event => [event.id, event])))
  const eventIdByName = computed(() => {
    const pairs = historyEvents.map(event => [normalizeSearchText(event.name), event.id] as const)
    return new Map(pairs)
  })

  function resolveEventFromSearchCandidate(candidate: Partial<LocalSearchResult> & { title?: string }): HistoryEvent | null {
    if (candidate.id) {
      const byId = eventById.value.get(candidate.id)
      if (byId) return byId
    }
    const nameKey = normalizeSearchText(candidate.name || candidate.title || '')
    if (!nameKey) return null
    const eventId = eventIdByName.value.get(nameKey)
    if (!eventId) return null
    return eventById.value.get(eventId) || null
  }

  function sanitizeRagResults(query: string, items: LocalSearchResult[]): LocalSearchResult[] {
    const out: LocalSearchResult[] = []
    for (const item of items) {
      if (!isSearchRelevant(item, query)) continue
      const event = resolveEventFromSearchCandidate(item)
      if (!event) continue
      out.push(buildSearchResult(
        event,
        Math.max(item.score || 0, event.importance),
        item.source || 'rag',
        item.description,
      ))
    }
    return out
  }

  function clearTimers() {
    if (loadingTimer) {
      clearTimeout(loadingTimer)
      loadingTimer = null
    }
    if (abortTimer) {
      clearTimeout(abortTimer)
      abortTimer = null
    }
  }

  async function runRagSearch(q: string, token: number) {
    try {
      try {
        const res = await ragApi.hybridSearch({ query: q, top_k: topK })
        if (disposed || token !== lastAbortToken) return
        ragResults.value = sanitizeRagResults(q, (res.data || []) as LocalSearchResult[])
      } catch {
        const res = await ragApi.search({ query: q, top_k: topK })
        if (disposed || token !== lastAbortToken) return
        ragResults.value = sanitizeRagResults(q, (res.data || []) as LocalSearchResult[])
      }
    } catch {
      if (disposed || token !== lastAbortToken) return
      ragResults.value = []
    }
  }

  function onInput() {
    showDropdown.value = true
    isLoading.value = true
    clearTimers()
    const myToken = ++lastAbortToken
    loadingTimer = setTimeout(() => {
      if (disposed) return
      isLoading.value = false
    }, loadingResetMs)
    abortTimer = setTimeout(() => {
      if (disposed) return
      const q = query.value.trim()
      if (!q) {
        ragResults.value = []
        return
      }
      void runRagSearch(q, myToken)
    }, debounceMs)
  }

  function onBlur() {
    setTimeout(() => {
      if (disposed) return
      showDropdown.value = false
    }, 200)
  }

  function onFocus() {
    if (query.value.trim()) showDropdown.value = true
  }

  function reset() {
    query.value = ''
    showDropdown.value = false
    isLoading.value = false
    ragResults.value = []
    clearTimers()
  }

  function onSelect(id: string): boolean {
    if (!eventById.value.has(id)) return false
    reset()
    return true
  }

  const results = computed<LocalSearchResult[]>(() => {
    const q = query.value.trim()
    if (!q) return []

    const localResults = searchEvents(q)
      .slice(0, localLimit)
      .map(event => buildSearchResult(event, event.importance + 20, 'event_table'))

    const merged = dedupeSearchResults([...localResults, ...ragResults.value])
    return sortSearchResults(merged, q).slice(0, resultLimit)
  })

  function onEnter(): string | null {
    if (results.value.length > 0) {
      const first = results.value[0]
      onSelect(first.id)
      return first.id
    }
    if (query.value.trim()) {
      showDropdown.value = true
    }
    return null
  }

  // 自动注册清理钩子: 在组件卸载时清掉 timer, 避免 setState-on-unmounted
  onBeforeUnmount(() => {
    disposed = true
    clearTimers()
    // 让正在进行的 RAG 请求的 stale 回调被丢弃 (通过 lastAbortToken 自增)
    lastAbortToken++
  })

  // 把响应式状态包装成 reactive, 这样在模板里访问 search.query / search.results
  // 时 Vue 会自动解包, 不需要在每个绑定处写 .value.
  const state = reactive({
    query,
    showDropdown,
    isLoading,
    results,
  })

  return Object.assign(state, {
    onInput,
    onBlur,
    onFocus,
    onSelect,
    onEnter,
    reset,
  })
}
