/**
 * Frontend date/time utilities.
 *
 * The backend serializes naive-UTC datetimes via `iso_utc()` which appends an
 * explicit `Z` suffix (e.g. `2026-06-05T01:43:42Z`).  JavaScript's
 * `new Date(...)` treats such strings as UTC instants, and the helpers below
 * render them in the browser's local timezone — so a UTC+8 client sees
 * `2026-06-05 09:43:42`.
 *
 * For backward compatibility with any pre-migration backend that still emits
 * a *naive* string (`2026-06-05 01:43:42` without a timezone marker), we
 * detect that shape and append `Z` before parsing, ensuring the displayed
 * time stays consistent across the cut-over.
 */

function toUtcDate(input: string | null | undefined): Date | null {
  if (!input) return null
  const s = String(input).trim()
  if (!s) return null
  // Already has explicit timezone: Z, +hh:mm, -hh:mm → trust the browser
  if (/[zZ]$|[+-]\d{2}:?\d{2}$/.test(s)) {
    const d = new Date(s)
    return isNaN(d.getTime()) ? null : d
  }
  // Naive datetime (no zone) — backend stores UTC → treat as UTC
  const d = new Date(s + 'Z')
  return isNaN(d.getTime()) ? null : d
}

function pad(n: number): string {
  return n.toString().padStart(2, '0')
}

/** Local-time `YYYY-MM-DD HH:mm:ss`. Empty string for invalid input. */
export function formatDateTime(input: string | null | undefined): string {
  const d = toUtcDate(input)
  if (!d) return ''
  return (
    `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ` +
    `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
  )
}

/** Local `YYYY-MM-DD`. Empty string for invalid input. */
export function formatDate(input: string | null | undefined): string {
  const d = toUtcDate(input)
  if (!d) return ''
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

/**
 * Human-friendly relative time (中文). Falls back to a local date string when
 * the gap is more than 30 days, mirroring common product UX.
 */
export function formatRelativeTime(input: string | null | undefined): string {
  const d = toUtcDate(input)
  if (!d) return ''
  const now = Date.now()
  const diff = Math.floor((now - d.getTime()) / 1000)
  if (diff < 0) return formatDateTime(input)
  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)} 分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)} 小时前`
  if (diff < 86400 * 30) return `${Math.floor(diff / 86400)} 天前`
  return formatDate(input)
}
