import { useEffect, useState } from 'react'
import { Download, LayoutDashboard, LogIn, Menu, X } from 'lucide-react'
import { useAuth } from '../../hooks/useAuth'
import { useDismiss } from '../../hooks/useDismiss'
import { useInstallPrompt } from '../../hooks/useInstallPrompt'
import Button from '../common/Button'
import InstallHelpDialog from '../common/InstallHelpDialog'
import Logo from '../layout/Logo'

const LANDING_LINKS = [
  { href: '#home', label: 'Home' },
  { href: '#services', label: 'Our Services' },
  { href: '#about', label: 'About' },
  { href: '#contact', label: 'Contact' },
]

const WIDE = '(min-width: 900px)'

/**
 * Landing page header: brand, section links, Install and Login. On narrow
 * screens the links and Install move into a menu; Login stays visible.
 */
export default function LandingHeader() {
  const { isAuthenticated } = useAuth()
  const { installed, install, helpOpen, closeHelp } = useInstallPrompt()
  const [open, setOpen] = useState(false)
  const ref = useDismiss(open, () => setOpen(false))

  // The menu closes when the window grows wide enough to show the full bar.
  useEffect(() => {
    if (!open) return undefined
    const media = window.matchMedia(WIDE)
    const onChange = (event) => {
      if (event.matches) setOpen(false)
    }
    media.addEventListener('change', onChange)
    return () => media.removeEventListener('change', onChange)
  }, [open])

  const account = isAuthenticated
    ? <Button to="/dashboard" size="sm" icon={LayoutDashboard}>Dashboard</Button>
    : <Button to="/login" size="sm" icon={LogIn}>Login</Button>

  return (
    <header className="landing-header" ref={ref}>
      <div className="landing-header__bar">
        <a href="#home" className="landing-header__brand" aria-label="DLL Library home">
          <Logo size={38} />
        </a>

        <nav className="landing-nav" aria-label="Sections">
          {LANDING_LINKS.map((link) => (
            <a key={link.href} href={link.href} className="landing-nav__link">{link.label}</a>
          ))}
        </nav>

        <div className="landing-header__actions">
          {!installed && (
            <Button variant="secondary" size="sm" icon={Download} onClick={install}
              className="landing-header__install">
              Install
            </Button>
          )}
          {account}
          <button
            type="button" className="icon-button landing-header__menu"
            onClick={() => setOpen((value) => !value)}
            aria-label={open ? 'Close menu' : 'Open menu'} aria-expanded={open}
            aria-controls="landing-menu"
          >
            {open ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>
      </div>

      {open && (
        <div className="landing-menu" id="landing-menu">
          <nav aria-label="Sections">
            {LANDING_LINKS.map((link) => (
              <a key={link.href} href={link.href} className="landing-menu__link"
                onClick={() => setOpen(false)}>
                {link.label}
              </a>
            ))}
          </nav>
          {!installed && (
            <Button variant="secondary" block icon={Download}
              onClick={() => { setOpen(false); install() }}>
              Install app
            </Button>
          )}
        </div>
      )}
      <InstallHelpDialog open={helpOpen} onClose={closeHelp} />
    </header>
  )
}
