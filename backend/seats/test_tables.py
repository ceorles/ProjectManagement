"""Whole-table availability, alongside the existing single-seat availability."""
from unittest import mock

from config.test_utils import PortalTestCase, at, frozen_time
from notifications.models import Notification
from reservations import services as reservation_services
from reservations.models import Reservation
from seats.models import Seat
from users.models import User

URL = '/api/seats/tables/set-status/'
Status = Reservation.Status


class TableManagementTests(PortalTestCase):
    def setUp(self):
        super().setUp()
        self.login_as(self.admin)

    def body(self, status='inactive', **extra):
        return {'zone': self.table_zone.pk, 'table_number': 1, 'status': status,
                'note': 'Table repair', **extra}

    def statuses(self):
        return list(Seat.objects.filter(table_number=1).order_by('number')
                    .values_list('status', flat=True))

    def overview(self):
        return self.client.get('/api/seats/tables/', {'zone': self.table_zone.pk}).data[0]

    def test_overview_lists_the_six_seats_of_a_table_together(self):
        table = self.overview()
        self.assertEqual(table['table_number'], 1)
        self.assertEqual([s['number'] for s in table['seats']],
                         ['T01-1', 'T01-2', 'T01-3', 'T01-4', 'T01-5', 'T01-6'])
        self.assertEqual(table['state'], 'available')
        self.assertEqual(table['available_seats'], 6)

    def test_seat_lists_keep_each_tables_seats_together(self):
        Seat.objects.create(zone=self.table_zone, number='T02-1', table_number=2, row=2, col=1)
        numbers = [seat['number'] for seat in self.client.get(
            '/api/seats/', {'zone': self.table_zone.pk}).data['results']]
        self.assertEqual(numbers[:7], ['T01-1', 'T01-2', 'T01-3', 'T01-4', 'T01-5', 'T01-6', 'T02-1'])
        with frozen_time(at(hour=9)):
            zones = self.client.get('/api/seats/availability/', {
                'date': '2026-03-02', 'start': '11:00', 'end': '12:00',
                'zone': self.table_zone.pk}).data['zones']
        self.assertEqual([s['number'] for s in zones[0]['seats']][:7], numbers[:7])

    def test_whole_table_out_of_service_and_back(self):
        response = self.client.post(URL, self.body())
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['state'], 'out_of_service')
        self.assertTrue(response.data['can_restore'])
        self.assertEqual(self.statuses(), ['inactive'] * 6)
        self.assertEqual(Seat.objects.get(number='T01-1').status_note, 'Table repair')
        # Other seats and the computers are not touched.
        self.assertEqual(Seat.objects.exclude(table_number=1).exclude(status='active').count(), 0)

        # Students cannot request it now.
        self.login_as(self.student)
        with frozen_time(at(hour=9)):
            refused = self.client.post('/api/reservations/', self.seat_payload(seat=self.table[0].pk))
        self.assertEqual(refused.status_code, 409)

        self.login_as(self.admin)
        restored = self.client.post(URL, self.body('active'))
        self.assertEqual(restored.status_code, 200, restored.data)
        self.assertEqual(restored.data['restored_seats'], 6)
        self.assertEqual(restored.data['state'], 'available')
        self.assertEqual(self.statuses(), ['active'] * 6)
        self.assertEqual(Seat.objects.get(number='T01-1').status_note, '')

    def test_a_seat_broken_before_the_table_closed_stays_broken(self):
        broken = self.table[2]
        self.client.post(f'/api/seats/{broken.pk}/set-status/',
                         {'status': 'inactive', 'note': 'Missing chair'})
        self.assertEqual(self.overview()['state'], 'partial')

        self.client.post(URL, self.body())
        broken.refresh_from_db()
        self.assertEqual(broken.status_note, 'Missing chair')  # keeps its own reason
        self.assertFalse(broken.out_with_table)

        response = self.client.post(URL, self.body('active'))
        self.assertEqual(response.data['restored_seats'], 5)
        self.assertEqual(response.data['state'], 'partial')
        self.assertEqual(response.data['available_seats'], 5)
        broken.refresh_from_db()
        self.assertEqual(broken.status, 'inactive')

    def test_a_single_seat_can_still_be_edited_on_its_own(self):
        seat = self.table[2]
        response = self.client.post(f'/api/seats/{seat.pk}/set-status/', {'status': 'inactive'})
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(self.statuses().count('inactive'), 1)
        self.assertEqual(self.overview()['available_seats'], 5)
        self.client.post(f'/api/seats/{seat.pk}/set-status/', {'status': 'active'})
        self.assertEqual(self.overview()['state'], 'available')

    def test_a_seat_cannot_be_reopened_while_its_table_is_closed(self):
        self.client.post(URL, self.body())
        response = self.client.post(f'/api/seats/{self.table[0].pk}/set-status/', {'status': 'active'})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(self.error_code(response), 'table_out_of_service')
        self.assertEqual(self.statuses(), ['inactive'] * 6)

    def test_a_seat_that_breaks_during_the_closure_stays_out_after_restoring(self):
        self.client.post(URL, self.body())
        seat = self.table[0]
        self.client.post(f'/api/seats/{seat.pk}/set-status/',
                         {'status': 'maintenance', 'note': 'Broken leg'})
        self.client.post(URL, self.body('active'))
        seat.refresh_from_db()
        self.assertEqual(seat.status, 'maintenance')
        self.assertEqual(self.statuses().count('active'), 5)

    def test_upcoming_reservations_must_be_confirmed_first(self):
        with frozen_time(at(hour=9)):
            reservation = self.book_seat(seat=self.table[1])
            self.login_as(self.admin)
            self.assertEqual(self.overview()['state'], 'reserved')
            self.assertEqual(self.overview()['reservations'][0]['code'], reservation.code)
            self.assertEqual(self.overview()['seats'][1]['reservation_count'], 1)

            refused = self.client.post(URL, self.body())
            self.assertEqual(refused.status_code, 409)
            self.assertEqual(self.error_code(refused), 'reservations_affected')
            self.assertEqual(self.statuses(), ['active'] * 6)
            reservation.refresh_from_db()
            self.assertEqual(reservation.status, Status.CONFIRMED)

            done = self.client.post(URL, self.body(confirm_cancellations=True))
            self.assertEqual(done.status_code, 200, done.data)
            self.assertEqual(done.data['cancelled_reservations'], 1)
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Status.CANCELLED)  # kept in the history
        self.assertIn('Table 1 is out of service', reservation.cancel_reason)
        self.assertTrue(Notification.objects.filter(
            user=self.student, title='Your reservation was cancelled').exists())

    def test_a_table_with_someone_seated_cannot_be_closed(self):
        with frozen_time(at(hour=9)):
            reservation = self.book_seat(seat=self.table[0])
        with frozen_time(at(hour=11)):
            reservation_services.check_in(reservation, actor=self.student)
            self.login_as(self.admin)
            response = self.client.post(URL, self.body(confirm_cancellations=True))
            self.assertEqual(response.status_code, 409)
            self.assertEqual(self.error_code(response), 'seat_in_use')
            single = self.client.post(f'/api/seats/{self.table[0].pk}/set-status/', {
                'status': 'inactive', 'confirm_cancellations': True})
            self.assertEqual(self.error_code(single), 'seat_in_use')
        self.assertEqual(self.statuses(), ['active'] * 6)

    def test_the_affected_reservations_of_one_seat_can_be_previewed(self):
        with frozen_time(at(hour=9)):
            reservation = self.book_seat(seat=self.computer)
            self.login_as(self.admin)
            data = self.client.get(f'/api/seats/{self.computer.pk}/affected-reservations/').data
        self.assertEqual(data[0]['code'], reservation.code)
        self.assertEqual(data[0]['seats'], ['PC-1'])

    def test_a_failure_leaves_all_six_seats_as_they_were(self):
        with frozen_time(at(hour=9)):
            self.book_seat(seat=self.table[5])
            self.login_as(self.admin)
            real = reservation_services.cancel_for_resource
            calls = []

            def fail_late(seat, **kwargs):
                calls.append(seat)
                if len(calls) == 6:
                    raise RuntimeError('database error on the last seat')
                return real(seat, **kwargs)

            self.client.raise_request_exception = False
            with mock.patch('seats.services.cancel_for_resource', fail_late):
                response = self.client.post(URL, self.body(confirm_cancellations=True))
        self.assertEqual(response.status_code, 500)
        self.assertEqual(self.statuses(), ['active'] * 6)
        self.assertFalse(Seat.objects.filter(out_with_table=True).exists())
        self.assertEqual(Reservation.objects.get().status, Status.CONFIRMED)

    def test_an_unknown_table_is_reported(self):
        response = self.client.post(URL, {**self.body(), 'table_number': 99})
        self.assertEqual(response.status_code, 404)

    def test_permissions_follow_the_seat_management_permission(self):
        for user in (self.student, self.assistant, self.librarian):
            self.login_as(user)
            self.assertEqual(self.client.post(URL, self.body()).status_code, 403, user.role)
            self.assertEqual(self.client.get(
                '/api/seats/tables/', {'zone': self.table_zone.pk}).status_code, 403, user.role)
            self.assertEqual(self.client.get(
                f'/api/seats/{self.seat.pk}/affected-reservations/').status_code, 403, user.role)
        self.assertEqual(self.statuses(), ['active'] * 6)

        User.objects.filter(pk=self.librarian.pk).update(can_manage_resources=True)
        self.librarian.refresh_from_db()
        self.login_as(self.librarian)
        self.assertEqual(self.client.post(URL, self.body()).status_code, 200)
