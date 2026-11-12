import { useState } from 'react'
import { ChevronDown, LogOut, Menu, User } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import { useDismiss } from '../../hooks/useDismiss'
import { useLibrary } from '../../hooks/useLibrary'
import { ROLES } from '../../utils/constants'
import { formatTime } from '../../utils/datetime'
import { initials } from '../../utils/roles'
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

function UserMenu() {
  const { user, logout } = useAuth()
  const [open, setOpen] = useState(false)
  const ref = useDismiss(open, () => setOpen(false))
  return (
    <div className="popover-anchor" ref={ref}>
      <button type="button" className="user-menu" onClick={() => setOpen((value) => !value)}
        aria-haspopup="menu" aria-expanded={open}>
        <span className="avatar">{initials(user)}</span>
        <span className="user-menu__text">
          <span className="user-menu__name truncate">{user.full_name}</span>
          <span className="user-menu__role">{ROLES[user.role]}</span>
        </span>
        <ChevronDown size={16} className="user-menu__chevron" aria-hidden="true" />
      </button>
      {open && (
        <div className="popover popover--menu" role="menu">
          <div className="popover__identity">
            <p className="strong truncate">{user.full_name}</p>
            <p className="muted small truncate">{user.email}</p>
          </div>
          <Link to="/profile" className="popover__item" role="menuitem" onClick={() => setOpen(false)}>
            <User size={16} aria-hidden="true" /> Profile
          </Link>
          <button type="button" className="popover__item" role="menuitem" onClick={logout}>
            <LogOut size={16} aria-hidden="true" /> Sign out
          </button>
        </div>
      )}
    </div>
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
      <UserMenu />
    </header>
  )
}
