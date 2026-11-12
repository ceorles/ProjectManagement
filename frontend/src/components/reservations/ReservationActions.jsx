import { useState } from 'react'
import { Ban, LogIn, LogOut, UserX } from 'lucide-react'
import { useAction } from '../../hooks/useAction'
import { useAuth } from '../../hooks/useAuth'
import { reservationService } from '../../services'
import Button from '../common/Button'
import ConfirmDialog from '../common/ConfirmDialog'
import { TextAreaField } from '../common/FormControls'
import Modal from '../common/Modal'

/**
 * The buttons for whatever may be done to a reservation right now: check in,
 * check out, cancel, mark as no-show. Which ones appear comes from the
 * `can_*` flags the server sends, and the server checks again on every click.
 */
export default function ReservationActions({ reservation, onChanged, size = 'sm' }) {
  const { isStaff } = useAuth()
  const [dialog, setDialog] = useState(null) // 'cancel' | 'check-out' | 'no-show'
  const [reason, setReason] = useState('')
  const close = () => setDialog(null)
  const done = (updated) => {
    close()
    setReason('')
    onChanged?.(updated)
  }
  // If the action is refused (e.g. the status changed meanwhile), refresh so
  // the buttons match reality again.
  const onError = () => {
    close()
    onChanged?.(null)
  }
  const { id, resource } = reservation

  const [checkIn, checkingIn] = useAction(() => reservationService.checkIn(id), {
    success: isStaff ? `${reservation.student.full_name} is checked in.` : 'You are checked in. Enjoy your study session!',
    onSuccess: done, onError,
  })
  const [checkOut, checkingOut] = useAction(() => reservationService.checkOut(id), {
    success: 'Checked out. Thank you!', onSuccess: done, onError,
  })
  const [cancel, cancelling] = useAction(() => reservationService.cancel(id, reason.trim()), {
    success: 'The reservation was cancelled.', onSuccess: done, onError,
  })
  const [noShow, markingNoShow] = useAction(() => reservationService.markNoShow(id), {
    success: 'Marked as a no-show. The place is available again.', onSuccess: done, onError,
  })

  const { can_check_in, can_check_out, can_cancel, can_mark_no_show } = reservation
  if (!can_check_in && !can_check_out && !can_cancel && !can_mark_no_show) return null

  return (
    <>
      {can_check_in && (
        <Button size={size} icon={LogIn} loading={checkingIn} onClick={checkIn}>Check in</Button>
      )}
      {can_check_out && (
        <Button size={size} variant="secondary" icon={LogOut} onClick={() => setDialog('check-out')}>
          Check out
        </Button>
      )}
      {can_mark_no_show && (
        <Button size={size} variant="secondary" icon={UserX} onClick={() => setDialog('no-show')}>
          No-show
        </Button>
      )}
      {can_cancel && (
        <Button size={size} variant="danger-soft" icon={Ban} onClick={() => setDialog('cancel')}>
          Cancel
        </Button>
      )}

      <Modal
        open={dialog === 'cancel'} onClose={close} busy={cancelling} size="sm"
        title="Cancel this reservation?"
        footer={(
          <>
            <Button variant="secondary" onClick={close} disabled={cancelling}>Keep it</Button>
            <Button variant="danger" onClick={cancel} loading={cancelling}>Cancel reservation</Button>
          </>
        )}
      >
        <div className="stack">
          <p className="soft">
            <strong>{resource.name}</strong> will be released so that other students can reserve it.
            This cannot be undone.
          </p>
          <TextAreaField
            label={isStaff ? 'Reason (shown to the student)' : 'Reason (optional)'} rows={2}
            maxLength={200} value={reason} onChange={(event) => setReason(event.target.value)}
          />
        </div>
      </Modal>

      <ConfirmDialog
        open={dialog === 'check-out'} onClose={close} onConfirm={checkOut} busy={checkingOut}
        title="Check out now?" confirmLabel="Check out" tone="primary"
      >
        <p>
          This ends the reservation of <strong>{resource.name}</strong>. The remaining time becomes
          available to other students.
        </p>
      </ConfirmDialog>

      <ConfirmDialog
        open={dialog === 'no-show'} onClose={close} onConfirm={noShow} busy={markingNoShow}
        title="Mark as no-show?" confirmLabel="Mark no-show"
      >
        <p>
          <strong>{reservation.student.full_name}</strong> has not arrived for <strong>{resource.name}</strong>.
          The place will be released and a missed reservation recorded on the student's account.
        </p>
      </ConfirmDialog>
    </>
  )
}
