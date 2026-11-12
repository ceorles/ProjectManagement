import { useState } from 'react'
import { CalendarCheck, Clock, GraduationCap, UserX } from 'lucide-react'
import Card from '../../components/common/Card'
import { EmptyState, QueryBoundary } from '../../components/common/Feedback'
import PageHeader from '../../components/common/PageHeader'
import Tabs from '../../components/common/Tabs'
import ColumnChart from '../../components/dashboard/ColumnChart'
import { BarList, StatCard } from '../../components/dashboard/Widgets'
import '../../components/dashboard/dashboard.css'
import { useApiQuery } from '../../hooks/useApiQuery'
import { reportService } from '../../services'
import { RESOURCE_SERIES, SINGLE_SERIES, toDailySeries } from '../../utils/charts'
import { formatDate, formatTime } from '../../utils/datetime'

const PERIODS = [
  { value: 7, label: '7 days' },
  { value: 14, label: '14 days' },
  { value: 30, label: '30 days' },
  { value: 90, label: '90 days' },
]

/** Usage report for a chosen period. Available to librarians and admins. */
export default function ReportsPage() {
  const [days, setDays] = useState(30)
  const query = useApiQuery(() => reportService.usage(days), [days], { keepPrevious: true })

  return (
    <>
      <PageHeader
        title="Reports"
        description="How seats and study rooms are being used."
        actions={<Tabs tabs={PERIODS} value={days} onChange={setDays} label="Period" />}
      />

      <QueryBoundary query={query} loadingLabel="Preparing the report...">
        {(data) => {
          const { totals } = data
          if (totals.total === 0) {
            return (
              <div className="card">
                <EmptyState icon={CalendarCheck} title="No reservations in this period"
                  description="Choose a longer period, or come back once students start booking." />
              </div>
            )
          }
          return (
            <div className="stack-lg">
              <p className="muted small">
                {formatDate(data.range.from)} to {formatDate(data.range.to)}
              </p>
              <div className="stat-grid">
                <StatCard icon={CalendarCheck} label="Reservations" value={totals.total}
                  hint={`${totals.seat} seats · ${totals.room} rooms`} />
                <StatCard icon={GraduationCap} label="Students served" value={totals.unique_students} tone="green" />
                <StatCard icon={Clock} label="Hours used" value={totals.hours_used} tone="yellow"
                  hint={`${totals.hours_booked} hours booked`} />
                <StatCard icon={UserX} label="No-show rate" value={`${totals.no_show_rate}%`}
                  tone={totals.no_show_rate > 10 ? 'red' : 'gray'}
                  hint={`${totals.cancellation_rate}% cancelled`} />
              </div>

              <Card title="Reservations per day" subtitle="By what was reserved">
                <ColumnChart data={toDailySeries(data.daily)} series={RESOURCE_SERIES} caption="Date" />
              </Card>

              <div className="grid-2">
                <Card title="Busiest start times" subtitle="When reservations begin (cancelled ones excluded)">
                  <ColumnChart
                    height={180} caption="Start time" series={SINGLE_SERIES}
                    data={data.by_hour.map((item) => ({
                      label: formatTime(`${item.hour}:00`).replace(':00', ''),
                      title: `${formatTime(`${item.hour}:00`)} - ${formatTime(`${item.hour}:59`)}`,
                      values: { count: item.count },
                    }))}
                  />
                </Card>
                <Card title="Busiest days of the week" subtitle="Cancelled reservations excluded">
                  <ColumnChart
                    height={180} caption="Day" series={SINGLE_SERIES}
                    data={data.by_weekday.map((item) => ({
                      label: item.label, title: item.label, values: { count: item.count },
                    }))}
                  />
                </Card>
              </div>

              <div className="grid-3">
                <Card title="Most-used seats"><BarList items={data.top_seats} /></Card>
                <Card title="Most-used rooms"><BarList items={data.top_rooms} /></Card>
                <Card title="Seat use by zone"><BarList items={data.by_zone} /></Card>
              </div>

              <Card title="Outcomes" subtitle="What happened to the reservations in this period">
                <div className="stat-grid">
                  {[
                    ['Completed', totals.completed, `${totals.completion_rate}%`],
                    ['Cancelled', totals.cancelled, `${totals.cancellation_rate}%`],
                    ['No-show', totals.no_show, `${totals.no_show_rate}%`],
                    ['Still active', totals.confirmed + totals.checked_in, 'Confirmed or checked in'],
                  ].map(([label, value, hint]) => (
                    <div key={label} className="rate">
                      <p className="rate__value">{value}</p>
                      <p className="rate__label">{label} · {hint}</p>
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          )
        }}
      </QueryBoundary>
    </>
  )
}
