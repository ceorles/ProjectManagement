import { useState } from 'react'
import { ExternalLink } from 'lucide-react'
import { useAction } from '../../hooks/useAction'
import { useApiQuery } from '../../hooks/useApiQuery'
import { useFormDraft } from '../../hooks/useFormDraft'
import { landingService } from '../../services'
import { fieldError } from '../../utils/errors'
import Button from '../common/Button'
import Card from '../common/Card'
import { QueryBoundary } from '../common/Feedback'
import { FormError, TextAreaField, TextField } from '../common/FormControls'
import ContentListEditor from './ContentListEditor'

const SECTIONS = [
  {
    title: 'Library information',
    fields: [
      { name: 'name', label: 'Library name', required: true, maxLength: 80 },
      { name: 'institution', label: 'School', maxLength: 150 },
      { name: 'tagline', label: 'Tagline', maxLength: 120, placeholder: 'e.g. Redefines Possibilities' },
      { name: 'introduction', label: 'Introduction', type: 'textarea', className: 'span-2' },
    ],
  },
  {
    title: 'Contact information',
    fields: [
      { name: 'address', label: 'Address', maxLength: 250, className: 'span-2' },
      { name: 'phone', label: 'Telephone / fax', maxLength: 80 },
      { name: 'email', label: 'Email address', type: 'email' },
      { name: 'facebook_page', label: 'Facebook page name', maxLength: 100, placeholder: 'e.g. @DLL-Library' },
      { name: 'facebook_url', label: 'Facebook page link', type: 'url', placeholder: 'https://www.facebook.com/...' },
    ],
  },
  {
    title: 'Notes shown above the lists',
    subtitle: 'Optional. Leave empty to show only the list.',
    fields: [
      { name: 'card_note', label: 'Library card note', maxLength: 300, className: 'span-2' },
      { name: 'rules_note', label: 'Library rules note', maxLength: 300, className: 'span-2' },
    ],
  },
]
const FIELD_NAMES = SECTIONS.flatMap((section) => section.fields.map((field) => field.name))

function pick(profile) {
  return Object.fromEntries(FIELD_NAMES.map((name) => [name, profile[name] ?? '']))
}

function InfoForm({ profile, onSaved }) {
  const saved = pick(profile)
  // Unsaved edits survive a refresh, like the other settings forms.
  const { values, setField, setValues, clearDraft, restored } = useFormDraft('settings-library-info', saved)
  const [error, setError] = useState(null)
  const changed = FIELD_NAMES.some((name) => values[name] !== saved[name])

  const [save, saving] = useAction(() => landingService.saveProfile(values), {
    success: 'Library information saved. The landing page shows it now.',
    onSuccess: (updated) => { clearDraft(); setValues(pick(updated)); clearDraft(); onSaved() },
    onError: (failure) => { setError(failure); return Boolean(failure.fields) },
  })

  return (
    <form className="stack" onSubmit={(event) => { event.preventDefault(); setError(null); save() }}>
      {restored && changed && <p className="notice">You have unsaved changes from earlier.</p>}
      <FormError error={error?.fields ? 'Please check the highlighted fields.' : error} />
      {SECTIONS.map((section) => (
        <Card key={section.title} title={section.title} subtitle={section.subtitle}>
          <div className="form-grid">
            {section.fields.map((field) => {
              const Control = field.type === 'textarea' ? TextAreaField : TextField
              return (
                <Control
                  key={field.name} label={field.label} required={field.required}
                  type={field.type === 'textarea' ? undefined : field.type}
                  maxLength={field.maxLength} placeholder={field.placeholder}
                  className={field.className} rows={4} value={values[field.name]}
                  error={fieldError(error, field.name)}
                  onChange={(event) => setField(field.name, event.target.value)}
                />
              )
            })}
          </div>
        </Card>
      ))}
      <div className="form-actions">
        <Button variant="secondary" disabled={!changed || saving}
          onClick={() => { setValues(saved); clearDraft(); setError(null) }}>
          Discard changes
        </Button>
        <Button type="submit" loading={saving} disabled={!changed}>Save information</Button>
      </div>
    </form>
  )
}

/** Library name, introduction and contact details shown on the public landing page. */
export function LibraryInfoSettings() {
  const query = useApiQuery(landingService.profile, [])
  return (
    <QueryBoundary query={query} loadingLabel="Loading library information...">
      {(profile) => <InfoForm key={profile.updated_at} profile={profile} onSaved={query.refetch} />}
    </QueryBoundary>
  )
}

const line = (item) => (
  <>
    <p className="strong">{item.title}</p>
    {item.description && <p className="muted small">{item.description}</p>}
  </>
)

const EDITORS = [
  {
    resource: 'landing-items', params: { section: 'service' }, defaults: { section: 'service' },
    title: 'Library services', noun: 'Service', render: line,
    fields: [
      { name: 'title', label: 'Service', required: true, maxLength: 200 },
      { name: 'description', label: 'Description (optional)', type: 'textarea' },
    ],
  },
  {
    resource: 'landing-items', params: { section: 'card' }, defaults: { section: 'card' },
    title: 'Library card', subtitle: 'How to get and keep a library card.', noun: 'Library card step', render: line,
    fields: [
      { name: 'title', label: 'Step or requirement', required: true, maxLength: 200 },
      { name: 'description', label: 'More detail (optional)', type: 'textarea' },
    ],
  },
  {
    resource: 'landing-items', params: { section: 'rule' }, defaults: { section: 'rule' },
    title: 'Library rules', noun: 'Rule', render: line,
    fields: [
      { name: 'title', label: 'Rule', required: true, maxLength: 200 },
      { name: 'description', label: 'More detail (optional)', type: 'textarea' },
    ],
  },
  {
    resource: 'personnel', title: 'Library personnel', noun: 'Person',
    render: (person) => (
      <div className="row">
        {person.photo
          ? <img src={person.photo} alt="" className="content-row__thumb content-row__thumb--round" />
          : <span className="avatar">{person.name.replace(/^(Ms|Mr|Mrs|Dr)\.?\s+/i, '')[0]}</span>}
        <div>
          <p className="strong">{person.name}</p>
          <p className="muted small">{person.position}</p>
        </div>
      </div>
    ),
    fields: [
      { name: 'name', label: 'Name', required: true, maxLength: 100, placeholder: 'e.g. Ms. Cora' },
      { name: 'position', label: 'Position', required: true, maxLength: 100, placeholder: 'e.g. Library Staff' },
      { name: 'photo', label: 'Photo (optional)', type: 'image' },
    ],
  },
  {
    resource: 'photos', title: 'Library photos',
    subtitle: 'Shown on the landing page. The first photo is also the background of the top banner.',
    noun: 'Photo',
    render: (photo) => (
      <div className="row">
        <img src={photo.image} alt="" className="content-row__thumb" />
        <p className={photo.caption ? 'strong' : 'muted'}>{photo.caption || 'No caption'}</p>
      </div>
    ),
    fields: [
      { name: 'image', label: 'Photo', type: 'image', required: true },
      { name: 'caption', label: 'Caption (optional)', maxLength: 150 },
    ],
  },
]

/** The lists on the public landing page. The hours come from the Opening hours tab. */
export function LandingContentSettings() {
  return (
    <div className="stack">
      <p className="notice">
        <span>
          Everything here appears on the public landing page as soon as it is saved. The library
          hours shown there come from the <strong>Opening hours</strong> tab.{' '}
          <a href="/" target="_blank" rel="noreferrer" className="nowrap">
            View landing page <ExternalLink size={13} style={{ display: 'inline', verticalAlign: '-2px' }} aria-hidden="true" />
          </a>
        </span>
      </p>
      <div className="split split--even">
        {EDITORS.map((editor) => <ContentListEditor key={`${editor.resource}-${editor.title}`} editor={editor} />)}
      </div>
    </div>
  )
}
