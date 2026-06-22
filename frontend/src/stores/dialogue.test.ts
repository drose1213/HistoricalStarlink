import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('@/api/dialogue', () => ({
  dialogueApi: {
    startDialogue: vi.fn(),
    sendChoice: vi.fn(),
    sendFreeText: vi.fn(),
    getDialogue: vi.fn(),
    getDialogues: vi.fn(),
    startDynamic: vi.fn(),
    sendDynamicChoice: vi.fn(),
    sendDynamicChat: vi.fn(),
    endDynamic: vi.fn(),
  },
  resolveHero: vi.fn(),
}))

import { dialogueApi } from '@/api/dialogue'
import { useDialogueStore } from './dialogue'

const mockedDialogueApi = vi.mocked(dialogueApi)

const successData = {
  dialogue_id: 'dlg-001',
  topic: '唐朝安史之乱',
  narrative: '欢迎来到唐朝的时空对话机',
  history: [],
}

describe('useDialogueStore.startDynamicFromTopic', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('success path: isLoading toggles, session data is written, errorMessage empty', async () => {
    mockedDialogueApi.startDynamic.mockResolvedValueOnce({
      code: 200,
      message: 'ok',
      data: successData,
    } as any)

    const store = useDialogueStore()
    expect(store.isLoading).toBe(false)
    expect(store.errorMessage).toBe('')

    const promise = store.startDynamicFromTopic('唐朝安史之乱')

    // Loading state is asserted via the ref (state machine: loading)
    expect(store.isLoading).toBe(true)

    await promise

    // State machine: success
    expect(store.isLoading).toBe(false)
    expect(store.errorMessage).toBe('')
    expect(store.currentSession).toEqual(successData)
    expect(store.dialogueId).toBe('dlg-001')
    expect(store.round).toBe(1)
    expect(store.isDynamic).toBe(true)
    expect(store.currentTopic).toBe('唐朝安史之乱')
  })

  it('failure path: errorMessage is set, isLoading returns to false', async () => {
    const err = Object.assign(new Error('Network Error'), {
      response: { status: 500, data: { detail: 'upstream timeout' } },
    })
    mockedDialogueApi.startDynamic.mockRejectedValueOnce(err)

    const store = useDialogueStore()
    const promise = store.startDynamicFromTopic('三国演义')

    expect(store.isLoading).toBe(true)

    // startDialogue re-throws; we assert the catch path runs without losing control
    await expect(promise).rejects.toBeTruthy()

    // State machine: error
    expect(store.isLoading).toBe(false)
    expect(store.errorMessage).toBe('upstream timeout')
    expect(store.currentSession).toBeNull()
  })

  it('failure path: does NOT throw uncaught to the caller (caller can await + catch)', async () => {
    const err = Object.assign(new Error('boom'), {
      response: { status: 500, data: { detail: 'server down' } },
    })
    mockedDialogueApi.startDynamic.mockRejectedValueOnce(err)

    const store = useDialogueStore()
    let caught: unknown = null
    try {
      await store.startDynamicFromTopic('某话题')
    } catch (e) {
      caught = e
    }

    // Caller received the error but the store still ended in a clean error state
    expect(caught).toBeTruthy()
    expect(store.isLoading).toBe(false)
    expect(store.errorMessage).toBe('server down')
  })

  it('empty topic: throws synchronously and sets errorMessage; no API call', async () => {
    const store = useDialogueStore()
    await expect(store.startDynamicFromTopic('   ')).rejects.toThrow('topic is required')
    expect(store.errorMessage).toBe('请输入话题')
    expect(mockedDialogueApi.startDynamic).not.toHaveBeenCalled()
  })

  it('404 path: notFound is set and errorMessage is the dynamic-specific message', async () => {
    const err = Object.assign(new Error('not found'), {
      response: { status: 404, data: {} },
    })
    mockedDialogueApi.startDynamic.mockRejectedValueOnce(err)

    const store = useDialogueStore()
    await expect(store.startDynamicFromTopic('未知话题')).rejects.toBeTruthy()

    expect(store.notFound).toBe(true)
    expect(store.errorMessage).toBe('该话题时空对话机暂时无法回应')
  })
})
