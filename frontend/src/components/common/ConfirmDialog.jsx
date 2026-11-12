import Button from './Button'
import Modal from './Modal'

/** "Are you sure?" before a destructive or important action. */
export default function ConfirmDialog({
  open, onClose, onConfirm, title, children, confirmLabel = 'Confirm',
  cancelLabel = 'Go back', tone = 'danger', busy = false,
}) {
  return (
    <Modal
      open={open} onClose={onClose} title={title} size="sm" busy={busy}
      footer={(
        <>
          <Button variant="secondary" onClick={onClose} disabled={busy}>{cancelLabel}</Button>
          <Button variant={tone === 'danger' ? 'danger' : 'primary'} onClick={onConfirm} loading={busy}>
            {confirmLabel}
          </Button>
        </>
      )}
    >
      <div className="stack-sm soft">{children}</div>
    </Modal>
  )
}
