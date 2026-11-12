import { APP_NAME, INSTITUTION_NAME } from '../../config'

/** The app mark: a reader (yellow) over an open book. */
export function LogoMark({ size = 36 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 1024 1024" role="img" aria-label={`${APP_NAME} logo`}>
      <rect width="1024" height="1024" rx="224" fill="#103479" />
      <path d="M212 430l280 62v308l-280-62z" fill="#fff" />
      <path d="M532 492l280-62v308l-280 62z" fill="#fff" />
      <path d="M492 492h40v308h-40z" fill="#c3d5f7" />
      <circle cx="512" cy="312" r="96" fill="#f5b700" />
    </svg>
  )
}

export default function Logo({ size = 36, onDark = false }) {
  return (
    <span className={`logo ${onDark ? 'logo--on-dark' : ''}`}>
      <LogoMark size={size} />
      <span className="logo__text">
        <span className="logo__name">{APP_NAME}</span>
        <span className="logo__sub">{INSTITUTION_NAME}</span>
      </span>
    </span>
  )
}
