import apiClient from './request'

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

export const authApi = {
  async sendCode(email: string) {
    const res = await apiClient.post('/api/auth/send-code', { email })
    return res.data as any
  },

  async register(data: { username: string; email: string; email_code: string; password: string; nickname?: string }) {
    const res = await apiClient.post('/api/auth/register', data)
    return res.data as any
  },

  async login(data: { username: string; password: string }) {
    const res = await apiClient.post('/api/auth/login', data)
    return res.data as any
  },

  async getMe() {
    const res = await apiClient.get('/api/auth/me')
    return res.data as any
  },

  async updateProfile(data: { nickname?: string; avatar_url?: string }) {
    const res = await apiClient.put('/api/auth/profile', data)
    return res.data as any
  }
}
