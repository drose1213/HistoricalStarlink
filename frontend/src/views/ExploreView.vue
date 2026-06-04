<template>
  <div class="explore-view">
    <header class="explore-header">
      <router-link to="/" class="back-link">
        <span>←</span> {{ t('common.backToPrev') }}
      </router-link>
      <h2 class="page-title">
        <span class="title-icon">◈</span>
        {{ t('explore.pageTitle') }}
      </h2>
      <div></div>
    </header>

    <main class="explore-main">
      <div class="explore-stats" v-if="stats">
        <div class="stat-card cy-card">
          <span class="stat-value">{{ stats.total_explorations || 0 }}</span>
          <span class="stat-label">{{ t('explore.statTotalExplorations') }}</span>
        </div>
        <div class="stat-card cy-card">
          <span class="stat-value">{{ stats.unique_events || 0 }}</span>
          <span class="stat-label">{{ t('explore.statUniqueEvents') }}</span>
        </div>
        <div class="stat-card cy-card">
          <span class="stat-value">{{ formatDuration(Number(stats.total_duration) || 0) }}</span>
          <span class="stat-label">{{ t('explore.statTotalDuration') }}</span>
        </div>
      </div>

      <div class="records-section">
        <h3 class="section-title">{{ t('explore.history') }}</h3>
        <div class="records-list" v-if="records.length > 0">
          <div v-for="record in records" :key="record.id" class="record-item cy-card">
            <div class="record-main">
              <div class="record-event">{{ record.event_id }}</div>
              <div class="record-meta">
                <span class="record-duration">{{ formatDuration(record.duration_seconds) }}</span>
                <span class="record-depth">{{ t('explore.depth', { n: record.path_depth }) }}</span>
              </div>
            </div>
            <div class="record-time">{{ formatTime(record.explored_at) }}</div>
          </div>
        </div>
        <div class="records-empty" v-else>
          <div class="empty-icon">◇</div>
          <p>{{ t('explore.empty') }}</p>
          <router-link to="/" class="cy-btn">{{ t('explore.start') }}</router-link>
        </div>
      </div>

      <div class="signature-section">
        <SignatureUpload />
      </div>
    </main>

    <div class="cy-scanlines"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useExplorationStore } from '@/stores/exploration'
import { useI18n } from '@/composables/useI18n'
import SignatureUpload from '@/components/SignatureUpload.vue'
import type { ExplorationRecord } from '@/types'

const { t } = useI18n()
const explorationStore = useExplorationStore()

const records = ref<ExplorationRecord[]>([])
const stats = ref<Record<string, unknown>>({})

function formatDuration(seconds: number): string {
  if (!seconds) return '00:00'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  if (h > 0) return `${h}h ${m}m`
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

function formatTime(dateStr: string): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, '0')}-${d.getDate().toString().padStart(2, '0')} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
}

onMounted(async () => {
  try {
    const data = await explorationStore.fetchRecords()
    records.value = data?.items || []
  } catch {
    records.value = []
  }
  try {
    stats.value = await explorationStore.fetchStats()
  } catch {
    stats.value = {}
  }
})
</script>

<style scoped>
.explore-view {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.explore-header {
  padding: 12px 22px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(180deg, rgba(4, 8, 15, 0.96), rgba(4, 8, 15, 0.72));
  border-bottom: 1px solid var(--border-subtle);
  z-index: var(--z-header);
  gap: 16px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.back-link {
  font-size: 13px;
  color: var(--cyan-core);
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 14px;
  border: 1px solid var(--border-cyan);
  border-radius: var(--radius-full);
  transition: all 0.2s;
}

.back-link:hover {
  background: rgba(49, 247, 255, 0.12);
  box-shadow: 0 0 12px rgba(49, 247, 255, 0.3);
}

.page-title {
  font-family: var(--font-serif);
  font-size: 18px;
  font-weight: 700;
  color: var(--cyan-core);
  text-shadow: 0 0 14px var(--cyan-core);
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-icon {
  font-size: 14px;
}

.explore-main {
  flex: 1;
  overflow-y: auto;
  padding: 24px 40px;
  display: flex;
  flex-direction: column;
  gap: 28px;
}

.explore-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.stat-card {
  padding: 24px;
  text-align: center;
}

.stat-value {
  display: block;
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 700;
  color: var(--cyan-core);
  text-shadow: 0 0 16px rgba(49, 247, 255, 0.5);
  margin-bottom: 6px;
}

.stat-label {
  font-size: 12px;
  color: var(--text-muted);
  letter-spacing: 1px;
}

.section-title {
  font-family: var(--font-serif);
  font-size: 16px;
  font-weight: 700;
  color: var(--cyan-core);
  text-shadow: 0 0 10px var(--cyan-core);
  margin-bottom: 14px;
}

.records-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.record-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
}

.record-event {
  font-size: 14px;
  color: var(--text-light);
  font-weight: 600;
  margin-bottom: 4px;
}

.record-meta {
  display: flex;
  gap: 12px;
}

.record-duration {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--cyan-core);
}

.record-depth {
  font-size: 12px;
  color: var(--text-muted);
}

.record-time {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
}

.records-empty {
  text-align: center;
  padding: 48px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.empty-icon {
  font-size: 40px;
  color: var(--cyan-core);
  opacity: 0.4;
  text-shadow: 0 0 20px var(--cyan-core);
}

.records-empty p {
  font-size: 13px;
  color: var(--text-muted);
}
</style>
