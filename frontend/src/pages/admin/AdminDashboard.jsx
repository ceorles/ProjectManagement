import {
  Armchair, CalendarCheck, CalendarClock, ChartColumn, DoorOpen, GraduationCap, Users,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import Button from '../../components/common/Button'
import Card from '../../components/common/Card'
import { QueryBoundary } from '../../components/common/Feedback'
import PageHeader from '../../components/common/PageHeader'
import ColumnChart from '../../components/dashboard/ColumnChart'
import { ActivityFeed, BarList, OccupancyMeter, StatCard } from '../../components/dashboard/Widgets'
import '../../components/dashboard/dashboard.css'
import { POLL } from '../../config'
import { useApiQuery } from '../../hooks/useApiQuery'
import { reportService } from '../../services'
import { RESOURCE_SERIES, toDailySeries } from '../../utils/charts'

/** System-wide overview for the administrator. */
export default function AdminDashboard() {
  const query = useApiQuery(reportService.adminDashboard, [], {
    interval: POLL.dashboard, keepPrevious: true,
  })

  return (
    <>
      <PageHeader
        title="Admin Dashboard"
        description="The whole library at a glance: accounts, resources, usage and recent activity."
        actions={<Button to="/reports" variant="secondary" icon={ChartColumn}>Full reports</Button>}
      />

      <QueryBoundary query={query} loadingLabel="Loading the overview...">
        {(data) => (
          <div className="stack-lg">
            <div className="stat-grid stat-grid--3">
              <StatCard icon={GraduationCap} label="Students" value={data.totals.students} to="/admin/users" />
              <StatCard icon={Users} label="Librarians" value={data.totals.librarians} to="/admin/users" />
              <StatCard icon={CalendarClock} label="Active reservations" value={data.totals.active_reservations}
                tone="green" to="/manage/reservations" hint="Confirmed or checked in" />
              <StatCard icon={Armchair} label="Seats" value={data.totals.seats} to="/manage/seats" />
              <StatCard icon={DoorOpen} label="Study rooms" value={data.totals.rooms} to="/manage/rooms" />
              <StatCard icon={CalendarCheck} label="Reservations today" value={data.totals.reservations_today}
                tone="yellow" to="/manage/reservations" />
            </div>

            <div className="grid-2">
              <Card><OccupancyMeter title="Seats right now" data={data.occupancy.seats} to="/seats" /></Card>
              <Card><OccupancyMeter title="Study rooms right now" data={data.occupancy.rooms} to="/rooms" /></Card>
            </div>

            <div className="split">
              <div className="stack">
                <Card title="Reservations per day" subtitle="Last 14 days, by what was reserved">
                  <ColumnChart data={toDailySeries(data.trend)} series={RESOURCE_SERIES} caption="Date" />
                </Card>
                <div className="grid-2">
                  <Card title="Most-used seats" subtitle="Last 30 days">
                    <BarList items={data.top_seats} />
                  </Card>
                  <Card title="Most-used rooms" subtitle="Last 30 days">
                    <BarList items={data.top_rooms} />
                  </Card>
                </div>
              </div>

              <div className="stack">
                <Card title="Last 30 days" subtitle={`${data.last_30_days.total} reservations`}>
                  <div className="rate-list">
                    <div className="rate">
                      <p className="rate__value">{data.last_30_days.completion_rate}%</p>
                      <p className="rate__label">Completed</p>
                    </div>
                    <div className="rate">
                      <p className="rate__value">{data.last_30_days.cancellation_rate}%</p>
                      <p className="rate__label">Cancelled</p>
                    </div>
                    <div className="rate">
                      <p className="rate__value">{data.last_30_days.no_show_rate}%</p>
                      <p className="rate__label">No-show</p>
                    </div>
                  </div>
                </Card>
                <Card title="Recent activity"
                  action={<Link to="/admin/activity" className="small strong">View log</Link>}>
                  <ActivityFeed items={data.recent_activity} />
                </Card>
              </div>
            </div>
          </div>
        )}
      </QueryBoundary>
    </>
  )
}
