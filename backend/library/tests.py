from config.test_utils import MONDAY, PortalTestCase, at, frozen_time
from library.models import ReservationPolicy


class LibrarySettingsTests(PortalTestCase):
    def test_overview_gives_the_booking_screens_what_they_need(self):
        self.login_as(self.student)
        with frozen_time(at(hour=9)):
            response = self.client.get('/api/library/overview/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['today'], MONDAY.isoformat())
        self.assertEqual(response.data['slot_minutes'], 30)
        self.assertEqual(len(response.data['hours']), 7)
        self.assertEqual(response.data['policy']['max_advance_days'], 7)
        self.assertEqual(response.data['floors'][0]['name'], 'Ground Floor')

    def test_only_admin_can_change_the_policy(self):
        for user in (self.student, self.librarian):
            self.login_as(user)
            self.assertEqual(self.client.get('/api/library/policy/').status_code, 200)
            self.assertEqual(
                self.client.patch('/api/library/policy/', {'max_advance_days': 30}).status_code,
                403)
        self.login_as(self.admin)
        response = self.client.patch('/api/library/policy/', {'max_advance_days': 14})
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(ReservationPolicy.load().max_advance_days, 14)

    def test_policy_values_are_validated(self):
        self.login_as(self.admin)
        ragged = self.client.patch('/api/library/policy/', {'max_seat_duration_minutes': 45})
        self.assertEqual(ragged.status_code, 400)
        inverted = self.client.patch(
            '/api/library/policy/', {'min_duration_minutes': 120, 'max_room_duration_minutes': 60})
        self.assertEqual(inverted.status_code, 400)

    def test_only_admin_can_change_hours_and_closures(self):
        self.login_as(self.librarian)
        hours = self.client.get('/api/library/hours/').data
        self.assertEqual(self.client.put('/api/library/hours/', hours).status_code, 403)
        self.assertEqual(
            self.client.post('/api/library/closures/',
                             {'date': '2026-03-10', 'reason': 'Holiday'}).status_code, 403)

    def test_hours_must_be_complete_and_sensible(self):
        self.login_as(self.admin)
        hours = self.client.get('/api/library/hours/').data
        self.assertEqual(self.client.put('/api/library/hours/', hours[:6]).status_code, 400)
        hours[0]['opens_at'], hours[0]['closes_at'] = '18:00', '09:00'
        self.assertEqual(self.client.put('/api/library/hours/', hours).status_code, 400)

    def test_closure_cannot_be_in_the_past_or_duplicated(self):
        self.login_as(self.admin)
        with frozen_time(at(hour=9)):
            past = self.client.post(
                '/api/library/closures/', {'date': '2026-03-01', 'reason': 'Too late'})
            self.assertEqual(past.status_code, 400)
            first = self.client.post(
                '/api/library/closures/', {'date': '2026-03-10', 'reason': 'Holiday'})
            self.assertEqual(first.status_code, 201)
            again = self.client.post(
                '/api/library/closures/', {'date': '2026-03-10', 'reason': 'Holiday'})
            self.assertEqual(again.status_code, 400)
            self.assertEqual(
                self.client.delete(f'/api/library/closures/{first.data["id"]}/').status_code, 204)
