import { get, upload, del } from './request'
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
    return get('/api/signature', { page, page_size: pageSize })
  },

  getSignatureById(id: number): Promise<ApiResponse<SignatureRecord>> {
    return get(`/api/signature/${id}`)
  },

  getUserSignatures(): Promise<ApiResponse<SignatureRecord[]>> {
    return get('/api/signature') as any
  },

  deleteSignature(id: number): Promise<ApiResponse<null>> {
    return del(`/api/signature/${id}`)
  }
}
