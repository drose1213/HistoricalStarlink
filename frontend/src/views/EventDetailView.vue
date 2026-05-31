<template>
  <div class="event-detail-view">
    <header class="detail-header">
      <button class="back-btn" @click="goBack">
        <span>←</span> 返回
      </button>
      <div class="detail-nav">
        <span class="breadcrumb">
          <span class="breadcrumb-item" @click="goHome">首页</span>
          <span class="breadcrumb-sep">›</span>
          <span class="breadcrumb-item active">{{ currentEvent?.name || '事件详情' }}</span>
        </span>
      </div>
    </header>

    <main class="detail-main" v-if="currentEvent">
      <div class="starlink-hero">
        <StarlinkPlanets
          :event-id="currentEvent.id"
          :name="currentEvent.name"
          :year="currentEvent.year"
          :region="currentEvent.region"
          :importance="currentEvent.importance"
          :causes="causeEvents"
          :consequences="consequenceEvents"
          @navigate="handleNavigate"
        />
      </div>

      <div class="detail-body">
        <div class="detail-left">
          <div class="causes-section">
            <h3 class="section-heading section-heading--cyan">
              <span class="heading-icon">◆</span>
              历史原因
            </h3>
            <div v-if="causeEvents.length" class="cause-list">
              <div
                v-for="(ev, idx) in causeEvents"
                :key="ev.id"
                class="cause-card"
                :class="{ expanded: expandedCauses.has(idx) }"
              >
                <div class="card-top" @click="toggleCause(idx)">
                  <span class="card-index">{{ String(idx + 1).padStart(2, '0') }}</span>
                  <span class="card-name">{{ ev.name }}</span>
                  <span class="card-year">{{ formatYear(ev.year) }}</span>
                  <span class="card-weight card-weight--cyan">权重 {{ ev.weight }}</span>
                  <span class="card-expand">{{ expandedCauses.has(idx) ? '−' : '+' }}</span>
                </div>
                <Transition name="desc-expand">
                  <div v-if="expandedCauses.has(idx)" class="card-desc">
                    <p v-if="currentEvent.causes[idx]" class="desc-content">{{ currentEvent.causes[idx] }}</p>
                    <p class="desc-event">{{ ev.name }} · {{ formatYear(ev.year) }}</p>
                    <button class="card-navigate" @click.stop="handleNavigate(ev.id)">
                      前往探索 →
                    </button>
                  </div>
                </Transition>
              </div>
            </div>
            <ul v-if="causeEvents.length === 0 && currentEvent.causes.length" class="cause-list">
              <li v-for="(cause, idx) in currentEvent.causes" :key="idx" class="cause-item">
                <span class="cause-index">{{ String(idx + 1).padStart(2, '0') }}</span>
                <span class="cause-text">{{ cause }}</span>
              </li>
            </ul>
            <div v-if="causeEvents.length === 0 && currentEvent.causes.length === 0" class="empty-hint">
              暂无历史原因记录
            </div>
          </div>

          <div class="consequences-section">
            <h3 class="section-heading section-heading--pink">
              <span class="heading-icon">◆</span>
              历史影响
            </h3>
            <div v-if="consequenceEvents.length" class="consequence-list">
              <div
                v-for="(ev, idx) in consequenceEvents"
                :key="ev.id"
                class="consequence-card"
                :class="{ expanded: expandedConsequences.has(idx) }"
              >
                <div class="card-top" @click="toggleConsequence(idx)">
                  <span class="card-index card-index--pink">{{ String(idx + 1).padStart(2, '0') }}</span>
                  <span class="card-name">{{ ev.name }}</span>
                  <span class="card-year">{{ formatYear(ev.year) }}</span>
                  <span class="card-weight card-weight--pink">权重 {{ ev.weight }}</span>
                  <span class="card-expand card-expand--pink">{{ expandedConsequences.has(idx) ? '−' : '+' }}</span>
                </div>
                <Transition name="desc-expand">
                  <div v-if="expandedConsequences.has(idx)" class="card-desc card-desc--pink">
                    <p v-if="currentEvent.consequences[idx]" class="desc-content">{{ currentEvent.consequences[idx] }}</p>
                    <p class="desc-event">{{ ev.name }} · {{ formatYear(ev.year) }}</p>
                    <button class="card-navigate card-navigate--pink" @click.stop="handleNavigate(ev.id)">
                      前往探索 →
                    </button>
                  </div>
                </Transition>
              </div>
            </div>
            <ul v-if="consequenceEvents.length === 0 && currentEvent.consequences.length" class="consequence-list">
              <li v-for="(c, idx) in currentEvent.consequences" :key="idx" class="consequence-item">
                <span class="consequence-index">{{ String(idx + 1).padStart(2, '0') }}</span>
                <span class="consequence-text">{{ c }}</span>
              </li>
            </ul>
            <div v-if="consequenceEvents.length === 0 && currentEvent.consequences.length === 0" class="empty-hint">
              暂无历史影响记录
            </div>
          </div>
        </div>
      </div>
    </main>

    <Transition name="drawer-overlay">
      <div v-if="currentEvent && drawerOpen" class="drawer-overlay-bg" @click="drawerOpen = false" />
    </Transition>

    <button v-if="currentEvent" class="drawer-trigger" :class="{ open: drawerOpen }" @click="drawerOpen = !drawerOpen">
      <span class="drawer-trigger-icon">{{ drawerOpen ? '›' : '‹' }}</span>
      <span class="drawer-trigger-label">历史</span>
    </button>

    <Transition name="drawer-slide-right">
      <div v-if="currentEvent && drawerOpen" class="right-drawer">
        <div class="drawer-header">
          <h4 class="drawer-title">历史档案</h4>
          <button class="drawer-close" @click="drawerOpen = false">✕</button>
        </div>
        <div class="drawer-body">
          <div class="drawer-section">
            <button class="cy-btn cy-btn--glow drawer-dialogue-btn" @click="startDialogue">
              开启时空对话
            </button>
            <p class="entry-hint">穿越时空，与历史人物对话</p>
          </div>

          <div class="drawer-section event-desc-panel">
            <h4 class="desc-title">事件概述</h4>
            <p class="desc-text">{{ currentEvent.description }}</p>
            <div class="desc-meta">
              <span class="meta-tag meta-tag--region">{{ currentEvent.region === 'china' ? '华夏' : '海外' }}</span>
              <span class="meta-tag meta-tag--year">{{ formatYear(currentEvent.year) }}</span>
              <span class="meta-tag meta-tag--importance">重要性 {{ currentEvent.importance }}</span>
            </div>
          </div>

          <div class="drawer-section">
            <h4 class="drawer-section-title">◆ 探索记录</h4>
            <ExplorationRecord :event-id="currentEvent.id" :event-name="currentEvent.name" :show-controls="true" />
          </div>

          <div class="drawer-section">
            <VotingSystem :event-id="currentEvent.id" :event-name="currentEvent.name" />
            <RatingSystem :event-id="currentEvent.id" :event-name="currentEvent.name" />
          </div>
        </div>
      </div>
    </Transition>

    <main class="detail-main" v-if="!currentEvent">
      <div class="not-found">
        <div class="not-found-icon">◇</div>
        <h2>事件未找到</h2>
        <p>无法找到指定的历史事件，请返回首页重试。</p>
        <button class="cy-btn" @click="goHome">返回首页</button>
      </div>
    </main>

    <Transition name="warp-fade">
      <div v-if="warpTarget" class="warp-overlay">
        <div class="warp-ship">🚀</div>
        <div class="warp-text">飞船正在前往</div>
        <div class="warp-dest">{{ warpTarget.name }}</div>
        <div class="warp-progress-bar">
          <div class="warp-progress-fill" />
        </div>
        <div class="warp-sub">{{ warpLoadingText }}</div>
      </div>
    </Transition>

    <div class="cy-scanlines"></div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import StarlinkPlanets from '@/components/StarlinkPlanets.vue'
import ExplorationRecord from '@/components/ExplorationRecord.vue'
import VotingSystem from '@/components/VotingSystem.vue'
import RatingSystem from '@/components/RatingSystem.vue'
import { allEvents, getEventById, getRelatedEvents, loadEvents } from '@/data/events'
import { requireAuth } from '@/utils/auth'
import { recordExploration } from '@/utils/exploration'

const route = useRoute()
const router = useRouter()

const warpTarget = ref<{ id: string; name: string } | null>(null)
const warpLoadingText = ref('正在穿越时空隧道...')

const loadingTexts = [
  '正在穿越时空隧道...',
  '校准时间坐标...',
  '连接历史数据库...',
  '加载时空档案...',
  '对接星链节点...',
  '数据同步完成 ✓',
]

let warpTextTimer: ReturnType<typeof setInterval> | null = null
const drawerOpen = ref(false)
const expandedCauses = ref<Set<number>>(new Set())
const expandedConsequences = ref<Set<number>>(new Set())

const eventId = computed(() => route.params.id as string)
const currentEvent = computed(() => getEventById(eventId.value))

const causeEvents = computed(() => {
  if (!currentEvent.value) return []
  return getRelatedEvents(currentEvent.value.id, 'causes')
})

const consequenceEvents = computed(() => {
  if (!currentEvent.value) return []
  return getRelatedEvents(currentEvent.value.id, 'consequences')
})

watch(eventId, (id) => {
  recordExploration(id)
}, { immediate: true })

function toggleCause(idx: number) {
  const s = new Set(expandedCauses.value)
  if (s.has(idx)) s.delete(idx); else s.add(idx)
  expandedCauses.value = s
}

function toggleConsequence(idx: number) {
  const s = new Set(expandedConsequences.value)
  if (s.has(idx)) s.delete(idx); else s.add(idx)
  expandedConsequences.value = s
}

function formatYear(year: number): string {
  return year < 0 ? `公元前${Math.abs(year)}年` : `${year}年`
}

function goBack() {
  router.back()
}

function goHome() {
  router.push({ name: 'Home' })
}

function startDialogue() {
  if (!requireAuth()) return
  if (!currentEvent.value) return
  warpTarget.value = { id: currentEvent.value.id, name: currentEvent.value.name }
  let textIdx = 0
  warpLoadingText.value = loadingTexts[0]
  warpTextTimer = setInterval(() => {
    textIdx++
    if (textIdx < loadingTexts.length) {
      warpLoadingText.value = loadingTexts[textIdx]
    }
  }, 350)
  setTimeout(() => {
    if (warpTextTimer) { clearInterval(warpTextTimer); warpTextTimer = null }
    warpTarget.value = null
    router.push({ name: 'Dialogue', params: { eventId: currentEvent.value!.id } })
  }, 2200)
}

function handleNavigate(eventId: string) {
  const event = getEventById(eventId)
  if (!event) return
  warpTarget.value = { id: event.id, name: event.name }
  setTimeout(() => {
    warpTarget.value = null
    router.push({ name: 'EventDetail', params: { id: eventId } })
  }, 1500)
}

watch(() => route.params.id, () => {
  if (currentEvent.value) {
    document.title = `${currentEvent.value.name} - 历史星链探索`
  }
  const main = document.querySelector('.detail-main')
  if (main) main.scrollTop = 0
}, { immediate: true })
</script>

<style scoped>
.event-detail-view {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.detail-header {
  padding: 12px 22px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(180deg, rgba(4, 8, 15, 0.96), rgba(4, 8, 15, 0.72));
  border-bottom: 1px solid var(--border-subtle);
  z-index: var(--z-header);
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  padding: 5px 14px;
  background: transparent;
  border: 1px solid var(--border-cyan);
  border-radius: var(--radius-full);
  color: var(--cyan-core);
  transition: all 0.2s;
}

.back-btn:hover {
  background: rgba(49, 247, 255, 0.12);
  box-shadow: 0 0 12px rgba(49, 247, 255, 0.3);
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-muted);
}

.breadcrumb-item {
  color: var(--cyan-core);
  cursor: pointer;
  padding: 3px 8px;
  border-radius: var(--radius-sm);
}

.breadcrumb-item:hover {
  background: rgba(49, 247, 255, 0.12);
}

.breadcrumb-item.active {
  color: #ffffff;
  cursor: default;
}

.breadcrumb-sep {
  color: var(--text-muted);
}

.detail-main {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
}

.starlink-hero {
  width: 100%;
  height: 55vh;
  min-height: 420px;
  overflow: hidden;
}

.detail-body {
  padding: 20px 40px 40px;
}

.detail-left {
  display: flex;
  flex-direction: column;
  gap: 28px;
  max-width: 800px;
}

.section-heading {
  font-family: var(--font-serif);
  font-size: 17px;
  font-weight: 700;
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.heading-icon {
  font-size: 10px;
}

.section-heading--cyan {
  color: var(--cyan-core);
  text-shadow: 0 0 10px var(--cyan-core);
}

.section-heading--pink {
  color: var(--pink-core);
  text-shadow: 0 0 10px var(--pink-core);
}

.cause-list,
.consequence-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.cause-item,
.consequence-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 16px;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  transition: all 0.2s;
}

.cause-item:hover {
  border-color: var(--border-cyan);
  box-shadow: 0 0 10px rgba(49, 247, 255, 0.15);
}

.consequence-item:hover {
  border-color: var(--border-pink);
  box-shadow: 0 0 10px rgba(255, 53, 243, 0.15);
}

.cause-index,
.consequence-index {
  font-family: var(--font-mono);
  font-size: 10px;
  min-width: 20px;
}

.cause-index {
  color: var(--cyan-core);
}

.consequence-index {
  color: var(--pink-core);
}

.cause-text,
.consequence-text {
  font-size: 13px;
  color: var(--text-light);
  line-height: 1.5;
}

.cause-card,
.consequence-card {
  padding: 14px 18px;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.25s ease;
}

.cause-card:hover {
  border-color: var(--cyan-core);
  box-shadow: 0 0 16px rgba(49, 247, 255, 0.25), inset 0 0 20px rgba(49, 247, 255, 0.05);
  transform: translateX(4px);
}

.consequence-card:hover {
  border-color: var(--pink-core);
  box-shadow: 0 0 16px rgba(255, 53, 243, 0.25), inset 0 0 20px rgba(255, 53, 243, 0.05);
  transform: translateX(4px);
}

.card-top {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.card-index {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--cyan-core);
  min-width: 20px;
}

.card-index--pink {
  color: var(--pink-core);
}

.card-name {
  font-size: 14px;
  font-weight: 600;
  color: #ffffff;
  font-family: var(--font-serif);
}

.card-year {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
  margin-left: auto;
}

.card-weight {
  font-family: var(--font-mono);
  font-size: 10px;
  padding: 2px 8px;
  border-radius: var(--radius-full);
}

.card-weight--cyan {
  color: var(--cyan-core);
  background: rgba(49, 247, 255, 0.1);
  border: 1px solid rgba(49, 247, 255, 0.3);
}

.card-weight--pink {
  color: var(--pink-core);
  background: rgba(255, 53, 243, 0.1);
  border: 1px solid rgba(255, 53, 243, 0.3);
}

.card-expand {
  font-family: var(--font-mono);
  font-size: 14px;
  color: var(--cyan-core);
  margin-left: auto;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(49, 247, 255, 0.1);
  transition: all 0.2s;
  flex-shrink: 0;
}

.card-expand--pink {
  color: var(--pink-core);
  background: rgba(255, 53, 243, 0.1);
}

.cause-card.expanded,
.consequence-card.expanded {
  transform: translateX(0);
}

.cause-card.expanded {
  border-color: var(--cyan-core);
  box-shadow: 0 0 20px rgba(49, 247, 255, 0.2);
}

.consequence-card.expanded {
  border-color: var(--pink-core);
  box-shadow: 0 0 20px rgba(255, 53, 243, 0.2);
}

.card-desc {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border-subtle);
}

.card-desc--pink {
  border-top-color: rgba(255, 53, 243, 0.2);
}

.desc-content {
  font-size: 13px;
  color: var(--text-light);
  line-height: 1.7;
  margin-bottom: 8px;
}

.desc-event {
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--text-muted);
  margin-bottom: 10px;
}

.card-navigate {
  display: inline-block;
  padding: 6px 16px;
  font-size: 12px;
  font-weight: 600;
  color: var(--cyan-core);
  background: rgba(49, 247, 255, 0.08);
  border: 1px solid rgba(49, 247, 255, 0.3);
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: all 0.2s;
}

.card-navigate:hover {
  background: rgba(49, 247, 255, 0.18);
  box-shadow: 0 0 12px rgba(49, 247, 255, 0.3);
}

.card-navigate--pink {
  color: var(--pink-core);
  background: rgba(255, 53, 243, 0.08);
  border-color: rgba(255, 53, 243, 0.3);
}

.card-navigate--pink:hover {
  background: rgba(255, 53, 243, 0.18);
  box-shadow: 0 0 12px rgba(255, 53, 243, 0.3);
}

.desc-expand-enter-active {
  transition: all 0.3s ease;
  overflow: hidden;
}

.desc-expand-leave-active {
  transition: all 0.2s ease;
  overflow: hidden;
}

.desc-expand-enter-from {
  opacity: 0;
  max-height: 0;
  transform: translateY(-8px);
}

.desc-expand-enter-to {
  opacity: 1;
  max-height: 200px;
}

.desc-expand-leave-from {
  opacity: 1;
  max-height: 200px;
}

.desc-expand-leave-to {
  opacity: 0;
  max-height: 0;
}

.empty-hint {
  font-size: 12px;
  color: var(--text-muted);
  padding: 16px;
  text-align: center;
  opacity: 0.6;
}

.drawer-trigger {
  position: fixed;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 32px;
  height: 80px;
  background: rgba(8, 15, 28, 0.9);
  border: 1px solid var(--border-cyan);
  border-right: none;
  border-radius: 8px 0 0 8px;
  color: var(--cyan-core);
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  transition: all 0.3s ease;
  z-index: 100;
  box-shadow: -4px 0 16px rgba(49, 247, 255, 0.1);
}

.drawer-trigger:hover {
  background: rgba(49, 247, 255, 0.12);
  box-shadow: -4px 0 20px rgba(49, 247, 255, 0.2);
}

.drawer-trigger.open {
  right: 340px;
}

.drawer-trigger-icon {
  font-size: 14px;
  line-height: 1;
}

.drawer-trigger-label {
  font-size: 10px;
  writing-mode: vertical-rl;
  letter-spacing: 2px;
}

.drawer-overlay-bg {
  position: fixed;
  inset: 0;
  z-index: 90;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(2px);
}

.right-drawer {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  width: 340px;
  z-index: 95;
  background: rgba(8, 15, 28, 0.96);
  border-left: 1px solid var(--border-cyan);
  display: flex;
  flex-direction: column;
  backdrop-filter: blur(16px);
  box-shadow: -8px 0 40px rgba(49, 247, 255, 0.1);
}

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 18px;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

.drawer-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--cyan-core);
  font-family: var(--font-serif);
  text-shadow: 0 0 10px rgba(49, 247, 255, 0.3);
}

.drawer-close {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--border-subtle);
  color: var(--text-muted);
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.drawer-close:hover {
  background: rgba(255, 60, 60, 0.15);
  color: #ff6b6b;
  border-color: rgba(255, 60, 60, 0.3);
}

.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.drawer-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.drawer-section-title {
  font-family: var(--font-serif);
  font-size: 13px;
  color: var(--cyan-core);
  font-weight: 700;
  margin-bottom: 4px;
}

.drawer-dialogue-btn {
  width: 100%;
}

.drawer-overlay-enter-active {
  transition: opacity 0.3s ease;
}

.drawer-overlay-leave-active {
  transition: opacity 0.25s ease;
}

.drawer-overlay-enter-from,
.drawer-overlay-leave-to {
  opacity: 0;
}

.drawer-slide-right-enter-active {
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.drawer-slide-right-leave-active {
  transition: transform 0.25s ease;
}

.drawer-slide-right-enter-from,
.drawer-slide-right-leave-to {
  transform: translateX(100%);
}

.cy-btn--glow {
  position: relative;
  z-index: 1;
  font-family: var(--font-serif);
  font-size: 14px;
  padding: 10px 28px;
  background: linear-gradient(135deg, rgba(49, 247, 255, 0.12), rgba(255, 53, 243, 0.08));
  border: 1px solid var(--cyan-core);
  color: #ffffff;
  border-radius: var(--radius-full);
  text-shadow: 0 0 10px var(--cyan-core);
  box-shadow: 0 0 16px rgba(49, 247, 255, 0.3), 0 0 32px rgba(49, 247, 255, 0.12);
  animation: glowPulse 2.5s ease-in-out infinite;
}

.cy-btn--glow:hover {
  background: linear-gradient(135deg, rgba(49, 247, 255, 0.22), rgba(255, 53, 243, 0.16));
  box-shadow: 0 0 24px rgba(49, 247, 255, 0.5), 0 0 48px rgba(49, 247, 255, 0.2);
  transform: translateY(-1px);
}

@keyframes glowPulse {
  0%, 100% { box-shadow: 0 0 16px rgba(49, 247, 255, 0.3), 0 0 32px rgba(49, 247, 255, 0.12); }
  50% { box-shadow: 0 0 20px rgba(49, 247, 255, 0.45), 0 0 40px rgba(49, 247, 255, 0.18); }
}

.entry-hint {
  font-size: 11px;
  color: var(--text-muted);
  text-align: center;
}

.event-desc-panel {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 18px 20px;
  position: relative;
  overflow: hidden;
}

.event-desc-panel::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, var(--cyan-core), var(--pink-core), var(--gold-core, #ffd700));
}

.desc-title {
  font-family: var(--font-serif);
  font-size: 14px;
  color: var(--gold-core, #ffd700);
  margin-bottom: 10px;
  text-shadow: 0 0 8px rgba(255, 215, 0, 0.3);
}

.desc-text {
  font-size: 13px;
  color: var(--text-light);
  line-height: 1.7;
  margin-bottom: 12px;
}

.desc-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.meta-tag {
  font-family: var(--font-mono);
  font-size: 10px;
  padding: 3px 10px;
  border-radius: var(--radius-full);
}

.meta-tag--region {
  color: var(--cyan-core);
  background: rgba(49, 247, 255, 0.1);
  border: 1px solid rgba(49, 247, 255, 0.25);
}

.meta-tag--year {
  color: var(--pink-core);
  background: rgba(255, 53, 243, 0.1);
  border: 1px solid rgba(255, 53, 243, 0.25);
}

.meta-tag--importance {
  color: var(--gold-core, #ffd700);
  background: rgba(255, 215, 0, 0.1);
  border: 1px solid rgba(255, 215, 0, 0.25);
}

.not-found {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 16px;
  text-align: center;
  padding: 40px;
}

.not-found-icon {
  font-size: 48px;
  color: var(--cyan-core);
  text-shadow: 0 0 30px var(--cyan-core);
  opacity: 0.4;
}

.not-found h2 {
  font-family: var(--font-display);
  font-size: 22px;
  color: var(--text-light);
}

.not-found p {
  font-size: 13px;
  color: var(--text-muted);
}

.warp-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  background: rgba(2, 4, 10, 0.92);
  backdrop-filter: blur(12px);
}

.warp-ship {
  font-size: 64px;
  animation: warpFly 1.5s ease-in-out forwards;
  filter: drop-shadow(0 0 20px rgba(49, 247, 255, 0.6));
}

@keyframes warpFly {
  0% {
    transform: translateX(-200px) translateY(40px) scale(0.6) rotate(-15deg);
    opacity: 0;
  }
  20% {
    opacity: 1;
    transform: translateX(-80px) translateY(10px) scale(1) rotate(-5deg);
  }
  80% {
    opacity: 1;
    transform: translateX(80px) translateY(-10px) scale(1.1) rotate(5deg);
  }
  100% {
    transform: translateX(300px) translateY(-40px) scale(0.6) rotate(15deg);
    opacity: 0;
  }
}

.warp-text {
  font-size: 14px;
  color: var(--text-muted);
  letter-spacing: 4px;
  text-transform: uppercase;
}

.warp-dest {
  font-family: var(--font-serif);
  font-size: 28px;
  font-weight: 700;
  color: var(--cyan-core);
  text-shadow: 0 0 20px var(--cyan-core), 0 0 40px rgba(49, 247, 255, 0.3);
  animation: warpPulse 0.8s ease-in-out infinite alternate;
}

@keyframes warpPulse {
  0% {
    text-shadow: 0 0 20px var(--cyan-core), 0 0 40px rgba(49, 247, 255, 0.3);
    transform: scale(1);
  }
  100% {
    text-shadow: 0 0 30px var(--cyan-core), 0 0 60px rgba(49, 247, 255, 0.5), 0 0 80px rgba(255, 53, 243, 0.2);
    transform: scale(1.05);
  }
}

.warp-sub {
  font-size: 12px;
  color: var(--pink-core);
  letter-spacing: 2px;
  animation: warpSubBlink 1s ease-in-out infinite;
}

.warp-progress-bar {
  width: 200px;
  height: 3px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  overflow: hidden;
  margin: 12px 0 8px;
}

.warp-progress-fill {
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, var(--cyan-core), var(--pink-core));
  border-radius: 2px;
  animation: warpProgressFill 2.2s ease-in-out forwards;
}

@keyframes warpProgressFill {
  0% { width: 0%; }
  80% { width: 90%; }
  100% { width: 100%; }
}

@keyframes warpSubBlink {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}

.warp-fade-enter-active {
  transition: opacity 0.2s ease;
}

.warp-fade-leave-active {
  transition: opacity 0.3s ease;
}

.warp-fade-enter-from,
.warp-fade-leave-to {
  opacity: 0;
}

@media (max-width: 1000px) {
  .right-drawer {
    width: min(340px, calc(100vw - 50px));
  }
  .drawer-trigger.open {
    right: min(340px, calc(100vw - 50px));
  }
}
</style>
