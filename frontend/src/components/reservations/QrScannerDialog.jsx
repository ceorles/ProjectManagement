import { useRef, useState } from 'react'
import { AlertTriangle, CheckCircle2, RefreshCw, ScanLine, SwitchCamera, VideoOff, XCircle } from 'lucide-react'
import { useQrCamera } from '../../hooks/useQrCamera'
import { reservationService } from '../../services'
import {
  INVALID_QR, describeCameraError, describeScanFailure, parseReservationCode,
} from '../../utils/checkInScan'
import Button from '../common/Button'
import { Spinner } from '../common/Feedback'
import Modal from '../common/Modal'

const RESULT_ICON = { success: CheckCircle2, warning: AlertTriangle, danger: XCircle }

/**
 * Reads a reservation QR code with the camera and sends it through the same
 * lookup and check-in requests as the desk's code box. Only the server's answer
 * decides what is shown. `onScanned` receives the reservation that was found.
 */
export default function QrScannerDialog({ onClose, onScanned }) {
  const [checking, setChecking] = useState(false)
  const [result, setResult] = useState(null)
  // Set the moment a code is read, so one QR code can only be submitted once.
  const lockedRef = useRef(false)

  const submit = async (text) => {
    if (lockedRef.current) return
    lockedRef.current = true

    const code = parseReservationCode(text)
    if (!code) {
      setResult(INVALID_QR)
      return
    }

    setChecking(true)
    let reservation = null
    try {
      reservation = await reservationService.lookup(code)
      const updated = await reservationService.checkIn(reservation.id)
      if (updated.status !== 'checked_in') throw new Error('The check-in was not recorded.')
      reservation = updated
      setResult({
        tone: 'success',
        title: 'Checked in',
        message: `${updated.student.full_name} is checked in to ${updated.resource.name}.`,
      })
    } catch (failure) {
      setResult(describeScanFailure(failure, reservation))
    } finally {
      setChecking(false)
    }
    if (reservation) onScanned(reservation)
  }

  const { videoRef, ...camera } = useQrCamera({ paused: checking || Boolean(result), onDecode: submit })

  const scanNext = () => {
    setResult(null)
    lockedRef.current = false
  }

  const failed = camera.status === 'error'
  const cameraProblem = failed ? describeCameraError(camera.error) : null
  const ResultIcon = result ? RESULT_ICON[result.tone] : null

  return (
    <Modal
      open onClose={onClose} busy={checking} title="Scan QR Code"
      description="Hold the student's reservation QR code inside the frame."
      footer={(
        <>
          {camera.canSwitch && !failed && (
            <Button variant="secondary" icon={SwitchCamera} onClick={camera.switchCamera} disabled={checking}>
              Switch camera
            </Button>
          )}
          <Button variant="ghost" onClick={onClose} disabled={checking}>Close</Button>
        </>
      )}
    >
      <div className="qr-scanner">
        {failed ? (
          <div className="qr-scanner__problem" role="alert">
            <VideoOff size={28} aria-hidden="true" />
            <h3>{cameraProblem.title}</h3>
            <p>{cameraProblem.message}</p>
            <p className="muted small">You can still type the reservation code on the Check-in Desk page.</p>
            <Button variant="secondary" icon={RefreshCw} onClick={camera.retry}>Try again</Button>
          </div>
        ) : (
          <div className="qr-scanner__view">
            <video ref={videoRef} className="qr-scanner__video" muted playsInline aria-label="Camera preview" />
            <div className="qr-scanner__frame" aria-hidden="true" />
            {(camera.status === 'starting' || checking) && (
              <div className="qr-scanner__overlay">
                <Spinner size={28} />
                <span>{checking ? 'Checking the reservation...' : 'Starting the camera...'}</span>
              </div>
            )}
          </div>
        )}

        {!failed && !result && (
          <p className="qr-scanner__hint" role="status">
            <ScanLine size={16} aria-hidden="true" />
            {camera.status === 'live' && !checking ? 'Looking for a QR code...' : 'Please wait...'}
          </p>
        )}

        {result && (
          <div className={`qr-scanner__result qr-scanner__result--${result.tone}`} role="alert">
            <ResultIcon size={22} aria-hidden="true" />
            <div className="grow">
              <p className="qr-scanner__result-title">{result.title}</p>
              <p className="small">{result.message}</p>
            </div>
            <Button size="sm" variant="secondary" icon={ScanLine} onClick={scanNext}>Scan next</Button>
          </div>
        )}
      </div>
    </Modal>
  )
}
