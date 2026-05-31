<template>
  <div class="profile-view">
    <header class="profile-header">
      <router-link to="/" class="back-link">
        <span>←</span> 返回首页
      </router-link>
      <h2 class="page-title">
        <span class="title-icon">◈</span>
        个人中心
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
            <span class="stat-label">总探索次数</span>
          </div>
          <div class="stat-card cy-card">
            <span class="stat-value">{{ stats.uniqueEvents }}</span>
            <span class="stat-label">涉及事件</span>
          </div>
          <div class="stat-card cy-card">
            <span class="stat-value">{{ stats.totalDuration }}</span>
            <span class="stat-label">累计时长</span>
          </div>
          <div class="stat-card cy-card">
            <span class="stat-value">{{ stats.streakDays }}</span>
            <span class="stat-label">连续探索</span>
          </div>
        </div>

        <div class="section-block cy-card">
          <h3 class="section-title">
            <span class="section-icon">◈</span>
            探索时间线
          </h3>
          <div class="timeline">
            <div v-for="(item, idx) in exploreTimeline" :key="idx" class="timeline-item">
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
            区域分布
          </h3>
          <div class="region-bar-container">
            <div class="region-bar">
              <div class="region-segment region-cyan" :style="{ width: '60%' }">
                <span class="region-segment-label">东方 60%</span>
              </div>
              <div class="region-segment region-pink" :style="{ width: '40%' }">
                <span class="region-segment-label">西方 40%</span>
              </div>
            </div>
            <div class="region-legend">
              <div class="legend-item">
                <span class="legend-dot legend-dot--cyan"></span>
                <span class="legend-text">东方 60%</span>
              </div>
              <div class="legend-item">
                <span class="legend-dot legend-dot--pink"></span>
                <span class="legend-text">西方 40%</span>
              </div>
            </div>
          </div>
        </div>

        <div class="section-block cy-card">
          <h3 class="section-title">
            <span class="section-icon">◇</span>
            兴趣维度
          </h3>
          <div class="dimensions-list">
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
            近期活动
          </h3>
          <div class="activity-list">
            <div v-for="(act, idx) in recentActivities" :key="idx" class="activity-row">
              <span class="activity-dot"></span>
              <span class="activity-event">{{ act.event }}</span>
              <span class="activity-meta">{{ act.date }} · {{ act.duration }}</span>
            </div>
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'cards'" class="tab-content">
        <div v-if="myCards.length > 0" class="cards-grid">
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
            </div>
          </div>
        </div>
        <div v-else class="cards-empty">
          <div class="empty-icon">⬡</div>
          <h3>暂无卡牌</h3>
          <p>探索历史事件可解锁冠军卡牌</p>
          <router-link to="/" class="cy-btn cy-btn--gold">开始探索</router-link>
        </div>
      </div>
    </main>

    <div class="cy-scanlines"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

type TabKey = 'explore' | 'trends' | 'cards'

const tabs = [
  { key: 'explore' as TabKey, label: '探索记录', icon: '◇' },
  { key: 'trends' as TabKey, label: '趋势分析', icon: '◈' },
  { key: 'cards' as TabKey, label: '我的卡牌', icon: '⬡' }
]

function resolveTab(query: unknown): TabKey {
  if (query === 'trends' || query === 'cards' || query === 'explore') return query
  return 'explore'
}

const activeTab = ref<TabKey>(resolveTab(route.query.tab))

function switchTab(key: TabKey) {
  activeTab.value = key
  router.replace({ query: { ...route.query, tab: key } })
}

const stats = ref({
  totalExplorations: 42,
  uniqueEvents: 7,
  totalDuration: '5h 23m',
  streakDays: '3天'
})

const exploreTimeline = ref([
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

const interestDimensions = ref([
  { name: '政治变革', value: 85 },
  { name: '军事征伐', value: 70 },
  { name: '文化交流', value: 55 },
  { name: '经济发展', value: 45 },
  { name: '科技进步', value: 65 }
])

const recentActivities = ref([
  { event: '商鞅变法', date: '2026-05-28', duration: '32min' },
  { event: '秦始皇统一六国', date: '2026-05-26', duration: '45min' },
  { event: '大汉帝国建立', date: '2026-05-24', duration: '28min' },
  { event: '亚历山大东征', date: '2026-05-22', duration: '37min' },
  { event: '罗马帝国建立', date: '2026-05-20', duration: '41min' },
  { event: '法国大革命', date: '2026-05-18', duration: '52min' },
  { event: '工业革命', date: '2026-05-15', duration: '38min' }
])

interface CardItem {
  id: number
  title: string
  event: string
  rarity: 'legendary' | 'epic' | 'rare' | 'common'
  unlockDate: string
}

const rarityLabels: Record<string, string> = {
  legendary: '传说',
  epic: '史诗',
  rare: '稀有',
  common: '普通'
}

const myCards = ref<CardItem[]>([
  { id: 1, title: '秦始皇·天下归一', event: '秦始皇统一六国', rarity: 'legendary', unlockDate: '2026-05-20' },
  { id: 2, title: '商鞅·变法图强', event: '商鞅变法', rarity: 'epic', unlockDate: '2026-05-18' },
  { id: 3, title: '凯撒·帝国之鹰', event: '罗马帝国建立', rarity: 'epic', unlockDate: '2026-05-15' },
  { id: 4, title: '汉武帝·开疆拓土', event: '大汉帝国建立', rarity: 'rare', unlockDate: '2026-05-12' },
  { id: 5, title: '亚历山大·远征号角', event: '亚历山大东征', rarity: 'rare', unlockDate: '2026-05-10' },
  { id: 6, title: '瓦特·蒸汽先驱', event: '工业革命', rarity: 'common', unlockDate: '2026-05-08' }
])

onMounted(async () => {
  await authStore.init()
  if (!authStore.isLoggedIn) {
    router.push('/login')
  }
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

.card-footer {
  display: flex;
  justify-content: flex-end;
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
