import { useContext } from 'react'
import { LibraryContext } from '../context/contexts'

/** Opening hours, booking rules, floors and the library clock. */
export function useLibrary() {
  const context = useContext(LibraryContext)
  if (!context) throw new Error('useLibrary must be used inside <LibraryProvider>')
  return context
}
