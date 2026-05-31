<template>
  <div
    class="dialogue-view"
    :class="{ 'timeline-flash': dialogueStore.isTimelineAnimating }"
  >
    <header class="dlg-header">
      <button class="back-btn" @click="goBack">
        <span>←</span> 返回
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
          第 {{ dialogueStore.round }} 轮
        </span>
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
                <span class="msg-npc-name">{{ npcInfo?.name || '时空之声' }}</span>
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
        <p>正在连接时空隧道...</p>
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
            {{ dialogueStore.outcomeType === 'alternate' ? '◇ 平行时间线' : '◆ 历史定论' }}
          </span>
          <span class="outcome-line"></span>
        </div>
        <p class="outcome-text">{{ dialogueStore.outcomeSummary || '这段时空对话已经结束。' }}</p>
        <div class="outcome-actions">
          <button class="cy-btn cy-btn--gold" @click="handleRestart">
            重新探索
          </button>
          <span class="post-hint">💡 你还可以继续输入，与历史人物进行「后日谈」</span>
        </div>
      </div>

      <div
        v-if="dialogueStore.choices.length > 0 && !dialogueStore.isDialogueEnded"
        class="choice-panel"
      >
        <div class="choice-label">
          <span class="choice-icon">◆</span> 做出你的选择
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
          :placeholder="dialogueStore.isDialogueEnded ? '与历史人物进行后日谈...' : '自由输入你的想法...'"
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
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDialogueStore } from '@/stores/dialogue'

const props = defineProps<{
  eventId: string
  eventName: string
}>()

const route = useRoute()
const router = useRouter()
const dialogueStore = useDialogueStore()

const chatContainer = ref<HTMLElement | null>(null)
const inputRef = ref<HTMLInputElement | null>(null)
const freeText = ref('')

const NPC_AVATARS: Record<string, { avatar: string; name: string; role: string }> = {
  shangyang_reform: { avatar: '⚖', name: '商鞅', role: '秦国大良造 · 变法者' },
  qin_unification: { avatar: '👑', name: '秦始皇', role: '始皇帝 · 天下共主' },
  han_empire: { avatar: '🐉', name: '刘邦', role: '汉高祖 · 布衣天子' },
  alexander_east: { avatar: '⚔', name: '亚历山大', role: '马其顿之王 · 东方征服者' },
  roman_empire: { avatar: '🦅', name: '屋大维', role: '奥古斯都 · 罗马帝皇' },
  french_revolution: { avatar: '⚔', name: '一位巴黎市民', role: '革命参与者' },
  industrial_revolution: { avatar: '⚙', name: '詹姆斯·瓦特', role: '发明家 · 蒸汽机之父' },
}

const npcInfo = computed(() => {
  return NPC_AVATARS[props.eventId] || { avatar: '◇', name: '时空旅人', role: '历史见证者' }
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

async function handleChoice(choiceId: string) {
  await dialogueStore.sendChoice(choiceId)
}

async function handleFreeText() {
  const text = freeText.value.trim()
  if (!text || dialogueStore.isLoading) return
  freeText.value = ''
  await dialogueStore.sendFreeText(text)
}

function handleRestart() {
  dialogueStore.resetDialogue()
  initDialogue()
}

async function initDialogue() {
  await dialogueStore.startDialogue(props.eventId)
  scrollToBottom()
}

function goBack() {
  router.back()
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
