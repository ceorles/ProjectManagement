import { RESERVATION_STATUS } from '../../utils/constants'

/** Small coloured label. tone: blue | green | yellow | orange | red | gray */
export default function Badge({ tone = 'gray', icon: Icon, dot = false, children, className = '' }) {
  return (
    <span className={`badge badge--${tone} ${className}`}>
      {dot && <span className="badge__dot" aria-hidden="true" />}
      {Icon && <Icon size={13} aria-hidden="true" />}
      {children}
    </span>
  )
}

/** Reservation status, always in the same colour everywhere in the app. */
export function StatusBadge({ status }) {
  const meta = RESERVATION_STATUS[status] || { label: status, tone: 'gray' }
  return <Badge tone={meta.tone} dot>{meta.label}</Badge>
}
