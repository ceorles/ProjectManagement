import { useState } from 'react'
import { Accessibility, Monitor, Plug, Sun, Wrench } from 'lucide-react'
import { Link } from 'react-router-dom'
import { POLL } from '../../config'
import { useAction } from '../../hooks/useAction'
import { useApiQuery } from '../../hooks/useApiQuery'
import { useAuth } from '../../hooks/useAuth'
import { useOnlineStatus } from '../../hooks/useOnlineStatus'
import { reservationService, seatService } from '../../services'
import { AVAILABILITY } from '../../utils/constants'
import Badge from '../common/Badge'
import Button from '../common/Button'
import { FormError } from '../common/FormControls'
import { QueryBoundary } from '../common/Feedback'
import Modal from '../common/Modal'
import { BookingSuccess, BookingSummary } from '../reservations/BookingReview'
import DayTimeline from '../reservations/DayTimeline'
import StudentPicker from '../reservations/StudentPicker'

const FEATURES = [
  { key: 'has_power_outlet', label: 'Power outlet', icon: Plug },
  { key: 'has_computer', label: 'Computer', icon: Monitor },
  { key: 'near_window', label: 'Near window', icon: Sun },
  { key: 'is_accessible', label: 'Wheelchair accessible', icon: Accessibility },
]

/**
 * Everything about one seat for the chosen time. For a free seat this is the
 * review-and-confirm step of making a reservation.
 */
export default function SeatDialog({
  seat, zone, booking, bookable, bookableReason, student, onStudentChange, onClose, onBooked,
}) {
  const { isStaff } = useAuth()
  const online = useOnlineStatus()
  const { window, end } = booking
  const [error, setError] = useState(null)
  const [confirmed, setConfirmed] = useState(null)

  const schedule = useApiQuery(() => seatService.schedule(seat.id, window.date), [seat.id, window.date], {
    interval: POLL.reservations, keepPrevious: true,
  })

  const [reserve, reserving] = useAction(
    () => reservationService.create({
      resource_type: 'seat', seat: seat.id, date: window.date, start_time: window.start,
      end_time: end, student: isStaff ? student?.id : undefined,
    }),
    {
      onSuccess: (reservation) => {
        setConfirmed(reservation)
        onBooked(reservation)
      },
      onError: (failure) => {
        setError(failure)
        onBooked(null) // someone may have taken it: refresh the map
        schedule.refetch()
        return true // shown in the dialog, no toast needed
      },
    },
  )

  const features = FEATURES.filter((feature) => seat[feature.key])
  const free = seat.state === 'available'
  const canReserve = free && bookable && online && (!isStaff || student)
  const state = AVAILABILITY[seat.state]

  if (confirmed) {
    return (
      <Modal open onClose={onClose} title={`Seat ${seat.number}`}>
        <BookingSuccess reservation={confirmed} onDone={onClose} />
      </Modal>
    )
  }

  return (
    <Modal
      open onClose={onClose} busy={reserving}
      title={`Seat ${seat.number}`}
      description={`${zone.name} · ${zone.floor.name}`}
      footer={free ? (
        <>
          <Button variant="secondary" onClick={onClose} disabled={reserving}>Cancel</Button>
          <Button onClick={() => { setError(null); reserve() }} loading={reserving} disabled={!canReserve}>
            Confirm reservation
          </Button>
        </>
      ) : (
        <Button variant="secondary" onClick={onClose}>Close</Button>
      )}
    >
      <div className="stack">
        <div className="row-wrap">
          <Badge tone={state.tone} dot>{state.label}</Badge>
          <span className="chip">{zone.zone_type_label}</span>
          {features.map((feature) => (
            <span key={feature.key} className="chip">
              <feature.icon size={13} aria-hidden="true" /> {feature.label}
            </span>
          ))}
        </div>

        {seat.state === 'unavailable' && (
          <p className="notice notice--warning">
            <Wrench size={16} aria-hidden="true" />
            <span>This seat is out of service{seat.status_note ? `: ${seat.status_note}` : '.'}</span>
          </p>
        )}

        {free && (
          <>
            {isStaff && (
              <div className="stack-sm">
                <p className="field__label">Reserve for</p>
                <StudentPicker value={student} onChange={onStudentChange} />
              </div>
            )}
            <BookingSummary
              window={window} end={end}
              items={[
                { label: 'Seat', value: `${seat.number} · ${zone.name}` },
                { label: 'Floor', value: zone.floor.name },
              ]}
            />
            {!bookable && <p className="notice notice--warning">{bookableReason}</p>}
            {!online && (
              <p className="notice notice--warning">
                You are offline. Reconnect to make this reservation.
              </p>
            )}
            <FormError error={error} />
          </>
        )}

        {seat.blocks.length > 0 && isStaff && (
          <ul className="stack-sm">
            {seat.blocks.map((block) => (
              <li key={block.reservation_id} className="between">
                <span>
                  <span className="strong">{block.student_name}</span>
                  <span className="muted small"> · {block.student_id} · {block.code}</span>
                </span>
                <Link to={`/reservations/${block.reservation_id}`} className="small strong">Open</Link>
              </li>
            ))}
          </ul>
        )}
        {seat.state === 'mine' && seat.blocks[0]?.reservation_id && (
          <Button to={`/reservations/${seat.blocks.find((block) => block.is_mine).reservation_id}`} variant="secondary">
            View your reservation
          </Button>
        )}

        <div className="stack-sm">
          <p className="field__label">This seat on the selected day</p>
          <QueryBoundary query={schedule} compact loadingLabel="Loading schedule...">
            {(data) => <DayTimeline schedule={data} selection={free ? { start: window.start, end } : null} />}
          </QueryBoundary>
        </div>
      </div>
    </Modal>
  )
}
