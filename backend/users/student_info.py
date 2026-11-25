"""
The rules for student details: student ID, year level, program, mobile number
and names. Registration, the Admin's account form and profile editing all use
these, so a Student and a Student Assistant are checked the same way.

The frontend copy of the program list and year levels is in
frontend/src/utils/studentInfo.js. Keep the two in step.
"""
import re

from rest_framework import serializers

# ── Student ID: 023A-12345 ─────────────────────────────────────────────────

# Prefixes the school has issued so far. Add new ones here when the school
# provides another ID range; nothing else needs to change.
STUDENT_ID_PREFIXES = ('019A', '020A', '021A', '022A', '023A')

STUDENT_ID_PATTERN = re.compile(r'^\d{3}A-\d{5}$')
STUDENT_ID_EXAMPLE = '023A-12345'


def normalize_student_id(value):
    """'023a 12345' or '023A12345' -> '023A-12345'. Anything else is returned tidied."""
    compact = re.sub(r'[\s-]+', '', value or '').upper()
    if len(compact) > 4:
        return f'{compact[:4]}-{compact[4:]}'
    return compact


def student_id_problem(value):
    """Why a normalized student ID is not acceptable, or None if it is."""
    if not STUDENT_ID_PATTERN.match(value):
        return (f'Enter the student ID as printed on your school ID, for example '
                f'{STUDENT_ID_EXAMPLE}: three digits and the letter A, then five digits.')
    if value[:4] not in STUDENT_ID_PREFIXES:
        return (f'Student IDs starting with {value[:4]} are not accepted. Accepted: '
                f'{", ".join(STUDENT_ID_PREFIXES)}.')
    return None


def is_new_format_student_id(value):
    return bool(value) and student_id_problem(value) is None


# ── Year level ─────────────────────────────────────────────────────────────

YEAR_LEVELS = ((1, '1st Year'), (2, '2nd Year'), (3, '3rd Year'), (4, '4th Year'))

# ── Programs ───────────────────────────────────────────────────────────────

# Code (for reference) -> full official name. The full name is what is stored
# and shown everywhere.
PROGRAMS = {
    'BSA': 'Bachelor of Science in Accountancy',
    'BSAIS': 'Bachelor of Science in Accounting Information System',
    'DHRS': 'Diploma in Hotel and Restaurant Services',
    'BSIT': 'Bachelor of Science in Information Technology',
    'BSE': 'Bachelor of Science in Entrepreneurship',
    'BSTVTED': 'Bachelor of Technical-Vocational Teacher Education',
    'ABELS': 'Bachelor of Arts in English Language Studies',
    'BSSW': 'Bachelor of Science in Social Work',
    'BSPA': 'Bachelor of Science in Public Administration',
}
PROGRAM_NAMES = tuple(PROGRAMS.values())


def _key(text):
    return re.sub(r'[^a-z0-9]', '', (text or '').lower())


# Spellings that clearly mean one program: the code, the full name, and the
# common "BS ..." short form. Anything else is left for a person to decide.
_PROGRAM_SPELLINGS = {}
for _code, _name in PROGRAMS.items():
    _PROGRAM_SPELLINGS[_key(_code)] = _name
    _PROGRAM_SPELLINGS[_key(_name)] = _name
    if _name.startswith('Bachelor of Science in '):
        _PROGRAM_SPELLINGS[_key('BS ' + _name.removeprefix('Bachelor of Science in '))] = _name


def official_program(value):
    """The full program name a stored or typed value stands for, or None."""
    return _PROGRAM_SPELLINGS.get(_key(value))


# ── Mobile number ──────────────────────────────────────────────────────────

MOBILE_PATTERN = re.compile(r'^09\d{9}$')

# ── Names ──────────────────────────────────────────────────────────────────

_ROMAN_NUMERALS = {'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X'}


def _capitalize_part(part):
    # Only all-capital or all-small parts are changed, so names that are
    # deliberately written like "McDonald" or "DeLeon" keep their capitals.
    if part in _ROMAN_NUMERALS or not (part.isupper() or part.islower()):
        return part
    return part[:1].upper() + part[1:].lower()


def format_name(value):
    """'KYLA MAE' -> 'Kyla Mae', 'juan dela cruz' -> 'Juan Dela Cruz'."""
    words = (value or '').split()
    formatted = []
    for word in words:
        # Each side of a hyphen or apostrophe is capitalized: Mary-Ann, O'Neil.
        pieces = re.split(r"([-'’])", word)
        formatted.append(''.join(_capitalize_part(piece) for piece in pieces))
    return ' '.join(formatted)


# ── Serializer support ─────────────────────────────────────────────────────

class StudentInfoValidationMixin:
    """
    Validation shared by every form that collects these details. A value an
    existing account already has is accepted unchanged, so accounts created
    before these rules keep working until their details are updated.
    """

    def _unchanged(self, field, value):
        return self.instance is not None and getattr(self.instance, field) == value

    def validate_first_name(self, value):
        return format_name(value)

    def validate_last_name(self, value):
        return format_name(value)

    def validate_phone(self, value):
        phone = (value or '').strip()
        if not phone or self._unchanged('phone', phone):
            return phone
        if not MOBILE_PATTERN.match(phone):
            raise serializers.ValidationError(
                'Enter an 11-digit mobile number that starts with 09, for example 09171234567.')
        return phone

    def validate_year_level(self, value):
        if value is None or self._unchanged('year_level', value):
            return value
        if value not in dict(YEAR_LEVELS):
            raise serializers.ValidationError('Choose 1st Year, 2nd Year, 3rd Year or 4th Year.')
        return value

    def validate_program(self, value):
        program = (value or '').strip()
        if not program or self._unchanged('program', program):
            return program
        official = official_program(program)
        if official is None:
            raise serializers.ValidationError('Choose a program from the list.')
        return official

    def clean_student_id(self, value):
        """Normalize and check a newly entered student ID (uniqueness is checked separately)."""
        student_id = (value or '').strip()
        if not student_id:
            return None
        if self._unchanged('student_id', student_id):
            return student_id
        student_id = normalize_student_id(student_id)
        problem = student_id_problem(student_id)
        if problem:
            raise serializers.ValidationError(problem)
        return student_id
