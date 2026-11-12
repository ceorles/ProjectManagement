import { Download, LogOut, X } from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import { useInstallPrompt } from '../../hooks/useInstallPrompt'
import { ROLES } from '../../utils/constants'
import { navigationFor } from '../../utils/navigation'
import { initials } from '../../utils/roles'
import Logo from './Logo'

/**
 * Main navigation. Always visible on desktop; on tablets and phones it is a
 * drawer that the hamburger button in the top bar opens.
 */
export default function Sidebar({ open, onClose, unread }) {
  const { user, logout } = useAuth()
  const { canInstall, install } = useInstallPrompt()
  const sections = navigationFor(user)

  return (
    <aside className={`sidebar ${open ? 'is-open' : ''}`} id="app-sidebar" aria-label="Main navigation">
      <div className="sidebar__brand">
        <Logo onDark />
        <button type="button" className="sidebar__close" onClick={onClose} aria-label="Close menu">
          <X size={20} />
        </button>
      </div>

      <nav className="sidebar__nav">
        {sections.map((section) => (
          <div key={section.title} className="sidebar__section">
            <p className="sidebar__heading">{section.title}</p>
            <ul>
              {section.items.map((item) => (
                <li key={item.to}>
                  <NavLink
                    to={item.to} onClick={onClose}
                    className={({ isActive }) => `sidebar__link ${isActive ? 'is-active' : ''}`}
                  >
                    <item.icon size={18} aria-hidden="true" />
                    <span className="grow">{item.label}</span>
                    {item.badge === 'notifications' && unread > 0 && (
                      <span className="sidebar__badge" aria-label={`${unread} unread`}>
                        {unread > 99 ? '99+' : unread}
                      </span>
                    )}
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>

      <div className="sidebar__footer">
        {canInstall && (
          <button type="button" className="sidebar__link sidebar__link--button" onClick={install}>
            <Download size={18} aria-hidden="true" />
            <span>Install app</span>
          </button>
        )}
        <div className="sidebar__user">
          <span className="avatar avatar--on-dark">{initials(user)}</span>
          <div className="grow">
            <p className="sidebar__user-name truncate">{user.full_name}</p>
            <p className="sidebar__user-role">{ROLES[user.role]}</p>
          </div>
          <button type="button" className="sidebar__logout" onClick={logout} aria-label="Sign out" title="Sign out">
            <LogOut size={18} />
          </button>
        </div>
      </div>
    </aside>
  )
}
