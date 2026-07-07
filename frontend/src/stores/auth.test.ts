import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

// Mock the @/api/auth module before importing the store
vi.mock('@/api/auth', () => ({
  authApi: {
    sendCode: vi.fn(),
    sendPasswordResetCode: vi.fn(),
    resetPassword: vi.fn(),
    register: vi.fn(),
    login: vi.fn(),
    getMe: vi.fn(),
    updateProfile: vi.fn(),
  },
}))

import { authApi, type UserInfo } from '@/api/auth'
import { useAuthStore } from './auth'

const mockedAuthApi = vi.mocked(authApi)

const fakeUser: UserInfo = {
  id: 1,
  username: 'alice',
  email: 'alice@example.com',
  nickname: 'Alice',
  avatar_url: 'https://example.com/a.png',
  is_admin: false,
}

describe('useAuthStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('login success: token and user are set; success flag returned', async () => {
    mockedAuthApi.login.mockResolvedValueOnce({
      code: 200,
      message: 'ok',
      data: { token: 'tok-abc', user: fakeUser },
    })

    const store = useAuthStore()
    const result = await store.login('alice', 'pw')

    expect(result).toEqual({ success: true })
    expect(store.token).toBe('tok-abc')
    expect(store.user).toEqual(fakeUser)
    expect(localStorage.getItem('auth_token')).toBe('tok-abc')
    expect(store.isLoggedIn).toBe(true)
  })

  it('login failure: token remains unchanged; failure flag returned', async () => {
    mockedAuthApi.login.mockResolvedValueOnce({
      code: 401,
      message: 'invalid credentials',
      data: null,
    })

    const store = useAuthStore()
    const before = store.token
    const result = await store.login('alice', 'wrong')

    expect(result.success).toBe(false)
    expect(store.token).toBe(before)
    expect(store.user).toBeNull()
  })

  it('logout: clears token, user, and persisted auth_token', async () => {
    mockedAuthApi.login.mockResolvedValueOnce({
      code: 200,
      message: 'ok',
      data: { token: 'tok-xyz', user: fakeUser },
    })

    const store = useAuthStore()
    await store.login('alice', 'pw')
    expect(store.token).toBe('tok-xyz')

    store.logout()
    expect(store.token).toBe('')
    expect(store.user).toBeNull()
    expect(localStorage.getItem('auth_token')).toBeNull()
    expect(store.isLoggedIn).toBe(false)
  })

  it('401 on getMe triggers clearAuth (token becomes empty, user null)', async () => {
    // Seed token as if a previous login occurred
    const store = useAuthStore()
    store.setToken('stale-token')
    expect(store.token).toBe('stale-token')

    // Simulate axios 401 error shape
    const err = Object.assign(new Error('Unauthorized'), {
      response: { status: 401, data: { detail: 'token expired' } },
    })
    mockedAuthApi.getMe.mockRejectedValueOnce(err)

    await store.fetchUser()

    expect(store.token).toBe('')
    expect(store.user).toBeNull()
    expect(localStorage.getItem('auth_token')).toBeNull()
  })

  it('fetchUser populates user on success and keeps token', async () => {
    const store = useAuthStore()
    store.setToken('good-token')

    mockedAuthApi.getMe.mockResolvedValueOnce({
      code: 200,
      message: 'ok',
      data: fakeUser,
    })

    await store.fetchUser()
    expect(store.user).toEqual(fakeUser)
    expect(store.token).toBe('good-token')
  })

  it('sendPasswordResetCode delegates to auth API', async () => {
    mockedAuthApi.sendPasswordResetCode.mockResolvedValueOnce({
      code: 200,
      message: 'sent',
      data: null,
    })

    const store = useAuthStore()
    const res = await store.sendPasswordResetCode('alice@example.com')

    expect(res.code).toBe(200)
    expect(mockedAuthApi.sendPasswordResetCode).toHaveBeenCalledWith('alice@example.com')
  })

  it('resetPassword returns success when API accepts the email code', async () => {
    mockedAuthApi.resetPassword.mockResolvedValueOnce({
      code: 200,
      message: 'reset',
      data: null,
    })

    const store = useAuthStore()
    const result = await store.resetPassword('alice@example.com', '123456', 'NewPass123')

    expect(result).toEqual({ success: true, message: 'reset' })
    expect(mockedAuthApi.resetPassword).toHaveBeenCalledWith({
      email: 'alice@example.com',
      email_code: '123456',
      new_password: 'NewPass123',
    })
  })
})
