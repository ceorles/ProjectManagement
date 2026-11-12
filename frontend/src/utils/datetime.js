/**
 * Date and time helpers.
 *
 * Reservation dates and times are exchanged with the API as plain strings in
 * the library's own time zone ("2026-11-13", "09:30"). They are formatted
 * here without ever converting through the browser's time zone, so a student
 * abroad sees the same times as the library clock.
 */

const DAY_MS = 86400000

function parseDate(dateString) {
  const [year, month, day] = dateString.split('-').map(Number)
  return new Date(Date.UTC(year, month - 1, day, 12))
}

function toDateString(date) {
  return date.toISOString().slice(0, 10)
}

export function addDays(dateString, days) {
  return toDateString(new Date(parseDate(dateString).getTime() + days * DAY_MS))
}

/** Monday = 0 ... Sunday = 6, matching the backend. */
export function weekdayOf(dateString) {
  return (parseDate(dateString).getUTCDay() + 6) % 7
}

export function formatDate(dateString, options = {}) {
  if (!dateString) return ''
  return new Intl.DateTimeFormat('en-US', {
    weekday: 'short', month: 'short', day: 'numeric', year: 'numeric',
    ...options,
    timeZone: 'UTC',
  }).format(parseDate(dateString))
}

export function formatShortDate(dateString) {
  return formatDate(dateString, { weekday: undefined, year: undefined })
}

/** "Today", "Tomorrow" or "Fri, Nov 13". */
export function formatFriendlyDate(dateString, today) {
  if (today && dateString === today) return 'Today'
  if (today && dateString === addDays(today, 1)) return 'Tomorrow'
  if (today && dateString === addDays(today, -1)) return 'Yesterday'
  return formatDate(dateString, { year: undefined })
}

export function timeToMinutes(time) {
  const [hours, minutes] = time.split(':').map(Number)
  return hours * 60 + minutes
}

export function minutesToTime(minutes) {
  const hours = Math.floor(minutes / 60)
  return `${String(hours).padStart(2, '0')}:${String(minutes % 60).padStart(2, '0')}`
}

/** "13:30" -> "1:30 PM" */
export function formatTime(time) {
  if (!time) return ''
  const [hours, minutes] = time.split(':').map(Number)
  const suffix = hours >= 12 ? 'PM' : 'AM'
  return `${hours % 12 || 12}:${String(minutes).padStart(2, '0')} ${suffix}`
}

export function formatTimeRange(start, end) {
  return `${formatTime(start)} - ${formatTime(end)}`
}

export function formatDuration(minutes) {
  const hours = Math.floor(minutes / 60)
  const rest = minutes % 60
  if (hours && rest) return `${hours} h ${rest} min`
  if (hours) return `${hours} ${hours === 1 ? 'hour' : 'hours'}`
  return `${rest} min`
}

/** The current date and time on the library's clock. */
export function libraryNow(timeZone) {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone, year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
  }).formatToParts(new Date())
  const get = (type) => parts.find((part) => part.type === type).value
  const time = `${get('hour')}:${get('minute')}`
  return {
    date: `${get('year')}-${get('month')}-${get('day')}`,
    time,
    minutes: timeToMinutes(time),
  }
}

/** Format an ISO timestamp (created at, checked in at, ...) on the library's clock. */
export function formatTimestamp(iso, timeZone, options) {
  if (!iso) return ''
  return new Intl.DateTimeFormat('en-US', {
    month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit',
    ...options,
    timeZone,
  }).format(new Date(iso))
}

export function formatClock(iso, timeZone) {
  return formatTimestamp(iso, timeZone, { month: undefined, day: undefined, year: undefined })
}

/** "just now", "5 min ago", "3 h ago", "2 days ago", then a date. */
export function formatRelative(iso, timeZone) {
  if (!iso) return ''
  const seconds = Math.round((Date.now() - new Date(iso).getTime()) / 1000)
  if (seconds < 45) return 'just now'
  const minutes = Math.round(seconds / 60)
  if (minutes < 60) return `${minutes} min ago`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `${hours} h ago`
  const days = Math.round(hours / 24)
  if (days < 7) return `${days} ${days === 1 ? 'day' : 'days'} ago`
  return formatTimestamp(iso, timeZone, { hour: undefined, minute: undefined })
}

export function greeting(minutes) {
  if (minutes < 12 * 60) return 'Good morning'
  if (minutes < 18 * 60) return 'Good afternoon'
  return 'Good evening'
}
