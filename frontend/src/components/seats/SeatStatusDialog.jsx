import { useState } from 'react'
import { Info } from 'lucide-react'
import { useAction } from '../../hooks/useAction'
import { useApiQuery } from '../../hooks/useApiQuery'
import { seatService } from '../../services'
import { RESOURCE_STATUS } from '../../utils/constants'
import Button from '../common/Button'
import { FormError, SelectField, TextField } from '../common/FormControls'
import Modal from '../common/Modal'
import AffectedReservations from './AffectedReservations'

/** Availability of one seat. The other seats of its table are not affected. */
export default function SeatStatusDialog({ seat, onClose, onSaved }) {
  const [status, setStatus] = useState(seat.status)
  const [note, setNote] = useState(seat.status_note || '')
  const [error, setError] = useState(null)
  const closing = status !== 'active'
  const impact = useApiQuery(() => seatService.affectedReservations(seat.id), [seat.id], { enabled: closing })
  const affected = closing ? impact.data ?? [] : []
  const seated = affected.some((item) => item.status === 'checked_in')

  const [submit, saving] = useAction(
    () => seatService.setStatus(seat.id, {
      status, note: note.trim(), confirm_cancellations: affected.length > 0,
    }),
    {
      success: (result) => (result.cancelled_reservations
        ? `Seat ${seat.number} updated. ${result.cancelled_reservations} reservation(s) were cancelled and the students notified.`
        : `Seat ${seat.number} updated.`),
      onSuccess: onSaved,
      onError: (failure) => {
        setError(failure)
        impact.refetch() // something may have changed: show the current list
        return true
      },
    },
  )
  const unchanged = status === seat.status && note === (seat.status_note || '')

  return (
    <Modal
      open onClose={onClose} busy={saving} size="sm" title={`Availability of Seat ${seat.number}`}
      footer={(
        <>
          <Button variant="secondary" onClick={onClose} disabled={saving}>Cancel</Button>
          <Button variant={affected.length ? 'danger' : 'primary'} onClick={() => { setError(null); submit() }}
            loading={saving} disabled={unchanged || seated || (closing && impact.loading)}>
            {affected.length && !seated ? `Cancel ${affected.length} and save` : 'Save'}
          </Button>
        </>
      )}
    >
      <div className="stack">
        {seat.out_with_table && (
          <p className="notice">
            <Info size={16} aria-hidden="true" />
            <span>
              This seat is out of service with Table {seat.table_number}. Restore the table to bring
              it back.
            </span>
          </p>
        )}
        <FormError error={error} />
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
            <AffectedReservations reservations={affected} />
          </>
        )}
      </div>
    </Modal>
  )
}
