import { useState } from 'react'
import { Armchair, CircleAlert, Plug, Monitor } from 'lucide-react'
import Badge from '../../components/common/Badge'
import Button from '../../components/common/Button'
import Card from '../../components/common/Card'
import { EmptyState, QueryBoundary, Spinner } from '../../components/common/Feedback'
import PageHeader from '../../components/common/PageHeader'
import Tabs from '../../components/common/Tabs'
import BookingWindowPicker from '../../components/reservations/BookingWindowPicker'
import SeatRequestDialog, { MAX_SEATS, SeatInfoDialog } from '../../components/seats/SeatDialog'
import SeatMap, { SeatLegend } from '../../components/seats/SeatMap'
import '../../components/seats/seats.css'
import '../../components/reservations/reservations.css'
import { POLL } from '../../config'
import { useApiQuery } from '../../hooks/useApiQuery'
import { useAuth } from '../../hooks/useAuth'
import { useBookingWindow } from '../../hooks/useBookingWindow'
import { useLibrary } from '../../hooks/useLibrary'
import { useToast } from '../../hooks/useToast'
import { seatService } from '../../services'
import { formatDate, formatTimeRange } from '../../utils/datetime'

const FILTERS = [
  { key: 'has_power_outlet', label: 'Power outlet', icon: Plug },
  { key: 'has_computer', label: 'Computer', icon: Monitor },
]

/**
 * Seat map for a chosen time. Students pick one seat, a few seats, a whole
 * table or one computer, and send a request to the librarian. Staff see the
 * same map with who is sitting where; librarians can book for a student.
 */
export default function SeatBookingPage() {
  const { isStaff, canManageReservations } = useAuth()
  const { floors } = useLibrary()
  const toast = useToast()
  const booking = useBookingWindow('seat-booking', 'seat', {
    floor: null, seatIds: [], reason: '', student: null, features: [],
  })
  const { values, setValues, setField, window, setWindow, params, end } = booking
  const floor = floors.some((item) => item.id === values.floor) ? values.floor : floors[0]?.id
  const [infoSeatId, setInfoSeatId] = useState(null)
  // The seats under review are frozen when the dialog opens, so the dialog
  // keeps showing them while the map behind it refreshes.
  const [review, setReview] = useState(null)
  // Student assistants watch the map but do not make reservations.
  const canPick = !isStaff || canManageReservations

  // Refreshed every few seconds, so a seat someone else just requested (or
  // released) changes colour without reloading the page.
  const availability = useApiQuery(
    () => seatService.availability({ ...params, floor }),
    [params?.date, params?.start, params?.end, floor],
    { interval: POLL.availability, enabled: Boolean(params && floor), keepPrevious: true },
  )

  const zones = availability.data?.zones ?? []
  const entries = zones.flatMap((zone) => zone.seats.map((seat) => ({ seat, zone })))
  // A picked seat that someone else has taken meanwhile simply drops out.
  const selected = entries.filter(
    (entry) => values.seatIds.includes(entry.seat.id) && entry.seat.state === 'available')
  const selectedIds = selected.map((entry) => entry.seat.id)
  const info = entries.find((entry) => entry.seat.id === infoSeatId)
  const dimmed = values.features.length
    ? (seat) => !values.features.every((feature) => seat[feature])
    : undefined

  const pick = (ids) => setValues((current) => ({ ...current, seatIds: ids }))

  const onSeat = (seat, zone) => {
    if (seat.state !== 'available' || !canPick) {
      setInfoSeatId(seat.id)
      return
    }
    if (selectedIds.includes(seat.id)) {
      pick(selectedIds.filter((id) => id !== seat.id))
      return
    }
    const sameArea = selected.length > 0 && selected[0].zone.id === zone.id
    const withComputer = seat.has_computer || selected.some((entry) => entry.seat.has_computer)
    if (!sameArea || withComputer) {
      // A computer is requested on its own, and one request stays in one area.
      if (selected.length > 0 && withComputer) {
        toast.info('A computer is reserved on its own: one computer per request.')
      }
      pick([seat.id])
    } else if (selected.length >= MAX_SEATS) {
      toast.info(`One request can cover at most ${MAX_SEATS} seats (one table).`)
    } else {
      pick([...selectedIds, seat.id])
    }
  }

  const onTable = (table) => {
    const ids = table.seats.map((seat) => seat.id)
    const already = ids.length === selectedIds.length && ids.every((id) => selectedIds.includes(id))
    pick(already ? [] : ids)
  }

  const toggleFeature = (key) => setField(
    'features',
    values.features.includes(key)
      ? values.features.filter((feature) => feature !== key)
      : [...values.features, key],
  )

  const closeReview = () => {
    // After a successful request the selection and reason are done with.
    if (review?.sent) setValues((current) => ({ ...current, seatIds: [], reason: '' }))
    setReview(null)
  }

  const picked = selected.map((entry) => entry.seat)
  const pickedLabel = picked.length === MAX_SEATS && picked.every(
    (seat) => seat.table_number != null && seat.table_number === picked[0].table_number)
    ? `Table ${picked[0].table_number} (all ${MAX_SEATS} seats)`
    : picked.map((seat) => seat.number).join(', ')

  return (
    <>
      <PageHeader
        title={isStaff ? 'Seat Map' : 'Reserve a Seat'}
        description={isStaff
          ? (canManageReservations
            ? 'Live view of every seat. Select free seats to reserve them for a student.'
            : 'Live view of every seat and computer, and who is using them.')
          : 'Choose when you want to study, then pick your seat, a table for your group, or a computer.'}
      />

      <div className="stack">
        <Card title="1. When do you need it?" icon={Armchair}>
          <BookingWindowPicker resourceType="seat" window={window} onChange={setWindow} />
        </Card>

        <Card
          title="2. Pick a seat"
          subtitle={params
            ? `${formatDate(window.date, { year: undefined })} · ${formatTimeRange(window.start, end)}`
            : undefined}
          action={availability.loading && availability.data ? <Spinner size={18} /> : null}
          padded={false}
        >
          <div className="seat-toolbar">
            {floors.length > 1 && (
              <Tabs
                label="Floor" value={floor} onChange={(value) => setField('floor', value)}
                tabs={floors.map((item) => ({ value: item.id, label: item.name }))}
              />
            )}
            <div className="row-wrap">
              <span className="small muted">Highlight seats with:</span>
              {FILTERS.map((filter) => (
                <button
                  key={filter.key} type="button" aria-pressed={values.features.includes(filter.key)}
                  className={`filter-chip ${values.features.includes(filter.key) ? 'is-active' : ''}`}
                  onClick={() => toggleFeature(filter.key)}
                >
                  <filter.icon size={14} aria-hidden="true" /> {filter.label}
                </button>
              ))}
            </div>
          </div>

          {!params ? (
            <EmptyState icon={Armchair} title="Nothing to show yet"
              description="There is no bookable time in the coming days." />
          ) : (
            <QueryBoundary query={availability} loadingLabel="Loading the seat map...">
              {(data) => (
                <div className="seat-zones">
                  {!data.bookable && (
                    <p className="notice notice--warning seat-zones__notice">
                      <CircleAlert size={16} aria-hidden="true" /> {data.bookable_reason}
                    </p>
                  )}
                  <div className="seat-summary">
                    <SeatLegend staff={isStaff} />
                    <p className="small soft">
                      <strong>{data.summary.available}</strong> of {data.summary.total} available
                    </p>
                  </div>
                  {canPick && (
                    <p className="small muted seat-zones__hint">
                      Tap a seat to select it (up to {MAX_SEATS}), or tap a table&apos;s name to select
                      the whole table. Computers are reserved one at a time.
                    </p>
                  )}
                  {data.zones.length === 0 && (
                    <EmptyState icon={Armchair} title="No seats on this floor"
                      description="Choose another floor to see its seats." />
                  )}
                  {data.zones.map((zone) => (
                    <section key={zone.id} className="seat-zone">
                      <header className="seat-zone__header">
                        <div>
                          <h3>{zone.name}</h3>
                          {zone.description && <p className="muted small">{zone.description}</p>}
                        </div>
                        <div className="row-wrap">
                          <Badge tone="blue">{zone.zone_type_label}</Badge>
                          <Badge tone={zone.summary.available ? 'green' : 'gray'}>
                            {zone.summary.available} free
                          </Badge>
                        </div>
                      </header>
                      <SeatMap
                        zone={zone} selectedIds={selectedIds} dimmed={dimmed}
                        onSelect={onSeat} onSelectTable={canPick ? onTable : undefined}
                      />
                    </section>
                  ))}

                  {picked.length > 0 && !review && (
                    <div className="selection-bar" role="status">
                      <p className="selection-bar__text">
                        <strong>
                          {picked.length} {picked[0].has_computer ? 'computer' : picked.length === 1 ? 'seat' : 'seats'} selected
                        </strong>
                        <span className="truncate">{pickedLabel}</span>
                      </p>
                      <div className="row-sm">
                        <Button variant="secondary" size="sm" onClick={() => pick([])}>Clear</Button>
                        <Button size="sm" onClick={() => setReview({ entries: selected, sent: false })}>
                          {canManageReservations ? 'Reserve for a student' : 'Review request'}
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </QueryBoundary>
          )}
        </Card>
      </div>

      {review && params && (
        <SeatRequestDialog
          entries={review.entries} booking={booking}
          bookable={availability.data.bookable} bookableReason={availability.data.bookable_reason}
          reason={values.reason} onReasonChange={(value) => setField('reason', value)}
          student={values.student} onStudentChange={(student) => setField('student', student)}
          onClose={closeReview}
          onBooked={(reservation) => {
            if (reservation) setReview((current) => ({ ...current, sent: true }))
            availability.refetch()
          }}
        />
      )}
      {info && params && !review && (
        <SeatInfoDialog
          key={info.seat.id} seat={info.seat} zone={info.zone} date={window.date}
          onClose={() => setInfoSeatId(null)}
        />
      )}
    </>
  )
}
