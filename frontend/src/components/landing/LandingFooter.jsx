export default function LandingFooter({ profile }) {
  return (
    <footer className="landing-footer">
      <div className="landing-container landing-footer__inner">
        <p><strong>{profile.name}</strong>{profile.institution && ` · ${profile.institution}`}</p>
      </div>
    </footer>
  )
}
