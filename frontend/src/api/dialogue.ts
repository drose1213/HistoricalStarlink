import { get, post } from './request'
import { normalizePaginatedResponse } from './pagination'
import type {
  ApiResponse,
  PaginatedResponse,
  DialogueSession,
  DialogueChoice
} from '@/types'

export interface DialogueChoiceSummary {
  round: number
  choice_id?: string
  choice_text?: string
  consequence?: string
}

export interface DialogueTurnResponse {
  dialogue_id: string | number
  session_id?: string
  event_id?: string
  topic?: string
  npc_name?: string
  npc_role?: string
  npc_symbol?: string
  context?: string
  narrative: string
  choices?: DialogueChoice[]
  round: number
  history?: Array<Record<string, unknown>>
  timeline_change?: boolean
  mood?: string
  is_ending?: boolean
  ending_type?: string
  path_signature?: string
  partial_match?: boolean
  cumulative_impact?: Record<string, number>
  predicted_endings?: Array<Record<string, unknown>>
  choices_summary?: DialogueChoiceSummary[]
  is_dynamic?: boolean
  already_completed?: boolean
}

export interface StartDialogueResponse {
  dialogue_id: string
  session_id?: string
  event_id?: string
  topic?: string
  npc_name?: string
  npc_role?: string
  npc_symbol?: string
  context?: string
  narrative?: string
  choices?: DialogueChoice[]
  round?: number
  history?: Array<Record<string, unknown>>
  path_signature?: string
  cumulative_impact?: Record<string, number>
  predicted_endings?: Array<Record<string, unknown>>
  is_dynamic?: boolean
}

export type ChoiceResponse = DialogueTurnResponse

export type ChatResponse = DialogueTurnResponse

export const dialogueApi = {
  startDialogue(sessionId: string, eventId: string): Promise<ApiResponse<StartDialogueResponse>> {
    return post('/api/dialogue/start', { session_id: sessionId, event_id: eventId })
  },

  sendChoice(dialogueId: string, choiceId: string, round: number): Promise<ApiResponse<ChoiceResponse>> {
    return post('/api/dialogue/choice', { dialogue_id: dialogueId, choice_id: choiceId, round })
  },

  sendFreeText(dialogueId: string, message: string): Promise<ApiResponse<ChatResponse>> {
    return post('/api/dialogue/chat', { dialogue_id: dialogueId, message })
  },

  getDialogue(dialogueId: string): Promise<ApiResponse<DialogueSession>> {
    return get(`/api/dialogue/${dialogueId}`)
  },

  getDialogues(page = 1, pageSize = 20): Promise<ApiResponse<PaginatedResponse<DialogueSession>>> {
    return get<DialogueSession[]>('/api/dialogue/records', { page, page_size: pageSize })
      .then(normalizePaginatedResponse)
  },

  // --- 任意话题 dynamic 模式 ---
  startDynamic(sessionId: string, topic: string, heroId?: string): Promise<ApiResponse<StartDialogueResponse>> {
    const payload: Record<string, unknown> = { session_id: sessionId, topic }
    if (heroId) payload.hero_id = heroId
    return post('/api/dialogue/dynamic/start', payload)
  },

  sendDynamicChoice(dialogueId: string, choiceId: string): Promise<ApiResponse<ChoiceResponse>> {
    return post('/api/dialogue/dynamic/choice', { dialogue_id: dialogueId, choice_id: choiceId })
  },

  sendDynamicChat(dialogueId: string, message: string): Promise<ApiResponse<ChatResponse>> {
    return post('/api/dialogue/dynamic/chat', { dialogue_id: dialogueId, message })
  },

  endDynamic(dialogueId: string): Promise<ApiResponse<ChatResponse>> {
    return post('/api/dialogue/dynamic/end', { dialogue_id: dialogueId })
  }
}

// 英雄卡牌相关类型
export interface HeroPersona {
  hero_id: string
  name: string
  role: string
  era: string
  greeting: string
  style_hint: string
  speaking_pattern: string
  description: string
}

export interface ResolveHeroResponse {
  heroes: HeroPersona[]
  source: 'llm' | 'fallback' | 'empty'
}

/**
 * 为话题推荐英雄卡牌列表.
 * - LLM 智能推荐
 * - 失败时回退到 events_data 关键词匹配
 */
export function resolveHero(topic: string): Promise<ApiResponse<ResolveHeroResponse>> {
  return post('/api/dialogue/dynamic/resolve-hero', { topic })
}
