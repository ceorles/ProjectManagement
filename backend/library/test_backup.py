"""The backup and restore commands used to move the library to a new database."""
import json
import tempfile
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from config.test_utils import PASSWORD
from library.models import Floor
from seats.models import Seat, Zone
from users.models import User


class BackupTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email='librarian@test.edu', password=PASSWORD, first_name='Lia', last_name='Brarian',
            role=User.Role.LIBRARIAN)
        floor = Floor.objects.create(name='Old Floor', level=9)
        zone = Zone.objects.create(floor=floor, name='Old Zone', rows=1, cols=1)
        cls.archived = Seat.objects.create(zone=zone, number='OLD-1', row=1, col=1, is_archived=True)

    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / 'backup.json'

    def backup(self):
        call_command('create_backup', str(self.path), stdout=StringIO())
        return json.loads(self.path.read_text(encoding='utf-8'))

    def test_includes_archived_records_and_only_the_password_hash(self):
        records = self.backup()
        seats = [r for r in records if r['model'] == 'seats.seat']
        self.assertIn(self.archived.pk, [r['pk'] for r in seats])
        account = next(r for r in records if r['model'] == 'users.user')
        self.assertEqual(account['fields']['password'], self.user.password)
        self.assertNotIn(PASSWORD, self.path.read_text(encoding='utf-8'))

    def test_leaves_out_what_django_rebuilds(self):
        models = {r['model'] for r in self.backup()}
        for label in ('contenttypes.contenttype', 'auth.permission', 'sessions.session',
                      'token_blacklist.outstandingtoken'):
            self.assertNotIn(label, models)

    def test_does_not_overwrite_an_existing_backup(self):
        self.path.write_text('keep me', encoding='utf-8')
        with self.assertRaises(CommandError):
            call_command('create_backup', str(self.path), stdout=StringIO())
        self.assertEqual(self.path.read_text(encoding='utf-8'), 'keep me')

    def test_replace_keeps_the_previous_file(self):
        self.path.write_text('old', encoding='utf-8')
        call_command('create_backup', str(self.path), replace=True, stdout=StringIO())
        previous = self.path.with_name('backup.previous.json')
        self.assertEqual(previous.read_text(encoding='utf-8'), 'old')

    def test_restore_brings_everything_back_with_working_logins(self):
        self.backup()
        pk, seat_pk = self.user.pk, self.archived.pk
        Seat.all_objects.all().delete()
        User.objects.all().delete()

        call_command('restore_backup', str(self.path), yes=True, stdout=StringIO())

        user = User.objects.get(pk=pk)
        self.assertTrue(user.check_password(PASSWORD))
        self.assertTrue(Seat.all_objects.get(pk=seat_pk).is_archived)

    def test_restore_refuses_a_database_that_has_accounts(self):
        self.backup()
        with self.assertRaisesMessage(CommandError, 'already has 1 accounts'):
            call_command('restore_backup', str(self.path), yes=True, stdout=StringIO())
        self.assertEqual(User.objects.count(), 1)

    def test_restore_rejects_a_file_that_is_not_a_backup(self):
        self.path.write_text('not json', encoding='utf-8')
        with self.assertRaisesMessage(CommandError, 'not a valid backup'):
            call_command('restore_backup', str(self.path), yes=True, stdout=StringIO())
