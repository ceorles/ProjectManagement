import { useState } from 'react'
import { Download, KeyRound, LogOut, Smartphone, UserRound } from 'lucide-react'
import Badge from '../../components/common/Badge'
import Button from '../../components/common/Button'
import Card from '../../components/common/Card'
import { FormError, PasswordField, SelectField, TextField } from '../../components/common/FormControls'
import PageHeader from '../../components/common/PageHeader'
import { useAction } from '../../hooks/useAction'
import { useAuth } from '../../hooks/useAuth'
import { useFormDraft } from '../../hooks/useFormDraft'
import { useInstallPrompt } from '../../hooks/useInstallPrompt'
import { useLibrary } from '../../hooks/useLibrary'
import { authService } from '../../services'
import { ROLES } from '../../utils/constants'
import { formatTimestamp } from '../../utils/datetime'
import { fieldError } from '../../utils/errors'
import { initials } from '../../utils/roles'

function profileOf(user) {
  return {
    first_name: user.first_name, last_name: user.last_name, phone: user.phone || '',
    program: user.program || '', year_level: user.year_level || '',
  }
}

function ProfileForm() {
  const { user, setUser } = useAuth()
  const saved = profileOf(user)
  // Edits survive a refresh until they are saved or discarded.
  const { values, setField, setValues, clearDraft, restored } = useFormDraft('profile', saved)
  const [error, setError] = useState(null)
  const changed = JSON.stringify(values) !== JSON.stringify(saved)

  const [save, saving] = useAction(
    () => authService.updateProfile({ ...values, year_level: values.year_level ? Number(values.year_level) : null }),
    {
      success: 'Your profile was updated.',
      onSuccess: (updated) => { setUser(updated); clearDraft(); setValues(profileOf(updated)); clearDraft() },
      onError: (failure) => { setError(failure); return Boolean(failure.fields) },
    },
  )
  const bind = (name) => ({
    value: values[name],
    error: fieldError(error, name),
    onChange: (event) => setField(name, event.target.value),
  })

  return (
    <Card title="Personal details" icon={UserRound}>
      <form className="form-grid" onSubmit={(event) => { event.preventDefault(); setError(null); save() }}>
        {restored && changed && <p className="notice span-2">You have unsaved changes from earlier.</p>}
        <FormError className="span-2" error={error?.fields ? null : error} />
        <TextField label="First name" required autoComplete="given-name" {...bind('first_name')} />
        <TextField label="Last name" required autoComplete="family-name" {...bind('last_name')} />
        <TextField label="Email address" value={user.email} disabled readOnly
          hint="Contact the library to change your email." />
        <TextField label="Mobile number" type="tel" autoComplete="tel" {...bind('phone')} />
        {user.role === 'student' && (
          <>
            <TextField label="Student ID" value={user.student_id || ''} disabled readOnly />
            <SelectField label="Year level" {...bind('year_level')}>
              <option value="">Not set</option>
              {[1, 2, 3, 4, 5, 6].map((year) => <option key={year} value={year}>Year {year}</option>)}
            </SelectField>
            <TextField label="Program / course" className="span-2" {...bind('program')} />
          </>
        )}
        <div className="form-actions span-2">
          <Button variant="secondary" disabled={!changed || saving}
            onClick={() => { setValues(saved); clearDraft(); setError(null) }}>
            Discard changes
          </Button>
          <Button type="submit" loading={saving} disabled={!changed}>Save changes</Button>
        </div>
      </form>
    </Card>
  )
}

const NO_PASSWORDS = { current_password: '', new_password: '', confirm_password: '' }

function PasswordForm() {
  // Passwords are deliberately NOT saved as a draft.
  const [values, setValues] = useState(NO_PASSWORDS)
  const [error, setError] = useState(null)
  const mismatch = values.confirm_password && values.new_password !== values.confirm_password
  const [save, saving] = useAction(() => authService.changePassword(values), {
    success: 'Your password was changed.',
    onSuccess: () => setValues(NO_PASSWORDS),
    onError: (failure) => { setError(failure); return Boolean(failure.fields) },
  })
  const bind = (name) => ({
    value: values[name],
    error: fieldError(error, name),
    onChange: (event) => setValues((current) => ({ ...current, [name]: event.target.value })),
  })
  return (
    <Card title="Change password" icon={KeyRound}>
      <form className="stack" onSubmit={(event) => {
        event.preventDefault()
        if (mismatch) return
        setError(null)
        save()
      }}>
        <FormError error={error?.fields ? null : error} />
        <PasswordField label="Current password" required autoComplete="current-password" {...bind('current_password')} />
        <PasswordField label="New password" required autoComplete="new-password"
          hint="At least 8 characters, not only numbers." {...bind('new_password')} />
        <PasswordField label="Confirm new password" required autoComplete="new-password"
          {...bind('confirm_password')}
          error={mismatch ? 'Passwords do not match.' : fieldError(error, 'confirm_password')} />
        <div className="form-actions">
          <Button type="submit" loading={saving}
            disabled={!values.current_password || !values.new_password || !values.confirm_password}>
            Change password
          </Button>
        </div>
      </form>
    </Card>
  )
}

export default function ProfilePage() {
  const { user, logout } = useAuth()
  const { timeZone } = useLibrary()
  const { canInstall, install } = useInstallPrompt()

  return (
    <>
      <PageHeader title="Profile" description="Your account details and password." />
      <div className="split">
        <div className="stack">
          <ProfileForm />
          <PasswordForm />
        </div>
        <div className="stack">
          <Card>
            <div className="stack">
              <div className="row">
                <span className="avatar" style={{ width: 52, height: 52, fontSize: '1.125rem' }}>{initials(user)}</span>
                <div className="grow">
                  <p className="strong truncate">{user.full_name}</p>
                  <p className="muted small truncate">{user.email}</p>
                </div>
              </div>
              <div className="row-wrap">
                <Badge tone="blue">{ROLES[user.role]}</Badge>
                {user.role === 'librarian' && user.can_manage_resources && (
                  <Badge tone="yellow">Manages seats and rooms</Badge>
                )}
              </div>
              <p className="muted small">Member since {formatTimestamp(user.date_joined, timeZone, { hour: undefined, minute: undefined })}</p>
              <Button variant="secondary" icon={LogOut} onClick={logout}>Sign out</Button>
            </div>
          </Card>
          <Card title="Use it as an app" icon={Smartphone}>
            <div className="stack-sm">
              <p className="soft small">
                Install the portal on your phone or computer to open it from the home screen like
                any other app.
              </p>
              {canInstall ? (
                <Button icon={Download} onClick={install}>Install app</Button>
              ) : (
                <p className="muted small">
                  If no install button appears: on iPhone open the Share menu and choose
                  &ldquo;Add to Home Screen&rdquo;; on Android or desktop Chrome/Edge use the browser
                  menu and choose &ldquo;Install app&rdquo;. It may already be installed.
                </p>
              )}
            </div>
          </Card>
        </div>
      </div>
    </>
  )
}
