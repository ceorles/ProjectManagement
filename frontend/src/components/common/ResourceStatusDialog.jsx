import { useState } from 'react'
import { TriangleAlert } from 'lucide-react'
import { useAction } from '../../hooks/useAction'
import { RESOURCE_STATUS } from '../../utils/constants'
import Button from './Button'
import { SelectField, TextField } from './FormControls'
import Modal from './Modal'

/**
 * Put a seat or study room into maintenance, take it out of service, or
 * bring it back. `save({ status, note })` performs the change.
 */
export default function ResourceStatusDialog({ name, current, note: currentNote, save, onClose, onSaved }) {
  const [status, setStatus] = useState(current)
  const [note, setNote] = useState(currentNote || '')
  const [submit, saving] = useAction(() => save({ status, note: note.trim() }), {
    success: (result) => (result.cancelled_reservations
      ? `${name} updated. ${result.cancelled_reservations} upcoming reservation(s) were cancelled and the students notified.`
      : `${name} updated.`),
    onSuccess: onSaved,
  })
  const closing = status !== 'active'

  return (
    <Modal
      open onClose={onClose} busy={saving} size="sm" title={`Availability of ${name}`}
      footer={(
        <>
          <Button variant="secondary" onClick={onClose} disabled={saving}>Cancel</Button>
          <Button onClick={submit} loading={saving} disabled={status === current && note === (currentNote || '')}>
            Save
          </Button>
        </>
      )}
    >
      <div className="stack">
        <SelectField label="Status" value={status} onChange={(event) => setStatus(event.target.value)}>
          {Object.entries(RESOURCE_STATUS).map(([value, meta]) => (
            <option key={value} value={value}>{meta.label}</option>
          ))}
        </SelectField>
        {closing && (
          <>
            <TextField label="Note for students" maxLength={200} value={note}
              placeholder="e.g. Broken chair, back on Monday"
              onChange={(event) => setNote(event.target.value)} />
            <p className="notice notice--warning">
              <TriangleAlert size={16} aria-hidden="true" />
              <span>
                It can no longer be reserved, and upcoming reservations for it will be{' '}
                <strong>cancelled</strong>. The students are notified.
              </span>
            </p>
          </>
        )}
      </div>
    </Modal>
  )
}
