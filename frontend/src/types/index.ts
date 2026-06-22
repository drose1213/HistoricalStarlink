export interface HistoryEvent {
  id: string
  name: string
  year: number
  region: 'china' | 'foreign'
  importance: number
  description: string
  causes: string[]
  consequences: string[]
  related_concepts?: string[]
  figures?: string[]
  tags?: string[]
  related?: {
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
  owner_session_id: string | null
  is_on_auction: boolean
  is_high_rated: boolean
  created_at: string | null
  updated_at: string | null
}

export interface UserCardCollection {
  id: number
  user_session_id: string
  card_id: number
  event_id: string
  event_name: string
  is_high_rated: boolean
  source: 'explore' | 'auction' | 'system'
  collected_at: string | null
}

export interface CardAuction {
  id: number
  card_id: number
  event_id: string
  event_name: string
  seller_session_id: string
  start_price: number
  current_price: number
  min_increment: number
  end_time: string
  status: 'active' | 'sold' | 'expired' | 'cancelled'
  sold_price: number | null
  platform_fee: number | null
  seller_revenue: number | null
  winner_session_id: string | null
  description: string | null
  bid_count: number
  created_at: string | null
  updated_at: string | null
}

export interface CardBid {
  id: number
  auction_id: number
  bidder_session_id: string
  amount: number
  is_winning: boolean
  created_at: string | null
}

export interface CardReview {
  id: number
  auction_id: number
  reviewer_session_id: string
  stars: number
  comment: string | null
  created_at: string | null
  updated_at: string | null
}

export interface AuctionDetail {
  auction: CardAuction
  bids: CardBid[]
  reviews: CardReview[]
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

// ==================== 评价系统（spec rating-system-enhancement）====================

export interface ReviewItem {
  id: number
  card_id: number | null
  auction_id: number | null
  reviewer_session_id: string  // 已被后端脱敏
  stars: number
  comment: string | null
  parent_review_id: number | null
  likes_count: number
  liked_by_me: boolean
  reply_count: number
  created_at: string | null
  updated_at: string | null
  replies?: ReviewItem[]  // 顶级评价嵌入的回复列表
}

export interface RatingDistributionItem {
  stars: number  // 0-5
  count: number
}

export interface RatingTrendPoint {
  date: string  // YYYY-MM-DD
  avg_score: number
  count: number
}

export interface RatingDistribution {
  event_id: string
  items: RatingDistributionItem[]
}

export interface RatingTrend {
  event_id: string
  days: number
  points: RatingTrendPoint[]
}
