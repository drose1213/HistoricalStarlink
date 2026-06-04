<template>
  <div class="voting-system">
    <div class="voting-header">
      <h3 class="cy-subtitle">
        <span class="header-icon">⬡</span>
        {{ t('rating.systemTitle') }}
      </h3>
    </div>

    <div class="voting-buttons">
      <button
        class="vote-btn vote-btn--up"
        :class="{ 'vote-btn--active': userVote === 'up' }"
        @click="handleVote('up')"
        :disabled="isLoading"
      >
        <span class="vote-icon">▲</span>
        <span class="vote-label">{{ t('rating.voteUp') }}</span>
        <span class="vote-count">{{ voteStats?.up_count || 0 }}</span>
      </button>

      <button
        class="vote-btn vote-btn--down"
        :class="{ 'vote-btn--active': userVote === 'down' }"
        @click="handleVote('down')"
        :disabled="isLoading"
      >
        <span class="vote-icon">▼</span>
        <span class="vote-label">{{ t('rating.voteDown') }}</span>
        <span class="vote-count">{{ voteStats?.down_count || 0 }}</span>
      </button>

      <button
        class="vote-btn vote-btn--star"
        :class="{ 'vote-btn--active': userVote === 'star' }"
        @click="handleVote('star')"
        :disabled="isLoading"
      >
        <span class="vote-icon">★</span>
        <span class="vote-label">{{ t('rating.voteStar') }}</span>
        <span class="vote-count">{{ voteStats?.star_count || 0 }}</span>
      </button>
    </div>

    <div class="voting-bar" v-if="totalVotes > 0">
      <div class="bar-track">
        <div
          class="bar-segment bar-segment--up"
          :style="{ width: upPercent + '%' }"
          v-if="upPercent > 0"
        >
          <span class="bar-label" v-if="upPercent > 15">{{ upPercent }}%</span>
        </div>
        <div
          class="bar-segment bar-segment--down"
          :style="{ width: downPercent + '%' }"
          v-if="downPercent > 0"
        >
          <span class="bar-label" v-if="downPercent > 15">{{ downPercent }}%</span>
        </div>
        <div
          class="bar-segment bar-segment--star"
          :style="{ width: starPercent + '%' }"
          v-if="starPercent > 0"
        >
          <span class="bar-label" v-if="starPercent > 15">{{ starPercent }}%</span>
        </div>
      </div>
      <div class="bar-legend">
        <span class="legend-item">
          <span class="legend-dot legend-dot--up"></span>
          {{ t('rating.voteUp') }} {{ upPercent }}%
        </span>
        <span class="legend-item">
          <span class="legend-dot legend-dot--down"></span>
          {{ t('rating.voteDown') }} {{ downPercent }}%
        </span>
        <span class="legend-item">
          <span class="legend-dot legend-dot--star"></span>
          {{ t('rating.voteStar') }} {{ starPercent }}%
        </span>
      </div>
    </div>

    <div class="voting-empty" v-else>
      <p class="empty-text">{{ t('rating.empty') }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
import { useVoteStore } from '@/stores/vote'
import { useAppStore } from '@/stores/app'
import { requireAuth } from '@/utils/auth'
import { useI18n } from '@/composables/useI18n'

const props = defineProps<{
  eventId: string
  eventName?: string
}>()

const voteStore = useVoteStore()
const appStore = useAppStore()
const { t } = useI18n()

const voteStats = computed(() => voteStore.voteStats)
const isLoading = computed(() => voteStore.isLoading)
const userVote = computed(() => voteStats.value?.user_vote || null)

const totalVotes = computed(() => {
  if (!voteStats.value) return 0
  return voteStats.value.up_count + voteStats.value.down_count + voteStats.value.star_count
})

const upPercent = computed(() => {
  if (totalVotes.value === 0) return 0
  return Math.round(((voteStats.value?.up_count || 0) / totalVotes.value) * 100)
})

const downPercent = computed(() => {
  if (totalVotes.value === 0) return 0
  return Math.round(((voteStats.value?.down_count || 0) / totalVotes.value) * 100)
})

const starPercent = computed(() => {
  if (totalVotes.value === 0) return 0
  return Math.round(((voteStats.value?.star_count || 0) / totalVotes.value) * 100)
})

async function handleVote(type: 'up' | 'down' | 'star') {
  try {
    await voteStore.submitVote(props.eventId, type, props.eventName)
    appStore.showToast('success', t('toast.voteOk'))
  } catch {
    appStore.showToast('error', t('toast.voteFail'))
  }
}

watch(() => props.eventId, async (id) => {
  if (id) {
    await voteStore.fetchVoteStats(id)
  }
}, { immediate: true })
</script>

<style scoped>
.voting-system {
  padding: 20px;
  background: var(--bg-card);
  border: 1px solid var(--border-cyan);
  border-radius: var(--radius-md);
  backdrop-filter: blur(10px);
  box-shadow: var(--glow-cyan);
}

.voting-header {
  margin-bottom: 16px;
}

.voting-header h3 {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-icon {
  color: var(--cyan-core);
  text-shadow: 0 0 10px var(--cyan-core);
  font-size: 18px;
}

.voting-buttons {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.vote-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px 8px;
  background: var(--bg-input);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  color: var(--text-muted);
  transition: all 0.2s;
  cursor: pointer;
}

.vote-btn:hover {
  border-color: var(--border-cyan);
  background: rgba(49, 247, 255, 0.08);
}

.vote-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.vote-btn--up:hover,
.vote-btn--up.vote-btn--active {
  border-color: var(--cyan-core);
  color: var(--cyan-core);
  box-shadow: 0 0 12px rgba(49, 247, 255, 0.3);
}

.vote-btn--down:hover,
.vote-btn--down.vote-btn--active {
  border-color: var(--pink-core);
  color: var(--pink-core);
  box-shadow: 0 0 12px rgba(255, 53, 243, 0.3);
}

.vote-btn--star:hover,
.vote-btn--star.vote-btn--active {
  border-color: var(--accent-gold);
  color: var(--accent-gold);
  box-shadow: 0 0 12px rgba(212, 168, 75, 0.3);
}

.vote-btn--active {
  background: rgba(49, 247, 255, 0.1);
}

.vote-icon {
  font-size: 18px;
}

.vote-label {
  font-size: 11px;
  letter-spacing: 0.5px;
}

.vote-count {
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 600;
}

.bar-track {
  display: flex;
  height: 8px;
  border-radius: 4px;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.3);
  margin-bottom: 10px;
}

.bar-segment {
  display: flex;
  align-items: center;
  justify-content: center;
  transition: width 0.4s ease;
  position: relative;
}

.bar-segment--up {
  background: linear-gradient(90deg, var(--cyan-core), rgba(49, 247, 255, 0.7));
  box-shadow: 0 0 6px var(--cyan-core);
}

.bar-segment--down {
  background: linear-gradient(90deg, rgba(255, 53, 243, 0.7), var(--pink-core));
  box-shadow: 0 0 6px var(--pink-core);
}

.bar-segment--star {
  background: linear-gradient(90deg, rgba(212, 168, 75, 0.7), var(--accent-gold));
  box-shadow: 0 0 6px var(--accent-gold);
}

.bar-label {
  font-size: 8px;
  color: #fff;
  font-weight: 700;
  position: absolute;
  white-space: nowrap;
}

.bar-legend {
  display: flex;
  justify-content: center;
  gap: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  color: var(--text-muted);
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.legend-dot--up {
  background: var(--cyan-core);
  box-shadow: 0 0 6px var(--cyan-core);
}

.legend-dot--down {
  background: var(--pink-core);
  box-shadow: 0 0 6px var(--pink-core);
}

.legend-dot--star {
  background: var(--accent-gold);
  box-shadow: 0 0 6px var(--accent-gold);
}

.voting-empty {
  text-align: center;
  padding: 20px;
}

.empty-text {
  font-size: 12px;
  color: var(--text-muted);
}
</style>
