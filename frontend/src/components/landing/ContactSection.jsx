import { BookOpen, CalendarX, Clock, Mail, MapPin, Megaphone, Phone } from 'lucide-react'
import { formatDate } from '../../utils/datetime'
import { groupHours } from '../../utils/hours'
import SectionPill from './SectionPill'

/** #contact: the opening hours (the same ones reservations use) and contact details. */
export default function ContactSection({ data }) {
  const { profile, hours, closures } = data
  const facebook = profile.facebook_page || profile.facebook_url
  return (
    <section id="contact" className="landing-section">
      <div className="landing-container landing-contact">
        <article className="landing-hours">
          <h2 className="landing-hours__title"><Clock size={20} aria-hidden="true" /> Library Hours</h2>
          <dl>
            {groupHours(hours).map((group) => (
              <div key={group.days} className={group.open ? '' : 'is-closed'}>
                <dt>{group.days}</dt>
                <dd>{group.hours}</dd>
              </div>
            ))}
          </dl>
          {closures.length > 0 && (
            <div className="landing-hours__closures">
              <p className="strong small"><CalendarX size={15} aria-hidden="true" /> Upcoming closures</p>
              <ul>
                {closures.map((closure) => (
                  <li key={closure.id}>
                    {formatDate(closure.date, { year: undefined })} - {closure.reason}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </article>

        <article className="landing-contact__info">
          <SectionPill dark>Contact</SectionPill>
          <ul className="landing-contact__list">
            {profile.institution && (
              <li><BookOpen size={18} aria-hidden="true" /><span>{profile.institution}</span></li>
            )}
            {profile.address && (
              <li><MapPin size={18} aria-hidden="true" /><span>{profile.address}</span></li>
            )}
            {profile.phone && (
              <li><Phone size={18} aria-hidden="true" /><span>{profile.phone}</span></li>
            )}
            {profile.email && (
              <li>
                <Mail size={18} aria-hidden="true" />
                <a href={`mailto:${profile.email}`}>{profile.email}</a>
              </li>
            )}
            {facebook && (
              <li>
                <Megaphone size={18} aria-hidden="true" />
                <span>
                  For more updates, like and follow our official Facebook page{' '}
                  {profile.facebook_url
                    ? <a href={profile.facebook_url} target="_blank" rel="noreferrer">{profile.facebook_page || 'here'}</a>
                    : <strong>{profile.facebook_page}</strong>}
                </span>
              </li>
            )}
          </ul>
        </article>
      </div>
    </section>
  )
}
