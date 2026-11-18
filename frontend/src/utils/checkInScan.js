// Turns what the camera read, and what the server answered, into plain messages.
// The server alone decides whether a check-in succeeded.

// The same alphabet the backend uses to generate reservation codes.
const RESERVATION_CODE = /^[ABCDEFGHJKMNPQRSTUVWXYZ23456789]{8}$/

/** The reservation code inside a scanned QR code, or null if it is not one of ours. */
export function parseReservationCode(text) {
  const code = String(text ?? '').replace(/\s+/g, '').toUpperCase()
  return RESERVATION_CODE.test(code) ? code : null
}

export const INVALID_QR = {
  tone: 'danger',
  title: 'Invalid QR code',
  message: 'This is not a DLL Library reservation QR code.',
}

function titleForStatus(reservation) {
  const reason = reservation?.cancel_reason || ''
  switch (reservation?.status) {
    case 'checked_in': return 'Already checked in'
    case 'pending': return 'Not approved yet'
    case 'rejected': return 'Reservation rejected'
    case 'completed': return 'Reservation completed'
    case 'no_show':
      return reason.startsWith('Automatically cancelled') ? 'Automatically cancelled' : 'Marked as no-show'
    case 'cancelled':
      return reason.includes('not reviewed') ? 'Reservation expired' : 'Reservation cancelled'
    default: return null
  }
}

/** Describes a failed lookup or check-in. `reservation` is set if the lookup worked. */
export function describeScanFailure(error, reservation) {
  if (error?.isNetworkError) {
    return { tone: 'danger', title: 'Server not reached', message: error.message }
  }
  if (error?.status === 401 || error?.status === 403) {
    return {
      tone: 'danger',
      title: 'Not allowed',
      message: 'Your account is not allowed to check in reservations.',
    }
  }
  if (error?.status === 404) {
    return {
      tone: 'danger',
      title: 'Reservation not found',
      message: 'No reservation has this code.',
    }
  }
  if (error?.code === 'too_early') {
    return { tone: 'warning', title: 'Too early to check in', message: error.message }
  }
  if (error?.code === 'checkin_closed') {
    return { tone: 'danger', title: 'Check-in period ended', message: error.message }
  }
  if (reservation?.status === 'checked_in') {
    return {
      tone: 'warning',
      title: 'Already checked in',
      message: 'This reservation has already been checked in.',
    }
  }
  return {
    tone: 'danger',
    title: titleForStatus(reservation) || 'Check-in failed',
    message: error?.message || 'The reservation could not be checked in.',
  }
}

/** Explains why the camera could not be opened. */
export function describeCameraError(error) {
  switch (error?.name) {
    case 'InsecureContext':
      return {
        title: 'Camera needs a secure connection',
        message: 'Browsers only allow the camera on HTTPS. Open the portal through its https:// address.',
      }
    case 'NotAllowedError':
    case 'SecurityError':
      return {
        title: 'Camera permission denied',
        message: 'Allow camera access for this site in your browser or app settings, then try again.',
      }
    case 'NotFoundError':
    case 'OverconstrainedError':
      return { title: 'No camera found', message: 'This device has no camera that can be used.' }
    case 'NotReadableError':
    case 'AbortError':
      return {
        title: 'Camera is busy',
        message: 'Another app may be using the camera. Close it, then try again.',
      }
    default:
      return { title: 'Camera could not start', message: 'Something stopped the camera from starting.' }
  }
}
