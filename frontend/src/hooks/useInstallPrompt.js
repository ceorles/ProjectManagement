import { useCallback, useState, useSyncExternalStore } from 'react'
import { getInstallState, promptInstall, subscribeInstall } from '../utils/pwa'

let snapshot = getInstallState()
function read() {
  const next = getInstallState()
  if (next.canPrompt !== snapshot.canPrompt || next.installed !== snapshot.installed) snapshot = next
  return snapshot
}

/**
 * State and action for an "Install app" button.
 *
 *   installed  - already running as the installed app: hide the button.
 *   install()  - shows the browser's install dialog when it has offered one;
 *                otherwise opens the manual instructions (`helpOpen`).
 *
 * Nothing claims success on its own: the button disappears only when the
 * browser reports that the app was actually installed.
 */
export function useInstallPrompt() {
  const state = useSyncExternalStore(subscribeInstall, read, read)
  const [helpOpen, setHelpOpen] = useState(false)

  const install = useCallback(async () => {
    const outcome = await promptInstall()
    if (outcome === 'unavailable') setHelpOpen(true)
  }, [])

  return {
    installed: state.installed,
    canPrompt: state.canPrompt,
    install,
    helpOpen,
    closeHelp: () => setHelpOpen(false),
  }
}
