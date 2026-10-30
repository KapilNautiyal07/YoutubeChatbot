export function formatTime(totalSeconds: number): string {
  const s = Math.max(0, Math.floor(totalSeconds))
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = s % 60
  const pad = (n: number) => n.toString().padStart(2, '0')
  return h ? `${h}:${pad(m)}:${pad(sec)}` : `${pad(m)}:${pad(sec)}`
}

export function parseTimestamp(value: string): number | null {
  const parts = value.trim().split(':').map(Number)
  if (parts.some(Number.isNaN) || parts.length < 2 || parts.length > 3) return null
  return parts.reduce((acc, part) => acc * 60 + part, 0)
}

export function formatDuration(seconds: number | null | undefined): string {
  if (!seconds) return ''
  const h = Math.floor(seconds / 3600)
  const m = Math.round((seconds % 3600) / 60)
  if (h) return `${h} hr ${m} min`
  if (seconds < 60) return `${seconds} sec`
  return `${m} min`
}

export function timeAgo(iso: string): string {
  const diff = (Date.now() - new Date(iso).getTime()) / 1000
  if (diff < 60) return 'just now'
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

const TS = String.raw`(?:\d{1,2}:)?\d{1,2}:\d{2}`
const BRACKET_RE = new RegExp(String.raw`\[(\s*${TS}(?:\s*(?:[-–,;]|and)\s*${TS})*\s*)\](?!\()`, 'g')
const SINGLE_RE = new RegExp(TS, 'g')

/** Turn bracketed timestamps like [04:12] or [1:02:03, 1:05:00] into markdown links handled as seek buttons. */
export function linkifyTimestamps(markdown: string): string {
  // Some models cite with lenticular brackets or Unicode dashes; normalize those first.
  const normalized = markdown
    .replace(/【([^】]*)】/g, '[$1]')
    .replace(/\[([^\]]*)\]/g, (m, inner: string) => (/\d:\d\d/.test(inner) ? `[${inner.replace(/[‐‑‒–—]/g, '-')}]` : m))
  return normalized.replace(BRACKET_RE, (_match, inner: string) =>
    inner.replace(SINGLE_RE, (ts) => {
      const seconds = parseTimestamp(ts)
      return seconds === null ? ts : `[${ts}](#t=${seconds})`
    }),
  )
}
