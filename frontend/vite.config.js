import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const appName = env.VITE_APP_NAME || 'LibReserve'

  // During development (and `vite preview`) requests to /api are forwarded to
  // the Django server. The browser then only ever talks to one origin, so the
  // login cookie is first-party and the app also works from a phone on the
  // same Wi-Fi without any CORS setup.
  const proxy = {
    '/api': {
      target: env.VITE_BACKEND_ORIGIN || 'http://127.0.0.1:8000',
      changeOrigin: true,
    },
  }

  return {
    plugins: [
      react(),
      VitePWA({
        registerType: 'autoUpdate',
        includeAssets: ['favicon.svg', 'apple-touch-icon.png'],
        manifest: {
          id: '/',
          name: `${appName} - Library Seat & Study Room Reservation`,
          short_name: appName,
          description:
            'Reserve library seats and study rooms, check in, and manage your reservations.',
          lang: 'en',
          start_url: '/',
          scope: '/',
          display: 'standalone',
          orientation: 'any',
          theme_color: '#103479',
          background_color: '#f4f6fb',
          categories: ['education', 'productivity'],
          icons: [
            { src: 'pwa-64x64.png', sizes: '64x64', type: 'image/png' },
            { src: 'pwa-192x192.png', sizes: '192x192', type: 'image/png' },
            { src: 'pwa-512x512.png', sizes: '512x512', type: 'image/png' },
            {
              src: 'maskable-512x512.png',
              sizes: '512x512',
              type: 'image/png',
              purpose: 'maskable',
            },
          ],
          shortcuts: [
            { name: 'Reserve a seat', url: '/seats' },
            { name: 'Study rooms', url: '/rooms' },
            { name: 'My reservations', url: '/reservations' },
          ],
        },
        workbox: {
          // Precache the application shell so it opens without a network.
          globPatterns: ['**/*.{js,css,html,svg,png,woff2}'],
          navigateFallback: '/index.html',
          // Never answer API or Django admin requests from the cache: every
          // booking action must reach the server and be confirmed by it.
          navigateFallbackDenylist: [/^\/api\//, /^\/admin\//],
          cleanupOutdatedCaches: true,
        },
      }),
    ],
    server: { proxy },
    preview: { proxy },
  }
})
