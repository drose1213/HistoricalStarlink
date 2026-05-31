<template>
  <div
    class="champion-card"
    :class="`champion-card--${card.rarity}`"
    @click="$emit('click', card)"
  >
    <div class="card-glow"></div>

    <div class="card-header">
      <span class="cy-badge" :class="`cy-badge--${card.rarity}`">
        {{ rarityLabels[card.rarity] }}
      </span>
      <span class="card-id">#{{ String(card.id).padStart(4, '0') }}</span>
    </div>

    <div class="card-image-section">
      <div class="image-frame" :class="`image-frame--${card.rarity}`">
        <img
          v-if="card.image_url"
          :src="card.image_url"
          :alt="card.title"
          class="card-image"
        />
        <div v-else class="image-placeholder">
          <span class="placeholder-icon">◇</span>
        </div>
      </div>
    </div>

    <div class="card-body">
      <h3 class="card-title">{{ card.title }}</h3>
      <p class="card-subtitle" v-if="card.subtitle">{{ card.subtitle }}</p>
      <p class="card-description" v-if="card.description">{{ card.description }}</p>
    </div>

    <div class="card-attributes" v-if="Object.keys(card.attributes).length > 0">
      <div class="cy-divider"></div>
      <div class="attributes-grid">
        <div
          v-for="(value, key) in card.attributes"
          :key="key"
          class="attribute-item"
        >
          <span class="attribute-key">{{ key }}</span>
          <span class="attribute-value">{{ value }}</span>
        </div>
      </div>
    </div>

    <div class="card-footer">
      <span class="unlock-time" v-if="card.unlocked_at">
        解锁于 {{ formatDate(card.unlocked_at) }}
      </span>
      <span class="event-id">事件: {{ card.event_id }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ChampionCard } from '@/types'

defineProps<{
  card: ChampionCard
}>()

defineEmits<{
  click: [card: ChampionCard]
}>()

const rarityLabels: Record<string, string> = {
  common: '普通',
  rare: '稀有',
  epic: '史诗',
  legendary: '传说'
}

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getFullYear()}.${(d.getMonth() + 1).toString().padStart(2, '0')}.${d.getDate().toString().padStart(2, '0')}`
}
</script>

<style scoped>
.champion-card {
  position: relative;
  padding: 20px;
  background: var(--bg-card);
  border: 1px solid var(--border-cyan);
  border-radius: var(--radius-md);
  backdrop-filter: blur(10px);
  transition: all 0.3s;
  cursor: pointer;
  overflow: hidden;
}

.champion-card:hover {
  transform: translateY(-4px);
}

.card-glow {
  position: absolute;
  inset: 0;
  opacity: 0;
  transition: opacity 0.3s;
  pointer-events: none;
}

.champion-card:hover .card-glow {
  opacity: 1;
}

.champion-card--common {
  border-color: rgba(142, 164, 184, 0.3);
  box-shadow: 0 0 10px rgba(142, 164, 184, 0.15);
}

.champion-card--common:hover {
  border-color: rgba(142, 164, 184, 0.5);
  box-shadow: 0 0 20px rgba(142, 164, 184, 0.25);
}

.champion-card--rare {
  border-color: var(--border-cyan);
  box-shadow: var(--glow-cyan);
}

.champion-card--rare:hover {
  border-color: var(--cyan-core);
  box-shadow: var(--glow-cyan-strong);
}

.champion-card--rare .card-glow {
  background: radial-gradient(ellipse at 50% 0%, rgba(49, 247, 255, 0.1), transparent 70%);
}

.champion-card--epic {
  border-color: var(--border-pink);
  box-shadow: var(--glow-pink);
}

.champion-card--epic:hover {
  border-color: var(--pink-core);
  box-shadow: var(--glow-pink-strong);
}

.champion-card--epic .card-glow {
  background: radial-gradient(ellipse at 50% 0%, rgba(255, 53, 243, 0.1), transparent 70%);
}

.champion-card--legendary {
  border-color: rgba(212, 168, 75, 0.5);
  box-shadow: 0 0 18px rgba(212, 168, 75, 0.3);
  animation: legendary-shimmer 3s ease-in-out infinite;
}

.champion-card--legendary:hover {
  border-color: var(--accent-gold);
  box-shadow: 0 0 30px rgba(212, 168, 75, 0.5);
}

.champion-card--legendary .card-glow {
  background:
    radial-gradient(ellipse at 30% 0%, rgba(212, 168, 75, 0.15), transparent 50%),
    radial-gradient(ellipse at 70% 100%, rgba(255, 53, 243, 0.08), transparent 50%);
}

@keyframes legendary-shimmer {
  0%, 100% {
    box-shadow: 0 0 18px rgba(212, 168, 75, 0.3);
  }
  50% {
    box-shadow: 0 0 30px rgba(212, 168, 75, 0.5), 0 0 60px rgba(212, 168, 75, 0.2);
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.card-id {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-muted);
  letter-spacing: 1px;
}

.card-image-section {
  margin-bottom: 14px;
}

.image-frame {
  border-radius: var(--radius-sm);
  overflow: hidden;
  border: 2px solid var(--border-subtle);
  aspect-ratio: 16 / 10;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-input);
}

.image-frame--rare {
  border-color: var(--border-cyan);
  box-shadow: inset 0 0 15px rgba(49, 247, 255, 0.1);
}

.image-frame--epic {
  border-color: var(--border-pink);
  box-shadow: inset 0 0 15px rgba(255, 53, 243, 0.1);
}

.image-frame--legendary {
  border-color: rgba(212, 168, 75, 0.5);
  box-shadow: inset 0 0 15px rgba(212, 168, 75, 0.1);
}

.card-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
}

.placeholder-icon {
  font-size: 32px;
  color: var(--cyan-core);
  opacity: 0.3;
  text-shadow: 0 0 16px var(--cyan-core);
}

.card-body {
  margin-bottom: 12px;
}

.card-title {
  font-family: var(--font-serif);
  font-size: 16px;
  font-weight: 700;
  color: #ffffff;
  text-shadow: 0 0 8px rgba(255, 255, 255, 0.2);
  margin-bottom: 4px;
}

.champion-card--legendary .card-title {
  color: var(--accent-gold);
  text-shadow: 0 0 12px rgba(212, 168, 75, 0.5);
}

.card-subtitle {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 6px;
}

.card-description {
  font-size: 12px;
  color: var(--text-light);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.attributes-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
}

.attribute-item {
  display: flex;
  justify-content: space-between;
  padding: 4px 8px;
  background: var(--bg-input);
  border-radius: var(--radius-sm);
  font-size: 11px;
}

.attribute-key {
  color: var(--text-muted);
}

.attribute-value {
  font-family: var(--font-mono);
  color: var(--cyan-core);
  font-weight: 600;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  font-size: 10px;
  font-family: var(--font-mono);
  color: var(--text-muted);
}

.unlock-time {
  opacity: 0.7;
}

.event-id {
  opacity: 0.5;
}
</style>
