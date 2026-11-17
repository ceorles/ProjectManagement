import { Link } from 'react-router-dom'

export default function LandingFooter({ profile }) {
  return (
    <footer className="landing-footer">
      <div className="landing-container landing-footer__inner">
        <p><strong>{profile.name}</strong>{profile.institution && ` · ${profile.institution}`}</p>
        <p className="landing-footer__links">
          <a href="#home">Back to top</a>
          <Link to="/login">Login</Link>
        </p>
      </div>
    </footer>
  )
}
