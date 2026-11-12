import { Armchair, CalendarCheck, DoorOpen, ScanLine } from 'lucide-react'
import { APP_NAME, INSTITUTION_NAME } from '../../config'
import Logo from '../../components/layout/Logo'
import './auth.css'

const HIGHLIGHTS = [
  { icon: Armchair, title: 'Pick your seat', text: 'See the floor map and choose a seat that is free when you need it.' },
  { icon: DoorOpen, title: 'Book a study room', text: 'Reserve a room for your group, with the facilities you need.' },
  { icon: CalendarCheck, title: 'Live availability', text: 'What you see is what is free right now. No double bookings.' },
  { icon: ScanLine, title: 'Quick check-in', text: 'Check in from your phone or show your code at the desk.' },
]

/** Two-panel layout for the sign-in and registration pages. */
export default function AuthLayout({ title, subtitle, children, footer, wide = false }) {
  return (
    <div className="auth">
      <aside className="auth__panel">
        <Logo onDark size={44} />
        <div className="auth__pitch">
          <h2>Your place in the library, reserved.</h2>
          <p>
            {APP_NAME} is the seat and study room reservation portal of the {INSTITUTION_NAME}.
          </p>
          <ul className="auth__highlights">
            {HIGHLIGHTS.map((item) => (
              <li key={item.title}>
                <span className="auth__highlight-icon"><item.icon size={18} aria-hidden="true" /></span>
                <span>
                  <strong>{item.title}</strong>
                  <span>{item.text}</span>
                </span>
              </li>
            ))}
          </ul>
        </div>
        <p className="auth__panel-footer">{INSTITUTION_NAME}</p>
      </aside>

      <main className="auth__main">
        <div className={`auth__card ${wide ? 'auth__card--wide' : ''}`}>
          <div className="auth__mobile-logo"><Logo size={40} /></div>
          <h1 className="auth__title">{title}</h1>
          <p className="auth__subtitle">{subtitle}</p>
          {children}
          {footer && <p className="auth__footer">{footer}</p>}
        </div>
      </main>
    </div>
  )
}
