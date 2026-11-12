import { useCallback, useEffect, useState } from 'react'

/**
 * Lets the app offer its own "Install app" button. Browsers that support
 * installation fire `beforeinstallprompt`; we keep the event and trigger it
 * when the user asks. (Safari on iOS installs through Share > Add to Home
 * Screen and never fires this event.)
 */
export function useInstallPrompt() {
  const [promptEvent, setPromptEvent] = useState(null)

  useEffect(() => {
    const onPrompt = (event) => {
      event.preventDefault()
      setPromptEvent(event)
    }
    const onInstalled = () => setPromptEvent(null)
    window.addEventListener('beforeinstallprompt', onPrompt)
    window.addEventListener('appinstalled', onInstalled)
    return () => {
      window.removeEventListener('beforeinstallprompt', onPrompt)
      window.removeEventListener('appinstalled', onInstalled)
    }
  }, [])

  const install = useCallback(async () => {
    if (!promptEvent) return
    promptEvent.prompt()
    await promptEvent.userChoice
    setPromptEvent(null)
  }, [promptEvent])

  return { canInstall: Boolean(promptEvent), install }
}
