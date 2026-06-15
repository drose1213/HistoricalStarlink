<template>
  <div class="home-view">
    <header class="app-header">
      <div class="logo">
        <span class="logo-icon" aria-hidden="true"></span>
        <div class="logo-text">
          <h1>{{ t('home.title') }}</h1>
          <span class="logo-subtitle">Starlink · 史河之链</span>
        </div>
      </div>

      <nav class="page-nav" :aria-label="t('nav.home')">
        <router-link to="/" class="nav-link nav-link--active">{{ t('nav.home') }}</router-link>
        <router-link to="/champions" class="nav-link">{{ t('nav.champions') }}</router-link>
        <router-link to="/leaderboard" class="nav-link">{{ t('nav.leaderboard') }}</router-link>
        <router-link v-if="authStore.user?.is_admin" to="/knowledge-base" class="nav-link">{{ t('nav.knowledge') }}</router-link>
        <router-link v-if="authStore.isLoggedIn" to="/profile" class="nav-link">{{ t('nav.profile') }}</router-link>
      </nav>

      <div class="user-area">
        <!-- 升级会员占位按钮 (埋点测试用) -->
        <button
          type="button"
          class="upgrade-btn"
          @click="handleUpgradeClick"
        >{{ t('home.upgrade') }}</button>
        <template v-if="authStore.isLoggedIn">
          <div class="user-menu" @click="showUserMenu = !showUserMenu">
            <div class="user-avatar">{{ authStore.userInitial }}</div>
            <span class="user-name">{{ authStore.displayName }}</span>
          </div>
          <Transition name="menu-fade">
            <div v-if="showUserMenu" class="user-dropdown">
              <div class="dropdown-header">
                <div class="dropdown-avatar">{{ authStore.userInitial }}</div>
                <div class="dropdown-info">
                  <span class="dropdown-name">{{ authStore.displayName }}</span>
                  <span class="dropdown-email">{{ authStore.user?.email }}</span>
                </div>
              </div>
              <div class="dropdown-divider"></div>
              <button class="dropdown-item" @click="handleLogout">
                <span class="item-icon" aria-hidden="true"></span>
                {{ t('home.logout') }}
              </button>
            </div>
          </Transition>
        </template>
        <template v-else>
          <router-link to="/login" class="login-btn">{{ t('nav.loginOrRegister') }}</router-link>
        </template>
      </div>

      <div class="locale-area" v-show="false">
        <LanguageSwitcher />
      </div>
    </header>

    <Transition name="banner-slide">
      <div v-if="!backendAvailable && loadError" class="backend-banner">
        <span class="banner-icon">⚠</span>
        <div class="banner-text">
          <strong>{{ t('home.backendDisconnected') }}</strong>
          <span>{{ loadError }}, {{ t('common.retry') }} {{ t('home.backendHint') }}</span>
        </div>
        <button class="banner-retry" @click="retryLoad">{{ t('home.backendRetry') }}</button>
      </div>
    </Transition>

    <main class="home-main">
      <div class="cosmic-section">
        <CosmicMap v-if="!loadingInitial" @select-event="goToEvent" />
          <div v-else class="cosmic-loading">
            <div class="cosmic-loading__spinner" aria-hidden="true"></div>
            <p class="cosmic-loading__text">{{ t('home.cosmicLoading') }}</p>
          </div>

        <div class="cosmic-overlay" aria-hidden="true"></div>

        <!-- 时空探索 FAB (浮动触发按钮) -->
        <button
          class="explore-fab"
          :class="{ 'explore-fab--active': showExploreModal }"
          @click="showExploreModal = true"
          aria-label="开启时空探索"
        >
          <span class="explore-fab__ring" aria-hidden="true"></span>
          <span class="explore-fab__core" aria-hidden="true"></span>
          <span class="explore-fab__label">时空探索</span>
        </button>

        <!-- 时空探索弹窗 (点击 FAB 后弹出) -->
        <Transition name="explore-modal">
          <div v-if="showExploreModal" class="explore-modal-overlay" @click.self="showExploreModal = false">
            <div class="explore-modal">
              <div class="explore-modal__scanline" aria-hidden="true"></div>
              <button class="explore-modal__close" @click="showExploreModal = false" aria-label="关闭">
                <span aria-hidden="true">&times;</span>
              </button>
              <div class="explore-modal__header">
                <div class="explore-modal__glyph" aria-hidden="true">
                  <span class="glyph-orbit"></span>
                  <span class="glyph-core">&#10022;</span>
                </div>
                <h2 class="explore-modal__title">任意话题 · 时空探索</h2>
                <p class="explore-modal__subtitle">输入任何你感兴趣的话题，穿越时空与历史人物对话</p>
              </div>
              <form class="explore-modal__form" @submit.prevent="handleFreeExplore">
                <input
                  ref="exploreInputRef"
                  v-model="freeExploreTopic"
                  type="text"
                  class="explore-modal__input"
                  placeholder="如「AI 发展史」「太空探索」「商鞅变法」..."
                  maxlength="120"
                  :disabled="freeExploreLoading"
                />
                <button
                  type="submit"
                  class="explore-modal__btn"
                  :disabled="freeExploreLoading || !freeExploreTopic.trim()"
                >
                  <span v-if="!freeExploreLoading">开启时空对话</span>
                  <span v-else>加载中...</span>
                </button>
              </form>
              <div v-if="freeExploreError" class="explore-modal__error">{{ freeExploreError }}</div>
              <div class="explore-modal__hints">
                <span class="explore-hint-tag" v-for="hint in exploreHints" :key="hint" @click="freeExploreTopic = hint">{{ hint }}</span>
              </div>
              <button
                v-if="!authStore.isLoggedIn && freeExploreError.includes('登录')"
                type="button"
                class="explore-modal__login-link"
                @click="handleLoginRedirect"
              >
                <span>前往登录</span>
                <span class="login-arrow" aria-hidden="true">→</span>
              </button>
            </div>
          </div>
        </Transition>

        <!-- 英雄卡牌选人覆盖层 -->
        <Transition name="hero-fade">
          <div v-if="showHeroSelection" class="hero-selection-overlay" @click.self="showHeroSelection = false">
            <div class="hero-selection-modal">
              <HeroSelectionStep
                :topic="currentExploreTopic"
                @select="onHeroSelect"
                @skip="onHeroSkip"
              />
            </div>
          </div>
        </Transition>

        <!-- 角色穿越中全屏遮罩 -->
        <Transition name="hero-fade">
          <div v-if="freeExploreLoading" class="traversing-overlay">
            <div class="traversing-content">
              <div class="traversing-spinner"></div>
              <div class="traversing-hero" v-if="selectedHeroName">
                <span class="traversing-symbol">✦</span>
              </div>
              <h2 class="traversing-title">时空穿越中</h2>
              <p class="traversing-hint">
                <template v-if="selectedHeroName">正在连接「{{ selectedHeroName }}」...</template>
                <template v-else>正在开启时空对话...</template>
              </p>
              <div class="traversing-progress">
                <div class="traversing-progress-bar"></div>
              </div>
            </div>
          </div>
        </Transition>
      </div>

      <a
        class="deerflow-signature"
        href="https://deerflow.tech"
        target="_blank"
        rel="noopener noreferrer"
      >
        Created By Deerflow
      </a>

      <button class="drawer-trigger" :class="{ open: drawerOpen }" @click="drawerOpen = !drawerOpen">
        <span class="trigger-icon" aria-hidden="true">{{ drawerOpen ? '×' : '‹' }}</span>
        <span class="trigger-label">{{ t('home.eventsButton') }}</span>
      </button>

      <Transition name="drawer-slide">
        <div v-if="drawerOpen" class="event-drawer">
          <div class="drawer-header">
            <h2 class="drawer-hero-title">{{ t('home.drawerHeroTitle') }}</h2>

            <div class="search-bar">
              <div class="search-input-wrap">
                <input
                  v-model="searchQuery"
                  type="text"
                  class="search-input"
                  :placeholder="t('home.searchPlaceholder')"
                  @input="onSearchInput"
                  @focus="showSearchDropdown = true"
                  @blur="handleSearchBlur"
                  @keydown.enter="handleSearchEnter"
                />
                <button class="search-btn" :aria-label="t('common.search')" @mousedown.prevent="handleSearchEnter">
                  <span class="search-icon" aria-hidden="true"></span>
                  <span class="search-btn-label">{{ t('home.search') }}</span>
                </button>
              </div>
              <div class="search-loading-bar" :class="{ active: searchLoading }">
                <div class="loading-track" />
              </div>
              <Transition name="menu-fade">
                <div v-if="showSearchDropdown && searchQuery.trim()" class="search-dropdown">
                  <template v-if="searchResults.length > 0">
                    <div
                      v-for="item in searchResults"
                      :key="item.id"
                      class="search-item"
                      @mousedown.prevent="handleSearchSelect(item.id)"
                    >
                      <span class="search-item-name">{{ tf(`events.${item.id}.name`, item.name) }}</span>
                      <span class="search-item-meta">
                        {{ formatEventYear(item.year) }} · {{ item.region === 'china' ? t('home.regionChina') : t('home.regionForeign') }}
                      </span>
                    </div>
                  </template>
                  <div v-else class="search-item search-empty">
                    <span class="search-item-name" style="opacity:0.4">{{ t('home.noMatch') }}</span>
                  </div>
                </div>
              </Transition>
            </div>

            <h3 class="drawer-title">
              <span class="title-icon" aria-hidden="true"></span>
              {{ t('home.drawerTitle') }}
            </h3>
            <div class="drawer-filters">
              <button
                v-for="f in filters"
                :key="f.value"
                class="drawer-filter-btn"
                :class="{ active: appStore.currentFilter === f.value }"
                @click="appStore.setFilter(f.value)"
              >
                {{ f.label }}
              </button>
            </div>
          </div>
          <div class="drawer-list">
            <div class="drawer-section-label" v-if="homeFeed.explored.length > 0 && homeFeed.recommended.length > 0">
              <span class="section-dot section-dot--cyan" aria-hidden="true"></span>
              <span>已探索 · {{ homeFeed.explored_total }}</span>
            </div>
            <div
              v-for="event in homeFeed.explored"
              :key="event.id"
              class="drawer-item"
              :data-importance="event.importance"
              @click="goToEvent(event.id); drawerOpen = false"
            >
              <div class="drawer-item-left">
                <span class="drawer-dot" :class="`drawer-dot--${event.region}`"></span>
                <div class="drawer-item-info">
                  <span class="drawer-item-name">{{ event.name }}</span>
                  <span class="drawer-item-year">{{ formatEventYear(event.year) }}</span>
                </div>
              </div>
              <div class="drawer-item-right">
                <span class="drawer-item-region" :class="`drawer-item-region--${event.region}`">
                  {{ event.region === 'china' ? t('home.regionChina') : t('home.regionForeign') }}
                </span>
                <span class="drawer-item-score">{{ event.importance }}/10</span>
              </div>
            </div>
            <div class="drawer-section-label" v-if="homeFeed.explored.length > 0 && homeFeed.recommended.length > 0">
              <span class="section-dot section-dot--gold" aria-hidden="true"></span>
              <span>为你推荐 · {{ homeFeed.recommended_total }}</span>
            </div>
            <div
              v-for="event in homeFeed.recommended"
              :key="event.id"
              class="drawer-item"
              :data-importance="event.importance"
              @click="goToEvent(event.id); drawerOpen = false"
            >
              <div class="drawer-item-left">
                <span class="drawer-dot" :class="`drawer-dot--${event.region}`"></span>
                <div class="drawer-item-info">
                  <span class="drawer-item-name">{{ event.name }}</span>
                  <span class="drawer-item-year">{{ formatEventYear(event.year) }}</span>
                </div>
              </div>
              <div class="drawer-item-right">
                <span class="drawer-item-region" :class="`drawer-item-region--${event.region}`">
                  {{ event.region === 'china' ? t('home.regionChina') : t('home.regionForeign') }}
                </span>
                <span class="drawer-item-score">{{ event.importance }}/10</span>
              </div>
            </div>
            <!-- 兜底: 既无探索也无推荐时, 展示全量事件 (按 filter 过滤) -->
            <div
              v-if="homeFeed.explored.length === 0 && homeFeed.recommended.length === 0"
              class="drawer-fallback"
            >
              <div
                v-for="event in historyEvents"
                :key="event.id"
                class="drawer-item"
                :data-importance="event.importance"
                @click="goToEvent(event.id); drawerOpen = false"
              >
                <div class="drawer-item-left">
                  <span class="drawer-dot" :class="`drawer-dot--${event.region}`"></span>
                  <div class="drawer-item-info">
                    <span class="drawer-item-name">{{ event.name }}</span>
                    <span class="drawer-item-year">{{ formatEventYear(event.year) }}</span>
                  </div>
                </div>
                <div class="drawer-item-right">
                  <span class="drawer-item-region" :class="`drawer-item-region--${event.region}`">
                    {{ event.region === 'china' ? t('home.regionChina') : t('home.regionForeign') }}
                  </span>
                  <span class="drawer-item-score">{{ event.importance }}/10</span>
                </div>
              </div>
            </div>
            <div v-if="homeFeed.explored.length === 0 && homeFeed.recommended.length === 0 && historyEvents.length === 0" class="drawer-empty">
              <span class="empty-glyph" aria-hidden="true">◇</span>
              <p>正在连接星图…</p>
            </div>
          </div>
        </div>
      </Transition>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import { useDialogueStore } from '@/stores/dialogue'
import { useI18n } from '@/composables/useI18n'
import { trackEvent } from '@/utils/analytics'
import CosmicMap from '@/components/CosmicMap.vue'
import LanguageSwitcher from '@/components/LanguageSwitcher.vue'
import HeroSelectionStep from '@/components/HeroSelectionStep.vue'
import type { HeroPersona } from '@/api/dialogue'
import { allEvents as historyEvents, searchEvents, backendAvailable, loadError, loadEvents } from '@/data/events'
import { ragApi } from '@/api/rag'
import { eventsApi, type HomeFeedResponse } from '@/api/events'
import { getSessionId } from '@/utils/session'
import type { HistoryEvent } from '@/types'

interface LocalSearchResult {
  id: string
  name: string
  year: number | null
  region: 'china' | 'foreign'
  importance: number
  description?: string
  score: number
  source?: string
}

const router = useRouter()
const appStore = useAppStore()
const authStore = useAuthStore()
const dialogueStore = useDialogueStore()
const { t, tf } = useI18n()
const showUserMenu = ref(false)
const drawerOpen = ref(false)
const searchQuery = ref('')
const showSearchDropdown = ref(false)
const searchLoading = ref(false)

// 任意话题自由探索
const freeExploreTopic = ref('')
const freeExploreLoading = ref(false)
const freeExploreError = ref('')
const showExploreModal = ref(false)
const exploreInputRef = ref<HTMLInputElement | null>(null)
const exploreHints = ['AI 发展史', '太空探索', '商鞅变法', '工业革命', '法国大革命', '人工智能伦理']
// 英雄卡牌选人
const showHeroSelection = ref(false)
const currentExploreTopic = ref('')
const selectedHeroName = ref('')
let searchLoadingTimer: ReturnType<typeof setTimeout> | null = null
let searchAbortTimer: ReturnType<typeof setTimeout> | null = null

// 弹窗打开时自动聚焦输入框
watch(showExploreModal, (val) => {
  if (val) {
    freeExploreError.value = ''
    nextTick(() => { exploreInputRef.value?.focus() })
  }
})

const ragSearchResults = ref<LocalSearchResult[]>([])

const homeFeed = ref<HomeFeedResponse>({
  recommended: [],
  explored: [],
  recommended_total: 0,
  explored_total: 0,
})

const exploredIdSet = computed(() => new Set(homeFeed.value.explored.map(e => e.id)))
const eventById = computed(() => new Map(historyEvents.map(event => [event.id, event])))
const eventIdByName = computed(() => {
  const pairs = historyEvents.map(event => [normalizeSearchText(event.name), event.id] as const)
  return new Map(pairs)
})

function normalizeSearchText(value: string): string {
  return value.trim().toLowerCase().replace(/\s+/g, '')
}

function buildSearchResult(
  event: HistoryEvent,
  score: number,
  source: string,
  description?: string,
): LocalSearchResult {
  return {
    id: event.id,
    name: event.name,
    year: event.year,
    region: event.region,
    importance: event.importance,
    description: description || event.description,
    score,
    source,
  }
}

function resolveEventFromSearchCandidate(candidate: Partial<LocalSearchResult> & { title?: string }): HistoryEvent | null {
  if (candidate.id) {
    const byId = eventById.value.get(candidate.id)
    if (byId) return byId
  }
  const nameKey = normalizeSearchText(candidate.name || candidate.title || '')
  if (!nameKey) return null
  const eventId = eventIdByName.value.get(nameKey)
  if (!eventId) return null
  return eventById.value.get(eventId) || null
}

function isSearchRelevant(candidate: Partial<LocalSearchResult> & { title?: string }, query: string): boolean {
  const normalizedQuery = normalizeSearchText(query)
  if (!normalizedQuery) return true
  const haystacks = [
    candidate.name,
    candidate.title,
    candidate.description,
  ]
    .filter((value): value is string => Boolean(value))
    .map(value => normalizeSearchText(value))
  return haystacks.some(value => value.includes(normalizedQuery))
}

function dedupeSearchResults(results: LocalSearchResult[]): LocalSearchResult[] {
  const deduped = new Map<string, LocalSearchResult>()
  for (const result of results) {
    const existing = deduped.get(result.id)
    if (!existing || result.score > existing.score) {
      deduped.set(result.id, result)
    }
  }
  return [...deduped.values()]
}

function sortSearchResults(results: LocalSearchResult[], query: string): LocalSearchResult[] {
  const normalizedQuery = normalizeSearchText(query)
  return [...results].sort((a, b) => {
    const aName = normalizeSearchText(a.name)
    const bName = normalizeSearchText(b.name)
    const aExact = aName === normalizedQuery ? 3 : aName.startsWith(normalizedQuery) ? 2 : aName.includes(normalizedQuery) ? 1 : 0
    const bExact = bName === normalizedQuery ? 3 : bName.startsWith(normalizedQuery) ? 2 : bName.includes(normalizedQuery) ? 1 : 0
    if (aExact !== bExact) return bExact - aExact
    if (a.score !== b.score) return b.score - a.score
    if (a.importance !== b.importance) return b.importance - a.importance
    return a.year === b.year ? a.name.localeCompare(b.name, 'zh-CN') : (b.year || 0) - (a.year || 0)
  })
}

function sanitizeRagSearchResults(query: string, items: LocalSearchResult[]): LocalSearchResult[] {
  const out: LocalSearchResult[] = []
  for (const item of items) {
    if (!isSearchRelevant(item, query)) continue
    const event = resolveEventFromSearchCandidate(item)
    if (!event) continue
    out.push(buildSearchResult(
      event,
      Math.max(item.score || 0, event.importance),
      item.source || 'rag',
      item.description,
    ))
  }
  return out
}

function onSearchInput() {
  showSearchDropdown.value = true
  searchLoading.value = true
  if (searchLoadingTimer) clearTimeout(searchLoadingTimer)
  if (searchAbortTimer) clearTimeout(searchAbortTimer)
  searchLoadingTimer = setTimeout(() => {
    searchLoading.value = false
  }, 600)
  searchAbortTimer = setTimeout(async () => {
    const q = searchQuery.value.trim()
    if (!q) { ragSearchResults.value = []; return }
    try {
      // 优先调用混合搜索 (事件表 + RAG 知识库), 失败时降级到纯 RAG
      try {
        const res = await ragApi.hybridSearch({ query: q, top_k: 5 })
        ragSearchResults.value = sanitizeRagSearchResults(q, (res.data || []) as LocalSearchResult[])
      } catch {
        const res = await ragApi.search({ query: q, top_k: 5 })
        ragSearchResults.value = sanitizeRagSearchResults(q, (res.data || []) as LocalSearchResult[])
      }
    } catch {
      ragSearchResults.value = []
    }
  }, 300)
}

const searchResults = computed(() => {
  const query = searchQuery.value.trim()
  if (!query) return []

  const localResults = searchEvents(query)
    .slice(0, 8)
    .map(event => buildSearchResult(event, event.importance + 20, 'event_table'))

  const merged = dedupeSearchResults([...localResults, ...ragSearchResults.value])
  return sortSearchResults(merged, query).slice(0, 6)
})

const filters = computed(() => [
  { value: 'all' as const, label: t('home.quickFilter.all') },
  { value: 'china' as const, label: t('home.quickFilter.china') },
  { value: 'foreign' as const, label: t('home.quickFilter.foreign') }
])

// 抽屉事件列表: 探索过的优先, 再用推荐补足, 再去重
const drawerEvents = computed<HistoryEvent[]>(() => {
  const seen = new Set<string>()
  const out: HistoryEvent[] = []
  for (const e of homeFeed.value.explored) {
    if (!seen.has(e.id)) {
      seen.add(e.id)
      out.push(e as HistoryEvent)
    }
  }
  for (const e of homeFeed.value.recommended) {
    if (!seen.has(e.id)) {
      seen.add(e.id)
      out.push(e)
    }
  }
  if (out.length > 0) {
    if (appStore.currentFilter === 'china') return out.filter(e => e.region === 'china')
    if (appStore.currentFilter === 'foreign') return out.filter(e => e.region === 'foreign')
    return out
  }
  // 降级: home feed 失败时, 使用本地 historyEvents
  if (appStore.currentFilter === 'all') return historyEvents
  return historyEvents.filter(e => e.region === appStore.currentFilter)
})

const filteredEvents = computed(() => drawerEvents.value)

function formatEventYear(year: number | null): string {
  if (year === null || year === undefined) return '-'
  return year < 0 ? t('event.bc', { n: Math.abs(year) }) : t('event.year', { n: year })
}

function handleSearchSelect(id: string) {
  if (!eventById.value.has(id)) return
  searchQuery.value = ''
  showSearchDropdown.value = false
  ragSearchResults.value = []
  goToEvent(id)
}

function handleSearchEnter() {
  if (searchResults.value.length > 0) {
    handleSearchSelect(searchResults.value[0].id)
  } else if (searchQuery.value.trim()) {
    showSearchDropdown.value = true
  }
}

function handleSearchBlur() {
  setTimeout(() => { showSearchDropdown.value = false }, 200)
}

function handleLogout() {
  authStore.logout()
  showUserMenu.value = false
  appStore.showToast('success', t('toast.signedOut'))
}

// 升级会员占位按钮: 触发 paywall_clicked 埋点 + 弹提示
function handleUpgradeClick() {
  trackEvent('paywall_clicked', {
    topic: (dialogueStore.currentTopic || freeExploreTopic.value || 'unknown').trim() || 'unknown',
  })
  // 简单占位 alert, 提示会员功能即将上线
  if (typeof window !== 'undefined') {
    window.alert(t('home.upgradeAlert'))
  }
}

function handleClickOutside(e: MouseEvent) {
  const target = e.target as HTMLElement
  if (!target.closest('.user-area')) {
    showUserMenu.value = false
  }
}

function goToEvent(id: string) {
  router.push({ name: 'EventDetail', params: { id } })
}

async function handleFreeExplore() {
  const topic = freeExploreTopic.value.trim()
  if (!topic) {
    freeExploreError.value = '请输入话题'
    return
  }
  // 未登录需先登录 (在弹窗内提示, 不跳转路由)
  if (!authStore.isLoggedIn) {
    freeExploreError.value = '请先登录后再开启时空探索'
    return
  }
  // 关闭探索弹窗，展示英雄卡牌选人界面
  showExploreModal.value = false
  currentExploreTopic.value = topic
  showHeroSelection.value = true
}

function navigateToDialogue(topic: string) {
  const eventId = `dynamic_${topic.replace(/[^\w一-龥]+/g, '_').slice(0, 32) || 'unknown'}`
  router.push({ name: 'Dialogue', params: { eventId } })
}

async function onHeroSelect(hero: HeroPersona) {
  showHeroSelection.value = false
  selectedHeroName.value = hero.name
  freeExploreLoading.value = true
  freeExploreError.value = ''
  try {
    await dialogueStore.startDynamicFromTopic(currentExploreTopic.value, hero.hero_id)
    navigateToDialogue(currentExploreTopic.value)
  } catch (err: any) {
    // 失败: 关闭英雄卡, 回到探索弹窗, 保留 topic 便于重试
    showHeroSelection.value = false
    showExploreModal.value = true
    freeExploreError.value = err?.message || '开启时空对话失败, 请稍后重试'
  } finally {
    freeExploreLoading.value = false
    selectedHeroName.value = ''
  }
}

async function onHeroSkip() {
  showHeroSelection.value = false
  selectedHeroName.value = ''
  freeExploreLoading.value = true
  freeExploreError.value = ''
  try {
    await dialogueStore.startDynamicFromTopic(currentExploreTopic.value)
    navigateToDialogue(currentExploreTopic.value)
  } catch (err: any) {
    // 失败: 关闭英雄卡, 回到探索弹窗, 保留 topic 便于重试
    showHeroSelection.value = false
    showExploreModal.value = true
    freeExploreError.value = err?.message || '开启时空对话失败, 请稍后重试'
  } finally {
    freeExploreLoading.value = false
    selectedHeroName.value = ''
  }
}

function closeHeroSelection() {
  currentExploreTopic.value = ''
  selectedHeroName.value = ''
  freeExploreError.value = ''
  freeExploreTopic.value = ''
}

function handleLoginRedirect() {
  router.push({ name: 'Login', query: { redirect: '/' } })
  showExploreModal.value = false
}

// 英雄卡关闭时清理状态, 避免下次打开残留
watch(showHeroSelection, (val) => {
  if (!val) closeHeroSelection()
})

async function retryLoad() {
  const { loadEvents } = await import('@/data/events')
  await loadEvents()
  await loadHomeFeed()
}

async function loadHomeFeed() {
  try {
    const sid = getSessionId()
    const res = await eventsApi.getHomeFeed({ session_id: sid })
    homeFeed.value = res.data || { recommended: [], explored: [], recommended_total: 0, explored_total: 0 }
  } catch (e) {
    console.warn('[HistoricalStarlink] Home feed load failed, fallback to local events', e)
    homeFeed.value = { recommended: [], explored: [], recommended_total: 0, explored_total: 0 }
  }
}

const loadingInitial = ref(true)

onMounted(async () => {
  authStore.init()
  document.addEventListener('click', handleClickOutside)
  // 并行加载: 事件全集 + 首页 feed
  try {
    await Promise.all([loadEvents(), loadHomeFeed()])
  } finally {
    loadingInitial.value = false
  }
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

/* ============================================================
 * 时空探索首页 · 布局优化要点 (v2)
 * ------------------------------------------------------------
 * 1) 顶层使用 CSS Grid 网格,Logo / Nav / User 三段式对齐
 * 2) 抽屉触发器右移,避开主图左侧星点密集区
 * 3) 自由探索面板加最大宽 / 触摸区,签名签条移到右侧
 * 4) 断点 1200 / 1024 / 768 / 480 四级响应式
 * 5) 抽屉事件按 importance 视觉分级, 顶部加分区标签
 * 6) 全局 focus-visible 焦点环 + 减少动效适配
 * 7) 顶部 brand 增加副标题, 抽屉项增加 importance 热度条
 * 8) 自由探索面板加时空主题的扫描线/光晕装饰
 * ============================================================ */
<style scoped>
.home-view {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #02050b;
}

/* ---------- 0) 全局焦点环 + 减少动效适配 ---------- */
.home-view :focus { outline: none; }
.home-view :focus-visible {
  outline: 2px solid rgba(139, 255, 225, 0.95);
  outline-offset: 2px;
  box-shadow: 0 0 0 4px rgba(139, 255, 225, 0.18);
  border-radius: 4px;
}
@media (prefers-reduced-motion: reduce) {
  .home-view,
  .home-view *,
  .home-view *::before,
  .home-view *::after {
    animation-duration: 0.001ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.001ms !important;
  }
}

/* ---------- 0.b) 环境装饰层: 顶部扫描线 + 角落光晕 ---------- */
.home-view::before,
.home-view::after {
  content: '';
  position: fixed;
  pointer-events: none;
  z-index: 1;
}
.home-view::before {
  /* 横向扫描线 */
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent 0%, rgba(139, 255, 225, 0.4) 50%, transparent 100%);
  animation: homeScan 12s linear infinite;
  opacity: 0.5;
}
@keyframes homeScan {
  0%   { transform: translateY(0); opacity: 0; }
  5%   { opacity: 0.6; }
  95%  { opacity: 0.6; }
  100% { transform: translateY(100vh); opacity: 0; }
}
.home-view::after {
  /* 右下角柔和光晕 */
  right: -120px;
  bottom: -120px;
  width: 320px;
  height: 320px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 53, 243, 0.08) 0%, transparent 70%);
  filter: blur(8px);
  animation: cornerBreathe 8s ease-in-out infinite;
}
@keyframes cornerBreathe {
  0%, 100% { opacity: 0.5; transform: scale(1); }
  50%      { opacity: 0.9; transform: scale(1.08); }
}

/* ---------- 1) 顶部导航栏: Grid 三栏式, 不再换行 ---------- */
.app-header {
  position: fixed;
  top: 18px;
  left: 24px;
  right: 24px;
  z-index: var(--z-header);
  min-height: 52px;
  display: grid;
  /* 左侧 logo / 中间 nav / 右侧 user */
  grid-template-columns: auto 1fr auto;
  align-items: center;
  column-gap: clamp(12px, 1.6vw, 24px);
  padding: 10px clamp(14px, 1.8vw, 22px);
  background: rgba(2, 5, 11, 0.5);
  border: 1px solid rgba(139, 255, 225, 0.78);
  border-radius: 8px;
  box-shadow: 0 0 28px rgba(139, 255, 225, 0.08);
  backdrop-filter: blur(10px);
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.logo-icon,
.item-icon,
.title-icon {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #8bffe1;
  box-shadow: 0 0 16px rgba(139, 255, 225, 0.95);
  flex: 0 0 auto;
  position: relative;
}

/* logo 图标双层光晕: 内核 + 外圈 */
.logo-icon::after {
  content: '';
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  border: 1px solid rgba(139, 255, 225, 0.35);
  animation: logoOrbit 4s linear infinite;
}
@keyframes logoOrbit {
  to { transform: rotate(360deg); }
}

.logo-text {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}

.logo h1 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 800;
  color: #f3fff9;
  letter-spacing: 0.04em;
  white-space: nowrap;
  text-shadow: 0 0 18px rgba(139, 255, 225, 0.34);
  line-height: 1.1;
}

.logo-subtitle {
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 500;
  color: rgba(139, 255, 225, 0.55);
  letter-spacing: 0.18em;
  text-transform: uppercase;
  white-space: nowrap;
  line-height: 1;
}

.filter-nav,
.page-nav,
.drawer-filters {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-btn,
.nav-link,
.drawer-filter-btn,
.login-btn {
  min-height: 30px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 6px 13px;
  background: rgba(2, 5, 11, 0.46);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 0;
  color: rgba(238, 249, 255, 0.82);
  font-size: 12px;
  line-height: 1;
  text-decoration: none;
  transition: border-color 0.18s ease, color 0.18s ease, background 0.18s ease, box-shadow 0.18s ease;
}

.filter-btn:hover,
.nav-link:hover,
.drawer-filter-btn:hover,
.login-btn:hover {
  color: #ffffff;
  border-color: rgba(139, 255, 225, 0.78);
  background: rgba(139, 255, 225, 0.08);
  text-shadow: none;
}

.filter-btn.active,
.nav-link--active,
.nav-link.router-link-exact-active,
.drawer-filter-btn.active {
  color: #ffffff;
  border-color: rgba(139, 255, 225, 0.95);
  box-shadow: 0 0 16px rgba(139, 255, 225, 0.12);
}

.user-area {
  position: relative;
  justify-self: end;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

/* 让 nav 居中, 避免被 user 挤到 */
.page-nav {
  justify-self: center;
  flex-wrap: wrap;
  justify-content: center;
}

.upgrade-btn {
  min-height: 30px;
  padding: 5px 14px;
  background: linear-gradient(180deg, rgba(212, 168, 75, 0.28), rgba(212, 168, 75, 0.10));
  border: 1px solid rgba(212, 168, 75, 0.7);
  border-radius: 0;
  color: #f5e3b1;
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-shadow: 0 0 8px rgba(212, 168, 75, 0.5);
  cursor: pointer;
  transition: background 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease, color 0.18s ease;
}

.upgrade-btn:hover {
  background: linear-gradient(180deg, rgba(212, 168, 75, 0.42), rgba(212, 168, 75, 0.16));
  color: #fff7d8;
  box-shadow: 0 0 18px rgba(212, 168, 75, 0.32);
  transform: translateY(-1px);
}

.locale-area {
  display: inline-flex;
  align-items: center;
  flex: 0 0 auto;
  min-width: 0;
  margin-left: 14px;
}

.user-menu {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 32px;
  padding: 3px 10px 3px 3px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  color: rgba(238, 249, 255, 0.84);
  cursor: pointer;
  transition: border-color 0.18s ease, background 0.18s ease;
}

.user-menu:hover {
  border-color: rgba(139, 255, 225, 0.78);
  background: rgba(139, 255, 225, 0.08);
}

.user-avatar,
.dropdown-avatar {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: rgba(139, 255, 225, 0.14);
  border: 1px solid rgba(139, 255, 225, 0.56);
  color: #8bffe1;
  font-size: 12px;
  font-weight: 800;
}

.user-name {
  max-width: 86px;
  overflow: hidden;
  color: #eef9ff;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-dropdown,
.search-dropdown {
  position: absolute;
  background: rgba(2, 6, 13, 0.9);
  border: 1px solid rgba(139, 255, 225, 0.5);
  border-radius: 4px;
  backdrop-filter: blur(14px);
  box-shadow: 0 18px 44px rgba(0, 0, 0, 0.48);
}

.user-dropdown {
  top: calc(100% + 10px);
  right: 0;
  z-index: var(--z-modal);
  width: 232px;
  overflow: hidden;
}

.dropdown-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px;
}

.dropdown-info {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 2px;
}

.dropdown-name {
  color: #ffffff;
  font-size: 13px;
  font-weight: 700;
}

.dropdown-email {
  overflow: hidden;
  color: rgba(238, 249, 255, 0.58);
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dropdown-divider {
  height: 1px;
  margin: 0 12px;
  background: rgba(255, 255, 255, 0.12);
}

.dropdown-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 11px 14px;
  background: transparent;
  border: 0;
  color: rgba(238, 249, 255, 0.72);
  font-size: 12px;
  text-align: left;
}

.dropdown-item:hover {
  background: rgba(139, 255, 225, 0.08);
  color: #ffffff;
}

.backend-banner {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 24px;
  background: linear-gradient(90deg, rgba(255, 100, 60, 0.16), rgba(212, 168, 75, 0.10));
  border-bottom: 1px solid rgba(255, 100, 60, 0.42);
  color: var(--text-light);
  font-size: 13px;
}

.banner-icon {
  font-size: 18px;
  color: #ff8a4d;
  text-shadow: 0 0 12px rgba(255, 138, 77, 0.5);
}

.banner-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}

.banner-text strong {
  color: #ffba6b;
  font-size: 13px;
}

.banner-text span {
  color: var(--text-muted);
  font-size: 12px;
}

.banner-retry {
  padding: 6px 16px;
  background: rgba(255, 138, 77, 0.14);
  border: 1px solid rgba(255, 138, 77, 0.5);
  border-radius: var(--radius-full);
  color: #ffba6b;
  font-size: 12px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.banner-retry:hover {
  background: rgba(255, 138, 77, 0.24);
  color: #ffffff;
}

.banner-slide-enter-active,
.banner-slide-leave-active {
  transition: all 0.4s ease;
}

.banner-slide-enter-from,
.banner-slide-leave-to {
  opacity: 0;
  transform: translateY(-12px);
}

.home-main,
.cosmic-section {
  position: relative;
  flex: 1;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.cosmic-overlay {
  position: absolute;
  left: 50%;
  top: clamp(80px, 14vh, 140px);
  transform: translateX(-50%);
  z-index: 20;
  width: min(720px, calc(100vw - 56px));
  text-align: center;
  pointer-events: none;
}

.cosmic-loading {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  z-index: 5;
  color: rgba(255, 255, 255, 0.78);
  background: radial-gradient(circle at 50% 50%, rgba(20, 30, 50, 0.35), transparent 70%);
}

.cosmic-loading__spinner {
  width: 44px;
  height: 44px;
  border: 2px solid rgba(73, 247, 255, 0.25);
  border-top-color: #49f7ff;
  border-radius: 50%;
  animation: cosmic-spin 0.9s linear infinite;
  box-shadow: 0 0 18px rgba(73, 247, 255, 0.35);
}

.cosmic-loading__text {
  margin: 0;
  font-size: 14px;
  letter-spacing: 0.12em;
  color: rgba(255, 255, 255, 0.72);
}

@keyframes cosmic-spin {
  to { transform: rotate(360deg); }
}

/* ================================================================
 * 时空探索 FAB (浮动触发按钮) — 悬浮在右下角, 不遮挡星图
 * ================================================================ */
.explore-fab {
  position: fixed;
  right: clamp(16px, 3vw, 32px);
  bottom: clamp(20px, 4vh, 44px);
  z-index: 25;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 20px 14px 16px;
  background:
    linear-gradient(135deg, rgba(2, 6, 13, 0.88), rgba(2, 6, 13, 0.72)),
    radial-gradient(circle at 30% 50%, rgba(139, 255, 225, 0.12), transparent 60%);
  border: 1px solid rgba(139, 255, 225, 0.6);
  border-radius: 40px;
  cursor: pointer;
  backdrop-filter: blur(14px);
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.45),
    0 0 20px rgba(139, 255, 225, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.06);
  transition: all 0.28s cubic-bezier(0.16, 1, 0.3, 1);
  outline: none;
}

.explore-fab:hover {
  border-color: rgba(139, 255, 225, 0.9);
  box-shadow:
    0 12px 44px rgba(0, 0, 0, 0.5),
    0 0 36px rgba(139, 255, 225, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.08);
  transform: translateY(-2px);
}

.explore-fab--active {
  border-color: rgba(139, 255, 225, 0.95);
  box-shadow: 0 0 40px rgba(139, 255, 225, 0.25);
}

.explore-fab__ring {
  position: absolute;
  inset: -3px;
  border-radius: 40px;
  border: 1px solid rgba(139, 255, 225, 0.2);
  animation: fabOrbit 3s linear infinite;
  pointer-events: none;
}
@keyframes fabOrbit {
  to { transform: rotate(360deg); }
}

.explore-fab__core {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #8bffe1;
  box-shadow: 0 0 14px rgba(139, 255, 225, 0.9), 0 0 28px rgba(139, 255, 225, 0.4);
  animation: fabPulse 2.4s ease-in-out infinite;
  flex-shrink: 0;
}
@keyframes fabPulse {
  0%, 100% { transform: scale(1); opacity: 0.85; }
  50% { transform: scale(1.25); opacity: 1; }
}

.explore-fab__label {
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: #dffff6;
  white-space: nowrap;
  text-shadow: 0 0 10px rgba(139, 255, 225, 0.3);
}

/* ================================================================
 * 时空探索弹窗 — 居中弹出, 星空玻璃质感
 * ================================================================ */
.explore-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: var(--z-modal, 100);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(2, 5, 11, 0.6);
  backdrop-filter: blur(8px);
}

.explore-modal {
  position: relative;
  width: min(560px, 100%);
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 36px 32px 28px;
  background:
    linear-gradient(170deg, rgba(4, 10, 22, 0.94), rgba(2, 6, 13, 0.88)),
    radial-gradient(circle at 0% 0%, rgba(139, 255, 225, 0.08), transparent 40%),
    radial-gradient(circle at 100% 100%, rgba(255, 53, 243, 0.05), transparent 40%);
  border: 1px solid rgba(139, 255, 225, 0.45);
  border-radius: 16px;
  backdrop-filter: blur(20px);
  box-shadow:
    0 32px 80px rgba(0, 0, 0, 0.55),
    0 0 40px rgba(139, 255, 225, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.06);
  overflow: hidden;
}

/* 扫描线装饰 */
.explore-modal__scanline {
  position: absolute;
  top: 0;
  left: 10%;
  right: 10%;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(139, 255, 225, 0.65), transparent);
  animation: modalScan 3s ease-in-out infinite;
  pointer-events: none;
}
@keyframes modalScan {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.9; }
}

.explore-modal__close {
  position: absolute;
  top: 12px;
  right: 14px;
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 6px;
  color: rgba(238, 249, 255, 0.6);
  font-size: 18px;
  cursor: pointer;
  transition: all 0.18s ease;
}
.explore-modal__close:hover {
  border-color: rgba(139, 255, 225, 0.6);
  color: #8bffe1;
  background: rgba(139, 255, 225, 0.08);
}

.explore-modal__header {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

/* 中央旋转图腾 */
.explore-modal__glyph {
  position: relative;
  width: 48px;
  height: 48px;
  display: grid;
  place-items: center;
}
.glyph-orbit {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 1px solid rgba(139, 255, 225, 0.3);
  border-top-color: rgba(139, 255, 225, 0.8);
  animation: cosmic-spin 3s linear infinite;
}
.glyph-core {
  font-size: 22px;
  color: #8bffe1;
  text-shadow: 0 0 18px rgba(139, 255, 225, 0.8), 0 0 36px rgba(139, 255, 225, 0.4);
  animation: fabPulse 2.6s ease-in-out infinite;
}

.explore-modal__title {
  margin: 0;
  font-family: var(--font-serif);
  font-size: clamp(20px, 3.2vw, 26px);
  font-weight: 900;
  color: #ffffff;
  letter-spacing: 0.02em;
  text-shadow: 0 0 18px rgba(65, 166, 255, 0.28), 0 2px 12px rgba(0, 0, 0, 0.6);
}

.explore-modal__subtitle {
  margin: 0;
  font-size: 13px;
  color: rgba(226, 246, 255, 0.65);
  line-height: 1.6;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
}

.explore-modal__form {
  display: flex;
  gap: 10px;
  align-items: stretch;
}

.explore-modal__input {
  flex: 1;
  min-width: 0;
  height: 46px;
  padding: 0 18px;
  background: rgba(2, 5, 11, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.22);
  border-radius: 8px;
  color: #ffffff;
  font-size: 14px;
  outline: none;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}
.explore-modal__input::placeholder {
  color: rgba(238, 249, 255, 0.38);
}
.explore-modal__input:focus {
  border-color: rgba(139, 255, 225, 0.85);
  box-shadow: 0 0 20px rgba(139, 255, 225, 0.18);
}
.explore-modal__input:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.explore-modal__btn {
  flex: 0 0 auto;
  height: 46px;
  padding: 0 24px;
  background: linear-gradient(180deg, rgba(139, 255, 225, 0.30), rgba(139, 255, 225, 0.10));
  border: 1px solid rgba(139, 255, 225, 0.85);
  border-radius: 8px;
  color: #dffff6;
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.08em;
  cursor: pointer;
  transition: background 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
  white-space: nowrap;
}
.explore-modal__btn:hover:not(:disabled) {
  background: linear-gradient(180deg, rgba(139, 255, 225, 0.44), rgba(139, 255, 225, 0.18));
  box-shadow: 0 0 24px rgba(139, 255, 225, 0.32);
  transform: translateY(-1px);
}
.explore-modal__btn:active:not(:disabled) {
  transform: translateY(0) scale(0.98);
}
.explore-modal__btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.explore-modal__error {
  color: #ff8a4d;
  font-size: 12px;
  text-align: center;
  text-shadow: 0 0 6px rgba(255, 138, 77, 0.3);
}

/* 快捷话题标签 */
.explore-modal__hints {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
  padding-top: 4px;
}
.explore-hint-tag {
  padding: 5px 14px;
  background: rgba(139, 255, 225, 0.06);
  border: 1px solid rgba(139, 255, 225, 0.25);
  border-radius: 20px;
  color: rgba(238, 249, 255, 0.72);
  font-size: 12px;
  font-family: var(--font-mono);
  cursor: pointer;
  transition: all 0.18s ease;
  white-space: nowrap;
}
.explore-hint-tag:hover {
  background: rgba(139, 255, 225, 0.14);
  border-color: rgba(139, 255, 225, 0.6);
  color: #ffffff;
  transform: translateY(-1px);
}

/* 未登录提示下的「前往登录」快捷按钮 */
.explore-modal__login-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin: 0 auto;
  padding: 8px 20px;
  background: linear-gradient(180deg, rgba(212, 168, 75, 0.18), rgba(212, 168, 75, 0.06));
  border: 1px solid rgba(212, 168, 75, 0.6);
  border-radius: 6px;
  color: #f5e3b1;
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.1em;
  cursor: pointer;
  transition: all 0.18s ease;
}
.explore-modal__login-link:hover {
  background: linear-gradient(180deg, rgba(212, 168, 75, 0.32), rgba(212, 168, 75, 0.12));
  border-color: rgba(212, 168, 75, 0.95);
  box-shadow: 0 0 18px rgba(212, 168, 75, 0.32);
  transform: translateY(-1px);
}
.login-arrow { font-size: 14px; }

/* 弹窗过渡动画 */
.explore-modal-enter-active {
  transition: opacity 0.25s ease;
}
.explore-modal-enter-active .explore-modal {
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.25s ease;
}
.explore-modal-leave-active {
  transition: opacity 0.18s ease;
}
.explore-modal-leave-active .explore-modal {
  transition: transform 0.18s ease, opacity 0.18s ease;
}
.explore-modal-enter-from {
  opacity: 0;
}
.explore-modal-enter-from .explore-modal {
  opacity: 0;
  transform: translateY(24px) scale(0.96);
}
.explore-modal-leave-to {
  opacity: 0;
}
.explore-modal-leave-to .explore-modal {
  opacity: 0;
  transform: translateY(12px) scale(0.98);
}

.hero-selection-overlay {
  position: fixed;
  inset: 0;
  z-index: var(--z-modal, 100);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(2, 5, 11, 0.72);
  backdrop-filter: blur(8px);
}

.hero-selection-modal {
  width: min(960px, 100%);
  max-height: 90vh;
  overflow-y: auto;
}

.hero-fade-enter-active,
.hero-fade-leave-active {
  transition: opacity 0.2s ease;
}

.hero-fade-enter-from,
.hero-fade-leave-to {
  opacity: 0;
}

/* 角色穿越中全屏遮罩 */
.traversing-overlay {
  position: fixed;
  inset: 0;
  z-index: calc(var(--z-modal, 100) + 10);
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(2, 5, 11, 0.92);
  backdrop-filter: blur(16px);
  cursor: not-allowed;
}

.traversing-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  text-align: center;
  animation: traversingPulse 2s ease-in-out infinite;
}

.traversing-spinner {
  width: 60px;
  height: 60px;
  border: 3px solid rgba(139, 255, 225, 0.15);
  border-top-color: #8bffe1;
  border-radius: 50%;
  animation: cosmic-spin 1s linear infinite;
  box-shadow: 0 0 30px rgba(139, 255, 225, 0.3);
}

.traversing-hero {
  margin-top: -10px;
}

.traversing-symbol {
  font-size: 2.5rem;
  color: #8bffe1;
  text-shadow: 0 0 30px rgba(139, 255, 225, 0.8), 0 0 60px rgba(139, 255, 225, 0.4);
  animation: traversingGlow 1.5s ease-in-out infinite alternate;
}

.traversing-title {
  margin: 0;
  color: #ffffff;
  font-family: var(--font-serif);
  font-size: clamp(24px, 4vw, 36px);
  font-weight: 900;
  letter-spacing: 0.15em;
  text-shadow: 0 0 20px rgba(139, 255, 225, 0.5), 0 2px 16px rgba(0, 0, 0, 0.6);
}

.traversing-hint {
  margin: 0;
  color: rgba(139, 255, 225, 0.8);
  font-size: 14px;
  letter-spacing: 0.1em;
}

.traversing-progress {
  width: 200px;
  height: 3px;
  background: rgba(139, 255, 225, 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.traversing-progress-bar {
  width: 40%;
  height: 100%;
  background: linear-gradient(90deg, transparent, #8bffe1, transparent);
  border-radius: 2px;
  animation: traversingSlide 1.2s ease-in-out infinite;
}

@keyframes traversingPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.02); }
}

@keyframes traversingGlow {
  from { text-shadow: 0 0 20px rgba(139, 255, 225, 0.6), 0 0 40px rgba(139, 255, 225, 0.3); }
  to { text-shadow: 0 0 40px rgba(139, 255, 225, 1), 0 0 80px rgba(139, 255, 225, 0.5); }
}

@keyframes traversingSlide {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(350%); }
}

@media (max-width: 680px) {
  .hero-selection-overlay {
    padding: 12px;
  }
}

.hero-copy {
  width: min(560px, 100%);
  margin: 0 auto;
}

.cosmic-title {
  margin: 0 0 14px;
  color: #ffffff;
  font-family: var(--font-serif);
  font-size: clamp(30px, 4.6vw, 58px);
  font-weight: 900;
  line-height: 1.04;
  letter-spacing: 0;
  text-align: center;
  text-shadow: 0 0 18px rgba(65, 166, 255, 0.32), 0 2px 16px rgba(0, 0, 0, 0.76);
}

.cosmic-subtitle {
  width: min(440px, 100%);
  margin: 0 auto;
  color: rgba(226, 246, 255, 0.78);
  font-size: 14px;
  line-height: 1.7;
  text-align: center;
  text-shadow: 0 2px 12px rgba(0, 0, 0, 0.72);
}

.search-bar {
  position: relative;
  left: auto;
  bottom: auto;
  width: 100%;
  display: flex;
  align-items: center;
  margin-top: 0;
  pointer-events: auto;
}

.search-input-wrap {
  position: relative;
  width: 100%;
}

.search-input {
  width: 100%;
  height: 40px;
  padding: 0 76px 0 16px;
  background: rgba(2, 5, 11, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.24);
  border-radius: 0;
  color: #ffffff;
  font-size: 13px;
  outline: none;
  backdrop-filter: blur(8px);
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.search-input::placeholder {
  color: rgba(238, 249, 255, 0.42);
}

.search-input:focus {
  border-color: rgba(139, 255, 225, 0.8);
  box-shadow: 0 0 18px rgba(139, 255, 225, 0.12);
}

.search-btn {
  position: absolute;
  top: 4px;
  right: 5px;
  min-width: 56px;
  height: 30px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 0 10px;
  border: 1px solid rgba(139, 255, 225, 0.78);
  border-radius: 0;
  background: linear-gradient(180deg, rgba(139, 255, 225, 0.2), rgba(139, 255, 225, 0.08));
  color: #dffff6;
  box-shadow: 0 0 14px rgba(139, 255, 225, 0.12);
  transition: transform 0.18s ease, background 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.search-btn:hover {
  transform: scale(1.06);
  background: linear-gradient(180deg, rgba(139, 255, 225, 0.34), rgba(139, 255, 225, 0.12));
  border-color: rgba(139, 255, 225, 0.96);
  box-shadow: 0 0 20px rgba(139, 255, 225, 0.24);
}

.search-icon {
  display: block;
  width: 8px;
  height: 8px;
  border-right: 2px solid currentColor;
  border-bottom: 2px solid currentColor;
  transform: rotate(-45deg);
}

.search-btn-label {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0;
}

.search-loading-bar {
  position: relative;
  height: 2px;
  overflow: hidden;
  opacity: 0;
  transition: opacity 0.2s;
  margin-top: 2px;
}

.search-loading-bar.active {
  opacity: 1;
}

.search-loading-bar .loading-track {
  position: absolute;
  top: 0;
  left: -40%;
  width: 40%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(139, 255, 225, 0.8), transparent);
  animation: searchLoadingSlide 0.8s ease-in-out infinite;
}

@keyframes searchLoadingSlide {
  0% { left: -40%; }
  100% { left: 100%; }
}

.search-dropdown {
  top: calc(100% + 8px);
  left: 0;
  right: 0;
  z-index: 60;
  max-height: 280px;
  overflow-y: auto;
  overflow-x: hidden;
}

.search-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 11px 14px;
  border-left: 2px solid transparent;
  cursor: pointer;
  transition: background 0.15s ease, border-color 0.15s ease;
}

.search-item.search-empty {
  justify-content: center;
  cursor: default;
}

.search-item:hover {
  background: rgba(139, 255, 225, 0.08);
  border-left-color: #8bffe1;
}

.search-item.search-empty:hover {
  background: transparent;
  border-left-color: transparent;
}

.search-item-name {
  overflow: hidden;
  color: #ffffff;
  font-size: 13px;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.search-item-meta {
  flex: 0 0 auto;
  color: rgba(238, 249, 255, 0.56);
  font-family: var(--font-mono);
  font-size: 11px;
}

.deerflow-signature {
  /* 由底部居中改为右侧, 避免和探索面板重叠 */
  position: fixed;
  right: 16px;
  bottom: 8px;
  z-index: 30;
  padding: 4px 8px;
  color: rgba(238, 249, 255, 0.32);
  background: transparent;
  border: 0;
  font-size: 10px;
  letter-spacing: 0.05em;
  text-decoration: none;
  transition: color 0.18s ease;
}

.deerflow-signature:hover {
  color: rgba(255, 255, 255, 0.7);
}

.drawer-trigger {
  /* 离开屏幕左边 6px, 不再贴 0; 仍保持纵向居中 */
  position: fixed;
  left: 6px;
  top: 50%;
  transform: translateY(-50%);
  z-index: var(--z-header);
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 16px 8px;
  color: #8bffe1;
  background: linear-gradient(180deg, rgba(2, 5, 11, 0.78), rgba(2, 5, 11, 0.62));
  border: 1px solid rgba(139, 255, 225, 0.56);
  border-left: 0;
  border-radius: 0 8px 8px 0;
  box-shadow: 0 0 24px rgba(139, 255, 225, 0.12), inset 1px 0 0 rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(10px);
  transition: left 0.28s ease, background 0.18s ease, box-shadow 0.18s ease;
  writing-mode: vertical-rl;
  font-family: var(--font-mono);
  font-weight: 600;
}

.drawer-trigger:hover {
  background: linear-gradient(180deg, rgba(139, 255, 225, 0.18), rgba(139, 255, 225, 0.06));
  box-shadow: 0 0 30px rgba(139, 255, 225, 0.24), inset 1px 0 0 rgba(255, 255, 255, 0.1);
}

.drawer-trigger.open {
  left: calc(320px + 6px);
}

.trigger-icon {
  font-size: 18px;
  line-height: 1;
}

.trigger-label {
  font-size: 13px;
  letter-spacing: 2px;
}

.event-drawer {
  position: fixed;
  left: 0;
  top: 80px;
  bottom: 0;
  z-index: calc(var(--z-header) - 1);
  width: 320px;
  display: flex;
  flex-direction: column;
  background:
    linear-gradient(180deg, rgba(2, 6, 13, 0.86), rgba(2, 6, 13, 0.72)),
    radial-gradient(circle at 0% 0%, rgba(139, 255, 225, 0.08), transparent 40%);
  border-right: 1px solid rgba(139, 255, 225, 0.44);
  box-shadow: 12px 0 42px rgba(0, 0, 0, 0.45), inset -1px 0 0 rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(18px);
}

.drawer-header {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 18px 18px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.drawer-hero-title {
  margin: 0;
  color: #ffffff;
  font-family: var(--font-serif);
  font-size: clamp(20px, 2.4vw, 28px);
  font-weight: 900;
  line-height: 1.1;
  letter-spacing: 0;
  text-shadow: 0 0 18px rgba(65, 166, 255, 0.32), 0 2px 16px rgba(0, 0, 0, 0.76);
}

.drawer-title {
  display: flex;
  align-items: center;
  gap: 9px;
  margin: 0;
  color: #ffffff;
  font-family: var(--font-serif);
  font-size: 16px;
  font-weight: 800;
}

.drawer-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px 0;
  position: relative;
  /* 顶部 + 底部柔化遮罩, 提示可滚动 */
  mask-image: linear-gradient(180deg, transparent 0, #000 18px, #000 calc(100% - 18px), transparent 100%);
  -webkit-mask-image: linear-gradient(180deg, transparent 0, #000 18px, #000 calc(100% - 18px), transparent 100%);
  scrollbar-width: thin;
  scrollbar-color: rgba(139, 255, 225, 0.4) transparent;
}

/* 自定义滚动条: Webkit */
.drawer-list::-webkit-scrollbar { width: 4px; }
.drawer-list::-webkit-scrollbar-track { background: transparent; }
.drawer-list::-webkit-scrollbar-thumb {
  background: rgba(139, 255, 225, 0.35);
  border-radius: 2px;
}
.drawer-list::-webkit-scrollbar-thumb:hover { background: rgba(139, 255, 225, 0.6); }

/* 分区标签: sticky 顶部, 玻璃质感 */
.drawer-section-label {
  position: sticky;
  top: 0;
  z-index: 2;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px 8px 22px;
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: rgba(238, 249, 255, 0.55);
  background: linear-gradient(180deg, rgba(2, 6, 13, 0.96), rgba(2, 6, 13, 0.7));
  border-bottom: 1px dashed rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(6px);
}
.section-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  flex: 0 0 auto;
}
.section-dot--cyan { background: #8bffe1; box-shadow: 0 0 8px rgba(139, 255, 225, 0.7); }
.section-dot--gold { background: #d4a84b; box-shadow: 0 0 8px rgba(212, 168, 75, 0.6); }

/* 空状态 */
.drawer-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 48px 16px;
  color: rgba(238, 249, 255, 0.42);
  font-size: 12px;
  letter-spacing: 0.1em;
}
.empty-glyph {
  font-size: 36px;
  color: rgba(139, 255, 225, 0.5);
  text-shadow: 0 0 16px rgba(139, 255, 225, 0.4);
  animation: emptyPulse 2.4s ease-in-out infinite;
}
@keyframes emptyPulse {
  0%, 100% { opacity: 0.4; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.08); }
}

.drawer-item {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 11px 18px 11px 22px;
  border-left: 2px solid transparent;
  cursor: pointer;
  transition: background 0.15s ease, border-color 0.15s ease, transform 0.15s ease;
}

/* 重要性热度条: 左侧 2px 颜色 + 透明度按 importance 1-10 线性插值 */
.drawer-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 8px;
  bottom: 8px;
  width: 2px;
  background: linear-gradient(180deg, rgba(139, 255, 225, 0.85), rgba(139, 255, 225, 0.25));
  opacity: 0;
  transition: opacity 0.15s ease;
}
.drawer-item[data-importance="9"]::before,
.drawer-item[data-importance="10"]::before { opacity: 1; }
.drawer-item[data-importance="7"]::before,
.drawer-item[data-importance="8"]::before { opacity: 0.7; }
.drawer-item[data-importance="5"]::before,
.drawer-item[data-importance="6"]::before { opacity: 0.45; }
.drawer-item[data-importance="3"]::before,
.drawer-item[data-importance="4"]::before { opacity: 0.25; }
.drawer-item[data-importance="1"]::before,
.drawer-item[data-importance="2"]::before { opacity: 0.12; }

.drawer-item:hover {
  background: rgba(139, 255, 225, 0.07);
  border-left-color: #8bffe1;
  transform: translateX(2px);
}

.drawer-item:active {
  transform: translateX(2px) scale(0.99);
}

.drawer-item-left,
.drawer-item-right {
  display: flex;
  align-items: center;
  min-width: 0;
}

.drawer-item-left {
  gap: 10px;
}

.drawer-item-right {
  flex: 0 0 auto;
  gap: 8px;
}

.drawer-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex: 0 0 auto;
  box-shadow: 0 0 12px currentColor;
}

.drawer-dot--china {
  color: #8bffe1;
  background: #8bffe1;
}

.drawer-dot--foreign {
  color: #ff68b8;
  background: #ff68b8;
}

.drawer-item-info {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 3px;
}

.drawer-item-name {
  overflow: hidden;
  color: #ffffff;
  font-size: 13px;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.drawer-item-year,
.drawer-item-score {
  color: rgba(238, 249, 255, 0.56);
  font-family: var(--font-mono);
  font-size: 11px;
}

.drawer-item-region {
  padding: 3px 7px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  color: rgba(238, 249, 255, 0.72);
  font-size: 10px;
}

.drawer-item-region--china {
  border-color: rgba(139, 255, 225, 0.4);
  color: #8bffe1;
}

.drawer-item-region--foreign {
  border-color: rgba(255, 104, 184, 0.42);
  color: #ff8cca;
}

.drawer-slide-enter-active {
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.3s ease;
}

.drawer-slide-leave-active {
  transition: transform 0.24s ease, opacity 0.2s ease;
}

.drawer-slide-enter-from,
.drawer-slide-leave-to {
  opacity: 0;
  transform: translateX(-100%);
}

.menu-fade-enter-active,
.menu-fade-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.menu-fade-enter-from,
.menu-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

/* ============================================================
 * 响应式断点
 * 1200: 平板横屏, nav 缩短
 * 1024: 中等屏幕, 探索面板收紧
 * 768:  平板竖屏 / 手机横屏
 * 480:  手机竖屏, 抽屉全屏化
 * ============================================================ */

/* 1200 横向平板: 收紧内边距 */
@media (max-width: 1200px) {
  .app-header {
    top: 14px;
    left: 16px;
    right: 16px;
    column-gap: 10px;
    padding: 8px 14px;
  }
}

/* 1024 中等屏幕 */
@media (max-width: 1024px) {
  .event-drawer {
    width: 300px;
    top: 76px; /* 同步缩短顶部偏移 */
  }

  .drawer-trigger.open {
    left: calc(300px + 6px);
  }
}

/* 1200 横向平板: 抽屉从 80px 缩到 76px 偏移, 与导航栏下沿对齐 */
@media (max-width: 1200px) {
  .event-drawer { top: 76px; }
}

/* 900 兼容原断点: nav 折行布局, 不再水平挤一行 */
@media (max-width: 900px) {
  .app-header {
    grid-template-columns: 1fr auto;
    row-gap: 10px;
  }

  .page-nav {
    grid-column: 1 / -1;
    justify-self: stretch;
    order: 3;
    overflow-x: auto;
    padding-bottom: 2px;
    flex-wrap: nowrap;
  }

  .user-area {
    order: 2;
  }
}

/* 768 平板竖屏: 全宽组件 */
@media (max-width: 768px) {
  .app-header {
    top: 12px;
    left: 12px;
    right: 12px;
    padding: 8px 12px;
    min-height: 48px;
  }

  .logo h1 {
    font-size: 13px;
  }

  .explore-fab {
    padding: 10px 16px 10px 14px;
  }
  .explore-fab__label {
    font-size: 12px;
  }

  .explore-modal {
    padding: 28px 20px 24px;
    border-radius: 12px;
  }
  .explore-modal__input,
  .explore-modal__btn {
    height: 44px;
    font-size: 13px;
  }
  .explore-hint-tag {
    padding: 4px 10px;
    font-size: 11px;
  }

  .event-drawer {
    width: min(300px, calc(100vw - 56px));
  }

  .drawer-trigger.open {
    left: calc(min(300px, calc(100vw - 56px)) + 6px);
  }
}

/* 680 兼容原断点: 抽屉紧凑 */
@media (max-width: 680px) {
  .event-drawer {
    width: min(300px, calc(100vw - 56px));
  }
}

/* 480 手机竖屏: 抽屉全屏化, 按钮加大 */
@media (max-width: 480px) {
  .app-header {
    grid-template-columns: 1fr;
    row-gap: 8px;
  }

  .logo,
  .user-area {
    justify-self: stretch;
  }

  .user-area {
    flex-wrap: wrap;
  }

  .explore-fab {
    right: 12px;
    bottom: 12px;
    padding: 10px 14px 10px 12px;
  }
  .explore-fab__core {
    width: 8px;
    height: 8px;
  }
  .explore-fab__label {
    font-size: 11px;
    letter-spacing: 0.08em;
  }

  .explore-modal-overlay {
    padding: 12px;
    align-items: flex-end;
  }
  .explore-modal {
    width: 100%;
    padding: 24px 16px 20px;
    border-radius: 14px 14px 0 0;
    max-height: 80vh;
    overflow-y: auto;
  }
  .explore-modal__form {
    flex-direction: column;
    gap: 10px;
  }
  .explore-modal__btn {
    width: 100%;
  }

  /* 抽屉全屏, 触发器上移到底部 (从底部 70vh 抽屉上沿伸出) */
  .drawer-trigger {
    left: 50%;
    top: auto;
    bottom: calc(70vh - 56px);
    transform: translateX(-50%);
    writing-mode: horizontal-tb;
    border-left: 1px solid rgba(139, 255, 225, 0.56);
    border-radius: 6px 6px 0 0;
  }

  .drawer-trigger.open {
    left: 50%;
    bottom: calc(70vh - 56px);
  }

  .event-drawer {
    width: 100vw;
    top: auto;
    bottom: 0;
    left: 0;
    height: 70vh;
    border-right: 0;
    border-top: 1px solid rgba(139, 255, 225, 0.44);
  }

  .deerflow-signature {
    /* 小屏仍保持右下角, 但要避开抽屉底部 */
    right: 12px;
    bottom: calc(70vh + 8px);
  }
}
</style>
