import { Suspense, useCallback, useEffect, useState } from 'react'
import { WifiOff } from 'lucide-react'
import { Outlet, useLocation } from 'react-router-dom'
import { POLL } from '../../config'
import { useApiQuery } from '../../hooks/useApiQuery'
import { useLibrary } from '../../hooks/useLibrary'
import { useOnlineStatus } from '../../hooks/useOnlineStatus'
import { notificationService } from '../../services'
import ErrorBoundary from '../common/ErrorBoundary'
import { ErrorState, LoadingState } from '../common/Feedback'
import Sidebar from './Sidebar'
import Topbar from './Topbar'
import './layout.css'

const DESKTOP = '(min-width: 1024px)'

/** The signed-in shell: sidebar, top bar and the current page. */
export default function AppLayout() {
  const library = useLibrary()
  const online = useOnlineStatus()
  const location = useLocation()
  // The drawer remembers which page it was opened on. Moving to another page
  // (a link, the back button) therefore closes it without any extra code.
  const [menuPath, setMenuPath] = useState(null)
  const menuOpen = menuPath === location.pathname
  const closeMenu = useCallback(() => setMenuPath(null), [])
  const toggleMenu = () => setMenuPath(menuOpen ? null : location.pathname)

  const unreadQuery = useApiQuery(notificationService.unreadCount, [], {
    interval: POLL.notifications, keepPrevious: true,
  })
  const unread = unreadQuery.data?.unread ?? 0

  // It also closes when Escape is pressed or the window grows to desktop width.
  useEffect(() => {
    if (!menuOpen) return undefined
    const onKey = (event) => {
      if (event.key === 'Escape') closeMenu()
    }
    const media = window.matchMedia(DESKTOP)
    const onResize = (event) => {
      if (event.matches) closeMenu()
    }
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden' // the page behind the drawer stays put
    document.addEventListener('keydown', onKey)
    media.addEventListener('change', onResize)
    return () => {
      document.body.style.overflow = previousOverflow
      document.removeEventListener('keydown', onKey)
      media.removeEventListener('change', onResize)
    }
  }, [menuOpen, closeMenu])

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main">Skip to content</a>
      <Sidebar open={menuOpen} onClose={closeMenu} unread={unread} />
      {menuOpen && <div className="sidebar-overlay" onClick={closeMenu} aria-hidden="true" />}

      <div className="app-shell__main">
        <Topbar
          menuOpen={menuOpen} onMenuToggle={toggleMenu}
          unread={unread} onNotificationsChange={unreadQuery.refetch}
        />
        {!online && (
          <div className="offline-banner" role="status">
            <WifiOff size={16} aria-hidden="true" />
            <span>
              You are offline. What you see may be out of date, and reservations cannot be
              made or changed until the connection returns.
            </span>
          </div>
        )}
        <main className="page" id="main" tabIndex={-1}>
          {library.ready ? (
            <ErrorBoundary resetKey={location.pathname}>
              <Suspense fallback={<LoadingState />}>
                <Outlet context={{ refreshUnread: unreadQuery.refetch }} />
              </Suspense>
            </ErrorBoundary>
          ) : library.error ? (
            <ErrorState error={library.error} onRetry={library.refetch} />
          ) : (
            <LoadingState label="Loading library information..." />
          )}
        </main>
      </div>
    </div>
  )
}
