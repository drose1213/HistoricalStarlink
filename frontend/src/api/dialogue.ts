import { get, post } from './request'
import type {
  ApiResponse,
  PaginatedResponse,
  DialogueSession,
  DialogueMessage
} from '@/types'

export interface StartDialogueResponse {
  dialogue_id: string
  session: DialogueSession
  opening_message: DialogueMessage
}

export interface ChoiceResponse {
  next_message: DialogueMessage
  is_ended: boolean
  outcome_type?: 'historical' | 'alternate'
  outcome_summary?: string
}

export interface ChatResponse {
  next_message: DialogueMessage
  is_ended: boolean
}

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
    return get('/api/dialogue/records', { page, page_size: pageSize })
  },

  // --- 任意话题 dynamic 模式 ---
  startDynamic(sessionId: string, topic: string): Promise<ApiResponse<any>> {
    return post('/api/dialogue/dynamic/start', { session_id: sessionId, topic })
  },

  sendDynamicChoice(dialogueId: string, choiceId: string): Promise<ApiResponse<any>> {
    return post('/api/dialogue/dynamic/choice', { dialogue_id: dialogueId, choice_id: choiceId })
  },

  sendDynamicChat(dialogueId: string, message: string): Promise<ApiResponse<any>> {
    return post('/api/dialogue/dynamic/chat', { dialogue_id: dialogueId, message })
  },

  endDynamic(dialogueId: string): Promise<ApiResponse<any>> {
    return post('/api/dialogue/dynamic/end', { dialogue_id: dialogueId })
  }
}
