import { useState } from 'react'
import { KeyRound, Pencil, UserCheck, UserPlus, UserX, Users } from 'lucide-react'
import Badge from '../../components/common/Badge'
import Button from '../../components/common/Button'
import ConfirmDialog from '../../components/common/ConfirmDialog'
import DataTable from '../../components/common/DataTable'
import { EmptyState, QueryBoundary } from '../../components/common/Feedback'
import {
  Checkbox, FormError, PasswordField, SearchInput, SelectField, TextField,
} from '../../components/common/FormControls'
import Modal from '../../components/common/Modal'
import PageHeader from '../../components/common/PageHeader'
import Pagination from '../../components/common/Pagination'
import Tabs from '../../components/common/Tabs'
import { useAction } from '../../hooks/useAction'
import { useApiQuery } from '../../hooks/useApiQuery'
import { useAuth } from '../../hooks/useAuth'
import { useDebounce } from '../../hooks/useDebounce'
import { useFormDraft } from '../../hooks/useFormDraft'
import { useLibrary } from '../../hooks/useLibrary'
import { userService } from '../../services'
import { ROLES } from '../../utils/constants'
import { formatTimestamp } from '../../utils/datetime'
import { fieldError } from '../../utils/errors'

const ROLE_TABS = [
  { value: '', label: 'Everyone' },
  { value: 'student', label: 'Students' },
  { value: 'librarian', label: 'Librarians' },
  { value: 'admin', label: 'Admins' },
]
const ROLE_TONE = { admin: 'blue', librarian: 'yellow', student: 'gray' }
const EMPTY = {
  role: 'librarian', first_name: '', last_name: '', email: '', phone: '',
  student_id: '', program: '', year_level: '', can_manage_resources: false,
}

/** Create or edit an account. Librarian accounts can only be made here. */
function UserFormModal({ account, defaultRole, onClose, onSaved }) {
  const { user: me } = useAuth()
  const editing = Boolean(account)
  // The draft never contains the password: it is kept in component state only.
  const { values, setField, clearDraft, restored } = useFormDraft(
    `user-form:${account?.id ?? 'new'}`,
    account
      ? {
        role: account.role, first_name: account.first_name, last_name: account.last_name,
        email: account.email, phone: account.phone, student_id: account.student_id || '',
        program: account.program, year_level: account.year_level || '',
        can_manage_resources: account.can_manage_resources,
      }
      : { ...EMPTY, role: defaultRole || 'librarian' },
  )
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)

  const [save, saving] = useAction(
    () => {
      const data = { ...values, year_level: values.year_level ? Number(values.year_level) : null }
      return editing ? userService.update(account.id, data) : userService.create({ ...data, password })
    },
    {
      success: (saved) => `${saved.full_name}'s account was ${editing ? 'updated' : 'created'}.`,
      onSuccess: () => { clearDraft(); onSaved() },
      onError: (failure) => { setError(failure); return Boolean(failure.fields) },
    },
  )
  const bind = (name) => ({
    value: values[name] ?? '',
    error: fieldError(error, name),
    onChange: (event) => setField(name, event.target.value),
  })
  const cancel = () => { clearDraft(); onClose() }
  const isStudent = values.role === 'student'

  return (
    <Modal
      open onClose={cancel} busy={saving} size="lg"
      title={editing ? `Edit ${account.full_name}` : 'Create an account'}
      description={editing ? undefined : 'Give the new user their email and password. They can change the password after signing in.'}
      footer={(
        <>
          <Button variant="secondary" onClick={cancel} disabled={saving}>Cancel</Button>
          <Button type="submit" form="user-form" loading={saving}>{editing ? 'Save changes' : 'Create account'}</Button>
        </>
      )}
    >
      <form id="user-form" className="form-grid"
        onSubmit={(event) => { event.preventDefault(); setError(null); save() }}>
        {restored && <p className="notice span-2">Your unsaved changes were restored.</p>}
        <FormError className="span-2" error={error?.fields ? null : error} />
        <SelectField label="Role" className="span-2" disabled={editing && account.id === me.id}
          hint={editing && account.id === me.id ? 'You cannot change your own role.' : undefined} {...bind('role')}>
          <option value="librarian">Librarian - runs daily operations</option>
          <option value="student">Student - reserves seats and rooms</option>
          <option value="admin">Admin - full access</option>
        </SelectField>
        <TextField label="First name" required {...bind('first_name')} />
        <TextField label="Last name" required {...bind('last_name')} />
        <TextField label="Email address" type="email" required autoComplete="off" {...bind('email')} />
        <TextField label="Mobile number" type="tel" {...bind('phone')} />
        {isStudent && (
          <>
            <TextField label="Student ID" required {...bind('student_id')} />
            <SelectField label="Year level" {...bind('year_level')}>
              <option value="">Not set</option>
              {[1, 2, 3, 4, 5, 6].map((year) => <option key={year} value={year}>Year {year}</option>)}
            </SelectField>
            <TextField label="Program / course" className="span-2" {...bind('program')} />
          </>
        )}
        {values.role === 'librarian' && (
          <Checkbox
            className="span-2" label="May manage seats and study rooms"
            description="Lets this librarian add, edit and take seats and rooms out of service."
            checked={values.can_manage_resources}
            onChange={(event) => setField('can_manage_resources', event.target.checked)}
          />
        )}
        {!editing && (
          <PasswordField
            label="Initial password" className="span-2" required autoComplete="new-password"
            hint="At least 8 characters, not only numbers."
            value={password} error={fieldError(error, 'password')}
            onChange={(event) => setPassword(event.target.value)}
          />
        )}
      </form>
    </Modal>
  )
}

function PasswordModal({ account, onClose }) {
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [save, saving] = useAction(() => userService.setPassword(account.id, password), {
    success: (result) => result.message,
    onSuccess: onClose,
    onError: (failure) => { setError(failure); return true },
  })
  return (
    <Modal
      open onClose={onClose} busy={saving} size="sm" title={`Reset password for ${account.full_name}`}
      footer={(
        <>
          <Button variant="secondary" onClick={onClose} disabled={saving}>Cancel</Button>
          <Button type="submit" form="password-form" loading={saving} disabled={!password}>Set password</Button>
        </>
      )}
    >
      <form id="password-form" className="stack"
        onSubmit={(event) => { event.preventDefault(); setError(null); save() }}>
        <p className="soft">Tell the user their new password in person. They are notified that it was changed.</p>
        <PasswordField label="New password" required autoComplete="new-password" value={password}
          error={fieldError(error, 'new_password') || (error && !error.fields ? error.message : undefined)}
          onChange={(event) => setPassword(event.target.value)} />
      </form>
    </Modal>
  )
}

/** Admin: every account in the system. */
export default function UsersPage() {
  const { user: me } = useAuth()
  const { timeZone } = useLibrary()
  const [role, setRole] = useState('')
  const [status, setStatus] = useState('')
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [dialog, setDialog] = useState(null) // { type, account? }
  const term = useDebounce(search.trim())

  const query = useApiQuery(
    () => userService.list({ role, status, search: term, page }),
    [role, status, term, page], { keepPrevious: true },
  )
  const close = () => setDialog(null)
  const reload = () => { close(); query.refetch() }
  const change = (setter) => (value) => { setter(value); setPage(1) }

  const [deactivate, deactivating] = useAction((account) => userService.deactivate(account.id), {
    success: (result) => (result.cancelled_reservations
      ? `${result.full_name} was deactivated and ${result.cancelled_reservations} upcoming reservation(s) cancelled.`
      : `${result.full_name} was deactivated.`),
    onSuccess: reload, onError: close,
  })
  const [activate] = useAction((account) => userService.activate(account.id), {
    success: (result) => `${result.full_name} can sign in again.`, onSuccess: reload,
  })

  const columns = [
    {
      key: 'name', header: 'Name', primary: true,
      render: (account) => (
        <>
          <span className="strong">{account.full_name}</span>
          {account.id === me.id && <span className="muted small"> (you)</span>}
          <span className="muted small" style={{ display: 'block' }}>
            {account.email}{account.student_id && ` · ${account.student_id}`}
          </span>
        </>
      ),
    },
    {
      key: 'role', header: 'Role',
      render: (account) => (
        <span className="row-wrap">
          <Badge tone={ROLE_TONE[account.role]}>{ROLES[account.role]}</Badge>
          {account.can_manage_resources && <span className="chip">Manages resources</span>}
        </span>
      ),
    },
    {
      key: 'last_login', header: 'Last sign-in',
      render: (account) => (account.last_login
        ? <span className="nowrap">{formatTimestamp(account.last_login, timeZone, { year: undefined })}</span>
        : <span className="muted">Never</span>),
    },
    {
      key: 'status', header: 'Status',
      render: (account) => (account.is_active
        ? <Badge tone="green" dot>Active</Badge>
        : <Badge tone="red" dot>Deactivated</Badge>),
    },
    {
      key: 'actions', header: 'Actions',
      render: (account) => (
        <>
          <Button size="sm" variant="secondary" icon={Pencil} title="Edit account"
            aria-label={`Edit ${account.full_name}`} onClick={() => setDialog({ type: 'form', account })} />
          <Button size="sm" variant="secondary" icon={KeyRound} title="Reset password"
            aria-label={`Reset password for ${account.full_name}`}
            onClick={() => setDialog({ type: 'password', account })} />
          {account.id !== me.id && (account.is_active ? (
            <Button size="sm" variant="danger-soft" icon={UserX} onClick={() => setDialog({ type: 'deactivate', account })}>Deactivate</Button>
          ) : (
            <Button size="sm" variant="secondary" icon={UserCheck} onClick={() => activate(account)}>Activate</Button>
          ))}
        </>
      ),
    },
  ]

  return (
    <>
      <PageHeader
        title="Users"
        description="Create librarian accounts, manage students, and control who can sign in."
        actions={<Button icon={UserPlus} onClick={() => setDialog({ type: 'form' })}>Create account</Button>}
      />

      <section className="card">
        <div className="toolbar">
          <Tabs tabs={ROLE_TABS} value={role} onChange={change(setRole)} label="Role" />
          <SearchInput value={search} onChange={change(setSearch)} placeholder="Search name, email or student ID" />
          <select className="input select" aria-label="Account status" value={status}
            onChange={(event) => change(setStatus)(event.target.value)}>
            <option value="">Active and deactivated</option>
            <option value="active">Active only</option>
            <option value="inactive">Deactivated only</option>
          </select>
        </div>
        <QueryBoundary query={query} loadingLabel="Loading accounts...">
          {(data) => (data.results.length === 0 ? (
            <EmptyState icon={Users} title="No accounts match"
              description="Try a different role, status or search term." />
          ) : (
            <>
              <DataTable columns={columns} rows={data.results} caption="User accounts" />
              <Pagination page={page} count={data.count} onChange={setPage} />
            </>
          ))}
        </QueryBoundary>
      </section>

      {dialog?.type === 'form' && (
        <UserFormModal account={dialog.account} defaultRole={role} onClose={close} onSaved={reload} />
      )}
      {dialog?.type === 'password' && <PasswordModal account={dialog.account} onClose={close} />}
      <ConfirmDialog
        open={dialog?.type === 'deactivate'} onClose={close} busy={deactivating}
        onConfirm={() => deactivate(dialog.account)}
        title={`Deactivate ${dialog?.account?.full_name}?`} confirmLabel="Deactivate"
      >
        <p>
          They will no longer be able to sign in.
          {dialog?.account?.role === 'student' && ' Their upcoming reservations will be cancelled.'}
          {' '}The account and its history are kept, and it can be reactivated later.
        </p>
      </ConfirmDialog>
    </>
  )
}
