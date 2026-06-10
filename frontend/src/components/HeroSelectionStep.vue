<template>
  <div class="hero-selection">
    <div class="hero-selection__header">
      <h3 class="hero-selection__title">选择与你对话的历史人物</h3>
      <p class="hero-selection__hint">话题: <strong>{{ topic }}</strong></p>
      <p class="hero-selection__subhint">
        <span v-if="source === 'llm'">AI 推荐</span>
        <span v-else-if="source === 'fallback'">推荐</span>
        <span v-else>暂无推荐人物</span>
      </p>
    </div>

    <div v-if="loading" class="hero-selection__loading">
      <div class="cy-loading"></div>
      <span>正在寻找最合适的历史人物...</span>
    </div>

    <div v-else-if="heroes.length === 0" class="hero-selection__empty">
      <p>未找到匹配的历史人物</p>
      <button class="cy-btn cy-btn--glow" @click="$emit('skip')">
        使用默认时空对话机
      </button>
    </div>

    <div v-else class="hero-selection__cards">
      <div
        v-for="hero in heroes"
        :key="hero.hero_id"
        class="hero-card"
        @click="selectHero(hero)"
      >
        <div class="hero-card__glow"></div>
        <div class="hero-card__header">
          <span class="hero-card__era">{{ hero.era }}</span>
        </div>
        <div class="hero-card__avatar">
          <span class="hero-card__symbol">✦</span>
        </div>
        <div class="hero-card__body">
          <h4 class="hero-card__name">{{ hero.name }}</h4>
          <p class="hero-card__role">{{ hero.role }}</p>
        </div>
        <div class="hero-card__greeting">
          <p>{{ hero.greeting }}</p>
        </div>
        <div class="hero-card__description">
          <p>{{ hero.description }}</p>
        </div>
        <button class="cy-btn cy-btn--glow hero-card__action">
          与 TA 对话
        </button>
      </div>

      <div class="hero-card hero-card--skip" @click="$emit('skip')">
        <div class="hero-card__glow"></div>
        <div class="hero-card__avatar">
          <span class="hero-card__symbol">✦</span>
        </div>
        <div class="hero-card__body">
          <h4 class="hero-card__name">时空对话机</h4>
          <p class="hero-card__role">全知观测者</p>
        </div>
        <div class="hero-card__greeting">
          <p>让我作为通用历史助手与你对话</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { resolveHero, type HeroPersona } from '../api/dialogue'

const props = defineProps<{
  topic: string
}>()

const emit = defineEmits<{
  (e: 'select', hero: HeroPersona): void
  (e: 'skip'): void
}>()

const heroes = ref<HeroPersona[]>([])
const source = ref<string>('')
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const result = await resolveHero(props.topic)
    heroes.value = result.data.heroes
    source.value = result.data.source
  } catch (e) {
    console.error('resolveHero failed:', e)
    heroes.value = []
  } finally {
    loading.value = false
  }
})

function selectHero(hero: HeroPersona) {
  emit('select', hero)
}
</script>

<style scoped>
.hero-selection {
  padding: 24px;
  background: rgba(0, 10, 30, 0.85);
  border: 1px solid rgba(0, 200, 255, 0.3);
  border-radius: 12px;
  backdrop-filter: blur(12px);
}

.hero-selection__header {
  text-align: center;
  margin-bottom: 24px;
}

.hero-selection__title {
  color: #00d4ff;
  font-size: 1.4rem;
  margin: 0 0 8px 0;
}

.hero-selection__hint {
  color: #ffffff;
  font-size: 1rem;
  margin: 4px 0;
}

.hero-selection__subhint {
  color: rgba(0, 200, 255, 0.7);
  font-size: 0.85rem;
  margin: 4px 0;
}

.hero-selection__loading,
.hero-selection__empty {
  text-align: center;
  padding: 40px 20px;
  color: rgba(255, 255, 255, 0.7);
}

.hero-selection__cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.hero-card {
  position: relative;
  background: linear-gradient(135deg, rgba(0, 30, 60, 0.9), rgba(0, 60, 100, 0.7));
  border: 1px solid rgba(0, 200, 255, 0.4);
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  overflow: hidden;
}

.hero-card:hover {
  transform: translateY(-4px);
  border-color: rgba(0, 255, 200, 0.8);
  box-shadow: 0 8px 24px rgba(0, 200, 255, 0.3);
}

.hero-card__glow {
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(0, 200, 255, 0.1), transparent 60%);
  pointer-events: none;
}

.hero-card__era {
  display: inline-block;
  padding: 4px 8px;
  background: rgba(0, 200, 255, 0.2);
  border: 1px solid rgba(0, 200, 255, 0.4);
  border-radius: 4px;
  font-size: 0.75rem;
  color: #00d4ff;
}

.hero-card__avatar {
  text-align: center;
  margin: 16px 0;
  font-size: 3rem;
  color: rgba(0, 200, 255, 0.5);
}

.hero-card__name {
  font-size: 1.4rem;
  color: #ffffff;
  margin: 8px 0 4px 0;
  text-align: center;
}

.hero-card__role {
  text-align: center;
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
  margin: 0 0 12px 0;
}

.hero-card__greeting,
.hero-card__description {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.6);
  line-height: 1.5;
  margin: 8px 0;
}

.hero-card__greeting p,
.hero-card__description p {
  margin: 0;
  font-style: italic;
}

.hero-card__action {
  width: 100%;
  margin-top: 12px;
}

.hero-card--skip {
  background: linear-gradient(135deg, rgba(30, 30, 40, 0.9), rgba(50, 50, 60, 0.7));
  border-color: rgba(150, 150, 150, 0.4);
}
</style>