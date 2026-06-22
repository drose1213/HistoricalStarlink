import { describe, it, expect, vi, beforeEach } from 'vitest'

// Use vi.hoisted to lift the mock state above vi.mock so the
// factory closure can safely reference it.
const { fakeAxiosInstance, requestHandlers, responseSuccessHandlers, responseErrorHandlers } = vi.hoisted(() => {
  const requestHandlers: Array<(config: any) => any> = []
  const responseSuccessHandlers: Array<(response: any) => any> = []
  const responseErrorHandlers: Array<(error: any) => any> = []
  const fakeAxiosInstance = {
    interceptors: {
      request: {
        use: (onFulfilled: any) => {
          requestHandlers.push(onFulfilled)
        },
      },
      response: {
        use: (onFulfilled: any, onRejected: any) => {
          responseSuccessHandlers.push(onFulfilled)
          responseErrorHandlers.push(onRejected)
        },
      },
    },
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  }
  return {
    fakeAxiosInstance,
    requestHandlers,
    responseSuccessHandlers,
    responseErrorHandlers,
  }
})

vi.mock('axios', () => {
  return {
    default: {
      create: () => fakeAxiosInstance,
    },
  }
})

// Re-import the module under test for every test to get a fresh set
// of interceptor registrations. The axios mock instance keeps the
// same handlers arrays, so we reset them between tests.
async function freshModule() {
  requestHandlers.length = 0
  responseSuccessHandlers.length = 0
  responseErrorHandlers.length = 0
  vi.resetModules()
  return await import('./request')
}

beforeEach(() => {
  localStorage.clear()
  window.location.hash = ''
  fakeAxiosInstance.get.mockReset()
  fakeAxiosInstance.post.mockReset()
  fakeAxiosInstance.put.mockReset()
  fakeAxiosInstance.delete.mockReset()
})

describe('api/request: request interceptor', () => {
  it('attaches Bearer Authorization header when auth_token is in localStorage', async () => {
    localStorage.setItem('auth_token', 'abc-123')
    await freshModule()
    expect(requestHandlers.length).toBeGreaterThan(0)
    const config = { headers: {} as Record<string, string> }
    const result = requestHandlers[0](config)
    expect(result.headers.Authorization).toBe('Bearer abc-123')
  })

  it('leaves Authorization header untouched when no token is stored', async () => {
    localStorage.removeItem('auth_token')
    await freshModule()
    const config = { headers: {} as Record<string, string> }
    const result = requestHandlers[0](config)
    expect(result.headers.Authorization).toBeUndefined()
  })

  it('returns the config object synchronously from the request interceptor', async () => {
    await freshModule()
    const config = { headers: {} as Record<string, string> }
    const result = requestHandlers[0](config)
    expect(result).toBe(config)
  })
})

describe('api/request: response interceptor on 401', () => {
  it('removes the auth_token from localStorage and sets hash to #/login', async () => {
    localStorage.setItem('auth_token', 'stale-token')
    await freshModule()
    expect(responseErrorHandlers.length).toBeGreaterThan(0)

    const err: any = new Error('Unauthorized')
    err.response = { status: 401, data: { detail: 'token expired' } }
    const promise = responseErrorHandlers[0](err)
    await expect(promise).rejects.toBe(err)
    expect(localStorage.getItem('auth_token')).toBeNull()
    expect(window.location.hash).toBe('#/login')
  })

  it('does not modify localStorage or hash on non-401 errors', async () => {
    localStorage.setItem('auth_token', 'good-token')
    await freshModule()
    const err: any = new Error('Server Error')
    err.response = { status: 500, data: { detail: 'boom' } }
    const promise = responseErrorHandlers[0](err)
    await expect(promise).rejects.toBe(err)
    expect(localStorage.getItem('auth_token')).toBe('good-token')
  })

  it('rejects with the original error (does not swallow it)', async () => {
    await freshModule()
    const err: any = new Error('Network Error')
    err.code = 'ERR_NETWORK'
    const promise = responseErrorHandlers[0](err)
    await expect(promise).rejects.toBe(err)
  })
})

describe('api/request: helper wrappers return response.data', () => {
  let mod: typeof import('./request')
  let get: typeof import('./request').get
  let post: typeof import('./request').post
  let put: typeof import('./request').put
  let del: typeof import('./request').del
  let upload: typeof import('./request').upload

  beforeEach(async () => {
    mod = await freshModule()
    get = mod.get
    post = mod.post
    put = mod.put
    del = mod.del
    upload = mod.upload
  })

  it('get() returns response.data', async () => {
    const data = { code: 200, message: 'ok', data: { foo: 1 } }
    fakeAxiosInstance.get.mockResolvedValueOnce({ data })
    const res = await get('/foo')
    expect(res).toEqual(data)
    expect(fakeAxiosInstance.get).toHaveBeenCalledWith('/foo', { params: undefined })
  })

  it('get() forwards query params', async () => {
    fakeAxiosInstance.get.mockResolvedValueOnce({ data: {} })
    await get('/foo', { a: 1, b: 'x' })
    expect(fakeAxiosInstance.get).toHaveBeenCalledWith('/foo', { params: { a: 1, b: 'x' } })
  })

  it('post() returns response.data', async () => {
    const data = { code: 200, message: 'ok', data: { id: 7 } }
    fakeAxiosInstance.post.mockResolvedValueOnce({ data })
    const res = await post('/foo', { x: 1 })
    expect(res).toEqual(data)
    expect(fakeAxiosInstance.post).toHaveBeenCalledWith('/foo', { x: 1 })
  })

  it('put() returns response.data', async () => {
    const data = { code: 200, message: 'ok', data: { updated: true } }
    fakeAxiosInstance.put.mockResolvedValueOnce({ data })
    const res = await put('/foo', { y: 2 })
    expect(res).toEqual(data)
    expect(fakeAxiosInstance.put).toHaveBeenCalledWith('/foo', { y: 2 })
  })

  it('del() returns response.data', async () => {
    const data = { code: 200, message: 'ok', data: null }
    fakeAxiosInstance.delete.mockResolvedValueOnce({ data })
    const res = await del('/foo')
    expect(res).toEqual(data)
    expect(fakeAxiosInstance.delete).toHaveBeenCalledWith('/foo')
  })

  it('upload() sends multipart/form-data and returns response.data', async () => {
    const data = { code: 200, message: 'ok', data: { url: 'https://x/y.png' } }
    fakeAxiosInstance.post.mockResolvedValueOnce({ data })
    const fd = new FormData()
    fd.append('file', new Blob(['x']), 'a.png')
    const res = await upload('/upload', fd)
    expect(res).toEqual(data)
    const [pathArg, bodyArg, configArg] = fakeAxiosInstance.post.mock.calls[0]
    expect(pathArg).toBe('/upload')
    expect(bodyArg).toBe(fd)
    expect(configArg).toMatchObject({
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  })
})

describe('api/request: default export is the axios instance', () => {
  it('exposes the api client as the default export', async () => {
    const mod = await freshModule()
    expect(mod.default).toBeDefined()
    expect((mod.default as any).interceptors).toBeDefined()
  })
})
