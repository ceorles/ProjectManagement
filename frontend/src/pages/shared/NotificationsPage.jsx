import { useState } from 'react'
import { Bell, CheckCheck, Trash2 } from 'lucide-react'
import { useNavigate, useOutletContext } from 'react-router-dom'
import Button from '../../components/common/Button'
import { EmptyState, QueryBoundary } from '../../components/common/Feedback'
import PageHeader from '../../components/common/PageHeader'
import Pagination from '../../components/common/Pagination'
import Tabs from '../../components/common/Tabs'
import { POLL } from '../../config'
import { useAction } from '../../hooks/useAction'
import { useApiQuery } from '../../hooks/useApiQuery'
import { useLibrary } from '../../hooks/useLibrary'
import { notificationService } from '../../services'
import { formatRelative } from '../../utils/datetime'

const TABS = [
  { value: 'all', label: 'All' },
  { value: 'unread', label: 'Unread' },
]

/** Everything the portal has told this user, newest first. */
export default function NotificationsPage() {
  const { timeZone } = useLibrary()
  const { refreshUnread } = useOutletContext()
  const navigate = useNavigate()
  const [filter, setFilter] = useState('all')
  const [page, setPage] = useState(1)

  const query = useApiQuery(
    () => notificationService.list({ unread: filter === 'unread' ? 'true' : undefined, page }),
    [filter, page], { interval: POLL.notifications, keepPrevious: true },
  )
  const refresh = () => {
    query.refetch()
    refreshUnread()
  }

  const [markAll, marking] = useAction(notificationService.markAllRead, {
    success: 'All notifications marked as read.', onSuccess: refresh,
  })
  const [remove] = useAction((item) => notificationService.remove(item.id), { onSuccess: refresh })

  const open = async (item) => {
    if (!item.is_read) {
      try {
        await notificationService.markRead(item.id)
        refresh()
      } catch {
        // Not critical: it stays unread.
      }
    }
    if (item.link) navigate(item.link)
  }

  return (
    <>
      <PageHeader
        title="Notifications"
        description="Confirmations, reminders and changes to your reservations."
        actions={(
          <Button variant="secondary" icon={CheckCheck} loading={marking} onClick={markAll}>
            Mark all as read
          </Button>
        )}
      />
      <div style={{ marginBottom: 16 }}>
        <Tabs tabs={TABS} value={filter} onChange={(value) => { setFilter(value); setPage(1) }} label="Filter" />
      </div>

      <section className="card">
        <QueryBoundary query={query} loadingLabel="Loading notifications...">
          {(data) => (data.results.length === 0 ? (
            <EmptyState icon={Bell}
              title={filter === 'unread' ? 'You are all caught up' : 'No notifications yet'}
              description={filter === 'unread'
                ? 'There is nothing new to read.'
                : 'When something happens to one of your reservations, you will see it here.'} />
          ) : (
            <>
              <ul className="list-rows">
                {data.results.map((item) => (
                  <li key={item.id} className="notification-item">
                    <button type="button" className={`notification-row ${item.is_read ? '' : 'is-unread'}`}
                      onClick={() => open(item)}>
                      <span className={`notification-row__dot notification-row__dot--${item.level}`} aria-hidden="true" />
                      <span className="grow">
                        <span className="notification-row__title">
                          {item.title}{!item.is_read && <span className="sr-only"> (unread)</span>}
                        </span>
                        <span className="notification-row__message">{item.message}</span>
                        <span className="notification-row__time">{formatRelative(item.created_at, timeZone)}</span>
                      </span>
                    </button>
                    <button type="button" className="icon-button" onClick={() => remove(item)}
                      aria-label={`Delete notification: ${item.title}`}>
                      <Trash2 size={16} />
                    </button>
                  </li>
                ))}
              </ul>
              <Pagination page={page} count={data.count} onChange={setPage} />
            </>
          ))}
        </QueryBoundary>
      </section>
    </>
  )
}
