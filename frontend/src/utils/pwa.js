/**
 * Installing the app (PWA), in one place for the whole application.
 *
 * Browsers that support installation fire `beforeinstallprompt` once, early,
 * often before any React component has mounted. This module is imported by
 * main.jsx, so it is listening from the very first moment and keeps the event
 * until someone presses "Install app" - in the sidebar or on the landing page.
 */

const INSTALLED_MODES = ['standalone', 'fullscreen', 'minimal-ui', 'window-controls-overlay']

/** True when DLL Library is running as an installed app, not in a browser tab. */
export function isStandalone() {
  if (typeof window === 'undefined') return false
  if (window.navigator.standalone === true) return true // iOS home-screen app
  return INSTALLED_MODES.some((mode) => window.matchMedia?.(`(display-mode: ${mode})`).matches)
}

let promptEvent = null
let installed = isStandalone()
const listeners = new Set()

function notify() {
  listeners.forEach((listener) => listener())
}

if (typeof window !== 'undefined') {
  window.addEventListener('beforeinstallprompt', (event) => {
    event.preventDefault() // keep it for our own button instead of the browser's mini-bar
    promptEvent = event
    notify()
  })
  window.addEventListener('appinstalled', () => {
    promptEvent = null
    installed = true
    notify()
  })
}

export function subscribeInstall(listener) {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

export function getInstallState() {
  return { canPrompt: Boolean(promptEvent), installed }
}

/**
 * Show the browser's own install dialog. Resolves to 'accepted',
 * 'dismissed' or 'unavailable' (the browser has not offered installation).
 */
export async function promptInstall() {
  if (!promptEvent) return 'unavailable'
  const event = promptEvent
  event.prompt()
  const { outcome } = await event.userChoice
  promptEvent = null // a prompt can only be used once
  notify()
  return outcome
}

/** Which manual steps to suggest when the browser has not offered installation. */
export function installPlatform() {
  const agent = window.navigator.userAgent
  const ios = /iPad|iPhone|iPod/.test(agent)
    || (window.navigator.platform === 'MacIntel' && window.navigator.maxTouchPoints > 1)
  if (ios) return 'ios'
  if (/Android/i.test(agent)) return 'android'
  if (/Firefox\//.test(agent)) return 'firefox'
  if (/Safari\//.test(agent) && !/Chrome|Chromium|Edg\//.test(agent)) return 'safari'
  return 'desktop'
}
