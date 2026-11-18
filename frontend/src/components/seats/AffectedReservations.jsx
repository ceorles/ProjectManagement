import { TriangleAlert } from 'lucide-react'
import { formatDate, formatTimeRange } from '../../utils/datetime'

/**
 * The reservations a change of availability would affect. Nothing is cancelled
 * until the user has seen this list and confirmed; each student is notified.
 */
export default function AffectedReservations({ reservations }) {
  if (reservations.length === 0) return null
  const seated = reservations.filter((item) => item.status === 'checked_in')
  return (
    <div className={`notice ${seated.length ? 'notice--danger' : 'notice--warning'}`}>
      <TriangleAlert size={16} aria-hidden="true" />
      <div className="grow">
        <p className="strong">
          {seated.length
            ? 'A student is checked in here. Check them out before taking this out of service.'
            : `${reservations.length} active or upcoming reservation${reservations.length === 1 ? '' : 's'} will be cancelled, and each student notified:`}
        </p>
        <ul className="affected-list">
          {reservations.map((item) => (
            <li key={item.id}>
              <span className="strong">{item.student_name}</span> · {item.status_label}
              <br />
              {formatDate(item.date, { year: undefined })}, {formatTimeRange(item.start_time, item.end_time)}
              {' · '}{item.seats.join(', ')}
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
