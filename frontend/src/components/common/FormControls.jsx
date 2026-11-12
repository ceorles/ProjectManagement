import { useId, useState } from 'react'
import { Eye, EyeOff, Search, X } from 'lucide-react'

/**
 * Label + control + hint/error, wired together for screen readers.
 * `children` is a function that receives the props to spread on the control.
 */
export function Field({ label, hint, error, required, className = '', children }) {
  const id = useId()
  const describedBy = error ? `${id}-error` : hint ? `${id}-hint` : undefined
  return (
    <div className={`field ${error ? 'field--invalid' : ''} ${className}`}>
      {label && (
        <label className="field__label" htmlFor={id}>
          {label}
          {required && <span className="field__required" aria-hidden="true"> *</span>}
        </label>
      )}
      {children({ id, 'aria-describedby': describedBy, 'aria-invalid': error ? true : undefined })}
      {error
        ? <p className="field__error" id={`${id}-error`} role="alert">{error}</p>
        : hint && <p className="field__hint" id={`${id}-hint`}>{hint}</p>}
    </div>
  )
}

export function TextField({ label, hint, error, required, className, ...input }) {
  return (
    <Field label={label} hint={hint} error={error} required={required} className={className}>
      {(control) => <input className="input" required={required} {...control} {...input} />}
    </Field>
  )
}

export function PasswordField({ label, hint, error, required, className, ...input }) {
  const [visible, setVisible] = useState(false)
  return (
    <Field label={label} hint={hint} error={error} required={required} className={className}>
      {(control) => (
        <div className="input-group">
          <input
            className="input" type={visible ? 'text' : 'password'} required={required}
            {...control} {...input}
          />
          <button
            type="button" className="input-group__button"
            onClick={() => setVisible((current) => !current)}
            aria-label={visible ? 'Hide password' : 'Show password'}
          >
            {visible ? <EyeOff size={17} /> : <Eye size={17} />}
          </button>
        </div>
      )}
    </Field>
  )
}

export function SelectField({ label, hint, error, required, className, children, ...select }) {
  return (
    <Field label={label} hint={hint} error={error} required={required} className={className}>
      {(control) => (
        <select className="input select" required={required} {...control} {...select}>
          {children}
        </select>
      )}
    </Field>
  )
}

export function TextAreaField({ label, hint, error, required, className, rows = 3, ...textarea }) {
  return (
    <Field label={label} hint={hint} error={error} required={required} className={className}>
      {(control) => (
        <textarea className="input textarea" rows={rows} required={required} {...control} {...textarea} />
      )}
    </Field>
  )
}

export function Checkbox({ label, description, className = '', ...input }) {
  return (
    <label className={`checkbox ${className}`}>
      <input type="checkbox" {...input} />
      <span>
        <span className="checkbox__label">{label}</span>
        {description && <span className="checkbox__description">{description}</span>}
      </span>
    </label>
  )
}

export function SearchInput({ value, onChange, placeholder = 'Search...', label = 'Search', className = '' }) {
  return (
    <div className={`search ${className}`}>
      <Search size={16} className="search__icon" aria-hidden="true" />
      <input
        className="input" type="search" value={value} placeholder={placeholder}
        aria-label={label} onChange={(event) => onChange(event.target.value)}
      />
      {value && (
        <button type="button" className="search__clear" onClick={() => onChange('')} aria-label="Clear search">
          <X size={15} />
        </button>
      )}
    </div>
  )
}

/** A general (non-field) error shown above a form. */
export function FormError({ error, className = '' }) {
  if (!error) return null
  return (
    <p className={`form-error ${className}`} role="alert">
      {typeof error === 'string' ? error : error.message}
    </p>
  )
}
