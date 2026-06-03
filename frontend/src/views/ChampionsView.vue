<template>
  <div class="champions-gallery">
    <header class="gallery-header">
      <router-link to="/" class="back-link">
        <span class="back-arrow">←</span>
        返回首页
      </router-link>
      <div class="header-titles">
        <h1 class="gallery-title">冠军展馆</h1>
        <p class="gallery-subtitle">全服探索者 · 稀有度殿堂</p>
      </div>
      <div class="header-decoration"></div>
    </header>

    <div class="tab-bar">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="tab-btn"
        :class="{ active: activeTab === tab.key, [`tab-btn--${tab.key}`]: activeTab === tab.key }"
        @click="activeTab = tab.key"
      >
        <span class="tab-icon">{{ tab.icon }}</span>
        <span class="tab-label">{{ tab.label }}</span>
        <span class="tab-count">{{ tab.count }}</span>
      </button>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="loading-icon">⬡</div>
      <p class="loading-text">正在加载卡牌数据…</p>
    </div>

    <div v-else-if="loadError" class="error-state">
      <div class="error-icon">⚠</div>
      <p class="error-text">{{ loadError }}</p>
      <button class="retry-btn" @click="loadCards">重试</button>
    </div>

    <div v-else-if="!hasAnyCard" class="empty-state empty-state--full">
      <div class="empty-icon">⬡</div>
      <p class="empty-text">暂无卡牌</p>
      <p class="empty-hint">去首页探索事件以解锁卡牌</p>
      <router-link to="/" class="empty-cta">前往首页探索 →</router-link>
    </div>

    <main v-else class="gallery-main">
      <Transition name="tab-switch" mode="out-in">
        <div :key="activeTab" class="card-grid">
          <div
            v-for="(card, idx) in currentCards"
            :key="card.id"
            class="champion-card"
            :class="[`champion-card--${activeTab}`, { 'champion-card--top': idx === 0 }]"
            @click="openDetail(card)"
          >
            <div class="card-rank-badge" v-if="idx < 3">
              {{ ['🥇','🥈','🥉'][idx] }}
            </div>
            <div class="card-inner">
              <div class="card-glow-layer"></div>
              <div class="card-head">
                <span class="card-rarity-tag" :class="`tag--${activeTab}`">{{ currentTab.label }}</span>
                <span class="card-score">{{ card.score }}分</span>
              </div>
              <h3 class="card-title">{{ card.title }}</h3>
              <p class="card-event-name">{{ card.event }}</p>
              <div class="card-divider" :class="`divider--${activeTab}`"></div>
              <div class="card-info-row">
                <div class="card-owner-block">
                  <div class="owner-avatar" :class="`avatar--${activeTab}`">
                    {{ card.owner.charAt(0) }}
                  </div>
                  <div class="owner-text">
                    <span class="owner-name">{{ card.owner }}</span>
                    <span class="owner-date">{{ card.date }}</span>
                  </div>
                </div>
              </div>
              <div class="card-footer">
                <span class="footer-hint">点击查看详情 →</span>
              </div>
            </div>
          </div>

          <div v-if="currentCards.length === 0" class="empty-state">
            <div class="empty-icon">⬡</div>
            <p class="empty-text">该稀有度暂无卡牌</p>
          </div>
        </div>
      </Transition>
    </main>

    <Transition name="modal-fade">
      <div v-if="detailCard" class="modal-overlay" @click.self="detailCard = null">
        <div class="modal-card" :class="`modal-card--${detailCard.rarity}`">
          <button class="modal-close" @click="detailCard = null">✕</button>
          <div class="modal-glow"></div>
          <div class="modal-header">
            <span class="modal-rarity-badge" :class="`badge--${detailCard.rarity}`">
              {{ rarityLabel(detailCard.rarity) }}
            </span>
            <span class="modal-score">{{ detailCard.score }}分</span>
          </div>
          <h2 class="modal-title">{{ detailCard.title }}</h2>
          <p class="modal-event">{{ detailCard.event }}</p>
          <div class="modal-divider" :class="`divider--${detailCard.rarity}`"></div>
          <div class="modal-details">
            <div class="detail-row">
              <span class="detail-label">拥有者</span>
              <span class="detail-value">{{ detailCard.owner }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">解锁时间</span>
              <span class="detail-value">{{ detailCard.date }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">稀有度</span>
              <span class="detail-value">{{ rarityLabel(detailCard.rarity) }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">关联事件</span>
              <span class="detail-value detail-value--link">{{ detailCard.event }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">探索次数</span>
              <span class="detail-value">{{ detailCard.exploreCount }} 次</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">累计停留</span>
              <span class="detail-value">{{ detailCard.stayText }}</span>
            </div>
          </div>
          <div class="modal-lore">
            <p class="lore-title">◈ 卡牌故事</p>
            <p class="lore-text">{{ detailCard.lore }}</p>
          </div>
        </div>
      </div>
    </Transition>

    <div class="cy-scanlines"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { championApi } from '@/api/champion'
import { getSessionId } from '@/utils/session'
import type { BackendChampionCard } from '@/types'

type RarityKey = 'legendary' | 'epic' | 'rare' | 'common'

interface ChampionEntry {
  id: number
  title: string
  event: string
  owner: string
  score: number
  date: string
  rarity: RarityKey
  exploreCount: number
  stayText: string
  lore: string
}

const activeTab = ref<RarityKey>('legendary')
const detailCard = ref<ChampionEntry | null>(null)
const cards = ref<ChampionEntry[]>([])
const loading = ref(false)
const loadError = ref<string | null>(null)

const LEVEL_TO_RARITY: Record<number, RarityKey> = {
  4: 'legendary',
  3: 'epic',
  2: 'rare',
  1: 'common',
}

const RARITY_LABEL: Record<RarityKey, string> = {
  legendary: '传说',
  epic: '史诗',
  rare: '稀有',
  common: '普通',
}

function rarityLabel(r: RarityKey): string {
  return RARITY_LABEL[r] || r
}

function formatDate(input: string | null | undefined): string {
  if (!input) return '-'
  const d = new Date(input)
  if (isNaN(d.getTime())) return '-'
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function formatDuration(seconds: number): string {
  if (!seconds || seconds <= 0) return '0 分钟'
  const minutes = Math.round(seconds / 60)
  if (minutes >= 60) {
    const h = Math.floor(minutes / 60)
    const m = minutes % 60
    return `${h} 小时 ${m} 分`
  }
  return `${minutes} 分钟`
}

function deriveScore(card: BackendChampionCard): number {
  // 综合得分: 探索次数 * 10 + 停留秒数 / 6, 归一到 0-100 区间
  const raw = card.explore_count * 10 + Math.floor((card.total_stay_duration || 0) / 6)
  if (card.card_level >= 4) return Math.max(85, Math.min(100, raw))
  if (card.card_level === 3) return Math.max(70, Math.min(90, raw))
  if (card.card_level === 2) return Math.max(55, Math.min(80, raw))
  return Math.max(30, Math.min(60, raw))
}

function deriveLore(card: BackendChampionCard): string {
  const desc = (card.event_description || '').trim()
  if (!desc) return '该卡牌记录了一段真实的探索旅程。'
  return desc.length > 120 ? `${desc.slice(0, 120)}…` : desc
}

function mapCard(card: BackendChampionCard): ChampionEntry {
  const rarity = LEVEL_TO_RARITY[card.card_level] || 'common'
  return {
    id: card.id,
    title: card.nickname?.trim() || card.event_name,
    event: card.event_name,
    owner: card.nickname?.trim() || '匿名探索者',
    score: deriveScore(card),
    date: formatDate(card.created_at),
    rarity,
    exploreCount: card.explore_count || 0,
    stayText: formatDuration(card.total_stay_duration || 0),
    lore: deriveLore(card),
  }
}

async function loadCards() {
  loading.value = true
  loadError.value = null
  try {
    const sid = getSessionId()
    const res = await championApi.getChampionCards(1, 100)
    const items = (res.data?.items || []) as unknown as BackendChampionCard[]
    cards.value = items.map(mapCard)
  } catch (e: unknown) {
    loadError.value = e instanceof Error ? e.message : '网络异常, 请稍后重试'
    cards.value = []
  } finally {
    loading.value = false
  }
}

onMounted(loadCards)

const hasAnyCard = computed(() => cards.value.length > 0)

const tabs = computed(() => {
  const counts: Record<RarityKey, number> = {
    legendary: 0, epic: 0, rare: 0, common: 0,
  }
  for (const c of cards.value) counts[c.rarity] += 1
  return [
    { key: 'legendary' as const, label: '传说', icon: '◆', count: counts.legendary },
    { key: 'epic' as const, label: '史诗', icon: '◈', count: counts.epic },
    { key: 'rare' as const, label: '稀有', icon: '◇', count: counts.rare },
    { key: 'common' as const, label: '普通', icon: '○', count: counts.common },
  ]
})

const currentTab = computed(() => tabs.value.find(t => t.key === activeTab.value) || tabs.value[0])

const currentCards = computed(() =>
  cards.value.filter(c => c.rarity === activeTab.value).sort((a, b) => b.score - a.score)
)

function openDetail(card: ChampionEntry) {
  detailCard.value = card
}
</script>

<style scoped>
.champions-gallery {
  width: 100%;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
  position: relative;
}

.gallery-header {
  position: sticky;
  top: 0;
  z-index: 100;
  padding: 14px 28px;
  display: flex;
  align-items: center;
  gap: 24px;
  background: linear-gradient(180deg, rgba(4, 8, 15, 0.98) 0%, rgba(4, 8, 15, 0.88) 100%);
  border-bottom: 1px solid var(--border-subtle);
  backdrop-filter: blur(12px);
}

.back-link {
  font-size: 13px;
  color: var(--cyan-core);
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 16px;
  border: 1px solid var(--border-cyan);
  border-radius: var(--radius-full);
  transition: all var(--transition-fast);
  white-space: nowrap;
  flex-shrink: 0;
}

.back-link:hover {
  background: rgba(49, 247, 255, 0.1);
  box-shadow: var(--glow-cyan);
}

.back-arrow { font-size: 15px; }

.header-titles {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
}

.gallery-title {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 800;
  color: var(--accent-gold);
  text-shadow: 0 0 20px rgba(212, 168, 75, 0.5);
  letter-spacing: 4px;
}

.gallery-subtitle {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
  letter-spacing: 3px;
  margin-top: 2px;
}

.header-decoration { width: 40px; flex-shrink: 0; }

.tab-bar {
  display: flex;
  gap: 4px;
  padding: 12px 28px;
  background: rgba(8, 15, 28, 0.6);
  border-bottom: 1px solid var(--border-subtle);
  overflow-x: auto;
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: none;
  border: 1px solid transparent;
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: all 0.25s;
  white-space: nowrap;
  font-size: 14px;
  color: var(--text-muted);
}

.tab-btn:hover {
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-light);
}

.tab-btn.active {
  background: rgba(49, 247, 255, 0.08);
  color: #fff;
}

.tab-btn--legendary.active {
  border-color: rgba(212, 168, 75, 0.5);
  background: rgba(212, 168, 75, 0.1);
}

.tab-btn--epic.active {
  border-color: rgba(255, 53, 243, 0.5);
  background: rgba(255, 53, 243, 0.1);
}

.tab-btn--rare.active {
  border-color: rgba(49, 247, 255, 0.5);
  background: rgba(49, 247, 255, 0.1);
}

.tab-btn--common.active {
  border-color: rgba(128, 128, 128, 0.4);
  background: rgba(128, 128, 128, 0.08);
}

.tab-icon { font-size: 16px; }

.tab-btn--legendary .tab-icon { color: var(--accent-gold); }
.tab-btn--epic .tab-icon { color: var(--pink-core); }
.tab-btn--rare .tab-icon { color: var(--cyan-core); }
.tab-btn--common .tab-icon { color: var(--text-muted); }

.tab-count {
  font-family: var(--font-mono);
  font-size: 11px;
  padding: 1px 8px;
  border-radius: var(--radius-full);
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-muted);
}

/* Loading / Error / Empty state */
.loading-state,
.error-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  gap: 12px;
}

.empty-state--full { min-height: 50vh; }

.loading-icon,
.empty-icon,
.error-icon {
  font-size: 48px;
  opacity: 0.4;
}

.loading-icon { color: var(--cyan-core); animation: pulse 1.4s ease-in-out infinite; }
.empty-icon { color: var(--text-muted); }
.error-icon { color: #ff8a4d; }

@keyframes pulse {
  0%, 100% { opacity: 0.3; transform: scale(1); }
  50% { opacity: 0.8; transform: scale(1.08); }
}

.loading-text,
.error-text,
.empty-text {
  font-family: var(--font-mono);
  font-size: 14px;
  color: var(--text-muted);
}

.error-text { color: #ffba6b; }
.empty-hint { font-size: 13px; color: var(--text-muted); opacity: 0.7; }

.retry-btn,
.empty-cta {
  margin-top: 6px;
  padding: 8px 22px;
  background: rgba(49, 247, 255, 0.12);
  border: 1px solid var(--border-cyan);
  border-radius: var(--radius-full);
  color: var(--cyan-core);
  font-size: 13px;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.2s;
}

.retry-btn:hover,
.empty-cta:hover {
  background: rgba(49, 247, 255, 0.2);
  box-shadow: var(--glow-cyan);
}

.gallery-main {
  flex: 1;
  overflow-y: auto;
  padding: 28px;
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.champion-card {
  position: relative;
  cursor: pointer;
  transition: all 0.3s;
}

.champion-card:hover {
  transform: translateY(-6px);
}

.card-rank-badge {
  position: absolute;
  top: -12px;
  left: 16px;
  font-size: 28px;
  z-index: 2;
  filter: drop-shadow(0 2px 8px rgba(0,0,0,0.5));
}

.champion-card--top .card-rank-badge {
  font-size: 34px;
  top: -16px;
  left: 20px;
}

.card-inner {
  position: relative;
  border-radius: var(--radius-md);
  padding: 2px;
  overflow: hidden;
}

.card-glow-layer {
  position: absolute;
  inset: 0;
  border-radius: var(--radius-md);
  opacity: 0;
  transition: opacity 0.3s;
  pointer-events: none;
}

.champion-card:hover .card-glow-layer { opacity: 1; }

.champion-card--legendary .card-inner {
  background: linear-gradient(135deg, rgba(212, 168, 75, 0.7), rgba(212, 168, 75, 0.15), rgba(212, 168, 75, 0.7));
}

.champion-card--epic .card-inner {
  background: linear-gradient(135deg, rgba(255, 53, 243, 0.6), rgba(255, 53, 243, 0.12), rgba(255, 53, 243, 0.6));
}

.champion-card--rare .card-inner {
  background: linear-gradient(135deg, rgba(49, 247, 255, 0.6), rgba(49, 247, 255, 0.12), rgba(49, 247, 255, 0.6));
}

.champion-card--common .card-inner {
  background: linear-gradient(135deg, rgba(128, 128, 128, 0.4), rgba(128, 128, 128, 0.08), rgba(128, 128, 128, 0.4));
}

.champion-card--legendary:hover .card-glow-layer {
  box-shadow: 0 0 40px rgba(212, 168, 75, 0.3), inset 0 0 40px rgba(212, 168, 75, 0.1);
}

.champion-card--epic:hover .card-glow-layer {
  box-shadow: 0 0 40px rgba(255, 53, 243, 0.3), inset 0 0 40px rgba(255, 53, 243, 0.1);
}

.champion-card--rare:hover .card-glow-layer {
  box-shadow: 0 0 40px rgba(49, 247, 255, 0.3), inset 0 0 40px rgba(49, 247, 255, 0.1);
}

.champion-card--common:hover .card-glow-layer {
  box-shadow: 0 0 30px rgba(128, 128, 128, 0.2);
}

.card-inner > .card-head { position: relative; z-index: 1; }

.card-head,
.card-title,
.card-event-name,
.card-divider,
.card-info-row,
.card-footer {
  position: relative;
  z-index: 1;
  background: var(--bg-card);
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 20px 0;
}

.card-rarity-tag {
  font-size: 11px;
  font-weight: 700;
  padding: 3px 12px;
  border-radius: var(--radius-full);
  font-family: var(--font-mono);
}

.tag--legendary { color: var(--accent-gold); background: rgba(212, 168, 75, 0.12); border: 1px solid rgba(212, 168, 75, 0.3); }
.tag--epic { color: var(--pink-core); background: rgba(255, 53, 243, 0.12); border: 1px solid rgba(255, 53, 243, 0.3); }
.tag--rare { color: var(--cyan-core); background: rgba(49, 247, 255, 0.12); border: 1px solid rgba(49, 247, 255, 0.3); }
.tag--common { color: var(--text-muted); background: rgba(128, 128, 128, 0.08); border: 1px solid rgba(128, 128, 128, 0.2); }

.card-score {
  font-family: var(--font-mono);
  font-size: 22px;
  font-weight: 800;
}

.champion-card--legendary .card-score { color: var(--accent-gold); text-shadow: 0 0 12px rgba(212, 168, 75, 0.4); }
.champion-card--epic .card-score { color: var(--pink-core); text-shadow: 0 0 12px rgba(255, 53, 243, 0.4); }
.champion-card--rare .card-score { color: var(--cyan-core); text-shadow: 0 0 12px rgba(49, 247, 255, 0.4); }
.champion-card--common .card-score { color: var(--text-muted); }

.card-title {
  font-family: var(--font-serif);
  font-size: 22px;
  font-weight: 700;
  color: #ffffff;
  padding: 12px 20px 4px;
  line-height: 1.3;
}

.card-event-name {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--text-muted);
  padding: 0 20px 12px;
}

.card-divider {
  height: 1px;
  margin: 0 20px;
}

.divider--legendary { background: linear-gradient(90deg, transparent, var(--accent-gold), transparent); opacity: 0.4; }
.divider--epic { background: linear-gradient(90deg, transparent, var(--pink-core), transparent); opacity: 0.4; }
.divider--rare { background: linear-gradient(90deg, transparent, var(--cyan-core), transparent); opacity: 0.4; }
.divider--common { background: linear-gradient(90deg, transparent, var(--text-muted), transparent); opacity: 0.3; }

.card-info-row {
  padding: 14px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-owner-block {
  display: flex;
  align-items: center;
  gap: 12px;
}

.owner-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 700;
  font-family: var(--font-serif);
  flex-shrink: 0;
}

.avatar--legendary { background: linear-gradient(135deg, rgba(212, 168, 75, 0.3), rgba(212, 168, 75, 0.1)); color: var(--accent-gold); border: 1px solid rgba(212, 168, 75, 0.4); }
.avatar--epic { background: linear-gradient(135deg, rgba(255, 53, 243, 0.3), rgba(255, 53, 243, 0.1)); color: var(--pink-core); border: 1px solid rgba(255, 53, 243, 0.4); }
.avatar--rare { background: linear-gradient(135deg, rgba(49, 247, 255, 0.3), rgba(49, 247, 255, 0.1)); color: var(--cyan-core); border: 1px solid rgba(49, 247, 255, 0.4); }
.avatar--common { background: rgba(128, 128, 128, 0.15); color: var(--text-muted); border: 1px solid rgba(128, 128, 128, 0.3); }

.owner-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.owner-name {
  font-size: 14px;
  color: var(--text-light);
  font-weight: 600;
}

.owner-date {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
}

.card-footer {
  padding: 10px 20px 16px;
  text-align: center;
}

.footer-hint {
  font-size: 12px;
  color: var(--text-muted);
  opacity: 0;
  transition: opacity 0.2s;
}

.champion-card:hover .footer-hint { opacity: 1; }

.empty-state {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 80px 20px;
}

.empty-icon {
  font-size: 48px;
  color: var(--text-muted);
  opacity: 0.3;
  margin-bottom: 12px;
}

.empty-text {
  font-family: var(--font-mono);
  font-size: 14px;
  color: var(--text-muted);
}

.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(2, 4, 10, 0.85);
  backdrop-filter: blur(8px);
  padding: 20px;
}

.modal-card {
  position: relative;
  width: min(480px, 90vw);
  border-radius: var(--radius-md);
  padding: 2px;
  overflow: hidden;
}

.modal-card--legendary { background: linear-gradient(135deg, rgba(212, 168, 75, 0.8), rgba(212, 168, 75, 0.2), rgba(212, 168, 75, 0.8)); }
.modal-card--epic { background: linear-gradient(135deg, rgba(255, 53, 243, 0.7), rgba(255, 53, 243, 0.15), rgba(255, 53, 243, 0.7)); }
.modal-card--rare { background: linear-gradient(135deg, rgba(49, 247, 255, 0.7), rgba(49, 247, 255, 0.15), rgba(49, 247, 255, 0.7)); }
.modal-card--common { background: linear-gradient(135deg, rgba(128, 128, 128, 0.5), rgba(128, 128, 128, 0.1), rgba(128, 128, 128, 0.5)); }

.modal-close {
  position: absolute;
  top: 16px;
  right: 16px;
  z-index: 10;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--border-subtle);
  color: var(--text-muted);
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.modal-close:hover {
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
}

.modal-glow {
  position: absolute;
  inset: 0;
  border-radius: var(--radius-md);
  pointer-events: none;
}

.modal-card--legendary .modal-glow { box-shadow: 0 0 60px rgba(212, 168, 75, 0.2); }
.modal-card--epic .modal-glow { box-shadow: 0 0 60px rgba(255, 53, 243, 0.2); }
.modal-card--rare .modal-glow { box-shadow: 0 0 60px rgba(49, 247, 255, 0.2); }
.modal-card--common .modal-glow { box-shadow: 0 0 40px rgba(128, 128, 128, 0.1); }

.modal-header {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 28px 28px 0;
  background: var(--bg-card);
  border-radius: var(--radius-md) var(--radius-md) 0 0;
}

.modal-rarity-badge {
  font-size: 13px;
  font-weight: 700;
  padding: 4px 14px;
  border-radius: var(--radius-full);
  font-family: var(--font-mono);
}

.badge--legendary { color: var(--accent-gold); background: rgba(212, 168, 75, 0.12); border: 1px solid rgba(212, 168, 75, 0.4); }
.badge--epic { color: var(--pink-core); background: rgba(255, 53, 243, 0.12); border: 1px solid rgba(255, 53, 243, 0.4); }
.badge--rare { color: var(--cyan-core); background: rgba(49, 247, 255, 0.12); border: 1px solid rgba(49, 247, 255, 0.4); }
.badge--common { color: var(--text-muted); background: rgba(128, 128, 128, 0.08); border: 1px solid rgba(128, 128, 128, 0.3); }

.modal-score {
  font-family: var(--font-mono);
  font-size: 28px;
  font-weight: 800;
}

.modal-card--legendary .modal-score { color: var(--accent-gold); text-shadow: 0 0 12px rgba(212, 168, 75, 0.4); }
.modal-card--epic .modal-score { color: var(--pink-core); text-shadow: 0 0 12px rgba(255, 53, 243, 0.4); }
.modal-card--rare .modal-score { color: var(--cyan-core); text-shadow: 0 0 12px rgba(49, 247, 255, 0.4); }
.modal-card--common .modal-score { color: var(--text-muted); }

.modal-title {
  position: relative;
  z-index: 1;
  background: var(--bg-card);
  padding: 16px 28px 4px;
  font-family: var(--font-serif);
  font-size: 26px;
  font-weight: 700;
  color: #fff;
}

.modal-event {
  position: relative;
  z-index: 1;
  background: var(--bg-card);
  padding: 0 28px 16px;
  font-family: var(--font-mono);
  font-size: 14px;
  color: var(--text-muted);
}

.modal-divider {
  position: relative;
  z-index: 1;
  height: 1px;
  margin: 0 28px;
}

.modal-details {
  position: relative;
  z-index: 1;
  background: var(--bg-card);
  padding: 16px 28px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.detail-label {
  font-size: 13px;
  color: var(--text-muted);
}

.detail-value {
  font-size: 14px;
  color: var(--text-light);
  font-weight: 600;
}

.detail-value--link { color: var(--cyan-core); }

.modal-lore {
  position: relative;
  z-index: 1;
  background: var(--bg-card);
  padding: 0 28px 28px;
}

.lore-title {
  font-size: 12px;
  font-weight: 700;
  color: var(--accent-gold);
  margin-bottom: 8px;
  font-family: var(--font-mono);
}

.lore-text {
  font-size: 14px;
  line-height: 1.8;
  color: var(--text-light);
  font-family: var(--font-serif);
}

.tab-switch-enter-active { transition: all 0.3s ease; }
.tab-switch-leave-active { transition: all 0.2s ease; }
.tab-switch-enter-from { opacity: 0; transform: translateY(12px); }
.tab-switch-leave-to { opacity: 0; transform: translateY(-8px); }

.modal-fade-enter-active { transition: all 0.3s ease; }
.modal-fade-leave-active { transition: all 0.2s ease; }
.modal-fade-enter-from { opacity: 0; }
.modal-fade-leave-to { opacity: 0; }
.modal-fade-enter-from .modal-card { transform: scale(0.92) translateY(20px); }
.modal-fade-enter-to .modal-card { transform: scale(1) translateY(0); }

@media (max-width: 640px) {
  .gallery-header { padding: 12px 16px; gap: 12px; }
  .gallery-title { font-size: 18px; letter-spacing: 2px; }
  .gallery-subtitle { font-size: 10px; }
  .header-decoration { display: none; }
  .tab-bar { padding: 10px 16px; }
  .tab-btn { padding: 8px 14px; font-size: 13px; }
  .gallery-main { padding: 20px 16px; }
  .card-grid { grid-template-columns: 1fr; gap: 16px; }
  .card-title { font-size: 18px; }
  .card-score { font-size: 18px; }
}
</style>
