import { useState } from 'react'
import { Info, LogIn } from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'
import Button from '../../components/common/Button'
import { FormError, PasswordField, TextField } from '../../components/common/FormControls'
import { useAuth } from '../../hooks/useAuth'
import { useFormDraft } from '../../hooks/useFormDraft'
import AuthLayout from './AuthLayout'

export default function LoginPage() {
  const { login, sessionExpired } = useAuth()
  const location = useLocation()
  // Only the email is kept across a refresh. The password never leaves this
  // component's memory.
  const { values, setField, clearDraft } = useFormDraft('login', { email: '' }, { storage: 'session' })
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const returning = Boolean(location.state?.from)

  const submit = async (event) => {
    event.preventDefault()
    if (submitting) return
    setSubmitting(true)
    setError(null)
    try {
      await login(values.email.trim(), password)
      clearDraft()
      // <GuestOnly> now redirects to the page the user came from, or the dashboard.
    } catch (failure) {
      setError(failure)
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout
      title="Sign in"
      subtitle="Use your library portal account to continue."
      footer={<>New student? <Link to="/register" state={location.state}>Create an account</Link></>}
    >
      <form className="auth__form" onSubmit={submit} noValidate>
        {sessionExpired && (
          <p className="notice notice--warning">
            <Info size={16} aria-hidden="true" />
            Your session has expired. Sign in again to pick up where you left off.
          </p>
        )}
        {!sessionExpired && returning && (
          <p className="notice">
            <Info size={16} aria-hidden="true" /> Please sign in to open that page.
          </p>
        )}
        <FormError error={error} />
        <TextField
          label="Email address" type="email" name="email" autoComplete="username" required
          value={values.email} onChange={(event) => setField('email', event.target.value)}
          placeholder="you@university.edu" autoFocus
        />
        <PasswordField
          label="Password" name="password" autoComplete="current-password" required
          value={password} onChange={(event) => setPassword(event.target.value)}
        />
        <Button type="submit" size="lg" block icon={LogIn} loading={submitting}
          disabled={!values.email || !password}>
          Sign in
        </Button>
        <p className="muted small center">
          Librarian and admin accounts are created by the library administrator.
        </p>
      </form>
    </AuthLayout>
  )
}
