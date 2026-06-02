<template>
  <div class="home-view">
    <header class="app-header">
      <div class="logo">
        <span class="logo-icon" aria-hidden="true"></span>
        <h1>历史星链</h1>
      </div>

      <nav class="page-nav" aria-label="页面导航">
        <router-link to="/" class="nav-link nav-link--active">首页</router-link>
        <router-link to="/champions" class="nav-link">卡牌</router-link>
        <router-link to="/leaderboard" class="nav-link">排行</router-link>
        <router-link to="/knowledge-base" class="nav-link">知识库</router-link>
        <router-link v-if="authStore.isLoggedIn" to="/profile" class="nav-link">个人中心</router-link>
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
                退出登录
              </button>
            </div>
          </Transition>
        </template>
        <template v-else>
          <router-link to="/login" class="login-btn">登录 / 注册</router-link>
        </template>
      </div>
    </header>

    <Transition name="banner-slide">
      <div v-if="!backendAvailable && loadError" class="backend-banner">
        <span class="banner-icon">⚠</span>
        <div class="banner-text">
          <strong>后端服务未连接</strong>
          <span>{{ loadError }}，请启动后端 (端口 8000) 后刷新页面</span>
        </div>
        <button class="banner-retry" @click="retryLoad">重新连接</button>
      </div>
    </Transition>

    <main class="home-main">
      <div class="cosmic-section">
        <CosmicMap @select-event="goToEvent" />

        <div class="cosmic-overlay">
          <div class="hero-copy">
            <h2 class="cosmic-title">探索时空之旅</h2>
          </div>

          <div class="search-bar">
            <div class="search-input-wrap">
              <input
                v-model="searchQuery"
                type="text"
                class="search-input"
                placeholder="搜索历史事件"
                @input="onSearchInput"
                @focus="showSearchDropdown = true"
                @blur="handleSearchBlur"
                @keydown.enter="handleSearchEnter"
              />
              <button class="search-btn" aria-label="搜索" @mousedown.prevent="handleSearchEnter">
                <span class="search-icon" aria-hidden="true"></span>
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
                    <span class="search-item-name">{{ item.name }}</span>
                    <span class="search-item-meta">
                      {{ formatEventYear(item.year) }} · {{ item.region === 'china' ? '东方' : '西方' }}
                    </span>
                  </div>
                </template>
                <div v-else class="search-item search-empty">
                  <span class="search-item-name" style="opacity:0.4">未找到匹配事件</span>
                </div>
              </div>
            </Transition>
          </div>
        </div>
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
        <span class="trigger-label">事件</span>
      </button>

      <Transition name="drawer-slide">
        <div v-if="drawerOpen" class="event-drawer">
          <div class="drawer-header">
            <h3 class="drawer-title">
              <span class="title-icon" aria-hidden="true"></span>
              历史事件
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
                  {{ event.region === 'china' ? '东方' : '西方' }}
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
import CosmicMap from '@/components/CosmicMap.vue'
import { allEvents as historyEvents, searchEvents, backendAvailable, loadError, loadEvents } from '@/data/events'
import { ragApi } from '@/api/rag'

interface LocalSearchResult {
  id: string
  name: string
  year: number | null
  region: string
  importance: number
  description?: string
  score: number
}

const router = useRouter()
const appStore = useAppStore()
const authStore = useAuthStore()
const showUserMenu = ref(false)
const drawerOpen = ref(false)
const searchQuery = ref('')
const showSearchDropdown = ref(false)
const searchLoading = ref(false)
let searchLoadingTimer: ReturnType<typeof setTimeout> | null = null
let searchAbortTimer: ReturnType<typeof setTimeout> | null = null

const ragSearchResults = ref<LocalSearchResult[]>([])

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
      const res = await ragApi.search({ query: q, top_k: 5 })
      ragSearchResults.value = res.data || []
    } catch {
      ragSearchResults.value = []
    }
  }, 300)
}

const searchResults = computed(() => {
  if (!searchQuery.value.trim()) return []
  if (ragSearchResults.value.length > 0) return ragSearchResults.value
  return searchEvents(searchQuery.value.trim()).slice(0, 5)
})

const filters = [
  { value: 'all' as const, label: '全部' },
  { value: 'china' as const, label: '东方' },
  { value: 'foreign' as const, label: '西方' }
]

const filteredEvents = computed(() => {
  if (appStore.currentFilter === 'all') return historyEvents
  return historyEvents.filter(e => {
    if (appStore.currentFilter === 'china') return e.region === 'china'
    return e.region === 'foreign'
  })
})

function formatEventYear(year: number | null): string {
  if (year === null || year === undefined) return '-'
  if (year < 0) return `公元前${Math.abs(year)}年`
  return `${year}年`
}

function handleSearchSelect(id: string) {
  searchQuery.value = ''
  showSearchDropdown.value = false
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
  appStore.showToast('success', '已退出登录')
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
}

onMounted(() => {
  authStore.init()
  document.addEventListener('click', handleClickOutside)
  loadEvents()
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
  display: grid;
  grid-template-columns: auto 1fr auto auto;
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
  width: min(360px, 100%);
  display: flex;
  align-items: center;
  margin-top: 20px;
  pointer-events: auto;
}

.search-input-wrap {
  position: relative;
  width: 100%;
}

.search-input {
  width: 100%;
  height: 38px;
  padding: 0 48px 0 16px;
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
  right: 5px;
  width: 28px;
  height: 28px;
  border: 1px solid rgba(139, 255, 225, 0.7);
  border-radius: 50%;
  background: rgba(139, 255, 225, 0.18);
  transition: transform 0.18s ease, background 0.18s ease;
}

.search-btn:hover {
  transform: scale(1.06);
  background: rgba(139, 255, 225, 0.26);
}

.search-icon {
  display: block;
  width: 9px;
  height: 9px;
  margin: 7px auto 0;
  border-right: 2px solid #8bffe1;
  border-bottom: 2px solid #8bffe1;
  transform: rotate(-45deg);
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

.search-item:hover {
  background: rgba(139, 255, 225, 0.08);
  border-left-color: #8bffe1;
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
  top: 50%;
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
  transform: translateY(-50%);
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
  top: 0;
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
  padding: 88px 18px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.drawer-title {
  display: flex;
  align-items: center;
  gap: 9px;
  margin: 0 0 14px;
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
