import { useState } from 'react'
import { Trash2 } from 'lucide-react'
import { useAction } from '../../hooks/useAction'
import { libraryService, seatService } from '../../services'
import { SEAT_FEATURES, ZONE_TYPES } from '../../utils/constants'
import { fieldError } from '../../utils/errors'
import Button from '../common/Button'
import { Checkbox, FormError, SelectField, TextField } from '../common/FormControls'
import Modal from '../common/Modal'

/** Shared plumbing for the small create/edit dialogs on this page. */
function useResourceForm(initial, save, { success, onSaved }) {
  const [values, setValues] = useState(initial)
  const [error, setError] = useState(null)
  const [submit, saving] = useAction(() => save(values), {
    success,
    onSuccess: onSaved,
    onError: (failure) => {
      setError(failure)
      return Boolean(failure.fields) // field errors are shown next to the fields
    },
  })
  const bind = (name, parse = (value) => value) => ({
    value: values[name] ?? '',
    error: fieldError(error, name),
    onChange: (event) => setValues((current) => ({ ...current, [name]: parse(event.target.value) })),
  })
  const onSubmit = (event) => {
    event.preventDefault()
    setError(null)
    submit()
  }
  return { values, setValues, error, bind, onSubmit, saving }
}

const toNumber = (value) => (value === '' ? '' : Number(value))

function Footer({ onClose, saving, label }) {
  return (
    <>
      <Button variant="secondary" onClick={onClose} disabled={saving}>Cancel</Button>
      <Button type="submit" form="resource-form" loading={saving}>{label}</Button>
    </>
  )
}

export function ZoneFormModal({ zone, floors, onClose, onSaved }) {
  const editing = Boolean(zone)
  const form = useResourceForm(
    zone
      ? { name: zone.name, floor: zone.floor, zone_type: zone.zone_type, description: zone.description, rows: zone.rows, cols: zone.cols }
      : { name: '', floor: floors[0]?.id ?? '', zone_type: 'general', description: '', rows: 4, cols: 8 },
    (values) => (editing ? seatService.updateZone(zone.id, values) : seatService.createZone(values)),
    { success: editing ? 'Zone updated.' : 'Zone added.', onSaved },
  )
  return (
    <Modal open onClose={onClose} busy={form.saving} title={editing ? `Edit ${zone.name}` : 'Add a zone'}
      description="A zone is a seating area on a floor. Its seats sit on a grid of rows and columns."
      footer={<Footer onClose={onClose} saving={form.saving} label={editing ? 'Save changes' : 'Add zone'} />}>
      <form id="resource-form" className="form-grid" onSubmit={form.onSubmit}>
        <FormError className="span-2" error={form.error?.fields ? null : form.error} />
        <TextField label="Zone name" required className="span-2" maxLength={60} {...form.bind('name')} />
        <SelectField label="Floor" required {...form.bind('floor', Number)}>
          {floors.map((floor) => <option key={floor.id} value={floor.id}>{floor.name}</option>)}
        </SelectField>
        <SelectField label="Type" {...form.bind('zone_type')}>
          {Object.entries(ZONE_TYPES).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
        </SelectField>
        <TextField label="Rows" type="number" min={1} max={20} required {...form.bind('rows', toNumber)} />
        <TextField label="Columns" type="number" min={1} max={20} required {...form.bind('cols', toNumber)} />
        <TextField label="Description" className="span-2" maxLength={200} {...form.bind('description')} />
      </form>
    </Modal>
  )
}

export function SeatFormModal({ seat, zone, position, onClose, onSaved }) {
  const editing = Boolean(seat)
  const form = useResourceForm(
    seat
      ? {
        number: seat.number, row: seat.row, col: seat.col,
        ...Object.fromEntries(SEAT_FEATURES.map((feature) => [feature.key, seat[feature.key]])),
      }
      : { number: '', row: position?.row ?? 1, col: position?.col ?? 1, has_power_outlet: false, has_computer: false, near_window: false, is_accessible: false },
    (values) => (editing
      ? seatService.update(seat.id, values)
      : seatService.create({ ...values, zone: zone.id })),
    { success: (saved) => `Seat ${saved.number} ${editing ? 'updated' : 'added'}.`, onSaved },
  )
  return (
    <Modal open onClose={onClose} busy={form.saving} size="sm"
      title={editing ? `Edit seat ${seat.number}` : `Add a seat to ${zone.name}`}
      footer={<Footer onClose={onClose} saving={form.saving} label={editing ? 'Save changes' : 'Add seat'} />}>
      <form id="resource-form" className="stack" onSubmit={form.onSubmit}>
        <FormError error={form.error?.fields ? null : form.error} />
        <TextField label="Seat number" required maxLength={12} placeholder="e.g. A25"
          hint="The label printed on the seat. Must be unique." {...form.bind('number')} />
        <div className="form-grid">
          <TextField label="Row" type="number" min={1} max={zone.rows} required
            hint={`1 to ${zone.rows}`} {...form.bind('row', toNumber)} />
          <TextField label="Column" type="number" min={1} max={zone.cols} required
            hint={`1 to ${zone.cols}`} {...form.bind('col', toNumber)} />
        </div>
        <fieldset className="stack-sm" style={{ border: 0, padding: 0, margin: 0 }}>
          <legend className="field__label">Features</legend>
          {SEAT_FEATURES.map((feature) => (
            <Checkbox key={feature.key} label={feature.label} checked={form.values[feature.key]}
              onChange={(event) => form.setValues((current) => ({ ...current, [feature.key]: event.target.checked }))} />
          ))}
        </fieldset>
      </form>
    </Modal>
  )
}

/** Add, rename and remove the floors of the building. */
export function FloorsModal({ floors, onClose, onChanged }) {
  const [name, setName] = useState('')
  const nextLevel = floors.length ? Math.max(...floors.map((floor) => floor.level)) + 1 : 0
  const [add, adding] = useAction(() => libraryService.createFloor({ name: name.trim(), level: nextLevel }), {
    success: 'Floor added.',
    onSuccess: () => { setName(''); onChanged() },
  })
  const [remove, removing] = useAction((floor) => libraryService.deleteFloor(floor.id), {
    success: 'Floor removed.', onSuccess: onChanged,
  })
  return (
    <Modal open onClose={onClose} title="Floors" size="sm" busy={adding || removing}
      description="Zones and study rooms are placed on a floor."
      footer={<Button variant="secondary" onClick={onClose}>Done</Button>}>
      <div className="stack">
        <ul className="invitees">
          {floors.map((floor) => (
            <li key={floor.id} className="invitee">
              <span>
                <span className="strong">{floor.name}</span>
                <span className="muted"> · {floor.seat_count} seats · {floor.room_count} rooms</span>
              </span>
              <button type="button" className="icon-button" aria-label={`Remove ${floor.name}`}
                disabled={removing || floor.seat_count > 0 || floor.room_count > 0}
                title={floor.seat_count || floor.room_count ? 'Only an empty floor can be removed' : 'Remove floor'}
                onClick={() => remove(floor)}>
                <Trash2 size={16} />
              </button>
            </li>
          ))}
        </ul>
        <form className="invite-form" onSubmit={(event) => { event.preventDefault(); if (name.trim()) add() }}>
          <input className="input" value={name} placeholder="New floor name, e.g. Fourth Floor"
            aria-label="New floor name" maxLength={60} onChange={(event) => setName(event.target.value)} />
          <Button type="submit" variant="secondary" loading={adding} disabled={!name.trim()}>Add</Button>
        </form>
      </div>
    </Modal>
  )
}
