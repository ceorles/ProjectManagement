import { Link } from 'react-router-dom'
import { useLibrary } from '../../hooks/useLibrary'
import { ACTIVITY_CATEGORIES } from '../../utils/constants'
import { formatRelative } from '../../utils/datetime'
import { EmptyState } from '../common/Feedback'

/** A single headline number. */
export function StatCard({ icon: Icon, label, value, hint, tone = 'blue', to }) {
  const body = (
    <>
      <span className={`stat__icon stat__icon--${tone}`}><Icon size={20} aria-hidden="true" /></span>
      <span className="stat__text">
        <span className="stat__label">{label}</span>
        <span className="stat__value">{value}</span>
        {hint && <span className="stat__hint">{hint}</span>}
      </span>
    </>
  )
  return to
    ? <Link to={to} className="stat stat--link">{body}</Link>
    : <div className="stat">{body}</div>
}

const SEGMENTS = [
  { key: 'occupied', label: 'Occupied' },
  { key: 'reserved', label: 'Reserved' },
  { key: 'available', label: 'Available' },
  { key: 'unavailable', label: 'Unavailable' },
]

/**
 * Live occupancy of seats or rooms as one segmented bar. Every segment is
 * also written out with its count, so the colours only repeat the text.
 */
export function OccupancyMeter({ title, data, to }) {
  const segments = SEGMENTS.filter((segment) => data[segment.key] > 0)
  return (
    <div className="occupancy">
      <div className="between">
        <p className="occupancy__title">{title}</p>
        {to && <Link to={to} className="small strong">Open map</Link>}
      </div>
      <p className="occupancy__headline">
        <strong>{data.available}</strong>
        <span> of {data.total} available</span>
      </p>
      <div className="occupancy__bar" role="img"
        aria-label={`${title}: ${SEGMENTS.map((s) => `${data[s.key]} ${s.label.toLowerCase()}`).join(', ')}`}>
        {segments.map((segment) => (
          <span key={segment.key} className={`occupancy__segment occupancy__segment--${segment.key}`}
            style={{ flexGrow: data[segment.key] }} />
        ))}
      </div>
      <ul className="occupancy__legend">
        {SEGMENTS.map((segment) => (
          <li key={segment.key}>
            <span className={`occupancy__dot occupancy__segment--${segment.key}`} aria-hidden="true" />
            <span className="grow">{segment.label}</span>
            <strong>{data[segment.key]}</strong>
          </li>
        ))}
      </ul>
    </div>
  )
}

/** Ranked horizontal bars, e.g. the most-used seats. One hue, value at the tip. */
export function BarList({ items, unit = 'reservations', empty = 'No data for this period yet.' }) {
  if (!items.length) return <p className="muted small">{empty}</p>
  const max = Math.max(...items.map((item) => item.count))
  return (
    <ul className="bar-list">
      {items.map((item) => (
        <li key={item.label} title={`${item.label}: ${item.count} ${unit}`}>
          <span className="bar-list__label truncate">{item.label}</span>
          <span className="bar-list__track">
            <span className="bar-list__bar" style={{ width: `${item.count / max * 100}%` }} />
          </span>
          <span className="bar-list__value">{item.count}</span>
        </li>
      ))}
    </ul>
  )
}

/** Recent audit-log entries. */
export function ActivityFeed({ items }) {
  const { timeZone } = useLibrary()
  if (!items.length) {
    return <EmptyState compact title="No activity yet" description="Actions taken in the portal are listed here." />
  }
  return (
    <ul className="activity-feed">
      {items.map((item) => (
        <li key={item.id}>
          <span className={`activity-feed__dot activity-feed__dot--${item.category}`} aria-hidden="true" />
          <div className="grow">
            <p className="activity-feed__text">{item.description}</p>
            <p className="muted tiny">
              {item.actor_name} · {ACTIVITY_CATEGORIES[item.category]} · {formatRelative(item.created_at, timeZone)}
            </p>
          </div>
        </li>
      ))}
    </ul>
  )
}
