import { useState } from 'react'
import {
  PROGRAMS, STUDENT_ID_EXAMPLE, YEAR_LEVELS, formatName, formatStudentId, mobileProblem,
} from '../../utils/studentInfo'
import { SelectField, TextField } from './FormControls'

// Fields for student details, used the same way by every form that has them.
// Each takes the same props as TextField: value, onChange(event), error.

const changeTo = (onChange, value) => onChange({ target: { value } })

/** First or last name. Capitalized when the field is left: KYLA -> Kyla. */
export function NameField({ value, onChange, onBlur, ...props }) {
  return (
    <TextField
      {...props} value={value} onChange={onChange}
      onBlur={(event) => {
        const formatted = formatName(value)
        if (formatted !== value) changeTo(onChange, formatted)
        onBlur?.(event)
      }}
    />
  )
}

/** 023A-12345. The hyphen is added automatically. */
export function StudentIdField({ value, onChange, hint, ...props }) {
  return (
    <TextField
      placeholder={`e.g. ${STUDENT_ID_EXAMPLE}`} hint={hint ?? 'As printed on your school ID. The hyphen is added for you.'}
      autoComplete="off" autoCapitalize="characters" spellCheck="false" maxLength={10}
      {...props} value={value}
      onChange={(event) => {
        const typed = event.target.value
        const deleting = typed.length < (value || '').length
        changeTo(onChange, formatStudentId(typed, { addHyphen: !deleting }))
      }}
    />
  )
}

/** Up to 11 digits, numbers only. Longer pasted numbers are refused, not cut. */
export function MobileNumberField({ value, onChange, error, ...props }) {
  const [problem, setProblem] = useState(null)
  return (
    <TextField
      type="tel" inputMode="numeric" autoComplete="tel" maxLength={11} placeholder="e.g. 09171234567"
      {...props} value={value} error={error || problem}
      onChange={(event) => {
        setProblem(null)
        changeTo(onChange, event.target.value.replace(/\D/g, ''))
      }}
      onPaste={(event) => {
        const digits = event.clipboardData.getData('text').replace(/\D/g, '')
        if (digits.length > 11) {
          event.preventDefault()
          setProblem('That number has more than 11 digits. Mobile numbers have 11 digits, e.g. 09171234567.')
        }
      }}
      onBlur={() => setProblem(mobileProblem(value))}
    />
  )
}

export function YearLevelField({ value, emptyLabel = 'Select...', ...props }) {
  const known = !value || YEAR_LEVELS.some((year) => String(year.value) === String(value))
  return (
    <SelectField label="Year level" {...props} value={value}>
      <option value="">{emptyLabel}</option>
      {YEAR_LEVELS.map((year) => <option key={year.value} value={year.value}>{year.label}</option>)}
      {!known && <option value={value}>Year {value} (no longer offered)</option>}
    </SelectField>
  )
}

/** The school's programs by full name. An older value stays selectable until changed. */
export function ProgramField({ value, emptyLabel = 'Select your program...', ...props }) {
  const known = !value || PROGRAMS.includes(value)
  return (
    <SelectField label="Program / course" {...props} value={value}>
      <option value="">{emptyLabel}</option>
      {PROGRAMS.map((program) => <option key={program} value={program}>{program}</option>)}
      {!known && <option value={value}>{value} (not in the list)</option>}
    </SelectField>
  )
}
