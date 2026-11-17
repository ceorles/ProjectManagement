// Build-time configuration. Values come from `.env` (see `.env.example`).

export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/+$/, '')
export const APP_NAME = import.meta.env.VITE_APP_NAME || 'DLL Library'
// Shown under the name in the logo.
export const APP_SUBTITLE = import.meta.env.VITE_APP_SUBTITLE || 'Reservation Portal'
export const INSTITUTION_NAME = import.meta.env.VITE_INSTITUTION_NAME || 'Dalubhasaan ng Lungsod ng Lucena'

// How often live data is refreshed while a page is visible (milliseconds).
export const POLL = {
  availability: 5000,
  reservations: 10000,
  dashboard: 15000,
  notifications: 20000,
}
