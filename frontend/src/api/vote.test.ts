import { beforeEach, describe, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => ({
  post: vi.fn(),
  get: vi.fn(),
}))

vi.mock('./request', () => ({
  post: mocks.post,
  get: mocks.get,
  del: vi.fn(),
}))

vi.mock('@/utils/session', () => ({
  getSessionId: () => 'session-test',
}))

import { voteApi } from './vote'

describe('voteApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('sends star votes as backend favorite vote type 2', async () => {
    mocks.post.mockResolvedValueOnce({ code: 200, message: 'ok', data: null })

    await voteApi.createVote({
      event_id: 'qin_unification',
      event_name: 'Qin unification',
      vote_type: 'star',
    })

    expect(mocks.post).toHaveBeenCalledWith('/api/vote', {
      event_id: 'qin_unification',
      event_name: 'Qin unification',
      session_id: 'session-test',
      vote_type: 2,
    })
  })

  it('loads current session vote for the requested event', async () => {
    mocks.get.mockResolvedValueOnce({
      code: 200,
      message: 'ok',
      data: [{ id: 1, event_id: 'qin_unification', vote_type: 2 }],
    })

    const res = await voteApi.getUserVote('qin_unification')

    expect(mocks.get).toHaveBeenCalledWith('/api/vote/my', {
      session_id: 'session-test',
      event_id: 'qin_unification',
    })
    expect(res.data?.vote_type).toBe(2)
  })
})
