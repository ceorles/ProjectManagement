import { Component } from 'react'
import { CircleAlert, RefreshCw } from 'lucide-react'

/**
 * Catches an unexpected error while rendering and shows a recovery screen
 * instead of a blank page. `resetKey` (the current URL) clears the error
 * when the user navigates somewhere else.
 */
export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { error: null, resetKey: props.resetKey }
  }

  static getDerivedStateFromError(error) {
    return { error }
  }

  static getDerivedStateFromProps(props, state) {
    if (props.resetKey !== state.resetKey) return { error: null, resetKey: props.resetKey }
    return null
  }

  componentDidCatch(error, info) {
    console.error('Unexpected error while rendering', error, info.componentStack)
  }

  render() {
    if (!this.state.error) return this.props.children
    return (
      <div className="state state--error" role="alert">
        <span className="state__icon"><CircleAlert size={26} aria-hidden="true" /></span>
        <p className="state__title">Something went wrong on this page</p>
        <p className="muted small state__text">
          Your reservations are not affected. Reload the page to continue; if it keeps
          happening, please tell the library staff.
        </p>
        <button type="button" className="btn btn--secondary btn--sm" onClick={() => window.location.reload()}>
          <RefreshCw size={15} aria-hidden="true" /> <span>Reload</span>
        </button>
      </div>
    )
  }
}
