<template>
  <div class="auction-detail-view">
    <header class="page-header">
      <router-link to="/auction" class="back-link">
        <span class="back-arrow">←</span>
        {{ t('common.backToList') }}
      </router-link>
    </header>

    <div v-if="!detail" class="state-block">
      <div class="state-icon">⬡</div>
      <p>{{ t('common.loading') }}</p>
    </div>

    <template v-else>
      <section class="auction-panel">
        <span class="ac-status" :class="`ac-status--${detail.auction.status}`">
          {{ statusLabel(detail.auction.status) }}
        </span>
        <h1 class="ad-title">{{ detail.auction.event_name }}</h1>
        <p class="ad-desc" v-if="detail.auction.description">{{ detail.auction.description }}</p>
        <div class="ad-price-row">
          <div>
            <div class="ad-label">{{ t('auction.currentPrice') }}</div>
            <div class="ad-price">¥ {{ detail.auction.current_price.toFixed(2) }}</div>
            <div class="ad-sub">
              {{ t('auction.startPrice', { n: detail.auction.start_price.toFixed(2) }) }}
            </div>
          </div>
          <div>
            <div class="ad-label">{{ t('auction.bidCount') }}</div>
            <div class="ad-price ad-price--cyan">{{ detail.auction.bid_count }}</div>
          </div>
          <div>
            <div class="ad-label">{{ t('auction.endsAt', { time: '' }) }}</div>
            <div class="ad-time">{{ formatTime(detail.auction.end_time) }}</div>
          </div>
        </div>

        <div class="ad-actions" v-if="detail.auction.status === 'active'">
          <input
            v-model.number="bidAmount"
            type="number"
            class="bid-input"
            :min="minBid"
            :placeholder="t('auction.bidPlaceholder', { n: minBid.toFixed(2) })"
          />
          <button class="bid-btn" :disabled="bidding" @click="onBid">
            {{ bidding ? t('auction.bidding') : t('auction.placeBid') }}
          </button>
        </div>

        <div class="ad-actions" v-else-if="detail.auction.status === 'sold' && isWinner">
          <div class="ad-review">
            <div class="ad-label">{{ t('auction.leaveReview') }}</div>
            <div class="ad-stars">
              <span
                v-for="n in 5"
                :key="n"
                class="ad-star"
                :class="{ active: reviewStars >= n }"
                @click="reviewStars = n"
              >★</span>
            </div>
            <input
              v-model="reviewComment"
              class="bid-input"
              :placeholder="t('auction.reviewPlaceholder')"
              maxlength="500"
            />
            <button class="bid-btn" :disabled="reviewStars === 0" @click="onReview">
              {{ t('auction.submitReview') }}
            </button>
          </div>
        </div>

        <div v-if="detail.auction.sold_price" class="ad-sold">
          {{ t('auction.soldFor', { n: detail.auction.sold_price.toFixed(2) }) }}
          <span v-if="detail.auction.platform_fee">
            · {{ t('auction.fee', { n: detail.auction.platform_fee.toFixed(2) }) }}
          </span>
        </div>
      </section>

      <section class="bid-section">
        <h2 class="section-title">{{ t('auction.bidHistory') }}</h2>
        <div v-if="detail.bids.length === 0" class="empty-bids">
          {{ t('auction.noBids') }}
        </div>
        <ul v-else class="bid-list">
          <li
            v-for="b in detail.bids"
            :key="b.id"
            class="bid-item"
            :class="{ winning: b.is_winning }"
          >
            <span class="bid-amount">¥ {{ b.amount.toFixed(2) }}</span>
            <span class="bid-user">{{ shortSid(b.bidder_session_id) }}</span>
            <span class="bid-time">{{ formatTime(b.created_at || '') }}</span>
            <span v-if="b.is_winning" class="bid-tag">{{ t('auction.winning') }}</span>
          </li>
        </ul>
      </section>

      <section class="bid-section" v-if="detail.reviews.length > 0">
        <h2 class="section-title">{{ t('auction.reviews') }}</h2>
        <ul class="bid-list">
          <li v-for="r in detail.reviews" :key="r.id" class="bid-item review-item">
            <div class="review-stars">
              <span v-for="n in 5" :key="n" :class="{ on: n <= r.stars }">★</span>
            </div>
            <span class="bid-user">{{ shortSid(r.reviewer_session_id) }}</span>
            <span class="review-comment" v-if="r.comment">{{ r.comment }}</span>
          </li>
        </ul>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAuctionStore } from '@/stores/auction'
import { useI18n } from '@/composables/useI18n'
import { useAppStore } from '@/stores/app'
import { getSessionId } from '@/utils/session'

const route = useRoute()
const { t } = useI18n()
const store = useAuctionStore()
const app = useAppStore()

const id = computed(() => Number(route.params.id))
const detail = computed(() => store.currentDetail)
const bidAmount = ref(0)
const bidding = ref(false)
const reviewStars = ref(0)
const reviewComment = ref('')

const minBid = computed(() => {
  if (!detail.value) return 0
  return detail.value.auction.current_price + detail.value.auction.min_increment
})

const isWinner = computed(() => {
  if (!detail.value) return false
  return detail.value.auction.winner_session_id === getSessionId()
})

function statusLabel(s: string) {
  return t(`auction.status.${s}`)
}

function formatTime(s: string): string {
  if (!s) return '-'
  const d = new Date(s)
  if (isNaN(d.getTime())) return '-'
  return d.toLocaleString()
}

function shortSid(sid: string) {
  if (!sid) return '?'
  return sid.length > 12 ? `${sid.slice(0, 6)}…${sid.slice(-4)}` : sid
}

async function onBid() {
  if (!detail.value) return
  if (bidAmount.value < minBid.value) {
    app.showToast('error', t('auction.bidTooLow', { n: minBid.value.toFixed(2) }))
    return
  }
  bidding.value = true
  try {
    await store.placeBid(detail.value.auction.id, bidAmount.value)
    app.showToast('success', t('auction.bidOk'))
    bidAmount.value = 0
  } catch (e: unknown) {
    const detail = (e as { response?: { data?: { detail?: string } } }).response?.data?.detail
    app.showToast('error', detail || t('auction.bidFail'))
  } finally {
    bidding.value = false
  }
}

async function onReview() {
  if (!detail.value) return
  try {
    await store.submitReview(detail.value.auction.id, reviewStars.value, reviewComment.value)
    app.showToast('success', t('auction.reviewOk'))
    reviewStars.value = 0
    reviewComment.value = ''
  } catch (e: unknown) {
    const detail = (e as { response?: { data?: { detail?: string } } }).response?.data?.detail
    app.showToast('error', detail || t('auction.reviewFail'))
  }
}

onMounted(() => store.loadDetail(id.value))
watch(id, (v) => v && store.loadDetail(v))
</script>

<style scoped>
.auction-detail-view {
  min-height: 100vh;
  padding: 24px 32px 60px;
  background: var(--bg-primary);
}
.page-header { margin-bottom: 18px; }
.back-link {
  font-size: 13px;
  color: var(--cyan-core);
  text-decoration: none;
  padding: 6px 14px;
  border: 1px solid var(--border-cyan);
  border-radius: var(--radius-full);
}
.state-block { text-align: center; padding: 80px 20px; }
.state-icon { font-size: 48px; opacity: 0.4; margin-bottom: 8px; }
.auction-panel {
  position: relative;
  padding: 24px;
  background: var(--bg-card);
  border: 1px solid var(--border-pink);
  border-radius: var(--radius-md);
  box-shadow: var(--glow-pink);
  margin-bottom: 24px;
}
.ac-status {
  position: absolute;
  top: 16px;
  right: 16px;
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 2px;
  padding: 3px 10px;
  border-radius: var(--radius-full);
  text-transform: uppercase;
}
.ac-status--active { color: var(--pink-core); background: rgba(255, 53, 243, 0.12); }
.ac-status--sold { color: var(--accent-gold); background: rgba(212, 168, 75, 0.15); }
.ac-status--expired { color: var(--text-muted); background: rgba(128, 128, 128, 0.15); }
.ac-status--cancelled { color: #ff8a8a; background: rgba(255, 107, 107, 0.12); }
.ad-title { font-family: var(--font-display); font-size: 28px; color: #fff; margin-bottom: 6px; }
.ad-desc { color: var(--text-muted); font-size: 14px; line-height: 1.6; margin-bottom: 16px; }
.ad-price-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}
.ad-label { font-family: var(--font-mono); font-size: 10px; color: var(--text-muted); letter-spacing: 1px; margin-bottom: 4px; }
.ad-price { font-family: var(--font-mono); font-size: 24px; color: var(--pink-core); font-weight: 700; }
.ad-price--cyan { color: var(--cyan-core); }
.ad-sub { font-family: var(--font-mono); font-size: 11px; color: var(--text-muted); }
.ad-time { font-family: var(--font-mono); font-size: 14px; color: var(--text-light); }
.ad-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.bid-input {
  flex: 1;
  min-width: 180px;
  padding: 10px 14px;
  background: var(--bg-input);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
  color: var(--text-light);
  font-family: var(--font-mono);
  font-size: 14px;
}
.bid-btn {
  padding: 10px 24px;
  background: rgba(255, 53, 243, 0.12);
  border: 1px solid var(--border-pink);
  border-radius: var(--radius-full);
  color: var(--pink-core);
  font-size: 14px;
  cursor: pointer;
}
.bid-btn:hover:not(:disabled) { background: rgba(255, 53, 243, 0.2); }
.bid-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.ad-review { width: 100%; display: flex; flex-direction: column; gap: 8px; }
.ad-stars { display: flex; gap: 6px; }
.ad-star {
  font-size: 22px;
  color: var(--text-muted);
  cursor: pointer;
  transition: color 0.2s;
}
.ad-star.active { color: var(--accent-gold); }
.ad-sold {
  margin-top: 14px;
  padding: 10px 16px;
  background: rgba(212, 168, 75, 0.1);
  border: 1px solid rgba(212, 168, 75, 0.3);
  border-radius: var(--radius-sm);
  color: var(--accent-gold);
  font-family: var(--font-mono);
  font-size: 13px;
}
.bid-section {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 20px;
  margin-bottom: 18px;
}
.section-title {
  font-family: var(--font-serif);
  font-size: 18px;
  color: var(--cyan-core);
  margin-bottom: 12px;
}
.empty-bids { padding: 20px; text-align: center; color: var(--text-muted); font-size: 13px; }
.bid-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; }
.bid-item {
  display: grid;
  grid-template-columns: 100px 1fr auto auto;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  background: var(--bg-input);
  border-radius: var(--radius-sm);
  font-size: 13px;
}
.bid-item.winning { border-left: 2px solid var(--pink-core); }
.bid-amount { font-family: var(--font-mono); color: var(--pink-core); font-weight: 700; }
.bid-user { font-family: var(--font-mono); color: var(--text-muted); font-size: 11px; }
.bid-time { font-family: var(--font-mono); color: var(--text-muted); font-size: 11px; }
.bid-tag { font-size: 10px; padding: 2px 8px; background: rgba(255, 53, 243, 0.12); color: var(--pink-core); border-radius: var(--radius-full); font-family: var(--font-mono); }
.review-item { grid-template-columns: auto 1fr 2fr; }
.review-stars { color: var(--text-muted); }
.review-stars .on { color: var(--accent-gold); }
.review-comment { color: var(--text-light); }
</style>
