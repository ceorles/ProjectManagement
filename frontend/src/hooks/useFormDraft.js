import { useCallback, useEffect, useRef, useState } from 'react'
import { draftKey, readDraft, removeDraft, writeDraft } from '../utils/storage'
import { useAuth } from './useAuth'

/**
 * Form state that survives a page refresh.
 *
 *   const { values, setField, clearDraft, restored } = useFormDraft('room-booking', initial)
 *
 * Whatever the user enters is saved as they type and restored when they come
 * back to the form. Call `clearDraft()` after a successful submit or when
 * the user cancels.
 *
 * Options:
 *   exclude  field names that must never be stored (passwords)
 *   storage  'local' (default) or 'session' (cleared when the tab closes;
 *            used for forms filled in before signing in)
 */
export function useFormDraft(form, initialValues, { exclude = [], storage = 'local' } = {}) {
  const { user } = useAuth()
  const key = draftKey(user?.id, form)
  const initialRef = useRef(initialValues)
  const excludeRef = useRef(exclude)

  const [restored, setRestored] = useState(() => readDraft(key, storage) !== null)
  const [values, setValues] = useState(() => ({
    ...initialValues,
    ...readDraft(key, storage),
  }))
  // After clearDraft(), nothing is saved again until the user edits the form.
  const paused = useRef(false)

  useEffect(() => {
    if (paused.current) return
    const draft = { ...values }
    excludeRef.current.forEach((field) => delete draft[field])
    writeDraft(key, draft, storage)
  }, [key, storage, values])

  const update = useCallback((next) => {
    paused.current = false
    setValues(next)
  }, [])

  const setField = useCallback((name, value) => {
    paused.current = false
    setValues((current) => ({ ...current, [name]: value }))
  }, [])

  /** Forget the saved draft. Pass `true` to also reset the form to its initial values. */
  const clearDraft = useCallback((reset = false) => {
    paused.current = true
    removeDraft(key, storage)
    setRestored(false)
    if (reset) setValues(initialRef.current)
  }, [key, storage])

  return { values, setValues: update, setField, clearDraft, restored }
}
