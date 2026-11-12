import { Armchair, DoorOpen, Info } from 'lucide-react'
import { useParams } from 'react-router-dom'
import { StatusBadge } from '../../components/common/Badge'
import Card from '../../components/common/Card'
import { QueryBoundary } from '../../components/common/Feedback'
import PageHeader from '../../components/common/PageHeader'
import ReservationActions from '../../components/reservations/ReservationActions'
import ReservationPass from '../../components/reservations/ReservationPass'
import '../../components/reservations/reservations.css'
import { POLL } from '../../config'
import { useApiQuery } from '../../hooks/useApiQuery'
import { useAuth } from '../../hooks/useAuth'
import { useLibrary } from '../../hooks/useLibrary'
import { reservationService } from '../../services'
import {
  formatClock, formatDate, formatDuration, formatTimeRange, formatTimestamp,
} from '../../utils/datetime'

function statusMessage(reservation, timeZone, isStaff) {
  const who = isStaff ? 'The student' : 'You'
  switch (reservation.status) {
    case 'confirmed':
      if (reservation.can_check_in) {
        return `Check-in is open until ${formatClock(reservation.checkin_deadline, timeZone)}. After that the reservation is released.`
      }
      return `Check-in opens at ${formatClock(reservation.checkin_opens_at, timeZone)} and closes at ${formatClock(reservation.checkin_deadline, timeZone)}.`
    case 'checked_in':
      return `${who} checked in at ${formatClock(reservation.checked_in_at, timeZone)}. The reservation ends at ${formatClock(reservation.end_at, timeZone)}.`
    case 'completed':
      return 'This reservation was completed.'
    case 'cancelled':
      return reservation.cancel_reason
        ? `This reservation was cancelled. Reason: ${reservation.cancel_reason}`
        : 'This reservation was cancelled.'
    case 'no_show':
      return 'Nobody checked in during the check-in period, so the reservation was released.'
    default:
      return ''
  }
}

function events(reservation, timeZone) {
  const at = (iso) => formatTimestamp(iso, timeZone)
  return [
    { tone: 'blue', label: reservation.booked_by_staff ? 'Reserved by library staff' : 'Reserved', time: at(reservation.created_at) },
    reservation.checked_in_at && { tone: 'green', label: 'Checked in', time: at(reservation.checked_in_at) },
    reservation.checked_out_at && { tone: 'gray', label: 'Checked out', time: at(reservation.checked_out_at) },
    reservation.cancelled_at && { tone: 'red', label: 'Cancelled', time: at(reservation.cancelled_at) },
    reservation.status === 'no_show' && { tone: 'orange', label: 'Marked as no-show', time: `after ${at(reservation.checkin_deadline)}` },
  ].filter(Boolean)
}

function Detail({ label, wide, children }) {
  return (
    <div className={`details__item ${wide ? 'details__item--wide' : ''}`}>
      <dt>{label}</dt>
      <dd>{children}</dd>
    </div>
  )
}

/** One reservation in full. Used by its owner, invited classmates and staff. */
export default function ReservationDetailPage() {
  const { id } = useParams()
  const { isStaff } = useAuth()
  const { timeZone } = useLibrary()
  const query = useApiQuery(() => reservationService.get(id), [id], { interval: POLL.reservations })

  return (
    <QueryBoundary query={query} loadingLabel="Loading reservation...">
      {(reservation) => {
        const { resource, student } = reservation
        const live = reservation.status === 'confirmed' || reservation.status === 'checked_in'
        const Icon = resource.type === 'seat' ? Armchair : DoorOpen
        return (
          <>
            <PageHeader
              back={isStaff
                ? { to: '/manage/reservations', label: 'All reservations' }
                : { to: '/reservations', label: 'My reservations' }}
              title={resource.name}
              description={resource.location}
              actions={<ReservationActions reservation={reservation} onChanged={query.refetch} size="md" />}
            />

            <div className="split">
              <div className="stack">
                <Card>
                  <div className="stack">
                    <div className="reservation-hero">
                      <div className="row">
                        <span className="reservation-card__icon"><Icon size={20} aria-hidden="true" /></span>
                        <div>
                          <p className="reservation-hero__when">{formatDate(reservation.date)}</p>
                          <p className="soft">
                            {formatTimeRange(reservation.start_time, reservation.end_time)}
                            {' · '}{formatDuration(reservation.duration_minutes)}
                          </p>
                        </div>
                      </div>
                      <StatusBadge status={reservation.status} />
                    </div>
                    <p className={`notice ${reservation.status === 'no_show' || reservation.status === 'cancelled' ? 'notice--warning' : ''}`}>
                      <Info size={16} aria-hidden="true" />
                      <span>{statusMessage(reservation, timeZone, isStaff)}</span>
                    </p>
                  </div>
                </Card>

                <Card title="Details">
                  <dl className="details">
                    <Detail label={resource.type === 'seat' ? 'Seat' : 'Room'}>
                      {resource.name}{resource.type === 'room' && ` (${resource.code})`}
                    </Detail>
                    <Detail label="Location">{resource.location}</Detail>
                    <Detail label="Reserved for">
                      {student.full_name}
                      {student.student_id && <span className="muted"> · {student.student_id}</span>}
                    </Detail>
                    {isStaff && <Detail label="Email">{student.email}</Detail>}
                    {isStaff && student.program && <Detail label="Program">{student.program}</Detail>}
                    {resource.type === 'room' && (
                      <Detail label="People">{reservation.participant_count} of {resource.capacity}</Detail>
                    )}
                    {reservation.purpose && <Detail label="Purpose" wide>{reservation.purpose}</Detail>}
                    {reservation.participants.length > 0 && (
                      <Detail label="Invited classmates" wide>
                        {reservation.participants.map((person) => person.full_name).join(', ')}
                      </Detail>
                    )}
                  </dl>
                </Card>
              </div>

              <div className="stack">
                {live && (reservation.is_owner || isStaff) && (
                  <Card title="Check-in code">
                    <ReservationPass
                      code={reservation.code}
                      caption={isStaff
                        ? 'The student can show this code at the desk.'
                        : 'Show this at the librarian desk, or check in yourself with the button above.'}
                    />
                  </Card>
                )}
                <Card title="History">
                  <ul className="event-list">
                    {events(reservation, timeZone).map((event) => (
                      <li key={event.label}>
                        <span className={`event-list__dot event-list__dot--${event.tone}`} aria-hidden="true" />
                        <div>
                          <p className="strong">{event.label}</p>
                          <p className="muted small">{event.time}</p>
                        </div>
                      </li>
                    ))}
                  </ul>
                  {!live && <p className="muted small" style={{ marginTop: 14 }}>Reference: <span className="mono">{reservation.code}</span></p>}
                </Card>
              </div>
            </div>
          </>
        )
      }}
    </QueryBoundary>
  )
}
