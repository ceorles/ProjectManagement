"""Student ID, year level, program, mobile number and name rules (revision 5)."""
import csv
import tempfile
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError

from config.test_utils import PASSWORD, PortalTestCase
from users.models import User
from users.student_info import format_name, normalize_student_id, official_program

BSIT = 'Bachelor of Science in Information Technology'


class FormattingTests(PortalTestCase):
    def test_names(self):
        cases = {
            'KYLA MAE CANTOS': 'Kyla Mae Cantos', 'JOHN DOE': 'John Doe',
            'maria clara santos': 'Maria Clara Santos', 'JUAN DELA CRUZ': 'Juan Dela Cruz',
            '  ana   marie ': 'Ana Marie', "MARY-ANN O'NEIL": "Mary-Ann O'Neil",
            'McDonald': 'McDonald', 'JOSE RIZAL III': 'Jose Rizal III', 'PEÑA': 'Peña',
        }
        for raw, expected in cases.items():
            self.assertEqual(format_name(raw), expected, raw)

    def test_student_id_normalization(self):
        for raw in ('023A12345', '023a-12345', ' 023A 12345 ', '023A-12345'):
            self.assertEqual(normalize_student_id(raw), '023A-12345', raw)

    def test_program_spellings(self):
        for raw in ('BSIT', 'bsit', 'BS Information Technology', BSIT):
            self.assertEqual(official_program(raw), BSIT, raw)
        self.assertEqual(official_program('ABELS'), 'Bachelor of Arts in English Language Studies')
        self.assertIsNone(official_program('BS Nursing'))


class RegistrationRulesTests(PortalTestCase):
    def register(self, **changes):
        payload = {
            'email': 'kyla@test.edu', 'first_name': 'KYLA MAE', 'last_name': 'CANTOS',
            'student_id': '023A12345', 'program': BSIT, 'year_level': 2, 'phone': '09171234567',
            'password': PASSWORD, 'confirm_password': PASSWORD, **changes,
        }
        return self.client.post('/api/auth/register/', payload)

    def test_valid_registration_is_normalized(self):
        response = self.register()
        self.assertEqual(response.status_code, 201, response.data)
        user = User.objects.get(email='kyla@test.edu')
        self.assertEqual((user.first_name, user.last_name), ('Kyla Mae', 'Cantos'))
        self.assertEqual(user.student_id, '023A-12345')

    def test_invalid_student_ids_are_rejected(self):
        for bad in ('2024-00123', '023B-12345', '023A-1234', '023A-1234X', '018A-12345', ''):
            response = self.register(student_id=bad)
            self.assertEqual(response.status_code, 400, bad)
            self.assertIn('student_id', response.data['error']['fields'], bad)

    def test_duplicate_student_id_is_rejected_in_any_spelling(self):
        self.assertEqual(self.register().status_code, 201)
        for spelling in ('023A-12345', '023a12345'):
            response = self.register(email='other@test.edu', student_id=spelling)
            self.assertEqual(response.status_code, 400)
            self.assertIn('already registered', response.data['error']['fields']['student_id'][0])

    def test_year_5_and_6_are_refused(self):
        for year in (0, 5, 6):
            response = self.register(year_level=year)
            self.assertEqual(response.status_code, 400, year)

    def test_programs_must_come_from_the_list(self):
        self.assertEqual(self.register(program='BS Nursing').status_code, 400)
        self.assertEqual(self.register(program='BSIT').status_code, 201)
        self.assertEqual(User.objects.get(email='kyla@test.edu').program, BSIT)

    def test_mobile_numbers_are_checked_not_cut(self):
        for bad in ('091712345678', '0917123456', '0917-123-4567', '+639171234567', '19171234567'):
            response = self.register(phone=bad)
            self.assertEqual(response.status_code, 400, bad)
            self.assertIn('phone', response.data['error']['fields'])


class ExistingAccountTests(PortalTestCase):
    """Accounts made before these rules keep working until they are updated."""

    def setUp(self):
        User.objects.filter(pk=self.student.pk).update(
            student_id='2024-00123', program='BS Nursing', year_level=6, phone='0917 000')
        self.student.refresh_from_db()

    def test_profile_saves_without_touching_old_values(self):
        self.login_as(self.student)
        response = self.client.patch('/api/auth/me/', {
            'first_name': 'SAM', 'program': 'BS Nursing', 'year_level': 6, 'phone': '0917 000'})
        self.assertEqual(response.status_code, 200, response.data)
        self.student.refresh_from_db()
        self.assertEqual(self.student.first_name, 'Sam')
        self.assertEqual(self.student.student_id, '2024-00123')

    def test_changing_a_value_must_follow_the_new_rules(self):
        self.login_as(self.student)
        self.assertEqual(self.client.patch('/api/auth/me/', {'year_level': 5}).status_code, 400)
        self.assertEqual(self.client.patch('/api/auth/me/', {'program': 'BS Math'}).status_code, 400)

    def test_old_student_id_can_still_sign_in(self):
        response = self.client.post('/api/auth/login/', {'email': self.student.email, 'password': PASSWORD})
        self.assertEqual(response.status_code, 200)

    def test_admin_can_keep_or_replace_an_old_id(self):
        self.login_as(self.admin)
        url = f'/api/users/{self.student.pk}/'
        self.assertEqual(self.client.patch(url, {'student_id': '2024-00123'}).status_code, 200)
        self.assertEqual(self.client.patch(url, {'student_id': '2024-00999'}).status_code, 400)
        self.assertEqual(self.client.patch(url, {'student_id': '022a54321'}).status_code, 200)
        self.student.refresh_from_db()
        self.assertEqual(self.student.student_id, '022A-54321')


class AssistantAccountTests(PortalTestCase):
    def test_admin_creates_an_assistant_with_the_same_rules(self):
        self.login_as(self.admin)
        payload = {
            'role': 'assistant', 'email': 'helper@test.edu', 'first_name': 'JUAN',
            'last_name': 'dela cruz', 'student_id': '021A55555', 'program': 'BSA',
            'year_level': 3, 'phone': '09181234567', 'password': PASSWORD,
        }
        for field, bad in (('student_id', '2023-0777'), ('year_level', 5),
                           ('program', 'Anything'), ('phone', '091812345678')):
            response = self.client.post('/api/users/', {**payload, field: bad})
            self.assertEqual(response.status_code, 400, field)
            self.assertIn(field, response.data['error']['fields'])
        response = self.client.post('/api/users/', payload)
        self.assertEqual(response.status_code, 201, response.data)
        helper = User.objects.get(email='helper@test.edu')
        self.assertEqual((helper.first_name, helper.last_name), ('Juan', 'Dela Cruz'))
        self.assertEqual(helper.student_id, '021A-55555')
        self.assertEqual(helper.program, 'Bachelor of Science in Accountancy')

    def test_staff_accounts_need_no_student_details(self):
        self.login_as(self.admin)
        response = self.client.post('/api/users/', {
            'role': 'librarian', 'email': 'lib2@test.edu', 'first_name': 'NORA',
            'last_name': 'REYES', 'password': PASSWORD})
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['full_name'], 'Nora Reyes')


class ReportAccessTests(PortalTestCase):
    def test_reports_are_for_the_admin_only(self):
        for user, expected in ((self.admin, 200), (self.librarian, 403),
                               (self.assistant, 403), (self.student, 403)):
            self.login_as(user)
            response = self.client.get('/api/reports/usage/', {'days': 7})
            self.assertEqual(response.status_code, expected, user.role)
        self.client.logout()
        self.client.credentials()
        self.assertEqual(self.client.get('/api/reports/usage/').status_code, 401)

    def test_librarian_keeps_the_operations_dashboard(self):
        self.login_as(self.librarian)
        self.assertEqual(self.client.get('/api/reports/staff-dashboard/').status_code, 200)


class UserListFilterTests(PortalTestCase):
    def emails(self, **params):
        self.login_as(self.admin)
        response = self.client.get('/api/users/', params)
        self.assertEqual(response.status_code, 200)
        return [row['email'] for row in response.data['results']]

    def test_never_signed_in_and_recent_sign_in(self):
        from django.utils import timezone
        from datetime import timedelta
        now = timezone.now()
        User.objects.update(last_login=None)
        User.objects.filter(pk=self.student.pk).update(last_login=now - timedelta(days=2))
        User.objects.filter(pk=self.librarian.pk).update(last_login=now - timedelta(hours=1))
        never = self.emails(signed_in='never')
        self.assertNotIn(self.student.email, never)
        self.assertNotIn(self.librarian.email, never)
        recent = self.emails(ordering='-last_login')
        # Most recent first; accounts that never signed in come after them.
        self.assertEqual(recent[:2], [self.librarian.email, self.student.email])
        self.assertEqual(len(recent), User.objects.count())

    def test_recently_added_and_alphabetical(self):
        newest = self.emails(ordering='-date_joined')
        self.assertEqual(newest[0], User.objects.order_by('-date_joined', '-id').first().email)
        names = [u.full_name for u in User.objects.order_by('first_name', 'last_name')]
        self.login_as(self.admin)
        listed = [r['full_name'] for r in self.client.get('/api/users/', {'ordering': 'name'}).data['results']]
        self.assertEqual(listed, names)
        reverse = [r['full_name'] for r in self.client.get('/api/users/', {'ordering': '-name'}).data['results']]
        self.assertEqual(reverse, names[::-1])

    def test_filters_combine_with_search_and_role(self):
        self.assertEqual(self.emails(role='student', search='Olive'), [self.other_student.email])
        self.assertEqual(self.emails(role='librarian', status='inactive'), [])

    def test_only_admins_can_list_users(self):
        for user in (self.librarian, self.assistant, self.student):
            self.login_as(user)
            self.assertEqual(self.client.get('/api/users/', {'ordering': 'name'}).status_code, 403)


class StudentIdMappingTests(PortalTestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.csv = Path(folder.name) / 'ids.csv'

    def run_command(self, *args):
        call_command('update_student_ids', *args, stdout=StringIO())

    def fill(self, mapping):
        rows = list(csv.DictReader(self.csv.open(encoding='utf-8-sig')))
        for row in rows:
            row['new_student_id'] = mapping.get(row['email'], '')
        with self.csv.open('w', newline='', encoding='utf-8-sig') as file:
            writer = csv.DictWriter(file, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    def test_template_check_and_commit(self):
        self.run_command('--export', str(self.csv))
        emails = [row['email'] for row in csv.DictReader(self.csv.open(encoding='utf-8-sig'))]
        self.assertIn(self.student.email, emails)
        self.fill({self.student.email: '023A11111'})

        self.run_command('--apply', str(self.csv))  # check only
        self.student.refresh_from_db()
        self.assertEqual(self.student.student_id, '2024-0001')

        self.run_command('--apply', str(self.csv), '--commit')
        self.student.refresh_from_db()
        self.assertEqual(self.student.student_id, '023A-11111')
        self.assertTrue(self.student.check_password(PASSWORD))

    def test_duplicates_and_bad_ids_save_nothing(self):
        self.run_command('--export', str(self.csv))
        self.fill({self.student.email: '023A11111', self.other_student.email: '023A-11111'})
        with self.assertRaises(CommandError):
            self.run_command('--apply', str(self.csv), '--commit')
        self.fill({self.student.email: '2024-99999'})
        with self.assertRaises(CommandError):
            self.run_command('--apply', str(self.csv), '--commit')
        self.student.refresh_from_db()
        self.assertEqual(self.student.student_id, '2024-0001')
