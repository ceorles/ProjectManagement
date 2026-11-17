import { useState } from 'react'
import { useAction } from '../../hooks/useAction'
import { seatService } from '../../services'
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
        {/* The library has one floor, so there is normally nothing to choose. */}
        {floors.length > 1 && (
          <SelectField label="Floor" required {...form.bind('floor', Number)}>
            {floors.map((floor) => <option key={floor.id} value={floor.id}>{floor.name}</option>)}
          </SelectField>
        )}
        <SelectField label="Type" className={floors.length > 1 ? undefined : 'span-2'} {...form.bind('zone_type')}>
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
        number: seat.number, row: seat.row, col: seat.col, table_number: seat.table_number ?? '',
        ...Object.fromEntries(SEAT_FEATURES.map((feature) => [feature.key, seat[feature.key]])),
      }
      : { number: '', row: position?.row ?? 1, col: position?.col ?? 1, table_number: '', has_power_outlet: false, has_computer: false, is_accessible: false },
    (values) => {
      const data = { ...values, table_number: values.table_number === '' ? null : values.table_number }
      return editing ? seatService.update(seat.id, data) : seatService.create({ ...data, zone: zone.id })
    },
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
        <TextField label="Table number" type="number" min={1} max={99}
          hint="Chairs with the same table number are drawn as one table. Leave empty for a stand-alone seat."
          {...form.bind('table_number', toNumber)} />
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
