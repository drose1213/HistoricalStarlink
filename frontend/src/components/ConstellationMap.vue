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
        <div class="tip-title">{{ hoveredNode.label }}</div>
        <div v-if="hoveredNode.year" class="tip-year">{{ formatYear(hoveredNode.year) }}</div>
        <div v-if="hoveredNode.description" class="tip-desc">{{ hoveredNode.description }}</div>
        <div v-if="hoveredNode.kind === 'event' && hoveredNode.role !== 'center'" class="tip-action">点击进入事件详情</div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { StarlinkGraph, StarlinkGraphNode } from '@/utils/starlinkGraph'

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

  layoutNodes()

  const particleCount = Math.min(90, Math.max(12, props.graph.edges.length * 2))
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
  const cx = width * 0.52
  const cy = height * 0.5
  const maxRadius = Math.min(width, height) * 0.47
  const sorted = [...nodes].sort((a, b) => b.importance - a.importance)

  sorted.forEach((node, index) => {
    if (node.kind === 'concept') {
      const angle = (index / Math.max(sorted.length, 1)) * Math.PI * 2 + node.phase
      const radius = maxRadius * (0.45 + ((hash(node.id) % 100) / 100) * 0.48)
      node.tx = cx + Math.cos(angle) * radius
      node.ty = cy + Math.sin(angle) * radius
      return
    }

    const rank = index + 1
    const angle = rank * 2.399963 + node.phase * 0.18
    const band = Math.sqrt(rank / Math.max(sorted.length, 1))
    const radius = maxRadius * (0.08 + band * 0.92)
    const regionBias = node.region === 'china' ? -width * 0.1 : width * 0.1
    node.tx = cx + regionBias * (1 - band) + Math.cos(angle) * radius
    node.ty = cy + Math.sin(angle) * radius * 0.86
  })

  clampTargets()
}

function layoutDetailNodes(): void {
  const cx = width / 2
  const cy = height / 2
  const radius = Math.min(width, height) * 0.34
  const causes = nodes.filter(node => node.role === 'cause')
  const consequences = nodes.filter(node => node.role === 'consequence')
  const concepts = nodes.filter(node => node.kind === 'concept')

  for (const node of nodes) {
    if (node.role === 'center') {
      node.tx = cx
      node.ty = cy
    }
  }

  causes.forEach((node, index) => {
    const angle = -Math.PI * 0.88 + (index / Math.max(causes.length - 1, 1)) * Math.PI * 0.76
    node.tx = cx + Math.cos(angle) * radius
    node.ty = cy + Math.sin(angle) * radius * 0.82
  })

  consequences.forEach((node, index) => {
    const angle = Math.PI * 0.12 + (index / Math.max(consequences.length - 1, 1)) * Math.PI * 0.76
    node.tx = cx + Math.cos(angle) * radius
    node.ty = cy + Math.sin(angle) * radius * 0.82
  })

  concepts.forEach((node, index) => {
    const angle = -Math.PI / 2 + (index / Math.max(concepts.length, 1)) * Math.PI * 2
    node.tx = cx + Math.cos(angle) * radius * 0.62
    node.ty = cy + Math.sin(angle) * radius * 0.62
  })

  clampTargets()
}

function clampTargets(): void {
  for (const node of nodes) {
    const pad = Math.max(42, node.radius * 4)
    node.tx = Math.max(pad, Math.min(width - pad, node.tx))
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
  const core = ctx.createRadialGradient(width * 0.5, height * 0.52, 0, width * 0.5, height * 0.52, Math.max(width, height) * 0.72)
  core.addColorStop(0, props.mode === 'detail' ? 'rgba(255,109,182,0.10)' : 'rgba(255,255,255,0.055)')
  core.addColorStop(0.38, 'rgba(134,255,232,0.035)')
  core.addColorStop(1, 'rgba(1,3,9,0)')
  ctx.fillStyle = core
  ctx.fillRect(0, 0, width, height)

  for (const star of bgStars) {
    const flicker = 0.55 + Math.sin(time * star.s + star.phase) * 0.45
    const x = ((star.x + time * star.s * 0.00018) % 1.002) * width
    const y = star.y * height
    ctx.beginPath()
    ctx.arc(x, y, star.r, 0, Math.PI * 2)
    ctx.fillStyle = rgba(star.color, star.o * flicker)
    ctx.fill()
  }
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
  drawEdges(ctx, activeHover, focusIds)
  drawParticles(ctx)
  drawNodes(ctx, time, search, activeHover, focusIds)
}

function drawEdges(
  ctx: CanvasRenderingContext2D,
  activeHover: PositionedNode | null,
  focusIds: Set<string> | null,
): void {
  for (const edge of props.graph.edges) {
    const source = nodeMap.get(edge.source)
    const target = nodeMap.get(edge.target)
    if (!source || !target) continue
    const highlighted = activeHover ? source.id === activeHover.id || target.id === activeHover.id : false
    const dimmedByFocus = focusIds ? !(focusIds.has(source.id) && focusIds.has(target.id)) : false
    ctx.beginPath()
    ctx.moveTo(source.x, source.y)
    ctx.lineTo(target.x, target.y)
    ctx.strokeStyle = highlighted
      ? 'rgba(255,255,255,0.78)'
      : dimmedByFocus
        ? 'rgba(255,255,255,0.05)'
        : edgeColor(edge.role, edge.strength)
    ctx.lineWidth = highlighted ? 1.35 : dimmedByFocus ? 0.3 : 0.45 + edge.strength * 0.8
    ctx.stroke()
  }
}

function drawParticles(ctx: CanvasRenderingContext2D): void {
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
    ctx.beginPath()
    ctx.arc(x, y, props.mode === 'detail' ? 1.25 : 0.85, 0, Math.PI * 2)
    ctx.fillStyle = 'rgba(255,255,255,0.58)'
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
    const matchesSearch = search ? node.label.toLowerCase().includes(search) : true
    const dimmedBySearch = search.length > 0 && !matchesSearch
    const dimmedByFocus = focusIds ? !focusIds.has(node.id) : false
    const dimmed = dimmedBySearch || dimmedByFocus
    const isConnected = node.connectionCount > 0
    const radius = node.role === 'center' ? node.radius * 1.45 : node.radius
    const drawRadius = isHover ? radius * 1.34 : radius

    drawHalo(ctx, node, drawRadius, dimmed, isConnected)
    drawCore(ctx, node, drawRadius, dimmed, isConnected)

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
): void {
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
}

function drawCore(
  ctx: CanvasRenderingContext2D,
  node: PositionedNode,
  radius: number,
  dimmed: boolean,
  isConnected: boolean,
): void {
  const gradient = ctx.createRadialGradient(node.x - radius * 0.28, node.y - radius * 0.28, 0, node.x, node.y, radius)
  gradient.addColorStop(0, isConnected ? '#ffffff' : 'rgba(255,255,255,0.72)')
  gradient.addColorStop(0.28, node.color)
  gradient.addColorStop(1, `${node.glowColor}${isConnected ? '0.42)' : '0.16)'}`)
  ctx.globalAlpha = dimmed ? 0.22 : isConnected ? 1 : 0.4
  ctx.beginPath()
  ctx.arc(node.x, node.y, isConnected ? radius : radius * 0.82, 0, Math.PI * 2)
  ctx.fillStyle = gradient
  ctx.fill()
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
  const visible = props.mode === 'detail' || isMajor || node.kind === 'concept'
  if (!visible) return

  ctx.font = `${isMajor ? 700 : 600} ${isHover ? 13 : isMajor ? 11 : 9}px "Noto Serif SC", "KaiTi", serif`
  ctx.textAlign = 'center'
  ctx.textBaseline = 'top'
  ctx.lineWidth = 3
  ctx.strokeStyle = 'rgba(1,3,9,0.92)'
  ctx.fillStyle = isHover || node.role === 'center' ? '#ffffff' : node.color
  ctx.globalAlpha = dimmed ? 0.16 : isConnected ? (isMajor ? 0.9 : 0.56) : 0.24
  ctx.strokeText(node.label, node.x, node.y + radius + 6)
  ctx.fillText(node.label, node.x, node.y + radius + 6)
  ctx.globalAlpha = 1
}

function edgeColor(role: string, strength: number): string {
  const alpha = 0.1 + strength * 0.26
  if (role === 'cause') return `rgba(134,255,232,${alpha})`
  if (role === 'consequence') return `rgba(255,109,182,${alpha})`
  if (role === 'concept') return `rgba(240,200,75,${alpha * 0.72})`
  return `rgba(255,255,255,${alpha * 0.62})`
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
  if (node.role === 'center') return '当前事件'
  if (node.role === 'cause') return '历史原因'
  if (node.role === 'consequence') return '历史影响'
  if (node.kind === 'concept') return '关联概念'
  return node.region === 'china' ? '华夏星链' : '世界星链'
}

function formatYear(year: number): string {
  return year < 0 ? `公元前${Math.abs(year)}年` : `${year}年`
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
  padding: 10px 12px;
  pointer-events: none;
  color: #eef8ff;
  background: rgba(3, 7, 16, 0.9);
  border: 1px solid rgba(134, 255, 232, 0.34);
  border-radius: 6px;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.55), 0 0 28px rgba(134, 255, 232, 0.12);
  backdrop-filter: blur(10px);
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
