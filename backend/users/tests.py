from django.conf import settings

from config.test_utils import PASSWORD, PortalTestCase, at, frozen_time
from reservations.models import Reservation
from users.models import User

AJAX = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}


class RegistrationTests(PortalTestCase):
    def payload(self, **overrides):
        data = {
            'email': 'New.Student@Test.edu', 'first_name': 'Nia', 'last_name': 'New',
            'student_id': '2025-0100', 'password': PASSWORD, 'confirm_password': PASSWORD,
        }
        data.update(overrides)
        return data

    def test_student_can_register_and_is_signed_in(self):
        response = self.client.post('/api/auth/register/', self.payload())
        self.assertEqual(response.status_code, 201)
        self.assertIn('access', response.data)
        self.assertEqual(response.data['user']['role'], 'student')
        self.assertEqual(response.data['user']['email'], 'new.student@test.edu')
        cookie = response.cookies[settings.REFRESH_COOKIE_NAME]
        self.assertTrue(cookie['httponly'])

    def test_registration_cannot_choose_a_role(self):
        response = self.client.post(
            '/api/auth/register/', self.payload(role='admin', is_staff=True))
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(email='new.student@test.edu')
        self.assertEqual(user.role, User.Role.STUDENT)
        self.assertFalse(user.is_staff)

    def test_duplicate_email_and_student_id_are_rejected(self):
        response = self.client.post(
            '/api/auth/register/',
            self.payload(email='STUDENT@test.edu', student_id='2024-0001'))
        self.assertEqual(response.status_code, 400)
        fields = response.data['error']['fields']
        self.assertIn('email', fields)
        self.assertIn('student_id', fields)

    def test_weak_or_mismatched_password_is_rejected(self):
        weak = self.client.post(
            '/api/auth/register/', self.payload(password='12345', confirm_password='12345'))
        self.assertEqual(weak.status_code, 400)
        self.assertIn('password', weak.data['error']['fields'])
        mismatch = self.client.post(
            '/api/auth/register/', self.payload(confirm_password='Different!123'))
        self.assertIn('confirm_password', mismatch.data['error']['fields'])


class SessionTests(PortalTestCase):
    def login(self, email='student@test.edu', password=PASSWORD):
        return self.client.post('/api/auth/login/', {'email': email, 'password': password})

    def test_login_returns_access_token_and_httponly_cookie(self):
        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user']['role'], 'student')
        cookie = response.cookies[settings.REFRESH_COOKIE_NAME]
        self.assertTrue(cookie['httponly'])
        self.assertEqual(cookie['path'], '/api/auth/')
        # The refresh token must never appear in the response body.
        self.assertNotIn('refresh', response.data)

    def test_wrong_password_is_rejected(self):
        response = self.login(password='nope')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(self.error_code(response), 'invalid_credentials')

    def test_deactivated_account_cannot_sign_in(self):
        User.objects.filter(pk=self.student.pk).update(is_active=False)
        response = self.login()
        self.assertEqual(response.status_code, 403)

    def test_access_token_authenticates_api_calls(self):
        access = self.login().data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['email'], 'student@test.edu')

    def test_refresh_restores_the_session_from_the_cookie(self):
        self.login()
        response = self.client.post('/api/auth/refresh/', **AJAX)
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertEqual(response.data['user']['email'], 'student@test.edu')

    def test_refresh_requires_cookie_and_app_header(self):
        self.assertEqual(self.client.post('/api/auth/refresh/', **AJAX).status_code, 401)
        self.login()
        self.assertEqual(self.client.post('/api/auth/refresh/').status_code, 403)

    def test_refresh_fails_for_deactivated_account(self):
        self.login()
        User.objects.filter(pk=self.student.pk).update(is_active=False)
        response = self.client.post('/api/auth/refresh/', **AJAX)
        self.assertEqual(response.status_code, 401)

    def test_logout_revokes_the_refresh_token(self):
        token = self.login().cookies[settings.REFRESH_COOKIE_NAME].value
        self.assertEqual(self.client.post('/api/auth/logout/', **AJAX).status_code, 204)
        # Even if someone kept a copy of the cookie, it no longer works.
        self.client.cookies[settings.REFRESH_COOKIE_NAME] = token
        self.assertEqual(self.client.post('/api/auth/refresh/', **AJAX).status_code, 401)

    def test_protected_endpoints_require_authentication(self):
        for url in ('/api/auth/me/', '/api/reservations/', '/api/seats/',
                    '/api/library/overview/', '/api/notifications/'):
            self.assertEqual(self.client.get(url).status_code, 401, url)

    def test_profile_update_and_password_change(self):
        self.login_as(self.student)
        response = self.client.patch('/api/auth/me/', {'phone': '0917 000 0000', 'role': 'admin'})
        self.assertEqual(response.status_code, 200)
        self.student.refresh_from_db()
        self.assertEqual(self.student.phone, '0917 000 0000')
        self.assertEqual(self.student.role, User.Role.STUDENT)  # role is not editable

        wrong = self.client.post('/api/auth/change-password/', {
            'current_password': 'wrong', 'new_password': 'An0ther!Passw0rd',
            'confirm_password': 'An0ther!Passw0rd'})
        self.assertEqual(wrong.status_code, 400)
        ok = self.client.post('/api/auth/change-password/', {
            'current_password': PASSWORD, 'new_password': 'An0ther!Passw0rd',
            'confirm_password': 'An0ther!Passw0rd'})
        self.assertEqual(ok.status_code, 200)
        self.student.refresh_from_db()
        self.assertTrue(self.student.check_password('An0ther!Passw0rd'))


class AccountManagementTests(PortalTestCase):
    librarian_payload = {
        'email': 'new.librarian@test.edu', 'first_name': 'Nora', 'last_name': 'Librarian',
        'role': 'librarian', 'password': PASSWORD, 'can_manage_resources': True,
    }

    def test_admin_can_create_a_librarian(self):
        self.login_as(self.admin)
        response = self.client.post('/api/users/', self.librarian_payload)
        self.assertEqual(response.status_code, 201, response.data)
        user = User.objects.get(email='new.librarian@test.edu')
        self.assertEqual(user.role, User.Role.LIBRARIAN)
        self.assertTrue(user.can_manage_resources)
        self.assertTrue(user.check_password(PASSWORD))
        self.assertNotIn('password', response.data)

    def test_only_admins_can_manage_accounts(self):
        for user in (self.librarian, self.student):
            self.login_as(user)
            self.assertEqual(self.client.get('/api/users/').status_code, 403)
            self.assertEqual(
                self.client.post('/api/users/', self.librarian_payload).status_code, 403)
            self.assertEqual(
                self.client.post(f'/api/users/{self.student.pk}/deactivate/').status_code, 403)

    def test_admin_can_filter_and_search_accounts(self):
        self.login_as(self.admin)
        response = self.client.get('/api/users/', {'role': 'student', 'search': 'olive'})
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['email'], 'other@test.edu')

    def test_deactivating_a_student_cancels_their_upcoming_reservations(self):
        with frozen_time(at(hour=9)):
            reservation = self.book_seat()
            self.login_as(self.admin)
            response = self.client.post(f'/api/users/{self.student.pk}/deactivate/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['cancelled_reservations'], 1)
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Reservation.Status.CANCELLED)
        self.assertFalse(reservation.slots.exists())

    def test_admin_cannot_deactivate_self_or_change_own_role(self):
        self.login_as(self.admin)
        response = self.client.post(f'/api/users/{self.admin.pk}/deactivate/')
        self.assertEqual(response.status_code, 400)
        response = self.client.patch(f'/api/users/{self.admin.pk}/', {'role': 'student'})
        self.assertEqual(response.status_code, 400)

    def test_admin_can_reset_a_password(self):
        self.login_as(self.admin)
        response = self.client.post(
            f'/api/users/{self.student.pk}/set-password/', {'new_password': 'Fresh!Passw0rd9'})
        self.assertEqual(response.status_code, 200)
        self.student.refresh_from_db()
        self.assertTrue(self.student.check_password('Fresh!Passw0rd9'))

    def test_student_lookup_is_exact_match_only(self):
        self.login_as(self.student)
        found = self.client.get('/api/users/lookup/', {'student_id': '2024-0002'})
        self.assertEqual(found.status_code, 200)
        self.assertEqual(set(found.data), {'id', 'full_name', 'student_id'})
        partial = self.client.get('/api/users/lookup/', {'student_id': '2024'})
        self.assertEqual(partial.status_code, 404)
        # Browsing the student list is for staff only.
        self.assertEqual(self.client.get('/api/users/students/').status_code, 403)
