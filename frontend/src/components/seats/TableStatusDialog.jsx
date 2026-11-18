import { useState } from 'react'
import { Info } from 'lucide-react'
import { useAction } from '../../hooks/useAction'
import { useApiQuery } from '../../hooks/useApiQuery'
import { seatService } from '../../services'
import { RESOURCE_STATUS, TABLE_STATE } from '../../utils/constants'
import Badge from '../common/Badge'
import Button from '../common/Button'
import { ErrorState, LoadingState } from '../common/Feedback'
import { FormError, TextField } from '../common/FormControls'
import Modal from '../common/Modal'
import AffectedReservations from './AffectedReservations'

/**
 * Availability of a whole table: see its six seats and take them all out of
 * service, or restore them. Seats that were out of service on their own stay
 * that way when the table is restored.
 */
export default function TableStatusDialog({ zoneId, tableNumber, onClose, onSaved }) {
  const query = useApiQuery(() => seatService.tables(zoneId), [zoneId, tableNumber])
  const table = query.data?.find((item) => item.table_number === tableNumber)
  const [note, setNote] = useState('')
  const [error, setError] = useState(null)

  const restoring = Boolean(table?.can_restore)
  const affected = restoring ? [] : table?.reservations ?? []
  const seated = affected.some((item) => item.status === 'checked_in')
  const allOff = table?.state === 'out_of_service'

  const [submit, saving] = useAction(
    () => seatService.setTableStatus({
      zone: zoneId, table_number: tableNumber, status: restoring ? 'active' : 'inactive',
      note: note.trim(), confirm_cancellations: affected.length > 0,
    }),
    {
      success: (result) => {
        if (restoring) {
          const left = result.total_seats - result.available_seats
          return `Table ${tableNumber} restored: ${result.restored_seats} seat(s) back in service.`
            + (left ? ` ${left} seat(s) stay out of service.` : '')
        }
        return `Table ${tableNumber} is out of service.`
          + (result.cancelled_reservations
            ? ` ${result.cancelled_reservations} reservation(s) were cancelled and the students notified.`
            : '')
      },
      onSuccess: onSaved,
      onError: (failure) => {
        setError(failure)
        query.refetch() // something may have changed: show the current state
        return true
      },
    },
  )

  let label = 'Mark table out of service'
  if (restoring) label = 'Restore table to service'
  else if (affected.length && !seated) label = `Cancel ${affected.length} and mark out of service`

  return (
    <Modal
      open onClose={onClose} busy={saving} title={`Manage Table ${tableNumber}`}
      description="Change the availability of all the seats at this table together."
      footer={(
        <>
          <Button variant="secondary" onClick={onClose} disabled={saving}>Cancel</Button>
          <Button
            variant={restoring ? 'primary' : 'danger'} onClick={() => { setError(null); submit() }}
            loading={saving} disabled={!table || seated || (allOff && !restoring)}
          >
            {label}
          </Button>
        </>
      )}
    >
      {!table ? (
        query.error
          ? <ErrorState compact error={query.error} onRetry={query.refetch} />
          : <LoadingState compact label="Loading table..." />
      ) : (
        <div className="stack">
          <div className="row-wrap">
            <Badge tone={TABLE_STATE[table.state].tone} dot>{TABLE_STATE[table.state].label}</Badge>
            <span className="small muted">{table.available_seats} of {table.total_seats} seats in service</span>
          </div>
          <ul className="table-seats">
            {table.seats.map((seat) => (
              <li key={seat.id} className="table-seat">
                <span className="strong">{seat.number}</span>
                <Badge tone={RESOURCE_STATUS[seat.status].tone} dot>{RESOURCE_STATUS[seat.status].label}</Badge>
                {seat.status_note && <span className="tiny muted">{seat.status_note}</span>}
                {seat.reservation_count > 0 && (
                  <span className="tiny muted">
                    {seat.reservation_count} reservation{seat.reservation_count === 1 ? '' : 's'}
                  </span>
                )}
              </li>
            ))}
          </ul>
          <FormError error={error} />
          {restoring ? (
            table.seats.some((seat) => seat.status !== 'active' && !seat.out_with_table) && (
              <p className="notice">
                <Info size={16} aria-hidden="true" />
                <span>Seats that were out of service on their own stay out of service.</span>
              </p>
            )
          ) : allOff ? (
            <p className="notice">
              <Info size={16} aria-hidden="true" />
              <span>Every seat here is out of service on its own. Use each seat&apos;s Availability button to restore it.</span>
            </p>
          ) : (
            <>
              <TextField label="Note for students" maxLength={200} value={note}
                placeholder="e.g. Table under repair until Friday"
                onChange={(event) => setNote(event.target.value)} />
              <AffectedReservations reservations={affected} />
            </>
          )}
        </div>
      )}
    </Modal>
  )
}
