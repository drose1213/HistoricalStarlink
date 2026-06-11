// 简单静默埋点 SDK: 失败 console.warn 不阻塞主流程
// 后端: POST /api/analytics/event
// Schema: { event_name, user_agent?, topic?, payload? }

export type AnalyticsEventName =
  | 'app_enter'
  | 'dialogue_completed'
  | 'paywall_clicked'
  | 'feedback_submitted'
  | 'dialogue_share_clicked'

// 常量对象: 防止业务方拼写错误, 用 ANALYTICS_EVENTS.APP_ENTER 代替 'app_enter'
export const ANALYTICS_EVENTS = {
  APP_ENTER: 'app_enter',
  DIALOGUE_COMPLETED: 'dialogue_completed',
  PAYWALL_CLICKED: 'paywall_clicked',
  FEEDBACK_SUBMITTED: 'feedback_submitted',
  DIALOGUE_SHARE_CLICKED: 'dialogue_share_clicked',
} as const satisfies Record<string, AnalyticsEventName>

export interface AnalyticsPayload {
  topic?: string
  [key: string]: unknown
}

export async function trackEvent(
  name: AnalyticsEventName,
  payload: AnalyticsPayload = {},
): Promise<void> {
  try {
    const topic = payload.topic
    const rest: Record<string, unknown> = {}
    for (const key in payload) {
      if (key !== 'topic') {
        rest[key] = payload[key]
      }
    }
    const body = {
      event_name: name,
      user_agent: typeof navigator !== 'undefined' ? navigator.userAgent : undefined,
      topic,
      payload: rest,
    }
    await fetch('/api/analytics/event', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      // 不阻塞, 无 keepalive
    })
  } catch (e) {
    console.warn('[analytics] trackEvent failed', name, e)
  }
}

// 判定是否启用埋点: 默认开启, 但 ?analytics=off 时禁用 (用于演示)
function isAnalyticsEnabled(): boolean {
  if (typeof window === 'undefined') return true
  try {
    const params = new URLSearchParams(window.location.search)
    const flag = params.get('analytics')
    if (flag && flag.toLowerCase() === 'off') return false
  } catch {
    // ignore
  }
  return true
}

// 对外包装: Task 7 集成使用时统一走这里, 默认开启, 支持 ?analytics=off 关闭
export async function trackEventIfEnabled(
  name: AnalyticsEventName,
  payload: AnalyticsPayload = {},
): Promise<void> {
  if (!isAnalyticsEnabled()) return
  await trackEvent(name, payload)
}
