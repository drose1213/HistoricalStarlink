import { get, post, put } from './request'
import type { ApiResponse } from '@/types'

export interface UserInfo {
  id: number
  username: string
  email: string
  nickname: string
  avatar_url: string
  is_admin: boolean
}

export interface AuthResponse {
  token: string
  user: UserInfo
}

export interface PasswordResetConfirmPayload {
  email: string
  email_code: string
  new_password: string
}

export const authApi = {
  async sendCode(email: string) {
    return post<null>('/api/auth/send-code', { email })
  },

  async sendPasswordResetCode(email: string): Promise<ApiResponse<null>> {
    return post<null>('/api/auth/password-reset/send-code', { email })
  },

  async resetPassword(data: PasswordResetConfirmPayload): Promise<ApiResponse<null>> {
    return post<null>('/api/auth/password-reset/confirm', data)
  },

  async register(data: { username: string; email: string; email_code: string; password: string; nickname?: string }) {
    return post<AuthResponse>('/api/auth/register', data)
  },

  async login(data: { username: string; password: string }) {
    return post<AuthResponse>('/api/auth/login', data)
  },

  async getMe() {
    return get<UserInfo>('/api/auth/me')
  },

  async updateProfile(data: { nickname?: string; avatar_url?: string }) {
    return put<UserInfo>('/api/auth/profile', data)
  }
}
