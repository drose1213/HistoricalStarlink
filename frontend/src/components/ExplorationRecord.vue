<template>
  <div class="exploration-record">
    <div class="exploration-header">
      <h3 class="cy-subtitle">
        <span class="header-icon">◈</span>
        探索记录
      </h3>
      <span class="cy-badge cy-badge--cyan" v-if="isActive">
        探索中 · {{ formatDuration(elapsedTime) }}
      </span>
    </div>

    <div class="exploration-body">
      <div class="record-info" v-if="currentRecord">
        <div class="info-row">
          <span class="info-label">记录ID</span>
          <span class="info-value">#{{ currentRecord.id }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">事件</span>
          <span class="info-value">{{ eventId }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">路径深度</span>
          <span class="info-value">{{ currentRecord.path_depth }} 层</span>
        </div>
        <div class="info-row">
          <span class="info-label">探索时长</span>
          <span class="info-value">{{ formatDuration(currentRecord.duration_seconds) }}</span>
        </div>
      </div>

      <div class="record-empty" v-else>
        <div class="empty-icon">◇</div>
        <p>尚未开始探索</p>
        <p class="empty-hint">点击事件节点开始探索旅程</p>
      </div>
    </div>

    <div class="exploration-footer" v-if="showControls">
      <button
        v-if="!isActive"
        class="cy-btn"
        :disabled="!eventId"
        @click="handleStart"
      >
        开始探索
      </button>
      <button
        v-else
        class="cy-btn cy-btn--pink"
        @click="handleEnd"
      >
        结束探索
      </button>
    </div>

    <div class="history-section" v-if="exploreHistory.length > 0">
      <div class="cy-divider"></div>
      <h4 class="history-title">探索历程</h4>
      <div class="history-list">
        <div
          v-for="(eid, idx) in exploreHistory"
          :key="eid"
          class="history-item"
        >
          <span class="history-index">{{ String(idx + 1).padStart(2, '0') }}</span>
          <span class="history-dot"></span>
          <span class="history-event">{{ eid }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onBeforeUnmount } from 'vue'
import { useExplorationStore } from '@/stores/exploration'
import { useAppStore } from '@/stores/app'
import { requireAuth } from '@/utils/auth'

const props = defineProps<{
  eventId?: string
  eventName?: string
  showControls?: boolean
}>()

const explorationStore = useExplorationStore()
const appStore = useAppStore()

const elapsedTime = ref(0)
let timer: ReturnType<typeof setInterval> | null = null

const currentRecord = computed(() => explorationStore.currentRecord)
const isActive = computed(() => currentRecord.value !== null)
const exploreHistory = computed(() => explorationStore.exploreHistory)

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

function startTimer() {
  elapsedTime.value = 0
  timer = setInterval(() => {
    elapsedTime.value++
  }, 1000)
}

function stopTimer() {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

async function handleStart() {
  if (!requireAuth()) return
  if (!props.eventId) return
  try {
    await explorationStore.startExploration(props.eventId, props.eventName)
    startTimer()
    appStore.showToast('success', '探索已开始')
  } catch {
    appStore.showToast('error', '开始探索失败')
  }
}

async function handleEnd() {
  if (!currentRecord.value) return
  stopTimer()
  try {
    await explorationStore.endExploration(
      currentRecord.value.id,
      elapsedTime.value,
      currentRecord.value.path_depth
    )
    appStore.showToast('success', `探索结束，共用时 ${formatDuration(elapsedTime.value)}`)
  } catch {
    appStore.showToast('error', '结束探索失败')
  }
}

onBeforeUnmount(() => {
  stopTimer()
})
</script>

<style scoped>
.exploration-record {
  padding: 20px;
  background: var(--bg-card);
  border: 1px solid var(--border-cyan);
  border-radius: var(--radius-md);
  backdrop-filter: blur(10px);
}

.exploration-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.exploration-header h3 {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-icon {
  color: var(--cyan-core);
  text-shadow: 0 0 10px var(--cyan-core);
  font-size: 18px;
}

.record-info {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px;
  background: var(--bg-input);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-subtle);
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-label {
  font-size: 12px;
  color: var(--text-muted);
  letter-spacing: 0.5px;
}

.info-value {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--cyan-core);
  text-shadow: 0 0 6px rgba(49, 247, 255, 0.4);
}

.record-empty {
  text-align: center;
  padding: 32px 16px;
  color: var(--text-muted);
}

.empty-icon {
  font-size: 32px;
  color: var(--cyan-core);
  text-shadow: 0 0 20px var(--cyan-core);
  margin-bottom: 12px;
  opacity: 0.5;
}

.empty-hint {
  font-size: 11px;
  margin-top: 6px;
  opacity: 0.6;
}

.exploration-footer {
  margin-top: 16px;
  display: flex;
  justify-content: center;
  gap: 12px;
}

.exploration-footer button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.history-section {
  margin-top: 8px;
}

.history-title {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 12px;
  letter-spacing: 1px;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 200px;
  overflow-y: auto;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 10px;
  border-radius: var(--radius-sm);
  background: var(--bg-input);
  font-size: 12px;
}

.history-index {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-muted);
  min-width: 20px;
}

.history-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--cyan-core);
  box-shadow: 0 0 6px var(--cyan-core);
}

.history-event {
  color: var(--text-light);
  font-size: 12px;
}
</style>
