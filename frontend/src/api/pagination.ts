import type { ApiResponse, PaginatedResponse } from '@/types'

export type BackendPaginatedResponse<T> = ApiResponse<T[]> & {
  total?: number
  page?: number
  page_size?: number
}

function isPaginatedData<T>(data: unknown): data is PaginatedResponse<T> {
  return (
    typeof data === 'object' &&
    data !== null &&
    Array.isArray((data as { items?: unknown }).items)
  )
}

export function normalizePaginatedResponse<T>(
  response: ApiResponse<PaginatedResponse<T>> | BackendPaginatedResponse<T>,
): ApiResponse<PaginatedResponse<T>> {
  if (isPaginatedData<T>(response.data)) {
    return response as ApiResponse<PaginatedResponse<T>>
  }

  const items = Array.isArray(response.data) ? response.data : []
  const backendResponse = response as BackendPaginatedResponse<T>
  return {
    code: response.code,
    message: response.message,
    data: {
      items,
      total: backendResponse.total ?? items.length,
      page: backendResponse.page ?? 1,
      page_size: backendResponse.page_size ?? items.length,
    },
  }
}
