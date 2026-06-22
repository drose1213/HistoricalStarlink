<template>
  <div class="collection-view">
    <header class="page-header">
      <router-link to="/" class="back-link">
        <span class="back-arrow">←</span>
        {{ t('common.back') }}
      </router-link>
      <h1 class="page-title">{{ t('collection.title') }}</h1>
      <p class="page-subtitle">{{ t('collection.subtitle') }}</p>
    </header>

    <div class="filter-bar">
      <button
        v-for="opt in filterOptions"
        :key="opt.value"
        class="filter-btn"
        :class="{ active: filter === opt.value }"
        @click="filter = opt.value; load()"
      >
        {{ opt.label }}
      </button>
      <span class="filter-count">
        {{ t('collection.total', { n: store.total }) }}
      </span>
    </div>

    <div v-if="store.isLoading" class="state-block">
      <div class="state-icon">⬡</div>
      <p>{{ t('common.loading') }}</p>
    </div>

    <div v-else-if="store.items.length === 0" class="state-block">
      <div class="state-icon">◇</div>
      <p class="state-title">{{ t('collection.empty') }}</p>
      <p class="state-hint">{{ t('collection.emptyHint') }}</p>
      <router-link to="/" class="cta-btn">{{ t('collection.goExplore') }}</router-link>
    </div>

    <div v-else class="card-grid">
      <div
        v-for="item in store.items"
        :key="item.id"
        class="collection-card"
        :class="{ 'is-high': item.is_high_rated, 'is-auction': isOnAuction(item.card_id) }"
        @click="openDetail(item)"
      >
        <div class="cc-head">
          <span class="cc-source">{{ sourceLabel(item.source) }}</span>
          <span v-if="item.is_high_rated" class="cc-tag cc-tag--high">★ {{ t('collection.highRated') }}</span>
        </div>
        <h3 class="cc-title">{{ item.event_name }}</h3>
        <p class="cc-meta">{{ t('collection.eventId', { id: item.event_id }) }}</p>
        <div class="cc-actions" @click.stop>
          <button
            v-if="isOnAuction(item.card_id)"
            class="cta-btn cta-btn--ghost"
            @click="goAuction(item.card_id)"
          >
            {{ t('collection.viewAuction') }}
          </button>
          <button class="cta-btn cta-btn--danger" @click="onRemove(item.id)">
            {{ t('common.delete') }}
          </button>
        </div>
      </div>
    </div>

    <Transition name="modal-fade">
      <div v-if="detailItem" class="modal-overlay" @click.self="detailItem = null">
        <div class="modal-card">
          <button class="modal-close" @click="detailItem = null">✕</button>
          <div class="modal-header">
            <span class="cc-source">{{ sourceLabel(detailItem.source) }}</span>
            <span v-if="detailItem.is_high_rated" class="cc-tag cc-tag--high">★ {{ t('collection.highRated') }}</span>
          </div>
          <h2 class="modal-title">{{ detailItem.event_name }}</h2>
          <p class="modal-event">{{ t('collection.eventId', { id: detailItem.event_id }) }}</p>
          <div class="modal-rating">
            <RatingPanel :event-id="detailItem.event_id" :card-id="detailItem.card_id" />
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useCollectionStore } from '@/stores/collection'
import { useAuctionStore } from '@/stores/auction'
import { useI18n } from '@/composables/useI18n'
import { useAppStore } from '@/stores/app'
import RatingPanel from '@/components/RatingPanel.vue'
import type { UserCardCollection } from '@/types'

const { t } = useI18n()
const store = useCollectionStore()
const auctionStore = useAuctionStore()
const app = useAppStore()
const router = useRouter()

const filter = ref<'all' | 'high'>('all')
const detailItem = ref<UserCardCollection | null>(null)

const filterOptions = [
  { value: 'all' as const, label: t('collection.filterAll') },
  { value: 'high' as const, label: t('collection.filterHigh') }
]

function isOnAuction(cardId: number) {
  return auctionStore.auctions.some(a => a.card_id === cardId && a.status === 'active')
}

function sourceLabel(source: UserCardCollection['source']) {
  return t(`collection.source.${source}`)
}

async function load() {
  await Promise.all([
    store.load(undefined, filter.value === 'high'),
    auctionStore.load({ status: 'active' })
  ])
}

async function onRemove(id: number) {
  try {
    await store.remove(id)
    app.showToast('success', t('collection.removed'))
  } catch (e) {
    app.showToast('error', t('collection.removeFail'))
  }
}

function goAuction(cardId: number) {
  const a = auctionStore.auctions.find(x => x.card_id === cardId && x.status === 'active')
  if (a) router.push({ name: 'AuctionDetail', params: { id: String(a.id) } })
}

function openDetail(item: UserCardCollection) {
  detailItem.value = item
}

onMounted(load)
</script>

<style scoped>
.collection-view {
  min-height: 100vh;
  padding: 24px 32px 60px;
  background: var(--bg-primary);
}
.page-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  margin-bottom: 24px;
}
.back-link {
  align-self: flex-start;
  font-size: 13px;
  color: var(--cyan-core);
  text-decoration: none;
  padding: 6px 14px;
  border: 1px solid var(--border-cyan);
  border-radius: var(--radius-full);
}
.back-link:hover { background: rgba(49, 247, 255, 0.1); }
.page-title {
  font-family: var(--font-display);
  font-size: 26px;
  font-weight: 800;
  color: var(--accent-gold);
  letter-spacing: 4px;
  text-shadow: 0 0 20px rgba(212, 168, 75, 0.4);
}
.page-subtitle {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-muted);
  letter-spacing: 2px;
}
.filter-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
}
.filter-btn {
  padding: 6px 16px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
  color: var(--text-muted);
  font-size: 13px;
  cursor: pointer;
}
.filter-btn.active {
  border-color: var(--border-cyan);
  color: var(--cyan-core);
  background: rgba(49, 247, 255, 0.08);
}
.filter-count {
  margin-left: auto;
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-muted);
}
.state-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 80px 20px;
  text-align: center;
}
.state-icon { font-size: 48px; opacity: 0.4; }
.state-title { font-size: 16px; color: var(--text-light); }
.state-hint { font-size: 13px; color: var(--text-muted); }
.cta-btn {
  padding: 8px 20px;
  background: rgba(49, 247, 255, 0.12);
  border: 1px solid var(--border-cyan);
  border-radius: var(--radius-full);
  color: var(--cyan-core);
  text-decoration: none;
  font-size: 13px;
  cursor: pointer;
}
.cta-btn--ghost { background: transparent; }
.cta-btn--danger {
  border-color: rgba(255, 107, 107, 0.4);
  color: #ff8a8a;
  background: rgba(255, 107, 107, 0.08);
}
.cta-btn:hover { box-shadow: var(--glow-cyan); }
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}
.collection-card {
  position: relative;
  padding: 18px;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.collection-card.is-high {
  border-color: rgba(212, 168, 75, 0.5);
  box-shadow: 0 0 18px rgba(212, 168, 75, 0.2);
}
.collection-card.is-auction::after {
  content: 'AUCTION';
  position: absolute;
  top: 10px;
  right: 10px;
  font-family: var(--font-mono);
  font-size: 9px;
  letter-spacing: 2px;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  background: rgba(255, 53, 243, 0.12);
  color: var(--pink-core);
  border: 1px solid var(--border-pink);
}
.cc-head { display: flex; align-items: center; gap: 6px; }
.cc-source {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-muted);
  padding: 2px 8px;
  border-radius: var(--radius-full);
  background: rgba(255, 255, 255, 0.04);
}
.cc-tag {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-family: var(--font-mono);
}
.cc-tag--high {
  background: rgba(212, 168, 75, 0.15);
  color: var(--accent-gold);
}
.cc-title { font-size: 18px; color: #fff; font-family: var(--font-serif); }
.cc-meta { font-family: var(--font-mono); font-size: 12px; color: var(--text-muted); }
.cc-actions { margin-top: auto; display: flex; gap: 8px; }

/* 详情弹层 */
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
  max-height: 90vh;
  overflow-y: auto;
  background: var(--bg-card);
  border: 1px solid var(--border-cyan);
  border-radius: var(--radius-md);
  padding: 24px 28px 28px;
  box-shadow: var(--glow-cyan);
}
.modal-close {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--border-subtle);
  color: var(--text-muted);
  font-size: 14px;
  cursor: pointer;
}
.modal-close:hover { background: rgba(255, 255, 255, 0.12); color: #fff; }
.modal-header { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
.modal-title {
  font-family: var(--font-serif);
  font-size: 22px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 4px;
}
.modal-event {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 16px;
}
.modal-rating { margin: 0 -4px; }
.modal-fade-enter-active { transition: opacity 0.3s ease; }
.modal-fade-leave-active { transition: opacity 0.2s ease; }
.modal-fade-enter-from, .modal-fade-leave-to { opacity: 0; }
.modal-fade-enter-from .modal-card { transform: scale(0.92) translateY(20px); }
.modal-fade-enter-to .modal-card { transform: scale(1) translateY(0); }
</style>
