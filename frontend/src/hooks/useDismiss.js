import { useEffect, useRef } from 'react'

/** Closes a popover when the user clicks elsewhere or presses Escape. */
export function useDismiss(open, onDismiss) {
  const ref = useRef(null)
  const handler = useRef(onDismiss)
  useEffect(() => {
    handler.current = onDismiss
  })

  useEffect(() => {
    if (!open) return undefined
    const onPointer = (event) => {
      if (ref.current && !ref.current.contains(event.target)) handler.current()
    }
    const onKey = (event) => {
      if (event.key === 'Escape') handler.current()
    }
    document.addEventListener('pointerdown', onPointer)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('pointerdown', onPointer)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])
  return ref
}
