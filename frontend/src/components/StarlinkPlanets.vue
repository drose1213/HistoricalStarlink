<template>
  <div class="starlink-planets" ref="containerRef">
    <canvas ref="bgCanvasRef" class="layer-bg" />
    <canvas ref="graphCanvasRef" class="layer-graph" @mousemove="onMouseMove" @click="onClick" @mouseleave="onMouseLeave" />

    <Transition name="tooltip-fade">
      <div v-if="hoveredNode" class="hover-tip" :class="`hover-tip--${hoveredNode.role}`" :style="{ left: tipX + 'px', top: tipY + 'px' }">
        <div class="tip-header">
          <span class="tip-year">{{ formatYear(hoveredNode.year) }}</span>
          <span v-if="hoveredNode.weight != null" class="tip-weight">权重 {{ hoveredNode.weight }}/10</span>
        </div>
        <div class="tip-name">{{ hoveredNode.label }}</div>
        <div v-if="hoveredNode.description" class="tip-desc">{{ hoveredNode.description }}</div>
        <div v-if="hoveredNode.role === 'cause'" class="tip-hint tip-hint--cyan">◆ 历史原因 · 点击探索</div>
        <div v-else-if="hoveredNode.role === 'consequence'" class="tip-hint tip-hint--pink">◆ 历史影响 · 点击探索</div>
        <div v-else class="tip-hint">当前事件</div>
      </div>
    </Transition>

    <div class="starlink-legend">
      <div class="legend-item">
        <span class="legend-dot legend-dot--cyan"></span>
        <span>因果链路</span>
      </div>
      <div class="legend-item">
        <span class="legend-dot legend-dot--pink"></span>
        <span>影响链路</span>
      </div>
      <div class="legend-item">
        <span class="legend-dot legend-dot--gold"></span>
        <span>当前事件</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'

interface RelatedEvent {
  id: string
  name: string
  year: number
  region: string
  weight?: number
  description?: string
}

interface Props {
  eventId: string
  name: string
  year: number
  region: 'china' | 'foreign'
  importance: number
  causes?: RelatedEvent[]
  consequences?: RelatedEvent[]
}

const props = withDefaults(defineProps<Props>(), {
  causes: () => [],
  consequences: () => []
})

const emit = defineEmits<{
  (e: 'navigate', eventId: string): void
}>()

const containerRef = ref<HTMLDivElement>()
const bgCanvasRef = ref<HTMLCanvasElement>()
const graphCanvasRef = ref<HTMLCanvasElement>()

interface GNode {
  id: string
  label: string
  role: 'center' | 'cause' | 'consequence'
  year: number
  region: string
  weight: number
  description?: string
  x: number
  y: number
  radius: number
  color: string
  glowColor: string
}

interface GEdge {
  source: string
  target: string
  type: 'cause' | 'consequence'
  strength: number
}

const graphNodes: GNode[] = []
const graphEdges: GEdge[] = []
const edgeParticles: { t: number; edgeIdx: number; speed: number }[] = []
const graphNodeMap = new Map<string, GNode>()

let W = 0
let H = 0
let animId: number | null = null
let mouse = { x: -999, y: -999 }

const hoveredNode = ref<GNode | null>(null)
const tipX = ref(0)
const tipY = ref(0)

const BG_STARS: { x: number; y: number; r: number; o: number; s: number; p: number; c: string }[] = []

function runLayout(iterations: number) {
  const k = 0.01
  const repulsion = 2000
  const damping = 0.7
  const centerPull = 0.004
  const centerIdx = 0

  const vx = new Float64Array(graphNodes.length)
  const vy = new Float64Array(graphNodes.length)

  for (let iter = 0; iter < iterations; iter++) {
    const decay = 1 - iter / iterations

    for (let i = 1; i < graphNodes.length; i++) {
      const a = graphNodes[i]
      let fx = 0
      let fy = 0

      for (let j = 0; j < graphNodes.length; j++) {
        if (i === j) continue
        const b = graphNodes[j]
        const dx = a.x - b.x
        const dy = a.y - b.y
        const dist = Math.sqrt(dx * dx + dy * dy) + 0.1
        if (dist < 150) {
          const force = repulsion / (dist * dist)
          fx += (dx / dist) * force
          fy += (dy / dist) * force
        }
        const minDist = a.radius + b.radius + 25
        if (dist < minDist) {
          const pushForce = (minDist - dist) * 0.5
          fx += (dx / dist) * pushForce
          fy += (dy / dist) * pushForce
        }
      }

      for (const e of graphEdges) {
        let other: GNode | null = null
        if (e.source === a.id) other = graphNodeMap.get(e.target) || null
        else if (e.target === a.id) other = graphNodeMap.get(e.source) || null
        if (!other) continue
        const dx = other.x - a.x
        const dy = other.y - a.y
        const dist = Math.sqrt(dx * dx + dy * dy) + 0.1
        const idealDist = 150 + (1 - e.strength) * 60
        const force = (dist - idealDist) * k * e.strength
        fx += (dx / dist) * force
        fy += (dy / dist) * force
      }

      const center = graphNodes[centerIdx]
      fx += (center.x - a.x) * centerPull
      fy += (center.y - a.y) * centerPull

      vx[i] = (vx[i] + fx * decay) * damping
      vy[i] = (vy[i] + fy * decay) * damping
      a.x += vx[i]
      a.y += vy[i]

      a.x = Math.max(a.radius + 10, Math.min(W - a.radius - 10, a.x))
      a.y = Math.max(a.radius + 10, Math.min(H - a.radius - 10, a.y))
    }
  }
}

function initGraph() {
  graphNodes.length = 0
  graphEdges.length = 0
  edgeParticles.length = 0
  graphNodeMap.clear()

  const cx = W / 2
  const cy = H / 2

  const isChina = props.region === 'china'
  const mainR = 12 + ((props.importance - 2) / 8) * 8

  const centerNode: GNode = {
    id: props.eventId,
    label: props.name,
    role: 'center',
    year: props.year,
    region: props.region,
    weight: props.importance,
    x: cx,
    y: cy,
    radius: mainR,
    color: isChina ? '#31f7ff' : '#ff35f3',
    glowColor: isChina ? 'rgba(49,247,255,' : 'rgba(255,53,243,',
  }
  graphNodes.push(centerNode)
  graphNodeMap.set(centerNode.id, centerNode)

  const causeList = props.causes || []
  const causeCount = causeList.length
  causeList.forEach((ev, i) => {
    const angle = -Math.PI + (i / Math.max(causeCount, 1)) * Math.PI
    const dist = 180 + Math.random() * 50
    const regionIsChina = ev.region === 'china'
    const w = ev.weight ?? 5
    const node: GNode = {
      id: ev.id,
      label: ev.name,
      role: 'cause',
      year: ev.year,
      region: ev.region,
      weight: w,
      description: ev.description,
      x: cx + Math.cos(angle) * dist,
      y: cy + Math.sin(angle) * dist,
      radius: 7 + (w / 10) * 5,
      color: regionIsChina ? '#31f7ff' : '#ff35f3',
      glowColor: regionIsChina ? 'rgba(49,247,255,' : 'rgba(255,53,243,',
    }
    graphNodes.push(node)
    graphNodeMap.set(node.id, node)
    graphEdges.push({ source: ev.id, target: props.eventId, type: 'cause', strength: 0.6 + (w / 10) * 0.4 })
  })

  const consList = props.consequences || []
  const consCount = consList.length
  consList.forEach((ev, i) => {
    const angle = (i / Math.max(consCount, 1)) * Math.PI
    const dist = 180 + Math.random() * 50
    const regionIsChina = ev.region === 'china'
    const w = ev.weight ?? 5
    const node: GNode = {
      id: ev.id,
      label: ev.name,
      role: 'consequence',
      year: ev.year,
      region: ev.region,
      weight: w,
      description: ev.description,
      x: cx + Math.cos(angle) * dist,
      y: cy + Math.sin(angle) * dist,
      radius: 7 + (w / 10) * 5,
      color: regionIsChina ? '#31f7ff' : '#ff35f3',
      glowColor: regionIsChina ? 'rgba(49,247,255,' : 'rgba(255,53,243,',
    }
    graphNodes.push(node)
    graphNodeMap.set(node.id, node)
    graphEdges.push({ source: props.eventId, target: ev.id, type: 'consequence', strength: 0.6 + (w / 10) * 0.4 })
  })

  runLayout(200)

  const totalEdges = graphEdges.length
  if (totalEdges === 0) return
  const particleCount = Math.min(totalEdges * 5, 30)
  for (let i = 0; i < particleCount; i++) {
    edgeParticles.push({
      t: Math.random(), edgeIdx: i % totalEdges, speed: 0.003 + Math.random() * 0.005,
    })
  }
}

function initBgStars() {
  BG_STARS.length = 0
  const colors = ['rgba(49,247,255,A)', 'rgba(255,53,243,A)', 'rgba(255,255,255,A)', 'rgba(212,168,75,A)']
  for (let i = 0; i < 200; i++) {
    const c = colors[Math.floor(Math.random() * colors.length)]
    BG_STARS.push({
      x: Math.random(), y: Math.random(),
      r: 0.4 + Math.random() * 1.5,
      o: 0.15 + Math.random() * 0.45,
      s: 0.00003 + Math.random() * 0.00015,
      p: Math.random() * Math.PI * 2,
      c,
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
    const opacity = s.o * (0.5 + flicker * 0.5)
    const cx = ((s.x + time * s.s * 0.0003) % 1.001) * W
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

  for (const e of graphEdges) {
    const a = graphNodeMap.get(e.source)
    const b = graphNodeMap.get(e.target)
    if (!a || !b) continue

    const isCause = e.type === 'cause'

    ctx.beginPath()
    ctx.moveTo(a.x, a.y)
    ctx.lineTo(b.x, b.y)
    ctx.strokeStyle = isCause ? 'rgba(49,247,255,0.3)' : 'rgba(255,53,243,0.3)'
    ctx.lineWidth = 1.2
    ctx.stroke()
  }

  for (const p of edgeParticles) {
    p.t += p.speed
    if (p.t >= 1) { p.t -= 1; p.edgeIdx = p.edgeIdx % graphEdges.length }
    const e = graphEdges[p.edgeIdx]
    const a = graphNodeMap.get(e.source)
    const b = graphNodeMap.get(e.target)
    if (!a || !b) continue
    const isCause = e.type === 'cause'
    const px = a.x + (b.x - a.x) * p.t
    const py = a.y + (b.y - a.y) * p.t
    ctx.beginPath()
    ctx.arc(px, py, 1.2, 0, Math.PI * 2)
    ctx.fillStyle = isCause ? 'rgba(49,247,255,0.6)' : 'rgba(255,53,243,0.5)'
    ctx.fill()
  }

  for (const node of graphNodes) {
    const isHover = hoveredNode.value?.id === node.id
    const baseR = node.radius
    const drawR = isHover ? baseR * 1.25 : baseR

    const grad = ctx.createRadialGradient(node.x, node.y, 0, node.x, node.y, drawR * 3)
    grad.addColorStop(0, node.glowColor + '0.4)')
    grad.addColorStop(0.5, node.glowColor + '0.1)')
    grad.addColorStop(1, node.glowColor + '0)')
    ctx.beginPath()
    ctx.arc(node.x, node.y, drawR * 3, 0, Math.PI * 2)
    ctx.fillStyle = grad
    ctx.fill()

    ctx.beginPath()
    ctx.arc(node.x, node.y, drawR, 0, Math.PI * 2)
    const coreGrad = ctx.createRadialGradient(node.x, node.y, 0, node.x, node.y, drawR)
    coreGrad.addColorStop(0, '#ffffff')
    coreGrad.addColorStop(0.3, node.color)
    coreGrad.addColorStop(1, node.glowColor + '0.3)')
    ctx.fillStyle = coreGrad
    ctx.fill()

    if (node.role === 'center') {
      ctx.beginPath()
      ctx.arc(node.x, node.y, drawR + 5, 0, Math.PI * 2)
      ctx.strokeStyle = node.color
      ctx.lineWidth = 1.5
      ctx.globalAlpha = 0.3 + Math.sin(time * 0.003) * 0.2
      ctx.stroke()
      ctx.globalAlpha = 1
    }

    if (isHover && node.role !== 'center') {
      ctx.beginPath()
      ctx.arc(node.x, node.y, drawR + 3, 0, Math.PI * 2)
      ctx.strokeStyle = node.role === 'cause' ? '#31f7ff' : '#ff35f3'
      ctx.lineWidth = 1.2
      ctx.globalAlpha = 0.5 + Math.sin(time * 0.004) * 0.3
      ctx.stroke()
      ctx.globalAlpha = 1
    }

    const isCenter = node.role === 'center'

    if (isCenter || node.role === 'cause' || node.role === 'consequence') {
      const ringCount = isCenter ? 3 : 2
      for (let r = 1; r <= ringCount; r++) {
        const orbitRx = drawR * (1.4 + r * 0.6)
        const orbitRy = orbitRx * (0.3 + r * 0.05)
        const rotSpeed = isCenter ? 0.0005 : 0.0008
        const rot = time * rotSpeed * (r % 2 === 0 ? 1 : -1) + r * 1.2
        ctx.save()
        ctx.translate(node.x, node.y)
        ctx.rotate(rot)
        ctx.beginPath()
        ctx.ellipse(0, 0, orbitRx, orbitRy, 0, 0, Math.PI * 2)
        ctx.strokeStyle = node.glowColor + (isCenter ? '0.2)' : '0.15)')
        ctx.lineWidth = isCenter ? 1 : 0.7
        ctx.stroke()
        if (isCenter) {
          const dotAngle = time * 0.002 * (r % 2 === 0 ? 1 : -1)
          const dotX = Math.cos(dotAngle) * orbitRx
          const dotY = Math.sin(dotAngle) * orbitRy
          ctx.beginPath()
          ctx.arc(dotX, dotY, 1.8, 0, Math.PI * 2)
          ctx.fillStyle = node.glowColor + '0.7)'
          ctx.fill()
        }
        ctx.restore()
      }
    }

    ctx.font = isCenter
      ? `700 ${isHover ? 14 : 12}px "Noto Serif SC", serif`
      : `600 ${isHover ? 12 : 10}px "Noto Serif SC", serif`
    ctx.textAlign = 'center'
    ctx.textBaseline = 'top'
    ctx.fillStyle = isHover ? '#ffffff' : (isCenter ? node.color : 'rgba(255,255,255,0.55)')
    ctx.globalAlpha = isHover ? 1 : (isCenter ? 0.9 : 0.65)
    ctx.fillText(node.label, node.x, node.y + drawR + 5)
    ctx.globalAlpha = 1
  }
}

function animate(time: number) {
  drawBg(time)
  drawGraph(time)
  animId = requestAnimationFrame(animate)
}

function hitTest(mx: number, my: number): GNode | null {
  for (let i = graphNodes.length - 1; i >= 0; i--) {
    const n = graphNodes[i]
    const dx = mx - n.x
    const dy = my - n.y
    if (dx * dx + dy * dy < (n.radius + 8) * (n.radius + 8)) return n
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
    canvas.style.cursor = (hit.role === 'cause' || hit.role === 'consequence') ? 'pointer' : 'default'
  } else {
    canvas.style.cursor = 'default'
  }
}

function onMouseLeave() {
  mouse.x = -999
  mouse.y = -999
  hoveredNode.value = null
}

function onClick() {
  if (hoveredNode.value && (hoveredNode.value.role === 'cause' || hoveredNode.value.role === 'consequence')) {
    emit('navigate', hoveredNode.value.id)
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
    if (cv) {
      const dpr = window.devicePixelRatio || 1
      cv.width = W * dpr
      cv.height = H * dpr
      cv.style.width = W + 'px'
      cv.style.height = H + 'px'
      const ctx = cv.getContext('2d')
      if (ctx) ctx.scale(dpr, dpr)
    }
  }
  if (graphNodes.length === 0) {
    initGraph()
  }
}

watch(() => [props.eventId, props.causes, props.consequences], () => {
  if (W > 0 && H > 0) {
    initGraph()
  }
})

onMounted(() => {
  initBgStars()
  onResize()
  animId = requestAnimationFrame(animate)
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  if (animId !== null) cancelAnimationFrame(animId)
  window.removeEventListener('resize', onResize)
})
</script>

<style scoped>
.starlink-planets {
  position: relative;
  width: 100%;
  aspect-ratio: 900 / 480;
  min-height: 320px;
  background:
    radial-gradient(ellipse at 35% 48%, rgba(49, 247, 255, 0.05), transparent 50%),
    radial-gradient(ellipse at 75% 48%, rgba(255, 53, 243, 0.04), transparent 50%),
    linear-gradient(180deg, #05070d, #081525 50%, #05070d);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-subtle);
  overflow: hidden;
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
  background: rgba(10, 18, 32, 0.92);
  border: 1px solid rgba(49, 247, 255, 0.3);
  border-radius: 8px;
  padding: 10px 14px;
  pointer-events: none;
  backdrop-filter: blur(10px);
  box-shadow: 0 0 20px rgba(49, 247, 255, 0.12);
  max-width: 220px;
}

.hover-tip--cause {
  border-color: rgba(49, 247, 255, 0.35);
}

.hover-tip--consequence {
  border-color: rgba(255, 53, 243, 0.35);
}

.tip-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.tip-year {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
}

.tip-weight {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--accent-gold);
}

.tip-name {
  font-family: 'Noto Serif SC', serif;
  font-size: 14px;
  font-weight: 700;
  color: #ffffff;
  margin-bottom: 4px;
}

.tip-desc {
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.6;
  max-height: 80px;
  overflow-y: auto;
}

.tip-hint {
  font-size: 10px;
  color: var(--text-muted);
  margin-top: 4px;
}

.tip-hint--cyan {
  color: rgba(49, 247, 255, 0.6);
}

.tip-hint--pink {
  color: rgba(255, 53, 243, 0.6);
}

.tooltip-fade-enter-active { transition: all 0.15s ease; }
.tooltip-fade-leave-active { transition: all 0.1s ease; }
.tooltip-fade-enter-from, .tooltip-fade-leave-to { opacity: 0; transform: translateY(4px); }

.starlink-legend {
  position: absolute;
  bottom: 12px;
  right: 16px;
  display: flex;
  gap: 16px;
  z-index: 10;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--text-muted);
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.legend-dot--cyan {
  background: var(--cyan-core);
  box-shadow: 0 0 8px var(--cyan-core);
}

.legend-dot--pink {
  background: var(--pink-core);
  box-shadow: 0 0 8px var(--pink-core);
}

.legend-dot--gold {
  background: var(--accent-gold);
  box-shadow: 0 0 8px var(--accent-gold);
}
</style>
