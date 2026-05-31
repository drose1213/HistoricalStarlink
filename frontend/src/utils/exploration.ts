const STORAGE_KEY = 'starlink_exploration_counts'

function loadCounts(): Record<string, number> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
}

export function recordExploration(eventId: string) {
  const counts = loadCounts()
  counts[eventId] = (counts[eventId] || 0) + 1
  localStorage.setItem(STORAGE_KEY, JSON.stringify(counts))
}

export function getExplorationCount(eventId: string): number {
  return loadCounts()[eventId] || 0
}

export function getAllExplorationCounts(): Record<string, number> {
  return loadCounts()
}
