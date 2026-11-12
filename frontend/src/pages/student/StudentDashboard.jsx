import {
  Armchair, CalendarCheck, CircleAlert, Clock, DoorOpen, GraduationCap, UserX,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import Button from '../../components/common/Button'
import Card from '../../components/common/Card'
import { EmptyState, QueryBoundary } from '../../components/common/Feedback'
import { OccupancyMeter, StatCard } from '../../components/dashboard/Widgets'
import '../../components/dashboard/dashboard.css'
import ReservationCard from '../../components/reservations/ReservationCard'
import '../../components/reservations/reservations.css'
import { POLL } from '../../config'
import { useApiQuery } from '../../hooks/useApiQuery'
import { useAuth } from '../../hooks/useAuth'
import { useLibrary } from '../../hooks/useLibrary'
import { reportService } from '../../services'
import { formatTime, greeting } from '../../utils/datetime'

function libraryLine(today) {
  if (today.openNow) return `The library is open until ${formatTime(today.closesAt)} today.`
  if (today.isOpen) return `The library is closed right now. Today's hours: ${formatTime(today.opensAt)} - ${formatTime(today.closesAt)}.`
  return `The library is closed today${today.reason && today.reason !== 'Closed' ? ` (${today.reason})` : ''}. You can still reserve for another day.`
}

function Standing({ limits }) {
  const activeShare = limits.active_reservations / limits.max_active_reservations
  const strikeShare = limits.no_show_limit ? limits.no_shows / limits.no_show_limit : 0
  return (
    <div className="standing">
      <div className="standing__row">
        <div className="between small">
          <span>Active reservations</span>
          <strong>{limits.active_reservations} of {limits.max_active_reservations}</strong>
        </div>
        <div className="standing__bar">
          <span className={`standing__fill ${activeShare >= 1 ? 'standing__fill--warning' : ''}`}
            style={{ width: `${Math.min(activeShare, 1) * 100}%` }} />
        </div>
      </div>
      {limits.no_show_limit > 0 && (
        <div className="standing__row">
          <div className="between small">
            <span>Missed reservations (last {limits.no_show_window_days} days)</span>
            <strong>{limits.no_shows} of {limits.no_show_limit}</strong>
          </div>
          <div className="standing__bar">
            <span
              className={`standing__fill ${strikeShare >= 1 ? 'standing__fill--danger' : strikeShare > 0 ? 'standing__fill--warning' : ''}`}
              style={{ width: `${Math.min(strikeShare, 1) * 100}%` }} />
          </div>
          <p className="tiny muted">
            Reaching the limit pauses new reservations. Cancel in advance if your plans change.
          </p>
        </div>
      )}
    </div>
  )
}

export default function StudentDashboard() {
  const { user } = useAuth()
  const { today, now } = useLibrary()
  const query = useApiQuery(reportService.studentDashboard, [], {
    interval: POLL.dashboard, keepPrevious: true,
  })

  return (
    <div className="stack-lg">
      <section className="welcome">
        <div>
          <h1>{greeting(now.minutes)}, {user.first_name}</h1>
          <p>{libraryLine(today)}</p>
        </div>
        <div className="welcome__actions">
          <Button to="/seats" variant="accent" icon={Armchair}>Reserve a seat</Button>
          <Button to="/rooms" variant="secondary" icon={DoorOpen}>Reserve a room</Button>
        </div>
      </section>

      <QueryBoundary query={query} loadingLabel="Loading your dashboard...">
        {(data) => (
          <>
            {data.limits.suspended && (
              <p className="notice notice--danger">
                <CircleAlert size={16} aria-hidden="true" />
                <span>
                  New reservations are paused because {data.limits.no_shows} reservations were missed
                  in the last {data.limits.no_show_window_days} days. Please see a librarian.
                </span>
              </p>
            )}

            {data.current && (
              <Card
                title={data.current.status === 'checked_in' ? 'You are checked in' : 'Ready for check-in'}
                subtitle={data.current.status === 'checked_in'
                  ? 'Check out when you leave so the place frees up for others.'
                  : 'Check in when you arrive, before the check-in period ends.'}
                icon={Clock}
              >
                <ReservationCard reservation={data.current} onChanged={query.refetch} />
              </Card>
            )}

            <div className="stat-grid">
              <StatCard icon={CalendarCheck} label="Upcoming" value={data.stats.upcoming} to="/reservations" />
              <StatCard icon={GraduationCap} label="Hours studied" value={data.stats.hours_studied} tone="yellow" />
              <StatCard icon={Armchair} label="Completed" value={data.stats.completed} tone="green" />
              <StatCard icon={UserX} label="Missed" value={data.stats.no_show} tone={data.stats.no_show ? 'red' : 'gray'} />
            </div>

            <div className="split">
              <div className="stack">
                <Card
                  title="Upcoming reservations"
                  action={<Link to="/reservations" className="small strong">View all</Link>}
                >
                  {data.upcoming.length === 0 ? (
                    <EmptyState
                      compact icon={CalendarCheck}
                      title={data.current ? 'Nothing else booked' : 'No upcoming reservations'}
                      description="Reserve a seat or a study room for your next study session."
                      action={<Button to="/seats" size="sm" icon={Armchair}>Reserve a seat</Button>}
                    />
                  ) : (
                    <div className="reservation-list">
                      {data.upcoming.map((reservation) => (
                        <ReservationCard key={reservation.id} reservation={reservation} onChanged={query.refetch} />
                      ))}
                    </div>
                  )}
                </Card>

                {data.recent.length > 0 && (
                  <Card
                    title="Recent history"
                    action={<Link to="/reservations" className="small strong">Full history</Link>}
                  >
                    <div className="reservation-list">
                      {data.recent.slice(0, 3).map((reservation) => (
                        <ReservationCard key={reservation.id} reservation={reservation} actions={false} />
                      ))}
                    </div>
                  </Card>
                )}
              </div>

              <div className="stack">
                <Card title="Available right now" subtitle="Updates automatically">
                  <div className="stack-lg">
                    <OccupancyMeter title="Seats" data={data.occupancy.seats} to="/seats" />
                    <hr className="divider" />
                    <OccupancyMeter title="Study rooms" data={data.occupancy.rooms} to="/rooms" />
                  </div>
                </Card>
                <Card title="Your booking standing">
                  <Standing limits={data.limits} />
                </Card>
              </div>
            </div>
          </>
        )}
      </QueryBoundary>
    </div>
  )
}
