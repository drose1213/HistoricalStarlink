<template>
  <div class="landing-view">
    <div class="landing-stars" aria-hidden="true"></div>
    <div class="landing-grid" aria-hidden="true"></div>

    <!-- 屏 1: Hero -->
    <section class="landing-hero">
      <div class="hero-inner">
        <div class="hero-badge">
          <span class="hero-badge-dot" aria-hidden="true"></span>
          <span>AI × 历史剧本</span>
        </div>
        <h1 class="hero-title">让嬴政教你学秦制</h1>
        <p class="hero-slogan">
          AI × 真实历史剧本，4 维画像 × 因果星链，让学习像穿越
        </p>
        <button
          type="button"
          class="hero-cta"
          :disabled="ctaLoading"
          @click="handleCtaClick"
        >
          <span v-if="!ctaLoading" class="hero-cta-text">{{ ctaText }}</span>
          <span v-else class="hero-cta-loading">
            <span class="cta-spinner" aria-hidden="true"></span>
            <span>准备时空入口...</span>
          </span>
          <span class="hero-cta-arrow" v-if="!ctaLoading" aria-hidden="true">→</span>
        </button>
        <p v-if="heroError" class="hero-error">{{ heroError }}</p>
      </div>
    </section>

    <!-- 屏 2: 特性卡 -->
    <section class="landing-features">
      <div class="features-inner">
        <h2 class="features-heading">
          <span class="features-heading-line" aria-hidden="true"></span>
          核心特性
          <span class="features-heading-line" aria-hidden="true"></span>
        </h2>
        <div class="features-grid">
          <article
            v-for="(card, idx) in featureCards"
            :key="card.title"
            class="feature-card"
            :class="`feature-card--${idx % 3}`"
          >
            <div class="feature-card-glow" aria-hidden="true"></div>
            <div class="feature-card-icon" aria-hidden="true">{{ card.icon }}</div>
            <h3 class="feature-card-title">{{ card.title }}</h3>
            <p class="feature-card-desc">{{ card.desc }}</p>
            <div class="feature-card-tag">{{ card.tag }}</div>
          </article>
        </div>
      </div>
    </section>

    <!-- 屏 3: 反馈表单 -->
    <section class="landing-feedback">
      <div class="feedback-inner">
        <h2 class="feedback-heading">留下你的反馈</h2>
        <p class="feedback-sub">告诉我们体验如何, 帮助我们持续改进</p>

        <form class="feedback-form" @submit.prevent="handleFeedbackSubmit">
          <div class="rating-row">
            <span class="rating-label">评分</span>
            <div class="rating-stars" role="radiogroup" aria-label="1-5 星评分">
              <button
                v-for="star in 5"
                :key="star"
                type="button"
                class="rating-star"
                :class="{ 'rating-star--active': star <= selectedRating }"
                :aria-label="`${star} 星`"
                :aria-pressed="star <= selectedRating"
                @click="selectedRating = star"
                @mouseenter="hoverRating = star"
                @mouseleave="hoverRating = 0"
              >
                <span aria-hidden="true">★</span>
              </button>
            </div>
            <span class="rating-value">{{ ratingLabel }}</span>
          </div>

          <div class="feedback-textarea-wrap">
            <textarea
              v-model="feedbackComment"
              class="feedback-textarea"
              placeholder="说点什么吧 (可选, 最多 200 字)"
              maxlength="200"
              rows="4"
            ></textarea>
            <span class="feedback-counter">{{ feedbackComment.length }} / 200</span>
          </div>

          <div class="feedback-actions">
            <button
              type="submit"
              class="feedback-submit"
              :disabled="!selectedRating || submitting"
            >
              <span v-if="!submitting">提交反馈</span>
              <span v-else>提交中...</span>
            </button>
            <Transition name="toast-fade">
              <span v-if="feedbackToast" class="feedback-toast" role="status">
                <span class="feedback-toast-dot" aria-hidden="true"></span>
                {{ feedbackToast }}
              </span>
            </Transition>
          </div>
        </form>
      </div>
    </section>

    <a
      class="landing-signature"
      href="https://deerflow.tech"
      target="_blank"
      rel="noopener noreferrer"
    >
      Created By Deerflow
    </a>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onBeforeUnmount, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useDialogueStore } from '@/stores/dialogue'
import { trackEvent } from '@/utils/analytics'
import { decodeTopic } from '@/utils/shareLink'

const router = useRouter()
const dialogueStore = useDialogueStore()

const shareTopic = ref<string | null>(null)
const ctaLoading = ref(false)
const heroError = ref('')

const selectedRating = ref(0)
const hoverRating = ref(0)
const feedbackComment = ref('')
const submitting = ref(false)
const feedbackToast = ref('')
let toastTimer: ReturnType<typeof setTimeout> | null = null

interface FeatureCard {
  icon: string
  title: string
  desc: string
  tag: string
}

const featureCards: FeatureCard[] = [
  {
    icon: '🔮',
    title: '任意话题时空对话',
    desc: '输入任何话题，RAG 实时生成深度历史脉络',
    tag: 'RAG · 实时生成',
  },
  {
    icon: '🧬',
    title: '4 维用户画像',
    desc: '改革/保守/共情/激进 4 维度，每轮选择都改变结局',
    tag: '四维人格 · 命运分支',
  },
  {
    icon: '🌌',
    title: '因果星链图谱',
    desc: '50+ 跨文明事件，事件之间因果链可视化',
    tag: '50+ 节点 · 因果可视化',
  },
]

const ratingLabel = computed(() => {
  const v = hoverRating.value || selectedRating.value
  if (!v) return '点击评分'
  return ['', '极差', '一般', '不错', '推荐', '惊艳'][v] || '点击评分'
})

const ctaText = computed(() => {
  const t = shareTopic.value
  if (t) {
    const display = t.length > 18 ? `${t.slice(0, 18)}…` : t
    return `立即探索: ${display}`
  }
  return '立即体验'
})

function slugifyDynamicTopic(topic: string): string {
  // 与 HomeView / dialogue store 一致: [^\w一-龥]+ -> _ , slice(0, 32)
  return topic.replace(/[^\w一-龥]+/g, '_').slice(0, 32) || 'unknown'
}

async function handleCtaClick() {
  if (ctaLoading.value) return
  heroError.value = ''
  const topic = shareTopic.value
  ctaLoading.value = true
  try {
    if (topic && topic.trim()) {
      // dynamic 模式: 通过 store 启动, 然后路由到 /dialogue/dynamic_<slug>
      try {
        await dialogueStore.startDynamicFromTopic(topic)
      } catch (err) {
        // 即使启动失败, 仍然跳转到对话页让 DialogueExplorer 展示错误
        // (与 HomeView.handleFreeExplore 行为保持一致)
      }
      const slug = slugifyDynamicTopic(topic.trim())
      router.push({ name: 'Dialogue', params: { eventId: `dynamic_${slug}` } })
    } else {
      // 无 topic: 路由到 / 让用户从主入口选择
      router.push({ name: 'Home' })
    }
  } finally {
    ctaLoading.value = false
  }
}

async function handleFeedbackSubmit() {
  if (!selectedRating.value || submitting.value) return
  submitting.value = true
  try {
    await trackEvent('feedback_submitted', {
      rating: selectedRating.value,
      comment: feedbackComment.value.trim(),
      topic: shareTopic.value || 'unknown',
    })
    feedbackToast.value = '感谢反馈！我们将用于改进'
    selectedRating.value = 0
    hoverRating.value = 0
    feedbackComment.value = ''
    if (toastTimer) clearTimeout(toastTimer)
    toastTimer = setTimeout(() => {
      feedbackToast.value = ''
    }, 3000)
  } finally {
    submitting.value = false
  }
}

function decodeShareTopicFromHash(): string | null {
  if (typeof window === 'undefined') return null
  try {
    const hash = window.location.hash || ''
    let encoded: string | null = null
    if (hash.includes('?')) {
      const qs = hash.slice(hash.indexOf('?') + 1)
      encoded = new URLSearchParams(qs).get('d')
    }
    if (!encoded) {
      encoded = new URLSearchParams(window.location.search).get('d')
    }
    if (!encoded) return null
    return decodeTopic(encoded) || null
  } catch (_) {
    return null
  }
}

function onHashChange() {
  shareTopic.value = decodeShareTopicFromHash()
}

onMounted(() => {
  shareTopic.value = decodeShareTopicFromHash()
  // hash 路由下, 同一个 LandingView 实例可能在 hash 变化时复用, 监听 hashchange 同步
  if (typeof window !== 'undefined') {
    window.addEventListener('hashchange', onHashChange)
  }
})

onBeforeUnmount(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('hashchange', onHashChange)
  }
})
</script>

<style scoped>
.landing-view {
  position: relative;
  width: 100%;
  min-height: 100vh;
  overflow-x: hidden;
  overflow-y: auto;
  background: #02050b;
  display: flex;
  flex-direction: column;
}

/* ===== 装饰背景: 星空 + 网格 ===== */
.landing-stars,
.landing-grid {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.landing-stars {
  background:
    radial-gradient(1px 1px at 20% 30%, rgba(139, 255, 225, 0.7), transparent 50%),
    radial-gradient(1px 1px at 70% 60%, rgba(73, 247, 255, 0.6), transparent 50%),
    radial-gradient(1.5px 1.5px at 40% 80%, rgba(255, 255, 255, 0.7), transparent 50%),
    radial-gradient(1px 1px at 85% 25%, rgba(255, 104, 184, 0.55), transparent 50%),
    radial-gradient(1px 1px at 10% 70%, rgba(139, 255, 225, 0.55), transparent 50%),
    radial-gradient(1px 1px at 55% 18%, rgba(255, 255, 255, 0.6), transparent 50%),
    radial-gradient(1.5px 1.5px at 92% 88%, rgba(73, 247, 255, 0.5), transparent 50%);
  background-size: 600px 600px;
  background-repeat: repeat;
  animation: landing-star-drift 60s linear infinite;
  opacity: 0.85;
}

.landing-grid {
  background-image:
    linear-gradient(rgba(49, 247, 255, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(49, 247, 255, 0.05) 1px, transparent 1px);
  background-size: 60px 60px;
  mask-image: radial-gradient(ellipse at 50% 50%, rgba(0, 0, 0, 0.7), transparent 75%);
  -webkit-mask-image: radial-gradient(ellipse at 50% 50%, rgba(0, 0, 0, 0.7), transparent 75%);
}

@keyframes landing-star-drift {
  from { background-position: 0 0; }
  to { background-position: 600px 600px; }
}

section {
  position: relative;
  z-index: 1;
}

/* ===== 屏 1: Hero ===== */
.landing-hero {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 24px;
}

.hero-inner {
  width: min(720px, 100%);
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 22px;
  animation: hero-fade-in 0.7s ease both;
}

@keyframes hero-fade-in {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
  background: rgba(2, 6, 13, 0.6);
  border: 1px solid rgba(139, 255, 225, 0.55);
  border-radius: 999px;
  color: rgba(238, 249, 255, 0.86);
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-shadow: 0 0 10px rgba(139, 255, 225, 0.32);
  backdrop-filter: blur(8px);
}

.hero-badge-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #8bffe1;
  box-shadow: 0 0 12px rgba(139, 255, 225, 0.95);
  animation: hero-pulse 2.4s ease-in-out infinite;
}

@keyframes hero-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.55; transform: scale(0.85); }
}

.hero-title {
  margin: 0;
  color: #ffffff;
  font-family: var(--font-serif);
  font-size: clamp(40px, 7vw, 84px);
  font-weight: 900;
  line-height: 1.05;
  letter-spacing: 0;
  text-shadow:
    0 0 24px rgba(65, 166, 255, 0.38),
    0 2px 18px rgba(0, 0, 0, 0.7);
}

.hero-slogan {
  margin: 0;
  max-width: 560px;
  color: rgba(226, 246, 255, 0.78);
  font-size: clamp(15px, 1.8vw, 18px);
  line-height: 1.7;
  text-shadow: 0 2px 12px rgba(0, 0, 0, 0.7);
}

.hero-cta {
  margin-top: 8px;
  min-height: 52px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 0 32px;
  background: linear-gradient(180deg, rgba(139, 255, 225, 0.32), rgba(139, 255, 225, 0.12));
  border: 1px solid rgba(139, 255, 225, 0.85);
  border-radius: 999px;
  color: #f3fff9;
  font-family: var(--font-mono);
  font-size: 15px;
  font-weight: 800;
  letter-spacing: 0.08em;
  cursor: pointer;
  box-shadow: 0 0 28px rgba(139, 255, 225, 0.32);
  transition: background 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}

.hero-cta:hover:not(:disabled) {
  background: linear-gradient(180deg, rgba(139, 255, 225, 0.5), rgba(139, 255, 225, 0.2));
  box-shadow: 0 0 36px rgba(139, 255, 225, 0.55);
  transform: translateY(-2px);
}

.hero-cta:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.hero-cta-text {
  text-shadow: 0 0 12px rgba(139, 255, 225, 0.55);
}

.hero-cta-arrow {
  font-size: 18px;
  transition: transform 0.2s ease;
}

.hero-cta:hover:not(:disabled) .hero-cta-arrow {
  transform: translateX(3px);
}

.hero-cta-loading {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.cta-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(139, 255, 225, 0.3);
  border-top-color: #8bffe1;
  border-radius: 50%;
  animation: hero-spin 0.85s linear infinite;
}

@keyframes hero-spin {
  to { transform: rotate(360deg); }
}

.hero-error {
  margin: 0;
  color: #ff8a4d;
  font-size: 13px;
  text-shadow: 0 0 8px rgba(255, 138, 77, 0.4);
}

/* ===== 屏 2: 特性卡 ===== */
.landing-features {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 24px;
}

.features-inner {
  width: min(1080px, 100%);
  display: flex;
  flex-direction: column;
  gap: 40px;
  align-items: center;
}

.features-heading {
  display: flex;
  align-items: center;
  gap: 14px;
  margin: 0;
  color: #ffffff;
  font-family: var(--font-display);
  font-size: clamp(18px, 2.4vw, 26px);
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  text-shadow: 0 0 16px rgba(49, 247, 255, 0.55);
}

.features-heading-line {
  display: inline-block;
  width: clamp(40px, 12vw, 110px);
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--cyan-core), transparent);
  opacity: 0.6;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 22px;
  width: 100%;
}

.feature-card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 28px 24px;
  background: rgba(10, 15, 24, 0.7);
  border: 1px solid rgba(139, 255, 225, 0.42);
  border-radius: 12px;
  backdrop-filter: blur(12px);
  box-shadow: 0 0 22px rgba(49, 247, 255, 0.18);
  transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
  overflow: hidden;
}

.feature-card:hover {
  transform: translateY(-4px);
  border-color: var(--cyan-core);
  box-shadow: 0 0 32px rgba(49, 247, 255, 0.45);
}

.feature-card--1:hover {
  border-color: #ff68b8;
  box-shadow: 0 0 32px rgba(255, 104, 184, 0.45);
}

.feature-card--2:hover {
  border-color: var(--accent-gold);
  box-shadow: 0 0 32px rgba(212, 168, 75, 0.5);
}

.feature-card-glow {
  position: absolute;
  top: -40%;
  right: -30%;
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, rgba(139, 255, 225, 0.18), transparent 60%);
  pointer-events: none;
  filter: blur(8px);
}

.feature-card--1 .feature-card-glow {
  background: radial-gradient(circle, rgba(255, 104, 184, 0.18), transparent 60%);
}

.feature-card--2 .feature-card-glow {
  background: radial-gradient(circle, rgba(212, 168, 75, 0.18), transparent 60%);
}

.feature-card-icon {
  font-size: 40px;
  line-height: 1;
  filter: drop-shadow(0 0 12px rgba(139, 255, 225, 0.45));
}

.feature-card-title {
  margin: 0;
  color: #ffffff;
  font-family: var(--font-serif);
  font-size: 20px;
  font-weight: 800;
  letter-spacing: 0;
  text-shadow: 0 0 12px rgba(255, 255, 255, 0.18);
}

.feature-card-desc {
  margin: 0;
  color: rgba(226, 246, 255, 0.72);
  font-size: 13px;
  line-height: 1.7;
}

.feature-card-tag {
  margin-top: auto;
  align-self: flex-start;
  padding: 4px 10px;
  background: rgba(139, 255, 225, 0.12);
  border: 1px solid rgba(139, 255, 225, 0.42);
  border-radius: 999px;
  color: #8bffe1;
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.feature-card--1 .feature-card-tag {
  background: rgba(255, 104, 184, 0.12);
  border-color: rgba(255, 104, 184, 0.42);
  color: #ff8cca;
}

.feature-card--2 .feature-card-tag {
  background: rgba(212, 168, 75, 0.14);
  border-color: rgba(212, 168, 75, 0.5);
  color: var(--accent-gold);
}

/* ===== 屏 3: 反馈表单 ===== */
.landing-feedback {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 24px;
}

.feedback-inner {
  width: min(640px, 100%);
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 36px 32px;
  background: rgba(10, 15, 24, 0.78);
  border: 1px solid rgba(139, 255, 225, 0.5);
  border-radius: 14px;
  backdrop-filter: blur(14px);
  box-shadow: 0 0 28px rgba(49, 247, 255, 0.22);
}

.feedback-heading {
  margin: 0;
  color: #ffffff;
  font-family: var(--font-serif);
  font-size: clamp(22px, 2.6vw, 28px);
  font-weight: 800;
  text-shadow: 0 0 14px rgba(49, 247, 255, 0.42);
}

.feedback-sub {
  margin: 0 0 8px;
  color: rgba(226, 246, 255, 0.66);
  font-size: 13px;
}

.feedback-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.rating-row {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}

.rating-label {
  color: rgba(238, 249, 255, 0.78);
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.1em;
}

.rating-stars {
  display: inline-flex;
  gap: 6px;
}

.rating-star {
  width: 36px;
  height: 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(2, 5, 11, 0.55);
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 4px;
  color: rgba(238, 249, 255, 0.42);
  font-size: 20px;
  cursor: pointer;
  transition: color 0.18s ease, border-color 0.18s ease, background 0.18s ease, transform 0.18s ease;
}

.rating-star:hover {
  transform: scale(1.08);
  border-color: rgba(139, 255, 225, 0.6);
  color: rgba(139, 255, 225, 0.6);
}

.rating-star--active {
  color: var(--accent-gold);
  border-color: rgba(212, 168, 75, 0.6);
  background: rgba(212, 168, 75, 0.12);
  text-shadow: 0 0 10px rgba(212, 168, 75, 0.7);
}

.rating-value {
  margin-left: auto;
  color: rgba(238, 249, 255, 0.7);
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: 0.05em;
}

.feedback-textarea-wrap {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.feedback-textarea {
  width: 100%;
  min-height: 110px;
  padding: 12px 14px;
  background: rgba(2, 5, 11, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  color: #ffffff;
  font-size: 13px;
  line-height: 1.7;
  resize: vertical;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.feedback-textarea::placeholder {
  color: rgba(238, 249, 255, 0.42);
}

.feedback-textarea:focus {
  border-color: rgba(139, 255, 225, 0.8);
  box-shadow: 0 0 14px rgba(139, 255, 225, 0.18);
}

.feedback-counter {
  align-self: flex-end;
  color: rgba(238, 249, 255, 0.5);
  font-family: var(--font-mono);
  font-size: 11px;
}

.feedback-actions {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.feedback-submit {
  min-height: 40px;
  padding: 0 22px;
  background: linear-gradient(180deg, rgba(139, 255, 225, 0.26), rgba(139, 255, 225, 0.1));
  border: 1px solid rgba(139, 255, 225, 0.78);
  border-radius: 999px;
  color: #dffff6;
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.08em;
  cursor: pointer;
  transition: background 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
}

.feedback-submit:hover:not(:disabled) {
  background: linear-gradient(180deg, rgba(139, 255, 225, 0.42), rgba(139, 255, 225, 0.16));
  box-shadow: 0 0 18px rgba(139, 255, 225, 0.32);
  transform: translateY(-1px);
}

.feedback-submit:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.feedback-toast {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #8bffe1;
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: 0.05em;
  text-shadow: 0 0 10px rgba(139, 255, 225, 0.5);
}

.feedback-toast-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #8bffe1;
  box-shadow: 0 0 10px rgba(139, 255, 225, 0.95);
}

.toast-fade-enter-active,
.toast-fade-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.toast-fade-enter-from,
.toast-fade-leave-to {
  opacity: 0;
  transform: translateX(8px);
}

/* ===== 签名 ===== */
.landing-signature {
  position: fixed;
  right: 18px;
  bottom: 14px;
  z-index: 30;
  padding: 5px 8px;
  color: rgba(238, 249, 255, 0.38);
  background: rgba(2, 5, 11, 0.36);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  font-size: 10px;
  text-decoration: none;
  backdrop-filter: blur(8px);
  transition: color 0.18s ease, border-color 0.18s ease, background 0.18s ease;
}

.landing-signature:hover {
  color: rgba(255, 255, 255, 0.78);
  background: rgba(139, 255, 225, 0.06);
  border-color: rgba(139, 255, 225, 0.3);
  text-shadow: none;
}

/* ===== 响应式 ===== */
@media (max-width: 880px) {
  .features-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 560px) {
  .landing-hero,
  .landing-features,
  .landing-feedback {
    padding: 48px 16px;
  }

  .feedback-inner {
    padding: 28px 20px;
  }

  .rating-star {
    width: 32px;
    height: 32px;
    font-size: 18px;
  }
}
</style>
