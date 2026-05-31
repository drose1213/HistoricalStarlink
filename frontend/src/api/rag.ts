import { post } from './request'
import type { ApiResponse, HistoryEvent } from '@/types'

interface RagSearchResult {
  id: string
  name: string
  year: number
  region: string
  importance: number
  description: string
  score: number
}

interface RagAskResult {
  answer: string
  sources: RagSearchResult[]
}

export const ragApi = {
  async search(query: string, top_k = 5) {
    const res = await post<RagSearchResult[]>('/api/rag/search', { query, top_k })
    return res
  },

  async ask(question: string) {
    const res = await post<RagAskResult>('/api/rag/ask', { question })
    return res
  },

  async rebuild() {
    const res = await post<{ mode: string; count: number }>('/api/rag/rebuild')
    return res
  }
}
