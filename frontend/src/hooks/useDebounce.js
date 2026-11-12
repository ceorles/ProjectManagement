import { useEffect, useState } from 'react'

/** Returns `value` once it has stopped changing for `delay` ms (search boxes). */
export function useDebounce(value, delay = 350) {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(value), delay)
    return () => window.clearTimeout(timer)
  }, [value, delay])
  return debounced
}
