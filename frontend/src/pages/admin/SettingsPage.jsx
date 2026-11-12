import { useState } from 'react'
import { CalendarX, Clock, ListChecks, Plus, Trash2, TriangleAlert } from 'lucide-react'
import Button from '../../components/common/Button'
import Card from '../../components/common/Card'
import ConfirmDialog from '../../components/common/ConfirmDialog'
import { EmptyState } from '../../components/common/Feedback'
import { Checkbox, FormError, SelectField, TextField } from '../../components/common/FormControls'
import PageHeader from '../../components/common/PageHeader'
import Tabs from '../../components/common/Tabs'
import { useAction } from '../../hooks/useAction'
import { useFormDraft } from '../../hooks/useFormDraft'
import { useLibrary } from '../../hooks/useLibrary'
import { libraryService } from '../../services'
import { addDays, formatDate, formatDuration, formatTime, minutesToTime } from '../../utils/datetime'
import { fieldError } from '../../utils/errors'
import './admin.css'

const TABS = [
  { value: 'hours', label: 'Opening hours', icon: Clock },
  { value: 'closures', label: 'Closures', icon: CalendarX },
  { value: 'rules', label: 'Reservation rules', icon: ListChecks },
]

function timeOptions(slot) {
  const options = []
  for (let minutes = 0; minutes < 24 * 60; minutes += slot) options.push(minutesToTime(minutes))
  return options
}

function cancelledNote(count) {
  return count ? ` ${count} upcoming reservation(s) no longer fit and were cancelled; the students were notified.` : ''
}

function HoursSettings() {
  const { overview, refetch } = useLibrary()
  const { values, setValues, clearDraft, restored } = useFormDraft('settings-hours', { hours: overview.hours })
  const [confirming, setConfirming] = useState(false)
  const [error, setError] = useState(null)
  const times = timeOptions(overview.slot_minutes)
  const changed = JSON.stringify(values.hours) !== JSON.stringify(overview.hours)

  const [save, saving] = useAction(() => libraryService.saveHours(values.hours), {
    success: (result) => `Opening hours saved.${cancelledNote(result.cancelled_reservations)}`,
    onSuccess: () => { setConfirming(false); clearDraft(); refetch() },
    onError: (failure) => { setConfirming(false); setError(failure); return true },
  })
  const update = (weekday, changes) => setValues({
    hours: values.hours.map((day) => (day.weekday === weekday ? { ...day, ...changes } : day)),
  })

  return (
    <Card title="Opening hours" subtitle="Reservations can only be made inside these hours.">
      <div className="stack">
        {restored && changed && <p className="notice">You have unsaved changes from earlier.</p>}
        <FormError error={error} />
        <ul className="hours-list">
          {values.hours.map((day) => (
            <li key={day.weekday} className="hours-row">
              <Checkbox label={day.weekday_name} checked={day.is_open}
                onChange={(event) => update(day.weekday, { is_open: event.target.checked })} />
              {day.is_open ? (
                <div className="hours-row__times">
                  <select className="input select" aria-label={`${day.weekday_name} opens at`} value={day.opens_at}
                    onChange={(event) => update(day.weekday, { opens_at: event.target.value })}>
                    {times.map((time) => <option key={time} value={time}>{formatTime(time)}</option>)}
                  </select>
                  <span className="muted">to</span>
                  <select className="input select" aria-label={`${day.weekday_name} closes at`} value={day.closes_at}
                    onChange={(event) => update(day.weekday, { closes_at: event.target.value })}>
                    {times.map((time) => <option key={time} value={time}>{formatTime(time)}</option>)}
                  </select>
                </div>
              ) : <span className="muted">Closed</span>}
            </li>
          ))}
        </ul>
        <div className="form-actions">
          <Button variant="secondary" disabled={!changed || saving}
            onClick={() => { setValues({ hours: overview.hours }); clearDraft(); setError(null) }}>
            Discard changes
          </Button>
          <Button disabled={!changed} onClick={() => { setError(null); setConfirming(true) }}>Save opening hours</Button>
        </div>
      </div>
      <ConfirmDialog open={confirming} onClose={() => setConfirming(false)} onConfirm={save} busy={saving}
        title="Change the opening hours?" confirmLabel="Save hours" tone="primary">
        <p>
          Upcoming reservations that fall outside the new hours will be <strong>cancelled</strong>{' '}
          and the students notified.
        </p>
      </ConfirmDialog>
    </Card>
  )
}

function ClosureSettings() {
  const { overview, now, refetch } = useLibrary()
  const { values, setField, clearDraft } = useFormDraft('settings-closure', { date: '', reason: '' })
  const [error, setError] = useState(null)
  const [confirming, setConfirming] = useState(false)
  const [removing, setRemoving] = useState(null)

  const [add, adding] = useAction(() => libraryService.addClosure(values), {
    success: (result) => `Closure added for ${formatDate(result.date)}.${cancelledNote(result.cancelled_reservations)}`,
    onSuccess: () => { setConfirming(false); clearDraft(true); refetch() },
    onError: (failure) => { setConfirming(false); setError(failure); return Boolean(failure.fields) },
  })
  const [remove, removingNow] = useAction(() => libraryService.removeClosure(removing.id), {
    success: 'Closure removed. The library is open on that day again.',
    onSuccess: () => { setRemoving(null); refetch() },
    onError: () => setRemoving(null),
  })

  return (
    <div className="split split--even">
      <Card title="Add a closure" subtitle="A whole day the library is closed: a holiday, an event, repairs.">
        <form className="stack" onSubmit={(event) => { event.preventDefault(); setError(null); setConfirming(true) }}>
          <FormError error={error?.fields ? null : error} />
          <TextField label="Date" type="date" required min={now.date} max={addDays(now.date, 365)}
            value={values.date} error={fieldError(error, 'date')}
            onChange={(event) => setField('date', event.target.value)} />
          <TextField label="Reason" required maxLength={120} placeholder="e.g. Foundation Day"
            hint="Shown to students." value={values.reason} error={fieldError(error, 'reason')}
            onChange={(event) => setField('reason', event.target.value)} />
          <div className="form-actions">
            <Button type="submit" icon={Plus} disabled={!values.date || !values.reason.trim()}>Add closure</Button>
          </div>
        </form>
      </Card>

      <Card title="Upcoming closures" padded={false}>
        {overview.closures.length === 0 ? (
          <EmptyState compact icon={CalendarX} title="No closures scheduled"
            description="The library follows its normal opening hours." />
        ) : (
          <ul className="list-rows">
            {overview.closures.map((closure) => (
              <li key={closure.id} className="between" style={{ padding: '12px 20px' }}>
                <div>
                  <p className="strong">{formatDate(closure.date)}</p>
                  <p className="muted small">{closure.reason}</p>
                </div>
                <Button size="sm" variant="danger-soft" icon={Trash2} onClick={() => setRemoving(closure)}
                  aria-label={`Remove closure on ${formatDate(closure.date)}`} />
              </li>
            ))}
          </ul>
        )}
      </Card>

      <ConfirmDialog open={confirming} onClose={() => setConfirming(false)} onConfirm={add} busy={adding}
        title="Close the library on this day?" confirmLabel="Add closure">
        <p>
          <strong>{values.date && formatDate(values.date)}</strong>: no reservations can be made, and
          existing reservations for that day will be <strong>cancelled</strong> with a notification
          to each student.
        </p>
      </ConfirmDialog>
      <ConfirmDialog open={Boolean(removing)} onClose={() => setRemoving(null)} onConfirm={remove} busy={removingNow}
        title="Remove this closure?" confirmLabel="Remove closure" tone="primary">
        <p>
          The library will be open on <strong>{removing && formatDate(removing.date)}</strong> with its
          normal hours. Reservations that were cancelled are not restored.
        </p>
      </ConfirmDialog>
    </div>
  )
}

const RULES = [
  {
    title: 'How long',
    fields: [
      { name: 'min_duration_minutes', label: 'Shortest reservation', kind: 'duration', max: 120 },
      { name: 'max_seat_duration_minutes', label: 'Longest seat reservation', kind: 'duration', max: 720 },
      { name: 'max_room_duration_minutes', label: 'Longest room reservation', kind: 'duration', max: 720 },
      { name: 'max_advance_days', label: 'Book ahead (days)', kind: 'number', min: 0, max: 60, hint: '0 = same day only.' },
    ],
  },
  {
    title: 'How many',
    fields: [
      { name: 'max_active_reservations', label: 'Active reservations per student', kind: 'number', min: 1, max: 20 },
      { name: 'max_reservations_per_day', label: 'Reservations per student per day', kind: 'number', min: 1, max: 20 },
    ],
  },
  {
    title: 'Check-in and cancellation',
    fields: [
      { name: 'checkin_early_minutes', label: 'Check-in opens (minutes before start)', kind: 'number', min: 0, max: 60 },
      { name: 'checkin_grace_minutes', label: 'Grace period (minutes after start)', kind: 'number', min: 5, max: 120, hint: 'After this, an unattended reservation becomes a no-show.' },
      { name: 'cancellation_cutoff_minutes', label: 'Cancel at least (minutes before start)', kind: 'number', min: 0, max: 1440, hint: '0 = students may cancel until the start time.' },
      { name: 'reminder_minutes', label: 'Reminder (minutes before start)', kind: 'number', min: 0, max: 240, hint: '0 = no reminders.' },
    ],
  },
  {
    title: 'Missed reservations',
    fields: [
      { name: 'no_show_limit', label: 'No-shows before booking is paused', kind: 'number', min: 0, max: 50, hint: '0 = never pause booking.' },
      { name: 'no_show_window_days', label: 'Counted over (days)', kind: 'number', min: 1, max: 365 },
    ],
  },
]

function RuleSettings() {
  const { overview, refetch } = useLibrary()
  const { values, setField, setValues, clearDraft, restored } = useFormDraft('settings-rules', overview.policy)
  const [error, setError] = useState(null)
  const changed = RULES.some((group) => group.fields.some((field) => values[field.name] !== overview.policy[field.name]))
    || values.allow_self_checkin !== overview.policy.allow_self_checkin

  const [save, saving] = useAction(() => {
    const { updated_at: _ignored, ...data } = values
    return libraryService.savePolicy(data)
  }, {
    success: 'Reservation rules saved. They apply to new reservations from now on.',
    onSuccess: () => { clearDraft(); refetch() },
    onError: (failure) => { setError(failure); return Boolean(failure.fields) },
  })

  const durations = (max) => {
    const options = []
    for (let minutes = overview.slot_minutes; minutes <= max; minutes += overview.slot_minutes) options.push(minutes)
    return options
  }

  return (
    <form className="stack" onSubmit={(event) => { event.preventDefault(); setError(null); save() }}>
      {restored && changed && <p className="notice">You have unsaved changes from earlier.</p>}
      <FormError error={error?.fields ? 'Please check the highlighted fields.' : error} />
      {RULES.map((group) => (
        <Card key={group.title} title={group.title}>
          <div className="form-grid">
            {group.fields.map((field) => (field.kind === 'duration' ? (
              <SelectField key={field.name} label={field.label} value={values[field.name]}
                error={fieldError(error, field.name)}
                onChange={(event) => setField(field.name, Number(event.target.value))}>
                {durations(field.max).map((minutes) => (
                  <option key={minutes} value={minutes}>{formatDuration(minutes)}</option>
                ))}
              </SelectField>
            ) : (
              <TextField key={field.name} label={field.label} type="number" inputMode="numeric" required
                min={field.min} max={field.max} hint={field.hint} value={values[field.name]}
                error={fieldError(error, field.name)}
                onChange={(event) => setField(field.name, event.target.value === '' ? '' : Number(event.target.value))} />
            )))}
          </div>
        </Card>
      ))}
      <Card title="Self check-in">
        <Checkbox
          label="Students may check themselves in from the app"
          description="When off, only library staff can confirm a check-in at the desk."
          checked={values.allow_self_checkin}
          onChange={(event) => setField('allow_self_checkin', event.target.checked)}
        />
      </Card>
      <p className="notice notice--warning">
        <TriangleAlert size={16} aria-hidden="true" />
        <span>Changes apply to reservations made from now on. Existing reservations are not cancelled.</span>
      </p>
      <div className="form-actions">
        <Button variant="secondary" disabled={!changed || saving}
          onClick={() => { setValues(overview.policy); clearDraft(); setError(null) }}>
          Discard changes
        </Button>
        <Button type="submit" loading={saving} disabled={!changed}>Save rules</Button>
      </div>
    </form>
  )
}

/** Admin: opening hours, closure days and the booking rules. */
export default function SettingsPage() {
  const tabDraft = useFormDraft('settings-tab', { tab: 'hours' })
  const { tab } = tabDraft.values
  return (
    <>
      <PageHeader
        title="Library Settings"
        description="When the library is open and the rules every reservation must follow."
      />
      <div className="stack">
        <Tabs tabs={TABS} value={tab} onChange={(value) => tabDraft.setField('tab', value)} label="Settings" />
        {tab === 'hours' && <HoursSettings />}
        {tab === 'closures' && <ClosureSettings />}
        {tab === 'rules' && <RuleSettings />}
      </div>
    </>
  )
}
