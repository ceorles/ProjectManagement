import { CalendarCheck, CalendarClock, Hourglass, ScanLine, UserCheck, UserX } from 'lucide-react'
import { Link } from 'react-router-dom'
import Button from '../../components/common/Button'
import Card from '../../components/common/Card'
import { EmptyState, QueryBoundary } from '../../components/common/Feedback'
import PageHeader from '../../components/common/PageHeader'
import { ActivityFeed, OccupancyMeter, StatCard } from '../../components/dashboard/Widgets'
import '../../components/dashboard/dashboard.css'
import ReservationCard from '../../components/reservations/ReservationCard'
import '../../components/reservations/reservations.css'
import { POLL } from '../../config'
import { useApiQuery } from '../../hooks/useApiQuery'
import { useLibrary } from '../../hooks/useLibrary'
import { reportService } from '../../services'
import { formatDate } from '../../utils/datetime'

function ReservationList({ items, onChanged, empty }) {
  if (items.length === 0) return <EmptyState compact icon={empty.icon} title={empty.title} description={empty.description} />
  return (
    <div className="reservation-list">
      {items.map((reservation) => (
        <ReservationCard key={reservation.id} reservation={reservation} onChanged={onChanged} showStudent />
      ))}
    </div>
  )
}

/** The librarian's working view of today. Refreshes on its own. */
export default function LibrarianDashboard() {
  const { now } = useLibrary()
  const query = useApiQuery(reportService.staffDashboard, [], {
    interval: POLL.dashboard, keepPrevious: true,
  })

  return (
    <>
      <PageHeader
        title="Today at the library"
        description={formatDate(now.date, { weekday: 'long', month: 'long' })}
        actions={<Button to="/desk" icon={ScanLine}>Check-in desk</Button>}
      />

      <QueryBoundary query={query} loadingLabel="Loading today's activity...">
        {(data) => (
          <div className="stack-lg">
            <div className="stat-grid">
              <StatCard icon={CalendarCheck} label="Reservations today" value={data.today.total}
                to="/manage/reservations" />
              <StatCard icon={UserCheck} label="Checked in now" tone="green"
                value={data.occupancy.seats.occupied + data.occupancy.rooms.occupied} />
              <StatCard icon={Hourglass} label="Awaiting check-in" tone="yellow"
                value={data.awaiting_check_in.length} hint="Started, nobody arrived yet" />
              <StatCard icon={UserX} label="No-shows today" value={data.today.no_show}
                tone={data.today.no_show ? 'red' : 'gray'} />
            </div>

            <div className="grid-2">
              <Card><OccupancyMeter title="Seats right now" data={data.occupancy.seats} to="/seats" /></Card>
              <Card><OccupancyMeter title="Study rooms right now" data={data.occupancy.rooms} to="/rooms" /></Card>
            </div>

            <div className="split">
              <div className="stack">
                <Card
                  title="Awaiting check-in" icon={Hourglass}
                  subtitle="These reservations have started. Check the student in, or they are released automatically."
                >
                  <ReservationList
                    items={data.awaiting_check_in} onChanged={query.refetch}
                    empty={{ icon: UserCheck, title: 'Nobody is overdue', description: 'Everyone whose reservation has started is checked in.' }}
                  />
                </Card>
                <Card title="Checked in now" icon={UserCheck}>
                  <ReservationList
                    items={data.checked_in} onChanged={query.refetch}
                    empty={{ icon: UserCheck, title: 'No one is checked in', description: 'Students who check in appear here.' }}
                  />
                </Card>
                <Card title="Coming up today" icon={CalendarClock}
                  action={<Link to="/manage/reservations" className="small strong">All reservations</Link>}>
                  <ReservationList
                    items={data.upcoming} onChanged={query.refetch}
                    empty={{ icon: CalendarClock, title: 'Nothing else scheduled today', description: 'New reservations for today appear here.' }}
                  />
                </Card>
              </div>
              <Card title="Recent reservation activity">
                <ActivityFeed items={data.recent_activity} />
              </Card>
            </div>
          </div>
        )}
      </QueryBoundary>
    </>
  )
}
