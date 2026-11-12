/**
 * Works out which dates and times can be offered in the booking screens,
 * from the library overview (opening hours, closures and booking rules).
 *
 * This only decides what to *offer*. The backend validates every rule again
 * when the reservation is submitted.
 */
import { addDays, minutesToTime, timeToMinutes, weekdayOf } from './datetime'

/** Opening hours for one date, or `{ isOpen: false, reason }`. */
export function scheduleFor(overview, date) {
  const closure = overview.closures.find((item) => item.date === date)
  if (closure) return { isOpen: false, reason: closure.reason }
  const hours = overview.hours.find((item) => item.weekday === weekdayOf(date))
  if (!hours || !hours.is_open) return { isOpen: false, reason: 'Closed' }
  return {
    isOpen: true,
    opensAt: hours.opens_at,
    closesAt: hours.closes_at,
    opens: timeToMinutes(hours.opens_at),
    closes: timeToMinutes(hours.closes_at),
  }
}

/** Every date a reservation may be made for, with its opening state. */
export function bookableDates(overview, now) {
  const dates = []
  for (let offset = 0; offset <= overview.policy.max_advance_days; offset += 1) {
    const date = addDays(now.date, offset)
    const schedule = scheduleFor(overview, date)
    let isOpen = schedule.isOpen
    let reason = schedule.reason
    // Today stops being bookable once the last slot has started.
    if (isOpen && offset === 0 && startTimes(overview, date, now).length === 0) {
      isOpen = false
      reason = 'Closed for today'
    }
    dates.push({ date, isOpen, reason })
  }
  return dates
}

/** Start times that can still be booked on `date` (the slot in progress included). */
export function startTimes(overview, date, now) {
  const schedule = scheduleFor(overview, date)
  if (!schedule.isOpen) return []
  const slot = overview.slot_minutes
  const minimum = overview.policy.min_duration_minutes
  let first = schedule.opens
  if (date === now.date) {
    first = Math.max(first, Math.floor(now.minutes / slot) * slot)
  }
  const times = []
  for (let minutes = first; minutes + minimum <= schedule.closes; minutes += slot) {
    times.push(minutesToTime(minutes))
  }
  return times
}

export function maxDuration(overview, resourceType) {
  return resourceType === 'room'
    ? overview.policy.max_room_duration_minutes
    : overview.policy.max_seat_duration_minutes
}

/** Durations (in minutes) that fit between `start` and closing time. */
export function durations(overview, date, start, resourceType) {
  const schedule = scheduleFor(overview, date)
  if (!schedule.isOpen || !start) return []
  const slot = overview.slot_minutes
  const limit = Math.min(maxDuration(overview, resourceType), schedule.closes - timeToMinutes(start))
  const options = []
  for (let minutes = overview.policy.min_duration_minutes; minutes <= limit; minutes += slot) {
    options.push(minutes)
  }
  return options
}

export function endTime(start, duration) {
  return minutesToTime(timeToMinutes(start) + duration)
}

/**
 * Repair a (possibly restored and now stale) window so it is valid again:
 * a past date moves to the first open day, a past start time to the next
 * free slot, an over-long duration is shortened.
 */
export function normalizeWindow(overview, now, resourceType, window) {
  const dates = bookableDates(overview, now)
  const open = dates.filter((item) => item.isOpen)
  if (open.length === 0) return { date: now.date, start: '', duration: 0 }

  const date = open.some((item) => item.date === window.date) ? window.date : open[0].date
  const starts = startTimes(overview, date, now)
  const start = starts.includes(window.start) ? window.start : starts[0]
  const options = durations(overview, date, start, resourceType)
  const preferred = resourceType === 'room' ? 60 : 120
  let duration = window.duration
  if (!options.includes(duration)) {
    duration = options.includes(preferred) ? preferred : options[options.length - 1]
  }
  return { date, start, duration }
}
