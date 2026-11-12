import { useEffect, useMemo, useState } from 'react'
import { LibraryContext } from './contexts'
import { libraryService } from '../services'
import { useApiQuery } from '../hooks/useApiQuery'
import { libraryNow } from '../utils/datetime'
import { scheduleFor } from '../utils/booking'

/**
 * The library's opening hours, closures, floors and booking rules, loaded
 * once for the signed-in user and refreshed occasionally. Also provides a
 * clock that ticks on the library's time zone.
 */
export function LibraryProvider({ children }) {
  const { data: overview, error, loading, refetch } = useApiQuery(
    libraryService.overview, [], { interval: 5 * 60 * 1000 },
  )
  const timeZone = overview?.time_zone
  const [now, setNow] = useState(null)

  useEffect(() => {
    if (!timeZone) return undefined
    const tick = () => setNow((previous) => {
      const next = libraryNow(timeZone)
      // Keep the same object while the minute has not changed, so consumers
      // do not re-render every few seconds for nothing.
      return previous && previous.date === next.date && previous.time === next.time
        ? previous
        : next
    })
    tick()
    const timer = window.setInterval(tick, 15000)
    return () => window.clearInterval(timer)
  }, [timeZone])

  const value = useMemo(() => {
    if (!overview || !now) return { ready: false, error, loading, refetch }
    const today = scheduleFor(overview, now.date)
    return {
      ready: true,
      error,
      loading,
      refetch,
      overview,
      policy: overview.policy,
      floors: overview.floors,
      timeZone,
      now,
      today: {
        ...today,
        openNow: today.isOpen && now.minutes >= today.opens && now.minutes < today.closes,
      },
    }
  }, [overview, now, error, loading, refetch, timeZone])

  return <LibraryContext.Provider value={value}>{children}</LibraryContext.Provider>
}
