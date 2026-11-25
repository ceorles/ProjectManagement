import { useState } from 'react'
import { UserPlus } from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'
import Button from '../../components/common/Button'
import {
  FormError, PasswordField, TextField,
} from '../../components/common/FormControls'
import {
  MobileNumberField, NameField, ProgramField, StudentIdField, YearLevelField,
} from '../../components/common/StudentFields'
import { useAuth } from '../../hooks/useAuth'
import { useFormDraft } from '../../hooks/useFormDraft'
import { fieldError } from '../../utils/errors'
import { formatName, mobileProblem, studentIdProblem } from '../../utils/studentInfo'
import AuthLayout from './AuthLayout'

const EMPTY = {
  first_name: '', last_name: '', email: '', student_id: '', program: '', year_level: '', phone: '',
}

/** Student self-registration. Staff accounts cannot be created here. */
export default function RegisterPage() {
  const { register } = useAuth()
  const location = useLocation()
  // The draft survives an accidental refresh. It lives in sessionStorage
  // (gone when the tab closes) and never includes the passwords.
  const { values, setField, clearDraft, restored } = useFormDraft('register', EMPTY, { storage: 'session' })
  const [passwords, setPasswords] = useState({ password: '', confirm_password: '' })
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  // Problems found before sending, shown under their fields.
  const [problems, setProblems] = useState({})

  const bind = (name) => ({
    name,
    value: values[name],
    error: problems[name] || fieldError(error, name),
    onChange: (event) => {
      setProblems((current) => ({ ...current, [name]: undefined }))
      setField(name, event.target.value)
    },
  })
  const mismatch = passwords.confirm_password && passwords.password !== passwords.confirm_password

  const submit = async (event) => {
    event.preventDefault()
    if (submitting || mismatch) return
    const found = { student_id: studentIdProblem(values.student_id), phone: mobileProblem(values.phone) }
    if (found.student_id || found.phone) {
      setProblems(found)
      setError('Please check the highlighted fields.')
      return
    }
    setSubmitting(true)
    setError(null)
    try {
      await register({
        ...values,
        first_name: formatName(values.first_name),
        last_name: formatName(values.last_name),
        ...passwords,
        year_level: values.year_level ? Number(values.year_level) : null,
      })
      clearDraft()
    } catch (failure) {
      setError(failure)
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout
      wide
      title="Create your student account"
      subtitle="Register once, then reserve seats and computers any time."
      footer={<>Already registered? <Link to="/login" state={location.state}>Sign in</Link></>}
    >
      <form className="auth__form" onSubmit={submit}>
        {restored && (
          <p className="notice">
            We kept what you had entered.{' '}
            <button type="button" className="link-button" onClick={() => clearDraft(true)}>Start over</button>
          </p>
        )}
        <FormError error={error?.fields ? 'Please check the highlighted fields.' : error} />
        <div className="form-grid">
          <NameField label="First name" autoComplete="given-name" required {...bind('first_name')} />
          <NameField label="Last name" autoComplete="family-name" required {...bind('last_name')} />
          <TextField label="Email address" type="email" autoComplete="email" required
            className="span-2" placeholder="you@university.edu" {...bind('email')} />
          <StudentIdField label="Student ID" required {...bind('student_id')} />
          <YearLevelField {...bind('year_level')} />
          <ProgramField className="span-2" {...bind('program')} />
          <MobileNumberField label="Mobile number" hint="Optional." {...bind('phone')} />
          <PasswordField
            label="Password" name="password" autoComplete="new-password" required
            hint="At least 8 characters, not only numbers."
            value={passwords.password} error={fieldError(error, 'password')}
            onChange={(event) => setPasswords((current) => ({ ...current, password: event.target.value }))}
          />
          <PasswordField
            label="Confirm password" name="confirm_password" autoComplete="new-password" required
            value={passwords.confirm_password}
            error={mismatch ? 'Passwords do not match.' : fieldError(error, 'confirm_password')}
            onChange={(event) => setPasswords((current) => ({ ...current, confirm_password: event.target.value }))}
          />
        </div>
        <Button type="submit" size="lg" block icon={UserPlus} loading={submitting}>
          Create account
        </Button>
      </form>
    </AuthLayout>
  )
}
