// Student details shared by registration, the Admin's account form and the
// profile page. The server checks the same rules (backend/users/student_info.py);
// keep the program list and year levels in step with it.

export const YEAR_LEVELS = [
  { value: 1, label: '1st Year' },
  { value: 2, label: '2nd Year' },
  { value: 3, label: '3rd Year' },
  { value: 4, label: '4th Year' },
]

/** Full official names. They are what is saved and shown everywhere. */
export const PROGRAMS = [
  'Bachelor of Science in Accountancy',
  'Bachelor of Science in Accounting Information System',
  'Diploma in Hotel and Restaurant Services',
  'Bachelor of Science in Information Technology',
  'Bachelor of Science in Entrepreneurship',
  'Bachelor of Technical-Vocational Teacher Education',
  'Bachelor of Arts in English Language Studies',
  'Bachelor of Science in Social Work',
  'Bachelor of Science in Public Administration',
]

export const STUDENT_ID_EXAMPLE = '023A-12345'

/**
 * Shapes what is typed or pasted into 023A-12345: three digits, the letter A,
 * a hyphen (added automatically), then five digits. Characters that do not
 * fit their position are ignored. `addHyphen` is false while deleting, so
 * Backspace can remove the hyphen.
 */
export function formatStudentId(text, { addHyphen = true } = {}) {
  let prefix = ''
  let number = ''
  for (const char of String(text ?? '').toUpperCase()) {
    if (prefix.length < 3) {
      if (/\d/.test(char)) prefix += char
    } else if (prefix.length === 3) {
      if (char === 'A') prefix += char
    } else if (number.length < 5 && /\d/.test(char)) {
      number += char
    }
  }
  if (prefix.length < 4) return prefix
  return number || addHyphen ? `${prefix}-${number}` : prefix
}

/** Message for an incomplete ID, or null. The server also checks the prefix. */
export function studentIdProblem(value) {
  if (!value) return 'Enter your student ID.'
  return /^\d{3}A-\d{5}$/.test(value)
    ? null
    : `Enter the full student ID, for example ${STUDENT_ID_EXAMPLE}.`
}

export function mobileProblem(value) {
  if (!value) return null
  return /^09\d{9}$/.test(value)
    ? null
    : 'Enter an 11-digit mobile number that starts with 09, for example 09171234567.'
}

const ROMAN_NUMERALS = new Set(['II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X'])

function capitalizePart(part) {
  const upper = part.toUpperCase()
  const lower = part.toLowerCase()
  // Names deliberately written with inner capitals (McDonald) are kept.
  if (ROMAN_NUMERALS.has(part) || (part !== upper && part !== lower)) return part
  return lower.charAt(0).toUpperCase() + lower.slice(1)
}

/** 'KYLA MAE' -> 'Kyla Mae', 'juan dela cruz' -> 'Juan Dela Cruz'. */
export function formatName(value) {
  return String(value ?? '')
    .split(/\s+/)
    .filter(Boolean)
    .map((word) => word.split(/([-'’])/).map(capitalizePart).join(''))
    .join(' ')
}
