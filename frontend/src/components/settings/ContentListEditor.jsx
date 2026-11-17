import { useEffect, useRef, useState } from 'react'
import { ArrowDown, ArrowUp, ImagePlus, Pencil, Plus, Trash2 } from 'lucide-react'
import { useAction } from '../../hooks/useAction'
import { useApiQuery } from '../../hooks/useApiQuery'
import { landingService } from '../../services'
import { fieldError } from '../../utils/errors'
import Button from '../common/Button'
import Card from '../common/Card'
import ConfirmDialog from '../common/ConfirmDialog'
import { EmptyState, QueryBoundary } from '../common/Feedback'
import { Field, FormError, TextAreaField, TextField } from '../common/FormControls'
import Modal from '../common/Modal'

/** Picking an image, with a preview of the current or newly chosen file. */
function ImageInput({ field, value, current, error, onChange }) {
  // A temporary URL for the picked file, released when replaced or unmounted.
  const [preview, setPreview] = useState(null)
  const previewRef = useRef(null)
  useEffect(() => () => previewRef.current && URL.revokeObjectURL(previewRef.current), [])
  const choose = (file) => {
    if (previewRef.current) URL.revokeObjectURL(previewRef.current)
    previewRef.current = file ? URL.createObjectURL(file) : null
    setPreview(previewRef.current)
    onChange(file)
  }
  const shown = value instanceof File ? preview : value === null ? null : current

  return (
    <Field label={field.label} required={field.required} error={error}
      hint="JPG, PNG or WebP, up to 5 MB.">
      {(control) => (
        <div className="image-input">
          {shown
            ? <img src={shown} alt="" className="image-input__preview" />
            : <span className="image-input__empty"><ImagePlus size={22} aria-hidden="true" /></span>}
          <div className="stack-sm">
            <input
              {...control} type="file" accept="image/jpeg,image/png,image/webp"
              onChange={(event) => choose(event.target.files[0] || undefined)}
            />
            {!field.required && shown && (
              <button type="button" className="link-button small" onClick={() => choose(null)}>
                Remove photo
              </button>
            )}
          </div>
        </div>
      )}
    </Field>
  )
}

function ItemForm({ editor, item, onClose, onSaved }) {
  const { resource, fields, defaults = {}, noun } = editor
  const [values, setValues] = useState(() => Object.fromEntries(
    fields.filter((field) => field.type !== 'image').map((field) => [field.name, item?.[field.name] ?? '']),
  ))
  const [error, setError] = useState(null)

  const [save, saving] = useAction(() => {
    // Leave an image out unless one was picked (a File) or removed (null).
    const data = Object.fromEntries(Object.entries(values).filter(([, value]) => value !== undefined))
    return item ? landingService.update(resource, item.id, data)
      : landingService.create(resource, { ...defaults, ...data })
  }, {
    success: item ? `${noun} updated.` : `${noun} added.`,
    onSuccess: onSaved,
    onError: (failure) => {
      setError(failure)
      return Boolean(failure.fields)
    },
  })

  const set = (name, value) => setValues((current) => ({ ...current, [name]: value }))

  return (
    <Modal
      open onClose={onClose} busy={saving} title={item ? `Edit ${noun.toLowerCase()}` : `Add ${noun.toLowerCase()}`}
      footer={(
        <>
          <Button variant="secondary" onClick={onClose} disabled={saving}>Cancel</Button>
          <Button type="submit" form="content-form" loading={saving}>{item ? 'Save changes' : 'Add'}</Button>
        </>
      )}
    >
      <form id="content-form" className="stack" onSubmit={(event) => { event.preventDefault(); setError(null); save() }}>
        <FormError error={error?.fields ? null : error} />
        {fields.map((field) => {
          const common = {
            label: field.label, required: field.required, maxLength: field.maxLength,
            placeholder: field.placeholder, hint: field.hint, error: fieldError(error, field.name),
          }
          if (field.type === 'image') {
            return (
              <ImageInput key={field.name} field={field} value={values[field.name]}
                current={item?.[field.name]} error={common.error}
                onChange={(value) => set(field.name, value)} />
            )
          }
          const Control = field.type === 'textarea' ? TextAreaField : TextField
          return (
            <Control key={field.name} {...common} value={values[field.name]}
              onChange={(event) => set(field.name, event.target.value)} />
          )
        })}
      </form>
    </Modal>
  )
}

/**
 * An editable, ordered list of landing page content (services, library card
 * steps, rules, personnel, photos): add, edit, move up/down, remove.
 *
 * editor: { resource, params, defaults, fields, noun, title, subtitle, render(item) }
 */
export default function ContentListEditor({ editor }) {
  const { resource, params, title, subtitle, noun, render } = editor
  const query = useApiQuery(() => landingService.list(resource, params), [resource, params])
  const [editing, setEditing] = useState(null) // { item } or { item: null } for a new one
  const [removing, setRemoving] = useState(null)

  const [move, moving] = useAction((ids) => landingService.reorder(resource, ids), {
    onSuccess: () => query.refetch(),
  })
  const [remove, deleting] = useAction(() => landingService.remove(resource, removing.id), {
    success: `${noun} removed.`,
    onSuccess: () => { setRemoving(null); query.refetch() },
    onError: () => setRemoving(null),
  })

  const shift = (items, index, step) => {
    const ids = items.map((item) => item.id)
    ;[ids[index], ids[index + step]] = [ids[index + step], ids[index]]
    move(ids)
  }

  return (
    <Card
      title={title} subtitle={subtitle} padded={false}
      action={<Button size="sm" icon={Plus} onClick={() => setEditing({ item: null })}>Add</Button>}
    >
      <QueryBoundary query={query} compact>
        {(items) => (items.length === 0 ? (
          <EmptyState compact title={`No ${noun.toLowerCase()} yet`}
            description="Nothing is shown in this part of the landing page until you add something." />
        ) : (
          <ul className="list-rows">
            {items.map((item, index) => (
              <li key={item.id} className="content-row">
                <div className="content-row__main">{render(item)}</div>
                <div className="content-row__actions">
                  <Button size="sm" variant="ghost" icon={ArrowUp} disabled={index === 0 || moving}
                    aria-label="Move up" title="Move up" onClick={() => shift(items, index, -1)} />
                  <Button size="sm" variant="ghost" icon={ArrowDown}
                    disabled={index === items.length - 1 || moving}
                    aria-label="Move down" title="Move down" onClick={() => shift(items, index, 1)} />
                  <Button size="sm" variant="secondary" icon={Pencil} aria-label="Edit" title="Edit"
                    onClick={() => setEditing({ item })} />
                  <Button size="sm" variant="danger-soft" icon={Trash2} aria-label="Remove" title="Remove"
                    onClick={() => setRemoving(item)} />
                </div>
              </li>
            ))}
          </ul>
        ))}
      </QueryBoundary>

      {editing && (
        <ItemForm editor={editor} item={editing.item} onClose={() => setEditing(null)}
          onSaved={() => { setEditing(null); query.refetch() }} />
      )}
      <ConfirmDialog
        open={Boolean(removing)} onClose={() => setRemoving(null)} onConfirm={remove} busy={deleting}
        title={`Remove this ${noun.toLowerCase()}?`} confirmLabel="Remove"
      >
        <p>It will no longer appear on the public landing page.</p>
      </ConfirmDialog>
    </Card>
  )
}
