/** A white surface with an optional header. The basic building block of every page. */
export default function Card({ title, subtitle, action, icon: Icon, padded = true, className = '', children }) {
  return (
    <section className={`card ${className}`}>
      {(title || action) && (
        <header className="card__header">
          <div className="row grow">
            {Icon && <span className="card__icon"><Icon size={18} aria-hidden="true" /></span>}
            <div className="grow">
              <h2 className="card__title">{title}</h2>
              {subtitle && <p className="card__subtitle">{subtitle}</p>}
            </div>
          </div>
          {action && <div className="card__action">{action}</div>}
        </header>
      )}
      <div className={padded ? 'card__body' : undefined}>{children}</div>
    </section>
  )
}
