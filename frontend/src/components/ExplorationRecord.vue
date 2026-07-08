<template>
  <div class="exploration-record">
    <div class="exploration-header">
      <h3 class="cy-subtitle">
        <span class="header-icon">◈</span>
        {{ t('exploration.title') }}
      </h3>
      <span class="cy-badge cy-badge--cyan" v-if="isActive && !isPaused">
        {{ t('exploration.active', { time: formatDuration(elapsedTime) }) }}
      </span>
      <span class="cy-badge cy-badge--amber" v-else-if="isPaused">
        {{ t('exploration.paused', { time: formatDuration(elapsedTime) }) }}
      </span>
    </div>

    <div class="exploration-body">
      <div class="record-info" v-if="currentRecord">
        <div class="info-row">
          <span class="info-label">{{ t('exploration.recordId') }}</span>
          <span class="info-value">#{{ currentRecord.id }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">{{ t('exploration.event') }}</span>
          <span class="info-value">{{ getExplorationTitle(currentRecord) || eventId }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">{{ t('exploration.pathDepth') }}</span>
          <span class="info-value">{{ t('exploration.pathDepthValue', { n: getExplorationDepth(currentRecord) }) }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">{{ t('exploration.duration') }}</span>
          <span class="info-value">{{ formatDuration(elapsedTime) }}</span>
        </div>
        <div class="info-row info-row--notes" v-if="getExplorationNotes(currentRecord)">
          <span class="info-label">{{ t('exploration.notes') }}</span>
          <span class="info-value info-value--notes">{{ getExplorationNotes(currentRecord) }}</span>
        </div>
      </div>

      <div class="record-empty" v-else>
        <div class="empty-icon">◇</div>
        <p>{{ t('exploration.notStarted') }}</p>
        <p class="empty-hint">{{ t('exploration.startHint') }}</p>
      </div>
    </div>

    <div class="exploration-footer" v-if="showControls">
      <button
        v-if="!isActive"
        class="cy-btn"
        :disabled="!eventId"
        @click="handleStart"
      >
        {{ t('exploration.start') }}
      </button>
      <template v-else>
        <button
          v-if="!isPaused"
          class="cy-btn cy-btn--ghost"
          @click="handlePause"
        >
          {{ t('exploration.pause') }}
        </button>
        <button
          v-else
          class="cy-btn"
          @click="handleResume"
        >
          {{ t('exploration.resume') }}
        </button>
        <button
          class="cy-btn cy-btn--pink"
          @click="handleEnd"
        >
          {{ t('exploration.end') }}
        </button>
      </template>
    </div>

    <div class="history-section" v-if="exploreHistory.length > 0">
      <div class="cy-divider"></div>
      <h4 class="history-title">{{ t('exploration.historyTitle') }}</h4>
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
import { useI18n } from '@/composables/useI18n'
import { getExplorationDepth, getExplorationNotes, getExplorationTitle } from '@/utils/explorationRecord'

const props = defineProps<{
  eventId?: string
  eventName?: string
  showControls?: boolean
}>()

const explorationStore = useExplorationStore()
const appStore = useAppStore()
const { t } = useI18n()

const elapsedTime = ref(0)
const isPaused = ref(false)
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
  isPaused.value = false
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

function handlePause() {
  if (!isActive.value || isPaused.value) return
  stopTimer()
  isPaused.value = true
  appStore.showToast('warning', t('toast.explorePaused'))
}

function handleResume() {
  if (!isActive.value || !isPaused.value) return
  isPaused.value = false
  timer = setInterval(() => {
    elapsedTime.value++
  }, 1000)
  appStore.showToast('success', t('toast.exploreResumed'))
}

async function handleStart() {
  if (!requireAuth()) return
  if (!props.eventId) return
  try {
    await explorationStore.startExploration(props.eventId, props.eventName)
    startTimer()
    appStore.showToast('success', t('toast.exploreStart'))
  } catch {
    appStore.showToast('error', t('toast.exploreStartFail'))
  }
}

async function handleEnd() {
  if (!currentRecord.value) return
  // 结束前若仍在暂停, 不需要重开定时器, 直接停掉以防泄漏
  stopTimer()
  isPaused.value = false
  try {
      await explorationStore.endExploration(
        currentRecord.value.id,
        elapsedTime.value,
        getExplorationDepth(currentRecord.value)
      )
    appStore.showToast('success', t('toast.exploreEnd', { duration: formatDuration(elapsedTime.value) }))
  } catch {
    appStore.showToast('error', t('toast.exploreEndFail'))
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

.info-row--notes {
  align-items: flex-start;
  gap: 12px;
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

.info-value--notes {
  max-width: 64%;
  white-space: normal;
  text-align: right;
  line-height: 1.5;
  overflow-wrap: anywhere;
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
