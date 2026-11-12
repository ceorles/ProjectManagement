import { CircleAlert, Inbox, LoaderCircle, RefreshCw, WifiOff } from 'lucide-react'
import Button from './Button'

/** Loading, empty and error states. Every data view uses one of these. */

export function Spinner({ size = 20, className = '' }) {
  return <LoaderCircle size={size} className={`spinner ${className}`} aria-hidden="true" />
}

export function LoadingState({ label = 'Loading...', compact = false }) {
  return (
    <div className={`state ${compact ? 'state--compact' : ''}`} role="status" aria-live="polite">
      <Spinner size={compact ? 20 : 28} />
      <p className="muted small">{label}</p>
    </div>
  )
}

export function EmptyState({ icon: Icon = Inbox, title, description, action, compact = false }) {
  return (
    <div className={`state ${compact ? 'state--compact' : ''}`}>
      <span className="state__icon"><Icon size={compact ? 20 : 26} aria-hidden="true" /></span>
      <p className="state__title">{title}</p>
      {description && <p className="muted small state__text">{description}</p>}
      {action}
    </div>
  )
}

export function ErrorState({ error, onRetry, compact = false }) {
  const offline = error?.isNetworkError
  const Icon = offline ? WifiOff : CircleAlert
  return (
    <div className={`state state--error ${compact ? 'state--compact' : ''}`} role="alert">
      <span className="state__icon"><Icon size={compact ? 20 : 26} aria-hidden="true" /></span>
      <p className="state__title">
        {offline ? 'Cannot reach the library server' : 'This could not be loaded'}
      </p>
      <p className="muted small state__text">
        {error?.message || 'Something went wrong. Please try again.'}
      </p>
      {onRetry && (
        <Button variant="secondary" size="sm" icon={RefreshCw} onClick={onRetry}>Try again</Button>
      )}
    </div>
  )
}

/**
 * Standard wrapper for anything loaded with useApiQuery: shows the loading
 * state first, an error with a retry button if it failed, otherwise the
 * content.
 */
export function QueryBoundary({ query, loadingLabel, compact, children }) {
  if (query.data !== null && query.data !== undefined) return children(query.data)
  if (query.error) return <ErrorState error={query.error} onRetry={query.refetch} compact={compact} />
  return <LoadingState label={loadingLabel} compact={compact} />
}
