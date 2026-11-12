import { CircleCheck, Info } from 'lucide-react'
import { useLibrary } from '../../hooks/useLibrary'
import {
  formatDate, formatDuration, formatTime, formatTimeRange, minutesToTime, timeToMinutes,
} from '../../utils/datetime'
import Button from '../common/Button'
import ReservationPass from './ReservationPass'

/** The "please check before you confirm" summary shown in booking dialogs. */
export function BookingSummary({ items, window, end }) {
  const { policy, now } = useLibrary()
  const start = timeToMinutes(window.start)
  // For a slot that is already running, the grace period counts from now.
  const base = window.date === now.date ? Math.max(start, now.minutes) : start
  const deadline = minutesToTime(Math.min(base + policy.checkin_grace_minutes, timeToMinutes(end)))
  const opens = minutesToTime(start - policy.checkin_early_minutes)
  return (
    <div className="stack">
      <dl className="details booking-summary">
        {items.map((item) => (
          <div key={item.label} className={`details__item ${item.wide ? 'details__item--wide' : ''}`}>
            <dt>{item.label}</dt>
            <dd>{item.value}</dd>
          </div>
        ))}
        <div className="details__item">
          <dt>Date</dt>
          <dd>{formatDate(window.date)}</dd>
        </div>
        <div className="details__item">
          <dt>Time</dt>
          <dd>{formatTimeRange(window.start, end)} <span className="muted">({formatDuration(window.duration)})</span></dd>
        </div>
      </dl>
      <p className="notice">
        <Info size={16} aria-hidden="true" />
        <span>
          Check in from <strong>{formatTime(opens)}</strong> and no later than{' '}
          <strong>{formatTime(deadline)}</strong>. After that the reservation is released and
          counted as a missed reservation.
        </span>
      </p>
    </div>
  )
}

/** Shown only after the server has confirmed the reservation. */
export function BookingSuccess({ reservation, onDone }) {
  return (
    <div className="stack booking-success">
      <div className="booking-success__head">
        <CircleCheck size={40} aria-hidden="true" />
        <h3>Reservation confirmed</h3>
        <p className="soft">
          {reservation.resource.name} · {formatDate(reservation.date)} ·{' '}
          {formatTimeRange(reservation.start_time, reservation.end_time)}
        </p>
      </div>
      <ReservationPass code={reservation.code} caption="Show this code at the librarian desk if you are asked." />
      <div className="form-actions">
        <Button variant="secondary" onClick={onDone}>Done</Button>
        <Button to={`/reservations/${reservation.id}`}>View reservation</Button>
      </div>
    </div>
  )
}
