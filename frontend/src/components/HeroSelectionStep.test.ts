import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick } from 'vue'

// Stub the api/dialogue module so onMounted's resolveHero call is deterministic.
vi.mock('@/api/dialogue', () => {
  return {
    resolveHero: vi.fn(),
  }
})

// Stub next/router transitively — the component only uses the api helper above.
import { resolveHero, type HeroPersona } from '@/api/dialogue'
import HeroSelectionStep from './HeroSelectionStep.vue'

const mockedResolveHero = vi.mocked(resolveHero)

const sampleHeroes: HeroPersona[] = [
  {
    hero_id: 'h-001',
    name: '商鞅',
    role: '变法者',
    era: '战国 · 秦',
    greeting: '以法治秦,可与君论',
    style_hint: '严肃',
    speaking_pattern: '文言',
    description: '秦国大良造,主持商鞅变法',
  },
  {
    hero_id: 'h-002',
    name: '亚历山大',
    role: '征服者',
    era: '公元前 4 世纪',
    greeting: '来吧,与我同行',
    style_hint: '激昂',
    speaking_pattern: '诗体',
    description: '马其顿国王,东征波斯',
  },
]

function mountComponent(props: { topic: string } = { topic: 'AI 发展史' }) {
  return mount(HeroSelectionStep, { props })
}

describe('HeroSelectionStep.vue', () => {
  beforeEach(() => {
    mockedResolveHero.mockReset()
    // default: return two heroes
    mockedResolveHero.mockResolvedValue({
      code: 200,
      message: 'ok',
      data: { heroes: sampleHeroes, source: 'llm' },
    } as any)
  })

  it('renders the topic in the header and shows the AI 推荐 subhint on llm source', async () => {
    const wrapper = mountComponent({ topic: 'AI 发展史' })
    await flushPromises()

    const html = wrapper.html()
    expect(html).toContain('AI 发展史')
    expect(wrapper.text()).toContain('选择与你对话的历史人物')
    expect(wrapper.text()).toContain('AI 推荐')
    // two cards + one "skip" card
    expect(wrapper.findAll('.hero-card').length).toBe(3)
  })

  it('emits "select" with the chosen hero object when a card is clicked', async () => {
    const wrapper = mountComponent({ topic: 'AI 发展史' })
    await flushPromises()

    const cards = wrapper.findAll('.hero-card').filter(c => !c.classes('hero-card--skip'))
    expect(cards.length).toBe(2)

    await cards[0].trigger('click')
    const events = wrapper.emitted('select')
    expect(events).toBeTruthy()
    expect(events!.length).toBe(1)
    expect((events![0][0] as HeroPersona).hero_id).toBe('h-001')
    expect((events![0][0] as HeroPersona).name).toBe('商鞅')
  })

  it('emits "skip" when the "时空对话机" skip card is clicked', async () => {
    const wrapper = mountComponent({ topic: 'AI 发展史' })
    await flushPromises()

    const skipCard = wrapper.find('.hero-card--skip')
    expect(skipCard.exists()).toBe(true)
    await skipCard.trigger('click')

    const events = wrapper.emitted('skip')
    expect(events).toBeTruthy()
    expect(events!.length).toBe(1)
  })

  it('falls back to empty state with the "skip" CTA when resolveHero returns []', async () => {
    mockedResolveHero.mockResolvedValueOnce({
      code: 200,
      message: 'ok',
      data: { heroes: [], source: 'empty' },
    } as any)

    const wrapper = mountComponent({ topic: '陌生话题' })
    await flushPromises()

    expect(wrapper.text()).toContain('未找到匹配的历史人物')
    expect(wrapper.findAll('.hero-card').length).toBe(0)
    // The empty-state CTA still surfaces the skip behavior
    const skipBtn = wrapper.find('button.cy-btn--glow')
    expect(skipBtn.exists()).toBe(true)
    await skipBtn.trigger('click')
    expect(wrapper.emitted('skip')).toBeTruthy()
  })

  it('does not crash when resolveHero rejects — cards simply remain empty', async () => {
    const err = Object.assign(new Error('boom'), { response: { status: 500 } })
    mockedResolveHero.mockRejectedValueOnce(err)
    // silence the in-component console.error noise from the catch
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})

    const wrapper = mountComponent({ topic: '失败话题' })
    await flushPromises()

    // After the catch path: heroes is still [], empty state is shown
    expect(wrapper.text()).toContain('未找到匹配的历史人物')
    expect(spy).toHaveBeenCalled()
  })

  it('shows the "推荐" subhint when the backend reports source=fallback', async () => {
    mockedResolveHero.mockResolvedValueOnce({
      code: 200,
      message: 'ok',
      data: { heroes: sampleHeroes, source: 'fallback' },
    } as any)

    const wrapper = mountComponent({ topic: 'AI 发展史' })
    await flushPromises()
    expect(wrapper.text()).toContain('推荐')
    expect(wrapper.text()).not.toContain('AI 推荐')
  })

  it('shows the "暂无推荐人物" subhint when source is anything other than llm/fallback', async () => {
    mockedResolveHero.mockResolvedValueOnce({
      code: 200,
      message: 'ok',
      data: { heroes: sampleHeroes, source: 'other-source' },
    } as any)

    const wrapper = mountComponent({ topic: 'AI 发展史' })
    await flushPromises()
    expect(wrapper.text()).toContain('暂无推荐人物')
  })

  it('displays the loading spinner area only while the resolveHero promise is in-flight', async () => {
    // Manually create a never-resolving promise so we can inspect the loading state.
    // We resolve from outside the test, so the loading branch should be visible
    // *before* we resolve the promise and disappear *after* we resolve.
    let resolveFn!: (val: any) => void
    mockedResolveHero.mockReturnValueOnce(new Promise(res => { resolveFn = res }) as any)

    const wrapper = mountComponent({ topic: '加载话题' })

    // Wait for: onMounted to fire (sets loading.value = true) and for Vue's
    // scheduler to flush that reactive update to the DOM. The mock promise
    // is permanently pending, so loading will not flip back to false.
    await nextTick()
    await flushPromises()

    expect(wrapper.find('.hero-selection__loading').exists()).toBe(true)
    expect(wrapper.text()).toContain('正在寻找最合适的历史人物')
    expect(wrapper.findAll('.hero-card').length).toBe(0)

    // Now let the promise resolve with two heroes
    resolveFn({ code: 200, message: 'ok', data: { heroes: sampleHeroes, source: 'llm' } })
    await flushPromises()

    expect(wrapper.find('.hero-selection__loading').exists()).toBe(false)
    expect(wrapper.findAll('.hero-card').length).toBe(3)
  })

  it('emits the "select" event with a valid HeroPersona shape (not just an id)', async () => {
    const wrapper = mountComponent({ topic: 'AI 发展史' })
    await flushPromises()

    const cards = wrapper.findAll('.hero-card').filter(c => !c.classes('hero-card--skip'))
    await cards[1].trigger('click')

    const payload = wrapper.emitted('select')![0][0] as HeroPersona
    // All required HeroPersona fields are present on the emitted object
    expect(payload).toMatchObject({
      hero_id: 'h-002',
      name: '亚历山大',
      role: expect.any(String),
      era: expect.any(String),
      greeting: expect.any(String),
      style_hint: expect.any(String),
      speaking_pattern: expect.any(String),
      description: expect.any(String),
    })
  })

  it('does not auto-refetch on prop change (current implementation only fetches on mount)', async () => {
    // The current component has no watcher on `props.topic` — it only fires
    // the initial fetch inside onMounted. We assert this behavior so a
    // future refactor that adds reactivity is intentional.
    const wrapper = mountComponent({ topic: '初始话题' })
    await flushPromises()
    expect(mockedResolveHero).toHaveBeenCalledTimes(1)
    expect(mockedResolveHero).toHaveBeenLastCalledWith('初始话题')

    await wrapper.setProps({ topic: '新话题' })
    await flushPromises()
    // No second call: the component intentionally only fetches on mount.
    expect(mockedResolveHero).toHaveBeenCalledTimes(1)
  })
})
