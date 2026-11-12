import { ArrowLeft } from 'lucide-react'
import { Link } from 'react-router-dom'

/** Title, short description and the page's main actions. */
export default function PageHeader({ title, description, actions, back }) {
  return (
    <header className="page-header">
      <div className="grow">
        {back && (
          <Link to={back.to} className="page-header__back">
            <ArrowLeft size={15} aria-hidden="true" /> {back.label}
          </Link>
        )}
        <h1 className="page-header__title">{title}</h1>
        {description && <p className="page-header__description">{description}</p>}
      </div>
      {actions && <div className="page-header__actions">{actions}</div>}
    </header>
  )
}
