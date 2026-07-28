import axios from 'axios'
import type { ApiResponse } from '@/types'

// BASE_URL 优先级: VITE_API_BASE_URL 环境变量 > dev 模式留空走 vite proxy > 生产环境默认 /api
// 注意: 不要在此硬编码任何具体服务器 IP / 域名, 否则切换部署环境时极易遗漏
const RAW_BASE_URL = import.meta.env.VITE_API_BASE_URL
const BASE_URL = RAW_BASE_URL !== undefined && RAW_BASE_URL !== ''
  ? RAW_BASE_URL
  : (import.meta.env.DEV ? '' : '/api')

const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 由 main.ts 在安装 pinia / router 之后注入, 用于 401 时优雅跳转而不是直接改 hash
let redirectOn401: ((currentPath: string) => void) | null = null

export function setupAuthRedirect(handler: (currentPath: string) => void) {
  redirectOn401 = handler
}

apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token')
      // 优先走 vue-router 跳转, 保留当前路径作为 redirect 查询参数;
      // 若尚未注册 handler (例如单测中), 退化到 hash 跳转以保证不阻塞功能.
      if (redirectOn401) {
        const current = window.location.hash.replace(/^#/, '') || '/'
        redirectOn401(current)
      } else {
        window.location.hash = '#/login'
      }
    }
    return Promise.reject(error)
  }
)

export async function get<T>(url: string, params?: Record<string, unknown>): Promise<ApiResponse<T>> {
  const response = await apiClient.get<ApiResponse<T>>(url, { params })
  return response.data
}

export async function post<T>(url: string, data?: unknown, config?: { params?: Record<string, unknown>; timeout?: number }): Promise<ApiResponse<T>> {
  // 仅在 config 实际有内容时才传给 axios, 避免传 undefined 导致 axios 多传一个空参数,
  // 进而导致基于 toHaveBeenCalledWith 的测试误判.
  const response = config
    ? await apiClient.post<ApiResponse<T>>(url, data, config)
    : await apiClient.post<ApiResponse<T>>(url, data)
  return response.data
}

export async function put<T>(url: string, data?: unknown): Promise<ApiResponse<T>> {
  const response = await apiClient.put<ApiResponse<T>>(url, data)
  return response.data
}

export async function del<T>(url: string): Promise<ApiResponse<T>> {
  const response = await apiClient.delete<ApiResponse<T>>(url)
  return response.data
}

export async function upload<T>(url: string, formData: FormData): Promise<ApiResponse<T>> {
  const response = await apiClient.post<ApiResponse<T>>(url, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
  return response.data
}

export default apiClient
