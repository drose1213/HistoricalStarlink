<template>
  <div class="cosmic-map" ref="containerRef">
    <canvas ref="bgCanvasRef" class="layer-bg" />
    <canvas
      ref="graphCanvasRef"
      class="layer-graph"
      @mousemove="onMouseMove"
      @click="onClick"
      @mouseleave="onMouseLeave"
    />

    <Transition name="tooltip">
      <div v-if="hoveredNode" class="hover-tip" :style="{ left: tipX + 'px', top: tipY + 'px' }">
        <div class="tip-name">{{ hoveredNode.label }}</div>
        <div v-if="hoveredNode.year" class="tip-year">{{ formatYear(hoveredNode.year) }}</div>
        <div v-if="hoveredNode.type === 'concept'" class="tip-concept">关联 {{ conceptConnectedCount(hoveredNode.id) }} 个事件</div>
        <div v-if="hoveredNode.type === 'event'" class="tip-hint">点击查看详情</div>
        <div v-if="hoveredNode.type === 'concept'" class="tip-hint">点击高亮关联事件</div>
      </div>
    </Transition>

    <div class="map-nebula nebula-1" />
    <div class="map-nebula nebula-2" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { allEvents } from '@/data/events'
import { getAllExplorationCounts } from '@/utils/exploration'

const props = defineProps<{ searchKeyword?: string }>()
const emit = defineEmits<{ selectEvent: [id: string] }>()
const containerRef = ref<HTMLDivElement>()
const bgCanvasRef = ref<HTMLCanvasElement>()
const graphCanvasRef = ref<HTMLCanvasElement>()

interface GNode {
  id: string
  label: string
  type: 'event' | 'concept'
  year?: number
  region?: string
  importance: number
  x: number
  y: number
  radius: number
  color: string
  glowColor: string
}

interface GEdge {
  source: string
  target: string
  strength: number
}

interface BackgroundStar {
  x: number
  y: number
  r: number
  o: number
  s: number
  p: number
  c: string
}

const nodes: GNode[] = []
const edges: GEdge[] = []
const edgeParticles: { t: number; edgeIdx: number; speed: number }[] = []
const nodeMap = new Map<string, GNode>()
const conceptIdByLabel = new Map<string, string>()
const BG_STARS: BackgroundStar[] = []

let W = 0
let H = 0
let animId: number | null = null
let mouse = { x: -999, y: -999 }
const hoveredNode = ref<GNode | null>(null)
const tipX = ref(0)
const tipY = ref(0)
const highlightConceptId = ref<string | null>(null)

function runLayout() {
  const cx = W / 2
  const cy = H / 2
  const baseR = Math.min(W, H) * 0.22

  const chinaEvts = nodes.filter(n => n.type === 'event' && n.region === 'china')
  const foreignEvts = nodes.filter(n => n.type === 'event' && n.region === 'foreign')
  const concepts = nodes.filter(n => n.type === 'concept')

  const perRing = 10

  chinaEvts.forEach((n, i) => {
    const ring = Math.floor(i / perRing)
    const pos = i % perRing
    const count = Math.min(perRing, chinaEvts.length - ring * perRing)
    const arcSpan = Math.PI * 0.85
    const arcCenter = -Math.PI * 0.5
    const angle = arcCenter + ((pos / Math.max(count - 1, 1)) - 0.5) * arcSpan + ring * 0.25
    const r = baseR + ring * (baseR * 0.5)
    n.x = cx + Math.cos(angle) * r
    n.y = cy + Math.sin(angle) * r
  })

  foreignEvts.forEach((n, i) => {
    const ring = Math.floor(i / perRing)
    const pos = i % perRing
    const count = Math.min(perRing, foreignEvts.length - ring * perRing)
    const arcSpan = Math.PI * 0.85
    const arcCenter = Math.PI * 0.5
    const angle = arcCenter + ((pos / Math.max(count - 1, 1)) - 0.5) * arcSpan - ring * 0.25
    const r = baseR + ring * (baseR * 0.5)
    n.x = cx + Math.cos(angle) * r
    n.y = cy + Math.sin(angle) * r
  })

  const outerR = baseR + Math.max(
    Math.ceil(chinaEvts.length / perRing),
    Math.ceil(foreignEvts.length / perRing)
  ) * baseR * 0.5 + 100

  concepts.forEach((n, i) => {
    const angle = (i / concepts.length) * Math.PI * 2 + Math.PI / concepts.length
    n.x = cx + Math.cos(angle) * outerR
    n.y = cy + Math.sin(angle) * outerR
  })

  for (const n of nodes) {
    n.x = Math.max(n.radius + 30, Math.min(W - n.radius - 30, n.x))
    n.y = Math.max(n.radius + 30, Math.min(H - n.radius - 30, n.y))
  }
}

function addEdge(source: string, target: string, strength: number) {
  if (nodeMap.has(source) && nodeMap.has(target)) {
    edges.push({ source, target, strength })
  }
}

function conceptId(label: string): string | undefined {
  return conceptIdByLabel.get(label)
}

function initGraph() {
  nodes.length = 0
  edges.length = 0
  edgeParticles.length = 0
  nodeMap.clear()
  conceptIdByLabel.clear()

  const cx = W / 2
  const cy = H / 2
  const exploreCounts = getAllExplorationCounts()
  const maxExplore = Math.max(1, ...Object.values(exploreCounts))

  allEvents.forEach((ev) => {
    const isChina = ev.region === 'china'
    const exploreBonus = (exploreCounts[ev.id] || 0) / maxExplore * 5
    const node: GNode = {
      id: ev.id,
      label: ev.name,
      type: 'event',
      year: ev.year,
      region: ev.region,
      importance: ev.importance,
      x: cx,
      y: cy,
      radius: 7 + (ev.importance / 10) * 10 + exploreBonus,
      color: isChina ? '#8bffe1' : '#ff68b8',
      glowColor: isChina ? 'rgba(139,255,225,' : 'rgba(255,104,184,'
    }
    nodes.push(node)
    nodeMap.set(node.id, node)
  })

  const concepts: Array<{ label: string; color: string; glow: string; r: number }> = [
    { label: '政治', color: '#8bffe1', glow: 'rgba(139,255,225,', r: 8 },
    { label: '军事', color: '#ff68b8', glow: 'rgba(255,104,184,', r: 8 },
    { label: '文化', color: '#f2d36b', glow: 'rgba(242,211,107,', r: 7 },
    { label: '经济', color: '#8bffe1', glow: 'rgba(139,255,225,', r: 7 },
    { label: '科技', color: '#7db5ff', glow: 'rgba(125,181,255,', r: 7 },
    { label: '法律', color: '#f2d36b', glow: 'rgba(242,211,107,', r: 6 },
    { label: '帝国', color: '#ff7a7a', glow: 'rgba(255,122,122,', r: 8 },
    { label: '改革', color: '#8bffe1', glow: 'rgba(139,255,225,', r: 7 },
    { label: '统一', color: '#f2d36b', glow: 'rgba(242,211,107,', r: 7 },
    { label: '贸易', color: '#91f0a8', glow: 'rgba(145,240,168,', r: 6 },
    { label: '启蒙', color: '#c2b7ff', glow: 'rgba(194,183,255,', r: 6 },
    { label: '革命', color: '#ff7a7a', glow: 'rgba(255,122,122,', r: 7 }
  ]

  concepts.forEach((c, i) => {
    const id = `concept_${i}`
    const node: GNode = {
      id,
      label: c.label,
      type: 'concept',
      importance: c.r,
      x: cx,
      y: cy,
      radius: c.r,
      color: c.color,
      glowColor: c.glow
    }
    nodes.push(node)
    nodeMap.set(id, node)
    conceptIdByLabel.set(c.label, id)
  })

  const eventEdges: Array<[string, string, number]> = [
    ['shangyang_reform', 'qin_unification', 1],
    ['qin_unification', 'han_empire', 1],
    ['han_empire', 'tang_prosperity', 0.6],
    ['han_empire', 'silk_road', 0.8],
    ['tang_prosperity', 'song_innovations', 0.7],
    ['song_innovations', 'mongol_conquests', 0.6],
    ['mongol_conquests', 'black_death', 0.5],
    ['han_empire', 'great_wall', 0.7],
    ['han_empire', 'invention_paper', 0.5],
    ['tang_prosperity', 'invention_gunpowder', 0.6],
    ['song_innovations', 'invention_compass', 0.7],
    ['tang_prosperity', 'invention_printing', 0.5],
    ['mongol_conquests', 'an_shi_rebellion', 0.4],
    ['silk_road', 'zhenghe_voyages', 0.7],
    ['han_empire', 'buddhism_china', 0.5],
    ['tang_prosperity', 'buddhism_china', 0.6],
    ['silk_road', 'alexander_east', 0.5],
    ['alexander_east', 'roman_empire', 0.8],
    ['roman_empire', 'crusades', 0.6],
    ['crusades', 'renaissance', 0.7],
    ['black_death', 'renaissance', 0.7],
    ['renaissance', 'enlightenment', 0.8],
    ['enlightenment', 'french_revolution', 0.9],
    ['enlightenment', 'american_independence', 0.7],
    ['french_revolution', 'american_independence', 0.6],
    ['french_revolution', 'napoleonic_wars', 0.8],
    ['napoleonic_wars', 'latin_american_independence', 0.7],
    ['enlightenment', 'industrial_revolution', 0.6],
    ['industrial_revolution', 'crimean_war', 0.5],
    ['crimean_war', 'world_war_1', 0.5],
    ['world_war_1', 'world_war_2', 0.9],
    ['world_war_2', 'cold_war', 0.9],
    ['cold_war', 'fall_of_berlin_wall', 0.8],
    ['cold_war', 'moon_landing', 0.7],
    ['cold_war', 'internet_birth', 0.6],
    ['world_war_2', 'independence_india', 0.6],
    ['world_war_2', 'state_of_israel', 0.6],
    ['world_war_2', 'african_decolonization', 0.6],
    ['roman_empire', 'justinian_code', 0.7],
    ['renaissance', 'printing_press', 0.7],
    ['industrial_revolution', 'meiji_restoration', 0.5],
    ['meiji_restoration', 'qin_unification', 0.3],
    ['han_empire', 'roman_empire', 0.5],
    ['roman_empire', 'anglo_saxon_chronicle', 0.5],
    ['crusades', 'islamic_golden_age', 0.6],
    ['islamic_golden_age', 'renaissance', 0.5],
    ['islamic_golden_age', 'printing_press', 0.4],
    ['printing_press', 'enlightenment', 0.6],
    ['opium_wars', 'self_strengthening', 0.8],
    ['self_strengthening', 'hundred_days_reform', 0.7],
    ['hundred_days_reform', 'xinhai_revolution', 0.8],
    ['xinhai_revolution', 'may_fourth_movement', 0.8],
    ['xinhai_revolution', 'founding_prc', 0.6],
    ['founding_prc', 'reform_opening', 0.9],
    ['founding_prc', 'korean_war', 0.6],
    ['korean_war', 'cold_war', 0.5],
    ['rome_to_byzantium', 'crusades', 0.5],
    ['rome_to_byzantium', 'justinian_code', 0.7],
    ['industrial_revolution', 'taiping_rebellion', 0.5],
    ['taiping_rebellion', 'opium_wars', 0.6],
    ['french_revolution', 'napoleonic_code', 0.8],
    ['napoleonic_wars', 'napoleonic_code', 0.6],
    ['british_parliament', 'american_independence', 0.5],
    ['world_war_1', 'treaty_versailles', 0.9],
    ['treaty_versailles', 'world_war_2', 0.6],
    ['treaty_versailles', 'french_revolution', 0.3],
  ]

  eventEdges.forEach(([source, target, strength]) => addEdge(source, target, strength))

  const conceptLinks: Array<[string, string, number]> = [
    ['shangyang_reform', '改革', 0.38],
    ['shangyang_reform', '法律', 0.32],
    ['qin_unification', '统一', 0.42],
    ['qin_unification', '帝国', 0.34],
    ['han_empire', '贸易', 0.34],
    ['han_empire', '帝国', 0.34],
    ['alexander_east', '军事', 0.34],
    ['roman_empire', '法律', 0.34],
    ['roman_empire', '帝国', 0.34],
    ['french_revolution', '革命', 0.4],
    ['french_revolution', '启蒙', 0.32],
    ['industrial_revolution', '科技', 0.4],
    ['industrial_revolution', '经济', 0.3],
    ['silk_road', '贸易', 0.35],
    ['tang_prosperity', '文化', 0.35],
    ['song_innovations', '科技', 0.35],
    ['mongol_conquests', '军事', 0.35],
    ['crusades', '军事', 0.3],
    ['renaissance', '文化', 0.4],
    ['enlightenment', '启蒙', 0.45],
    ['cold_war', '政治', 0.35],
    ['world_war_1', '军事', 0.35],
    ['world_war_2', '军事', 0.35],
    ['meiji_restoration', '改革', 0.35],
    ['black_death', '经济', 0.3],
    ['xinhai_revolution', '革命', 0.4],
    ['founding_prc', '政治', 0.35],
    ['reform_opening', '经济', 0.35],
    ['printing_press', '科技', 0.35],
    ['great_wall', '军事', 0.3],
    ['buddhism_china', '文化', 0.35],
    ['moon_landing', '科技', 0.35],
    ['internet_birth', '科技', 0.35],
    ['african_decolonization', '革命', 0.3],
    ['napoleonic_code', '法律', 0.35],
    ['british_parliament', '政治', 0.35],
  ]

  conceptLinks.forEach(([eventId, label, strength]) => {
    const target = conceptId(label)
    if (target) addEdge(eventId, target, strength)
  })

  const conceptConceptLinks: Array<[string, string, number]> = [
    ['政治', '改革', 0.2],
    ['政治', '革命', 0.22],
    ['军事', '帝国', 0.18],
    ['文化', '启蒙', 0.2],
    ['经济', '贸易', 0.2],
    ['科技', '经济', 0.2],
    ['法律', '政治', 0.18],
    ['政治', '统一', 0.16],
    ['军事', '革命', 0.16],
    ['科技', '文化', 0.15],
    ['经济', '改革', 0.16],
    ['帝国', '统一', 0.18],
    ['贸易', '文化', 0.15],
    ['启蒙', '革命', 0.2],
    ['法律', '帝国', 0.16],
    ['改革', '经济', 0.16],
  ]

  conceptConceptLinks.forEach(([a, b, strength]) => {
    const source = conceptId(a)
    const target = conceptId(b)
    if (source && target) addEdge(source, target, strength)
  })

  runLayout()

  for (let i = 0; i < 30; i++) {
    const edgeIdx = Math.floor(Math.random() * edges.length)
    edgeParticles.push({
      t: Math.random(),
      edgeIdx,
      speed: 0.0014 + Math.random() * 0.0022
    })
  }
}

function initBgStars() {
  BG_STARS.length = 0
  const colors = [
    'rgba(255,255,255,A)',
    'rgba(139,255,225,A)',
    'rgba(255,104,184,A)',
    'rgba(125,181,255,A)'
  ]

  for (let i = 0; i < 260; i++) {
    const c = colors[Math.floor(Math.random() * colors.length)]
    BG_STARS.push({
      x: Math.random(),
      y: Math.random(),
      r: 0.45 + Math.random() * 1.25,
      o: 0.12 + Math.random() * 0.46,
      s: 0.00002 + Math.random() * 0.0001,
      p: Math.random() * Math.PI * 2,
      c
    })
  }
}

function drawBg(time: number) {
  const canvas = bgCanvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  ctx.clearRect(0, 0, W, H)

  for (const s of BG_STARS) {
    const flicker = Math.sin(time * s.s * 0.001 + s.p)
    const opacity = s.o * (0.55 + flicker * 0.45)
    const cx = ((s.x + time * s.s * 0.00025) % 1.001) * W
    const cy = s.y * H
    const col = s.c.replace('A', opacity.toFixed(3))

    ctx.beginPath()
    ctx.arc(cx, cy, s.r, 0, Math.PI * 2)
    ctx.fillStyle = col
    ctx.fill()
  }
}

function drawGraph(time: number) {
  const canvas = graphCanvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  ctx.clearRect(0, 0, W, H)

  const sq = (props.searchKeyword || '').trim().toLowerCase()
  const isSearchActive = sq.length > 0
  const hlConcept = highlightConceptId.value
  const hlEventIds = hlConcept ? getConceptEventIds(hlConcept) : null
  const isConceptHighlightActive = hlEventIds !== null

  for (const e of edges) {
    const a = nodeMap.get(e.source)
    const b = nodeMap.get(e.target)
    if (!a || !b) continue

    const isEventEdge = a.type === 'event' && b.type === 'event'
    const isCross = a.region !== b.region
    const conceptEdgeDim = isConceptHighlightActive
      ? !(a.id === hlConcept || b.id === hlConcept || hlEventIds!.has(a.id) || hlEventIds!.has(b.id))
      : false
    const edgeDim = conceptEdgeDim
      ? true
      : (isSearchActive && isEventEdge)
        ? !(a.label.toLowerCase().includes(sq) || b.label.toLowerCase().includes(sq))
        : false

    ctx.beginPath()
    ctx.moveTo(a.x, a.y)
    ctx.lineTo(b.x, b.y)
    if (edgeDim) {
      ctx.strokeStyle = 'rgba(255,255,255,0.03)'
      ctx.lineWidth = 0.3
    } else {
      ctx.strokeStyle = isEventEdge
        ? (isCross ? 'rgba(255,255,255,0.32)' : 'rgba(255,255,255,0.24)')
        : 'rgba(255,255,255,0.08)'
      ctx.lineWidth = isEventEdge ? 1 : 0.6
    }
    ctx.stroke()
  }

  for (const p of edgeParticles) {
    p.t += p.speed
    if (p.t >= 1) {
      p.t -= 1
      p.edgeIdx = Math.floor(Math.random() * edges.length)
    }

    const e = edges[p.edgeIdx]
    const a = nodeMap.get(e.source)
    const b = nodeMap.get(e.target)
    if (!a || !b) continue

    const isEvent = a.type === 'event' && b.type === 'event'
    const px = a.x + (b.x - a.x) * p.t
    const py = a.y + (b.y - a.y) * p.t

    ctx.beginPath()
    ctx.arc(px, py, isEvent ? 1.2 : 0.7, 0, Math.PI * 2)
    ctx.fillStyle = isEvent ? 'rgba(255,255,255,0.5)' : 'rgba(255,255,255,0.22)'
    ctx.fill()
  }

  for (const node of nodes) {
    const isHover = hoveredNode.value?.id === node.id
    const sq = (props.searchKeyword || '').trim().toLowerCase()
    const isSearchActive = sq.length > 0
    const matchesSearch = isSearchActive
      ? node.label.toLowerCase().includes(sq)
      : true
    const matchesConcept = isConceptHighlightActive
      ? (node.type === 'concept' ? node.id === hlConcept : hlEventIds!.has(node.id))
      : true
    const nodeDim = (isSearchActive && !matchesSearch) || (isConceptHighlightActive && !matchesConcept)
    const baseR = node.radius
    const drawR = isHover ? baseR * 1.28 : baseR
    const isImportant = node.type === 'event' && node.importance >= 9
    const haloSize = node.type === 'event' ? drawR * 3.4 : drawR * 2.2

    const grad = ctx.createRadialGradient(node.x, node.y, 0, node.x, node.y, haloSize)
    grad.addColorStop(0, node.glowColor + (nodeDim ? '0.06)' : (node.type === 'event' ? '0.34)' : '0.18)')))
    grad.addColorStop(0.55, node.glowColor + (node.type === 'event' ? '0.08)' : '0.04)'))
    grad.addColorStop(1, node.glowColor + '0)')
    ctx.beginPath()
    ctx.arc(node.x, node.y, haloSize, 0, Math.PI * 2)
    ctx.fillStyle = grad
    ctx.fill()

    ctx.globalAlpha = nodeDim ? 0.25 : 1
    ctx.beginPath()
    ctx.arc(node.x, node.y, drawR, 0, Math.PI * 2)
    const coreGrad = ctx.createRadialGradient(node.x, node.y, 0, node.x, node.y, drawR)
    coreGrad.addColorStop(0, '#ffffff')
    coreGrad.addColorStop(0.34, node.color)
    coreGrad.addColorStop(1, node.glowColor + '0.34)')
    ctx.fillStyle = coreGrad
    ctx.fill()
    ctx.globalAlpha = 1

    if (node.type === 'event') {
      drawEventOrbit(ctx, node, drawR, time, isHover || isImportant || matchesSearch)
    }

    if (isHover && node.type === 'event') {
      ctx.beginPath()
      ctx.arc(node.x, node.y, drawR + 5, 0, Math.PI * 2)
      ctx.strokeStyle = node.color
      ctx.lineWidth = 1.4
      ctx.globalAlpha = 0.52 + Math.sin(time * 0.004) * 0.28
      ctx.stroke()
      ctx.globalAlpha = 1
    }

    if (matchesSearch && isSearchActive && node.type === 'event') {
      ctx.beginPath()
      ctx.arc(node.x, node.y, drawR + 8, 0, Math.PI * 2)
      ctx.strokeStyle = '#ffffff'
      ctx.lineWidth = 2
      ctx.globalAlpha = 0.6 + Math.sin(time * 0.003) * 0.3
      ctx.stroke()
      ctx.globalAlpha = 1
    }

    const labelAlpha = nodeDim ? 0.1 : (isHover ? 1 : (node.type === 'event' ? 0.74 : 0.26))
    ctx.font = node.type === 'event'
      ? `700 ${isHover ? 13 : 11}px "Noto Serif SC", serif`
      : `400 ${isHover ? 11 : 10}px "JetBrains Mono", monospace`
    ctx.textAlign = 'center'
    ctx.textBaseline = 'top'
    ctx.fillStyle = isHover ? '#ffffff' : (matchesSearch && isSearchActive ? '#ffffff' : (node.type === 'event' ? node.color : 'rgba(255,255,255,0.45)'))
    ctx.globalAlpha = labelAlpha
    ctx.fillText(node.label, node.x, node.y + drawR + 6)
    ctx.globalAlpha = 1
  }
}

function drawEventOrbit(
  ctx: CanvasRenderingContext2D,
  node: GNode,
  drawR: number,
  time: number,
  prominent: boolean
) {
  const orbitR1 = drawR * (prominent ? 2.1 : 1.75)
  const orbitR2 = drawR * (prominent ? 2.7 : 2.25)
  const rot1 = time * 0.00075 + node.importance * 0.7
  const rot2 = time * 0.00055 + node.importance * 1.3
  const alpha = prominent ? 0.34 : 0.14

  ctx.save()
  ctx.translate(node.x, node.y)
  ctx.rotate(rot1)
  ctx.beginPath()
  ctx.ellipse(0, 0, orbitR1, orbitR1 * 0.34, 0, 0, Math.PI * 2)
  ctx.strokeStyle = node.glowColor + `${alpha})`
  ctx.lineWidth = prominent ? 0.9 : 0.55
  ctx.stroke()
  ctx.restore()

  if (!prominent) return

  ctx.save()
  ctx.translate(node.x, node.y)
  ctx.rotate(rot2)
  ctx.beginPath()
  ctx.ellipse(0, 0, orbitR2, orbitR2 * 0.28, 0, 0, Math.PI * 2)
  ctx.strokeStyle = node.glowColor + '0.18)'
  ctx.lineWidth = 0.6
  ctx.stroke()
  ctx.restore()
}

function animate(time: number) {
  drawBg(time)
  drawGraph(time)
  animId = requestAnimationFrame(animate)
}

function hitTest(mx: number, my: number): GNode | null {
  for (let i = nodes.length - 1; i >= 0; i--) {
    const n = nodes[i]
    const dx = mx - n.x
    const dy = my - n.y
    if (dx * dx + dy * dy < (n.radius + 9) * (n.radius + 9)) return n
  }
  return null
}

function onMouseMove(e: MouseEvent) {
  const canvas = graphCanvasRef.value
  const container = containerRef.value
  if (!canvas || !container) return

  const rect = canvas.getBoundingClientRect()
  mouse.x = e.clientX - rect.left
  mouse.y = e.clientY - rect.top
  const hit = hitTest(mouse.x, mouse.y)
  hoveredNode.value = hit

  if (hit) {
    tipX.value = e.clientX - container.getBoundingClientRect().left + 16
    tipY.value = e.clientY - container.getBoundingClientRect().top - 10
    canvas.style.cursor = 'pointer'
  } else {
    canvas.style.cursor = 'default'
  }
}

function onMouseLeave() {
  mouse.x = -999
  mouse.y = -999
  hoveredNode.value = null
}

function conceptConnectedCount(conceptId: string): number {
  let count = 0
  for (const e of edges) {
    if (e.source === conceptId || e.target === conceptId) count++
  }
  return count
}

function getConceptEventIds(conceptId: string): Set<string> {
  const ids = new Set<string>()
  for (const e of edges) {
    if (e.source === conceptId) ids.add(e.target)
    else if (e.target === conceptId) ids.add(e.source)
  }
  return ids
}

function onClick() {
  if (!hoveredNode.value) return
  if (hoveredNode.value.type === 'event') {
    highlightConceptId.value = null
    emit('selectEvent', hoveredNode.value.id)
  } else if (hoveredNode.value.type === 'concept') {
    if (highlightConceptId.value === hoveredNode.value.id) {
      highlightConceptId.value = null
    } else {
      highlightConceptId.value = hoveredNode.value.id
    }
  }
}

function formatYear(year: number): string {
  if (year < 0) return `公元前${Math.abs(year)}年`
  return `${year}年`
}

function onResize() {
  const c = containerRef.value
  if (!c) return

  W = c.clientWidth
  H = c.clientHeight

  for (const cv of [bgCanvasRef.value, graphCanvasRef.value]) {
    if (!cv) continue
    const dpr = window.devicePixelRatio || 1
    cv.width = W * dpr
    cv.height = H * dpr
    cv.style.width = `${W}px`
    cv.style.height = `${H}px`
    const ctx = cv.getContext('2d')
    if (ctx) ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  }

  if (nodes.length === 0) {
    initGraph()
  } else {
    runLayout()
  }
}

let resizeObs: ResizeObserver | null = null

onMounted(() => {
  initBgStars()
  onResize()
  animId = requestAnimationFrame(animate)
  window.addEventListener('resize', onResize)
  if (containerRef.value) {
    resizeObs = new ResizeObserver(() => {
      if (W === 0 || H === 0) onResize()
    })
    resizeObs.observe(containerRef.value)
  }
})

onBeforeUnmount(() => {
  if (animId !== null) cancelAnimationFrame(animId)
  window.removeEventListener('resize', onResize)
  resizeObs?.disconnect()
})
</script>

<style scoped>
.cosmic-map {
  position: relative;
  width: 100%;
  height: 100vh;
  min-height: 560px;
  overflow: hidden;
  background:
    radial-gradient(circle at 68% 42%, rgba(139, 255, 225, 0.08), transparent 18%),
    radial-gradient(circle at 46% 52%, rgba(255, 104, 184, 0.08), transparent 16%),
    linear-gradient(180deg, #02050b 0%, #03060d 54%, #010309 100%);
  user-select: none;
}

.layer-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
}

.layer-graph {
  position: absolute;
  inset: 0;
  z-index: 1;
}

.hover-tip {
  position: absolute;
  z-index: 50;
  max-width: 220px;
  padding: 10px 13px;
  pointer-events: none;
  background: rgba(2, 6, 13, 0.86);
  border: 1px solid rgba(139, 255, 225, 0.48);
  border-radius: 4px;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.45), 0 0 20px rgba(139, 255, 225, 0.1);
  backdrop-filter: blur(10px);
}

.tip-name {
  margin-bottom: 2px;
  color: #ffffff;
  font-family: 'Noto Serif SC', serif;
  font-size: 14px;
  font-weight: 800;
}

.tip-year {
  color: #8bffe1;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
}

.tip-hint {
  margin-top: 4px;
  color: rgba(238, 249, 255, 0.58);
  font-size: 10px;
}

.tip-concept {
  color: rgba(212, 168, 75, 0.9);
  font-size: 11px;
}

.tooltip-enter-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.tooltip-leave-active {
  transition: opacity 0.1s ease, transform 0.1s ease;
}

.tooltip-enter-from,
.tooltip-leave-to {
  opacity: 0;
  transform: translateY(4px);
}

.map-nebula {
  position: absolute;
  z-index: 0;
  border-radius: 50%;
  pointer-events: none;
}

.nebula-1 {
  left: 50%;
  top: 24%;
  width: 420px;
  height: 320px;
  background: radial-gradient(ellipse, rgba(139, 255, 225, 0.035) 0%, transparent 70%);
}

.nebula-2 {
  left: 30%;
  top: 36%;
  width: 340px;
  height: 260px;
  background: radial-gradient(ellipse, rgba(255, 104, 184, 0.035) 0%, transparent 72%);
}
</style>
