import { useCallback, useEffect, useRef, useState } from 'react'

/**
 * Load data from the API and keep it fresh.
 *
 *   const { data, error, loading, refetch } = useApiQuery(
 *     () => seatService.availability(params), [params.date, params.start],
 *     { interval: 5000 },
 *   )
 *
 * - Refetches whenever a value in `deps` changes.
 * - With `interval`, polls while the tab is visible and the device is online,
 *   and refreshes straight away when the tab becomes visible again or the
 *   connection returns. This is what keeps availability near real-time.
 * - Previous data stays on screen during a refresh (no flicker), and a
 *   slow, outdated response can never overwrite a newer one.
 */
export function useApiQuery(
  fetcher, deps = [], { interval = 0, enabled = true, keepPrevious = false } = {},
) {
  const [state, setState] = useState({ data: null, error: null, loading: enabled })
  const fetcherRef = useRef(fetcher)
  const latestRequest = useRef(0)
  // Each change of `deps` starts a new "generation": results of the previous
  // one are discarded and its data is cleared.
  const depsKey = JSON.stringify(deps)

  useEffect(() => {
    fetcherRef.current = fetcher
  })

  const load = useCallback(async ({ silent = false } = {}) => {
    const requestId = ++latestRequest.current
    if (!silent) setState((current) => ({ ...current, loading: true }))
    try {
      const data = await fetcherRef.current()
      if (requestId === latestRequest.current) {
        setState({ data, error: null, loading: false })
      }
      return data
    } catch (error) {
      if (requestId === latestRequest.current) {
        // A failed background refresh keeps the data we already have.
        setState((current) => ({
          data: silent ? current.data : null,
          error,
          loading: false,
        }))
      }
      return null
    }
  }, [])

  useEffect(() => {
    if (!enabled) {
      latestRequest.current += 1
      setState({ data: null, error: null, loading: false })
      return undefined
    }
    // `keepPrevious` leaves the old result on screen while the new one loads
    // (lists and maps whose filters change); otherwise it is cleared.
    setState((current) => ({
      data: keepPrevious ? current.data : null, error: null, loading: true,
    }))
    load()

    if (!interval) return undefined

    const refresh = () => {
      if (document.visibilityState === 'visible' && navigator.onLine) load({ silent: true })
    }
    const timer = window.setInterval(refresh, interval)
    document.addEventListener('visibilitychange', refresh)
    window.addEventListener('online', refresh)
    return () => {
      window.clearInterval(timer)
      document.removeEventListener('visibilitychange', refresh)
      window.removeEventListener('online', refresh)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- depsKey stands in for deps
  }, [depsKey, enabled, interval, keepPrevious, load])

  const refetch = useCallback(() => load({ silent: true }), [load])

  return { ...state, refetch }
}
