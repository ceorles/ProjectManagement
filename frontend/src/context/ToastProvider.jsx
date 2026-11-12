import { useCallback, useMemo, useRef, useState } from 'react'
import { ToastContext } from './contexts'
import ToastViewport from '../components/common/ToastViewport'

const DURATION = { success: 4000, info: 4500, error: 6500 }

/** App-wide success / error messages shown briefly in a corner of the screen. */
export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])
  const nextId = useRef(1)

  const dismiss = useCallback((id) => {
    setToasts((current) => current.filter((toast) => toast.id !== id))
  }, [])

  const show = useCallback((type, message) => {
    const id = nextId.current++
    // Keep the stack short; identical consecutive messages are not repeated.
    setToasts((current) => {
      if (current.some((toast) => toast.message === message && toast.type === type)) return current
      return [...current.slice(-3), { id, type, message }]
    })
    window.setTimeout(() => dismiss(id), DURATION[type])
  }, [dismiss])

  const toast = useMemo(() => ({
    success: (message) => show('success', message),
    error: (message) => show('error', message),
    info: (message) => show('info', message),
  }), [show])

  return (
    <ToastContext.Provider value={toast}>
      {children}
      <ToastViewport toasts={toasts} onDismiss={dismiss} />
    </ToastContext.Provider>
  )
}
