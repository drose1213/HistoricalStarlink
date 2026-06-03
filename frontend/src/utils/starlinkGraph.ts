import type { HistoryEvent } from '@/types'

export type StarlinkNodeKind = 'event' | 'concept'
export type StarlinkNodeRole = 'center' | 'cause' | 'consequence' | 'context' | 'concept'
export type StarlinkEdgeRole = 'cause' | 'consequence' | 'concept' | 'related'

export interface StarlinkGraphNode {
  id: string
  label: string
  kind: StarlinkNodeKind
  role: StarlinkNodeRole
  year?: number
  region?: 'china' | 'foreign'
  importance: number
  description?: string
  color: string
  glowColor: string
  radius: number
}

export interface StarlinkGraphEdge {
  source: string
  target: string
  role: StarlinkEdgeRole
  strength: number
}

export interface StarlinkGraph {
  nodes: StarlinkGraphNode[]
  edges: StarlinkGraphEdge[]
}

const CHINA_COLOR = '#86ffe8'
const FOREIGN_COLOR = '#ff6db6'
const CONCEPT_COLORS = ['#ffffff', '#f0c84b', '#79d8ff', '#8fffba', '#bfa8ff']

function eventColor(region: HistoryEvent['region']): { color: string; glowColor: string } {
  if (region === 'china') {
    return { color: CHINA_COLOR, glowColor: 'rgba(134,255,232,' }
  }
  return { color: FOREIGN_COLOR, glowColor: 'rgba(255,109,182,' }
}

function conceptNodeId(label: string): string {
  return `concept_${label.trim().replace(/\s+/g, '_')}`
}

function addNode(nodes: Map<string, StarlinkGraphNode>, node: StarlinkGraphNode): void {
  if (!nodes.has(node.id)) {
    nodes.set(node.id, node)
  }
}

function addEdge(
  edges: Map<string, StarlinkGraphEdge>,
  edge: StarlinkGraphEdge,
): void {
  if (edge.source === edge.target) return
  const key = `${edge.source}->${edge.target}:${edge.role}`
  if (!edges.has(key)) {
    edges.set(key, edge)
  }
}

function toEventNode(event: HistoryEvent, role: StarlinkNodeRole): StarlinkGraphNode {
  const color = eventColor(event.region)
  return {
    id: event.id,
    label: event.name,
    kind: 'event',
    role,
    year: event.year,
    region: event.region,
    importance: event.importance,
    description: event.description,
    color: color.color,
    glowColor: color.glowColor,
    radius: Math.max(6, Math.min(22, 6 + event.importance * 1.4)),
  }
}

function toConceptNode(label: string, index: number): StarlinkGraphNode {
  const color = CONCEPT_COLORS[index % CONCEPT_COLORS.length]
  return {
    id: conceptNodeId(label),
    label,
    kind: 'concept',
    role: 'concept',
    importance: 4,
    color,
    glowColor: color === '#ffffff' ? 'rgba(255,255,255,' : `${hexToRgbaPrefix(color)}`,
    radius: 4.8,
  }
}

function hexToRgbaPrefix(hex: string): string {
  const clean = hex.replace('#', '')
  const r = parseInt(clean.slice(0, 2), 16)
  const g = parseInt(clean.slice(2, 4), 16)
  const b = parseInt(clean.slice(4, 6), 16)
  return `rgba(${r},${g},${b},`
}

function eventMap(events: HistoryEvent[]): Map<string, HistoryEvent> {
  return new Map(events.map(event => [event.id, event]))
}

function addEventRelations(
  source: HistoryEvent,
  eventsById: Map<string, HistoryEvent>,
  nodes: Map<string, StarlinkGraphNode>,
  edges: Map<string, StarlinkGraphEdge>,
): void {
  for (const rel of source.related?.causes || []) {
    const cause = eventsById.get(rel.id)
    if (!cause) continue
    addNode(nodes, toEventNode(cause, 'context'))
    addEdge(edges, {
      source: cause.id,
      target: source.id,
      role: 'cause',
      strength: Math.max(0.25, Math.min(1, rel.weight / 10)),
    })
  }

  for (const rel of source.related?.consequences || []) {
    const consequence = eventsById.get(rel.id)
    if (!consequence) continue
    addNode(nodes, toEventNode(consequence, 'context'))
    addEdge(edges, {
      source: source.id,
      target: consequence.id,
      role: 'consequence',
      strength: Math.max(0.25, Math.min(1, rel.weight / 10)),
    })
  }
}

function addConcepts(
  event: HistoryEvent,
  nodes: Map<string, StarlinkGraphNode>,
  edges: Map<string, StarlinkGraphEdge>,
): void {
  const concepts = event.related_concepts || event.tags || []
  concepts.slice(0, 4).forEach((label, index) => {
    const trimmed = label.trim()
    if (!trimmed) return
    const concept = toConceptNode(trimmed, index)
    addNode(nodes, concept)
    addEdge(edges, {
      source: event.id,
      target: concept.id,
      role: 'concept',
      strength: 0.32,
    })
  })
}

export function buildHomeStarlinkGraph(events: HistoryEvent[]): StarlinkGraph {
  const nodes = new Map<string, StarlinkGraphNode>()
  const edges = new Map<string, StarlinkGraphEdge>()
  const eventsById = eventMap(events)

  for (const event of events) {
    addNode(nodes, toEventNode(event, 'context'))
  }

  for (const event of events) {
    addEventRelations(event, eventsById, nodes, edges)
    addConcepts(event, nodes, edges)
  }

  return {
    nodes: [...nodes.values()],
    edges: [...edges.values()],
  }
}

export function buildDetailStarlinkGraph(eventId: string, events: HistoryEvent[]): StarlinkGraph {
  const nodes = new Map<string, StarlinkGraphNode>()
  const edges = new Map<string, StarlinkGraphEdge>()
  const eventsById = eventMap(events)
  const current = eventsById.get(eventId)
  if (!current) return { nodes: [], edges: [] }

  addNode(nodes, toEventNode(current, 'center'))

  for (const rel of current.related?.causes || []) {
    const cause = eventsById.get(rel.id)
    if (!cause) continue
    addNode(nodes, toEventNode(cause, 'cause'))
    addEdge(edges, {
      source: cause.id,
      target: current.id,
      role: 'cause',
      strength: Math.max(0.25, Math.min(1, rel.weight / 10)),
    })
  }

  for (const rel of current.related?.consequences || []) {
    const consequence = eventsById.get(rel.id)
    if (!consequence) continue
    addNode(nodes, toEventNode(consequence, 'consequence'))
    addEdge(edges, {
      source: current.id,
      target: consequence.id,
      role: 'consequence',
      strength: Math.max(0.25, Math.min(1, rel.weight / 10)),
    })
  }

  addConcepts(current, nodes, edges)

  return {
    nodes: [...nodes.values()],
    edges: [...edges.values()],
  }
}
