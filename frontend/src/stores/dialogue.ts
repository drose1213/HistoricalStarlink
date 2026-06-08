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
  const errorMessage = ref<string>('')
  const notFound = ref(false)
  const isDynamic = ref(false)  // 当前对话是否 dynamic 模式
  const currentTopic = ref<string>('')  // dynamic 模式的话题

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
    errorMessage.value = ''
    notFound.value = false
    isDynamic.value = eventId.startsWith('dynamic_')
    if (!isDynamic.value) {
      currentTopic.value = ''
    }
    try {
      const res = isDynamic.value
        ? await dialogueApi.startDynamic(sessionId.value, currentTopic.value || eventId) as any
        : await dialogueApi.startDialogue(sessionId.value, eventId) as any
      const data = res.data
      dialogueId.value = String(data.dialogue_id)
      currentSession.value = data
      messages.value = []
      round.value = 1
      isDialogueEnded.value = false
      outcomeType.value = null
      outcomeSummary.value = ''
      if (isDynamic.value) {
        currentTopic.value = data.topic || currentTopic.value
      }

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
    } catch (err: any) {
      const status = err?.response?.status
      if (status === 404) {
        notFound.value = true
        errorMessage.value = isDynamic.value
          ? '该话题时空对话机暂时无法回应'
          : '该历史事件暂未配置时空对话剧本'
      } else {
        errorMessage.value = err?.response?.data?.detail || err?.message || '对话启动失败'
      }
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 专门为 dynamic 模式提供的入口: 直接从 topic 启动, 走 startDynamic 接口.
   * HomeView 用户输入任意话题时调用.
   */
  async function startDynamicFromTopic(topic: string) {
    currentTopic.value = topic.trim()
    if (!currentTopic.value) {
      errorMessage.value = '请输入话题'
      throw new Error('topic is required')
    }
    // 复用 startDialogue, 但需要预先设置 isDynamic 让逻辑走 dynamic 分支
    isDynamic.value = true
    // 构造一个 dynamic_<slug> 的 eventId 给 startDialogue 用
    const slug = currentTopic.value.replace(/[^\w一-龥]+/g, '_').slice(0, 32) || 'unknown'
    return await startDialogue(`dynamic_${slug}`)
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
      const res = isDynamic.value
        ? await dialogueApi.sendDynamicChoice(dialogueId.value, choiceId) as any
        : await dialogueApi.sendChoice(dialogueId.value, choiceId, round.value) as any
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
      const res = isDynamic.value
        ? await dialogueApi.sendDynamicChat(dialogueId.value, message) as any
        : await dialogueApi.sendFreeText(dialogueId.value, message) as any
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
    errorMessage.value = ''
    notFound.value = false
    isDynamic.value = false
    currentTopic.value = ''
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
    errorMessage,
    notFound,
    isDynamic,
    currentTopic,
    lastNpcMessage,
    startDialogue,
    startDynamicFromTopic,
    sendChoice,
    sendFreeText,
    resetDialogue
  }
})
