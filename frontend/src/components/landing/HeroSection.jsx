import { Armchair } from 'lucide-react'
import { scheduleFor } from '../../utils/booking'
import { formatTime, libraryNow } from '../../utils/datetime'
import Button from '../common/Button'

function todayStatus(data) {
  const now = libraryNow(data.time_zone)
  const today = scheduleFor(data, now.date)
  if (!today.isOpen) return { open: false, text: 'Closed today' }
  if (now.minutes >= today.opens && now.minutes < today.closes) {
    return { open: true, text: `Open now · until ${formatTime(today.closesAt)}` }
  }
  return {
    open: false,
    text: `Closed now · today ${formatTime(today.opensAt)} - ${formatTime(today.closesAt)}`,
  }
}

/** #home: name, tagline, introduction and today's opening status. */
export function HeroSection({ data }) {
  const { profile } = data
  const status = todayStatus(data)
  const backdrop = data.photos[0]?.image
  return (
    <section id="home" className="landing-hero"
      style={backdrop ? { '--hero-photo': `url("${backdrop}")` } : undefined}>
      <div className="landing-hero__inner">
        {profile.institution && <p className="landing-hero__institution">{profile.institution}</p>}
        <h1 className="landing-hero__title">{profile.name}</h1>
        {profile.tagline && <p className="landing-hero__tagline">{profile.tagline}</p>}
        {profile.introduction && <p className="landing-hero__intro">{profile.introduction}</p>}
        <div className="landing-hero__actions">
          <Button to="/login" variant="accent" size="lg" icon={Armchair}>Reserve a seat</Button>
          <a href="#services" className="btn btn--lg landing-hero__ghost">Our services</a>
        </div>
        <p className={`landing-hero__status ${status.open ? 'is-open' : ''}`}>
          <span className="landing-hero__dot" aria-hidden="true" /> {status.text}
        </p>
      </div>
    </section>
  )
}

/** Photos of the library, when the Admin has uploaded some. */
export function PhotoStrip({ photos }) {
  if (photos.length === 0) return null
  return (
    <section className="landing-photos" aria-label="Photos of the library">
      {photos.map((photo) => (
        <figure key={photo.id} className="landing-photo">
          <img src={photo.image} alt={photo.caption || 'The library'} loading="lazy" />
          {photo.caption && <figcaption>{photo.caption}</figcaption>}
        </figure>
      ))}
    </section>
  )
}
