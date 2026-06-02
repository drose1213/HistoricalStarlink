import { get } from './request'

export interface Explorer {
  id: number
  sessionId: string
  name: string
  exploreCount: number
  totalDuration: number
  favoriteEvent: string
}

export interface ChampionEvent {
  name: string
  exploreCount: number
}

export interface LeaderboardData {
  period: 'daily' | 'weekly' | 'monthly' | 'yearly'
  ranking: Explorer[]
  championEvents: ChampionEvent[]
}

export const leaderboardApi = {
  async get(period: 'daily' | 'weekly' | 'monthly' | 'yearly' = 'weekly', limit = 10) {
    const res = await get<LeaderboardData>('/api/leaderboard', { period, limit })
    return res
  }
}
