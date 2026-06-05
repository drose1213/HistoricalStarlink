<template>
  <div class="home-view">
    <header class="app-header">
      <div class="logo">
        <span class="logo-icon" aria-hidden="true"></span>
        <h1>{{ t('home.title') }}</h1>
      </div>

      <nav class="page-nav" :aria-label="t('nav.home')">
        <router-link to="/" class="nav-link nav-link--active">{{ t('nav.home') }}</router-link>
        <router-link to="/champions" class="nav-link">{{ t('nav.champions') }}</router-link>
        <router-link to="/leaderboard" class="nav-link">{{ t('nav.leaderboard') }}</router-link>
        <router-link v-if="authStore.user?.is_admin" to="/knowledge-base" class="nav-link">{{ t('nav.knowledge') }}</router-link>
        <router-link v-if="authStore.isLoggedIn" to="/profile" class="nav-link">{{ t('nav.profile') }}</router-link>
      </nav>

      <div class="user-area">
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
            <div
              v-for="event in filteredEvents"
              :key="event.id"
              class="drawer-item"
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
        </div>
      </Transition>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from '@/composables/useI18n'
import CosmicMap from '@/components/CosmicMap.vue'
import LanguageSwitcher from '@/components/LanguageSwitcher.vue'
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
const { t, tf } = useI18n()
const showUserMenu = ref(false)
const drawerOpen = ref(false)
const searchQuery = ref('')
const showSearchDropdown = ref(false)
const searchLoading = ref(false)
let searchLoadingTimer: ReturnType<typeof setTimeout> | null = null
let searchAbortTimer: ReturnType<typeof setTimeout> | null = null

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

function handleClickOutside(e: MouseEvent) {
  const target = e.target as HTMLElement
  if (!target.closest('.user-area')) {
    showUserMenu.value = false
  }
}

function goToEvent(id: string) {
  router.push({ name: 'EventDetail', params: { id } })
}

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

<style scoped>
.home-view {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #02050b;
}

.app-header {
  position: fixed;
  top: 18px;
  left: 24px;
  right: 24px;
  z-index: var(--z-header);
  min-height: 48px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 14px;
  padding: 10px 14px;
  background: rgba(2, 5, 11, 0.5);
  border: 1px solid rgba(139, 255, 225, 0.78);
  border-radius: 8px;
  box-shadow: 0 0 28px rgba(139, 255, 225, 0.08);
  backdrop-filter: blur(10px);
}

.logo {
  display: flex;
  align-items: center;
  gap: 9px;
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
}

.logo h1 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 800;
  color: #f3fff9;
  letter-spacing: 0;
  white-space: nowrap;
  text-shadow: 0 0 18px rgba(139, 255, 225, 0.34);
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
  margin-left: auto;
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
  left: clamp(28px, 7vw, 104px);
  bottom: clamp(72px, 13vh, 142px);
  z-index: 20;
  width: min(440px, calc(100vw - 56px));
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

.hero-copy {
  width: min(420px, 100%);
}

.cosmic-title {
  margin: 0 0 14px;
  color: #ffffff;
  font-family: var(--font-serif);
  font-size: clamp(30px, 4.6vw, 58px);
  font-weight: 900;
  line-height: 1.04;
  letter-spacing: 0;
  text-shadow: 0 0 18px rgba(65, 166, 255, 0.32), 0 2px 16px rgba(0, 0, 0, 0.76);
}

.cosmic-subtitle {
  width: min(360px, 100%);
  margin: 0;
  color: rgba(226, 246, 255, 0.76);
  font-size: 14px;
  line-height: 1.7;
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
  letter-spacing: 0;
  text-decoration: none;
  backdrop-filter: blur(8px);
  transition: color 0.18s ease, border-color 0.18s ease, background 0.18s ease;
}

.deerflow-signature:hover {
  color: rgba(255, 255, 255, 0.78);
  background: rgba(139, 255, 225, 0.06);
  border-color: rgba(139, 255, 225, 0.3);
  text-shadow: none;
}

.drawer-trigger {
  position: fixed;
  left: 0;
  top: 90px;
  z-index: var(--z-header);
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 9px;
  color: #8bffe1;
  background: rgba(2, 5, 11, 0.7);
  border: 1px solid rgba(139, 255, 225, 0.56);
  border-left: 0;
  border-radius: 0 6px 6px 0;
  box-shadow: 0 0 20px rgba(139, 255, 225, 0.08);
  transition: left 0.28s ease, background 0.18s ease;
  writing-mode: vertical-rl;
}

.drawer-trigger:hover {
  background: rgba(139, 255, 225, 0.1);
}

.drawer-trigger.open {
  left: 306px;
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
  top: 90px;
  bottom: 0;
  z-index: calc(var(--z-header) - 1);
  width: 306px;
  display: flex;
  flex-direction: column;
  background: rgba(2, 6, 13, 0.72);
  border-right: 1px solid rgba(139, 255, 225, 0.44);
  box-shadow: 12px 0 42px rgba(0, 0, 0, 0.35);
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
}

.drawer-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 11px 18px;
  border-left: 2px solid transparent;
  cursor: pointer;
  transition: background 0.15s ease, border-color 0.15s ease;
}

.drawer-item:hover {
  background: rgba(139, 255, 225, 0.07);
  border-left-color: #8bffe1;
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

@media (max-width: 900px) {
  .app-header {
    grid-template-columns: 1fr auto;
    gap: 10px;
  }

  .filter-nav {
    order: 3;
    grid-column: 1 / -1;
    justify-content: flex-start;
  }

  .page-nav {
    justify-self: end;
  }

  .user-area {
    order: 2;
  }

  .locale-area {
    order: 1;
    margin-left: 0;
  }
}

@media (max-width: 680px) {
  .app-header {
    top: 10px;
    left: 10px;
    right: 10px;
    grid-template-columns: 1fr;
  }

  .page-nav,
  .filter-nav {
    width: 100%;
    justify-content: flex-start;
    overflow-x: auto;
    padding-bottom: 2px;
  }

  .user-area {
    justify-self: start;
  }

  .locale-area {
    justify-self: end;
    margin-left: 0;
  }

  .cosmic-overlay {
    left: 22px;
    right: 22px;
    bottom: 56px;
    width: auto;
  }

  .cosmic-title {
    font-size: clamp(28px, 11vw, 42px);
  }

  .drawer-trigger.open {
    left: min(306px, calc(100vw - 44px));
  }

  .event-drawer {
    width: min(306px, calc(100vw - 44px));
  }
}
</style>
