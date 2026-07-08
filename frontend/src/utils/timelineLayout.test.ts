import { describe, expect, it } from 'vitest'
import { mapYearToTimelineY, resolveStarfieldX, resolveTimelineLaneY } from './timelineLayout'

describe('timeline layout helpers', () => {
  it('maps the newest year to the top and expands dense recent years with log scale', () => {
    const options = {
      minYear: -3000,
      maxYear: 1989,
      height: 720,
      topPad: 96,
      bottomPad: 96,
    }

    const newest = mapYearToTimelineY(1989, options)
    const nearNewest = mapYearToTimelineY(1979, options)
    const oldest = mapYearToTimelineY(-3000, options)
    const linearGapForTenYears = (10 / (options.maxYear - options.minYear)) * (options.height - options.topPad - options.bottomPad)

    expect(newest).toBe(options.topPad)
    expect(oldest).toBe(options.height - options.bottomPad)
    expect(nearNewest - newest).toBeGreaterThan(linearGapForTenYears * 20)
  })

  it('keeps ancient years visually separated instead of collapsing them at the bottom', () => {
    const options = {
      minYear: -3000,
      maxYear: 2000,
      height: 800,
      topPad: 100,
      bottomPad: 100,
    }

    const oldest = mapYearToTimelineY(-3000, options)
    const ancient = mapYearToTimelineY(-2000, options)

    expect(oldest - ancient).toBeGreaterThan(60)
  })

  it('keeps crowded lane items separated without leaving the available rail bounds', () => {
    const items = [
      { id: 'a', targetY: 100, radius: 10 },
      { id: 'b', targetY: 104, radius: 12 },
      { id: 'c', targetY: 107, radius: 9 },
    ]

    const resolved = resolveTimelineLaneY(items, {
      minY: 80,
      maxY: 180,
      minGap: 18,
    })

    expect(resolved.map(item => item.id)).toEqual(['a', 'b', 'c'])
    expect(resolved[0].y).toBeGreaterThanOrEqual(80)
    expect(resolved[2].y).toBeLessThanOrEqual(180)
    expect(resolved[1].y - resolved[0].y).toBeGreaterThanOrEqual(18)
    expect(resolved[2].y - resolved[1].y).toBeGreaterThanOrEqual(18)
  })

  it('spreads starfield nodes around the rail while staying inside the viewport', () => {
    const positions = [
      resolveStarfieldX({ id: 'a', width: 1000, railX: 500, region: 'china', importance: 9 }),
      resolveStarfieldX({ id: 'b', width: 1000, railX: 500, region: 'foreign', importance: 8 }),
      resolveStarfieldX({ id: 'c', width: 1000, railX: 500, region: 'china', importance: 5 }),
      resolveStarfieldX({ id: 'd', width: 1000, railX: 500, region: 'foreign', importance: 4 }),
    ]

    expect(Math.min(...positions)).toBeGreaterThanOrEqual(52)
    expect(Math.max(...positions)).toBeLessThanOrEqual(948)
    expect(positions.some(x => x < 500)).toBe(true)
    expect(positions.some(x => x > 500)).toBe(true)
    expect(new Set(positions.map(x => Math.round(x))).size).toBeGreaterThan(2)
  })
})
