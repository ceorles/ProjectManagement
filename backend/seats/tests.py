from config.test_utils import PortalTestCase, at, frozen_time
from reservations.models import Reservation
from seats.models import Seat
from users.models import User


class SeatManagementTests(PortalTestCase):
    payload = {'number': 'a09', 'row': 2, 'col': 1, 'has_power_outlet': True}

    def create(self):
        return self.client.post('/api/seats/', {**self.payload, 'zone': self.zone.pk})

    def test_everyone_signed_in_can_browse_seats_and_zones(self):
        self.login_as(self.student)
        self.assertEqual(self.client.get('/api/seats/').data['count'], 2)
        self.assertEqual(len(self.client.get('/api/seats/zones/').data), 1)

    def test_admin_can_create_edit_and_delete_a_seat(self):
        self.login_as(self.admin)
        created = self.create()
        self.assertEqual(created.status_code, 201, created.data)
        self.assertEqual(created.data['number'], 'A09')  # normalised
        seat_id = created.data['id']
        edited = self.client.patch(f'/api/seats/{seat_id}/', {'near_window': True})
        self.assertTrue(edited.data['near_window'])
        self.assertEqual(self.client.delete(f'/api/seats/{seat_id}/').status_code, 204)

    def test_students_and_unprivileged_librarians_cannot_manage_seats(self):
        for user in (self.student, self.librarian):
            self.login_as(user)
            self.assertEqual(self.create().status_code, 403)
            self.assertEqual(
                self.client.patch(f'/api/seats/{self.seat.pk}/', {'row': 2}).status_code, 403)
            self.assertEqual(self.client.delete(f'/api/seats/{self.seat.pk}/').status_code, 403)
            self.assertEqual(
                self.client.post(f'/api/seats/{self.seat.pk}/set-status/',
                                 {'status': 'maintenance'}).status_code, 403)

    def test_librarian_granted_permission_by_admin_can_manage_seats(self):
        User.objects.filter(pk=self.librarian.pk).update(can_manage_resources=True)
        self.librarian.refresh_from_db()
        self.login_as(self.librarian)
        self.assertEqual(self.create().status_code, 201)

    def test_seat_position_and_number_must_be_valid(self):
        self.login_as(self.admin)
        taken = self.client.post(
            '/api/seats/', {'number': 'B01', 'zone': self.zone.pk, 'row': 1, 'col': 1})
        self.assertEqual(taken.status_code, 400)
        outside = self.client.post(
            '/api/seats/', {'number': 'B02', 'zone': self.zone.pk, 'row': 9, 'col': 1})
        self.assertEqual(outside.status_code, 400)
        duplicate = self.client.post(
            '/api/seats/', {'number': 'a01', 'zone': self.zone.pk, 'row': 2, 'col': 2})
        self.assertIn('number', duplicate.data['error']['fields'])

    def test_zone_cannot_shrink_below_its_seats(self):
        self.login_as(self.admin)
        response = self.client.patch(f'/api/seats/zones/{self.zone.pk}/', {'cols': 1})
        self.assertEqual(response.status_code, 400)

    def test_maintenance_cancels_upcoming_reservations_and_blocks_booking(self):
        with frozen_time(at(hour=9)):
            reservation = self.book_seat()
            self.login_as(self.admin)
            response = self.client.post(
                f'/api/seats/{self.seat.pk}/set-status/',
                {'status': 'maintenance', 'note': 'Broken armrest'})
            self.assertEqual(response.status_code, 200, response.data)
            self.assertEqual(response.data['cancelled_reservations'], 1)
            reservation.refresh_from_db()
            self.assertEqual(reservation.status, Reservation.Status.CANCELLED)

            self.login_as(self.other_student)
            blocked = self.client.post('/api/reservations/', self.seat_payload())
            self.assertEqual(blocked.status_code, 409)

            self.login_as(self.admin)
            self.client.post(f'/api/seats/{self.seat.pk}/set-status/', {'status': 'active'})
            self.login_as(self.other_student)
            self.assertEqual(
                self.client.post('/api/reservations/', self.seat_payload()).status_code, 201)

    def test_seat_with_history_cannot_be_deleted(self):
        with frozen_time(at(hour=9)):
            self.book_seat()
        self.login_as(self.admin)
        response = self.client.delete(f'/api/seats/{self.seat.pk}/')
        self.assertEqual(response.status_code, 409)
        self.assertEqual(self.error_code(response), 'in_use')
        self.assertTrue(Seat.objects.filter(pk=self.seat.pk).exists())
