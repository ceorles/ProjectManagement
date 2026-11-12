import { useCallback, useEffect, useMemo, useState } from 'react'
import { AuthContext } from './contexts'
import { onSessionExpired, setAccessToken } from '../services/apiClient'
import { authService } from '../services'
import { clearDraftsFor } from '../utils/storage'

/**
 * Session state for the whole app.
 *
 * status: 'loading'         - restoring the session after a page load
 *         'authenticated'   - `user` is set
 *         'unauthenticated' - nobody is signed in
 *         'unreachable'     - the server could not be reached, so we cannot
 *                             tell yet (offline). The app waits and retries
 *                             instead of throwing the user out to the login page.
 */
// Not a credential: only remembers that this browser has signed in before,
// so a first-time visitor is not sent through a refresh that must fail.
const SESSION_HINT = 'libreserve:signed-in'

function sessionHint(value) {
  try {
    if (value === undefined) return window.localStorage.getItem(SESSION_HINT) === '1'
    if (value) window.localStorage.setItem(SESSION_HINT, '1')
    else window.localStorage.removeItem(SESSION_HINT)
  } catch {
    return true // storage unavailable: always ask the server
  }
  return value
}

export function AuthProvider({ children }) {
  const [status, setStatus] = useState(() => (sessionHint() ? 'loading' : 'unauthenticated'))
  const [user, setUser] = useState(null)
  const [sessionExpired, setSessionExpired] = useState(false)

  const restore = useCallback(() => authService.restore().then(
    (session) => {
      setUser(session.user)
      setStatus('authenticated')
    },
    (error) => {
      if (error.isNetworkError || error.status >= 500) {
        setStatus('unreachable')
      } else {
        sessionHint(false)
        setUser(null)
        setStatus('unauthenticated')
      }
    },
  ), [])

  // On every page load, turn the HttpOnly refresh cookie back into a session.
  useEffect(() => {
    if (sessionHint()) restore()
  }, [restore])

  // If we could not reach the server, try again as soon as we are back online.
  useEffect(() => {
    if (status !== 'unreachable') return undefined
    const retry = () => restore()
    window.addEventListener('online', retry)
    const timer = window.setInterval(retry, 8000)
    return () => {
      window.removeEventListener('online', retry)
      window.clearInterval(timer)
    }
  }, [status, restore])

  // The API client calls this when a refresh is refused mid-session.
  useEffect(() => {
    onSessionExpired(() => {
      sessionHint(false)
      setSessionExpired(true)
      setUser(null)
      setStatus('unauthenticated')
    })
    return () => onSessionExpired(null)
  }, [])

  const startSession = useCallback((session) => {
    setAccessToken(session.access)
    sessionHint(true)
    setUser(session.user)
    setSessionExpired(false)
    setStatus('authenticated')
    return session.user
  }, [])

  const login = useCallback(
    async (email, password) => startSession(await authService.login(email, password)),
    [startSession],
  )

  const register = useCallback(
    async (data) => startSession(await authService.register(data)),
    [startSession],
  )

  const logout = useCallback(async () => {
    const userId = user?.id
    try {
      await authService.logout()
    } catch {
      // Even if the server cannot be reached, sign out on this device.
    }
    setAccessToken(null)
    sessionHint(false)
    if (userId) clearDraftsFor(userId)
    setUser(null)
    setSessionExpired(false)
    setStatus('unauthenticated')
  }, [user])

  const value = useMemo(() => ({
    status,
    user,
    sessionExpired,
    isAuthenticated: status === 'authenticated',
    isStaff: user?.role === 'admin' || user?.role === 'librarian',
    login,
    register,
    logout,
    retry: restore,
    setUser,
    acknowledgeSessionExpired: () => setSessionExpired(false),
  }), [status, user, sessionExpired, login, register, logout, restore])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
