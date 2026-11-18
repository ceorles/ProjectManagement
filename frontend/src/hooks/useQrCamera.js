import { useCallback, useEffect, useRef, useState } from 'react'

// Reading about eight frames a second is fast enough and keeps phones cool.
const SCAN_INTERVAL_MS = 120
const MAX_SCAN_SIZE = 720

/**
 * Opens the camera, shows it in `videoRef` and calls `onDecode` with the text of
 * any QR code it sees. The camera is always released when the component using
 * this hook goes away, when the page is hidden, and before switching cameras.
 */
export function useQrCamera({ paused, onDecode }) {
  const videoRef = useRef(null)
  const pausedRef = useRef(paused)
  const onDecodeRef = useRef(onDecode)
  const [status, setStatus] = useState('starting') // starting | live | error
  const [error, setError] = useState(null)
  const [cameras, setCameras] = useState([])
  const [activeId, setActiveId] = useState(null)
  const [request, setRequest] = useState({ deviceId: null, attempt: 0 })

  useEffect(() => {
    pausedRef.current = paused
    onDecodeRef.current = onDecode
  })

  useEffect(() => {
    let cancelled = false
    let stream = null
    let frame = 0

    const release = () => {
      cancelAnimationFrame(frame)
      stream?.getTracks().forEach((track) => track.stop())
      stream = null
      if (videoRef.current) videoRef.current.srcObject = null
    }

    const scan = (jsQR) => {
      const canvas = document.createElement('canvas')
      const context = canvas.getContext('2d', { willReadFrequently: true })
      let last = 0
      const tick = (time) => {
        if (cancelled) return
        frame = requestAnimationFrame(tick)
        const video = videoRef.current
        if (pausedRef.current || time - last < SCAN_INTERVAL_MS) return
        if (!video || video.readyState < 2 || !video.videoWidth) return
        last = time
        const scale = Math.min(1, MAX_SCAN_SIZE / Math.max(video.videoWidth, video.videoHeight))
        canvas.width = Math.round(video.videoWidth * scale)
        canvas.height = Math.round(video.videoHeight * scale)
        context.drawImage(video, 0, 0, canvas.width, canvas.height)
        const image = context.getImageData(0, 0, canvas.width, canvas.height)
        const found = jsQR(image.data, image.width, image.height)
        if (found?.data) onDecodeRef.current(found.data)
      }
      frame = requestAnimationFrame(tick)
    }

    const start = async () => {
      setStatus('starting')
      setError(null)
      try {
        if (!window.isSecureContext) throw Object.assign(new Error(), { name: 'InsecureContext' })
        if (!navigator.mediaDevices?.getUserMedia) throw Object.assign(new Error(), { name: 'NotFoundError' })

        const { default: jsQR } = await import('jsqr')
        if (cancelled) return
        const opened = await navigator.mediaDevices.getUserMedia({
          audio: false,
          video: {
            ...(request.deviceId
              ? { deviceId: { exact: request.deviceId } }
              : { facingMode: { ideal: 'environment' } }), // the rear camera on phones
            width: { ideal: 1280 },
            height: { ideal: 720 },
          },
        })
        // The dialog may have closed while the browser was asking for permission.
        if (cancelled) {
          opened.getTracks().forEach((track) => track.stop())
          return
        }
        stream = opened
        const video = videoRef.current
        video.srcObject = stream
        await video.play()
        if (cancelled) return

        // Device names and the full list are only available after permission.
        const devices = await navigator.mediaDevices.enumerateDevices()
        if (cancelled) return
        setCameras(devices.filter((device) => device.kind === 'videoinput'))
        setActiveId(stream.getVideoTracks()[0]?.getSettings().deviceId ?? null)
        setStatus('live')
        scan(jsQR)
      } catch (failure) {
        if (cancelled) return
        release()
        setError(failure)
        setStatus('error')
      }
    }

    const onVisibility = () => {
      if (document.hidden) {
        cancelled = true
        release()
      } else {
        setRequest((current) => ({ ...current, attempt: current.attempt + 1 }))
      }
    }

    document.addEventListener('visibilitychange', onVisibility)
    start()
    return () => {
      cancelled = true
      document.removeEventListener('visibilitychange', onVisibility)
      release()
    }
  }, [request])

  const retry = useCallback(() => {
    setRequest((current) => ({ ...current, attempt: current.attempt + 1 }))
  }, [])

  const switchCamera = useCallback(() => {
    if (cameras.length < 2) return
    const index = cameras.findIndex((camera) => camera.deviceId === activeId)
    const next = cameras[(index + 1) % cameras.length]
    setRequest((current) => ({ deviceId: next.deviceId, attempt: current.attempt + 1 }))
  }, [cameras, activeId])

  return { videoRef, status, error, canSwitch: cameras.length > 1, retry, switchCamera }
}
