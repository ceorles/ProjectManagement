import { useEffect, useId, useRef } from 'react'
import { createPortal } from 'react-dom'
import { X } from 'lucide-react'

/**
 * Dialog. On phones it becomes a sheet that slides up from the bottom and
 * scrolls inside itself, so it can never overflow the screen.
 *
 * `busy` blocks closing while a request is in flight.
 */
export default function Modal({ open, onClose, title, description, size = 'md', busy = false, footer, children }) {
  const titleId = useId()
  const dialogRef = useRef(null)
  // Latest props for the key handler, without re-running the effect below.
  const closeRef = useRef(onClose)
  const busyRef = useRef(busy)
  useEffect(() => {
    closeRef.current = onClose
    busyRef.current = busy
  })

  useEffect(() => {
    if (!open) return undefined
    const previouslyFocused = document.activeElement
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden' // the page behind must not scroll
    dialogRef.current?.focus()

    const onKeyDown = (event) => {
      if (event.key === 'Escape' && !busyRef.current) closeRef.current()
      if (event.key !== 'Tab') return
      // Keep keyboard focus inside the dialog.
      const focusable = dialogRef.current?.querySelectorAll(
        'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex="0"]',
      )
      if (!focusable?.length) return
      const first = focusable[0]
      const last = focusable[focusable.length - 1]
      if (event.shiftKey && (document.activeElement === first || document.activeElement === dialogRef.current)) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    }
    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      document.body.style.overflow = previousOverflow
      previouslyFocused?.focus?.()
    }
  }, [open])

  if (!open) return null

  return createPortal(
    <div
      className="modal-overlay"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && !busy) onClose()
      }}
    >
      <div
        ref={dialogRef} className={`modal modal--${size}`} role="dialog" aria-modal="true"
        aria-labelledby={titleId} tabIndex={-1}
      >
        <header className="modal__header">
          <div className="grow">
            <h2 id={titleId} className="modal__title">{title}</h2>
            {description && <p className="modal__description">{description}</p>}
          </div>
          <button type="button" className="icon-button" onClick={onClose} disabled={busy} aria-label="Close">
            <X size={18} />
          </button>
        </header>
        <div className="modal__body">{children}</div>
        {footer && <footer className="modal__footer">{footer}</footer>}
      </div>
    </div>,
    document.body,
  )
}
