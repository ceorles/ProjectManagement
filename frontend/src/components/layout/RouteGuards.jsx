import { RefreshCw, WifiOff } from 'lucide-react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { canOpen } from '../../utils/roles'
import { LibraryProvider } from '../../context/LibraryProvider'
import { useAuth } from '../../hooks/useAuth'
import ForbiddenPage from '../../pages/shared/ForbiddenPage'
import Button from '../common/Button'
import { Spinner } from '../common/Feedback'
import AppLayout from './AppLayout'
import { LogoMark } from './Logo'

/** Full-screen placeholder while the session is restored after a page load. */
export function SplashScreen({ unreachable = false, onRetry }) {
  return (
    <div className="splash" role="status">
      <LogoMark size={64} />
      {unreachable ? (
        <>
          <WifiOff size={22} className="muted" aria-hidden="true" />
          <h1 className="splash__title">Cannot reach the library server</h1>
          <p className="muted splash__text">
            You appear to be offline, or the server is not responding. Your reservations are
            safe on the server and will show as soon as the connection is back.
          </p>
          <Button icon={RefreshCw} onClick={onRetry}>Try again</Button>
        </>
      ) : (
        <Spinner size={26} className="splash__spinner" />
      )}
    </div>
  )
}

/**
 * Wraps every signed-in page. A refresh keeps the user on the same URL: we
 * wait for the session to be restored before deciding anything, and only
 * send people to the login page when they really are signed out.
 */
export function RequireAuth() {
  const { status, retry, signedOut, lastUserId } = useAuth()
  const location = useLocation()

  if (status === 'loading') return <SplashScreen />
  if (status === 'unreachable') return <SplashScreen unreachable onRetry={retry} />
  if (status === 'unauthenticated') {
    // After pressing "Sign out" the next person starts fresh on their own
    // dashboard. Otherwise (a bookmark, an expired session) remember the page,
    // and whose it was, to return there after signing in.
    if (signedOut) return <Navigate to="/login" replace />
    const from = { pathname: location.pathname, search: location.search }
    return <Navigate to="/login" replace state={{ from, userId: lastUserId }} />
  }
  return (
    <LibraryProvider>
      <AppLayout />
    </LibraryProvider>
  )
}

/**
 * Restricts a group of routes. `allow(user)` decides. Someone without access
 * sees a clear "no access" page rather than being silently redirected.
 * (The backend enforces the same rule on every request.)
 */
export function RequireRole({ allow }) {
  const { user } = useAuth()
  return allow(user) ? <Outlet /> : <ForbiddenPage />
}

/**
 * Where to go after signing in: back to the page that asked for it, but only
 * if it belonged to this same person and their role may open it. Anyone else
 * lands on their own role's dashboard.
 */
function afterSignIn(state, user) {
  const from = state?.from
  if (!from) return '/dashboard'
  const sameUser = state.userId == null || state.userId === user.id
  if (!sameUser || !canOpen(from.pathname, user)) return '/dashboard'
  return `${from.pathname}${from.search || ''}`
}

/** Login and registration: signed-in users are sent on to the app. */
export function GuestOnly() {
  const { status, retry, user } = useAuth()
  const location = useLocation()

  if (status === 'loading') return <SplashScreen />
  if (status === 'unreachable') return <SplashScreen unreachable onRetry={retry} />
  if (status === 'authenticated') {
    return <Navigate to={afterSignIn(location.state, user)} replace />
  }
  return <Outlet />
}
