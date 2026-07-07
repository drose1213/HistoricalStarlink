<template>
  <div
    class="dialogue-view"
    :class="{ 'timeline-flash': dialogueStore.isTimelineAnimating }"
  >
    <header class="dlg-header">
      <button class="back-btn" @click="goBack">
        <span>←</span> {{ t('dialogue.back') }}
      </button>
      <div class="dlg-npc-info" v-if="npcInfo">
        <span class="npc-avatar">{{ npcInfo.avatar }}</span>
        <div class="npc-detail">
          <span class="npc-name">{{ npcInfo.name }}</span>
          <span class="npc-role">{{ npcInfo.role }}</span>
        </div>
      </div>
      <div class="dlg-header-right">
        <span class="dlg-round" v-if="dialogueStore.round > 0">
          {{ t('dialogue.round', { n: dialogueStore.round }) }}
        </span>
        <button
          v-if="dialogueStore.isDynamic"
          class="share-btn"
          :class="{ 'share-btn--copied': shareCopied }"
          :disabled="!canShare"
          @click="handleShare"
        >
          <span class="share-icon">{{ shareCopied ? '✓' : '↗' }}</span>
          <span class="share-label">{{ shareCopied ? shareCopiedLabel : shareLabel }}</span>
        </button>
      </div>
    </header>

    <div class="dlg-body" ref="chatContainer">
      <TransitionGroup name="msg" tag="div" class="msg-list">
        <div
          v-for="msg in dialogueStore.messages"
          :key="msg.id"
          class="msg-item"
          :class="[
            `msg-item--${msg.role}`,
            { 'msg-item--timeline-change': msg.isTimelineChange }
          ]"
        >
          <div
            v-if="msg.role === 'narrative' || msg.role === 'system'"
            class="msg-bubble msg-bubble--narrative"
          >
            <span class="msg-avatar">{{ npcInfo?.avatar || '◇' }}</span>
            <div class="msg-content-wrap">
              <div class="msg-meta">
                <span class="msg-npc-name">{{ npcInfo?.name || t('dialogue.npcFallbackName') }}</span>
                <span class="msg-mood" v-if="msg.mood">{{ msg.mood }}</span>
              </div>
              <div class="msg-text">{{ msg.content }}</div>
            </div>
          </div>

          <div v-else-if="msg.role === 'user'" class="msg-bubble msg-bubble--user">
            <div class="msg-content-wrap">
              <div class="msg-text">{{ msg.content }}</div>
            </div>
            <span class="msg-avatar msg-avatar--user">◈</span>
          </div>

          <div v-else-if="msg.role === 'choice'" class="msg-bubble msg-bubble--choice">
            <div class="msg-text">{{ msg.content }}</div>
          </div>
        </div>
      </TransitionGroup>

      <div v-if="dialogueStore.isTyping && !dialogueStore.isLoading" class="typing-indicator">
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
      </div>

      <div v-if="dialogueStore.isLoading && dialogueStore.messages.length === 0" class="dlg-loading">
        <div class="cy-loading"></div>
        <p>{{ t('dialogue.connecting') }}</p>
      </div>

      <div v-if="dialogueStore.errorMessage && !dialogueStore.isLoading" class="dlg-error">
        <div class="dlg-error-icon">◇</div>
        <h3 class="dlg-error-title">
          {{ dialogueStore.notFound ? t('dialogue.notUnlocked') : t('dialogue.startupFail') }}
        </h3>
        <p class="dlg-error-text">{{ dialogueStore.errorMessage }}</p>
        <p v-if="dialogueStore.notFound" class="dlg-error-hint">
          {{ t('dialogue.notFoundHint') }}
        </p>
        <div class="dlg-error-actions">
          <button class="cy-btn" @click="goBack">{{ t('dialogue.backPrev') }}</button>
          <button class="cy-btn cy-btn--ghost" @click="retryInit">{{ t('dialogue.retry') }}</button>
          <button
            v-if="dialogueStore.notFound"
            class="cy-btn cy-btn--glow"
            @click="goFreeExplore"
          >自由探索任意话题</button>
        </div>
      </div>
    </div>

    <div class="dlg-footer">
      <div
        v-if="dialogueStore.isDialogueEnded"
        class="outcome-panel"
      >
        <div class="outcome-divider">
          <span class="outcome-line"></span>
          <span class="outcome-label">
            {{ dialogueStore.outcomeType === 'alternate' ? t('dialogue.outcomeAlternate') : t('dialogue.outcomeCanonical') }}
          </span>
          <span class="outcome-line"></span>
        </div>
        <p class="outcome-text">{{ dialogueStore.outcomeSummary || t('dialogue.outcomeEmpty') }}</p>
        <div class="outcome-actions">
          <button class="cy-btn cy-btn--gold" @click="handleRestart">
            {{ t('dialogue.restart') }}
          </button>
          <span class="post-hint">{{ t('dialogue.postHint') }}</span>
        </div>
      </div>

      <div
        v-if="dialogueStore.choices.length > 0 && !dialogueStore.isDialogueEnded"
        class="choice-panel"
      >
        <div class="choice-label">
          <span class="choice-icon">◆</span> {{ t('dialogue.choiceLabel') }}
        </div>
        <div class="choice-list">
          <button
            v-for="choice in dialogueStore.choices"
            :key="choice.choice_id"
            class="choice-btn"
            :disabled="dialogueStore.isLoading"
            @click="handleChoice(choice.choice_id)"
          >
            <span class="choice-text">{{ choice.text }}</span>
            <span class="choice-arrow">→</span>
          </button>
        </div>
      </div>

      <div
        v-if="dialogueStore.messages.length > 0"
        class="input-bar"
      >
        <input
          ref="inputRef"
          v-model="freeText"
          class="cy-input dlg-input"
          :placeholder="dialogueStore.isDialogueEnded ? t('dialogue.placeholderEnded') : t('dialogue.placeholderActive')"
          :disabled="dialogueStore.isLoading"
          @keydown.enter="handleFreeText"
        />
        <button
          class="send-btn"
          :disabled="dialogueStore.isLoading || !freeText.trim()"
          @click="handleFreeText"
        >
          <span>▶</span>
        </button>
      </div>
    </div>

    <div class="cy-scanlines"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDialogueStore } from '@/stores/dialogue'
import { useI18n } from '@/composables/useI18n'
import { trackEvent } from '@/utils/analytics'
import { generateShareLink } from '@/utils/shareLink'

interface ToastBridge {
  showToast(type: string, message: string): void
}

interface AppWindow extends Window {
  __appStore?: ToastBridge
}

const props = defineProps<{
  eventId: string
  eventName: string
}>()

const route = useRoute()
const router = useRouter()
const dialogueStore = useDialogueStore()
const { t } = useI18n()

const chatContainer = ref<HTMLElement | null>(null)
const inputRef = ref<HTMLInputElement | null>(null)
const freeText = ref('')

// 对话起始时间 (用于计算 duration_seconds)
const dialogueStartAt = ref<number>(Date.now())
// 路径签名: 用户每个选择的 choice_id 序列, 简单拼接
const pathSignature = ref<string[]>([])

const NPC_AVATARS: Record<string, { avatar: string; key: string }> = {
  shangyang_reform: { avatar: '⚖', key: 'shangyang_reform' },
  qin_unification: { avatar: '👑', key: 'qin_unification' },
  han_empire: { avatar: '🐉', key: 'han_empire' },
  alexander_east: { avatar: '⚔', key: 'alexander_east' },
  roman_empire: { avatar: '🦅', key: 'roman_empire' },
  french_revolution: { avatar: '⚔', key: 'french_revolution' },
  industrial_revolution: { avatar: '⚙', key: 'industrial_revolution' },
}

const npcInfo = computed(() => {
  // 1) 动态对话模式: 优先用 store 里的 npc 信息 (后端返回)
  const session = dialogueStore.currentSession
  if (dialogueStore.isDynamic && session?.npc_name) {
    return {
      avatar: session.npc_symbol || '✦',
      name: session.npc_name,
      role: session.npc_role || '',
    }
  }
  // 2) 预设事件: 用 NPC_AVATARS 表查 locale key
  const entry = NPC_AVATARS[props.eventId]
  if (!entry) {
    return { avatar: '◇', name: t('dialogue.npc.fallback.name'), role: t('dialogue.npc.fallback.role') }
  }
  return { avatar: entry.avatar, name: t(`dialogue.npc.${entry.key}.name`), role: t(`dialogue.npc.${entry.key}.role`) }
})

function scrollToBottom() {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

watch(
  () => dialogueStore.messages.length,
  () => {
    scrollToBottom()
  }
)

watch(
  () => dialogueStore.isTyping,
  () => {
    scrollToBottom()
  }
)

// 对话结束 (preset 或 dynamic 都上报, 让 PMF 验证看数据差异)
watch(
  () => dialogueStore.isDialogueEnded,
  (ended) => {
    if (!ended) return
    const durationMs = Date.now() - dialogueStartAt.value
    const duration_seconds = Math.round(durationMs / 1000)
    const rounds = pathSignature.value.length
    // scores: 当前后端未在每次选择返回 scores 字段, 先传路径签名供分析
    const scores: Record<string, number> = {}
    trackEvent('dialogue_completed', {
      topic: dialogueStore.currentTopic || props.eventId,
      rounds,
      path_signature: pathSignature.value.join('>'),
      scores,
      duration_seconds,
      // 额外附加: 结局类型 & 是否 dynamic
      outcome_type: dialogueStore.outcomeType || 'historical',
      is_dynamic: dialogueStore.isDynamic,
    })
  }
)

async function handleChoice(choiceId: string) {
  // 记录路径签名 (用于 PMF 验证 dynamic vs preset 的路径差异)
  pathSignature.value.push(choiceId)
  await dialogueStore.sendChoice(choiceId)
}

async function handleFreeText() {
  const text = freeText.value.trim()
  if (!text || dialogueStore.isLoading) return
  freeText.value = ''
  // free text 也算一轮, 用 'free' 标记
  pathSignature.value.push('free')
  await dialogueStore.sendFreeText(text)
}

function handleRestart() {
  dialogueStore.resetDialogue()
  initDialogue()
}

async function initDialogue() {
  // 重置起始时间和路径
  dialogueStartAt.value = Date.now()
  pathSignature.value = []
  try {
    await dialogueStore.startDialogue(props.eventId)
  } catch (e) {
    // 错误已存入 dialogueStore.errorMessage，由模板渲染
  }
  scrollToBottom()
}

function retryInit() {
  initDialogue()
}

function goBack() {
  router.back()
}

// ===== 分享给朋友 =====
const shareCopied = ref(false)
let shareCopiedTimer: number | null = null

const currentTopic = computed(() => dialogueStore.currentTopic || '')
const canShare = computed(() => !!currentTopic.value.trim())
const shareLabel = computed(() => t('dialogue.share'))
const shareCopiedLabel = computed(() => t('dialogue.shareCopied'))

function flashShareCopied() {
  shareCopied.value = true
  if (shareCopiedTimer !== null) {
    window.clearTimeout(shareCopiedTimer)
  }
  shareCopiedTimer = window.setTimeout(() => {
    shareCopied.value = false
    shareCopiedTimer = null
  }, 1800)
}

/**
 * 复制到剪贴板的兜底实现：
 * - 优先用 navigator.clipboard（仅 HTTPS / localhost）
 * - 不可用时用临时 textarea + execCommand('copy')
 * - 两者都失败则弹出 prompt 让用户手动复制
 */
async function copyToClipboard(text: string): Promise<boolean> {
  // 1) 现代化 API
  try {
    if (typeof navigator !== 'undefined' && navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text)
      return true
    }
  } catch (_) {
    // 继续 fallback
  }
  // 2) execCommand fallback
  try {
    const ta = document.createElement('textarea')
    ta.value = text
    ta.setAttribute('readonly', '')
    ta.style.position = 'fixed'
    ta.style.top = '-9999px'
    ta.style.opacity = '0'
    document.body.appendChild(ta)
    ta.select()
    ta.setSelectionRange(0, text.length)
    const ok = document.execCommand('copy')
    document.body.removeChild(ta)
    return ok
  } catch (_) {
    return false
  }
}

async function handleShare() {
  const topic = currentTopic.value.trim()
  if (!topic) return
  const url = generateShareLink(topic)

  const ok = await copyToClipboard(url)
  if (ok) {
    flashShareCopied()
    try {
      const app = (window as AppWindow).__appStore
      // 静默尝试触发现有 toast，若不可用则跳过
      if (app && typeof app.showToast === 'function') {
        app.showToast('success', shareCopiedLabel.value)
      }
    } catch (_) {
      // 忽略
    }
  } else {
    // 3) 最后的兜底：弹出 prompt 让用户手动复制
    window.prompt(t('dialogue.shareManualCopy'), url)
  }
  trackEvent('dialogue_share_clicked', {
    topic,
    is_dynamic: true,
    copy_success: ok,
  })
}

onBeforeUnmount(() => {
  if (shareCopiedTimer !== null) {
    window.clearTimeout(shareCopiedTimer)
    shareCopiedTimer = null
  }
})

function goFreeExplore() {
  // 清掉错误状态, 跳到 HomeView 让 user 自由输入 topic
  dialogueStore.resetDialogue()
  router.push({ name: 'Home' })
}

onMounted(() => {
  if (!dialogueStore.messages.length) {
    initDialogue()
  }
})
</script>

<style scoped>
.dialogue-view {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
  background:
    radial-gradient(ellipse at 50% 0%, rgba(49, 247, 255, 0.06), transparent 60%),
    radial-gradient(ellipse at 80% 100%, rgba(255, 53, 243, 0.04), transparent 50%),
    var(--bg-primary);
}

.dialogue-view.timeline-flash {
  animation: timelineFlash 1.2s ease;
}

@keyframes timelineFlash {
  0% { background-color: var(--bg-primary); }
  15% { background-color: rgba(49, 247, 255, 0.12); }
  30% { background-color: var(--bg-primary); }
  45% { background-color: rgba(255, 53, 243, 0.10); }
  60% { background-color: var(--bg-primary); }
  75% { background-color: rgba(212, 168, 75, 0.08); }
  100% { background-color: var(--bg-primary); }
}

.dlg-header {
  padding: 12px 22px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(180deg, rgba(4, 8, 15, 0.96), rgba(4, 8, 15, 0.72));
  border-bottom: 1px solid var(--border-subtle);
  z-index: var(--z-header);
  gap: 16px;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  padding: 5px 14px;
  background: transparent;
  border: 1px solid var(--border-cyan);
  border-radius: var(--radius-full);
  color: var(--cyan-core);
  transition: all 0.2s;
  flex-shrink: 0;
}

.back-btn:hover {
  background: rgba(49, 247, 255, 0.12);
  box-shadow: 0 0 12px rgba(49, 247, 255, 0.3);
}

.dlg-npc-info {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  justify-content: center;
}

.npc-avatar {
  width: 38px;
  height: 38px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  border-radius: 50%;
  background: rgba(49, 247, 255, 0.12);
  border: 1px solid var(--border-cyan);
  box-shadow: 0 0 12px rgba(49, 247, 255, 0.25);
  flex-shrink: 0;
}

.npc-detail {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.npc-name {
  font-family: var(--font-serif);
  font-size: 14px;
  font-weight: 700;
  color: var(--cyan-core);
  text-shadow: 0 0 10px rgba(49, 247, 255, 0.4);
}

.npc-role {
  font-size: 11px;
  color: var(--text-muted);
  font-family: var(--font-mono);
}

.dlg-header-right {
  flex-shrink: 0;
  min-width: 80px;
  text-align: right;
  display: flex;
  align-items: center;
  gap: 8px;
}

.dlg-round {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--accent-gold);
  padding: 3px 10px;
  border: 1px solid rgba(212, 168, 75, 0.3);
  border-radius: var(--radius-full);
  background: rgba(212, 168, 75, 0.1);
}

.share-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  padding: 4px 12px;
  background: rgba(255, 53, 243, 0.08);
  border: 1px solid var(--border-pink);
  border-radius: var(--radius-full);
  color: var(--pink-core);
  font-family: var(--font-mono);
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.share-btn:hover:not(:disabled) {
  background: rgba(255, 53, 243, 0.18);
  box-shadow: 0 0 12px rgba(255, 53, 243, 0.35);
  transform: translateY(-1px);
}

.share-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.share-btn--copied {
  background: rgba(212, 168, 75, 0.18);
  border-color: var(--accent-gold);
  color: var(--accent-gold);
  box-shadow: 0 0 12px rgba(212, 168, 75, 0.4);
}

.share-icon {
  font-size: 13px;
  line-height: 1;
}

.share-label {
  font-size: 12px;
  letter-spacing: 0.05em;
}

.dlg-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.msg-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.msg-enter-active {
  transition: all 0.4s ease;
}

.msg-enter-from {
  opacity: 0;
  transform: translateY(16px);
}

.msg-item {
  display: flex;
  width: 100%;
}

.msg-item--narrative {
  justify-content: flex-start;
}

.msg-item--user {
  justify-content: flex-end;
}

.msg-item--choice {
  justify-content: center;
}

.msg-item--timeline-change .msg-bubble {
  animation: msgTimelineGlow 1.2s ease;
}

@keyframes msgTimelineGlow {
  0% { box-shadow: none; }
  30% { box-shadow: 0 0 20px rgba(212, 168, 75, 0.6), 0 0 40px rgba(212, 168, 75, 0.3); border-color: var(--accent-gold); }
  100% { box-shadow: none; }
}

.msg-bubble {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  max-width: 72%;
}

.msg-bubble--narrative {
  background: rgba(49, 247, 255, 0.06);
  border: 1px solid var(--border-cyan);
  border-radius: 2px var(--radius-md) var(--radius-md) var(--radius-md);
  padding: 12px 16px;
}

.msg-bubble--user {
  background: rgba(255, 53, 243, 0.06);
  border: 1px solid var(--border-pink);
  border-radius: var(--radius-md) 2px var(--radius-md) var(--radius-md);
  padding: 12px 16px;
}

.msg-bubble--choice {
  background: rgba(212, 168, 75, 0.08);
  border: 1px solid rgba(212, 168, 75, 0.3);
  border-radius: var(--radius-full);
  padding: 8px 20px;
  font-size: 12px;
  color: var(--accent-gold);
  max-width: 80%;
}

.msg-avatar {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  border-radius: 50%;
  background: rgba(49, 247, 255, 0.1);
  border: 1px solid var(--border-cyan);
  flex-shrink: 0;
}

.msg-avatar--user {
  background: rgba(255, 53, 243, 0.1);
  border-color: var(--border-pink);
  color: var(--pink-core);
}

.msg-content-wrap {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.msg-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.msg-npc-name {
  font-size: 12px;
  font-weight: 600;
  color: var(--cyan-core);
  font-family: var(--font-serif);
}

.msg-mood {
  font-size: 10px;
  color: var(--text-muted);
  font-family: var(--font-mono);
}

.msg-text {
  font-size: 14px;
  line-height: 1.8;
  color: var(--text-light);
  word-break: break-word;
}

.msg-text::after {
  content: '▌';
  animation: cursorBlink 0.8s step-end infinite;
  color: var(--cyan-core);
  margin-left: 1px;
  opacity: 0;
}

.msg-item:last-child .msg-text::after {
  opacity: 1;
}

@keyframes cursorBlink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.typing-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  align-self: flex-start;
}

.typing-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--cyan-core);
  animation: typingBounce 1.2s infinite;
}

.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes typingBounce {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-6px); opacity: 1; }
}

.dlg-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  flex: 1;
  min-height: 200px;
}

.dlg-error {
  margin: 32px 24px;
  padding: 28px 24px;
  border: 1px dashed var(--border-cyan);
  border-radius: var(--radius-md);
  background: var(--bg-card);
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.dlg-error-icon {
  font-size: 36px;
  color: var(--accent-gold);
  text-shadow: 0 0 12px rgba(212, 168, 75, 0.5);
  letter-spacing: 0.3em;
}

.dlg-error-title {
  font-size: 17px;
  color: var(--cyan-core);
  font-weight: 500;
  letter-spacing: 0.1em;
}

.dlg-error-text {
  font-size: 13px;
  color: var(--text-light);
  opacity: 0.85;
}

.dlg-error-hint {
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.7;
  max-width: 460px;
  margin: 0 auto;
}

.dlg-error-actions {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}

.dlg-loading p {
  font-size: 13px;
  color: var(--text-muted);
  font-family: var(--font-mono);
}

.dlg-footer {
  padding: 0 20px 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.choice-panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
}

.choice-label {
  font-size: 12px;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  gap: 6px;
}

.choice-icon {
  color: var(--accent-gold);
  font-size: 10px;
}

.choice-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.choice-btn {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--bg-input);
  border: 1px solid var(--border-cyan);
  border-radius: var(--radius-sm);
  color: var(--text-light);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.25s ease;
  position: relative;
  overflow: hidden;
}

.choice-btn::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(49, 247, 255, 0.1), rgba(255, 53, 243, 0.1));
  opacity: 0;
  transition: opacity 0.25s;
}

.choice-btn:hover {
  border-color: var(--cyan-core);
  box-shadow: 0 0 16px rgba(49, 247, 255, 0.35), 0 0 32px rgba(49, 247, 255, 0.15);
  transform: translateX(4px);
}

.choice-btn:hover::before {
  opacity: 1;
}

.choice-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.choice-btn:disabled::before {
  display: none;
}

.choice-text {
  position: relative;
  z-index: 1;
}

.choice-arrow {
  color: var(--cyan-core);
  opacity: 0;
  transform: translateX(-4px);
  transition: all 0.25s ease;
  position: relative;
  z-index: 1;
}

.choice-btn:hover .choice-arrow {
  opacity: 1;
  transform: translateX(0);
}

.outcome-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  padding: 20px 16px;
  background: var(--bg-card);
  border: 1px solid rgba(212, 168, 75, 0.3);
  border-radius: var(--radius-md);
  animation: outcomeAppear 0.8s ease;
}

@keyframes outcomeAppear {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

.outcome-divider {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.outcome-line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--accent-gold), transparent);
  opacity: 0.4;
}

.outcome-label {
  font-family: var(--font-serif);
  font-size: 14px;
  color: var(--accent-gold);
  white-space: nowrap;
  text-shadow: 0 0 10px rgba(212, 168, 75, 0.4);
}

.outcome-text {
  font-size: 13px;
  color: var(--text-muted);
  line-height: 1.8;
  text-align: center;
}

.outcome-actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.post-hint {
  font-size: 11px;
  color: var(--text-muted);
  font-family: var(--font-mono);
  opacity: 0.7;
}

.input-bar {
  display: flex;
  gap: 10px;
  align-items: center;
}

.dlg-input {
  flex: 1;
}

.send-btn {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(49, 247, 255, 0.12);
  border: 1px solid var(--border-cyan);
  border-radius: 50%;
  color: var(--cyan-core);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}

.send-btn:hover:not(:disabled) {
  background: rgba(49, 247, 255, 0.25);
  box-shadow: 0 0 14px rgba(49, 247, 255, 0.4);
}

.send-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

@media (max-width: 700px) {
  .msg-bubble {
    max-width: 88%;
  }

  .dlg-header {
    padding: 10px 14px;
  }

  .npc-role {
    display: none;
  }
}
</style>
