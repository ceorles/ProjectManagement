import { useState } from 'react'
import { Armchair, CalendarCheck, DoorOpen, History } from 'lucide-react'
import Button from '../../components/common/Button'
import { EmptyState, QueryBoundary } from '../../components/common/Feedback'
import PageHeader from '../../components/common/PageHeader'
import Pagination from '../../components/common/Pagination'
import Tabs from '../../components/common/Tabs'
import ReservationCard from '../../components/reservations/ReservationCard'
import '../../components/reservations/reservations.css'
import { POLL } from '../../config'
import { useApiQuery } from '../../hooks/useApiQuery'
import { reservationService } from '../../services'

const TABS = [
  { value: 'active', label: 'Upcoming', icon: CalendarCheck },
  { value: 'history', label: 'History', icon: History },
]

const TYPES = [
  { value: '', label: 'All' },
  { value: 'seat', label: 'Seats' },
  { value: 'room', label: 'Rooms' },
]

/** The student's own reservations: what is coming up, and what has passed. */
export default function MyReservationsPage() {
  const [scope, setScope] = useState('active')
  const [type, setType] = useState('')
  const [page, setPage] = useState(1)

  const query = useApiQuery(
    () => reservationService.list({
      scope, resource_type: type, page,
      // Upcoming: soonest first. History: most recent first.
      ordering: scope === 'active' ? 'start_at' : '-start_at',
    }),
    [scope, type, page],
    { interval: POLL.reservations, keepPrevious: true },
  )

  const change = (setter) => (value) => {
    setter(value)
    setPage(1)
  }

  return (
    <>
      <PageHeader
        title="My Reservations"
        description="Check in, cancel, or look back at your past reservations."
        actions={(
          <>
            <Button to="/seats" icon={Armchair}>Reserve a seat</Button>
            <Button to="/rooms" variant="secondary" icon={DoorOpen}>Reserve a room</Button>
          </>
        )}
      />

      <div className="between" style={{ flexWrap: 'wrap', marginBottom: 16 }}>
        <Tabs tabs={TABS} value={scope} onChange={change(setScope)} label="Reservations" />
        <Tabs tabs={TYPES} value={type} onChange={change(setType)} label="Type" />
      </div>

      <QueryBoundary query={query} loadingLabel="Loading your reservations...">
        {(data) => (data.results.length === 0 ? (
          <div className="card">
            <EmptyState
              icon={scope === 'active' ? CalendarCheck : History}
              title={scope === 'active' ? 'No upcoming reservations' : 'No past reservations yet'}
              description={scope === 'active'
                ? 'Reserve a seat or a study room and it will appear here.'
                : 'Completed, cancelled and missed reservations are listed here.'}
              action={scope === 'active' && <Button to="/seats" icon={Armchair}>Reserve a seat</Button>}
            />
          </div>
        ) : (
          <>
            <div className="reservation-list">
              {data.results.map((reservation) => (
                <ReservationCard key={reservation.id} reservation={reservation} onChanged={query.refetch} />
              ))}
            </div>
            <Pagination page={page} count={data.count} onChange={setPage} />
          </>
        ))}
      </QueryBoundary>
    </>
  )
}
