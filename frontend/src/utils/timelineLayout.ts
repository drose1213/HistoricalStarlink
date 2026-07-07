export interface TimelineScaleOptions {
  minYear: number
  maxYear: number
  height: number
  topPad: number
  bottomPad: number
}

export interface TimelineLaneItem {
  id: string
  targetY: number
  radius: number
}

export interface TimelineResolvedLaneItem extends TimelineLaneItem {
  y: number
}

export interface TimelineLaneOptions {
  minY: number
  maxY: number
  minGap: number
}

export interface StarfieldXOptions {
  id: string
  width: number
  railX: number
  region?: 'china' | 'foreign'
  importance: number
}

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value))
}

function finiteOrFallback(value: number, fallback: number): number {
  return Number.isFinite(value) ? value : fallback
}

function hashSeed(value: string): number {
  let hash = 2166136261
  for (let i = 0; i < value.length; i++) {
    hash ^= value.charCodeAt(i)
    hash = Math.imul(hash, 16777619)
  }
  return Math.abs(hash >>> 0)
}

export function mapYearToTimelineY(year: number | undefined, options: TimelineScaleOptions): number {
  const minYear = finiteOrFallback(options.minYear, 0)
  const maxYear = finiteOrFallback(options.maxYear, minYear + 1)
  const topPad = Math.max(0, finiteOrFallback(options.topPad, 0))
  const bottomPad = Math.max(0, finiteOrFallback(options.bottomPad, 0))
  const height = Math.max(topPad + bottomPad + 1, finiteOrFallback(options.height, topPad + bottomPad + 1))
  const drawableHeight = Math.max(1, height - topPad - bottomPad)

  const safeYear = typeof year === 'number' && Number.isFinite(year) ? year : undefined

  if (safeYear === undefined || maxYear <= minYear) {
    return topPad + drawableHeight / 2
  }

  const age = clamp(maxYear - safeYear, 0, maxYear - minYear)
  const ageMax = Math.max(1, maxYear - minYear)
  const linearRatio = age / ageMax
  const logRatio = Math.log1p(age) / Math.log1p(ageMax)
  const ratio = linearRatio * 0.72 + logRatio * 0.28

  return topPad + ratio * drawableHeight
}

export function resolveTimelineLaneY(
  items: TimelineLaneItem[],
  options: TimelineLaneOptions,
): TimelineResolvedLaneItem[] {
  if (items.length === 0) return []

  const minY = finiteOrFallback(options.minY, 0)
  const maxY = Math.max(minY, finiteOrFallback(options.maxY, minY))
  const minGap = Math.max(0, finiteOrFallback(options.minGap, 0))
  const sorted = [...items].sort((a, b) => a.targetY === b.targetY ? a.id.localeCompare(b.id) : a.targetY - b.targetY)
  const resolved = sorted.map(item => ({
    ...item,
    y: clamp(item.targetY, minY, maxY),
  }))

  for (let i = 1; i < resolved.length; i++) {
    const previous = resolved[i - 1]
    const current = resolved[i]
    const gap = Math.max(minGap, previous.radius + current.radius + 8)
    current.y = Math.max(current.y, previous.y + gap)
  }

  let overflow = resolved[resolved.length - 1].y - maxY
  if (overflow > 0) {
    resolved[resolved.length - 1].y = maxY
    for (let i = resolved.length - 2; i >= 0; i--) {
      const next = resolved[i + 1]
      const current = resolved[i]
      const gap = Math.max(minGap, current.radius + next.radius + 8)
      current.y = Math.min(current.y, next.y - gap)
    }
  }

  overflow = minY - resolved[0].y
  if (overflow > 0) {
    resolved[0].y = minY
    for (let i = 1; i < resolved.length; i++) {
      const previous = resolved[i - 1]
      const current = resolved[i]
      const gap = Math.max(minGap, previous.radius + current.radius + 8)
      current.y = Math.max(current.y, previous.y + gap)
    }
  }

  for (const item of resolved) {
    item.y = clamp(item.y, minY, maxY)
  }

  return resolved
}

export function resolveStarfieldX(options: StarfieldXOptions): number {
  const width = Math.max(1, finiteOrFallback(options.width, 1))
  const railX = clamp(finiteOrFallback(options.railX, width / 2), 0, width)
  const pad = Math.max(52, Math.min(96, width * 0.065))
  const availableHalf = Math.max(1, Math.min(railX - pad, width - pad - railX))
  const sideSeed = hashSeed(`${options.id}:side`)
  const offsetSeed = hashSeed(`${options.id}:offset`)
  const regionBias = options.region === 'china' ? -0.16 : options.region === 'foreign' ? 0.16 : 0
  const side = sideSeed % 2 === 0 ? -1 : 1
  const importance = clamp((options.importance - 1) / 9, 0, 1)
  const radial = 0.18 + ((offsetSeed % 1000) / 1000) * 0.62 + importance * 0.12
  const jitter = (((offsetSeed >>> 10) % 1000) / 1000 - 0.5) * availableHalf * 0.34
  const x = railX + side * availableHalf * radial + regionBias * availableHalf + jitter

  return clamp(x, pad, width - pad)
}
