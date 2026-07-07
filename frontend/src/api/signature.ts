import { get, upload, del } from './request'
import { normalizePaginatedResponse } from './pagination'
import type {
  ApiResponse,
  SignatureRecord,
  PaginatedResponse
} from '@/types'

export const signatureApi = {
  uploadSignature(formData: FormData): Promise<ApiResponse<SignatureRecord>> {
    return upload('/api/signature/upload', formData)
  },

  getSignatureRecords(page = 1, pageSize = 20): Promise<ApiResponse<PaginatedResponse<SignatureRecord>>> {
    return get<SignatureRecord[]>('/api/signature', { page, page_size: pageSize })
      .then(normalizePaginatedResponse)
  },

  getSignatureById(id: number): Promise<ApiResponse<SignatureRecord>> {
    return get(`/api/signature/${id}`)
  },

  getUserSignatures(): Promise<ApiResponse<SignatureRecord[]>> {
    return get<SignatureRecord[]>('/api/signature').then(res => ({
      code: res.code,
      message: res.message,
      data: Array.isArray(res.data) ? res.data : [],
    }))
  },

  deleteSignature(id: number): Promise<ApiResponse<null>> {
    return del(`/api/signature/${id}`)
  }
}
