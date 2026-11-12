import { ChevronLeft, ChevronRight } from 'lucide-react'
import Button from './Button'

/** Previous / next paging for API lists ({ count, results }). */
export default function Pagination({ page, pageSize = 20, count, onChange }) {
  const pages = Math.max(1, Math.ceil(count / pageSize))
  if (count <= pageSize) return null
  const first = (page - 1) * pageSize + 1
  const last = Math.min(page * pageSize, count)
  return (
    <nav className="pagination" aria-label="Pagination">
      <p className="muted small">Showing {first}-{last} of {count}</p>
      <div className="row-sm">
        <Button
          variant="secondary" size="sm" icon={ChevronLeft} disabled={page <= 1}
          onClick={() => onChange(page - 1)}
        >
          Previous
        </Button>
        <span className="small soft nowrap">Page {page} of {pages}</span>
        <Button
          variant="secondary" size="sm" iconRight={ChevronRight} disabled={page >= pages}
          onClick={() => onChange(page + 1)}
        >
          Next
        </Button>
      </div>
    </nav>
  )
}
