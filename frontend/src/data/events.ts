import type { HistoryEvent } from '@/types'

export const allEvents: HistoryEvent[] = [
  {
    id: 'shangyang_reform',
    name: '商鞅变法',
    year: -356,
    region: 'china',
    importance: 8,
    description: '商鞅在秦孝公支持下进行的系统性变法，推行废井田、重农抑商、奖励军功、建立县制等制度，为秦国统一六国奠定坚实基础。',
    causes: ['战国时期诸侯争霸，秦国相对落后', '秦孝公求贤若渴', '井田制阻碍生产力发展'],
    consequences: ['秦国国力大增', '建立中央集权制度雏形', '为统一六国奠定基础'],
    related: {
      causes: [],
      consequences: [{ id: 'qin_unification', weight: 9 }]
    }
  },
  {
    id: 'qin_unification',
    name: '秦始皇统一六国',
    year: -221,
    region: 'china',
    importance: 10,
    description: '秦始皇赢政消灭六国，建立中国历史上第一个大一统王朝，创建皇帝制度，统一文字、度量衡。',
    causes: ['商鞅变法国力大增', '远交近攻战略成功', '六国实力衰退'],
    consequences: ['统一文字小篆', '统一度量衡', '修筑万里长城', '建立郡县制'],
    related: {
      causes: [{ id: 'shangyang_reform', weight: 9 }],
      consequences: [{ id: 'han_empire', weight: 8 }]
    }
  },
  {
    id: 'han_empire',
    name: '大汉帝国建立',
    year: -202,
    region: 'china',
    importance: 10,
    description: '刘邦击败项羽建立汉朝，实行休养生息政策，丝绸之路连接东西方。',
    causes: ['秦始皇暴政导致亡国', '楚汉争霸项羽失败'],
    consequences: ['开启文景之治', '汉武帝北击匈奴', '丝绸之路开通'],
    related: {
      causes: [{ id: 'qin_unification', weight: 9 }],
      consequences: [{ id: 'roman_empire', weight: 6 }]
    }
  },
  {
    id: 'alexander_east',
    name: '亚历山大东征',
    year: -334,
    region: 'foreign',
    importance: 9,
    description: '马其顿国王亚历山大三世率军东征，建立横跨欧亚非的大帝国，开启希腊化时代。',
    causes: ['马其顿崛起', '希腊城邦衰落'],
    consequences: ['希腊化时代开启', '东西方文化交流'],
    related: {
      causes: [],
      consequences: [{ id: 'roman_empire', weight: 7 }]
    }
  },
  {
    id: 'roman_empire',
    name: '罗马帝国建立',
    year: -27,
    region: 'foreign',
    importance: 10,
    description: '屋大维获奥古斯都称号，罗马从共和制走向帝制。',
    causes: ['共和制衰落', '内战频发'],
    consequences: ['罗马和平时代', '法律体系完善'],
    related: {
      causes: [{ id: 'alexander_east', weight: 7 }],
      consequences: []
    }
  },
  {
    id: 'french_revolution',
    name: '法国大革命',
    year: 1789,
    region: 'foreign',
    importance: 9,
    description: '1789年巴黎人民攻占巴士底狱，法国大革命爆发，推翻了封建专制统治，传播了民主共和理念。',
    causes: ['启蒙运动思想传播', '封建专制压迫', '财政危机严重'],
    consequences: ['推翻封建专制', '传播民主理念', '拿破仑崛起'],
    related: {
      causes: [],
      consequences: [{ id: 'industrial_revolution', weight: 6 }]
    }
  },
  {
    id: 'industrial_revolution',
    name: '工业革命',
    year: 1769,
    region: 'foreign',
    importance: 9,
    description: '瓦特改进蒸汽机，开启工业革命，机器取代人力，人类社会进入工业化时代。',
    causes: [],
    consequences: [],
    related: {
      causes: [{ id: 'roman_empire', weight: 5 }],
      consequences: []
    }
  }
]

export function getEventById(id: string): HistoryEvent | undefined {
  return allEvents.find(e => e.id === id)
}

export function getRelatedEvents(
  eventId: string,
  type: 'causes' | 'consequences'
): (HistoryEvent & { weight: number })[] {
  const event = getEventById(eventId)
  if (!event) return []

  const relations = event.related[type] || []
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
    if (e.causes.some(c => c.toLowerCase().includes(lower))) return true
    if (e.consequences.some(c => c.toLowerCase().includes(lower))) return true
    return false
  })
}
