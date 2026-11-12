import { useState } from 'react'
import { UserPlus, X } from 'lucide-react'
import { useAction } from '../../hooks/useAction'
import { userService } from '../../services'
import Button from '../common/Button'

/**
 * Invite classmates to a room reservation by their student ID. Each ID is
 * checked with the server, which answers with the student's name.
 */
export default function InviteList({ value, onChange, max, ownStudentId }) {
  const [studentId, setStudentId] = useState('')
  const [error, setError] = useState('')
  const full = value.length >= max

  const [lookup, looking] = useAction(() => userService.lookupStudent(studentId.trim()), {
    onSuccess: (student) => {
      onChange([...value, { student_id: student.student_id, full_name: student.full_name }])
      setStudentId('')
    },
    onError: (failure) => {
      setError(failure.status === 404 ? 'No active student has that ID.' : failure.message)
      return true
    },
  })

  const add = () => {
    const entered = studentId.trim().toLowerCase()
    setError('')
    if (!entered) return
    if (ownStudentId && entered === ownStudentId.toLowerCase()) {
      setError('That is the person making the reservation. Add other students.')
    } else if (value.some((person) => person.student_id.toLowerCase() === entered)) {
      setError('That student is already on the list.')
    } else {
      lookup()
    }
  }

  return (
    <div className="stack-sm">
      <p className="field__label">Invite classmates <span className="muted">(optional)</span></p>
      {value.length > 0 && (
        <ul className="invitees">
          {value.map((person) => (
            <li key={person.student_id} className="invitee">
              <span className="truncate">
                <span className="strong">{person.full_name}</span>
                <span className="muted"> · {person.student_id}</span>
              </span>
              <button type="button" className="icon-button"
                onClick={() => onChange(value.filter((other) => other.student_id !== person.student_id))}
                aria-label={`Remove ${person.full_name}`}>
                <X size={16} />
              </button>
            </li>
          ))}
        </ul>
      )}
      {full ? (
        <p className="field__hint">The room is at capacity with this group.</p>
      ) : (
        <>
          <div className="invite-form">
            <input
              className="input" value={studentId} placeholder="Classmate's student ID"
              aria-label="Classmate's student ID" autoComplete="off"
              onChange={(event) => { setStudentId(event.target.value); setError('') }}
              onKeyDown={(event) => {
                if (event.key === 'Enter') {
                  event.preventDefault()
                  add()
                }
              }}
            />
            <Button variant="secondary" icon={UserPlus} loading={looking} onClick={add}
              disabled={!studentId.trim()}>
              Add
            </Button>
          </div>
          {error
            ? <p className="field__error" role="alert">{error}</p>
            : <p className="field__hint">They are notified and can see the reservation.</p>}
        </>
      )}
    </div>
  )
}
