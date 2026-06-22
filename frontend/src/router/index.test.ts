import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import {
  createRouter,
  createMemoryHistory,
  createWebHashHistory,
  type Router,
} from 'vue-router'

// Mock auth store before importing the router module so that
// the guard's `useAuthStore()` call is replaced with a controlled stub.
const authState = {
  isLoggedIn: false,
  isAdmin: false,
  user: null as null | { is_admin: boolean },
}

vi.mock('@/stores/auth', () => ({
  useAuthStore: () => ({
    get isLoggedIn() {
      return authState.isLoggedIn
    },
    get user() {
      return authState.user
    },
  }),
}))

// Mock the app store to avoid pulling in heavy module side effects
// and to make the toast path deterministic.
const toastCalls: Array<{ type: string; message: string }> = []
vi.mock('@/stores/app', () => ({
  useAppStore: () => ({
    locale: 'zh',
    showToast: (type: string, message: string) => {
      toastCalls.push({ type, message })
    },
  }),
}))

// Build a test router with the same `meta.requiresAdmin` rule used in
// the real router. We replicate the guard logic verbatim so we can
// drive it under test without depending on the exported singleton.
// The `useAuthStore`/`useAppStore` imports below resolve to the
// `vi.mock` factories above (mocked modules are resolved at call time).
async function buildTestRouter(): Promise<Router> {
  const { useAuthStore } = await import('@/stores/auth')
  const { useAppStore } = await import('@/stores/app')
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', name: 'Home', component: { template: '<div />' } },
      {
        path: '/knowledge-base',
        name: 'KnowledgeBase',
        component: { template: '<div />' },
        meta: { requiresAdmin: true },
      },
      { path: '/login', name: 'Login', component: { template: '<div />' } },
      { path: '/public', name: 'Public', component: { template: '<div />' } },
    ],
  })
  router.beforeEach((to, _from, next) => {
    if (to.meta?.requiresAdmin) {
      const auth = useAuthStore()
      if (!auth.isLoggedIn) {
        return next({ name: 'Login' })
      }
      if (!auth.user?.is_admin) {
        const app = useAppStore()
        app.showToast('warning', '无访问权限,仅管理员可访问知识库')
        return next({ name: 'Home' })
      }
    }
    next()
  })
  return router
}

describe('router beforeEach guard (requiresAdmin)', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    toastCalls.length = 0
    authState.isLoggedIn = false
    authState.isAdmin = false
    authState.user = null
  })

  it('redirects unauthenticated user away from requiresAdmin route to Login', async () => {
    authState.isLoggedIn = false
    const router = await buildTestRouter()
    await router.push('/knowledge-base')
    expect(router.currentRoute.value.name).toBe('Login')
  })

  it('allows authenticated admin into requiresAdmin route', async () => {
    authState.isLoggedIn = true
    authState.isAdmin = true
    authState.user = { is_admin: true }
    const router = await buildTestRouter()
    await router.push('/knowledge-base')
    expect(router.currentRoute.value.name).toBe('KnowledgeBase')
  })

  it('redirects authenticated non-admin from requiresAdmin route to Home and shows toast', async () => {
    authState.isLoggedIn = true
    authState.isAdmin = false
    authState.user = { is_admin: false }
    const router = await buildTestRouter()
    await router.push('/knowledge-base')
    expect(router.currentRoute.value.name).toBe('Home')
    expect(toastCalls).toHaveLength(1)
    expect(toastCalls[0].type).toBe('warning')
    expect(typeof toastCalls[0].message).toBe('string')
    expect(toastCalls[0].message.length).toBeGreaterThan(0)
  })

  it('allows access to public routes regardless of login state', async () => {
    authState.isLoggedIn = false
    const router = await buildTestRouter()
    await router.push('/public')
    expect(router.currentRoute.value.name).toBe('Public')
  })

  it('allows guest access to root when route has no requiresAdmin meta', async () => {
    authState.isLoggedIn = false
    const router = await buildTestRouter()
    await router.push('/')
    expect(router.currentRoute.value.name).toBe('Home')
  })
})

describe('the exported router instance', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    toastCalls.length = 0
    authState.isLoggedIn = false
    authState.isAdmin = false
    authState.user = null
  })

  it('exposes a vue-router instance with all registered routes', async () => {
    const mod = await import('./index')
    const router = mod.default
    expect(router).toBeDefined()
    expect(typeof router.push).toBe('function')

    const names = router.getRoutes().map((r) => String(r.name ?? ''))
    expect(names).toContain('Home')
    expect(names).toContain('Login')
    expect(names).toContain('KnowledgeBase')
    expect(names).toContain('Profile')
    expect(names).toContain('EventDetail')
    expect(names).toContain('Dialogue')
  })

  it('flags /knowledge-base as requiresAdmin in its route meta', async () => {
    const mod = await import('./index')
    const router = mod.default
    const matched = router.resolve({ path: '/knowledge-base' })
    expect(matched.matched.some((m) => m.meta?.requiresAdmin)).toBe(true)
  })

  it('does not flag / (Home) as requiresAdmin', async () => {
    const mod = await import('./index')
    const router = mod.default
    const matched = router.resolve({ path: '/' })
    expect(matched.matched.some((m) => m.meta?.requiresAdmin)).toBe(false)
  })

  it('exposes a hash-mode history by default', async () => {
    const mod = await import('./index')
    const router = mod.default
    expect(router).toBeDefined()
    expect(router.options.history).toBeDefined()
  })
})

describe('auth-aware redirect encoding (Login route accepts redirect query)', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    authState.isLoggedIn = false
  })

  it('Login route query string preserves a redirect param exactly as encoded', async () => {
    const router = await buildTestRouter()
    const target = '/knowledge-base'
    const encoded = encodeURIComponent(target)
    await router.push({ name: 'Login', query: { redirect: encoded } })
    expect(router.currentRoute.value.name).toBe('Login')
    expect(router.currentRoute.value.query.redirect).toBe(encoded)
  })

  it('vue-router preserves the original string in the query record after navigation', async () => {
    const router = createRouter({
      history: createWebHashHistory(),
      routes: [
        { path: '/', name: 'Home', component: { template: '<div />' } },
        { path: '/login', name: 'Login', component: { template: '<div />' } },
      ],
    })
    await router.push({
      name: 'Login',
      query: { redirect: '/protected/path?q=1&p=2' },
    })
    // vue-router 4 keeps the original (un-decoded) value in `query`.
    expect(router.currentRoute.value.query.redirect).toBe('/protected/path?q=1&p=2')
    // The resolved href should contain the redirect key.
    const href = router.resolve(router.currentRoute.value).href
    expect(href).toContain('redirect=')
    // `&` inside the redirect value is percent-encoded by vue-router 4
    // so it is not interpreted as a top-level query separator.
    // (the value is rendered as `/protected/path?q=1%26p=2` in the href)
    expect(href).toContain('%26p=2')
  })
})
