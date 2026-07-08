import { get, post } from './request'
import apiClient from './request'
import type { ApiResponse } from '@/types'

interface RagSearchResult {
  id: string
  name: string
  title?: string
  year: number | null
  region: string
  category?: string
  importance: number
  description?: string
  tags?: string[]
  score: number
  source: string
}

interface RagAskResult {
  answer: string
  sources: RagSearchResult[]
}

export interface KnowledgeEntry {
  id: number
  title: string
  content?: string
  content_preview?: string
  source_type: string
  source_url?: string | null
  file_name?: string | null
  file_type?: string | null
  event_name?: string | null
  year?: number | null
  year_end?: number | null
  region?: string | null
  category?: string | null
  tags?: string[] | null
  figures?: string[] | null
  keywords?: string[] | null
  importance?: number | null
  language?: string | null
  source_reliability?: number | null
  chunk_index: number
  chunk_total: number
  version: number
  version_count?: number
  parent_event_id?: string | null
  is_locked?: number
  status: string
  created_at?: string
  updated_at?: string
  last_indexed_at?: string
  content_hash?: string
}

export interface KnowledgeStats {
  total: number
  active: number
  by_source: Record<string, number>
  by_region: Record<string, number>
  by_category?: Record<string, number>
  versions?: number
  crawl_sources?: number
  recommended_sources?: number
  latest_update: string | null
}

export interface KnowledgeListResult {
  items: KnowledgeEntry[]
  total: number
  page: number
  page_size: number
}

export interface ConditionalSearchResult extends KnowledgeListResult {
  filters_applied?: Record<string, unknown>
}

export interface KnowledgeVersion {
  id: number
  version: number
  title: string
  content_hash: string
  change_summary?: string
  change_source?: string
  operator?: string
  snapshot_meta?: Record<string, unknown>
  created_at?: string
}

export interface ConditionalSearchParams {
  text?: string
  region?: string
  category?: string
  year_min?: number
  year_max?: number
  importance_min?: number
  event_name?: string
  event_name_like?: string
  tag?: string
  source_type?: string
  status?: string
  language?: string
  page?: number
  page_size?: number
  order_by?: 'relevance' | 'importance' | 'year' | 'updated_at'
  include_seed?: boolean
}

export interface SearchParams {
  query: string
  top_k?: number
  region?: string
  category?: string
  year_min?: number
  year_max?: number
  importance_min?: number
  event_name?: string
  tag?: string
  include_seed?: boolean
}

export interface CrawlSource {
  id: number
  name: string
  url: string
  category?: string
  region?: string
  tags?: string[]
  description?: string
  recommended: number
  enabled: number
  priority: number
  last_crawled_at?: string
  last_status?: string
  last_imported?: number
}

export const ragApi = {
  async search(params: SearchParams) {
    const res = await post<RagSearchResult[]>('/api/rag/search', params)
    return res
  },

  async hybridSearch(params: SearchParams) {
    const res = await post<RagSearchResult[]>('/api/rag/search-hybrid', params)
    return res
  },

  async ask(question: string, filters?: Partial<SearchParams>) {
    const res = await post<RagAskResult>('/api/rag/ask', { question, ...filters })
    return res
  },

  async conditionalSearch(params: ConditionalSearchParams) {
    const res = await post<ConditionalSearchResult>(
      '/api/rag/conditional-search',
      params,
    )
    return res
  },

  async rebuild() {
    // rebuild_index 是长任务，覆盖 axios 默认 15s 超时
    const res = await post<{ mode: string; count: number }>('/api/rag/rebuild', undefined, { timeout: 0 })
    return res
  },

  async importFile(file: File, metadata?: {
    event_name?: string
    year?: number
    year_end?: number
    region?: string
    category?: string
    tags?: string
    figures?: string
    importance?: number
    language?: string
    source_reliability?: number
    operator?: string
  }): Promise<ApiResponse<{ imported: number; skipped: number; updated?: number; chunks: number; format: string; file_name?: string; count?: number }>> {
    const formData = new FormData()
    formData.append('file', file)
    if (metadata?.event_name) formData.append('event_name', metadata.event_name)
    if (metadata?.year !== undefined && metadata?.year !== null) formData.append('year', String(metadata.year))
    if (metadata?.year_end !== undefined && metadata?.year_end !== null) formData.append('year_end', String(metadata.year_end))
    if (metadata?.region) formData.append('region', metadata.region)
    if (metadata?.category) formData.append('category', metadata.category)
    if (metadata?.tags) formData.append('tags', metadata.tags)
    if (metadata?.figures) formData.append('figures', metadata.figures)
    if (metadata?.importance !== undefined && metadata?.importance !== null) formData.append('importance', String(metadata.importance))
    if (metadata?.language) formData.append('language', metadata.language)
    if (metadata?.source_reliability) formData.append('source_reliability', String(metadata.source_reliability))
    if (metadata?.operator) formData.append('operator', metadata.operator)

    const res = await apiClient.post('/api/rag/import/file', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return res.data
  },

  async addManualEntry(data: {
    title: string
    content: string
    event_name?: string
    year?: number
    year_end?: number
    region?: string
    category?: string
    tags?: string[]
    figures?: string[]
    keywords?: string[]
    importance?: number
    language?: string
    source_reliability?: number
    parent_event_id?: string
  }) {
    const res = await post<{ imported: number; skipped: number; updated?: number; chunks: number }>(
      '/api/rag/import/manual',
      data,
    )
    return res
  },

  async importSeed() {
    const res = await post<{ imported: number; skipped: number; updated?: number; total_events: number }>(
      '/api/rag/import/seed',
      {},
    )
    return res
  },

  async getEntries(params?: {
    source_type?: string
    region?: string
    category?: string
    status?: string
    keyword?: string
    event_name?: string
    importance_min?: number
    year_min?: number
    year_max?: number
    page?: number
    page_size?: number
  }) {
    const res = await get<KnowledgeListResult>('/api/rag/entries', params)
    return res
  },

  async getEntry(id: number) {
    const res = await get<KnowledgeEntry>(`/api/rag/entries/${id}`)
    return res
  },

  async getEntryVersions(id: number) {
    const res = await get<{ items: KnowledgeVersion[]; total: number; entry_id: number }>(
      `/api/rag/entries/${id}/versions`,
    )
    return res
  },

  async updateEntry(id: number, data: Partial<KnowledgeEntry> & { change_summary?: string; operator?: string }): Promise<ApiResponse<{ version: number }>> {
    const res = await apiClient.put(`/api/rag/entries/${id}`, data)
    return res.data
  },

  async deleteEntry(id: number): Promise<ApiResponse<null>> {
    const res = await apiClient.delete(`/api/rag/entries/${id}`)
    return res.data
  },

  async getStats() {
    const res = await get<KnowledgeStats>('/api/rag/stats')
    return res
  },

  async listCrawlSources(params?: { recommended?: number; enabled?: number }) {
    const res = await get<{ items: CrawlSource[]; total: number }>('/api/rag/crawl-sources', params)
    return res
  },

  async triggerCrawl() {
    // 爬取是长任务，可能耗时 1-5 分钟，覆盖 axios 默认 15s 超时
    const res = await post<{
      imported: number; updated: number; skipped_duplicates: number;
      sources_processed: number; sources_failed: number; total_entries?: number;
    }>('/api/rag/crawl', undefined, { timeout: 0 })
    return res
  },
}
