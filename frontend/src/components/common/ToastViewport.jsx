import { CircleAlert, CircleCheck, Info, X } from 'lucide-react'

const ICONS = { success: CircleCheck, error: CircleAlert, info: Info }

export default function ToastViewport({ toasts, onDismiss }) {
  return (
    <div className="toasts" aria-live="polite" aria-atomic="false">
      {toasts.map((toast) => {
        const Icon = ICONS[toast.type]
        return (
          <div key={toast.id} className={`toast toast--${toast.type}`} role={toast.type === 'error' ? 'alert' : 'status'}>
            <Icon size={18} className="toast__icon" aria-hidden="true" />
            <p className="toast__message">{toast.message}</p>
            <button type="button" className="toast__close" onClick={() => onDismiss(toast.id)} aria-label="Dismiss">
              <X size={15} />
            </button>
          </div>
        )
      })}
    </div>
  )
}
