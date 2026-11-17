import { useState } from 'react'
import { Accessibility, Info, Monitor, Plug, Wrench } from 'lucide-react'
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
import { FormError, TextAreaField } from '../common/FormControls'
import { QueryBoundary } from '../common/Feedback'
import Modal from '../common/Modal'
import { BookingSuccess, BookingSummary } from '../reservations/BookingReview'
import DayTimeline from '../reservations/DayTimeline'
import StudentPicker from '../reservations/StudentPicker'

const FEATURES = [
  { key: 'has_power_outlet', label: 'Power outlet', icon: Plug },
  { key: 'has_computer', label: 'Computer', icon: Monitor },
  { key: 'is_accessible', label: 'Wheelchair accessible', icon: Accessibility },
]

// More seats than this need a reason (the server enforces the same rule).
export const SEATS_WITHOUT_REASON = 2
export const MAX_SEATS = 6

function seatTitle(seat) {
  return seat.has_computer ? `Computer ${seat.number}` : `Seat ${seat.number}`
}

function FeatureChips({ seat, zone }) {
  return (
    <>
      <span className="chip">{zone.zone_type_label}</span>
      {seat.table_number != null && <span className="chip">Table {seat.table_number}</span>}
      {FEATURES.filter((feature) => seat[feature.key]).map((feature) => (
        <span key={feature.key} className="chip">
          <feature.icon size={13} aria-hidden="true" /> {feature.label}
        </span>
      ))}
    </>
  )
}

function SeatSchedule({ seat, date, selection }) {
  const schedule = useApiQuery(() => seatService.schedule(seat.id, date), [seat.id, date], {
    interval: POLL.reservations, keepPrevious: true,
  })
  return (
    <div className="stack-sm">
      <p className="field__label">This {seat.has_computer ? 'computer' : 'seat'} on the selected day</p>
      <QueryBoundary query={schedule} compact loadingLabel="Loading schedule...">
        {(data) => <DayTimeline schedule={data} selection={selection} />}
      </QueryBoundary>
    </div>
  )
}

/** Details of one seat that cannot be picked right now (taken, yours, out of service). */
export function SeatInfoDialog({ seat, zone, date, onClose }) {
  const { isStaff } = useAuth()
  const state = AVAILABILITY[seat.state]
  const mine = seat.blocks.find((block) => block.is_mine)
  return (
    <Modal
      open onClose={onClose} title={seatTitle(seat)} description={`${zone.name} · ${zone.floor.name}`}
      footer={<Button variant="secondary" onClick={onClose}>Close</Button>}
    >
      <div className="stack">
        <div className="row-wrap">
          <Badge tone={state.tone} dot>{state.label}</Badge>
          <FeatureChips seat={seat} zone={zone} />
        </div>
        {seat.state === 'unavailable' && (
          <p className="notice notice--warning">
            <Wrench size={16} aria-hidden="true" />
            <span>This seat is out of service{seat.status_note ? `: ${seat.status_note}` : '.'}</span>
          </p>
        )}
        {isStaff && seat.blocks.length > 0 && (
          <ul className="stack-sm">
            {seat.blocks.map((block) => (
              <li key={block.reservation_id} className="between">
                <span>
                  <span className="strong">{block.student_name}</span>
                  <span className="muted small">
                    {' '}· {block.student_id} · {block.code}{block.status === 'pending' && ' · pending approval'}
                  </span>
                </span>
                <Link to={`/reservations/${block.reservation_id}`} className="small strong">Open</Link>
              </li>
            ))}
          </ul>
        )}
        {mine?.reservation_id && (
          <Button to={`/reservations/${mine.reservation_id}`} variant="secondary">
            View your {mine.status === 'pending' ? 'request' : 'reservation'}
          </Button>
        )}
        <SeatSchedule seat={seat} date={date} />
      </div>
    </Modal>
  )
}

/**
 * Review step for the seats a student has picked (one seat, a group, a whole
 * table, or one computer). A student's request goes to the librarian for
 * approval; a librarian booking for a student is confirmed directly.
 */
export default function SeatRequestDialog({
  entries, booking, bookable, bookableReason, reason, onReasonChange,
  student, onStudentChange, onClose, onBooked,
}) {
  const { canManageReservations } = useAuth()
  const online = useOnlineStatus()
  const { window, end } = booking
  const [error, setError] = useState(null)
  const [confirmed, setConfirmed] = useState(null)

  const seats = entries.map((entry) => entry.seat)
  const { zone } = entries[0]
  const tables = new Set(seats.map((seat) => seat.table_number))
  const wholeTable = seats.length === MAX_SEATS && tables.size === 1 && seats[0].table_number != null
  const needsReason = seats.length > SEATS_WITHOUT_REASON
  const title = seats.length === 1
    ? seatTitle(seats[0])
    : wholeTable ? `Table ${seats[0].table_number} (${seats.length} seats)` : `${seats.length} seats`

  const [submit, submitting] = useAction(
    () => reservationService.create({
      resource_type: 'seat', seats: seats.map((seat) => seat.id), date: window.date,
      start_time: window.start, end_time: end, purpose: needsReason ? reason.trim() : '',
      student: canManageReservations ? student?.id : undefined,
    }),
    {
      onSuccess: (reservation) => {
        setConfirmed(reservation)
        onBooked(reservation)
      },
      onError: (failure) => {
        setError(failure)
        onBooked(null) // someone may have taken a seat: refresh the map
        return true // shown in the dialog, no toast needed
      },
    },
  )

  if (confirmed) {
    return (
      <Modal open onClose={onClose} title={title}>
        <BookingSuccess reservation={confirmed} onDone={onClose} />
      </Modal>
    )
  }

  const ready = bookable && online && (!needsReason || reason.trim())
    && (!canManageReservations || student)

  return (
    <Modal
      open onClose={onClose} busy={submitting} title={title}
      description={`${zone.name} · ${zone.floor.name}`}
      footer={(
        <>
          <Button variant="secondary" onClick={onClose} disabled={submitting}>Cancel</Button>
          <Button onClick={() => { setError(null); submit() }} loading={submitting} disabled={!ready}>
            {canManageReservations ? 'Confirm reservation' : 'Send request'}
          </Button>
        </>
      )}
    >
      <div className="stack">
        {seats.length === 1 && (
          <div className="row-wrap">
            <Badge tone="green" dot>Available</Badge>
            <FeatureChips seat={seats[0]} zone={zone} />
          </div>
        )}

        {canManageReservations && (
          <div className="stack-sm">
            <p className="field__label">Reserve for</p>
            <StudentPicker value={student} onChange={onStudentChange} />
          </div>
        )}

        <BookingSummary
          window={window} end={end}
          items={[
            {
              label: seats.length === 1 ? (seats[0].has_computer ? 'Computer' : 'Seat') : 'Seats',
              value: wholeTable
                ? `Whole table ${seats[0].table_number}: ${seats.map((seat) => seat.number).join(', ')}`
                : seats.map((seat) => seat.number).join(', '),
              wide: seats.length > 2,
            },
            { label: 'Number of seats', value: seats.length },
            { label: 'Area', value: `${zone.name} · ${zone.floor.name}` },
          ]}
        />

        {needsReason && (
          <TextAreaField
            label={`Reason for requesting ${seats.length} seats`} required rows={2} maxLength={200}
            placeholder="e.g. Group study for our thesis"
            hint={`Needed for more than ${SEATS_WITHOUT_REASON} seats. The librarian reads it when reviewing the request.`}
            value={reason} onChange={(event) => onReasonChange(event.target.value)}
          />
        )}

        {!canManageReservations && (
          <p className="notice notice--warning">
            <Info size={16} aria-hidden="true" />
            <span>
              This sends a <strong>request</strong>. It is confirmed only after the librarian
              approves it; you will be notified.
            </span>
          </p>
        )}
        {!bookable && <p className="notice notice--warning">{bookableReason}</p>}
        {!online && (
          <p className="notice notice--warning">You are offline. Reconnect to send this request.</p>
        )}
        <FormError error={error} />

        {seats.length === 1 && (
          <SeatSchedule seat={seats[0]} date={window.date} selection={{ start: window.start, end }} />
        )}
      </div>
    </Modal>
  )
}
