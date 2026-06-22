/**
 * 分享链接工具
 * 用于将 dynamic 对话完成后的 topic 编码到 URL 中，
 * 落地页 (/landing) 可通过 ?d= 参数解码还原。
 *
 * 纯函数实现，无副作用，便于单元测试。
 */

const LANDING_PATH = '/landing'
const SHARE_PARAM = 'd'

/**
 * Base64 编码（兼容中文/多字节字符）。
 * 使用 encodeURIComponent + unescape + btoa 模式，
 * 避免直接 btoa 中文抛出 InvalidCharacterError。
 * 进一步替换为 base64url（+/= → -_ 不带填充），避免 URL parser 把 + 当空格。
 */
export function encodeTopic(topic: string): string {
  if (typeof topic !== 'string') return ''
  try {
    const std = btoa(unescape(encodeURIComponent(topic)))
    return std.replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '')
  } catch (_) {
    return ''
  }
}

/**
 * Base64 解码（兼容中文/多字节字符）。
 * 解码失败返回空串。同时兼容标准 base64 与 base64url 输入。
 */
export function decodeTopic(encoded: string): string {
  if (typeof encoded !== 'string' || !encoded) return ''
  try {
    let std = encoded.replace(/-/g, '+').replace(/_/g, '/')
    const pad = std.length % 4
    if (pad === 2) std += '=='
    else if (pad === 3) std += '='
    else if (pad === 1) return ''
    return decodeURIComponent(escape(atob(std)))
  } catch (_) {
    return ''
  }
}

/**
 * 生成可分享链接。
 * @param topic 用户在 dynamic 模式下输入的话题
 * @returns 形如 `${origin}/landing?d=<base64>` 的完整 URL
 */
export function generateShareLink(topic: string): string {
  if (typeof window === 'undefined') {
    // SSR / 测试环境无 window 时返回相对路径
    const encoded = encodeTopic(topic)
    return `${LANDING_PATH}?${SHARE_PARAM}=${encoded}`
  }
  const origin = window.location.origin || ''
  const encoded = encodeTopic(topic)
  return `${origin}${LANDING_PATH}?${SHARE_PARAM}=${encoded}`
}

/**
 * 解析当前页面 URL 中的 ?d= 参数。
 * @returns 解码后的 topic；无参数或解析失败返回 null
 */
export function parseShareLink(): string | null {
  if (typeof window === 'undefined') return null
  try {
    const params = new URLSearchParams(window.location.search)
    const raw = params.get(SHARE_PARAM)
    if (!raw) return null
    const decoded = decodeTopic(raw)
    return decoded || null
  } catch (_) {
    return null
  }
}

/**
 * 解析指定 URL（字符串）中的 ?d= 参数。
 * 纯函数变体，便于测试。
 */
export function parseShareLinkFromUrl(url: string): string | null {
  try {
    const u = new URL(url, 'http://placeholder.local')
    const raw = u.searchParams.get(SHARE_PARAM)
    if (!raw) return null
    const decoded = decodeTopic(raw)
    return decoded || null
  } catch (_) {
    return null
  }
}
