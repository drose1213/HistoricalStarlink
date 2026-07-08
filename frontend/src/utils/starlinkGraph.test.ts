import { describe, expect, it } from 'vitest'
import { buildDetailStarlinkGraph, buildHomeStarlinkGraph, shouldShowStarlinkLabel } from './starlinkGraph'
import type { HistoryEvent } from '@/types'

const baseEvents: HistoryEvent[] = [
  {
    id: 'origin',
    name: '起源事件',
    year: 100,
    region: 'china',
    importance: 9,
    description: '中心事件',
    causes: [],
    consequences: [],
    related_concepts: ['制度', '改革'],
    figures: ['甲'],
    tags: ['制度'],
    related: {
      causes: [{ id: 'cause', weight: 8 }],
      consequences: [{ id: 'effect', weight: 7 }],
    },
  },
  {
    id: 'cause',
    name: '原因事件',
    year: 80,
    region: 'china',
    importance: 7,
    description: '原因',
    causes: [],
    consequences: [],
    related_concepts: ['制度'],
    figures: ['乙'],
    tags: ['制度'],
  },
  {
    id: 'effect',
    name: '影响事件',
    year: 130,
    region: 'foreign',
    importance: 6,
    description: '影响',
    causes: [],
    consequences: [],
    related_concepts: ['贸易'],
    figures: ['丙'],
    tags: ['贸易'],
  },
  {
    id: 'distant',
    name: '远端事件',
    year: 900,
    region: 'foreign',
    importance: 5,
    description: '不属于详情一跳关系',
    causes: [],
    consequences: [],
    related_concepts: ['技术'],
    figures: ['丁'],
    tags: ['技术'],
  },
]

describe('starlink graph builders', () => {
  it('builds a homepage graph with event nodes, concept nodes, and relation edges', () => {
    const graph = buildHomeStarlinkGraph(baseEvents)

    expect(graph.nodes.some(node => node.id === 'origin' && node.kind === 'event')).toBe(true)
    expect(graph.nodes.some(node => node.id === 'concept_制度' && node.kind === 'concept')).toBe(true)
    expect(graph.edges.some(edge => edge.source === 'cause' && edge.target === 'origin')).toBe(true)
    expect(graph.edges.some(edge => edge.source === 'origin' && edge.target === 'effect')).toBe(true)
    expect(graph.edges.some(edge => edge.source === 'origin' && edge.target === 'concept_制度')).toBe(true)
  })

  it('builds a detail graph limited to the current event and direct associations', () => {
    const graph = buildDetailStarlinkGraph('origin', baseEvents)
    const ids = new Set(graph.nodes.map(node => node.id))

    expect(ids.has('origin')).toBe(true)
    expect(ids.has('cause')).toBe(true)
    expect(ids.has('effect')).toBe(true)
    expect(ids.has('concept_制度')).toBe(true)
    expect(ids.has('concept_改革')).toBe(true)
    expect(ids.has('distant')).toBe(false)
    expect(graph.nodes.find(node => node.id === 'origin')?.role).toBe('center')
    expect(graph.edges.every(edge => edge.source === 'origin' || edge.target === 'origin')).toBe(true)
  })

  it('caps dense homepage concept edges while preserving event relation edges', () => {
    const denseEvents: HistoryEvent[] = Array.from({ length: 20 }, (_, index) => ({
      id: `dense_${index}`,
      name: `Dense ${index}`,
      year: 1840 + index,
      region: index % 2 === 0 ? 'china' : 'foreign',
      importance: (index % 10) + 1,
      description: `Dense event ${index}`,
      causes: [],
      consequences: [],
      related_concepts: [
        `topic_${index}_0`,
        `topic_${index}_1`,
        `topic_${index}_2`,
        `topic_${index}_3`,
      ],
      figures: [],
      tags: [],
      related: {
        causes: index === 10 ? [{ id: 'dense_9', weight: 9 }] : [],
        consequences: index === 10 ? [{ id: 'dense_11', weight: 8 }] : [],
      },
    }))

    const graph = buildHomeStarlinkGraph(denseEvents)
    const conceptEdges = graph.edges.filter(edge => edge.role === 'concept')
    const relationEdges = graph.edges.filter(edge => edge.role === 'cause' || edge.role === 'consequence')

    expect(graph.nodes.some(node => node.id === 'concept_topic_0_0')).toBe(true)
    expect(conceptEdges.length).toBeLessThan(80)
    expect(conceptEdges.length).toBeLessThanOrEqual(36)
    expect(relationEdges.some(edge => edge.source === 'dense_9' && edge.target === 'dense_10')).toBe(true)
    expect(relationEdges.some(edge => edge.source === 'dense_10' && edge.target === 'dense_11')).toBe(true)
  })

  it('hides homepage concept labels until hover while keeping important event labels visible', () => {
    const graph = buildHomeStarlinkGraph(baseEvents)
    const concept = graph.nodes.find(node => node.kind === 'concept')
    const importantEvent = graph.nodes.find(node => node.id === 'origin')

    expect(concept).toBeDefined()
    expect(importantEvent).toBeDefined()
    expect(shouldShowStarlinkLabel({ mode: 'home', node: concept!, isHover: false })).toBe(false)
    expect(shouldShowStarlinkLabel({ mode: 'home', node: concept!, isHover: true })).toBe(true)
    expect(shouldShowStarlinkLabel({ mode: 'home', node: importantEvent!, isHover: false })).toBe(true)
  })

  it('adds readable related-event notes to homepage concept nodes', () => {
    const events: HistoryEvent[] = [
      {
        id: 'alpha',
        name: 'Alpha Event',
        year: 100,
        region: 'china',
        importance: 8,
        description: 'Alpha description',
        causes: [],
        consequences: [],
        related_concepts: ['Shared Idea'],
        figures: [],
        tags: [],
      },
      {
        id: 'beta',
        name: 'Beta Event',
        year: 200,
        region: 'foreign',
        importance: 7,
        description: 'Beta description',
        causes: [],
        consequences: [],
        related_concepts: ['Shared Idea'],
        figures: [],
        tags: [],
      },
    ]

    const graph = buildHomeStarlinkGraph(events)
    const concept = graph.nodes.find(node => node.id === 'concept_Shared_Idea')

    expect(concept?.description).toBe('关联事件：Alpha Event、Beta Event')
  })
})
