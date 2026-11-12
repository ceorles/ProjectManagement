import { Armchair, CircleAlert, Plug, Monitor } from 'lucide-react'
import Badge from '../../components/common/Badge'
import Card from '../../components/common/Card'
import { EmptyState, QueryBoundary, Spinner } from '../../components/common/Feedback'
import PageHeader from '../../components/common/PageHeader'
import Tabs from '../../components/common/Tabs'
import BookingWindowPicker from '../../components/reservations/BookingWindowPicker'
import SeatDialog from '../../components/seats/SeatDialog'
import SeatMap, { SeatLegend } from '../../components/seats/SeatMap'
import '../../components/seats/seats.css'
import '../../components/reservations/reservations.css'
import { POLL } from '../../config'
import { useApiQuery } from '../../hooks/useApiQuery'
import { useAuth } from '../../hooks/useAuth'
import { useBookingWindow } from '../../hooks/useBookingWindow'
import { useLibrary } from '../../hooks/useLibrary'
import { seatService } from '../../services'
import { formatDate, formatTimeRange } from '../../utils/datetime'

const FILTERS = [
  { key: 'has_power_outlet', label: 'Power outlet', icon: Plug },
  { key: 'has_computer', label: 'Computer', icon: Monitor },
]

/**
 * Seat map for a chosen time. Students use it to reserve a seat. Staff see
 * the same map with who is sitting where, and can book for a student.
 */
export default function SeatBookingPage() {
  const { isStaff } = useAuth()
  const { floors } = useLibrary()
  const booking = useBookingWindow('seat-booking', 'seat', {
    floor: null, seatId: null, student: null, features: [],
  })
  const { values, setField, window, setWindow, params, end } = booking
  const floor = floors.some((item) => item.id === values.floor) ? values.floor : floors[0]?.id

  // Refreshed every few seconds, so a seat someone else just took (or
  // released) changes colour without reloading the page.
  const availability = useApiQuery(
    () => seatService.availability({ ...params, floor }),
    [params?.date, params?.start, params?.end, floor],
    { interval: POLL.availability, enabled: Boolean(params && floor), keepPrevious: true },
  )

  const zones = availability.data?.zones ?? []
  const selected = values.seatId
    ? zones.flatMap((zone) => zone.seats.map((seat) => ({ seat, zone })))
      .find((entry) => entry.seat.id === values.seatId)
    : null
  const dimmed = values.features.length
    ? (seat) => !values.features.every((feature) => seat[feature])
    : undefined

  const toggleFeature = (key) => setField(
    'features',
    values.features.includes(key)
      ? values.features.filter((feature) => feature !== key)
      : [...values.features, key],
  )

  return (
    <>
      <PageHeader
        title={isStaff ? 'Seat Map' : 'Reserve a Seat'}
        description={isStaff
          ? 'Live view of every seat. Select a free seat to reserve it for a student.'
          : 'Choose when you want to study, then pick a free seat on the map.'}
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
                      <strong>{data.summary.available}</strong> of {data.summary.total} seats available
                    </p>
                  </div>
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
                        zone={zone} selectedId={values.seatId} dimmed={dimmed}
                        onSelect={(seat) => setField('seatId', seat.id)}
                      />
                    </section>
                  ))}
                </div>
              )}
            </QueryBoundary>
          )}
        </Card>
      </div>

      {selected && params && (
        <SeatDialog
          key={selected.seat.id}
          seat={selected.seat} zone={selected.zone} booking={booking}
          bookable={availability.data.bookable} bookableReason={availability.data.bookable_reason}
          student={values.student} onStudentChange={(student) => setField('student', student)}
          onClose={() => setField('seatId', null)}
          onBooked={() => availability.refetch()}
        />
      )}
    </>
  )
}
