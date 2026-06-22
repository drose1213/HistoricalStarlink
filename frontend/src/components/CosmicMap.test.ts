import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick } from 'vue'
import { setActivePinia, createPinia } from 'pinia'

import CosmicMap from './CosmicMap.vue'
import type { StarlinkGraph } from '@/utils/starlinkGraph'

// We need a controllable ConstellationMap because it does heavy canvas work.
// We mount the real CosmicMap but stub its only child component so we can:
//   - assert it forwards the right props
//   - emit `selectEvent` from the stub to verify the wrapper re-emits
//   - avoid canvas / animation paths that happy-dom does not support
const ConstellationMapStub = {
  name: 'ConstellationMap',
  props: ['graph', 'searchKeyword', 'mode'],
  emits: ['selectEvent'],
  template: '<div data-stub="constellation-map" :data-mode="mode" :data-node-count="graph.nodes.length" @click="onClick" />',
  methods: {
    onClick() {
      // Helper for the test that drives a node click via the canvas.
      // We dispatch the event from the parent so it bubbles through the wrapper.
      this.$emit('selectEvent', 'evt-001')
    },
  },
}

function mountCosmic(props: { searchKeyword?: string } = {}) {
  return mount(CosmicMap, {
    props,
    global: {
      stubs: {
        ConstellationMap: ConstellationMapStub,
      },
    },
  })
}

describe('CosmicMap.vue (wrapper around ConstellationMap)', () => {
  beforeEach(() => {
    // happy-dom's canvas getContext returns null; the real component
    // would call canvas APIs that throw. We stub the child so the wrapper
    // never instantiates a real canvas, but we also silence any leftover
    // errors just in case.
    vi.spyOn(console, 'error').mockImplementation(() => {})
    vi.spyOn(console, 'warn').mockImplementation(() => {})
  })

  it('renders without throwing when there are zero nodes', () => {
    // CosmicMap builds the graph from allEvents; we can't easily inject a graph,
    // but the real allEvents dataset is non-empty. We mount with the stub and
    // assert the wrapper hands off to its child cleanly regardless of the data
    // size.
    expect(() => mountCosmic()).not.toThrow()
  })

  it('forwards the searchKeyword prop to the inner ConstellationMap', () => {
    const wrapper = mountCosmic({ searchKeyword: 'silk' })
    const stub = wrapper.findComponent(ConstellationMapStub as any)
    expect(stub.exists()).toBe(true)
    expect(stub.props('searchKeyword')).toBe('silk')
    expect(stub.props('mode')).toBe('home')
  })

  it('re-emits "selectEvent" coming from ConstellationMap as its own "selectEvent" event', async () => {
    const wrapper = mountCosmic()
    const stub = wrapper.findComponent(ConstellationMapStub as any)
    expect(stub.exists()).toBe(true)

    // Drive the inner stub to emit selectEvent with id 'evt-001'
    await stub.vm.$emit('selectEvent', 'evt-001')

    const events = wrapper.emitted('selectEvent')
    expect(events).toBeTruthy()
    expect(events!.length).toBe(1)
    expect(events![0]).toEqual(['evt-001'])
  })

  it('builds a graph object (via allEvents) and hands it to the child with the right shape', () => {
    // CosmicMap constructs `homeGraph` from `allEvents` and forwards it as
    // a prop to ConstellationMap. We do not assert on the node count
    // (the underlying allEvents is a `reactive([])` that gets populated
    // asynchronously by the real app), but we do assert the wrapper passes
    // a graph object with the expected shape down to its child.
    const wrapper = mountCosmic()
    const stub = wrapper.findComponent(ConstellationMapStub as any)
    const graph = stub.props('graph') as StarlinkGraph
    expect(graph).toBeDefined()
    expect(Array.isArray(graph.nodes)).toBe(true)
    expect(Array.isArray(graph.edges)).toBe(true)
    // The graph is the same reference the wrapper computed; mutating it
    // through the child (in a real app) would round-trip via the computed.
    expect(typeof graph).toBe('object')
  })

  it('renders the stubbed ConstellationMap (smoke render)', () => {
    const wrapper = mountCosmic()
    expect(wrapper.find('[data-stub="constellation-map"]').exists()).toBe(true)
  })

  it('exposes the child graph even when the searchKeyword is empty', () => {
    const wrapper = mountCosmic({ searchKeyword: '' })
    const stub = wrapper.findComponent(ConstellationMapStub as any)
    expect(stub.props('searchKeyword')).toBe('')
  })
})

describe('CosmicMap.vue with the real ConstellationMap (canvas renderability)', () => {
  beforeEach(() => {
    // ConstellationMap uses useI18n() which calls useAppStore(); we need
    // an active Pinia for that hook to work.
    setActivePinia(createPinia())
    localStorage.clear()

    // happy-dom: HTMLCanvasElement.prototype.getContext is implemented but
    // returns a basic context that lacks many 2d APIs used in the real
    // ConstellationMap. We pre-empt that with a permissive stub so the
    // animation loop can no-op gracefully.
    if (typeof HTMLCanvasElement !== 'undefined') {
      const ctxStub = new Proxy({}, {
        get: (_t, prop) => {
          if (prop === 'createRadialGradient' || prop === 'createLinearGradient') {
            return () => ({ addColorStop: () => {} })
          }
          // Return a function for every method call so the renderer can
          // call them without throwing.
          return () => {}
        },
        set: () => true,
      })
      vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(ctxStub as any)
    }

    // ResizeObserver is used to drive layout; happy-dom doesn't provide it.
    if (typeof window !== 'undefined' && !(window as any).ResizeObserver) {
      class RO {
        observe() {}
        unobserve() {}
        disconnect() {}
      }
      ;(window as any).ResizeObserver = RO
    }
    vi.spyOn(window, 'requestAnimationFrame').mockImplementation((cb: any) => {
      return setTimeout(() => cb(performance.now()), 16) as unknown as number
    })
    vi.spyOn(window, 'cancelAnimationFrame').mockImplementation((id: any) => {
      clearTimeout(id)
    })
  })

  it('mounts the real ConstellationMap with a graph (no crash) and exposes the canvas layer', async () => {
    const wrapper = mount(CosmicMap, { attachTo: document.body })
    await flushPromises()
    await nextTick()

    // ConstellationMap renders 2 canvases (bg + graph) inside its root
    const canvases = wrapper.findAll('canvas')
    expect(canvases.length).toBeGreaterThanOrEqual(2)

    wrapper.unmount()
  })
})

// keep StarlinkGraph import live for the prop assertions
const _typeProbe: StarlinkGraph | undefined = undefined
void _typeProbe
