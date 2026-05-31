import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { dialogueApi } from '@/api/dialogue'
import type { DialogueMessage, DialogueSession } from '@/types'

function generateSessionId(): string {
  return `session_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`
}

export const useDialogueStore = defineStore('dialogue', () => {
  const currentSession = ref<DialogueSession | null>(null)
  const dialogueId = ref<string>('')
  const messages = ref<DialogueMessage[]>([])
  const isTyping = ref(false)
  const choices = ref<{ choice_id: string; text: string; consequence?: string }[]>([])
  const isLoading = ref(false)
  const isDialogueEnded = ref(false)
  const outcomeType = ref<'historical' | 'alternate' | null>(null)
  const outcomeSummary = ref('')
  const round = ref(0)
  const sessionId = ref(generateSessionId())

  const isTimelineAnimating = ref(false)

  const lastNpcMessage = computed(() => {
    for (let i = messages.value.length - 1; i >= 0; i--) {
      if (messages.value[i].role === 'narrative' || messages.value[i].role === 'system') {
        return messages.value[i]
      }
    }
    return null
  })

  async function startDialogue(eventId: string) {
    isLoading.value = true
    try {
      const res = await dialogueApi.startDialogue(sessionId.value, eventId) as any
      const data = res.data
      dialogueId.value = String(data.dialogue_id)
      currentSession.value = data
      messages.value = []
      round.value = 1
      isDialogueEnded.value = false
      outcomeType.value = null
      outcomeSummary.value = ''

      if (data.history && Array.isArray(data.history)) {
        for (const h of data.history) {
          if (h.role === 'narrative') {
            appendMessage({
              id: `npc_${Date.now()}`,
              role: 'narrative',
              content: h.content,
              choices: h.choices,
              timestamp: Date.now()
            })
            if (h.choices) {
              choices.value = h.choices
            }
          }
        }
      } else if (data.narrative) {
        appendMessage({
          id: `npc_${Date.now()}`,
          role: 'narrative',
          content: data.narrative,
          choices: data.choices,
          timestamp: Date.now()
        })
        if (data.choices) {
          choices.value = data.choices
        }
      }

      return data
    } finally {
      isLoading.value = false
    }
  }

  async function sendChoice(choiceId: string) {
    const selectedChoice = choices.value.find(c => c.choice_id === choiceId)
    if (selectedChoice) {
      appendMessage({
        id: `choice_${Date.now()}`,
        role: 'choice',
        content: selectedChoice.text,
        timestamp: Date.now()
      })
    }

    choices.value = []
    round.value++
    isLoading.value = true
    isTyping.value = true

    try {
      const res = await dialogueApi.sendChoice(dialogueId.value, choiceId, round.value) as any
      const data = res.data

      if (data.timeline_change) {
        triggerTimelineAnimation()
      }

      const content = data.narrative || ''
      const finalMsg = await typeMessage({
        id: `npc_${Date.now()}`,
        role: 'narrative',
        content,
        choices: data.choices,
        timestamp: Date.now()
      })

      if (data.is_ending) {
        isDialogueEnded.value = true
        outcomeType.value = data.ending_type || 'historical'
        outcomeSummary.value = data.choices_summary
          ? data.choices_summary.map((s: any) => s.consequence).filter(Boolean).join(' → ')
          : content
        round.value = 0
      } else if (finalMsg.choices && finalMsg.choices.length > 0) {
        choices.value = finalMsg.choices
      }
    } finally {
      isLoading.value = false
      isTyping.value = false
    }
  }

  async function sendFreeText(message: string) {
    appendMessage({
      id: `user_${Date.now()}`,
      role: 'user',
      content: message,
      timestamp: Date.now()
    })

    isLoading.value = true
    isTyping.value = true

    try {
      const res = await dialogueApi.sendFreeText(dialogueId.value, message) as any
      const data = res.data

      const content = data.narrative || ''
      const finalMsg = await typeMessage({
        id: `npc_${Date.now()}`,
        role: 'narrative',
        content,
        choices: data.choices,
        timestamp: Date.now()
      })

      if (data.is_ending) {
        isDialogueEnded.value = true
        outcomeType.value = data.ending_type || 'historical'
      } else if (finalMsg.choices && finalMsg.choices.length > 0) {
        choices.value = finalMsg.choices
      }
    } finally {
      isLoading.value = false
      isTyping.value = false
    }
  }

  function appendMessage(msg: DialogueMessage) {
    messages.value.push({ ...msg })
  }

  function typeMessage(msg: DialogueMessage): Promise<DialogueMessage> {
    return new Promise(resolve => {
      const chars = msg.content.split('')
      const typedMsg = { ...msg, content: '' }
      appendMessage(typedMsg)
      let i = 0
      const interval = setInterval(() => {
        if (i < chars.length) {
          const last = messages.value[messages.value.length - 1]
          last.content += chars[i]
          i++
        } else {
          clearInterval(interval)
          resolve(msg)
        }
      }, 30)
    })
  }

  function triggerTimelineAnimation() {
    isTimelineAnimating.value = true
    setTimeout(() => {
      isTimelineAnimating.value = false
    }, 1200)
  }

  function resetDialogue() {
    currentSession.value = null
    dialogueId.value = ''
    messages.value = []
    isTyping.value = false
    choices.value = []
    isLoading.value = false
    isDialogueEnded.value = false
    outcomeType.value = null
    outcomeSummary.value = ''
    round.value = 0
    sessionId.value = generateSessionId()
    isTimelineAnimating.value = false
  }

  return {
    currentSession,
    dialogueId,
    messages,
    isTyping,
    choices,
    isLoading,
    isDialogueEnded,
    outcomeType,
    outcomeSummary,
    round,
    sessionId,
    isTimelineAnimating,
    lastNpcMessage,
    startDialogue,
    sendChoice,
    sendFreeText,
    resetDialogue
  }
})
