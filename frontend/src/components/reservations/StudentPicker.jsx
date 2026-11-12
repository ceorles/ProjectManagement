import { useState } from 'react'
import { UserRound, X } from 'lucide-react'
import { useApiQuery } from '../../hooks/useApiQuery'
import { useDebounce } from '../../hooks/useDebounce'
import { userService } from '../../services'
import { EmptyState, ErrorState, LoadingState } from '../common/Feedback'
import { SearchInput } from '../common/FormControls'

/** Staff: choose the student a reservation is being made for. */
export default function StudentPicker({ value, onChange }) {
  const [search, setSearch] = useState('')
  const term = useDebounce(search.trim())
  const query = useApiQuery(() => userService.searchStudents(term), [term], {
    enabled: !value && term.length >= 2,
  })

  if (value) {
    return (
      <div className="picked-student">
        <span className="avatar"><UserRound size={18} aria-hidden="true" /></span>
        <div className="grow">
          <p className="strong truncate">{value.full_name}</p>
          <p className="muted small truncate">{value.student_id}</p>
        </div>
        <button type="button" className="icon-button" onClick={() => onChange(null)} aria-label="Choose a different student">
          <X size={17} />
        </button>
      </div>
    )
  }

  return (
    <div className="stack-sm">
      <SearchInput value={search} onChange={setSearch} label="Find a student"
        placeholder="Search by name, student ID or email" />
      {term.length < 2 ? (
        <p className="field__hint">Type at least 2 characters to search.</p>
      ) : query.error ? (
        <ErrorState compact error={query.error} onRetry={query.refetch} />
      ) : !query.data ? (
        <LoadingState compact label="Searching..." />
      ) : query.data.length === 0 ? (
        <EmptyState compact icon={UserRound} title="No student found"
          description="Check the spelling or try the student ID." />
      ) : (
        <ul className="student-results">
          {query.data.map((student) => (
            <li key={student.id}>
              <button type="button" onClick={() => {
                onChange({ id: student.id, full_name: student.full_name, student_id: student.student_id })
                setSearch('')
              }}>
                <span className="strong">{student.full_name}</span>
                <span className="muted small">{student.student_id} - {student.program || student.email}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
