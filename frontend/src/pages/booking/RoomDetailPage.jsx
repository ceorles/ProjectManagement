import { useState } from 'react'
import { CalendarCheck, MapPin, Minus, Plus, Users, Wrench } from 'lucide-react'
import { useParams } from 'react-router-dom'
import Badge from '../../components/common/Badge'
import Button from '../../components/common/Button'
import Card from '../../components/common/Card'
import { QueryBoundary } from '../../components/common/Feedback'
import { FormError, TextField } from '../../components/common/FormControls'
import Modal from '../../components/common/Modal'
import PageHeader from '../../components/common/PageHeader'
import { BookingSuccess, BookingSummary } from '../../components/reservations/BookingReview'
import BookingWindowPicker from '../../components/reservations/BookingWindowPicker'
import DayTimeline from '../../components/reservations/DayTimeline'
import '../../components/reservations/reservations.css'
import StudentPicker from '../../components/reservations/StudentPicker'
import InviteList from '../../components/rooms/InviteList'
import '../../components/rooms/rooms.css'
import { POLL } from '../../config'
import { useAction } from '../../hooks/useAction'
import { useApiQuery } from '../../hooks/useApiQuery'
import { useAuth } from '../../hooks/useAuth'
import { useBookingWindow } from '../../hooks/useBookingWindow'
import { useFormDraft } from '../../hooks/useFormDraft'
import { useOnlineStatus } from '../../hooks/useOnlineStatus'
import { reservationService, roomService } from '../../services'
import { RESOURCE_STATUS } from '../../utils/constants'
import { formatDate, formatTimeRange, timeToMinutes } from '../../utils/datetime'

function overlaps(block, start, end) {
  return timeToMinutes(block.start_time) < timeToMinutes(end)
    && timeToMinutes(block.end_time) > timeToMinutes(start)
}

function BookingForm({ room, booking, schedule, onBooked }) {
  const { user, isStaff } = useAuth()
  const online = useOnlineStatus()
  const { window, setWindow, end, bookable } = booking
  // What has been typed for this room is kept if the page is refreshed.
  const form = useFormDraft(`room-booking:${room.id}`, {
    participant_count: null, purpose: '', invitees: [], student: null,
  })
  const { values, setField, clearDraft, restored } = form
  const [reviewing, setReviewing] = useState(false)
  const [error, setError] = useState(null)
  const [confirmed, setConfirmed] = useState(null)

  const minimum = Math.max(room.min_occupancy, values.invitees.length + 1)
  const people = Math.min(Math.max(values.participant_count ?? minimum, minimum), room.capacity)
  const taken = bookable && schedule?.blocks.some((block) => overlaps(block, window.start, end))
  const inService = room.status === 'active'
  const ready = bookable && inService && !taken && online && (!isStaff || values.student)

  const [reserve, reserving] = useAction(
    () => reservationService.create({
      resource_type: 'room', room: room.id, date: window.date, start_time: window.start,
      end_time: end, participant_count: people, purpose: values.purpose.trim(),
      participant_student_ids: values.invitees.map((person) => person.student_id),
      student: isStaff ? values.student?.id : undefined,
    }),
    {
      onSuccess: (reservation) => {
        setConfirmed(reservation)
        clearDraft(true) // the form is done: forget the draft
        onBooked()
      },
      onError: (failure) => {
        setError(failure)
        onBooked() // refresh the schedule: the time may have been taken
        return true
      },
    },
  )

  const closeDialog = () => {
    setReviewing(false)
    setConfirmed(null)
    setError(null)
  }

  return (
    <Card title="Reserve this room" icon={CalendarCheck}>
      <div className="stack">
        {restored && (
          <p className="notice">
            <span>
              Your unfinished reservation was restored.{' '}
              <button type="button" className="link-button" onClick={() => clearDraft(true)}>Clear it</button>
            </span>
          </p>
        )}
        {isStaff && (
          <div className="stack-sm">
            <p className="field__label">Reserve for</p>
            <StudentPicker value={values.student} onChange={(student) => setField('student', student)} />
          </div>
        )}

        <BookingWindowPicker resourceType="room" window={window} onChange={setWindow} />

        <div className="stack-sm">
          <p className="field__label" id="people-label">Number of people</p>
          <div className="row">
            <div className="stepper" role="group" aria-labelledby="people-label">
              <button type="button" aria-label="Fewer people" disabled={people <= minimum}
                onClick={() => setField('participant_count', people - 1)}>
                <Minus size={16} />
              </button>
              <span className="stepper__value" aria-live="polite">{people}</span>
              <button type="button" aria-label="More people" disabled={people >= room.capacity}
                onClick={() => setField('participant_count', people + 1)}>
                <Plus size={16} />
              </button>
            </div>
            <p className="muted small">
              {room.min_occupancy > 1 ? `Groups of ${room.min_occupancy} to ${room.capacity}.` : `Up to ${room.capacity} people.`}
            </p>
          </div>
        </div>

        <TextField label="Purpose" placeholder="e.g. Capstone project meeting" maxLength={200}
          hint="Optional. Helps the library understand how rooms are used."
          value={values.purpose} onChange={(event) => setField('purpose', event.target.value)} />

        <InviteList
          value={values.invitees} max={room.capacity - 1}
          ownStudentId={isStaff ? values.student?.student_id : user.student_id}
          onChange={(invitees) => setField('invitees', invitees)}
        />

        {!inService && (
          <p className="notice notice--warning">
            <Wrench size={16} aria-hidden="true" />
            <span>This room cannot be reserved right now{room.status_note ? `: ${room.status_note}` : '.'}</span>
          </p>
        )}
        {inService && taken && (
          <p className="notice notice--warning">
            The room is already booked for all or part of this time. Pick another time using the
            schedule.
          </p>
        )}
        {!online && <p className="notice notice--warning">You are offline. Reconnect to reserve this room.</p>}

        <Button size="lg" block disabled={!ready} onClick={() => setReviewing(true)}>
          Review reservation
        </Button>
      </div>

      <Modal
        open={reviewing} onClose={closeDialog} busy={reserving}
        title={confirmed ? room.name : 'Review your reservation'}
        description={confirmed ? undefined : 'Please check the details before confirming.'}
        footer={confirmed ? null : (
          <>
            <Button variant="secondary" onClick={closeDialog} disabled={reserving}>Go back</Button>
            <Button onClick={() => { setError(null); reserve() }} loading={reserving}>Confirm reservation</Button>
          </>
        )}
      >
        {confirmed ? (
          <BookingSuccess reservation={confirmed} onDone={closeDialog} />
        ) : (
          <div className="stack">
            <BookingSummary
              window={window} end={end}
              items={[
                { label: 'Room', value: `${room.name} (${room.code})` },
                { label: 'Floor', value: room.floor_detail.name },
                ...(isStaff && values.student
                  ? [{ label: 'Reserved for', value: `${values.student.full_name} · ${values.student.student_id}`, wide: true }]
                  : []),
                { label: 'People', value: people },
                { label: 'Purpose', value: values.purpose.trim() || 'Not given' },
                ...(values.invitees.length
                  ? [{ label: 'Invited', value: values.invitees.map((person) => person.full_name).join(', '), wide: true }]
                  : []),
              ]}
            />
            <FormError error={error} />
          </div>
        )}
      </Modal>
    </Card>
  )
}

/** One study room: its details, its schedule for a day, and the booking form. */
export default function RoomDetailPage() {
  const { id } = useParams()
  // One shared instance: the form changes the time, the schedule follows it.
  const booking = useBookingWindow('room-window', 'room')
  const { window, end, bookable } = booking
  const room = useApiQuery(() => roomService.get(id), [id])
  // Polled so a booking made by someone else appears on the schedule.
  const schedule = useApiQuery(() => roomService.schedule(id, window.date), [id, window.date], {
    interval: POLL.availability, keepPrevious: true, enabled: Boolean(window.date),
  })

  return (
    <QueryBoundary query={room} loadingLabel="Loading room...">
      {(data) => {
        const status = RESOURCE_STATUS[data.status]
        return (
          <>
            <PageHeader
              back={{ to: '/rooms', label: 'All study rooms' }}
              title={data.name}
              description={`Room ${data.code}`}
              actions={<Badge tone={status.tone} dot>{status.label}</Badge>}
            />
            <div className="split split--wide-side">
              <div className="stack">
                <Card title="About this room">
                  <div className="stack">
                    <dl className="room-facts">
                      <div className="room-fact">
                        <MapPin size={18} aria-hidden="true" />
                        <div><dt>Location</dt><dd>{data.floor_detail.name}</dd></div>
                      </div>
                      <div className="room-fact">
                        <Users size={18} aria-hidden="true" />
                        <div><dt>Capacity</dt><dd>{data.capacity} people</dd></div>
                      </div>
                      <div className="room-fact">
                        <Users size={18} aria-hidden="true" />
                        <div><dt>Minimum group</dt><dd>{data.min_occupancy} {data.min_occupancy === 1 ? 'person' : 'people'}</dd></div>
                      </div>
                    </dl>
                    {data.description && <p className="soft">{data.description}</p>}
                    {data.facility_details.length > 0 && (
                      <div className="stack-sm">
                        <p className="field__label">Facilities</p>
                        <div className="chips">
                          {data.facility_details.map((facility) => (
                            <span key={facility.id} className="chip">{facility.name}</span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </Card>

                <Card
                  title="Schedule"
                  subtitle={window.date ? formatDate(window.date) : undefined}
                >
                  <QueryBoundary query={schedule} compact loadingLabel="Loading schedule...">
                    {(day) => (
                      <div className="stack-sm">
                        <DayTimeline schedule={day} selection={bookable ? { start: window.start, end } : null} />
                        {bookable && (
                          <p className="tiny muted">
                            The outlined area is the time you selected ({formatTimeRange(window.start, end)}).
                          </p>
                        )}
                      </div>
                    )}
                  </QueryBoundary>
                </Card>
              </div>

              <BookingForm room={data} booking={booking} schedule={schedule.data} onBooked={schedule.refetch} />
            </div>
          </>
        )
      }}
    </QueryBoundary>
  )
}
