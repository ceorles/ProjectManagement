/**
 * The single place the app talks to the backend.
 *
 * - The access token lives only in this module's memory. It is never written
 *   to localStorage, so a script injected into the page cannot steal a
 *   long-lived credential.
 * - The refresh token is an HttpOnly cookie that only the browser can send.
 *   When a request comes back 401, the client silently asks for a new access
 *   token once and repeats the request.
 */
import { API_BASE_URL } from '../config'

let accessToken = null
let refreshInFlight = null
let sessionExpiredHandler = null

export class ApiError extends Error {
  constructor({ status = 0, code = 'error', message = 'Something went wrong.', fields = null }) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.fields = fields
  }

  /** True when the request never reached the server (offline, server down). */
  get isNetworkError() {
    return this.status === 0
  }
}

export function setAccessToken(token) {
  accessToken = token
}

export function hasAccessToken() {
  return Boolean(accessToken)
}

/** Called when the session can no longer be refreshed (expired or revoked). */
export function onSessionExpired(handler) {
  sessionExpiredHandler = handler
}

function buildUrl(path, params) {
  const url = `${API_BASE_URL}${path}`
  if (!params) return url
  const query = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') query.append(key, value)
  })
  const text = query.toString()
  return text ? `${url}?${text}` : url
}

async function send(path, { method = 'GET', body, params, auth = true, headers = {}, signal } = {}) {
  const requestHeaders = { Accept: 'application/json', ...headers }
  if (body !== undefined) requestHeaders['Content-Type'] = 'application/json'
  if (auth && accessToken) requestHeaders.Authorization = `Bearer ${accessToken}`

  let response
  try {
    response = await fetch(buildUrl(path, params), {
      method,
      headers: requestHeaders,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      credentials: 'include', // lets the browser send the refresh cookie
      signal,
    })
  } catch (error) {
    if (error.name === 'AbortError') throw error
    throw new ApiError({
      status: 0,
      code: 'network_error',
      message: navigator.onLine
        ? 'The server could not be reached. Please try again in a moment.'
        : 'You are offline. Check your connection and try again.',
    })
  }

  let data = null
  if (response.status !== 204) {
    const text = await response.text()
    if (text) {
      try {
        data = JSON.parse(text)
      } catch {
        data = null // not JSON: e.g. a proxy error page
      }
    }
  }

  if (!response.ok) {
    const error = data?.error || {}
    throw new ApiError({
      status: response.status,
      code: error.code || 'error',
      message:
        error.message ||
        (response.status >= 500
          ? 'The server ran into a problem. Please try again.'
          : 'The request could not be completed.'),
      fields: error.fields || null,
    })
  }
  return data
}

/**
 * Exchange the refresh cookie for a new access token. Concurrent callers
 * share one request, so two tabs or two components never race each other.
 */
export function refreshSession() {
  if (!refreshInFlight) {
    refreshInFlight = send('/auth/refresh/', {
      method: 'POST',
      auth: false,
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
    })
      .then((data) => {
        accessToken = data.access
        return data
      })
      .finally(() => {
        refreshInFlight = null
      })
  }
  return refreshInFlight
}

export async function request(path, options = {}) {
  try {
    return await send(path, options)
  } catch (error) {
    const canRetry = error instanceof ApiError && error.status === 401 && options.auth !== false
    if (!canRetry) throw error

    try {
      await refreshSession()
    } catch (refreshError) {
      if (refreshError instanceof ApiError && !refreshError.isNetworkError) {
        accessToken = null
        sessionExpiredHandler?.()
      }
      throw refreshError
    }
    return send(path, options)
  }
}

export const api = {
  get: (path, params, options) => request(path, { ...options, params }),
  post: (path, body = {}, options) => request(path, { ...options, method: 'POST', body }),
  put: (path, body, options) => request(path, { ...options, method: 'PUT', body }),
  patch: (path, body, options) => request(path, { ...options, method: 'PATCH', body }),
  delete: (path, options) => request(path, { ...options, method: 'DELETE' }),
}
