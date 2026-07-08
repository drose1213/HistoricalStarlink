import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { dialogueApi } from '@/api/dialogue'
import type { ChoiceResponse, HeroPersona, StartDialogueResponse } from '@/api/dialogue'
import type { DialogueChoice, DialogueMessage } from '@/types'

function generateSessionId(): string {
  return `session_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`
}

export const useDialogueStore = defineStore('dialogue', () => {
  const currentSession = ref<StartDialogueResponse | null>(null)
  const dialogueId = ref<string>('')
  const messages = ref<DialogueMessage[]>([])
  const isTyping = ref(false)
  const choices = ref<{ choice_id: string; text: string; consequence?: string }[]>([])
  const isLoading = ref(false)
  const isDialogueEnded = ref(false)
  const outcomeType = ref<string | null>(null)
  const outcomeSummary = ref('')
  const round = ref(0)
  const sessionId = ref(generateSessionId())
  const errorMessage = ref<string>('')
  const notFound = ref(false)
  const isDynamic = ref(false)  // 当前对话是否 dynamic 模式
  const currentTopic = ref<string>('')  // dynamic 模式的话题
  const selectedHero = ref<HeroPersona | null>(null)  // dynamic 模式选中的英雄
  const isSelectingHero = ref(false)  // 是否在英雄选人阶段
  const pendingHeroId = ref<string>('')  // 暂存的 hero_id, startDialogue 时透传给后端

  const isTimelineAnimating = ref(false)

  function getErrorStatus(err: unknown): number | undefined {
    return typeof err === 'object' && err !== null && 'response' in err
      ? (err.response as { status?: number }).status
      : undefined
  }

  function getErrorMessage(err: unknown, fallback: string): string {
    if (typeof err === 'object' && err !== null && 'response' in err) {
      const response = err.response as { data?: { detail?: string } }
      if (response.data?.detail) return response.data.detail
    }
    return err instanceof Error ? err.message : fallback
  }

  function buildOutcomeSummary(data: ChoiceResponse): string {
    const consequences = data.choices_summary
      ?.map(summary => summary.consequence)
      .filter((value): value is string => Boolean(value))
    if (consequences?.length) {
      return consequences.join(' → ')
    }
    return data.narrative || ''
  }

  function isDialogueChoiceList(value: unknown): value is DialogueChoice[] {
    return Array.isArray(value) && value.every(choice => (
      typeof choice === 'object' &&
      choice !== null &&
      typeof (choice as { choice_id?: unknown }).choice_id === 'string' &&
      typeof (choice as { text?: unknown }).text === 'string'
    ))
  }

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
        ? await dialogueApi.startDynamic(sessionId.value, currentTopic.value || eventId, pendingHeroId.value || undefined)
        : await dialogueApi.startDialogue(sessionId.value, eventId)
      // 启动后清掉 pendingHeroId, 避免污染后续对话
      if (isDynamic.value) {
        pendingHeroId.value = ''
      }
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
            const historyChoices = isDialogueChoiceList(h.choices) ? h.choices : undefined
            appendMessage({
              id: `npc_${Date.now()}`,
              role: 'narrative',
              content: typeof h.content === 'string' ? h.content : '',
              choices: historyChoices,
              timestamp: Date.now()
            })
            if (historyChoices) {
              choices.value = historyChoices
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
    } catch (err: unknown) {
      const status = getErrorStatus(err)
      if (status === 404) {
        notFound.value = true
        errorMessage.value = isDynamic.value
          ? '该话题时空对话机暂时无法回应'
          : '该历史事件暂未配置时空对话剧本'
      } else {
        errorMessage.value = getErrorMessage(err, '对话启动失败')
      }
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 专门为 dynamic 模式提供的入口: 直接从 topic 启动, 走 startDynamic 接口.
   * HomeView 用户输入任意话题时调用.
   * 可选传入 heroId, 会透传给后端 /dynamic/start 用于角色扮演.
   */
  async function startDynamicFromTopic(topic: string, heroId?: string) {
    currentTopic.value = topic.trim()
    if (!currentTopic.value) {
      errorMessage.value = '请输入话题'
      throw new Error('topic is required')
    }
    // 复用 startDialogue, 但需要预先设置 isDynamic 让逻辑走 dynamic 分支
    isDynamic.value = true
    // 保存 hero_id 到 session, 后续 startDialogue 时透传给后端
    pendingHeroId.value = heroId || ''
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
        ? await dialogueApi.sendDynamicChoice(dialogueId.value, choiceId)
        : await dialogueApi.sendChoice(dialogueId.value, choiceId, round.value)
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
        outcomeSummary.value = buildOutcomeSummary(data)
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
        ? await dialogueApi.sendDynamicChat(dialogueId.value, message)
        : await dialogueApi.sendFreeText(dialogueId.value, message)
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
    selectedHero.value = null
    isSelectingHero.value = false
    pendingHeroId.value = ''
  }

  function setSelectedHero(hero: HeroPersona | null) {
    selectedHero.value = hero
  }

  function setIsSelectingHero(v: boolean) {
    isSelectingHero.value = v
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
    selectedHero,
    isSelectingHero,
    lastNpcMessage,
    startDialogue,
    startDynamicFromTopic,
    sendChoice,
    sendFreeText,
    resetDialogue,
    setSelectedHero,
    setIsSelectingHero
  }
})
