<template>
  <div class="trends-view">
    <header class="trends-header">
      <router-link to="/" class="back-link">
        <span>←</span> {{ t('common.backToPrev') }}
      </router-link>
      <h2 class="page-title">
        <span class="title-icon">◈</span>
        {{ t('trends.pageTitle') }}
      </h2>
      <div class="header-accent"></div>
    </header>

    <main class="trends-main">
      <div class="stats-grid">
        <div class="stat-card cy-card">
          <span class="stat-value">{{ totalExplorations }}</span>
          <span class="stat-label">{{ t('trends.statTotalExplorations') }}</span>
        </div>
        <div class="stat-card cy-card">
          <span class="stat-value">{{ uniqueEvents }}</span>
          <span class="stat-label">{{ t('trends.statUniqueEvents') }}</span>
        </div>
        <div class="stat-card cy-card">
          <span class="stat-value">{{ totalDuration }}</span>
          <span class="stat-label">{{ t('trends.statTotalDuration') }}</span>
        </div>
        <div class="stat-card cy-card">
          <span class="stat-value">{{ streakDays }}</span>
          <span class="stat-label">{{ t('trends.statStreakDays') }}</span>
        </div>
      </div>

      <div class="section-block cy-card">
        <h3 class="section-title">
          <span class="section-icon">⬡</span>
          {{ t('trends.regionDistribution') }}
        </h3>
        <div class="region-bar-container">
          <div class="region-bar">
            <div class="region-segment region-china" :style="{ width: chinaRatio + '%' }">
              <span class="region-segment-label" v-if="chinaRatio > 20">{{ t('trends.regionChina') }} {{ chinaRatio }}%</span>
            </div>
            <div class="region-segment region-foreign" :style="{ width: foreignRatio + '%' }">
              <span class="region-segment-label" v-if="foreignRatio > 20">{{ t('trends.regionForeign') }} {{ foreignRatio }}%</span>
            </div>
          </div>
          <div class="region-legend">
            <div class="legend-item">
              <span class="legend-dot legend-dot--china"></span>
              <span class="legend-text">{{ t('trends.regionChinaFull', { n: chinaRatio }) }}</span>
            </div>
            <div class="legend-item">
              <span class="legend-dot legend-dot--foreign"></span>
              <span class="legend-text">{{ t('trends.regionForeignFull', { n: foreignRatio }) }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="section-block cy-card">
        <h3 class="section-title">
          <span class="section-icon">◇</span>
          {{ t('trends.interestDimensions') }}
        </h3>
        <div class="dimensions-list">
          <div v-for="dim in dimensions" :key="dim.name" class="dimension-row">
            <span class="dimension-name">{{ dim.name }}</span>
            <div class="dimension-bar-wrap">
              <div class="dimension-bar" :style="{ width: dim.value + '%' }"></div>
            </div>
            <span class="dimension-value">{{ dim.value }}%</span>
          </div>
        </div>
      </div>

      <div class="section-block cy-card">
        <h3 class="section-title">
          <span class="section-icon">◈</span>
          {{ t('trends.timeline') }}
        </h3>
        <div class="timeline">
          <div v-for="(item, idx) in timelineItems" :key="idx" class="timeline-item">
            <div class="timeline-date">{{ item.date }}</div>
            <div class="timeline-track">
              <div class="timeline-line" v-if="idx < timelineItems.length - 1"></div>
              <div class="timeline-dot"></div>
            </div>
            <div class="timeline-content">
              <div class="timeline-event">{{ item.event }}</div>
              <div class="timeline-duration">{{ item.duration }}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="section-block cy-card">
        <h3 class="section-title">
          <span class="section-icon">⬡</span>
          {{ t('trends.recentActivities') }}
        </h3>
        <div class="activity-table">
          <div class="table-columns">
            <span class="col-event">{{ t('trends.colEvent') }}</span>
            <span class="col-date">{{ t('trends.colDate') }}</span>
            <span class="col-duration">{{ t('trends.colDuration') }}</span>
            <span class="col-depth">{{ t('trends.colDepth') }}</span>
          </div>
          <div class="table-body">
            <div
              v-for="(row, idx) in activityRows"
              :key="idx"
              class="table-row"
            >
              <span class="col-event">
                <span class="event-badge">{{ row.event }}</span>
              </span>
              <span class="col-date">{{ row.date }}</span>
              <span class="col-duration">
                <span class="duration-value">{{ row.duration }}</span>
              </span>
              <span class="col-depth">
                <span class="depth-badge">{{ t('trends.dimDepth', { n: row.depth }) }}</span>
              </span>
            </div>
          </div>
        </div>
      </div>
    </main>

    <div class="cy-scanlines"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from '@/composables/useI18n'

const { t } = useI18n()

const totalExplorations = ref(42)
const uniqueEvents = ref(7)
const totalDuration = ref('5h 23m')
const streakDays = ref('3天')

const chinaRatio = ref(60)
const foreignRatio = computed(() => 100 - chinaRatio.value)

const dimensions = ref([
  { name: t('profile.dimension.politics'), value: 85 },
  { name: t('profile.dimension.military'), value: 70 },
  { name: t('profile.dimension.culture'), value: 55 },
  { name: t('profile.dimension.economy'), value: 45 },
  { name: t('profile.dimension.science'), value: 65 }
])

const timelineItems = ref([
  { date: '2026-05-28', event: '商鞅变法', duration: '32min' },
  { date: '2026-05-26', event: '秦始皇统一六国', duration: '45min' },
  { date: '2026-05-24', event: '大汉帝国建立', duration: '28min' },
  { date: '2026-05-22', event: '亚历山大东征', duration: '37min' },
  { date: '2026-05-20', event: '罗马帝国建立', duration: '41min' },
  { date: '2026-05-18', event: '法国大革命', duration: '52min' },
  { date: '2026-05-15', event: '工业革命', duration: '38min' },
  { date: '2026-05-13', event: '商鞅变法', duration: '27min' },
  { date: '2026-05-11', event: '大汉帝国建立', duration: '33min' },
  { date: '2026-05-08', event: '法国大革命', duration: '29min' }
])

const activityRows = ref([
  { event: '商鞅变法', date: '2026-05-28', duration: '32min', depth: 3 },
  { event: '秦始皇统一六国', date: '2026-05-26', duration: '45min', depth: 4 },
  { event: '大汉帝国建立', date: '2026-05-24', duration: '28min', depth: 2 },
  { event: '亚历山大东征', date: '2026-05-22', duration: '37min', depth: 3 },
  { event: '罗马帝国建立', date: '2026-05-20', duration: '41min', depth: 5 },
  { event: '法国大革命', date: '2026-05-18', duration: '52min', depth: 4 },
  { event: '工业革命', date: '2026-05-15', duration: '38min', depth: 3 }
])
</script>

<style scoped>
.trends-view {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.trends-header {
  padding: 12px 22px;
  display: flex;
  align-items: center;
  background: linear-gradient(180deg, rgba(4, 8, 15, 0.96), rgba(4, 8, 15, 0.72));
  border-bottom: 1px solid var(--border-subtle);
  z-index: var(--z-header);
  gap: 16px;
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
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.back-link:hover {
  background: rgba(49, 247, 255, 0.12);
  box-shadow: 0 0 12px rgba(49, 247, 255, 0.3);
}

.page-title {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 700;
  color: var(--accent-gold);
  text-shadow: 0 0 14px rgba(212, 168, 75, 0.5);
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-icon {
  font-size: 20px;
}

.header-accent {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, var(--border-cyan), transparent);
  margin-left: 8px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.trends-main {
  flex: 1;
  overflow-y: auto;
  padding: 20px 40px 40px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-card {
  padding: 24px 16px;
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

.section-block {
  padding: 24px;
}

.section-title {
  font-family: var(--font-serif);
  font-size: 16px;
  font-weight: 700;
  color: var(--cyan-core);
  text-shadow: 0 0 10px var(--cyan-core);
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
}

.section-icon {
  font-size: 14px;
}

.region-bar-container {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.region-bar {
  display: flex;
  width: 100%;
  height: 32px;
  border-radius: var(--radius-full);
  overflow: hidden;
  border: 1px solid var(--border-subtle);
}

.region-segment {
  display: flex;
  align-items: center;
  justify-content: center;
  transition: width var(--transition-normal);
}

.region-china {
  background: linear-gradient(90deg, rgba(49, 247, 255, 0.6), rgba(49, 247, 255, 0.35));
}

.region-foreign {
  background: linear-gradient(90deg, rgba(255, 53, 243, 0.35), rgba(255, 53, 243, 0.6));
}

.region-segment-label {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 700;
  color: #fff;
  text-shadow: 0 0 8px rgba(0, 0, 0, 0.6);
  letter-spacing: 0.5px;
}

.region-legend {
  display: flex;
  gap: 24px;
  justify-content: center;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.legend-dot--china {
  background: var(--cyan-core);
  box-shadow: 0 0 8px rgba(49, 247, 255, 0.6);
}

.legend-dot--foreign {
  background: var(--pink-core);
  box-shadow: 0 0 8px rgba(255, 53, 243, 0.6);
}

.legend-text {
  font-size: 12px;
  color: var(--text-muted);
  font-family: var(--font-mono);
}

.dimensions-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.dimension-row {
  display: flex;
  align-items: center;
  gap: 14px;
}

.dimension-name {
  width: 72px;
  flex-shrink: 0;
  font-size: 13px;
  font-family: var(--font-serif);
  color: var(--text-light);
  text-align: right;
}

.dimension-bar-wrap {
  flex: 1;
  height: 8px;
  background: rgba(49, 247, 255, 0.08);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.dimension-bar {
  height: 100%;
  background: linear-gradient(90deg, rgba(49, 247, 255, 0.7), rgba(49, 247, 255, 0.3));
  border-radius: var(--radius-full);
  box-shadow: 0 0 8px rgba(49, 247, 255, 0.3);
  transition: width 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}

.dimension-value {
  width: 40px;
  flex-shrink: 0;
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 700;
  color: var(--cyan-core);
  text-align: right;
}

.timeline {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.timeline-item {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  min-height: 56px;
}

.timeline-date {
  width: 90px;
  flex-shrink: 0;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
  text-align: right;
  padding-top: 2px;
}

.timeline-track {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  width: 20px;
  flex-shrink: 0;
}

.timeline-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--cyan-core);
  box-shadow: 0 0 10px rgba(49, 247, 255, 0.6);
  border: 2px solid rgba(49, 247, 255, 0.3);
  position: relative;
  z-index: 2;
  margin-top: 3px;
}

.timeline-line {
  position: absolute;
  top: 16px;
  left: 50%;
  transform: translateX(-50%);
  width: 1px;
  height: calc(100% + 24px);
  background: linear-gradient(180deg, var(--border-cyan), var(--border-subtle));
  z-index: 1;
}

.timeline-content {
  flex: 1;
  padding-bottom: 16px;
  padding-top: 1px;
}

.timeline-event {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-light);
  margin-bottom: 2px;
}

.timeline-duration {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
}

.activity-table {
  overflow: hidden;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-subtle);
}

.table-columns {
  display: grid;
  grid-template-columns: 1fr 120px 100px 80px;
  padding: 10px 20px;
  background: rgba(49, 247, 255, 0.04);
  border-bottom: 1px solid var(--border-subtle);
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--text-muted);
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.table-body {
  position: relative;
}

.table-row {
  display: grid;
  grid-template-columns: 1fr 120px 100px 80px;
  padding: 12px 20px;
  align-items: center;
  border-bottom: 1px solid rgba(49, 247, 255, 0.04);
  transition: all var(--transition-fast);
}

.table-row:last-child {
  border-bottom: none;
}

.table-row:hover {
  background: rgba(49, 247, 255, 0.06);
}

.event-badge {
  display: inline-block;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-light);
}

.col-date {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-muted);
  text-align: center;
}

.col-duration {
  text-align: center;
}

.duration-value {
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 700;
  color: var(--cyan-core);
}

.col-depth {
  text-align: center;
}

.depth-badge {
  display: inline-block;
  font-size: 11px;
  padding: 2px 10px;
  background: rgba(49, 247, 255, 0.08);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
  color: var(--text-muted);
  font-family: var(--font-mono);
}
</style>
