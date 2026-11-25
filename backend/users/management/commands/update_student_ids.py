"""
Moves students to their school-issued IDs (023A-12345) from a list you fill in.
Nobody's ID is ever invented: an account only changes when you give its new ID.

1. Make the template (accounts that still have an old-style ID):

       python manage.py update_student_ids --export student-ids.csv

2. Open it in Excel and type each student's real ID in the new_student_id
   column. Leave a row blank to keep that account's current ID for now.

3. Check the file. Nothing is saved:

       python manage.py update_student_ids --apply student-ids.csv

4. Save the changes, all at once or none at all:

       python manage.py update_student_ids --apply student-ids.csv --commit

Only the student ID changes. Passwords, sign-in (by email), reservations and
history stay exactly as they are. The CSV holds personal data: keep it private.
"""
import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from activity.services import log_activity
from users.models import User
from users.student_info import is_new_format_student_id, normalize_student_id, student_id_problem

COLUMNS = ['email', 'name', 'role', 'current_student_id', 'new_student_id']


class Command(BaseCommand):
    help = "Update students' IDs to the new school format from a CSV you fill in."

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--export', metavar='CSV', help='Write the template.')
        group.add_argument('--apply', metavar='CSV', help='Read a filled-in template.')
        parser.add_argument('--commit', action='store_true', help='Save the changes.')

    def _path(self, name):
        path = Path(name)
        return path if path.is_absolute() else settings.BASE_DIR / path

    def handle(self, *args, export=None, apply=None, commit=False, **options):
        if export:
            self.export(self._path(export))
        else:
            self.apply(self._path(apply), commit)

    def export(self, path):
        if path.exists():
            raise CommandError(f'{path} already exists. Choose another name.')
        accounts = [
            user for user in User.objects.filter(
                role__in=(User.Role.STUDENT, User.Role.ASSISTANT)).order_by('last_name', 'first_name')
            if not is_new_format_student_id(user.student_id)
        ]
        # utf-8-sig so Excel shows names with ñ correctly.
        with path.open('w', newline='', encoding='utf-8-sig') as file:
            writer = csv.writer(file)
            writer.writerow(COLUMNS)
            for user in accounts:
                writer.writerow([user.email, user.full_name, user.get_role_display(),
                                 user.student_id or '', ''])
        self.stdout.write(self.style.SUCCESS(f'{len(accounts)} accounts written to {path}'))

    def apply(self, path, commit):
        if not path.exists():
            raise CommandError(f'{path} was not found.')
        with path.open(newline='', encoding='utf-8-sig') as file:
            rows = list(csv.DictReader(file))
        if rows and not set(COLUMNS) <= set(rows[0]):
            raise CommandError(f'The file must have the columns: {", ".join(COLUMNS)}.')

        changes, errors, seen = [], [], {}
        for line, row in enumerate(rows, start=2):
            new_id = normalize_student_id(row.get('new_student_id', '').strip())
            if not new_id:
                continue
            email = row.get('email', '').strip().lower()
            user = User.objects.filter(email__iexact=email).first()
            problem = student_id_problem(new_id)
            if user is None:
                errors.append(f'Line {line}: no account has the email {email}.')
            elif problem:
                errors.append(f'Line {line} ({email}): {problem}')
            elif new_id in seen:
                errors.append(f'Line {line} ({email}): {new_id} is also given on line {seen[new_id]}.')
            elif User.objects.filter(student_id__iexact=new_id).exclude(pk=user.pk).exists():
                errors.append(f'Line {line} ({email}): {new_id} already belongs to another account.')
            else:
                seen[new_id] = line
                if user.student_id != new_id:
                    changes.append((user, user.student_id, new_id))

        for message in errors:
            self.stdout.write(self.style.ERROR(message))
        for user, old, new in changes:
            self.stdout.write(f'  {user.email}: {old or "(none)"} -> {new}')
        if errors:
            raise CommandError(f'{len(errors)} problem(s) found. Nothing was saved.')
        if not commit:
            self.stdout.write(self.style.WARNING(
                f'{len(changes)} change(s) checked. Nothing was saved: add --commit to save.'))
            return

        with transaction.atomic():
            for user, old, new in changes:
                user.student_id = new
                user.save(update_fields=['student_id'])
                log_activity('user.updated', f'Student ID of {user.full_name} changed from '
                             f'{old or "none"} to {new}.', target=user)
        self.stdout.write(self.style.SUCCESS(f'{len(changes)} student ID(s) updated.'))
