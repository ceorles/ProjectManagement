import { useState } from 'react'
import { ClipboardList, Plus } from 'lucide-react'
import { Link } from 'react-router-dom'
import { StatusBadge } from '../../components/common/Badge'
import Button from '../../components/common/Button'
import DataTable from '../../components/common/DataTable'
import { EmptyState, QueryBoundary } from '../../components/common/Feedback'
import { SearchInput } from '../../components/common/FormControls'
import PageHeader from '../../components/common/PageHeader'
import Pagination from '../../components/common/Pagination'
import ReservationActions from '../../components/reservations/ReservationActions'
import '../../components/reservations/reservations.css'
import { POLL } from '../../config'
import { useApiQuery } from '../../hooks/useApiQuery'
import { useDebounce } from '../../hooks/useDebounce'
import { useFormDraft } from '../../hooks/useFormDraft'
import { useLibrary } from '../../hooks/useLibrary'
import { reservationService } from '../../services'
import { RESERVATION_STATUS } from '../../utils/constants'
import { formatFriendlyDate, formatTimeRange } from '../../utils/datetime'

const NO_FILTERS = { search: '', date: '', status: '', type: '' }

/** Every reservation in the system, searchable and filterable. Staff only. */
export default function ManageReservationsPage() {
  const { now } = useLibrary()
  // Filters are remembered, so a refresh shows the same list.
  const { values: filters, setField, setValues } = useFormDraft('reservation-filters', NO_FILTERS)
  const [page, setPage] = useState(1)
  const search = useDebounce(filters.search.trim())

  const query = useApiQuery(
    () => reservationService.list({
      search, date: filters.date, status: filters.status, resource_type: filters.type,
      page, ordering: '-start_at',
    }),
    [search, filters.date, filters.status, filters.type, page],
    { interval: POLL.reservations, keepPrevious: true },
  )

  const change = (name) => (eventOrValue) => {
    setField(name, eventOrValue?.target ? eventOrValue.target.value : eventOrValue)
    setPage(1)
  }
  const filtered = Object.values(filters).some(Boolean)

  const columns = [
    {
      key: 'resource', header: 'Reservation', primary: true,
      render: (row) => (
        <>
          <Link to={`/reservations/${row.id}`} className="strong">{row.resource.name}</Link>
          <span className="muted small"> · {row.resource.location}</span>
        </>
      ),
    },
    {
      key: 'student', header: 'Student',
      render: (row) => (
        <span>
          {row.student.full_name}
          <span className="muted small"> · {row.student.student_id}</span>
        </span>
      ),
    },
    {
      key: 'when', header: 'When',
      render: (row) => (
        <span className="nowrap">
          {formatFriendlyDate(row.date, now.date)}, {formatTimeRange(row.start_time, row.end_time)}
        </span>
      ),
    },
    { key: 'code', header: 'Code', render: (row) => <span className="mono small">{row.code}</span> },
    { key: 'status', header: 'Status', render: (row) => <StatusBadge status={row.status} /> },
    {
      key: 'actions', header: 'Actions',
      render: (row) => <ReservationActions reservation={row} onChanged={query.refetch} />,
    },
  ]

  return (
    <>
      <PageHeader
        title="Reservations"
        description="Monitor, check in, cancel and review every reservation."
        actions={<Button to="/seats" icon={Plus}>New reservation</Button>}
      />

      <section className="card">
        <div className="toolbar">
          <SearchInput value={filters.search} onChange={change('search')}
            placeholder="Search student, ID, code, seat or room" />
          <input type="date" className="input" aria-label="Date" value={filters.date}
            onChange={change('date')} />
          <select className="input select" aria-label="Status" value={filters.status}
            onChange={change('status')}>
            <option value="">All statuses</option>
            {Object.entries(RESERVATION_STATUS).map(([value, meta]) => (
              <option key={value} value={value}>{meta.label}</option>
            ))}
          </select>
          <select className="input select" aria-label="Type" value={filters.type} onChange={change('type')}>
            <option value="">Seats and rooms</option>
            <option value="seat">Seats</option>
            <option value="room">Study rooms</option>
          </select>
          {filtered && (
            <Button variant="ghost" size="sm" onClick={() => { setValues(NO_FILTERS); setPage(1) }}>
              Clear filters
            </Button>
          )}
        </div>

        <QueryBoundary query={query} loadingLabel="Loading reservations...">
          {(data) => (data.results.length === 0 ? (
            <EmptyState
              icon={ClipboardList}
              title={filtered ? 'No reservations match these filters' : 'No reservations yet'}
              description={filtered
                ? 'Try a different search, date or status.'
                : 'Reservations made by students and staff appear here.'}
            />
          ) : (
            <>
              <DataTable columns={columns} rows={data.results} caption="Reservations" />
              <Pagination page={page} count={data.count} onChange={setPage} />
            </>
          ))}
        </QueryBoundary>
      </section>
    </>
  )
}
