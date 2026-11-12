import { useCallback, useMemo } from 'react'
import { endTime, normalizeWindow } from '../utils/booking'
import { useFormDraft } from './useFormDraft'
import { useLibrary } from './useLibrary'

/**
 * The date / start time / duration a user is booking for, plus any extra
 * fields of the same form. Everything is kept as a draft, so a refresh does
 * not lose it.
 *
 * A restored draft can be out of date (yesterday's date, a start time that
 * has passed). `window` is therefore always the saved values repaired
 * against the current opening hours and clock.
 */
export function useBookingWindow(form, resourceType, extra = {}) {
  const { overview, now } = useLibrary()
  const draft = useFormDraft(form, { date: '', start: '', duration: 0, ...extra })
  const { values, setValues } = draft

  const window = useMemo(
    () => normalizeWindow(overview, now, resourceType, values),
    [overview, now, resourceType, values],
  )

  const setWindow = useCallback((changes) => {
    setValues((current) => ({
      ...current,
      ...normalizeWindow(overview, now, resourceType, { ...current, ...changes }),
    }))
  }, [overview, now, resourceType, setValues])

  const bookable = Boolean(window.start && window.duration)
  return {
    ...draft,
    window,
    setWindow,
    bookable,
    end: bookable ? endTime(window.start, window.duration) : '',
    // Query parameters for the availability endpoints.
    params: bookable
      ? { date: window.date, start: window.start, end: endTime(window.start, window.duration) }
      : null,
  }
}
