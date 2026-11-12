import { QRCodeSVG } from 'qrcode.react'

/**
 * The reservation code as text and as a QR code. The student shows it at the
 * librarian desk, where it is typed or scanned into the Check-in Desk page.
 */
export default function ReservationPass({ code, caption }) {
  return (
    <div className="pass">
      <div className="pass__qr">
        <QRCodeSVG value={code} size={132} level="M" marginSize={0}
          fgColor="#0b2559" title={`Reservation code ${code}`} />
      </div>
      <div className="pass__text">
        <p className="pass__label">Reservation code</p>
        <p className="pass__code mono">{code.slice(0, 4)} {code.slice(4)}</p>
        {caption && <p className="muted small">{caption}</p>}
      </div>
    </div>
  )
}
