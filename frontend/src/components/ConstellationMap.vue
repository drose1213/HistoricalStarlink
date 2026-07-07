<template>
  <div ref="containerRef" class="constellation-map" :class="`constellation-map--${mode}`">
    <canvas ref="bgCanvasRef" class="map-layer map-layer--bg" />
    <canvas
      ref="graphCanvasRef"
      class="map-layer map-layer--graph"
      @mousemove="onMouseMove"
      @mouseleave="onMouseLeave"
      @click="onClick"
    />

    <Transition name="tip-fade">
      <div v-if="hoveredNode" class="constellation-tip" :style="{ left: tipX + 'px', top: tipY + 'px' }">
        <div class="tip-kicker">{{ tipKicker(hoveredNode) }}</div>
        <div class="tip-title">{{ nodeLabel(hoveredNode) }}</div>
        <div v-if="hoveredNode.year" class="tip-year">{{ formatYear(hoveredNode.year) }}</div>
        <div v-if="hoveredNode.description" class="tip-desc">{{ hoveredNode.description }}</div>
        <div v-if="hoveredNode.kind === 'event' && hoveredNode.role !== 'center'" class="tip-action">{{ t('map.enterEvent') }}</div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { StarlinkGraph, StarlinkGraphNode } from '@/utils/starlinkGraph'
import { shouldShowStarlinkLabel } from '@/utils/starlinkGraph'
import { mapYearToTimelineY, resolveStarfieldX, resolveTimelineLaneY } from '@/utils/timelineLayout'
import { useI18n } from '@/composables/useI18n'

const { t, tf, tc, locale } = useI18n()

interface PositionedNode extends StarlinkGraphNode {
  x: number
  y: number
  tx: number
  ty: number
  phase: number
  orbit: number
  connectionCount: number
}

interface BackgroundStar {
  x: number
  y: number
  r: number
  o: number
  s: number
  phase: number
  color: string
}

interface EdgeParticle {
  edgeIndex: number
  t: number
  speed: number
}

const props = withDefaults(defineProps<{
  graph: StarlinkGraph
  mode?: 'home' | 'detail'
  searchKeyword?: string
}>(), {
  mode: 'home',
  searchKeyword: '',
})

const emit = defineEmits<{
  selectEvent: [id: string]
}>()

const containerRef = ref<HTMLDivElement | null>(null)
const bgCanvasRef = ref<HTMLCanvasElement | null>(null)
const graphCanvasRef = ref<HTMLCanvasElement | null>(null)
const hoveredNode = ref<PositionedNode | null>(null)
const tipX = ref(0)
const tipY = ref(0)

const nodes: PositionedNode[] = []
const nodeMap = new Map<string, PositionedNode>()
const bgStars: BackgroundStar[] = []
const particles: EdgeParticle[] = []
const adjacencyMap = new Map<string, Set<string>>()

let width = 0
let height = 0
let animationId: number | null = null
let resizeObserver: ResizeObserver | null = null

// 时间轴边界 (首页垂直时间轴布局使用, 由 rebuildGraph 从事件年份动态计算)
let yearBounds = { min: -500, max: 2025 }
let yearSpan = yearBounds.max - yearBounds.min

// 首页时间轴布局共享常量 (节点定位 + 刻度绘制都用)
const HOME_TOP_PAD = 112
const HOME_BOTTOM_PAD = 92

/** 年份 → Y 像素 — 对数感知映射 (新→旧)
 *  让密集的近现代事件获得更多视觉空间, 远古 (低密度) 自然压缩到底部
 *  age=0 (year=max, 最新) → ratio=0 (顶),  age=yearSpan (year=min, 最旧) → ratio=1 (底) */
function yearToY(year: number | undefined, topPad = HOME_TOP_PAD, bottomPad = HOME_BOTTOM_PAD): number {
  return mapYearToTimelineY(year, {
    minYear: yearBounds.min,
    maxYear: yearBounds.max,
    height,
    topPad,
    bottomPad,
  })
}

function hash(value: string): number {
  let h = 2166136261
  for (let i = 0; i < value.length; i++) {
    h ^= value.charCodeAt(i)
    h = Math.imul(h, 16777619)
  }
  return Math.abs(h >>> 0)
}

function resetCanvases(): void {
  for (const canvas of [bgCanvasRef.value, graphCanvasRef.value]) {
    if (!canvas) continue
    const dpr = window.devicePixelRatio || 1
    canvas.width = Math.max(1, Math.floor(width * dpr))
    canvas.height = Math.max(1, Math.floor(height * dpr))
    canvas.style.width = `${width}px`
    canvas.style.height = `${height}px`
    const ctx = canvas.getContext('2d')
    if (ctx) ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  }
}

function rebuildBackground(): void {
  bgStars.length = 0
  const count = props.mode === 'detail' ? 220 : 360
  const colors = ['#ffffff', '#86ffe8', '#ff6db6', '#f0c84b', '#79d8ff']
  for (let i = 0; i < count; i++) {
    bgStars.push({
      x: Math.random(),
      y: Math.random(),
      r: 0.35 + Math.random() * 1.7,
      o: 0.12 + Math.random() * 0.7,
      s: 0.00003 + Math.random() * 0.00016,
      phase: Math.random() * Math.PI * 2,
      color: colors[Math.floor(Math.random() * colors.length)],
    })
  }
}

function rebuildGraph(): void {
  nodes.length = 0
  nodeMap.clear()
  particles.length = 0
  adjacencyMap.clear()

  for (const node of props.graph.nodes) {
    const h = hash(node.id)
    const positioned: PositionedNode = {
      ...node,
      x: width / 2,
      y: height / 2,
      tx: width / 2,
      ty: height / 2,
      phase: (h % 628) / 100,
      orbit: 0.8 + ((h % 100) / 100) * 0.8,
      connectionCount: 0,
    }
    nodes.push(positioned)
    nodeMap.set(positioned.id, positioned)
  }

  for (const edge of props.graph.edges) {
    const source = nodeMap.get(edge.source)
    const target = nodeMap.get(edge.target)
    if (source) source.connectionCount += 1
    if (target) target.connectionCount += 1
    if (!adjacencyMap.has(edge.source)) adjacencyMap.set(edge.source, new Set())
    if (!adjacencyMap.has(edge.target)) adjacencyMap.set(edge.target, new Set())
    adjacencyMap.get(edge.source)?.add(edge.target)
    adjacencyMap.get(edge.target)?.add(edge.source)
  }

  // 收集事件年份用于垂直时间轴布局
  const eventYears: number[] = []
  for (const n of props.graph.nodes) {
    if (n.kind === 'event' && typeof n.year === 'number') {
      eventYears.push(n.year)
    }
  }
  if (eventYears.length > 0) {
    yearBounds = { min: Math.min(...eventYears), max: Math.max(...eventYears) }
    yearSpan = Math.max(1, yearBounds.max - yearBounds.min)
  }

  layoutNodes()

  const particleCount = props.mode === 'home'
    ? Math.min(36, Math.max(8, Math.ceil(props.graph.edges.length * 0.35)))
    : Math.min(90, Math.max(12, props.graph.edges.length * 2))
  for (let i = 0; i < particleCount; i++) {
    particles.push({
      edgeIndex: props.graph.edges.length > 0 ? i % props.graph.edges.length : 0,
      t: Math.random(),
      speed: 0.001 + Math.random() * 0.0026,
    })
  }
}

function layoutNodes(): void {
  if (width <= 0 || height <= 0) return
  if (props.mode === 'detail') {
    layoutDetailNodes()
  } else {
    layoutHomeNodes()
  }
}

function layoutHomeNodes(): void {
  // ── 年代星座布局 ──
  //   Y 轴保持严格年代秩序: 新事件在上, 早期事件在下。
  //   X 轴按确定性星场散布, 形成图二那种网络感, 不再固定左右两列。
  const topPad = HOME_TOP_PAD
  const bottomPad = HOME_BOTTOM_PAD
  const railX = width / 2

  const eventNodes = nodes.filter(node => node.kind === 'event')
  const conceptNodes = nodes.filter(node => node.kind === 'concept')

  const ySlots = resolveTimelineLaneY(
    eventNodes.map(node => ({
      id: node.id,
      targetY: yearToY(node.year, topPad, bottomPad),
      radius: Math.min(node.radius, 5),
    })),
    {
      minY: topPad,
      maxY: height - bottomPad,
      minGap: Math.max(14, Math.min(22, height * 0.024)),
    },
  )
  const yById = new Map(ySlots.map(slot => [slot.id, slot.y]))

  eventNodes.forEach((node) => {
    node.ty = yById.get(node.id) ?? yearToY(node.year, topPad, bottomPad)
    node.tx = resolveStarfieldX({
      id: node.id,
      width,
      railX,
      region: node.region,
      importance: node.importance,
    })
  })

  // 概念节点靠近其关联事件的质心, 形成图二式“星座注脚”。
  conceptNodes.forEach((node) => {
    const relatedEvents = [...(adjacencyMap.get(node.id) || [])]
      .map(id => nodeMap.get(id))
      .filter((related): related is PositionedNode => related?.kind === 'event')
    const angleSeed = (hash(node.id) % 360) / 360 * Math.PI * 2
    const drift = Math.min(width, height) * (0.055 + (hash(`${node.id}_d`) % 90) / 1000)
    if (relatedEvents.length > 0) {
      const avgX = relatedEvents.reduce((sum, related) => sum + related.tx, 0) / relatedEvents.length
      const avgY = relatedEvents.reduce((sum, related) => sum + related.ty, 0) / relatedEvents.length
      node.tx = avgX + Math.cos(angleSeed) * drift
      node.ty = avgY + Math.sin(angleSeed) * drift
    } else {
      node.tx = resolveStarfieldX({ id: node.id, width, railX, importance: node.importance })
      node.ty = topPad + ((hash(`${node.id}_y`) % 1000) / 1000) * (height - topPad - bottomPad)
    }
    // 概念节点保持轻量但可识别, hover 时显示具体关联备注
    node.radius = 3.8
  })

  clampTargets()
}

function layoutDetailNodes(): void {
  const cx = width * 0.52
  const cy = height * 0.5
  const topPad = Math.max(72, height * 0.14)
  const bottomPad = Math.max(72, height * 0.14)
  const railX = cx
  const relatedEvents = nodes.filter(node => node.kind === 'event' && node.role !== 'center')
  const concepts = nodes.filter(node => node.kind === 'concept')
  const center = nodes.find(node => node.role === 'center')

  if (center) {
    center.tx = cx
    center.ty = cy
  }

  const ySlots = resolveTimelineLaneY(
    relatedEvents.map(node => {
      const timelineY = yearToY(node.year, topPad, bottomPad)
      return {
        id: node.id,
        targetY: cy + (timelineY - cy) * 0.62,
        radius: Math.min(node.radius, 8),
      }
    }),
    {
      minY: topPad,
      maxY: height - bottomPad,
      minGap: Math.max(34, Math.min(54, height * 0.07)),
    },
  )
  const yById = new Map(ySlots.map(slot => [slot.id, slot.y]))

  relatedEvents.forEach((node) => {
    const sideBias = node.role === 'cause'
      ? -width * 0.16
      : node.role === 'consequence'
        ? width * 0.16
        : 0
    const starfieldX = resolveStarfieldX({
      id: node.id,
      width,
      railX,
      region: node.region,
      importance: node.importance,
    })
    node.tx = cx + sideBias + (starfieldX - railX) * 0.42
    node.ty = yById.get(node.id) ?? cy + (yearToY(node.year, topPad, bottomPad) - cy) * 0.62
  })

  concepts.forEach((node) => {
    const relatedNodes = [...(adjacencyMap.get(node.id) || [])]
      .map(id => nodeMap.get(id))
      .filter((related): related is PositionedNode => related !== undefined)
    const angleSeed = (hash(node.id) % 360) / 360 * Math.PI * 2
    const drift = Math.min(width, height) * (0.07 + (hash(`${node.id}_detail`) % 70) / 1000)
    const baseX = relatedNodes.length > 0
      ? relatedNodes.reduce((sum, related) => sum + related.tx, 0) / relatedNodes.length
      : cx
    const baseY = relatedNodes.length > 0
      ? relatedNodes.reduce((sum, related) => sum + related.ty, 0) / relatedNodes.length
      : cy
    node.tx = baseX + Math.cos(angleSeed) * drift
    node.ty = baseY + Math.sin(angleSeed) * drift
    node.radius = 3.8
  })

  clampTargets()
}

function clampTargets(): void {
  for (const node of nodes) {
    const pad = props.mode === 'home'
      ? Math.max(26, node.radius * 3.1)
      : Math.max(42, node.radius * 4)
    let minX = pad
    let maxX = width - pad
    node.tx = Math.max(minX, Math.min(maxX, node.tx))
    node.ty = Math.max(pad, Math.min(height - pad, node.ty))
    if (node.x === width / 2 && node.y === height / 2) {
      node.x = node.tx
      node.y = node.ty
    }
  }
}

function updateNodePositions(time: number): void {
  for (const node of nodes) {
    const drift = props.mode === 'detail' && node.role === 'center' ? 0.8 : 2.4
    const dx = Math.cos(time * 0.00032 * node.orbit + node.phase) * drift
    const dy = Math.sin(time * 0.00028 * node.orbit + node.phase) * drift
    node.x += (node.tx + dx - node.x) * 0.045
    node.y += (node.ty + dy - node.y) * 0.045
  }
}

function drawBackground(time: number): void {
  const canvas = bgCanvasRef.value
  const ctx = canvas?.getContext('2d')
  if (!canvas || !ctx) return

  ctx.clearRect(0, 0, width, height)

  // ── 深空星云基底 ──
  const core = ctx.createRadialGradient(width * 0.5, height * 0.52, 0, width * 0.5, height * 0.52, Math.max(width, height) * 0.72)
  core.addColorStop(0, props.mode === 'detail' ? 'rgba(255,109,182,0.10)' : 'rgba(255,255,255,0.055)')
  core.addColorStop(0.38, 'rgba(134,255,232,0.035)')
  core.addColorStop(1, 'rgba(1,3,9,0)')
  ctx.fillStyle = core
  ctx.fillRect(0, 0, width, height)

  // ── 赛博朋克六角网格 (仅首页模式) ──
  if (props.mode === 'home') {
    drawHexGrid(ctx, time)
  }

  // ── 星空粒子 ──
  for (const star of bgStars) {
    const flicker = 0.55 + Math.sin(time * star.s + star.phase) * 0.45
    const x = ((star.x + time * star.s * 0.00018) % 1.002) * width
    const y = star.y * height
    ctx.beginPath()
    ctx.arc(x, y, star.r, 0, Math.PI * 2)
    ctx.fillStyle = rgba(star.color, star.o * flicker)
    ctx.fill()
  }

  // ── CRT 水平扫描线 ──
  drawScanlines(ctx, time)

  // ── 暗角渐晕 ──
  drawVignette(ctx)

  // ── 史河主轴 (仅首页) — 发光中线 + 时间粒子流, 画在背景层 ──
  // ── 时间轴导轨 (仅首页) — 年份刻度 + 文字标签, 画在最上层保证可读 ──
  if (props.mode === 'home') {
    drawTimelineRail(ctx)
  }
}

/** 六角网格 — 赛博朋克标志性背景元素 */
function drawHexGrid(ctx: CanvasRenderingContext2D, time: number): void {
  const hexSize = 38
  const hexH = hexSize * Math.sqrt(3)
  const cols = Math.ceil(width / (hexSize * 1.5)) + 2
  const rows = Math.ceil(height / hexH) + 2
  const drift = time * 0.004

  ctx.lineWidth = 0.35
  // 微妙的呼吸效果
  const breathe = 0.028 + Math.sin(time * 0.0004) * 0.012
  ctx.strokeStyle = `rgba(134,255,232,${breathe})`

  for (let row = 0; row < rows; row++) {
    for (let col = 0; col < cols; col++) {
      const cx = col * hexSize * 1.5
      const cy = row * hexH + (col % 2 === 1 ? hexH / 2 : 0)
      // 每个六角格有微弱的随机明暗变化，避免均匀死板
      const cellNoise = Math.sin(cx * 0.017 + cy * 0.013 + drift * 0.3) * 0.01
      ctx.globalAlpha = 1
      ctx.beginPath()
      for (let i = 0; i < 6; i++) {
        const angle = (Math.PI / 3) * i - Math.PI / 6
        const px = cx + hexSize * 0.48 * Math.cos(angle)
        const py = cy + hexSize * 0.48 * Math.sin(angle)
        if (i === 0) ctx.moveTo(px, py)
        else ctx.lineTo(px, py)
      }
      ctx.closePath()
      ctx.globalAlpha = 0.6 + cellNoise
      ctx.stroke()
    }
  }
  ctx.globalAlpha = 1
}

/** CRT 扫描线 — 模拟老式显示器的横纹 */
function drawScanlines(ctx: CanvasRenderingContext2D, time: number): void {
  // 快速移动的亮线
  const scanY = ((time * 0.06) % (height + 40)) - 20
  const grad = ctx.createLinearGradient(0, scanY - 18, 0, scanY + 18)
  grad.addColorStop(0, 'rgba(134,255,232,0)')
  grad.addColorStop(0.4, 'rgba(134,255,232,0.028)')
  grad.addColorStop(0.5, 'rgba(134,255,232,0.055)')
  grad.addColorStop(0.6, 'rgba(134,255,232,0.028)')
  grad.addColorStop(1, 'rgba(134,255,232,0)')
  ctx.fillStyle = grad
  ctx.fillRect(0, scanY - 18, width, 36)

  // 全屏极细横纹 (模拟CRT磷光条纹)
  ctx.fillStyle = 'rgba(0,0,0,0.06)'
  for (let y = 0; y < height; y += 3) {
    ctx.fillRect(0, y, width, 1)
  }
}

/** 暗角渐晕 — 四角压暗聚焦中心 */
function drawVignette(ctx: CanvasRenderingContext2D): void {
  const vignette = ctx.createRadialGradient(
    width / 2, height / 2, Math.min(width, height) * 0.28,
    width / 2, height / 2, Math.max(width, height) * 0.76,
  )
  vignette.addColorStop(0, 'rgba(0,0,0,0)')
  vignette.addColorStop(0.6, 'rgba(0,0,0,0.08)')
  vignette.addColorStop(1, 'rgba(0,0,0,0.38)')
  ctx.fillStyle = vignette
  ctx.fillRect(0, 0, width, height)
}

/** Home timeline ticks and year labels without the previous central light pillar. */
function drawTimelineRail(ctx: CanvasRenderingContext2D): void {
  if (props.mode !== 'home') return
  const railX = width / 2
  const topPad = HOME_TOP_PAD
  const bottomPad = HOME_BOTTOM_PAD

  ctx.save()

  // ── 顶部 / 底部方向标记 (NEWER / OLDER), 带轻微辉光 ──
  ctx.font = '700 9px "JetBrains Mono", ui-monospace, monospace'
  ctx.textBaseline = 'middle'
  ctx.textAlign = 'left'
  ctx.shadowColor = '#86ffe8'
  ctx.shadowBlur = 6
  ctx.fillStyle = 'rgba(200, 255, 245, 0.85)'
  ctx.fillText('▼ NEWER', railX + 10, topPad - 16)
  ctx.shadowColor = '#ff6db6'
  ctx.fillStyle = 'rgba(255, 180, 210, 0.7)'
  ctx.fillText('OLDER ▲', railX + 10, height - bottomPad + 16)
  ctx.shadowBlur = 0

  // ── 年份刻度 — 对数感知下的步长自适应 (250 / 500 / 1000) ──
  const tickStep = yearSpan > 3000 ? 1000 : yearSpan > 1500 ? 500 : 250
  const tickStart = Math.floor(yearBounds.min / tickStep) * tickStep
  const tickEnd = Math.ceil(yearBounds.max / tickStep) * tickStep

  ctx.font = '500 10px "JetBrains Mono", ui-monospace, monospace'

  for (let year = tickStart; year <= tickEnd; year += tickStep) {
    if (year < yearBounds.min - 50 || year > yearBounds.max + 50) continue
    const y = yearToY(year, topPad, bottomPad)
    if (y < topPad - 6 || y > height - bottomPad + 6) continue

    // 刻度短线
    ctx.strokeStyle = 'rgba(134, 255, 232, 0.36)'
    ctx.lineWidth = 1
    ctx.beginPath()
    ctx.moveTo(railX - 5, y)
    ctx.lineTo(railX + 5, y)
    ctx.stroke()

    // 引导线到右侧标签区
    ctx.strokeStyle = 'rgba(134, 255, 232, 0.10)'
    ctx.beginPath()
    ctx.moveTo(railX + 5, y)
    ctx.lineTo(width - 76, y)
    ctx.stroke()

    // 年份标签 (BC 用品红, AD 用青色)
    const isBC = year < 0
    const absYear = Math.abs(year)
    const label = isBC ? `公元前 ${absYear}` : `公元 ${absYear}`
    ctx.textAlign = 'right'
    ctx.fillStyle = isBC
      ? 'rgba(255, 109, 182, 0.5)'
      : 'rgba(134, 255, 232, 0.55)'
    ctx.fillText(label, width - 14, y)
  }

  ctx.restore()
}

function drawGraph(time: number): void {
  const canvas = graphCanvasRef.value
  const ctx = canvas?.getContext('2d')
  if (!canvas || !ctx) return
  const search = props.searchKeyword.trim().toLowerCase()
  const activeHover = hoveredNode.value
  const focusIds = getFocusNodeIds(activeHover)

  ctx.clearRect(0, 0, width, height)
  updateNodePositions(time)
  drawEdges(ctx, time, activeHover, focusIds)
  drawParticles(ctx, time)
  drawNodes(ctx, time, search, activeHover, focusIds)
}

function drawEdges(
  ctx: CanvasRenderingContext2D,
  time: number,
  activeHover: PositionedNode | null,
  focusIds: Set<string> | null,
): void {
  for (const edge of props.graph.edges) {
    const source = nodeMap.get(edge.source)
    const target = nodeMap.get(edge.target)
    if (!source || !target) continue
    const highlighted = activeHover ? source.id === activeHover.id || target.id === activeHover.id : false
    const dimmedByFocus = focusIds ? !(focusIds.has(source.id) && focusIds.has(target.id)) : false

    // ── 赛博线路: 两段式折角路径 (L形拐角) ──
    ctx.beginPath()
    ctx.moveTo(source.x, source.y)
    ctx.lineTo(target.x, target.y)

    const color = highlighted
      ? 'rgba(255,255,255,0.85)'
      : dimmedByFocus
        ? 'rgba(255,255,255,0.03)'
        : edgeColor(edge.role, edge.strength)
    ctx.strokeStyle = color
    ctx.lineWidth = highlighted ? 1.5 : dimmedByFocus ? 0.3 : 0.35 + edge.strength * 0.55
    ctx.stroke()

    // ── 边线发光层 (高亮或非淡化时) ──
    if (!dimmedByFocus && (highlighted || edge.strength > 0.6)) {
      ctx.save()
      ctx.globalAlpha = highlighted ? 0.38 : 0.08
      ctx.shadowColor = edge.role === 'cause' ? '#86ffe8' : edge.role === 'consequence' ? '#ff6db6' : '#f0c84b'
      ctx.shadowBlur = highlighted ? 12 : 5
      ctx.beginPath()
      ctx.moveTo(source.x, source.y)
      ctx.lineTo(target.x, target.y)
      ctx.strokeStyle = color
      ctx.lineWidth = highlighted ? 2.4 : 1.0
      ctx.stroke()
      ctx.restore()
    }
  }
}

function drawParticles(ctx: CanvasRenderingContext2D, _time: number): void {
  if (props.graph.edges.length === 0) return
  for (const particle of particles) {
    particle.t += particle.speed
    if (particle.t >= 1) {
      particle.t -= 1
      particle.edgeIndex = Math.floor(Math.random() * props.graph.edges.length)
    }
    const edge = props.graph.edges[particle.edgeIndex]
    const source = nodeMap.get(edge.source)
    const target = nodeMap.get(edge.target)
    if (!source || !target) continue
    const x = source.x + (target.x - source.x) * particle.t
    const y = source.y + (target.y - source.y) * particle.t

    // 区域配色粒子
    const particleColor = edge.role === 'cause'
      ? 'rgba(134,255,232,'
      : edge.role === 'consequence'
        ? 'rgba(255,109,182,'
        : 'rgba(240,200,75,'

    // ── 拖尾效果: 绘制3-4个尾迹残影 ──
    const trailCount = 4
    for (let t = trailCount; t >= 0; t--) {
      const trailT = particle.t - t * 0.012
      if (trailT < 0) continue
      const tx = source.x + (target.x - source.x) * trailT
      const ty = source.y + (target.y - source.y) * trailT
      const alpha = (1 - t / trailCount) * 0.42
      const r = (props.mode === 'detail' ? 1.4 : 0.95) * (1 - t / trailCount * 0.6)
      ctx.beginPath()
      ctx.arc(tx, ty, r, 0, Math.PI * 2)
      ctx.fillStyle = `${particleColor}${alpha})`
      ctx.fill()
    }

    // 主粒子核心 (更亮)
    ctx.beginPath()
    ctx.arc(x, y, props.mode === 'detail' ? 1.6 : 1.1, 0, Math.PI * 2)
    ctx.fillStyle = `${particleColor}0.72)`
    ctx.fill()
  }
}

function drawNodes(
  ctx: CanvasRenderingContext2D,
  time: number,
  search: string,
  activeHover: PositionedNode | null,
  focusIds: Set<string> | null,
): void {
  const sorted = [...nodes].sort((a, b) => {
    if (activeHover?.id === a.id) return 1
    if (activeHover?.id === b.id) return -1
    return a.radius - b.radius
  })

  for (const node of sorted) {
    const isHover = activeHover?.id === node.id
    const label = nodeLabel(node)
    const matchesSearch = search ? label.toLowerCase().includes(search) : true
    const dimmedBySearch = search.length > 0 && !matchesSearch
    const dimmedByFocus = focusIds ? !focusIds.has(node.id) : false
    const dimmed = dimmedBySearch || dimmedByFocus
    const isConnected = node.connectionCount > 0
    const radius = node.role === 'center' ? node.radius * 1.45 : node.radius
    const drawRadius = isHover ? radius * 1.34 : radius

    drawHalo(ctx, node, drawRadius, dimmed, isConnected, time)
    drawCore(ctx, node, drawRadius, dimmed, isConnected, time)

    if (node.kind === 'event') {
      drawOrbit(ctx, node, drawRadius, time, isConnected && (isHover || node.role === 'center' || node.importance >= 9))
    }

    drawLabel(ctx, node, drawRadius, isHover, dimmed, isConnected)
  }
}

function getFocusNodeIds(activeHover: PositionedNode | null): Set<string> | null {
  if (!activeHover) return null
  const focusIds = new Set<string>([activeHover.id])
  for (const relatedId of adjacencyMap.get(activeHover.id) || []) {
    focusIds.add(relatedId)
  }
  return focusIds
}

function drawHalo(
  ctx: CanvasRenderingContext2D,
  node: PositionedNode,
  radius: number,
  dimmed: boolean,
  isConnected: boolean,
  time: number,
): void {
  // ── 多层光晕: 外层大弥散 + 内层锐利核心 ──
  const halo = node.role === 'center' ? radius * 7.2 : radius * (isConnected ? 4.2 : 2.1)
  const gradient = ctx.createRadialGradient(node.x, node.y, 0, node.x, node.y, halo)
  const coreAlpha = dimmed ? 0.06 : isConnected ? 0.58 : 0.14
  const outerAlpha = dimmed ? 0.025 : isConnected ? 0.18 : 0.04
  gradient.addColorStop(0, `${node.glowColor}${coreAlpha})`)
  gradient.addColorStop(0.35, `${node.glowColor}${outerAlpha})`)
  gradient.addColorStop(1, `${node.glowColor}0)`)
  ctx.beginPath()
  ctx.arc(node.x, node.y, halo, 0, Math.PI * 2)
  ctx.fillStyle = gradient
  ctx.fill()

  // ── 赛博朋克"数据环": 围绕重要节点的虚线旋转环 ──
  if (!dimmed && isConnected && (node.importance >= 7 || node.role === 'center')) {
    const ringRadius = radius * 2.8
    const segments = node.role === 'center' ? 16 : 10
    const segmentLen = (Math.PI * 2) / segments
    const rot = time * 0.0008
    ctx.save()
    ctx.translate(node.x, node.y)
    ctx.rotate(rot)
    ctx.lineWidth = 0.6
    ctx.strokeStyle = node.role === 'center'
      ? `rgba(255,255,255,0.22)`
      : `${node.glowColor}0.18)`
    ctx.setLineDash([segmentLen * 0.5, segmentLen * 0.5])
    ctx.beginPath()
    ctx.arc(0, 0, ringRadius, 0, Math.PI * 2)
    ctx.stroke()
    ctx.setLineDash([])
    ctx.restore()

    // 反向慢旋第二圈
    if (node.role === 'center' || node.importance >= 9) {
      const ring2 = radius * 3.6
      ctx.save()
      ctx.translate(node.x, node.y)
      ctx.rotate(-time * 0.0005)
      ctx.lineWidth = 0.45
      ctx.strokeStyle = `${node.glowColor}0.12)`
      ctx.setLineDash([segmentLen * 0.3, segmentLen * 0.7])
      ctx.beginPath()
      ctx.arc(0, 0, ring2, 0, Math.PI * 2)
      ctx.stroke()
      ctx.setLineDash([])
      ctx.restore()
    }
  }
}

function drawCore(
  ctx: CanvasRenderingContext2D,
  node: PositionedNode,
  radius: number,
  dimmed: boolean,
  isConnected: boolean,
  time: number,
): void {
  // ── 赛博朋克节点核心: 偏移高光 + 微故障闪烁 ──
  const glitchOffset = isConnected && node.importance >= 8
    ? Math.sin(time * 0.008 + node.phase * 3) > 0.97 ? (Math.random() - 0.5) * 2.5 : 0
    : 0

  const gradient = ctx.createRadialGradient(
    node.x - radius * 0.28 + glitchOffset,
    node.y - radius * 0.28,
    0,
    node.x,
    node.y,
    radius,
  )
  gradient.addColorStop(0, isConnected ? '#ffffff' : 'rgba(255,255,255,0.72)')
  gradient.addColorStop(0.28, node.color)
  gradient.addColorStop(1, `${node.glowColor}${isConnected ? '0.42)' : '0.16)'}`)

  ctx.globalAlpha = dimmed ? 0.22 : isConnected ? 1 : 0.4
  ctx.beginPath()
  ctx.arc(node.x, node.y, isConnected ? radius : radius * 0.82, 0, Math.PI * 2)
  ctx.fillStyle = gradient
  ctx.fill()

  // ── 节点外圈锐利描边 (赛博朋克硬边风格) ──
  if (!dimmed && isConnected) {
    ctx.beginPath()
    ctx.arc(node.x, node.y, radius + 0.5, 0, Math.PI * 2)
    ctx.strokeStyle = `${node.glowColor}0.35)`
    ctx.lineWidth = 0.8
    ctx.stroke()
  }

  // ── 赛博故障色偏移 (RGB split) ──
  if (!dimmed && isConnected && node.importance >= 7 && glitchOffset !== 0) {
    ctx.globalAlpha = 0.18
    ctx.beginPath()
    ctx.arc(node.x + 2, node.y, radius * 0.9, 0, Math.PI * 2)
    ctx.fillStyle = 'rgba(255,0,0,0.25)'
    ctx.fill()
    ctx.beginPath()
    ctx.arc(node.x - 2, node.y, radius * 0.9, 0, Math.PI * 2)
    ctx.fillStyle = 'rgba(0,255,255,0.25)'
    ctx.fill()
  }

  ctx.globalAlpha = 1
}

function drawOrbit(
  ctx: CanvasRenderingContext2D,
  node: PositionedNode,
  radius: number,
  time: number,
  prominent: boolean,
): void {
  const orbitCount = prominent ? 2 : 1
  for (let i = 0; i < orbitCount; i++) {
    ctx.save()
    ctx.translate(node.x, node.y)
    ctx.rotate(time * (0.00045 + i * 0.00012) + node.phase + i)
    ctx.beginPath()
    ctx.ellipse(0, 0, radius * (2.0 + i * 0.62), radius * (0.55 + i * 0.08), 0, 0, Math.PI * 2)
    ctx.strokeStyle = `${node.glowColor}${prominent ? '0.38)' : '0.16)'}`
    ctx.lineWidth = prominent ? 0.9 : 0.55
    ctx.stroke()
    ctx.restore()
  }
}

function drawLabel(
  ctx: CanvasRenderingContext2D,
  node: PositionedNode,
  radius: number,
  isHover: boolean,
  dimmed: boolean,
  isConnected: boolean,
): void {
  const isMajor = node.role === 'center' || node.importance >= 8 || isHover
  if (!shouldShowStarlinkLabel({ mode: props.mode, node, isHover })) return

  ctx.font = `${isMajor ? 700 : 600} ${isHover ? 13 : isMajor ? 11 : 9}px "Noto Serif SC", "KaiTi", serif`
  ctx.textAlign = 'center'
  ctx.textBaseline = 'top'
  ctx.lineWidth = 3
  ctx.strokeStyle = 'rgba(1,3,9,0.92)'
  ctx.fillStyle = isHover || node.role === 'center' ? '#ffffff' : node.color
  ctx.globalAlpha = dimmed ? 0.16 : isConnected ? (isMajor ? 0.9 : 0.56) : 0.24
  const label = nodeLabel(node)
  ctx.strokeText(label, node.x, node.y + radius + 6)
  ctx.fillText(label, node.x, node.y + radius + 6)
  ctx.globalAlpha = 1
}

function edgeColor(role: string, strength: number): string {
  // 默认低透明度 — 让边线作为背景纹理存在, hover 时再凸显
  const alpha = 0.06 + strength * 0.16
  if (role === 'cause') return `rgba(134,255,232,${alpha})`
  if (role === 'consequence') return `rgba(255,109,182,${alpha})`
  if (role === 'concept') return `rgba(240,200,75,${alpha * 0.7})`
  return `rgba(255,255,255,${alpha * 0.55})`
}

function rgba(hex: string, alpha: number): string {
  const clean = hex.replace('#', '')
  const r = parseInt(clean.slice(0, 2), 16)
  const g = parseInt(clean.slice(2, 4), 16)
  const b = parseInt(clean.slice(4, 6), 16)
  return `rgba(${r},${g},${b},${alpha.toFixed(3)})`
}

function hitTest(x: number, y: number): PositionedNode | null {
  for (let i = nodes.length - 1; i >= 0; i--) {
    const node = nodes[i]
    const radius = Math.max(12, node.radius + 8)
    const dx = x - node.x
    const dy = y - node.y
    if (dx * dx + dy * dy <= radius * radius) return node
  }
  return null
}

function onMouseMove(event: MouseEvent): void {
  const canvas = graphCanvasRef.value
  const container = containerRef.value
  if (!canvas || !container) return
  const rect = canvas.getBoundingClientRect()
  const node = hitTest(event.clientX - rect.left, event.clientY - rect.top)
  hoveredNode.value = node
  canvas.style.cursor = node?.kind === 'event' && node.role !== 'center' ? 'pointer' : 'default'
  if (!node) return
  const parentRect = container.getBoundingClientRect()
  tipX.value = Math.min(parentRect.width - 260, event.clientX - parentRect.left + 14)
  tipY.value = Math.max(12, event.clientY - parentRect.top - 12)
}

function onMouseLeave(): void {
  hoveredNode.value = null
  if (graphCanvasRef.value) graphCanvasRef.value.style.cursor = 'default'
}

function onClick(): void {
  const node = hoveredNode.value
  if (!node || node.kind !== 'event' || node.role === 'center') return
  emit('selectEvent', node.id)
}

function tipKicker(node: PositionedNode): string {
  if (node.role === 'center') return t('map.currentEvent')
  if (node.role === 'cause') return t('map.cause')
  if (node.role === 'consequence') return t('map.consequence')
  if (node.kind === 'concept') return t('map.concept')
  return node.region === 'china' ? t('map.chainChina') : t('map.chainWorld')
}

function nodeLabel(node: StarlinkGraphNode): string {
  if (node.kind === 'event') {
    return tf(`events.${node.id}.name`, node.label)
  }
  return node.label
}

function formatYear(year: number): string {
  return year < 0 ? t('map.bc', { n: Math.abs(year) }) : t('map.year', { n: year })
}

function animate(time: number): void {
  drawBackground(time)
  drawGraph(time)
  animationId = requestAnimationFrame(animate)
}

function resize(): void {
  const container = containerRef.value
  if (!container) return
  width = container.clientWidth
  height = container.clientHeight
  resetCanvases()
  layoutNodes()
}

watch(() => props.graph, () => {
  rebuildGraph()
}, { deep: true })

// Redraw all labels when locale changes (concept/event text may switch language)
watch(locale, () => {
  if (!graphCanvasRef.value) return
  const ctx = graphCanvasRef.value.getContext('2d')
  if (!ctx) return
  // Force a full redraw without rebuilding layout
  const time = performance.now()
  drawBackground(time)
  drawGraph(time)
})

onMounted(() => {
  resize()
  rebuildBackground()
  rebuildGraph()
  animationId = requestAnimationFrame(animate)
  window.addEventListener('resize', resize)
  if (containerRef.value) {
    resizeObserver = new ResizeObserver(resize)
    resizeObserver.observe(containerRef.value)
  }
})

onBeforeUnmount(() => {
  if (animationId !== null) cancelAnimationFrame(animationId)
  resizeObserver?.disconnect()
  window.removeEventListener('resize', resize)
})
</script>

<style scoped>
.constellation-map {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 360px;
  overflow: hidden;
  background:
    radial-gradient(circle at 50% 48%, rgba(255, 255, 255, 0.055), transparent 19%),
    radial-gradient(circle at 36% 44%, rgba(134, 255, 232, 0.05), transparent 26%),
    radial-gradient(circle at 68% 52%, rgba(255, 109, 182, 0.052), transparent 24%),
    linear-gradient(180deg, #01030a 0%, #030610 58%, #010208 100%);
  user-select: none;
}

/* 赛博朋克噪点纹理覆盖层 */
.constellation-map::after {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 2;
  pointer-events: none;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.04'/%3E%3C/svg%3E");
  opacity: 0.35;
  mix-blend-mode: overlay;
}

.constellation-map--detail {
  min-height: 360px;
  border: 1px solid rgba(134, 255, 232, 0.16);
  border-radius: 8px;
}

.map-layer {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.map-layer--bg {
  z-index: 0;
}

.map-layer--graph {
  z-index: 1;
}

.constellation-tip {
  position: absolute;
  z-index: 4;
  width: 240px;
  max-width: calc(100% - 24px);
  padding: 12px 14px;
  pointer-events: none;
  color: #eef8ff;
  background:
    linear-gradient(135deg, rgba(3, 7, 16, 0.94), rgba(3, 7, 16, 0.86)),
    radial-gradient(circle at 0% 0%, rgba(134, 255, 232, 0.06), transparent 50%);
  border: 1px solid rgba(134, 255, 232, 0.42);
  border-left: 2px solid rgba(134, 255, 232, 0.78);
  border-radius: 2px;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.55), 0 0 28px rgba(134, 255, 232, 0.12);
  backdrop-filter: blur(12px);
  clip-path: polygon(0 0, 100% 0, 100% calc(100% - 6px), calc(100% - 6px) 100%, 0 100%);
}

.tip-kicker {
  margin-bottom: 4px;
  color: #86ffe8;
  font-family: var(--font-mono, monospace);
  font-size: 10px;
  letter-spacing: 1px;
}

.tip-title {
  color: #ffffff;
  font-family: var(--font-serif, 'Noto Serif SC', serif);
  font-size: 14px;
  font-weight: 800;
}

.tip-year,
.tip-action {
  margin-top: 3px;
  color: rgba(238, 248, 255, 0.62);
  font-size: 11px;
}

.tip-desc {
  display: -webkit-box;
  margin-top: 6px;
  overflow: hidden;
  color: rgba(238, 248, 255, 0.72);
  font-size: 11px;
  line-height: 1.55;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
}

.tip-fade-enter-active,
.tip-fade-leave-active {
  transition: opacity 0.14s ease, transform 0.14s ease;
}

.tip-fade-enter-from,
.tip-fade-leave-to {
  opacity: 0;
  transform: translateY(4px);
}
</style>
