import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { registerSW } from 'virtual:pwa-register'
import '@fontsource-variable/inter'
import './styles/tokens.css'
import './styles/base.css'
import './components/common/common.css'
import App from './App.jsx'

// Installs the service worker that makes the app installable and lets its
// shell open offline. A new version is picked up automatically.
registerSW({ immediate: true })

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
