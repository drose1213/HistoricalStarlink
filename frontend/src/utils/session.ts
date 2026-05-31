export function getSessionId(): string {
  let sid = localStorage.getItem('explorer_session_id')
  if (!sid) {
    sid = `session_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`
    localStorage.setItem('explorer_session_id', sid)
  }
  return sid
}
