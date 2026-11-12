import { useCallback, useEffect, useRef, useState } from 'react'
import { useToast } from './useToast'

/**
 * Run a server action from a button, safely.
 *
 *   const [cancel, cancelling] = useAction(
 *     () => reservationService.cancel(id), { success: 'Reservation cancelled.' })
 *
 * While the request is in flight `cancelling` is true (disable the button)
 * and further calls are ignored, so a double click cannot submit twice.
 * Success is only reported after the server has answered; an error shows the
 * server's message.
 */
export function useAction(action, { success, onSuccess, onError } = {}) {
  const toast = useToast()
  const [pending, setPending] = useState(false)
  const busy = useRef(false)
  // Always call the newest callbacks, even if the component re-rendered
  // while the request was in flight.
  const latest = useRef({ action, success, onSuccess, onError })
  useEffect(() => {
    latest.current = { action, success, onSuccess, onError }
  })

  const run = useCallback(async (...args) => {
    if (busy.current) return undefined
    busy.current = true
    setPending(true)
    const current = latest.current
    try {
      const result = await current.action(...args)
      if (current.success) {
        toast.success(typeof current.success === 'function' ? current.success(result) : current.success)
      }
      current.onSuccess?.(result, ...args)
      return result
    } catch (error) {
      if (current.onError?.(error) !== true) toast.error(error.message)
      return undefined
    } finally {
      busy.current = false
      setPending(false)
    }
  }, [toast])

  return [run, pending]
}
