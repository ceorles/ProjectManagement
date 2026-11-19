const INSTALLED_MODES = ['standalone', 'fullscreen', 'minimal-ui', 'window-controls-overlay']

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
    event.preventDefault()
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

export async function promptInstall() {
  if (!promptEvent) return 'unavailable'
  const event = promptEvent
  event.prompt()
  const { outcome } = await event.userChoice
  promptEvent = null
  notify()
  return outcome
}

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
