import { formatDate } from './datetime'

// The two chart series colours are defined (and documented) in dashboard.css.
export const RESOURCE_SERIES = [
  { key: 'seat', label: 'Seats', color: 'var(--chart-1)' },
  { key: 'room', label: 'Study rooms', color: 'var(--chart-2)' },
]

export const SINGLE_SERIES = [{ key: 'count', label: 'Reservations', color: 'var(--chart-1)' }]

/** API "daily" rows -> ColumnChart data, split by seat / room. */
export function toDailySeries(daily) {
  return daily.map((day) => ({
    label: formatDate(day.date, { weekday: undefined, year: undefined }),
    title: formatDate(day.date, { year: undefined }),
    values: { seat: day.seat, room: day.room },
  }))
}
