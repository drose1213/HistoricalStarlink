import { get } from './request'
import { getSessionId } from '@/utils/session'
import type { ApiResponse } from '@/types'

export interface ExplorationStats {
  total_records: number
  unique_events: number
  total_stay_duration: number
}

export interface ChampionStats {
  session_id: string
  total_cards: number
  total_explores: number
  favorite_count: number
  level_distribution: Record<string, number>
}

export interface BackendExplorationRecord {
  id: number
  session_id: string
  event_id: string
  event_name: string
  event_year: number | null
  event_region: string | null
  parent_event_id: string | null
  depth: number
  explore_path: Record<string, unknown> | null
  stay_duration: number
  from_direction: string | null
  created_at: string | null
}

export interface BackendChampionCard {
  id: number
  session_id: string
  nickname: string | null
  event_id: string
  event_name: string
  event_year: number | null
  event_region: string | null
  event_description: string | null
  card_level: number
  explore_count: number
  total_stay_duration: number
  related_events: Record<string, unknown> | null
  achievements: string[] | null
  is_favorite: boolean
  created_at: string | null
  updated_at: string | null
}

const CARD_LEVEL_NAME: Record<number, string> = {
  1: 'common',
  2: 'rare',
  3: 'epic',
  4: 'legendary',
}

const RARITY_LABELS: Record<string, string> = {
  legendary: '传说',
  epic: '史诗',
  rare: '稀有',
  common: '普通',
}

export const profileApi = {
  async getExplorationStats() {
    const sid = getSessionId()
    const res = await get<ExplorationStats>('/api/exploration/stats', { session_id: sid })
    return res
  },

  async getExplorationRecords(page = 1, pageSize = 50) {
    const sid = getSessionId()
    const res = await get<BackendExplorationRecord[]>('/api/exploration/records', {
      session_id: sid,
      page,
      page_size: pageSize,
    })
    return res
  },

  async getChampionCards(page = 1, pageSize = 100) {
    const sid = getSessionId()
    const res = await get<BackendChampionCard[]>('/api/champion', {
      session_id: sid,
      page,
      page_size: pageSize,
    })
    return res
  },

  async getChampionStats() {
    const sid = getSessionId()
    const res = await get<ChampionStats>(`/api/champion/stats/${sid}`)
    return res
  },
}

export function cardLevelToRarity(level: number): 'common' | 'rare' | 'epic' | 'legendary' {
  const name = CARD_LEVEL_NAME[level] || 'common'
  return name as 'common' | 'rare' | 'epic' | 'legendary'
}

export function rarityLabel(r: string): string {
  return RARITY_LABELS[r] || r
}

export function formatDuration(seconds: number): string {
  const sec = Math.round(seconds || 0)
  const hours = Math.floor(sec / 3600)
  const minutes = Math.floor((sec % 3600) / 60)
  const s = sec % 60
  if (hours > 0) return `${hours}h ${minutes}m`
  if (minutes > 0) return `${minutes}m`
  return `${s}s`
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return ''
  return iso.slice(0, 10)
}
