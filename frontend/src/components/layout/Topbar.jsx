import { Menu } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useLibrary } from '../../hooks/useLibrary'
import { formatTime } from '../../utils/datetime'
import { LogoMark } from './Logo'
import NotificationBell from './NotificationBell'

function LibraryStatus() {
  const { ready, today } = useLibrary()
  if (!ready) return null // opening hours are still loading
  if (today.openNow) {
    return (
      <span className="library-status library-status--open">
        <span className="library-status__dot" aria-hidden="true" />
        <span>Open <span className="library-status__detail">until {formatTime(today.closesAt)}</span></span>
      </span>
    )
  }
  return (
    <span className="library-status">
      <span className="library-status__dot" aria-hidden="true" />
      <span>
        Closed
        {today.isOpen && (
          <span className="library-status__detail"> · {formatTime(today.opensAt)} - {formatTime(today.closesAt)} today</span>
        )}
      </span>
    </span>
  )
}

export default function Topbar({ menuOpen, onMenuToggle, unread, onNotificationsChange }) {
  return (
    <header className="topbar">
      {/* Shown on tablets and phones only (see layout.css). */}
      <button
        type="button" className="icon-button topbar__menu" onClick={onMenuToggle}
        aria-label="Open menu" aria-controls="app-sidebar" aria-expanded={menuOpen}
      >
        <Menu size={22} />
      </button>
      <Link to="/dashboard" className="topbar__brand" aria-label="Dashboard">
        <LogoMark size={30} />
      </Link>
      <LibraryStatus />
      <div className="topbar__spacer" />
      <NotificationBell unread={unread} onChange={onNotificationsChange} />
    </header>
  )
}
