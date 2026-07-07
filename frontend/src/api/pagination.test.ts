import { describe, expect, it } from 'vitest'
import type { ApiResponse } from '@/types'
import { normalizePaginatedResponse } from './pagination'

interface DemoItem {
  id: number
  name: string
}

describe('normalizePaginatedResponse', () => {
  it('converts backend top-level pagination metadata into frontend items shape', () => {
    const response: ApiResponse<DemoItem[]> & { total: number; page: number; page_size: number } = {
      code: 200,
      message: 'success',
      data: [{ id: 1, name: 'Qin' }],
      total: 1,
      page: 2,
      page_size: 10,
    }

    const normalized = normalizePaginatedResponse(response)

    expect(normalized.data).toEqual({
      items: [{ id: 1, name: 'Qin' }],
      total: 1,
      page: 2,
      page_size: 10,
    })
  })

  it('keeps already-normalized responses stable', () => {
    const response: ApiResponse<{ items: DemoItem[]; total: number; page: number; page_size: number }> = {
      code: 200,
      message: 'success',
      data: {
        items: [{ id: 2, name: 'Han' }],
        total: 5,
        page: 1,
        page_size: 20,
      },
    }

    const normalized = normalizePaginatedResponse(response)

    expect(normalized.data.items).toEqual([{ id: 2, name: 'Han' }])
    expect(normalized.data.total).toBe(5)
  })
})
