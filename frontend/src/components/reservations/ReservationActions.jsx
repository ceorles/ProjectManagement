import { useState } from 'react'
import { Ban, Check, LogIn, LogOut, UserX, X } from 'lucide-react'
import { useAction } from '../../hooks/useAction'
import { useAuth } from '../../hooks/useAuth'
import { reservationService } from '../../services'
import Button from '../common/Button'
import ConfirmDialog from '../common/ConfirmDialog'
import { TextAreaField } from '../common/FormControls'
import Modal from '../common/Modal'

/**
 * The buttons for whatever may be done to a reservation right now: approve,
 * reject, check in, check out, cancel, mark as no-show. Which ones appear
 * comes from the `can_*` flags the server sends, and the server checks again
 * on every click.
 */
export default function ReservationActions({ reservation, onChanged, size = 'sm' }) {
  const { isStaff } = useAuth()
  const [dialog, setDialog] = useState(null) // 'reject' | 'cancel' | 'check-out' | 'no-show'
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
  const { id, resource, student } = reservation

  const [approve, approving] = useAction(() => reservationService.approve(id), {
    success: `Approved. ${student.full_name} has been notified.`, onSuccess: done, onError,
  })
  const [reject, rejecting] = useAction(() => reservationService.reject(id, reason.trim()), {
    success: `Rejected. ${student.full_name} has been notified and the places are free again.`,
    onSuccess: done, onError,
  })
  const [checkIn, checkingIn] = useAction(() => reservationService.checkIn(id), {
    success: isStaff ? `${student.full_name} is checked in.` : 'You are checked in. Enjoy your study session!',
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

  const { can_approve, can_check_in, can_check_out, can_cancel, can_mark_no_show } = reservation
  if (!can_approve && !can_check_in && !can_check_out && !can_cancel && !can_mark_no_show) return null
  const pending = reservation.status === 'pending'

  return (
    <>
      {can_approve && (
        <>
          <Button size={size} icon={Check} loading={approving} onClick={approve}>Approve</Button>
          <Button size={size} variant="danger-soft" icon={X} onClick={() => setDialog('reject')}>
            Reject
          </Button>
        </>
      )}
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
      {can_cancel && !can_approve && (
        <Button size={size} variant="danger-soft" icon={Ban} onClick={() => setDialog('cancel')}>
          {pending ? 'Withdraw' : 'Cancel'}
        </Button>
      )}

      <Modal
        open={dialog === 'reject'} onClose={close} busy={rejecting} size="sm"
        title="Reject this request?"
        footer={(
          <>
            <Button variant="secondary" onClick={close} disabled={rejecting}>Go back</Button>
            <Button variant="danger" onClick={reject} loading={rejecting}>Reject request</Button>
          </>
        )}
      >
        <div className="stack">
          <p className="soft">
            <strong>{student.full_name}</strong>&apos;s request for <strong>{resource.name}</strong> will
            be rejected and the places released for other students. The student is notified.
          </p>
          <TextAreaField
            label="Reason (shown to the student)" rows={2} maxLength={200}
            value={reason} onChange={(event) => setReason(event.target.value)}
          />
        </div>
      </Modal>

      <Modal
        open={dialog === 'cancel'} onClose={close} busy={cancelling} size="sm"
        title={pending ? 'Withdraw this request?' : 'Cancel this reservation?'}
        footer={(
          <>
            <Button variant="secondary" onClick={close} disabled={cancelling}>Keep it</Button>
            <Button variant="danger" onClick={cancel} loading={cancelling}>
              {pending ? 'Withdraw request' : 'Cancel reservation'}
            </Button>
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
          <strong>{student.full_name}</strong> has not arrived for <strong>{resource.name}</strong>.
          The place will be released and a missed reservation recorded on the student&apos;s account.
        </p>
      </ConfirmDialog>
    </>
  )
}
