import { useState } from 'react'
import { Plus } from 'lucide-react'
import { useAction } from '../../hooks/useAction'
import { useFormDraft } from '../../hooks/useFormDraft'
import { roomService } from '../../services'
import { fieldError } from '../../utils/errors'
import Button from '../common/Button'
import { Checkbox, FormError, SelectField, TextAreaField, TextField } from '../common/FormControls'
import Modal from '../common/Modal'

const EMPTY = { name: '', code: '', floor: '', capacity: 4, min_occupancy: 2, description: '', facilities: [] }

/** Create or edit a study room, including which facilities it offers. */
export default function RoomFormModal({ room, floors, facilities, onClose, onSaved, onFacilityAdded }) {
  const editing = Boolean(room)
  // A half-filled form survives a refresh; one draft per room (or "new").
  const { values, setField, clearDraft, restored } = useFormDraft(
    `room-form:${room?.id ?? 'new'}`,
    room
      ? {
        name: room.name, code: room.code, floor: room.floor, capacity: room.capacity,
        min_occupancy: room.min_occupancy, description: room.description, facilities: room.facilities,
      }
      : { ...EMPTY, floor: floors[0]?.id ?? '' },
  )
  const [error, setError] = useState(null)
  const [newFacility, setNewFacility] = useState('')

  const [save, saving] = useAction(
    () => (editing ? roomService.update(room.id, values) : roomService.create(values)),
    {
      success: (saved) => `${saved.name} ${editing ? 'updated' : 'added'}.`,
      onSuccess: (saved) => { clearDraft(); onSaved(saved) },
      onError: (failure) => { setError(failure); return Boolean(failure.fields) },
    },
  )
  const [addFacility, addingFacility] = useAction(() => roomService.createFacility(newFacility.trim()), {
    onSuccess: (facility) => {
      setNewFacility('')
      setField('facilities', [...values.facilities, facility.id])
      onFacilityAdded()
    },
  })

  const bind = (name, parse = (value) => value) => ({
    value: values[name] ?? '',
    error: fieldError(error, name),
    onChange: (event) => setField(name, parse(event.target.value)),
  })
  const toNumber = (value) => (value === '' ? '' : Number(value))
  const cancel = () => { clearDraft(); onClose() }

  return (
    <Modal
      open onClose={cancel} busy={saving} size="lg"
      title={editing ? `Edit ${room.name}` : 'Add a study room'}
      footer={(
        <>
          <Button variant="secondary" onClick={cancel} disabled={saving}>Cancel</Button>
          <Button type="submit" form="room-form" loading={saving}>{editing ? 'Save changes' : 'Add room'}</Button>
        </>
      )}
    >
      <form id="room-form" className="form-grid"
        onSubmit={(event) => { event.preventDefault(); setError(null); save() }}>
        {restored && <p className="notice span-2">Your unsaved changes were restored.</p>}
        <FormError className="span-2" error={error?.fields ? null : error} />
        <TextField label="Room name" required maxLength={80} placeholder="e.g. Study Room 204" {...bind('name')} />
        <TextField label="Room number" required maxLength={12} placeholder="e.g. SR-204" {...bind('code')} />
        <SelectField label="Floor" required {...bind('floor', Number)}>
          {floors.map((floor) => <option key={floor.id} value={floor.id}>{floor.name}</option>)}
        </SelectField>
        <div className="form-grid">
          <TextField label="Capacity" type="number" min={1} max={100} required {...bind('capacity', toNumber)} />
          <TextField label="Minimum group" type="number" min={1} max={100} required {...bind('min_occupancy', toNumber)} />
        </div>
        <TextAreaField label="Description" className="span-2" rows={3} {...bind('description')} />

        <fieldset className="span-2 stack-sm" style={{ border: 0, padding: 0, margin: 0 }}>
          <legend className="field__label">Facilities</legend>
          <div className="form-grid">
            {facilities.map((facility) => (
              <Checkbox
                key={facility.id} label={facility.name} checked={values.facilities.includes(facility.id)}
                onChange={(event) => setField(
                  'facilities',
                  event.target.checked
                    ? [...values.facilities, facility.id]
                    : values.facilities.filter((id) => id !== facility.id),
                )}
              />
            ))}
          </div>
          <div className="invite-form">
            <input className="input" value={newFacility} placeholder="Add another facility, e.g. Smart board"
              aria-label="New facility name" maxLength={60}
              onChange={(event) => setNewFacility(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter') {
                  event.preventDefault()
                  if (newFacility.trim()) addFacility()
                }
              }} />
            <Button variant="secondary" icon={Plus} loading={addingFacility}
              disabled={!newFacility.trim()} onClick={addFacility}>
              Add
            </Button>
          </div>
        </fieldset>
      </form>
    </Modal>
  )
}
