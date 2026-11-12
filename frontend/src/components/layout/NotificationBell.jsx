import { useState } from 'react'
import { Bell } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import { useApiQuery } from '../../hooks/useApiQuery'
import { useDismiss } from '../../hooks/useDismiss'
import { useLibrary } from '../../hooks/useLibrary'
import { notificationService } from '../../services'
import { formatRelative } from '../../utils/datetime'
import { EmptyState, QueryBoundary } from '../common/Feedback'

function RecentNotifications({ onOpen }) {
  const { timeZone } = useLibrary()
  const query = useApiQuery(() => notificationService.list({ page_size: 6 }), [])
  return (
    <QueryBoundary query={query} compact>
      {(data) => (data.results.length === 0 ? (
        <EmptyState compact icon={Bell} title="No notifications yet"
          description="Updates about your reservations appear here." />
      ) : (
        <ul className="popover__list">
          {data.results.map((item) => (
            <li key={item.id}>
              <button type="button" className={`notification-row ${item.is_read ? '' : 'is-unread'}`}
                onClick={() => onOpen(item)}>
                <span className={`notification-row__dot notification-row__dot--${item.level}`} aria-hidden="true" />
                <span className="grow">
                  <span className="notification-row__title">{item.title}</span>
                  <span className="notification-row__message">{item.message}</span>
                  <span className="notification-row__time">{formatRelative(item.created_at, timeZone)}</span>
                </span>
              </button>
            </li>
          ))}
        </ul>
      ))}
    </QueryBoundary>
  )
}

export default function NotificationBell({ unread, onChange }) {
  const [open, setOpen] = useState(false)
  const navigate = useNavigate()
  const ref = useDismiss(open, () => setOpen(false))

  const openNotification = async (item) => {
    setOpen(false)
    if (!item.is_read) {
      try {
        await notificationService.markRead(item.id)
        onChange()
      } catch {
        // Not critical: it simply stays unread.
      }
    }
    navigate(item.link || '/notifications')
  }

  return (
    <div className="popover-anchor" ref={ref}>
      <button
        type="button" className="icon-button topbar__bell" onClick={() => setOpen((value) => !value)}
        aria-haspopup="true" aria-expanded={open}
        aria-label={unread ? `Notifications, ${unread} unread` : 'Notifications'}
      >
        <Bell size={20} />
        {unread > 0 && <span className="topbar__bell-count">{unread > 9 ? '9+' : unread}</span>}
      </button>
      {open && (
        <div className="popover popover--notifications" role="dialog" aria-label="Notifications">
          <div className="popover__header">
            <h2>Notifications</h2>
            {unread > 0 && <span className="badge badge--yellow">{unread} new</span>}
          </div>
          <RecentNotifications onOpen={openNotification} />
          <Link to="/notifications" className="popover__footer" onClick={() => setOpen(false)}>
            View all notifications
          </Link>
        </div>
      )}
    </div>
  )
}
