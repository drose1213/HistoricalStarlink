import { reactive, ref } from 'vue'
import type { HistoryEvent } from '@/types'
import { eventsApi } from '@/api/events'

const EVENT_RELATIONS: Record<string, { causes: { id: string; weight: number }[]; consequences: { id: string; weight: number }[] }> = {
  shangyang_reform: { causes: [], consequences: [{ id: 'qin_unification', weight: 9 }] },
  qin_unification: { causes: [{ id: 'shangyang_reform', weight: 9 }], consequences: [{ id: 'han_empire', weight: 8 }] },
  han_empire: { causes: [{ id: 'qin_unification', weight: 9 }], consequences: [{ id: 'silk_road', weight: 8 }] },
  alexander_conquests: { causes: [], consequences: [{ id: 'roman_empire', weight: 7 }] },
  roman_empire: { causes: [{ id: 'alexander_conquests', weight: 7 }], consequences: [{ id: 'fall_of_rome', weight: 8 }] },
  fall_of_rome: { causes: [{ id: 'roman_empire', weight: 8 }], consequences: [{ id: 'crusades', weight: 6 }] },
  crusades: { causes: [{ id: 'fall_of_rome', weight: 6 }], consequences: [{ id: 'renaissance', weight: 7 }] },
  black_death: { causes: [], consequences: [{ id: 'renaissance', weight: 8 }] },
  renaissance: { causes: [{ id: 'crusades', weight: 7 }, { id: 'black_death', weight: 8 }], consequences: [{ id: 'scientific_revolution', weight: 8 }, { id: 'reformation', weight: 7 }] },
  scientific_revolution: { causes: [{ id: 'renaissance', weight: 8 }], consequences: [{ id: 'enlightenment', weight: 8 }, { id: 'industrial_revolution', weight: 9 }] },
  enlightenment: { causes: [{ id: 'scientific_revolution', weight: 8 }], consequences: [{ id: 'american_independence', weight: 8 }, { id: 'french_revolution', weight: 9 }] },
  reformation: { causes: [{ id: 'renaissance', weight: 7 }], consequences: [{ id: 'glorious_revolution', weight: 7 }] },
  glorious_revolution: { causes: [{ id: 'reformation', weight: 7 }], consequences: [{ id: 'industrial_revolution', weight: 7 }] },
  american_independence: { causes: [{ id: 'enlightenment', weight: 8 }], consequences: [{ id: 'french_revolution', weight: 7 }] },
  french_revolution: { causes: [{ id: 'enlightenment', weight: 9 }, { id: 'american_independence', weight: 7 }], consequences: [{ id: 'industrial_revolution', weight: 6 }] },
  industrial_revolution: { causes: [{ id: 'scientific_revolution', weight: 9 }, { id: 'glorious_revolution', weight: 7 }], consequences: [{ id: 'world_war_1', weight: 6 }] },
  silk_road: { causes: [{ id: 'han_empire', weight: 8 }], consequences: [{ id: 'silk_road_maritime', weight: 7 }] },
  silk_road_maritime: { causes: [{ id: 'silk_road', weight: 7 }], consequences: [{ id: 'zhenghe_voyages', weight: 7 }] },
  tang_dynasty_prosperity: { causes: [{ id: 'han_empire', weight: 5 }], consequences: [{ id: 'an_shi_rebellion', weight: 7 }] },
  an_shi_rebellion: { causes: [{ id: 'tang_dynasty_prosperity', weight: 7 }], consequences: [{ id: 'song_dynasty_commerce', weight: 6 }] },
  song_innovations: { causes: [], consequences: [{ id: 'mongol_empire', weight: 5 }] },
  song_dynasty_commerce: { causes: [{ id: 'an_shi_rebellion', weight: 6 }], consequences: [] },
  mongol_empire: { causes: [{ id: 'song_innovations', weight: 5 }], consequences: [{ id: 'black_death', weight: 7 }] },
  zhenghe_voyages: { causes: [{ id: 'silk_road_maritime', weight: 7 }], consequences: [] },
  opium_war: { causes: [], consequences: [{ id: 'taiping_rebellion', weight: 7 }, { id: 'self_strengthening', weight: 7 }] },
  taiping_rebellion: { causes: [{ id: 'opium_war', weight: 7 }], consequences: [{ id: 'self_strengthening', weight: 6 }] },
  self_strengthening: { causes: [{ id: 'opium_war', weight: 7 }, { id: 'taiping_rebellion', weight: 6 }], consequences: [{ id: 'hundred_days_reform', weight: 6 }] },
  hundred_days_reform: { causes: [{ id: 'self_strengthening', weight: 6 }], consequences: [{ id: 'xinhai_revolution', weight: 7 }] },
  xinhai_revolution: { causes: [{ id: 'hundred_days_reform', weight: 7 }], consequences: [{ id: 'may_fourth_movement', weight: 8 }] },
  may_fourth_movement: { causes: [{ id: 'xinhai_revolution', weight: 8 }], consequences: [{ id: 'long_march', weight: 7 }] },
  long_march: { causes: [{ id: 'may_fourth_movement', weight: 7 }], consequences: [{ id: 'founding_prc', weight: 9 }] },
  founding_prc: { causes: [{ id: 'long_march', weight: 9 }], consequences: [{ id: 'chinese_reform_opening', weight: 9 }] },
  chinese_reform_opening: { causes: [{ id: 'founding_prc', weight: 9 }], consequences: [] },
  world_war_1: { causes: [{ id: 'industrial_revolution', weight: 6 }], consequences: [{ id: 'world_war_2', weight: 8 }] },
  world_war_2: { causes: [{ id: 'world_war_1', weight: 8 }], consequences: [{ id: 'cold_war', weight: 9 }] },
  cold_war: { causes: [{ id: 'world_war_2', weight: 9 }], consequences: [{ id: 'fall_of_berlin_wall', weight: 8 }, { id: 'internet_birth', weight: 7 }] },
  fall_of_berlin_wall: { causes: [{ id: 'cold_war', weight: 8 }], consequences: [] },
  internet_birth: { causes: [{ id: 'cold_war', weight: 7 }], consequences: [] },
  moon_landing: { causes: [{ id: 'cold_war', weight: 6 }], consequences: [] },
  abolition_of_slavery: { causes: [{ id: 'enlightenment', weight: 6 }], consequences: [] },
  meiji_restoration: { causes: [], consequences: [{ id: 'world_war_1', weight: 5 }] },
  american_civil_war: { causes: [{ id: 'american_independence', weight: 5 }], consequences: [] },
  great_wall_construction: { causes: [], consequences: [] },
  invention_of_paper: { causes: [], consequences: [] },
  invention_of_gunpowder: { causes: [], consequences: [] },
  invention_of_compass: { causes: [], consequences: [] },
  invention_of_printing: { causes: [], consequences: [] },
  bauhaus_founded: { causes: [], consequences: [] },
  french_colonial_indochina: { causes: [], consequences: [] },
  abolition_feudalism_japan: { causes: [], consequences: [{ id: 'meiji_restoration', weight: 8 }] },
}

export const allEvents: HistoryEvent[] = reactive([])

export const backendAvailable = ref(false)
export const loadError = ref<string>('')

let _loaded = false

export async function loadEvents(): Promise<void> {
  if (_loaded) return
  try {
    const res = await eventsApi.getAll()
    const list = res.data?.list || []
    allEvents.length = 0
    for (const ev of list) {
      const rel = EVENT_RELATIONS[ev.id] || { causes: [], consequences: [] }
      allEvents.push({
        ...ev,
        related: rel,
      })
    }
    backendAvailable.value = true
    loadError.value = ''
    _loaded = true
  } catch (e: any) {
    backendAvailable.value = false
    if (e?.code === 'ERR_NETWORK' || e?.message?.includes('Network Error')) {
      loadError.value = '后端服务未启动（localhost:8000）'
    } else if (e?.code === 'ECONNABORTED') {
      loadError.value = '后端响应超时'
    } else {
      loadError.value = e?.message || '加载历史事件失败'
    }
    console.warn('[HistoricalStarlink] 后端事件加载失败：', loadError.value, '— 页面将以降级模式运行')
    _loaded = true
  }
}

export function getEventById(id: string): HistoryEvent | undefined {
  return allEvents.find(e => e.id === id)
}

export function getRelatedEvents(
  eventId: string,
  type: 'causes' | 'consequences'
): (HistoryEvent & { weight: number })[] {
  const event = getEventById(eventId)
  if (!event) return []

  const relations = event.related?.[type] || []
  return relations
    .map(rel => {
      const found = getEventById(rel.id)
      if (!found) return null
      return { ...found, weight: rel.weight }
    })
    .filter((e): e is HistoryEvent & { weight: number } => e !== null)
}

export function searchEvents(keyword: string): HistoryEvent[] {
  const lower = keyword.toLowerCase()
  return allEvents.filter(e => {
    if (e.name.toLowerCase().includes(lower)) return true
    if (e.description.toLowerCase().includes(lower)) return true
    if (e.causes?.some(c => c.toLowerCase().includes(lower))) return true
    if (e.consequences?.some(c => c.toLowerCase().includes(lower))) return true
    if (e.related_concepts?.some(c => c.toLowerCase().includes(lower))) return true
    if (e.figures?.some(f => f.toLowerCase().includes(lower))) return true
    if (e.tags?.some(t => t.toLowerCase().includes(lower))) return true
    return false
  })
}
