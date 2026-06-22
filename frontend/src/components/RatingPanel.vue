<template>
  <div class="rating-panel">
    <!-- 投票区 -->
    <div class="rp-section">
      <h3 class="cy-subtitle">
        <span class="header-icon">⬡</span>
        {{ t('ratingPanel.voteTitle') }}
      </h3>
      <div class="rp-vote-buttons">
        <button
          class="rp-vote-btn rp-vote-btn--agree"
          :class="{ 'rp-vote-btn--active': voteStore.myVote === 1 }"
          :disabled="voteStore.isLoading"
          @click="onVote('up')"
        >
          <span class="rp-vote-icon">▲</span>
          <span class="rp-vote-label">{{ t('ratingPanel.agree') }}</span>
          <span class="rp-vote-count">{{ voteStore.agreeCount }}</span>
        </button>
        <button
          class="rp-vote-btn rp-vote-btn--disagree"
          :class="{ 'rp-vote-btn--active': voteStore.myVote === -1 }"
          :disabled="voteStore.isLoading"
          @click="onVote('down')"
        >
          <span class="rp-vote-icon">▼</span>
          <span class="rp-vote-label">{{ t('ratingPanel.disagree') }}</span>
          <span class="rp-vote-count">{{ voteStore.disagreeCount }}</span>
        </button>
        <button
          class="rp-vote-btn rp-vote-btn--favorite"
          :class="{ 'rp-vote-btn--active': voteStore.myVote === 1 && favoriteToggled }"
          :disabled="voteStore.isLoading"
          @click="onVote('star')"
        >
          <span class="rp-vote-icon">★</span>
          <span class="rp-vote-label">{{ t('ratingPanel.favorite') }}</span>
          <span class="rp-vote-count">{{ voteStore.favoriteCount }}</span>
        </button>
      </div>
    </div>

    <!-- 评分区 -->
    <div class="rp-section">
      <h3 class="cy-subtitle">
        <span class="header-icon">✦</span>
        {{ t('ratingPanel.ratingTitle') }}
      </h3>
      <div class="rp-rating-display">
        <div class="rp-score-big">
          <span class="rp-score-num">{{ (ratingStore.averageData.average / 2).toFixed(1) }}</span>
          <span class="rp-score-max">/5</span>
        </div>
        <div class="rp-stars-row">
          <span
            v-for="i in 5"
            :key="i"
            class="rp-star"
            :class="{ 'rp-star--filled': i <= Math.round(ratingStore.averageData.average / 2) }"
            @click="submitScore(i * 2)"
            :title="t('ratingPanel.submitScore', { n: i })"
          >{{ i <= Math.round(ratingStore.averageData.average / 2) ? '★' : '☆' }}</span>
        </div>
        <span class="rp-rating-count">{{ t('ratingPanel.ratingCount', { n: ratingStore.averageData.count }) }}</span>
      </div>

      <!-- 分布柱状图 -->
      <div class="rp-distribution" v-if="ratingStore.distribution?.items?.length">
        <div
          v-for="bucket in ratingStore.distribution.items"
          :key="bucket.stars"
          class="rp-dist-row"
        >
          <span class="rp-dist-label">{{ bucket.stars }}★</span>
          <div class="rp-dist-bar-track">
            <div
              class="rp-dist-bar-fill"
              :style="{ width: distPercent(bucket.count) + '%' }"
            ></div>
          </div>
          <span class="rp-dist-count">{{ bucket.count }}</span>
        </div>
      </div>

      <!-- 趋势图 -->
      <div class="rp-trend" v-if="ratingStore.trend?.points?.length">
        <div class="rp-trend-header">
          <span class="rp-trend-label">{{ t('ratingPanel.trend7d') }}</span>
          <button class="rp-trend-toggle" @click="toggleTrendDays">{{ trendDays === 7 ? '30d' : '7d' }}</button>
        </div>
        <div class="rp-trend-chart">
          <div
            v-for="(p, idx) in ratingStore.trend.points"
            :key="idx"
            class="rp-trend-bar"
            :title="`${p.date}: ${p.avg_score.toFixed(2)} (${p.count} 评)`"
          >
            <div
              class="rp-trend-bar-fill"
              :style="{ height: trendHeight(p.avg_score) + '%' }"
            ></div>
            <span class="rp-trend-bar-label">{{ p.date.slice(5) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 提交评价 -->
    <div class="rp-section">
      <h3 class="cy-subtitle">
        <span class="header-icon">✎</span>
        {{ t('ratingPanel.reviewTitle') }}
      </h3>
      <div class="rp-review-form">
        <div class="rp-review-stars">
          <span
            v-for="i in 5"
            :key="i"
            class="rp-review-star"
            :class="{ 'rp-review-star--active': i <= (hoverScore || newStars) }"
            @mouseenter="hoverScore = i"
            @mouseleave="hoverScore = 0"
            @click="newStars = i"
          >{{ i <= (hoverScore || newStars) ? '★' : '☆' }}</span>
        </div>
        <textarea
          v-model="newComment"
          class="cy-textarea rp-review-textarea"
          :placeholder="t('ratingPanel.reviewPlaceholder')"
          rows="3"
          maxlength="500"
        ></textarea>
        <div class="rp-review-meta">
          <span :class="{ 'rp-review-meta--warn': newComment.length > 480 }">
            {{ newComment.length }} / 500
          </span>
          <button
            class="cy-btn cy-btn--cyan"
            :disabled="!canSubmit || reviewStore.submitting"
            @click="submitReview"
          >
            {{ reviewStore.submitting ? t('ratingPanel.submitting') : t('ratingPanel.submitReview') }}
          </button>
        </div>
      </div>
    </div>

    <!-- 评价列表 -->
    <div class="rp-section">
      <h3 class="cy-subtitle">
        <span class="header-icon">☷</span>
        {{ t('ratingPanel.reviewListTitle') }}
        <span class="rp-section-count">({{ reviewStore.total }})</span>
      </h3>

      <!-- 星级过滤 -->
      <div class="rp-filter-row">
        <button
          v-for="opt in filterOptions"
          :key="opt.label"
          class="rp-filter-chip"
          :class="{ 'rp-filter-chip--active': isFilterActive(opt) }"
          @click="applyFilter(opt)"
        >{{ opt.label }}</button>
      </div>

      <div v-if="reviewStore.isLoading" class="rp-loading">{{ t('ratingPanel.loading') }}</div>

      <div v-else-if="!reviewStore.reviews.length" class="rp-empty">
        {{ t('ratingPanel.emptyReviews') }}
      </div>

      <div v-else class="rp-review-list">
        <div
          v-for="r in reviewStore.reviews"
          :key="r.id"
          class="rp-review-item"
        >
          <div class="rp-review-head">
            <span class="rp-review-author">{{ r.reviewer_session_id }}</span>
            <span class="rp-review-stars-display">
              <span v-for="i in 5" :key="i">{{ i <= r.stars ? '★' : '☆' }}</span>
            </span>
            <span class="rp-review-time">{{ formatTime(r.created_at) }}</span>
          </div>
          <div class="rp-review-body" v-if="r.comment">{{ r.comment }}</div>
          <div class="rp-review-actions">
            <button
              class="rp-like-btn"
              :class="{ 'rp-like-btn--active': r.liked_by_me }"
              @click="onLike(r.id)"
            >
              {{ r.liked_by_me ? '♥' : '♡' }} {{ r.likes_count }}
            </button>
            <button class="rp-reply-btn" @click="toggleReply(r.id)">
              {{ t('ratingPanel.reply') }}
            </button>
          </div>
          <div v-if="replyTargetId === r.id" class="rp-reply-form">
            <textarea
              v-model="replyText"
              class="cy-textarea"
              :placeholder="t('ratingPanel.replyPlaceholder')"
              maxlength="500"
              rows="2"
            ></textarea>
            <div class="rp-review-meta">
              <span :class="{ 'rp-review-meta--warn': replyText.length > 480 }">
                {{ replyText.length }} / 500
              </span>
              <button
                class="cy-btn cy-btn--cyan"
                :disabled="!replyText.trim() || reviewStore.submitting"
                @click="submitReply(r.id)"
              >{{ t('ratingPanel.sendReply') }}</button>
            </div>
          </div>
          <!-- 嵌入回复 -->
          <div v-if="r.replies && r.replies.length" class="rp-replies">
            <div v-for="rp in r.replies" :key="rp.id" class="rp-reply-item">
              <span class="rp-review-author">{{ rp.reviewer_session_id }}：</span>
              <span class="rp-reply-stars">
                <span v-for="i in 5" :key="i">{{ i <= rp.stars ? '★' : '☆' }}</span>
              </span>
              <span class="rp-reply-comment">{{ rp.comment }}</span>
              <span class="rp-reply-time">{{ formatTime(rp.created_at) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRatingStore } from '@/stores/rating'
import { useVoteStore } from '@/stores/vote'
import { useReviewStore } from '@/stores/review'

const props = defineProps<{
  eventId: string
  cardId?: number
}>()

const { t } = useI18n()
const ratingStore = useRatingStore()
const voteStore = useVoteStore()
const reviewStore = useReviewStore()

// 评价表单
const newStars = ref(0)
const hoverScore = ref(0)
const newComment = ref('')
const replyTargetId = ref<number | null>(null)
const replyText = ref('')
const trendDays = ref(7)
const favoriteToggled = ref(false)

const canSubmit = computed(() => newStars.value > 0 && newComment.value.trim().length > 0)

const filterOptions = computed(() => [
  { label: t('ratingPanel.filterAll'), min: null, max: null },
  { label: '5★', min: 5, max: 5 },
  { label: '4★', min: 4, max: 4 },
  { label: '3★', min: 3, max: 3 },
  { label: '≤2★', min: null, max: 2 },
])

function isFilterActive(opt: { min: number | null; max: number | null }) {
  return reviewStore.minStars === opt.min && reviewStore.maxStars === opt.max
}

function applyFilter(opt: { min: number | null; max: number | null }) {
  reviewStore.setStarsFilter(opt.min, opt.max)
  if (props.cardId) {
    reviewStore.load(props.cardId)
  }
}

function distPercent(count: number): number {
  const items = ratingStore.distribution?.items || []
  const max = items.reduce((m, b) => Math.max(m, b.count), 0)
  if (max === 0) return 0
  return Math.round((count / max) * 100)
}

function trendHeight(avg: number): number {
  if (!avg) return 4
  return Math.max(8, Math.min(100, (avg / 10) * 100))
}

function toggleTrendDays() {
  trendDays.value = trendDays.value === 7 ? 30 : 7
  ratingStore.fetchTrend(props.eventId, trendDays.value)
}

function formatTime(t: string | null | undefined): string {
  if (!t) return ''
  const d = new Date(t)
  if (isNaN(d.getTime())) return ''
  return d.toLocaleString()
}

async function onVote(type: 'up' | 'down' | 'star') {
  await voteStore.submitVote(props.eventId, type as any, props.eventId)
  if (type === 'star') favoriteToggled.value = !favoriteToggled.value
}

async function submitScore(score: number) {
  await ratingStore.submitRating(props.eventId, score, undefined, props.eventId)
  if (props.cardId) await reviewStore.load(props.cardId)
}

async function submitReview() {
  if (!canSubmit.value || !props.cardId) return
  await reviewStore.create({
    card_id: props.cardId,
    stars: newStars.value,
    comment: newComment.value.trim(),
  })
  newStars.value = 0
  newComment.value = ''
  await reviewStore.load(props.cardId)
}

function toggleReply(id: number) {
  replyTargetId.value = replyTargetId.value === id ? null : id
  replyText.value = ''
}

async function submitReply(parentId: number) {
  if (!replyText.value.trim() || !props.cardId) return
  await reviewStore.create({
    card_id: props.cardId,
    stars: 5,
    comment: replyText.value.trim(),
    parent_review_id: parentId,
  })
  replyText.value = ''
  replyTargetId.value = null
  await reviewStore.load(props.cardId)
}

async function onLike(reviewId: number) {
  await reviewStore.toggleLike(reviewId)
}

onMounted(async () => {
  voteStore.resetLocal()
  await Promise.all([
    voteStore.fetchVoteStats(props.eventId),
    voteStore.fetchMyVote(props.eventId),
    ratingStore.fetchAverage(props.eventId),
    ratingStore.fetchDistribution(props.eventId),
    ratingStore.fetchTrend(props.eventId, 7),
  ])
  if (props.cardId) {
    await reviewStore.load(props.cardId)
  }
})

watch(() => props.eventId, async (newId) => {
  if (newId) {
    await voteStore.fetchVoteStats(newId)
    await ratingStore.fetchAverage(newId)
  }
})
</script>

<style scoped>
.rating-panel {
  display: flex;
  flex-direction: column;
  gap: 24px;
  color: #c8d8e8;
}

.rp-section {
  background: linear-gradient(180deg, rgba(8, 16, 32, 0.6), rgba(8, 16, 32, 0.3));
  border: 1px solid rgba(0, 229, 255, 0.18);
  border-radius: 12px;
  padding: 16px 18px;
  backdrop-filter: blur(6px);
}

.rp-section-count {
  font-size: 13px;
  color: #6c87a3;
  font-weight: normal;
  margin-left: 4px;
}

.rp-vote-buttons {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-top: 10px;
}

.rp-vote-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 8px;
  background: rgba(0, 229, 255, 0.06);
  border: 1px solid rgba(0, 229, 255, 0.2);
  color: #c8d8e8;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.rp-vote-btn:hover:not(:disabled) {
  background: rgba(0, 229, 255, 0.12);
  transform: translateY(-1px);
}

.rp-vote-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.rp-vote-btn--active {
  background: linear-gradient(135deg, rgba(0, 229, 255, 0.4), rgba(0, 229, 255, 0.2));
  border-color: #00e5ff;
  box-shadow: 0 0 12px rgba(0, 229, 255, 0.4);
  color: #00e5ff;
}

.rp-vote-icon {
  font-size: 18px;
}
.rp-vote-count {
  font-weight: 600;
  font-size: 14px;
  background: rgba(0, 0, 0, 0.3);
  padding: 2px 8px;
  border-radius: 999px;
}

/* 评分 */
.rp-rating-display {
  display: flex;
  align-items: center;
  gap: 16px;
  margin: 12px 0;
}
.rp-score-big {
  font-size: 32px;
  font-weight: 700;
  color: #ffd54f;
  display: flex;
  align-items: baseline;
  gap: 2px;
}
.rp-score-num { font-size: 36px; }
.rp-score-max { font-size: 16px; color: #6c87a3; }

.rp-stars-row { display: flex; gap: 2px; }
.rp-star {
  cursor: pointer;
  font-size: 22px;
  color: #455a72;
  transition: color 0.15s;
}
.rp-star--filled { color: #ffd54f; }

.rp-rating-count {
  color: #6c87a3;
  font-size: 13px;
}

/* 分布 */
.rp-distribution {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 10px;
}
.rp-dist-row {
  display: grid;
  grid-template-columns: 32px 1fr 36px;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}
.rp-dist-label { color: #ffd54f; }
.rp-dist-bar-track {
  background: rgba(0, 0, 0, 0.4);
  height: 8px;
  border-radius: 4px;
  overflow: hidden;
}
.rp-dist-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #00e5ff, #ffd54f);
  transition: width 0.4s;
}
.rp-dist-count { color: #c8d8e8; text-align: right; }

/* 趋势 */
.rp-trend {
  margin-top: 14px;
  border-top: 1px dashed rgba(0, 229, 255, 0.15);
  padding-top: 10px;
}
.rp-trend-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #6c87a3;
  margin-bottom: 6px;
}
.rp-trend-toggle {
  background: transparent;
  border: 1px solid rgba(0, 229, 255, 0.3);
  color: #00e5ff;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  cursor: pointer;
}
.rp-trend-chart {
  display: flex;
  align-items: flex-end;
  gap: 2px;
  height: 60px;
}
.rp-trend-bar {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  min-width: 0;
}
.rp-trend-bar-fill {
  width: 100%;
  background: linear-gradient(180deg, #00e5ff, #008cb3);
  border-radius: 2px 2px 0 0;
  transition: height 0.3s;
  min-height: 2px;
}
.rp-trend-bar-label {
  font-size: 9px;
  color: #6c87a3;
  writing-mode: vertical-rl;
  white-space: nowrap;
}

/* 评价表单 */
.rp-review-form {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 10px;
}
.rp-review-stars {
  display: flex;
  gap: 4px;
  font-size: 22px;
}
.rp-review-star {
  cursor: pointer;
  color: #455a72;
}
.rp-review-star--active {
  color: #ffd54f;
}
.rp-review-textarea {
  resize: vertical;
  min-height: 60px;
}
.rp-review-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #6c87a3;
}
.rp-review-meta--warn {
  color: #ff8a65;
}

/* 评价列表 */
.rp-filter-row {
  display: flex;
  gap: 6px;
  margin: 8px 0;
  flex-wrap: wrap;
}
.rp-filter-chip {
  background: transparent;
  border: 1px solid rgba(0, 229, 255, 0.2);
  color: #c8d8e8;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  cursor: pointer;
}
.rp-filter-chip--active {
  background: #00e5ff;
  color: #001722;
}

.rp-loading, .rp-empty {
  text-align: center;
  color: #6c87a3;
  padding: 20px;
  font-size: 13px;
}

.rp-review-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.rp-review-item {
  background: rgba(8, 16, 32, 0.5);
  border: 1px solid rgba(0, 229, 255, 0.1);
  border-radius: 8px;
  padding: 10px 12px;
}
.rp-review-head {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #6c87a3;
}
.rp-review-author {
  color: #00e5ff;
  font-weight: 600;
}
.rp-review-stars-display {
  color: #ffd54f;
}
.rp-review-time {
  margin-left: auto;
}
.rp-review-body {
  margin: 6px 0;
  font-size: 14px;
  line-height: 1.5;
  color: #e0eaf2;
}
.rp-review-actions {
  display: flex;
  gap: 12px;
  font-size: 12px;
}
.rp-like-btn, .rp-reply-btn {
  background: transparent;
  border: none;
  color: #6c87a3;
  cursor: pointer;
  font-size: 12px;
}
.rp-like-btn--active {
  color: #ff5a8a;
}
.rp-reply-form {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.rp-replies {
  margin-top: 8px;
  padding-left: 12px;
  border-left: 2px solid rgba(0, 229, 255, 0.2);
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.rp-reply-item {
  font-size: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.rp-reply-stars { color: #ffd54f; }
.rp-reply-comment { color: #c8d8e8; }
.rp-reply-time { color: #6c87a3; margin-left: auto; }
</style>
