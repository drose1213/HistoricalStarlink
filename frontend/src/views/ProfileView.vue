<template>
  <div class="profile-view">
    <header class="profile-header">
      <router-link to="/" class="back-link">
        <span>←</span> {{ t('common.backToPrev') }}
      </router-link>
      <h2 class="page-title">
        <span class="title-icon">◈</span>
        {{ t('profile.pageTitle') }}
      </h2>
      <div class="header-accent"></div>
    </header>

    <main class="profile-main">
      <div class="profile-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="profile-tab"
          :class="{ active: activeTab === tab.key }"
          @click="switchTab(tab.key)"
        >
          <span class="tab-icon">{{ tab.icon }}</span>
          <span class="tab-label">{{ tab.label }}</span>
        </button>
      </div>

      <div v-if="activeTab === 'explore'" class="tab-content">
        <div class="stats-grid">
          <div class="stat-card cy-card">
            <span class="stat-value">{{ stats.totalExplorations }}</span>
            <span class="stat-label">{{ t('profile.statTotalExplorations') }}</span>
          </div>
          <div class="stat-card cy-card">
            <span class="stat-value">{{ stats.uniqueEvents }}</span>
            <span class="stat-label">{{ t('profile.statUniqueEvents') }}</span>
          </div>
          <div class="stat-card cy-card">
            <span class="stat-value">{{ stats.totalDuration }}</span>
            <span class="stat-label">{{ t('profile.statTotalDuration') }}</span>
          </div>
          <div class="stat-card cy-card">
            <span class="stat-value">{{ stats.streakDays }}</span>
            <span class="stat-label">{{ t('profile.statStreakDays') }}</span>
          </div>
        </div>

        <div class="section-block cy-card">
          <h3 class="section-title">
            <span class="section-icon">◈</span>
            {{ t('profile.timeline') }}
          </h3>
          <div v-if="loading" class="loading-state">
            <div class="cy-loading"></div>
            <p>{{ t('profile.loadingRecords') }}</p>
          </div>
          <div v-else-if="exploreTimeline.length === 0" class="empty-state">
            <div class="empty-icon">◇</div>
            <p>{{ t('profile.emptyRecords') }}</p>
            <router-link to="/" class="cy-btn cy-btn--gold">{{ t('profile.startExplore') }}</router-link>
          </div>
          <div v-else class="timeline">
            <div v-for="(item, idx) in exploreTimeline" :key="item.id" class="timeline-item">
              <div class="timeline-date">{{ item.date }}</div>
              <div class="timeline-track">
                <div class="timeline-line" v-if="idx < exploreTimeline.length - 1"></div>
                <div class="timeline-dot"></div>
              </div>
              <div class="timeline-content">
                <div class="timeline-event">{{ item.event }}</div>
                <div class="timeline-duration">{{ item.duration }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'trends'" class="tab-content">
        <div class="section-block cy-card">
          <h3 class="section-title">
            <span class="section-icon">⬡</span>
            {{ t('profile.regionDistribution') }}
          </h3>
          <div v-if="regionChinaPercent + regionForeignPercent === 0" class="empty-state">
            <p>{{ t('profile.regionEmpty') }}</p>
          </div>
          <div v-else class="region-bar-container">
            <div class="region-bar">
              <div class="region-segment region-cyan" :style="{ width: regionChinaPercent + '%' }">
                <span v-if="regionChinaPercent >= 12" class="region-segment-label">{{ t('profile.regionChina', { percent: regionChinaPercent }) }}</span>
              </div>
              <div class="region-segment region-pink" :style="{ width: regionForeignPercent + '%' }">
                <span v-if="regionForeignPercent >= 12" class="region-segment-label">{{ t('profile.regionForeign', { percent: regionForeignPercent }) }}</span>
              </div>
            </div>
            <div class="region-legend">
              <div class="legend-item">
                <span class="legend-dot legend-dot--cyan"></span>
                <span class="legend-text">{{ t('profile.regionChina', { percent: regionChinaPercent }) }}</span>
              </div>
              <div class="legend-item">
                <span class="legend-dot legend-dot--pink"></span>
                <span class="legend-text">{{ t('profile.regionForeign', { percent: regionForeignPercent }) }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="section-block cy-card">
          <h3 class="section-title">
            <span class="section-icon">◇</span>
            {{ t('profile.interestDimensions') }}
          </h3>
          <div v-if="interestDimensions.length === 0" class="empty-state">
            <p>{{ t('profile.interestEmpty') }}</p>
          </div>
          <div v-else class="dimensions-list">
            <div v-for="dim in interestDimensions" :key="dim.name" class="dimension-row">
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
            {{ t('profile.recentActivities') }}
          </h3>
          <div v-if="recentActivities.length === 0" class="empty-state">
            <p>{{ t('profile.activityEmpty') }}</p>
          </div>
          <div v-else class="activity-list">
            <div v-for="act in recentActivities" :key="act.id" class="activity-row">
              <span class="activity-dot"></span>
              <span class="activity-event">{{ act.event }}</span>
              <span class="activity-meta">{{ act.date }} · {{ act.duration }}</span>
            </div>
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'cards'" class="tab-content">
        <div v-if="loading" class="loading-state">
          <div class="cy-loading"></div>
          <p>{{ t('profile.loadingCards') }}</p>
        </div>
        <div v-else-if="myCards.length > 0" class="cards-grid">
          <div
            v-for="card in myCards"
            :key="card.id"
            class="card-item cy-card"
            :class="`card-item--${card.rarity}`"
          >
            <div class="card-header">
              <span class="card-title">{{ card.title }}</span>
              <span class="card-rarity" :class="`card-rarity--${card.rarity}`">
                {{ rarityLabels[card.rarity] }}
              </span>
            </div>
            <div class="card-event">{{ card.event }}</div>
            <div class="card-footer">
              <span class="card-date">{{ card.unlockDate }}</span>
              <span v-if="card.exploreCount > 1" class="card-count">{{ t('profile.cardExploreTimes', { n: card.exploreCount }) }}</span>
            </div>
          </div>
        </div>
        <div v-else class="cards-empty">
          <div class="empty-icon">⬡</div>
          <h3>{{ t('profile.noCards') }}</h3>
          <p>{{ t('profile.noCardsHint') }}</p>
          <router-link to="/" class="cy-btn cy-btn--gold">{{ t('profile.startExplore') }}</router-link>
        </div>
      </div>
    </main>

    <div class="cy-scanlines"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from '@/composables/useI18n'
import {
  profileApi,
  cardLevelToRarity,
  rarityLabel as rarityLabelApi,
  formatDuration as formatDurationApi,
  formatDate as formatDateApi,
  type BackendExplorationRecord,
  type BackendChampionCard,
  type ExplorationStats,
  type ChampionStats
} from '@/api/profile'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const { t } = useI18n()

type TabKey = 'explore' | 'trends' | 'cards'

const tabs = computed(() => [
  { key: 'explore' as TabKey, label: t('profile.tabs.explore'), icon: '◇' },
  { key: 'trends' as TabKey, label: t('trends.pageTitle'), icon: '◈' },
  { key: 'cards' as TabKey, label: t('profile.cardsTab'), icon: '⬡' }
])

function resolveTab(query: unknown): TabKey {
  if (query === 'trends' || query === 'cards' || query === 'explore') return query
  return 'explore'
}

const activeTab = ref<TabKey>(resolveTab(route.query.tab))

function switchTab(key: TabKey) {
  activeTab.value = key
  router.replace({ query: { ...route.query, tab: key } })
}

const loading = ref(false)
const explorationStats = ref<ExplorationStats>({
  total_records: 0,
  unique_events: 0,
  total_stay_duration: 0,
})
const championStats = ref<ChampionStats | null>(null)
const records = ref<BackendExplorationRecord[]>([])
const cards = ref<BackendChampionCard[]>([])

const stats = computed(() => ({
  totalExplorations: explorationStats.value.total_records,
  uniqueEvents: explorationStats.value.unique_events,
  totalDuration: formatDurationApi(explorationStats.value.total_stay_duration),
  streakDays: computeStreakDays(),
}))

function computeStreakDays(): string {
  if (records.value.length === 0) return t('profile.streakDaysZero')
  const days = new Set<string>()
  for (const r of records.value) {
    if (r.created_at) days.add(r.created_at.slice(0, 10))
  }
  const sortedDays = Array.from(days).sort().reverse()
  if (sortedDays.length === 0) return t('profile.streakDaysZero')

  const today = new Date()
  const todayStr = today.toISOString().slice(0, 10)
  let cursor = new Date(today)
  if (sortedDays[0] !== todayStr) {
    const yesterday = new Date(today)
    yesterday.setDate(today.getDate() - 1)
    if (sortedDays[0] !== yesterday.toISOString().slice(0, 10)) {
      return t('profile.streakDaysZero')
    }
    cursor = yesterday
  }

  let streak = 0
  for (let i = 0; i < sortedDays.length; i++) {
    const expected = cursor.toISOString().slice(0, 10)
    if (sortedDays[i] === expected) {
      streak++
      cursor.setDate(cursor.getDate() - 1)
    } else if (i === 0 && sortedDays[i] === today.toISOString().slice(0, 10)) {
      streak++
      cursor.setDate(cursor.getDate() - 1)
    } else {
      break
    }
  }
  return t('profile.streakDays', { n: streak })
}

const exploreTimeline = computed(() => {
  return records.value
    .slice(0, 10)
    .map(r => ({
      id: r.id,
      date: formatDateApi(r.created_at),
      event: r.event_name,
      duration: formatDurationApi(r.stay_duration),
    }))
})

const regionStats = computed(() => {
  let china = 0
  let foreign = 0
  for (const r of records.value) {
    if (r.event_region === 'china') china++
    else if (r.event_region === 'foreign') foreign++
  }
  const total = china + foreign
  if (total === 0) return { china: 0, foreign: 0, chinaPercent: 0, foreignPercent: 0 }
  return {
    china,
    foreign,
    chinaPercent: Math.round((china / total) * 100),
    foreignPercent: Math.round((foreign / total) * 100),
  }
})

const regionChinaPercent = computed(() => regionStats.value.chinaPercent)
const regionForeignPercent = computed(() => regionStats.value.foreignPercent)

const interestDimensions = computed(() => {
  if (records.value.length === 0) return []
  const buckets: Record<string, string[]> = {
    [t('profile.dimension.politics')]: ['改革', '统一', '革命', '帝国', '政治', '议会', '民主', '共和', '立宪', '制度'],
    [t('profile.dimension.military')]: ['军事', '征伐', '战争', '远征', '东征', '东渡', '北伐', '南征', '抗战', '十字军'],
    [t('profile.dimension.culture')]: ['文化', '宗教', '艺术', '文学', '思想', '哲学', '儒', '佛', '禅', '启蒙'],
    [t('profile.dimension.economy')]: ['经济', '贸易', '商业', '市场', '资本', '工业', '金融', '货币', '工业革命'],
    [t('profile.dimension.science')]: ['科技', '技术', '发明', '科学', '医学', '工程', '天文', '数学', '网络', '蒸汽'],
    [t('profile.dimension.society')]: ['社会', '生活', '家庭', '教育', '医疗', '人口', '城市', '建筑'],
  }
  const scores: Record<string, number> = {}
  for (const name of Object.keys(buckets)) scores[name] = 0
  const total = records.value.length
  for (const r of records.value) {
    const text = `${r.event_name}`
    let matched = false
    for (const [dim, keywords] of Object.entries(buckets)) {
      if (keywords.some(k => text.includes(k))) {
        scores[dim] = (scores[dim] || 0) + 1
        matched = true
      }
    }
    if (!matched) {
      const fallback = t('profile.dimension.politics')
      scores[fallback] = (scores[fallback] || 0) + 0.4
    }
  }
  const max = Math.max(...Object.values(scores), 1)
  return Object.entries(scores)
    .filter(([, v]) => v > 0)
    .map(([name, v]) => ({ name, value: Math.round((v / max) * 100) }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 5)
})

const recentActivities = computed(() => {
  return records.value
    .slice(0, 7)
    .map(r => ({
      id: r.id,
      event: r.event_name,
      date: formatDateApi(r.created_at),
      duration: formatDurationApi(r.stay_duration),
    }))
})

const rarityLabels: Record<string, string> = {
  legendary: t('champions.rarity.legendary'),
  epic: t('champions.rarity.epic'),
  rare: t('champions.rarity.rare'),
  common: t('champions.rarity.common'),
}

interface CardItem {
  id: number
  title: string
  event: string
  rarity: 'legendary' | 'epic' | 'rare' | 'common'
  unlockDate: string
  exploreCount: number
}

const myCards = computed<CardItem[]>(() =>
  cards.value.map(c => ({
    id: c.id,
    title: generateCardTitle(c),
    event: c.event_name,
    rarity: cardLevelToRarity(c.card_level),
    unlockDate: formatDateApi(c.created_at),
    exploreCount: c.explore_count,
  }))
)

function generateCardTitle(c: BackendChampionCard): string {
  const name = c.event_name
  if (c.card_level >= 4) return `${name}${t('profile.cardTitleSuffix.legendary')}`
  if (c.card_level >= 3) return `${name}${t('profile.cardTitleSuffix.epic')}`
  if (c.card_level >= 2) return `${name}${t('profile.cardTitleSuffix.rare')}`
  return `${name}${t('profile.cardTitleSuffix.common')}`
}

async function loadAll() {
  loading.value = true
  try {
    const [statsRes, recordsRes, cardsRes] = await Promise.all([
      profileApi.getExplorationStats(),
      profileApi.getExplorationRecords(1, 50),
      profileApi.getChampionCards(1, 100),
    ])
    if (statsRes.code === 200 && statsRes.data) {
      explorationStats.value = statsRes.data
    }
    if (recordsRes.code === 200 && recordsRes.data) {
      records.value = recordsRes.data.items
    }
    if (cardsRes.code === 200 && cardsRes.data) {
      cards.value = cardsRes.data.items
    }
  } catch (e) {
    console.warn('[ProfileView] 数据加载失败', e)
  } finally {
    loading.value = false
  }
}

watch(activeTab, (tab) => {
  if (records.value.length === 0 && !loading.value) {
    loadAll()
  }
})

onMounted(async () => {
  await authStore.init()
  if (!authStore.isLoggedIn) {
    router.push('/login')
    return
  }
  await loadAll()
})
</script>

<style scoped>
.profile-view {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.profile-header {
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

.profile-main {
  flex: 1;
  overflow-y: auto;
  padding: 20px 40px 40px;
}

.profile-tabs {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-bottom: 28px;
}

.profile-tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 24px;
  background: var(--bg-input);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
  color: var(--text-muted);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--transition-fast);
  backdrop-filter: blur(10px);
}

.profile-tab:hover {
  color: var(--cyan-core);
  border-color: var(--border-cyan);
  background: rgba(49, 247, 255, 0.08);
}

.profile-tab.active {
  color: #ffffff;
  border-color: var(--cyan-core);
  background: rgba(49, 247, 255, 0.16);
  box-shadow: var(--glow-cyan);
  text-shadow: 0 0 8px rgba(49, 247, 255, 0.5);
}

.tab-icon {
  font-size: 14px;
}

.tab-label {
  font-family: var(--font-serif);
  letter-spacing: 1px;
}

.tab-content {
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

.region-cyan {
  background: linear-gradient(90deg, rgba(49, 247, 255, 0.6), rgba(49, 247, 255, 0.35));
}

.region-pink {
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

.legend-dot--cyan {
  background: var(--cyan-core);
  box-shadow: 0 0 8px rgba(49, 247, 255, 0.6);
}

.legend-dot--pink {
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

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.activity-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(49, 247, 255, 0.04);
  transition: all var(--transition-fast);
}

.activity-row:last-child {
  border-bottom: none;
}

.activity-row:hover {
  background: rgba(49, 247, 255, 0.06);
}

.activity-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--cyan-core);
  box-shadow: 0 0 6px rgba(49, 247, 255, 0.5);
  flex-shrink: 0;
}

.activity-event {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-light);
  flex: 1;
}

.activity-meta {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
  flex-shrink: 0;
}

.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.card-item {
  padding: 20px;
  transition: all var(--transition-normal);
}

.card-item:hover {
  transform: translateY(-2px);
}

.card-item--legendary {
  border-color: var(--accent-gold);
  box-shadow: 0 0 20px rgba(212, 168, 75, 0.15);
}

.card-item--legendary:hover {
  box-shadow: 0 0 30px rgba(212, 168, 75, 0.3);
}

.card-item--epic {
  border-color: var(--pink-core);
  box-shadow: 0 0 16px rgba(255, 53, 243, 0.12);
}

.card-item--epic:hover {
  box-shadow: 0 0 24px rgba(255, 53, 243, 0.25);
}

.card-item--rare {
  border-color: var(--cyan-core);
  box-shadow: 0 0 12px rgba(49, 247, 255, 0.1);
}

.card-item--rare:hover {
  box-shadow: 0 0 20px rgba(49, 247, 255, 0.2);
}

.card-item--common {
  border-color: var(--border-subtle);
}

.card-item--common:hover {
  border-color: var(--border-cyan);
  box-shadow: 0 0 12px rgba(49, 247, 255, 0.12);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.card-title {
  font-family: var(--font-serif);
  font-size: 15px;
  font-weight: 700;
  color: #ffffff;
}

.card-rarity {
  font-size: 10px;
  padding: 3px 10px;
  border-radius: var(--radius-full);
  font-family: var(--font-mono);
  letter-spacing: 0.5px;
}

.card-rarity--legendary {
  background: rgba(212, 168, 75, 0.15);
  border: 1px solid rgba(212, 168, 75, 0.4);
  color: var(--accent-gold);
  text-shadow: 0 0 6px rgba(212, 168, 75, 0.4);
}

.card-rarity--epic {
  background: rgba(255, 53, 243, 0.12);
  border: 1px solid rgba(255, 53, 243, 0.3);
  color: var(--pink-core);
}

.card-rarity--rare {
  background: rgba(49, 247, 255, 0.1);
  border: 1px solid rgba(49, 247, 255, 0.3);
  color: var(--cyan-core);
}

.card-rarity--common {
  background: rgba(49, 247, 255, 0.04);
  border: 1px solid var(--border-subtle);
  color: var(--text-muted);
}

.card-event {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 14px;
}

.card-date {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
}

.cards-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  text-align: center;
  gap: 14px;
}

.empty-icon {
  font-size: 56px;
  color: var(--accent-gold);
  opacity: 0.3;
  text-shadow: 0 0 30px rgba(212, 168, 75, 0.4);
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  gap: 14px;
  color: var(--text-muted);
  text-align: center;
}

.cy-loading {
  width: 36px;
  height: 36px;
  border: 2px solid rgba(49, 247, 255, 0.18);
  border-top-color: var(--cyan-core);
  border-radius: 50%;
  animation: cy-spin 0.9s linear infinite;
}

@keyframes cy-spin {
  to { transform: rotate(360deg); }
}

.card-count {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--cyan-core);
  margin-left: 12px;
  padding: 2px 8px;
  background: rgba(49, 247, 255, 0.08);
  border: 1px solid rgba(49, 247, 255, 0.24);
  border-radius: var(--radius-full);
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.cards-empty h3 {
  font-family: var(--font-display);
  font-size: 20px;
  color: var(--text-light);
}

.cards-empty p {
  font-size: 13px;
  color: var(--text-muted);
}
</style>
