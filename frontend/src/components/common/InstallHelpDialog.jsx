import { Info } from 'lucide-react'
import { APP_NAME } from '../../config'
import { installPlatform } from '../../utils/pwa'
import Button from './Button'
import Modal from './Modal'

const STEPS = {
  ios: [
    'Open this page in Safari.',
    'Tap the Share button (the square with an arrow pointing up).',
    'Choose "Add to Home Screen", then tap "Add".',
  ],
  android: [
    'Open the browser menu (the three dots at the top right).',
    'Choose "Install app" or "Add to Home screen".',
    'Confirm by tapping "Install".',
  ],
  desktop: [
    'Look for the install icon at the right end of the address bar, or open the browser menu.',
    'Choose "Install DLL Library" (in Edge: Apps > Install this site as an app).',
    'Confirm by clicking "Install".',
  ],
  safari: [
    'In Safari on a Mac, open the File menu.',
    'Choose "Add to Dock".',
  ],
  firefox: [
    'Firefox on computers cannot install web apps.',
    'Open this page in Chrome, Edge or Safari to install it, or keep using it in the browser.',
  ],
}

/**
 * Shown when the browser has not offered its own install dialog: explains how
 * to install manually. It never claims that installation succeeded.
 */
export default function InstallHelpDialog({ open, onClose }) {
  if (!open) return null
  const steps = STEPS[installPlatform()]
  return (
    <Modal
      open onClose={onClose} size="sm" title={`Install ${APP_NAME}`}
      description="Add it to your home screen or desktop to open it like an app."
      footer={<Button variant="secondary" onClick={onClose}>Close</Button>}
    >
      <div className="stack">
        <ol className="install-steps">
          {steps.map((step) => <li key={step}>{step}</li>)}
        </ol>
        <p className="notice">
          <Info size={16} aria-hidden="true" />
          <span>
            Your browser has not offered to install the app on this visit. If you do not see the
            option, the app may already be installed on this device, or this browser does not
            support installing apps.
          </span>
        </p>
      </div>
    </Modal>
  )
}
