export interface ExplorationRecordDisplaySource {
  event_id?: string
  event_name?: string | null
  depth?: number | null
  path_depth?: number | null
  stay_duration?: number | null
  duration_seconds?: number | null
  created_at?: string | null
  explored_at?: string | null
  notes?: string | null
}

export function getExplorationTitle(record: ExplorationRecordDisplaySource): string {
  return record.event_name?.trim() || record.event_id || ''
}

export function getExplorationDepth(record: ExplorationRecordDisplaySource): number {
  return Number(record.depth ?? record.path_depth ?? 0)
}

export function getExplorationDuration(record: ExplorationRecordDisplaySource): number {
  return Number(record.stay_duration ?? record.duration_seconds ?? 0)
}

export function getExplorationTimestamp(record: ExplorationRecordDisplaySource): string {
  return record.created_at || record.explored_at || ''
}

export function getExplorationNotes(record: ExplorationRecordDisplaySource): string {
  return record.notes?.trim() || ''
}
