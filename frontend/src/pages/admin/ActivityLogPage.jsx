import { useState } from 'react'
import { ScrollText } from 'lucide-react'
import Badge from '../../components/common/Badge'
import Button from '../../components/common/Button'
import DataTable from '../../components/common/DataTable'
import { EmptyState, QueryBoundary } from '../../components/common/Feedback'
import { SearchInput } from '../../components/common/FormControls'
import PageHeader from '../../components/common/PageHeader'
import Pagination from '../../components/common/Pagination'
import { POLL } from '../../config'
import { useApiQuery } from '../../hooks/useApiQuery'
import { useDebounce } from '../../hooks/useDebounce'
import { useLibrary } from '../../hooks/useLibrary'
import { activityService } from '../../services'
import { ACTIVITY_CATEGORIES, ROLES } from '../../utils/constants'
import { formatTimestamp } from '../../utils/datetime'

const TONES = { auth: 'gray', user: 'green', reservation: 'blue', resource: 'yellow', settings: 'orange' }
const NO_FILTERS = { search: '', category: '', date_from: '', date_to: '' }

/** Admin: the audit trail of everything done in the portal. */
export default function ActivityLogPage() {
  const { timeZone } = useLibrary()
  const [filters, setFilters] = useState(NO_FILTERS)
  const [page, setPage] = useState(1)
  const search = useDebounce(filters.search.trim())

  const query = useApiQuery(
    () => activityService.list({ ...filters, search, page }),
    [search, filters.category, filters.date_from, filters.date_to, page],
    { interval: POLL.dashboard, keepPrevious: true },
  )
  const change = (name) => (eventOrValue) => {
    const value = eventOrValue?.target ? eventOrValue.target.value : eventOrValue
    setFilters((current) => ({ ...current, [name]: value }))
    setPage(1)
  }
  const filtered = Object.values(filters).some(Boolean)

  const columns = [
    {
      key: 'description', header: 'Activity', primary: true,
      render: (entry) => entry.description,
    },
    {
      key: 'actor', header: 'By',
      render: (entry) => (
        <span>
          {entry.actor_name}
          {ROLES[entry.actor_role] && <span className="muted small"> · {ROLES[entry.actor_role]}</span>}
        </span>
      ),
    },
    {
      key: 'category', header: 'Area',
      render: (entry) => <Badge tone={TONES[entry.category]}>{ACTIVITY_CATEGORIES[entry.category]}</Badge>,
    },
    {
      key: 'created_at', header: 'When',
      render: (entry) => <span className="nowrap">{formatTimestamp(entry.created_at, timeZone)}</span>,
    },
  ]

  return (
    <>
      <PageHeader
        title="Activity Log"
        description="A record of sign-ins, reservations, and changes to accounts, resources and settings."
      />
      <section className="card">
        <div className="toolbar">
          <SearchInput value={filters.search} onChange={change('search')} placeholder="Search activity or person" />
          <select className="input select" aria-label="Area" value={filters.category} onChange={change('category')}>
            <option value="">All areas</option>
            {Object.entries(ACTIVITY_CATEGORIES).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
          <input type="date" className="input" aria-label="From date" value={filters.date_from}
            max={filters.date_to || undefined} onChange={change('date_from')} />
          <input type="date" className="input" aria-label="To date" value={filters.date_to}
            min={filters.date_from || undefined} onChange={change('date_to')} />
          {filtered && (
            <Button variant="ghost" size="sm" onClick={() => { setFilters(NO_FILTERS); setPage(1) }}>
              Clear filters
            </Button>
          )}
        </div>
        <QueryBoundary query={query} loadingLabel="Loading activity...">
          {(data) => (data.results.length === 0 ? (
            <EmptyState icon={ScrollText}
              title={filtered ? 'Nothing matches these filters' : 'No activity recorded yet'}
              description={filtered ? 'Try a wider date range or another area.' : 'Actions taken in the portal are recorded here.'} />
          ) : (
            <>
              <DataTable columns={columns} rows={data.results} caption="Activity log" />
              <Pagination page={page} count={data.count} onChange={setPage} />
            </>
          ))}
        </QueryBoundary>
      </section>
    </>
  )
}
