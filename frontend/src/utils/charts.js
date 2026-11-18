import { formatDate } from './datetime'

// The two chart series colours are defined (and documented) in dashboard.css.
export const RESOURCE_SERIES = [
  { key: 'seat', label: 'Seats', color: 'var(--chart-1)' },
  { key: 'computer', label: 'Computers', color: 'var(--chart-2)' },
]

export const SINGLE_SERIES = [{ key: 'count', label: 'Reservations', color: 'var(--chart-1)' }]

/** API "daily" rows -> ColumnChart data, split by seats / computers. */
export function toDailySeries(daily) {
  return daily.map((day) => ({
    label: formatDate(day.date, { weekday: undefined, year: undefined }),
    title: formatDate(day.date, { year: undefined }),
    values: { seat: day.seat, computer: day.computer },
  }))
}
