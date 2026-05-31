export interface HistoryEvent {
  id: string
  name: string
  year: number
  region: 'china' | 'foreign'
  importance: number
  description: string
  causes: string[]
  consequences: string[]
  related: {
    causes: { id: string; weight: number }[]
    consequences: { id: string; weight: number }[]
  }
}

export interface ExplorationRecord {
  id: number
  user_id: number
  event_id: string
  explored_at: string
  duration_seconds: number
  path_depth: number
  notes: string
}

export interface RatingEntry {
  id: number
  user_id: number
  event_id: string
  score: number
  comment: string
  created_at: string
}

export interface VoteEntry {
  id: number
  user_id: number
  event_id: string
  vote_type: 'up' | 'down' | 'star'
  created_at: string
}

export interface VoteStats {
  event_id: string
  up_count: number
  down_count: number
  star_count: number
  user_vote: 'up' | 'down' | 'star' | null
}

export interface SignatureRecord {
  id: number
  user_id: number
  image_url: string
  title: string
  description: string
  created_at: string
}

export interface ChampionCard {
  id: number
  event_id: string
  title: string
  subtitle: string
  description: string
  image_url: string
  rarity: 'common' | 'rare' | 'epic' | 'legendary'
  attributes: Record<string, string | number>
  unlocked_at: string
}

export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface ExploreStartRequest {
  event_id: string
  session_id?: string
  event_name?: string
}

export interface ExploreEndRequest {
  record_id: number
  duration_seconds: number
  path_depth: number
  notes?: string
}

export interface RatingCreateRequest {
  event_id: string
  event_name?: string
  session_id?: string
  score: number
  comment?: string
}

export interface VoteCreateRequest {
  event_id: string
  event_name?: string
  session_id?: string
  vote_type: 'up' | 'down' | 'star'
}

export interface SignatureUploadRequest {
  image: File
  title?: string
  description?: string
}

export interface DialogueMessage {
  id: string
  role: 'narrative' | 'choice' | 'user' | 'system'
  content: string
  choices?: DialogueChoice[]
  mood?: string
  timestamp: number
  isTimelineChange?: boolean
}

export interface DialogueChoice {
  choice_id: string
  text: string
  consequence?: string
}

export interface DialogueSession {
  id: number
  session_id: string
  event_id: string
  event_name: string
  dialogue_history: any
  choices_made: any[]
  timeline_branches: any[]
  path_depth: number
  is_completed: boolean
  outcome_summary?: string
  created_at: string
}
