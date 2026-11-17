import { initials } from '../../utils/roles'
import SectionPill from './SectionPill'

function InfoPanel({ title, note, children }) {
  return (
    <article className="landing-panel">
      <SectionPill>{title}</SectionPill>
      <div className="landing-panel__body">
        {note && <p className="landing-panel__note">{note}</p>}
        {children}
      </div>
    </article>
  )
}

function Bullets({ items }) {
  return (
    <ul className="landing-bullets">
      {items.map((item) => (
        <li key={item.id}>
          {item.title}
          {item.description && <span className="landing-bullets__detail">{item.description}</span>}
        </li>
      ))}
    </ul>
  )
}

/** #about: library card, rules and personnel, on the dark band as on the library's board. */
export default function AboutSection({ data }) {
  const { profile, card, rules, personnel } = data
  return (
    <section id="about" className="landing-section landing-section--dark">
      <div className="landing-container">
        <div className="landing-panels">
          <InfoPanel title="Library Card" note={profile.card_note}>
            <Bullets items={card} />
          </InfoPanel>
          <InfoPanel title="Library Rules" note={profile.rules_note}>
            <Bullets items={rules} />
          </InfoPanel>
          <InfoPanel title="Library Personnel">
            <ul className="landing-people">
              {personnel.map((person) => (
                <li key={person.id}>
                  {person.photo
                    ? <img src={person.photo} alt="" className="landing-people__photo" loading="lazy" />
                    : (
                      <span className="landing-people__photo landing-people__initials" aria-hidden="true">
                        {initials({ first_name: person.name.replace(/^(Ms|Mr|Mrs|Dr)\.?\s+/i, ''), last_name: '' })}
                      </span>
                    )}
                  <span>
                    <span className="landing-people__name">{person.name}</span>
                    <span className="landing-people__role">{person.position}</span>
                  </span>
                </li>
              ))}
            </ul>
          </InfoPanel>
        </div>
      </div>
    </section>
  )
}
