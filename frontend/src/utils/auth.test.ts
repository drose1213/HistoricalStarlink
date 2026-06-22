import { describe, it, expect, beforeEach, vi } from 'vitest'

// Hoisted mock store instances — shared by useAuthStore / useAppStore
const { authState, appState, routerPush } = vi.hoisted(() => ({
  authState: {
    isLoggedIn: false,
  },
  appState: {
    toasts: [] as { id: number; type: string; message: string }[],
    showToast: vi.fn((type: 'success' | 'error' | 'warning', message: string) => {
      appState.toasts.push({ id: Date.now(), type, message })
    }),
  },
  routerPush: vi.fn(),
}))

vi.mock('@/stores/auth', () => ({
  useAuthStore: () => authState,
}))

vi.mock('@/stores/app', () => ({
  useAppStore: () => appState,
}))

vi.mock('@/router', () => ({
  default: {
    push: routerPush,
  },
}))

// Import AFTER mocks are set up
import { requireAuth } from './auth'

describe('auth.requireAuth utility', () => {
  beforeEach(() => {
    authState.isLoggedIn = false
    appState.toasts = []
    appState.showToast.mockClear()
    routerPush.mockClear()
  })

  it('returns true when user is already logged in; does not push route or toast', () => {
    authState.isLoggedIn = true
    const ok = requireAuth()
    expect(ok).toBe(true)
    expect(routerPush).not.toHaveBeenCalled()
    expect(appState.showToast).not.toHaveBeenCalled()
  })

  it('returns false when user is not logged in; pushes Login route and shows error toast', () => {
    authState.isLoggedIn = false
    const ok = requireAuth()
    expect(ok).toBe(false)
    expect(routerPush).toHaveBeenCalledTimes(1)
    expect(routerPush).toHaveBeenCalledWith({ name: 'Login' })
    expect(appState.showToast).toHaveBeenCalledTimes(1)
    expect(appState.showToast).toHaveBeenCalledWith('error', expect.any(String))
  })
})
