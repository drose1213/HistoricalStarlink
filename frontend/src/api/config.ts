import { get, put } from './request'
import type { ApiResponse } from '@/types'

export interface ConfigItem {
  key: string
  value: string | null
  group: string
  label: string | null
  value_type: string
}

export const configApi = {
  async getAll(group?: string) {
    const params = group ? { group } : undefined
    const res = await get<ConfigItem[]>('/api/config', params)
    return res
  },

  async getGroups() {
    const res = await get<string[]>('/api/config/groups')
    return res
  },

  async getByKey(key: string) {
    const res = await get<ConfigItem>(`/api/config/${key}`)
    return res
  },

  async updateBatch(configs: ConfigItem[]) {
    const res = await put<{ updated: number }>('/api/config', { configs })
    return res
  },

  async updateOne(key: string, value: string | null, group = 'general', label = '', value_type = 'string') {
    const res = await put(`/api/config/${key}`, { key, value, group, label, value_type })
    return res
  }
}
