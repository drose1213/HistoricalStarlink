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

    <main class="gallery-main">
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
          </div>
          <div class="modal-lore">
            <p class="lore-title">◈ 卡牌故事</p>
            <p class="lore-text">{{ getLore(detailCard) }}</p>
          </div>
        </div>
      </div>
    </Transition>

    <div class="cy-scanlines"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface ChampionEntry {
  id: number
  title: string
  event: string
  owner: string
  score: number
  date: string
  rarity: string
}

const activeTab = ref('legendary')
const detailCard = ref<ChampionEntry | null>(null)

const allCards: ChampionEntry[] = [
  { id: 1, title: '时空主宰·秦', event: '秦始皇统一六国', owner: '司马星辰', score: 98, date: '2025-12-01', rarity: 'legendary' },
  { id: 2, title: '帝国缔造者', event: '罗马帝国建立', owner: '诸葛云霄', score: 95, date: '2025-11-15', rarity: 'legendary' },
  { id: 3, title: '变革先锋', event: '法国大革命', owner: '李白银河', score: 92, date: '2025-10-20', rarity: 'legendary' },
  { id: 4, title: '铁血商君', event: '商鞅变法', owner: '轩辕破晓', score: 88, date: '2025-09-10', rarity: 'epic' },
  { id: 5, title: '丝路开拓者', event: '大汉帝国建立', owner: '王羲之光', score: 85, date: '2025-08-22', rarity: 'epic' },
  { id: 6, title: '启蒙之火', event: '工业革命', owner: '苏轼流星', score: 82, date: '2025-07-18', rarity: 'epic' },
  { id: 7, title: '东征战神', event: '亚历山大东征', owner: '诸葛亮辰', score: 78, date: '2025-06-05', rarity: 'rare' },
  { id: 8, title: '文化使者', event: '大汉帝国建立', owner: '杜甫月华', score: 75, date: '2025-05-12', rarity: 'rare' },
  { id: 9, title: '航海先驱', event: '工业革命', owner: '辛弃疾风', score: 72, date: '2025-04-08', rarity: 'rare' },
  { id: 10, title: '历史初探', event: '商鞅变法', owner: '陆游星河', score: 65, date: '2025-03-01', rarity: 'common' },
  { id: 11, title: '文明观察者', event: '罗马帝国建立', owner: '陶渊明日', score: 60, date: '2025-02-14', rarity: 'common' },
  { id: 12, title: '探索学徒', event: '法国大革命', owner: '柳宗元辰', score: 55, date: '2025-01-20', rarity: 'common' },
]

const tabs = computed(() => [
  { key: 'legendary', label: '传说', icon: '◆', count: allCards.filter(c => c.rarity === 'legendary').length },
  { key: 'epic', label: '史诗', icon: '◈', count: allCards.filter(c => c.rarity === 'epic').length },
  { key: 'rare', label: '稀有', icon: '◇', count: allCards.filter(c => c.rarity === 'rare').length },
  { key: 'common', label: '普通', icon: '○', count: allCards.filter(c => c.rarity === 'common').length },
])

const currentTab = computed(() => tabs.value.find(t => t.key === activeTab.value) || tabs.value[0])

const currentCards = computed(() =>
  allCards.filter(c => c.rarity === activeTab.value).sort((a, b) => b.score - a.score)
)

function openDetail(card: ChampionEntry) {
  detailCard.value = card
}

function rarityLabel(rarity: string): string {
  const map: Record<string, string> = { legendary: '传说', epic: '史诗', rare: '稀有', common: '普通' }
  return map[rarity] || rarity
}

function getLore(card: ChampionEntry): string {
  const lores: Record<string, string> = {
    '时空主宰·秦': '穿越两千年的迷雾，以铁血手腕统一六国，书同文、车同轨，铸就华夏第一帝国的不朽传说。',
    '帝国缔造者': '从罗马废墟中崛起，以智慧与权谋缔造延续千年的辉煌帝国，永恒之城的奠基者。',
    '变革先锋': '当旧制度的枷锁破碎，自由之声响彻巴黎街头，一个新时代在革命的火焰中诞生。',
    '铁血商君': '以严刑峻法重塑秦国，废井田、开阡陌，为统一天下奠定根基的改革先驱。',
    '丝路开拓者': '凿空西域，开辟万里丝路，将东方文明的光辉播撒至世界的每一个角落。',
    '启蒙之火': '蒸汽机的轰鸣唤醒了沉睡的生产力，人类文明从此驶入工业化的快车道。',
    '东征战神': '率军横扫欧亚大陆，以征服者的姿态将希腊文明的种子播撒到已知世界的尽头。',
    '文化使者': '驼铃声声，佛经万卷，以一人之力搭建起东西方文明交流的桥梁。',
    '航海先驱': '当大洋不再未知，文明的航船便驶向了更广阔的星辰大海。',
    '历史初探': '每一次翻阅史书，都是与古人的一次跨时空对话，探索之路由此开始。',
    '文明观察者': '以旁观者的视角审视历史的洪流，在细微处发现文明演进的密码。',
    '探索学徒': '踏出探索的第一步，虽是学徒，却怀揣着对历史最纯粹的好奇与敬畏。',
  }
  return lores[card.title] || '这张卡牌记录了一段珍贵的探索旅程。'
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
