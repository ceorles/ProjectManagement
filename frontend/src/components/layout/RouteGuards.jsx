import { RefreshCw, WifiOff } from 'lucide-react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'
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
  const { status, retry } = useAuth()
  const location = useLocation()

  if (status === 'loading') return <SplashScreen />
  if (status === 'unreachable') return <SplashScreen unreachable onRetry={retry} />
  if (status === 'unauthenticated') {
    // Remember where they were going, to return there after signing in.
    return <Navigate to="/login" replace state={{ from: location }} />
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

/** Login and registration: signed-in users are sent on to the app. */
export function GuestOnly() {
  const { status, retry } = useAuth()
  const location = useLocation()

  if (status === 'loading') return <SplashScreen />
  if (status === 'unreachable') return <SplashScreen unreachable onRetry={retry} />
  if (status === 'authenticated') {
    const from = location.state?.from
    const target = from ? `${from.pathname}${from.search || ''}` : '/dashboard'
    return <Navigate to={target} replace />
  }
  return <Outlet />
}
