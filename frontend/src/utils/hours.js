import { formatTime } from './datetime'

const SHORT = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

function same(a, b) {
  if (a.is_open !== b.is_open) return false
  return !a.is_open || (a.opens_at === b.opens_at && a.closes_at === b.closes_at)
}

/**
 * Weekly opening hours as short lines, joining consecutive days with the same
 * hours: [{ days: 'Mon - Fri', hours: '7:00 AM - 7:00 PM' }, { days: 'Sun', hours: 'Closed' }]
 */
export function groupHours(hours) {
  const days = [...hours].sort((a, b) => a.weekday - b.weekday)
  const groups = []
  days.forEach((day) => {
    const last = groups[groups.length - 1]
    if (last && same(last.sample, day) && last.to === day.weekday - 1) {
      last.to = day.weekday
    } else {
      groups.push({ from: day.weekday, to: day.weekday, sample: day })
    }
  })
  return groups.map(({ from, to, sample }) => ({
    days: from === to ? SHORT[from] : `${SHORT[from]} - ${SHORT[to]}`,
    hours: sample.is_open ? `${formatTime(sample.opens_at)} - ${formatTime(sample.closes_at)}` : 'Closed',
    open: sample.is_open,
  }))
}
