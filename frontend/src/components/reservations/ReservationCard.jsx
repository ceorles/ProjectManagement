import { Armchair, ChevronRight, Clock, DoorOpen, MapPin, UserRound, Users } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import { useLibrary } from '../../hooks/useLibrary'
import { formatDuration, formatFriendlyDate, formatTimeRange } from '../../utils/datetime'
import { StatusBadge } from '../common/Badge'
import ReservationActions from './ReservationActions'

/** One reservation in a list, with its quick actions. */
export default function ReservationCard({ reservation, onChanged, showStudent = false, actions = true }) {
  const { now } = useLibrary()
  const { isStaff } = useAuth()
  const { resource } = reservation
  const Icon = resource.type === 'seat' ? Armchair : DoorOpen

  return (
    <article className={`reservation-card reservation-card--${reservation.status}`}>
      <span className="reservation-card__icon"><Icon size={20} aria-hidden="true" /></span>
      <div className="reservation-card__main">
        <div className="reservation-card__top">
          <Link to={`/reservations/${reservation.id}`} className="reservation-card__title">
            {resource.name}
          </Link>
          <StatusBadge status={reservation.status} />
          {!reservation.is_owner && !isStaff && <span className="badge badge--yellow">Invited</span>}
        </div>
        <ul className="reservation-card__meta">
          <li>
            <Clock size={14} aria-hidden="true" />
            <span>
              <strong>{formatFriendlyDate(reservation.date, now.date)}</strong>
              {' · '}{formatTimeRange(reservation.start_time, reservation.end_time)}
              <span className="muted"> ({formatDuration(reservation.duration_minutes)})</span>
            </span>
          </li>
          <li><MapPin size={14} aria-hidden="true" /><span>{resource.location}</span></li>
          {resource.type === 'room' && (
            <li><Users size={14} aria-hidden="true" /><span>{reservation.participant_count} people</span></li>
          )}
          {showStudent && (
            <li>
              <UserRound size={14} aria-hidden="true" />
              <span>{reservation.student.full_name}
                {reservation.student.student_id && <span className="muted"> · {reservation.student.student_id}</span>}
              </span>
            </li>
          )}
        </ul>
      </div>
      <div className="reservation-card__actions">
        {actions && <ReservationActions reservation={reservation} onChanged={onChanged} />}
        <Link to={`/reservations/${reservation.id}`} className="btn btn--ghost btn--sm">
          Details <ChevronRight size={15} aria-hidden="true" />
        </Link>
      </div>
    </article>
  )
}
