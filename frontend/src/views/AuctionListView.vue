<template>
  <div class="auction-list-view">
    <header class="page-header">
      <router-link to="/" class="back-link">
        <span class="back-arrow">←</span>
        {{ t('common.back') }}
      </router-link>
      <h1 class="page-title">{{ t('auction.title') }}</h1>
      <p class="page-subtitle">{{ t('auction.subtitle') }}</p>
    </header>

    <div class="filter-bar">
      <button
        v-for="opt in statusOptions"
        :key="opt.value"
        class="filter-btn"
        :class="{ active: status === opt.value }"
        @click="onStatusChange(opt.value)"
      >
        {{ opt.label }}
      </button>
      <span class="filter-count">{{ t('auction.total', { n: store.total }) }}</span>
    </div>

    <div v-if="store.isLoading" class="state-block">
      <div class="state-icon">⬡</div>
      <p>{{ t('common.loading') }}</p>
    </div>

    <div v-else-if="store.auctions.length === 0" class="state-block">
      <div class="state-icon">⚖</div>
      <p class="state-title">{{ t('auction.empty') }}</p>
      <p class="state-hint">{{ t('auction.emptyHint') }}</p>
    </div>

    <div v-else class="auction-grid">
      <router-link
        v-for="a in store.auctions"
        :key="a.id"
        :to="{ name: 'AuctionDetail', params: { id: String(a.id) } }"
        class="auction-card"
        :class="`auction-card--${a.status}`"
      >
        <div class="ac-head">
          <span class="ac-status" :class="`ac-status--${a.status}`">{{ statusLabel(a.status) }}</span>
          <span class="ac-id">#{{ a.id }}</span>
        </div>
        <h3 class="ac-title">{{ a.event_name }}</h3>
        <p class="ac-desc" v-if="a.description">{{ a.description }}</p>
        <div class="ac-price-row">
          <div>
            <div class="ac-price-label">{{ t('auction.currentPrice') }}</div>
            <div class="ac-price">¥ {{ a.current_price.toFixed(2) }}</div>
          </div>
          <div class="ac-bids">
            <div class="ac-bids-label">{{ t('auction.bidCount') }}</div>
            <div class="ac-bids-value">{{ a.bid_count }}</div>
          </div>
        </div>
        <div class="ac-time">{{ t('auction.endsAt', { time: formatTime(a.end_time) }) }}</div>
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useAuctionStore } from '@/stores/auction'
import { useI18n } from '@/composables/useI18n'
import type { CardAuction } from '@/types'

const { t } = useI18n()
const store = useAuctionStore()
const status = ref<'active' | 'sold' | 'expired' | 'cancelled' | 'all'>('active')

const statusOptions: { value: typeof status.value; label: string }[] = [
  { value: 'active', label: t('auction.statusActive') },
  { value: 'sold', label: t('auction.statusSold') },
  { value: 'expired', label: t('auction.statusExpired') },
  { value: 'cancelled', label: t('auction.statusCancelled') }
]

function statusLabel(s: CardAuction['status']) {
  return t(`auction.status.${s}`)
}

function formatTime(s: string): string {
  if (!s) return '-'
  const d = new Date(s)
  if (isNaN(d.getTime())) return '-'
  return d.toLocaleString()
}

function onStatusChange(s: typeof status.value) {
  status.value = s
  store.load({ status: s })
}

onMounted(() => store.load({ status: status.value }))
</script>

<style scoped>
.auction-list-view {
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
.page-title {
  font-family: var(--font-display);
  font-size: 26px;
  font-weight: 800;
  color: var(--pink-core);
  letter-spacing: 4px;
  text-shadow: 0 0 20px rgba(255, 53, 243, 0.4);
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
  flex-wrap: wrap;
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
  border-color: var(--border-pink);
  color: var(--pink-core);
  background: rgba(255, 53, 243, 0.08);
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
.auction-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}
.auction-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 20px;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  text-decoration: none;
  color: inherit;
  transition: all 0.25s;
}
.auction-card:hover {
  transform: translateY(-4px);
  border-color: var(--border-pink);
  box-shadow: var(--glow-pink);
}
.auction-card--sold { border-color: rgba(212, 168, 75, 0.4); }
.auction-card--expired, .auction-card--cancelled { opacity: 0.6; }
.ac-head { display: flex; justify-content: space-between; align-items: center; }
.ac-status {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 2px;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  text-transform: uppercase;
}
.ac-status--active { color: var(--pink-core); background: rgba(255, 53, 243, 0.12); }
.ac-status--sold { color: var(--accent-gold); background: rgba(212, 168, 75, 0.15); }
.ac-status--expired { color: var(--text-muted); background: rgba(128, 128, 128, 0.15); }
.ac-status--cancelled { color: #ff8a8a; background: rgba(255, 107, 107, 0.12); }
.ac-id { font-family: var(--font-mono); font-size: 10px; color: var(--text-muted); }
.ac-title { font-family: var(--font-serif); font-size: 20px; color: #fff; }
.ac-desc { font-size: 13px; color: var(--text-muted); line-height: 1.5; max-height: 3em; overflow: hidden; }
.ac-price-row { display: flex; justify-content: space-between; align-items: flex-end; margin-top: 6px; }
.ac-price-label, .ac-bids-label {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-muted);
  letter-spacing: 1px;
}
.ac-price { font-family: var(--font-mono); font-size: 22px; color: var(--pink-core); font-weight: 700; }
.ac-bids-value { font-family: var(--font-mono); font-size: 18px; color: var(--cyan-core); text-align: right; }
.ac-time { font-family: var(--font-mono); font-size: 11px; color: var(--text-muted); }
</style>
