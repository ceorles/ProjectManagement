import { Armchair, BookOpen } from 'lucide-react'
import Button from '../common/Button'
import SectionPill from './SectionPill'

/** #services: the library's services, and how to reserve a seat online. */
export default function ServicesSection({ services }) {
  return (
    <section id="services" className="landing-section">
      <div className="landing-container">
        <SectionPill dark>Library Services</SectionPill>
        {services.length > 0 && (
          <ul className="landing-services">
            {services.map((service) => (
              <li key={service.id} className="landing-service">
                <span className="landing-service__icon"><BookOpen size={20} aria-hidden="true" /></span>
                <div>
                  <h3>{service.title}</h3>
                  {service.description && <p>{service.description}</p>}
                </div>
              </li>
            ))}
          </ul>
        )}
        <div className="landing-callout">
          <div>
            <h3>Reserve a seat online</h3>
            <p>
              Request a seat, a whole table for your group, or a computer for the time you need.
              The librarian reviews each request, and you check in when you arrive.
            </p>
          </div>
          <Button to="/login" icon={Armchair}>Reserve now</Button>
        </div>
      </div>
    </section>
  )
}
