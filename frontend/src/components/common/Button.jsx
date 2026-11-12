import { Link } from 'react-router-dom'
import { Spinner } from './Feedback'

/**
 * The app's button. Renders a router link when `to` is given.
 *
 * variant: primary | secondary | accent | ghost | danger | danger-soft
 * size:    sm | md | lg
 * loading: shows a spinner and blocks further clicks (prevents double submits)
 */
export default function Button({
  variant = 'primary', size = 'md', icon: Icon, iconRight: IconRight, loading = false,
  block = false, to, type = 'button', disabled, className = '', children, ...rest
}) {
  const classes = [
    'btn', `btn--${variant}`, `btn--${size}`,
    block && 'btn--block', !children && 'btn--icon-only', className,
  ].filter(Boolean).join(' ')

  const content = (
    <>
      {loading ? <Spinner size={16} /> : Icon && <Icon size={size === 'sm' ? 15 : 17} aria-hidden="true" />}
      {children && <span>{children}</span>}
      {IconRight && !loading && <IconRight size={16} aria-hidden="true" />}
    </>
  )

  if (to && !disabled) {
    return <Link to={to} className={classes} {...rest}>{content}</Link>
  }
  return (
    <button
      type={type} className={classes} disabled={disabled || loading}
      aria-busy={loading || undefined} {...rest}
    >
      {content}
    </button>
  )
}
