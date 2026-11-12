import { createContext } from 'react'

// The context objects live apart from the provider components so that each
// provider file exports only a component (keeps React Fast Refresh working).
export const AuthContext = createContext(null)
export const LibraryContext = createContext(null)
export const ToastContext = createContext(null)
