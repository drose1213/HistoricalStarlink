<template>
  <div class="leaderboard-view">
    <header class="lb-header">
      <router-link to="/" class="back-link">
        <span>←</span> {{ t('common.backToPrev') }}
      </router-link>
      <h2 class="page-title">
        <span class="title-icon">◈</span>
        {{ t('leaderboard.pageTitle') }}
      </h2>
      <div class="header-accent"></div>
    </header>

    <main class="lb-main">
      <div class="period-tabs">
        <button
          v-for="tab in periodTabs"
          :key="tab.value"
          class="period-tab"
          :class="{ active: activePeriod === tab.value }"
          @click="activePeriod = tab.value"
        >
          <span class="tab-icon">{{ tab.icon }}</span>
          <span class="tab-label">{{ tab.label }}</span>
        </button>
      </div>

      <div v-if="loading" class="loading-state">
        <div class="loading-icon">⬡</div>
        <p class="loading-text">{{ t('leaderboard.loading') }}</p>
      </div>

      <div v-else-if="loadError" class="empty-card empty-card--error">
        <div class="empty-icon">⚠</div>
        <p class="empty-title">{{ t('leaderboard.loadError') }}</p>
        <p class="empty-hint">{{ loadError }}</p>
        <button class="retry-btn" @click="loadLeaderboard(activePeriod)">{{ t('common.retry') }}</button>
      </div>

      <div v-else-if="ranking.length === 0" class="empty-card">
        <div class="empty-icon">⬡</div>
        <p class="empty-title">{{ t('leaderboard.empty') }}</p>
        <p class="empty-hint">{{ t('leaderboard.emptyHint') }}</p>
      </div>

      <div v-else class="podium-section">
        <div class="podium-bg-glow"></div>
        <h3 class="section-title">
          <span class="section-icon">⬡</span>
          {{ t('leaderboard.topExplorers') }}
        </h3>
        <div class="podium">
          <div class="podium-item podium-item--second">
            <div class="podium-avatar">
              <span class="avatar-initial">{{ topThree[1]?.name.charAt(0) }}</span>
              <span class="podium-medal">🥈</span>
            </div>
            <div class="podium-name">{{ topThree[1]?.name }}</div>
            <div class="podium-count">{{ t('leaderboard.exploreTimes', { count: topThree[1]?.exploreCount ?? 0 }) }}</div>
            <div class="podium-pedestal">
              <div class="pedestal-face">2</div>
            </div>
          </div>
          <div class="podium-item podium-item--first">
            <div class="podium-crown">✦</div>
            <div class="podium-avatar podium-avatar--gold">
              <span class="avatar-initial">{{ topThree[0]?.name.charAt(0) }}</span>
              <span class="podium-medal">🥇</span>
            </div>
            <div class="podium-name">{{ topThree[0]?.name }}</div>
            <div class="podium-count">{{ t('leaderboard.exploreTimes', { count: topThree[0]?.exploreCount ?? 0 }) }}</div>
            <div class="podium-pedestal podium-pedestal--gold">
              <div class="pedestal-face">1</div>
            </div>
          </div>
          <div class="podium-item podium-item--third">
            <div class="podium-avatar">
              <span class="avatar-initial">{{ topThree[2]?.name.charAt(0) }}</span>
              <span class="podium-medal">🥉</span>
            </div>
            <div class="podium-name">{{ topThree[2]?.name }}</div>
            <div class="podium-count">{{ t('leaderboard.exploreTimes', { count: topThree[2]?.exploreCount ?? 0 }) }}</div>
            <div class="podium-pedestal">
              <div class="pedestal-face">3</div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="ranking.length > 0" class="ranking-table">
        <div class="table-header">
          <h3 class="section-title">
            <span class="section-icon">◇</span>
            {{ t('leaderboard.fullRank') }}
          </h3>
          <div class="table-meta">
            {{ t('leaderboard.totalExplorers', { count: currentRanking.length }) }}
          </div>
        </div>
        <div class="table-columns">
          <span class="col-rank">{{ t('leaderboard.colRank') }}</span>
          <span class="col-name">{{ t('leaderboard.colName') }}</span>
          <span class="col-count">{{ t('leaderboard.colCount') }}</span>
          <span class="col-duration">{{ t('leaderboard.colDuration') }}</span>
          <span class="col-fav">{{ t('leaderboard.colFav') }}</span>
        </div>
        <TransitionGroup name="row-slide" tag="div" class="table-body">
          <div
            v-for="(explorer, index) in currentRanking"
            :key="explorer.id"
            class="table-row"
            :class="{
              'table-row--gold': index === 0,
              'table-row--silver': index === 1,
              'table-row--bronze': index === 2
            }"
          >
            <span class="col-rank">
              <span v-if="index < 3" class="rank-medal">
                {{ index === 0 ? '🥇' : index === 1 ? '🥈' : '🥉' }}
              </span>
              <span v-else class="rank-num">{{ index + 1 }}</span>
            </span>
            <span class="col-name">
              <span class="explorer-avatar" :style="{ background: avatarGradient(explorer.name) }">
                {{ explorer.name.charAt(0) }}
              </span>
              <span class="explorer-name-text">{{ explorer.name }}</span>
            </span>
            <span class="col-count">
              <span class="count-value">{{ explorer.exploreCount }}</span>
              <span class="count-unit">{{ t('leaderboard.unit') }}</span>
            </span>
            <span class="col-duration">
              <span class="duration-value">{{ formatDuration(explorer.totalDuration) }}</span>
            </span>
            <span class="col-fav">
              <span class="fav-badge">{{ explorer.favoriteEvent }}</span>
            </span>
          </div>
        </TransitionGroup>
      </div>

      <div class="champion-events">
        <h3 class="section-title">
          <span class="section-icon">◈</span>
          {{ t('leaderboard.championEvents') }} · {{ periodLabel }}
        </h3>
        <div v-if="!loading && championEvents.length === 0 && !loadError" class="empty-inline">
          <span class="empty-inline-text">{{ t('leaderboard.noChampionEvents') }}</span>
        </div>
        <div v-else-if="!loading" class="champion-grid">
          <div
            v-for="(event, idx) in championEvents"
            :key="event.name"
            class="champion-card"
            :class="{ 'champion-card--highlight': idx === 0 }"
          >
            <div class="champion-rank">{{ idx + 1 }}</div>
            <div class="champion-info">
              <div class="champion-name">{{ event.name }}</div>
              <div class="champion-bar-wrap">
                <div
                  class="champion-bar"
                  :style="{ width: event.barWidth + '%' }"
                ></div>
              </div>
            </div>
            <div class="champion-count">{{ t('leaderboard.exploreTimes', { count: event.exploreCount }) }}</div>
          </div>
        </div>
      </div>
    </main>

    <div class="cy-scanlines"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { leaderboardApi, type Explorer, type ChampionEvent } from '@/api/leaderboard'
import { useI18n } from '@/composables/useI18n'

const { t } = useI18n()

const periodTabs = computed(() => [
  { value: 'daily' as const, label: t('leaderboard.period.daily'), icon: '◇' },
  { value: 'weekly' as const, label: t('leaderboard.period.weekly'), icon: '◈' },
  { value: 'monthly' as const, label: t('leaderboard.period.monthly'), icon: '⬡' },
  { value: 'yearly' as const, label: t('leaderboard.period.yearly'), icon: '✦' }
])

type Period = 'daily' | 'weekly' | 'monthly' | 'yearly'

const activePeriod = ref<Period>('weekly')
const ranking = ref<Explorer[]>([])
const championEventsRaw = ref<ChampionEvent[]>([])
const loading = ref(false)
const loadError = ref<string | null>(null)

async function loadLeaderboard(period: Period) {
  loading.value = true
  loadError.value = null
  try {
    const res = await leaderboardApi.get(period, 10)
    ranking.value = res.data?.ranking || []
    championEventsRaw.value = res.data?.championEvents || []
  } catch (e: unknown) {
    loadError.value = e instanceof Error ? e.message : t('leaderboard.networkError')
    ranking.value = []
    championEventsRaw.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => loadLeaderboard(activePeriod.value))
watch(activePeriod, (p) => loadLeaderboard(p))

const periodLabel = computed(() => {
  const labels: Record<Period, string> = {
    daily: t('leaderboard.period.daily'),
    weekly: t('leaderboard.period.weekly'),
    monthly: t('leaderboard.period.monthly'),
    yearly: t('leaderboard.period.yearly')
  }
  return labels[activePeriod.value]
})

const currentRanking = computed(() => ranking.value)
const topThree = computed(() => currentRanking.value.slice(0, 3))

const championEvents = computed(() => {
  const events = championEventsRaw.value
  const maxCount = events[0]?.exploreCount || 1
  return events.map(e => ({
    ...e,
    barWidth: Math.round((e.exploreCount / maxCount) * 100)
  }))
})

function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  if (hours >= 1000) {
    return t('leaderboard.duration.k', { n: (hours / 1000).toFixed(1) })
  }
  if (hours > 0) {
    return t('leaderboard.duration.h', { h: hours, m: minutes })
  }
  return t('leaderboard.duration.m', { m: minutes })
}

function avatarGradient(name: string): string {
  // 基于用户名 hash 派生稳定且独特的渐变色, 同一用户名始终同一颜色
  const palettes: Array<[string, string]> = [
    ['rgba(212, 168, 75, 0.6)', 'rgba(255, 200, 100, 0.3)'],   // 金色
    ['rgba(49, 247, 255, 0.4)', 'rgba(255, 53, 243, 0.2)'],    // 青-粉
    ['rgba(255, 53, 243, 0.35)', 'rgba(49, 247, 255, 0.2)'],   // 粉-青
    ['rgba(49, 247, 255, 0.25)', 'rgba(142, 164, 184, 0.15)'], // 青-灰
    ['rgba(255, 152, 71, 0.4)', 'rgba(255, 53, 243, 0.2)'],    // 橙-粉
    ['rgba(120, 220, 168, 0.4)', 'rgba(49, 247, 255, 0.2)'],   // 绿-青
    ['rgba(186, 132, 255, 0.4)', 'rgba(255, 53, 243, 0.2)'],   // 紫-粉
    ['rgba(212, 168, 75, 0.4)', 'rgba(49, 247, 255, 0.2)'],    // 金-青
  ]
  let hash = 0
  for (let i = 0; i < name.length; i++) {
    hash = (hash * 31 + name.charCodeAt(i)) >>> 0
  }
  const [c1, c2] = palettes[hash % palettes.length]
  return `linear-gradient(135deg, ${c1}, ${c2})`
}
</script>

<style scoped>
.leaderboard-view {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.lb-header {
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

.lb-main {
  flex: 1;
  overflow-y: auto;
  padding: 20px 40px 40px;
}

.period-tabs {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-bottom: 28px;
}

.period-tab {
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

.period-tab:hover {
  color: var(--cyan-core);
  border-color: var(--border-cyan);
  background: rgba(49, 247, 255, 0.08);
}

.period-tab.active {
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

.podium-section {
  position: relative;
  margin-bottom: 32px;
  padding: 28px 32px 20px;
  background: var(--bg-card);
  border: 1px solid var(--border-cyan);
  border-radius: var(--radius-md);
  backdrop-filter: blur(10px);
  overflow: hidden;
}

.podium-bg-glow {
  position: absolute;
  top: -60px;
  left: 50%;
  transform: translateX(-50%);
  width: 400px;
  height: 200px;
  background: radial-gradient(ellipse, rgba(212, 168, 75, 0.15), transparent 70%);
  pointer-events: none;
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
  position: relative;
}

.section-icon {
  font-size: 14px;
}

.podium {
  display: flex;
  justify-content: center;
  align-items: flex-end;
  gap: 20px;
  position: relative;
}

.podium-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  animation: podium-rise 0.8s ease backwards;
}

.podium-item--first {
  order: 2;
  animation-delay: 0.2s;
}

.podium-item--second {
  order: 1;
  animation-delay: 0.4s;
}

.podium-item--third {
  order: 3;
  animation-delay: 0.6s;
}

@keyframes podium-rise {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.podium-crown {
  font-size: 20px;
  color: var(--accent-gold);
  text-shadow: 0 0 16px rgba(212, 168, 75, 0.8);
  animation: crown-pulse 2s ease-in-out infinite;
}

@keyframes crown-pulse {
  0%, 100% { opacity: 0.8; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.15); }
}

.podium-avatar {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(49, 247, 255, 0.3), rgba(255, 53, 243, 0.15));
  border: 2px solid var(--border-cyan);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  box-shadow: 0 0 20px rgba(49, 247, 255, 0.25);
}

.podium-avatar--gold {
  width: 68px;
  height: 68px;
  background: linear-gradient(135deg, rgba(212, 168, 75, 0.4), rgba(255, 200, 100, 0.2));
  border-color: var(--accent-gold);
  box-shadow: 0 0 24px rgba(212, 168, 75, 0.4);
}

.avatar-initial {
  font-size: 20px;
  font-weight: 700;
  color: #ffffff;
  text-shadow: 0 0 8px rgba(255, 255, 255, 0.3);
}

.podium-avatar--gold .avatar-initial {
  font-size: 24px;
}

.podium-medal {
  position: absolute;
  bottom: -6px;
  right: -6px;
  font-size: 18px;
  filter: drop-shadow(0 0 4px rgba(0, 0, 0, 0.6));
}

.podium-name {
  font-family: var(--font-serif);
  font-size: 14px;
  font-weight: 700;
  color: #ffffff;
}

.podium-count {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
}

.podium-pedestal {
  width: 80px;
  height: 48px;
  background: linear-gradient(180deg, rgba(49, 247, 255, 0.12), rgba(49, 247, 255, 0.04));
  border: 1px solid var(--border-cyan);
  border-bottom: none;
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.podium-pedestal--gold {
  height: 64px;
  background: linear-gradient(180deg, rgba(212, 168, 75, 0.2), rgba(212, 168, 75, 0.06));
  border-color: rgba(212, 168, 75, 0.4);
}

.podium-item--second .podium-pedestal {
  height: 40px;
}

.podium-item--third .podium-pedestal {
  height: 32px;
}

.pedestal-face {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 900;
  color: rgba(49, 247, 255, 0.2);
}

.podium-pedestal--gold .pedestal-face {
  color: rgba(212, 168, 75, 0.25);
}

.ranking-table {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  backdrop-filter: blur(10px);
  margin-bottom: 32px;
  overflow: hidden;
}

.table-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid var(--border-subtle);
}

.table-header .section-title {
  margin-bottom: 0;
}

.table-meta {
  font-size: 12px;
  font-family: var(--font-mono);
  color: var(--text-muted);
}

.table-columns {
  display: grid;
  grid-template-columns: 60px 1fr 100px 120px 140px;
  padding: 10px 24px;
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
  grid-template-columns: 60px 1fr 100px 120px 140px;
  padding: 12px 24px;
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

.table-row--gold {
  background: rgba(212, 168, 75, 0.06);
  border-left: 2px solid var(--accent-gold);
}

.table-row--silver {
  background: rgba(192, 192, 192, 0.04);
  border-left: 2px solid rgba(192, 192, 192, 0.4);
}

.table-row--bronze {
  background: rgba(205, 127, 50, 0.04);
  border-left: 2px solid rgba(205, 127, 50, 0.4);
}

.col-rank {
  text-align: center;
}

.rank-medal {
  font-size: 18px;
}

.rank-num {
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 700;
  color: var(--text-muted);
}

.col-name {
  display: flex;
  align-items: center;
  gap: 10px;
}

.explorer-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid var(--border-cyan);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  color: #ffffff;
  flex-shrink: 0;
}

.explorer-name-text {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-light);
}

.col-count {
  text-align: center;
}

.count-value {
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 700;
  color: var(--cyan-core);
}

.count-unit {
  font-size: 11px;
  color: var(--text-muted);
  margin-left: 2px;
}

.col-duration {
  text-align: center;
}

.duration-value {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-light);
}

.col-fav {
  text-align: center;
}

.fav-badge {
  display: inline-block;
  font-size: 11px;
  padding: 3px 10px;
  background: rgba(49, 247, 255, 0.08);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
  color: var(--text-muted);
}

.row-slide-enter-active {
  transition: all 0.4s ease;
}

.row-slide-leave-active {
  transition: all 0.3s ease;
}

.row-slide-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.row-slide-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

.champion-events {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  backdrop-filter: blur(10px);
  padding: 20px 24px;
}

.champion-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.champion-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 18px;
  background: var(--bg-input);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}

.champion-card:hover {
  border-color: var(--border-cyan);
  background: rgba(49, 247, 255, 0.06);
}

.champion-card--highlight {
  border-color: var(--accent-gold);
  background: rgba(212, 168, 75, 0.06);
}

.champion-card--highlight:hover {
  border-color: var(--accent-gold);
  background: rgba(212, 168, 75, 0.1);
  box-shadow: 0 0 18px rgba(212, 168, 75, 0.2);
}

.champion-rank {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 900;
  color: var(--cyan-core);
  border: 1px solid var(--border-cyan);
  border-radius: var(--radius-sm);
  flex-shrink: 0;
}

.champion-card--highlight .champion-rank {
  color: var(--accent-gold);
  border-color: var(--accent-gold);
  text-shadow: 0 0 8px rgba(212, 168, 75, 0.5);
}

.champion-info {
  flex: 1;
  min-width: 0;
}

.champion-name {
  font-family: var(--font-serif);
  font-size: 14px;
  font-weight: 700;
  color: #ffffff;
  margin-bottom: 8px;
}

.champion-bar-wrap {
  width: 100%;
  height: 4px;
  background: rgba(49, 247, 255, 0.08);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.champion-bar {
  height: 100%;
  background: linear-gradient(90deg, var(--cyan-core), var(--pink-core));
  border-radius: var(--radius-full);
  transition: width 0.6s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 0 8px rgba(49, 247, 255, 0.4);
}

.champion-card--highlight .champion-bar {
  background: linear-gradient(90deg, var(--accent-gold), var(--cyan-core));
  box-shadow: 0 0 8px rgba(212, 168, 75, 0.4);
}

.champion-count {
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 700;
  color: var(--cyan-core);
  white-space: nowrap;
  flex-shrink: 0;
}

.champion-card--highlight .champion-count {
  color: var(--accent-gold);
  text-shadow: 0 0 8px rgba(212, 168, 75, 0.5);
}

/* Loading / Empty / Error states */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  gap: 12px;
}

.loading-icon {
  font-size: 48px;
  color: var(--cyan-core);
  opacity: 0.5;
  animation: pulse 1.4s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.3; transform: scale(1); }
  50% { opacity: 0.8; transform: scale(1.08); }
}

.loading-text {
  font-family: var(--font-mono);
  font-size: 14px;
  color: var(--text-muted);
}

.empty-card {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 60px 20px;
  margin-bottom: 32px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  backdrop-filter: blur(10px);
}

.empty-card--error {
  border-color: rgba(255, 138, 77, 0.4);
  background: linear-gradient(180deg, rgba(255, 138, 77, 0.06), var(--bg-card));
}

.empty-icon {
  font-size: 48px;
  color: var(--text-muted);
  opacity: 0.4;
}

.empty-card--error .empty-icon { color: #ff8a4d; opacity: 0.7; }

.empty-title {
  font-family: var(--font-serif);
  font-size: 18px;
  font-weight: 700;
  color: var(--text-light);
}

.empty-card--error .empty-title { color: #ffba6b; }

.empty-hint {
  font-size: 13px;
  color: var(--text-muted);
}

.retry-btn {
  margin-top: 6px;
  padding: 8px 22px;
  background: rgba(49, 247, 255, 0.12);
  border: 1px solid var(--border-cyan);
  border-radius: var(--radius-full);
  color: var(--cyan-core);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.retry-btn:hover {
  background: rgba(49, 247, 255, 0.2);
  box-shadow: var(--glow-cyan);
}

.empty-inline {
  padding: 32px 20px;
  text-align: center;
  background: rgba(49, 247, 255, 0.04);
  border: 1px dashed var(--border-subtle);
  border-radius: var(--radius-sm);
}

.empty-inline-text {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--text-muted);
}
</style>
