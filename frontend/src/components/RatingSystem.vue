<template>
  <div class="rating-system">
    <div class="rating-header">
      <h3 class="cy-subtitle">
        <span class="header-icon">★</span>
        评分系统
      </h3>
    </div>

    <div class="rating-display">
      <div class="rating-stars">
        <div class="average-score">
          <span class="score-number">{{ averageData.average.toFixed(1) }}</span>
          <span class="score-max">/5</span>
        </div>
        <div class="stars-row">
          <span
            v-for="i in 5"
            :key="i"
            class="star"
            :class="{
              'star--filled': i <= Math.round(averageData.average),
              'star--user': i <= (userRating?.score || 0)
            }"
            @click="setRating(i)"
          >
            {{ i <= displayScore ? '★' : '☆' }}
          </span>
        </div>
        <span class="rating-count">{{ averageData.count }} 次评分</span>
      </div>
    </div>

    <div class="rating-input" v-if="showInput">
      <div class="input-score">
        <span
          v-for="i in 5"
          :key="i"
          class="score-star"
          :class="{ 'score-star--active': i <= hoverScore }"
          @mouseenter="hoverScore = i"
          @mouseleave="hoverScore = 0"
          @click="selectedScore = i"
        >
          {{ i <= (hoverScore || selectedScore) ? '★' : '☆' }}
        </span>
        <span class="score-label" v-if="selectedScore > 0">
          {{ scoreLabels[selectedScore - 1] }}
        </span>
      </div>

      <textarea
        v-model="comment"
        class="cy-textarea"
        placeholder="留下你的评价..."
        rows="3"
      ></textarea>

      <div class="input-actions">
        <button
          class="cy-btn cy-btn--gold"
          :disabled="selectedScore === 0 || isSubmitting"
          @click="handleSubmit"
        >
          {{ isSubmitting ? '提交中...' : '提交评分' }}
        </button>
        <button
          v-if="userRating"
          class="cy-btn"
          @click="showInput = false"
        >
          取消
        </button>
      </div>
    </div>

    <button
      v-else
      class="cy-btn add-rating-btn"
      @click="showInput = true"
    >
      {{ userRating ? '修改评分' : '添加评分' }}
    </button>

    <div class="recent-ratings" v-if="ratings.length > 0">
      <div class="cy-divider"></div>
      <h4 class="recent-title">近期评价</h4>
      <div class="ratings-list">
        <div v-for="rating in ratings" :key="rating.id" class="rating-item">
          <div class="rating-item-header">
            <div class="rating-item-stars">
              <span v-for="i in 5" :key="i" class="mini-star">
                {{ i <= rating.score ? '★' : '☆' }}
              </span>
            </div>
            <span class="rating-item-time">{{ formatTime(rating.created_at) }}</span>
          </div>
          <p class="rating-item-comment" v-if="rating.comment">{{ rating.comment }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRatingStore } from '@/stores/rating'
import { useAppStore } from '@/stores/app'
import { requireAuth } from '@/utils/auth'

const props = defineProps<{
  eventId: string
  eventName?: string
}>()

const ratingStore = useRatingStore()
const appStore = useAppStore()

const showInput = ref(false)
const selectedScore = ref(0)
const hoverScore = ref(0)
const comment = ref('')
const isSubmitting = ref(false)

const scoreLabels = ['很差', '较差', '一般', '较好', '很好']

const averageData = computed(() => ratingStore.averageData)
const userRating = computed(() => ratingStore.userRating)
const ratings = computed(() => ratingStore.ratings)

const displayScore = computed(() => {
  if (hoverScore.value > 0) return hoverScore.value
  if (selectedScore.value > 0) return selectedScore.value
  return Math.round(averageData.value.average)
})

function formatTime(dateStr: string): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:${d.getMinutes().toString().padStart(2, '0')}`
}

function setRating(score: number) {
  selectedScore.value = score
  showInput.value = true
}

async function handleSubmit() {
  if (!requireAuth()) return
  if (selectedScore.value === 0) return
  isSubmitting.value = true
  try {
    await ratingStore.submitRating(props.eventId, selectedScore.value, comment.value || undefined, props.eventName)
    showInput.value = false
    selectedScore.value = 0
    comment.value = ''
    appStore.showToast('success', '评分已提交')
  } catch {
    appStore.showToast('error', '评分提交失败')
  } finally {
    isSubmitting.value = false
  }
}

watch(() => props.eventId, async (id) => {
  if (id) {
    await ratingStore.fetchAverage(id)
    await ratingStore.fetchUserRating(id)
    await ratingStore.fetchRatingsByEvent(id)
  }
}, { immediate: true })
</script>

<style scoped>
.rating-system {
  padding: 20px;
  background: var(--bg-card);
  border: 1px solid var(--border-pink);
  border-radius: var(--radius-md);
  backdrop-filter: blur(10px);
  box-shadow: var(--glow-pink);
}

.rating-header {
  margin-bottom: 16px;
}

.rating-header h3 {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-icon {
  color: var(--accent-gold);
  text-shadow: 0 0 10px rgba(212, 168, 75, 0.6);
  font-size: 18px;
}

.rating-display {
  text-align: center;
  margin-bottom: 16px;
}

.average-score {
  margin-bottom: 8px;
}

.score-number {
  font-family: var(--font-display);
  font-size: 36px;
  font-weight: 700;
  color: var(--accent-gold);
  text-shadow: 0 0 20px rgba(212, 168, 75, 0.6);
}

.score-max {
  font-size: 14px;
  color: var(--text-muted);
}

.stars-row {
  display: flex;
  justify-content: center;
  gap: 6px;
  margin-bottom: 6px;
}

.star {
  font-size: 22px;
  color: rgba(142, 164, 184, 0.3);
  cursor: pointer;
  transition: all 0.15s;
}

.star--filled {
  color: var(--accent-gold);
  text-shadow: 0 0 8px rgba(212, 168, 75, 0.5);
}

.star--user {
  color: var(--pink-core);
  text-shadow: 0 0 8px var(--pink-soft);
}

.star:hover {
  transform: scale(1.2);
}

.rating-count {
  font-size: 11px;
  color: var(--text-muted);
}

.rating-input {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.input-score {
  display: flex;
  align-items: center;
  gap: 6px;
  justify-content: center;
}

.score-star {
  font-size: 28px;
  color: rgba(142, 164, 184, 0.3);
  cursor: pointer;
  transition: all 0.15s;
}

.score-star--active {
  color: var(--accent-gold);
  text-shadow: 0 0 12px rgba(212, 168, 75, 0.7);
}

.score-label {
  font-size: 13px;
  color: var(--accent-gold);
  margin-left: 8px;
}

.input-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
}

.add-rating-btn {
  display: block;
  margin: 0 auto 16px;
}

.recent-title {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 12px;
  letter-spacing: 1px;
}

.ratings-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 200px;
  overflow-y: auto;
}

.rating-item {
  padding: 10px 12px;
  background: var(--bg-input);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-subtle);
}

.rating-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.rating-item-stars {
  display: flex;
  gap: 2px;
}

.mini-star {
  font-size: 12px;
  color: var(--accent-gold);
}

.rating-item-time {
  font-size: 10px;
  font-family: var(--font-mono);
  color: var(--text-muted);
}

.rating-item-comment {
  font-size: 12px;
  color: var(--text-light);
  line-height: 1.5;
}
</style>
