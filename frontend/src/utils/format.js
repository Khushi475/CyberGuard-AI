/** Shared formatting and severity helpers used across every page. */

export const SEVERITY_COLORS = {
  LOW: '#22c55e',
  MEDIUM: '#f59e0b',
  HIGH: '#fb7185',
  CRITICAL: '#dc2626',
}

export const SEVERITY_BADGE = {
  LOW: 'border-safe/40 bg-safe/10 text-safe',
  MEDIUM: 'border-warn/40 bg-warn/10 text-warn',
  HIGH: 'border-rose-400/40 bg-rose-400/10 text-rose-300',
  CRITICAL: 'border-critical/50 bg-critical/15 text-red-300',
}

export const STATUS_BADGE = {
  NEW: 'border-info/40 bg-info/10 text-info',
  OPEN: 'border-info/40 bg-info/10 text-info',
  ACKNOWLEDGED: 'border-sky-400/40 bg-sky-400/10 text-sky-300',
  INVESTIGATING: 'border-warn/40 bg-warn/10 text-warn',
  CONTAINED: 'border-violet-400/40 bg-violet-400/10 text-violet-300',
  RESOLVED: 'border-safe/40 bg-safe/10 text-safe',
  FALSE_POSITIVE: 'border-slate-500/40 bg-slate-500/10 text-slate-400',
  ONLINE: 'border-safe/40 bg-safe/10 text-safe',
  OFFLINE: 'border-slate-500/40 bg-slate-500/10 text-slate-400',
  MAINTENANCE: 'border-warn/40 bg-warn/10 text-warn',
  QUARANTINED: 'border-critical/50 bg-critical/15 text-red-300',
  ACTIVE: 'border-info/40 bg-info/10 text-info',
  MONITORING: 'border-warn/40 bg-warn/10 text-warn',
  RETIRED: 'border-slate-500/40 bg-slate-500/10 text-slate-400',
}

export const CHART_PALETTE = [
  '#22d3ee',
  '#38bdf8',
  '#a78bfa',
  '#f59e0b',
  '#fb7185',
  '#34d399',
  '#f472b6',
  '#facc15',
  '#60a5fa',
  '#4ade80',
]

/** Severity band for a 0-100 risk score - mirrors the backend bands exactly. */
export const severityFor = (score) => {
  const value = Number(score) || 0
  if (value >= 76) return 'CRITICAL'
  if (value >= 51) return 'HIGH'
  if (value >= 26) return 'MEDIUM'
  return 'LOW'
}

export const titleCase = (value = '') =>
  String(value)
    .replace(/_/g, ' ')
    .toLowerCase()
    .replace(/\b\w/g, (character) => character.toUpperCase())

export const formatNumber = (value) => {
  const number = Number(value)
  if (!Number.isFinite(number)) return '0'
  return number.toLocaleString('en-US')
}

export const formatCompact = (value) => {
  const number = Number(value) || 0
  if (Math.abs(number) >= 1_000_000) return `${(number / 1_000_000).toFixed(1)}M`
  if (Math.abs(number) >= 1_000) return `${(number / 1_000).toFixed(1)}K`
  return String(number)
}

export const formatBytes = (bytes) => {
  const value = Number(bytes) || 0
  if (value === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const index = Math.min(Math.floor(Math.log(value) / Math.log(1024)), units.length - 1)
  return `${(value / 1024 ** index).toFixed(index === 0 ? 0 : 1)} ${units[index]}`
}

export const formatDuration = (seconds) => {
  const value = Number(seconds) || 0
  if (value < 60) return `${value.toFixed(value < 10 ? 1 : 0)}s`
  if (value < 3600) return `${Math.floor(value / 60)}m ${Math.round(value % 60)}s`
  return `${(value / 3600).toFixed(1)}h`
}

/**
 * Parse a timestamp coming from the API.
 *
 * The backend stores and emits **naive UTC** (`datetime.utcnow()` serialised as
 * `2026-09-21T22:35:51`). A date-time string with no timezone designator is
 * parsed by the browser as *local* time, which silently shifts every displayed
 * timestamp by the viewer's UTC offset - on a UTC+5:30 machine a value written
 * one second ago renders as "5h ago". Marking the string as UTC before parsing
 * makes the browser convert it into local time correctly.
 *
 * Date-only strings (the `YYYY-MM-DD` keys used by the chart series) are already
 * treated as UTC by the ECMAScript specification, so they are left untouched.
 */
const parseTimestamp = (value) => {
  if (value instanceof Date) return value
  if (typeof value !== 'string') return new Date(value)
  const hasZone = /(?:Z|[+-]\d{2}:?\d{2})$/.test(value)
  const hasTime = value.includes('T') || value.includes(' ')
  if (!hasZone && hasTime) return new Date(`${value.replace(' ', 'T')}Z`)
  return new Date(value)
}

export const formatDateTime = (value) => {
  if (!value) return '-'
  const date = parseTimestamp(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return date.toLocaleString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export const formatDate = (value) => {
  if (!value) return '-'
  const date = parseTimestamp(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return date.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

export const formatShortDate = (value) => {
  if (!value) return ''
  const date = parseTimestamp(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return date.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })
}

/** "3 minutes ago" style relative time for the activity feed. */
export const timeAgo = (value) => {
  if (!value) return '-'
  const date = parseTimestamp(value)
  if (Number.isNaN(date.getTime())) return String(value)
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000)
  if (seconds < 0) return 'just now'
  if (seconds < 60) return `${seconds}s ago`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days < 30) return `${days}d ago`
  return formatDate(value)
}

export const percent = (value, digits = 0) => `${(Number(value) * 100).toFixed(digits)}%`
