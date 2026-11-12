"""The reservation and availability endpoints, including who may do what."""
from config.test_utils import MONDAY, PortalTestCase, at, frozen_time
from library.models import ResourceStatus
from reservations import services
from reservations.models import Reservation

Status = Reservation.Status
DAY = MONDAY.isoformat()


class ReservationApiTests(PortalTestCase):
    def test_student_books_a_seat(self):
        self.login_as(self.student)
        with frozen_time(at(hour=9)):
            response = self.client.post('/api/reservations/', self.seat_payload())
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['status'], 'confirmed')
        self.assertEqual(response.data['resource']['name'], 'Seat A01')
        self.assertEqual(response.data['date'], DAY)
        self.assertEqual(response.data['start_time'], '11:00')
        self.assertTrue(response.data['is_owner'])
        self.assertTrue(response.data['can_cancel'])
        self.assertFalse(response.data['can_check_in'])  # too early

    def test_student_books_a_room_with_an_invited_classmate(self):
        self.login_as(self.student)
        with frozen_time(at(hour=9)):
            response = self.client.post('/api/reservations/', {
                'resource_type': 'room', 'room': self.room.pk, 'date': DAY,
                'start_time': '13:00', 'end_time': '14:30', 'participant_count': 3,
                'purpose': 'Capstone meeting', 'participant_student_ids': ['2024-0002'],
            })
            self.assertEqual(response.status_code, 201, response.data)
            self.assertEqual(response.data['participant_count'], 3)
            self.assertEqual(response.data['participants'][0]['full_name'], 'Olive Other')

            # The invited classmate sees it, read-only.
            self.login_as(self.other_student)
            listing = self.client.get('/api/reservations/')
            self.assertEqual(listing.data['count'], 1)
            self.assertFalse(listing.data['results'][0]['is_owner'])
            self.assertFalse(listing.data['results'][0]['can_cancel'])
            cancel = self.client.post(f'/api/reservations/{response.data["id"]}/cancel/')
            self.assertEqual(cancel.status_code, 403)

    def test_conflict_returns_409(self):
        with frozen_time(at(hour=9)):
            self.book_seat(student=self.other_student)
            self.login_as(self.student)
            response = self.client.post('/api/reservations/', self.seat_payload())
        self.assertEqual(response.status_code, 409)
        self.assertEqual(self.error_code(response), 'slot_taken')

    def test_invalid_payloads_are_rejected(self):
        self.login_as(self.student)
        with frozen_time(at(hour=9)):
            missing = self.client.post('/api/reservations/', self.seat_payload(seat=None))
            self.assertEqual(missing.status_code, 400)
            unknown = self.client.post('/api/reservations/', self.seat_payload(seat=99999))
            self.assertEqual(self.error_code(unknown), 'resource_not_found')
            ragged = self.client.post(
                '/api/reservations/', self.seat_payload(start_time='11:10'))
            self.assertEqual(self.error_code(ragged), 'invalid_time')
            unknown_classmate = self.client.post('/api/reservations/', {
                'resource_type': 'room', 'room': self.room.pk, 'date': DAY,
                'start_time': '13:00', 'end_time': '14:00', 'participant_count': 2,
                'participant_student_ids': ['0000-0000'],
            })
            self.assertEqual(unknown_classmate.status_code, 400)

    def test_student_field_is_ignored_for_students(self):
        """A student cannot book in another student's name by sending `student`."""
        self.login_as(self.student)
        with frozen_time(at(hour=9)):
            response = self.client.post(
                '/api/reservations/', self.seat_payload(student=self.other_student.pk))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['student']['id'], self.student.pk)

    def test_librarian_books_for_a_student(self):
        self.login_as(self.librarian)
        with frozen_time(at(hour=9)):
            missing = self.client.post('/api/reservations/', self.seat_payload())
            self.assertEqual(missing.status_code, 400)
            response = self.client.post(
                '/api/reservations/', self.seat_payload(student=self.student.pk))
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['student']['id'], self.student.pk)
        self.assertTrue(response.data['booked_by_staff'])

    def test_students_only_see_their_own_reservations(self):
        with frozen_time(at(hour=9)):
            mine = self.book_seat()
            theirs = self.book_seat(student=self.other_student, seat=self.seat2)
            self.login_as(self.student)
            listing = self.client.get('/api/reservations/')
            self.assertEqual([r['id'] for r in listing.data['results']], [mine.pk])
            self.assertEqual(
                self.client.get(f'/api/reservations/{theirs.pk}/').status_code, 404)
            for action in ('cancel', 'check-in', 'check-out'):
                response = self.client.post(f'/api/reservations/{theirs.pk}/{action}/')
                self.assertEqual(response.status_code, 404, action)

            self.login_as(self.librarian)
            self.assertEqual(self.client.get('/api/reservations/').data['count'], 2)

    def test_cancel_check_in_and_check_out_over_http(self):
        with frozen_time(at(hour=9)):
            reservation = self.book_seat()
        self.login_as(self.student)
        url = f'/api/reservations/{reservation.pk}'
        with frozen_time(at(hour=11)):
            checked_in = self.client.post(f'{url}/check-in/')
            self.assertEqual(checked_in.data['status'], 'checked_in')
            self.assertTrue(checked_in.data['can_check_out'])
            still_running = self.client.post(f'{url}/cancel/')
            self.assertEqual(still_running.status_code, 400)
        with frozen_time(at(hour=11, minute=30)):
            checked_out = self.client.post(f'{url}/check-out/')
            self.assertEqual(checked_out.data['status'], 'completed')

    def test_staff_only_actions(self):
        with frozen_time(at(hour=9)):
            reservation = self.book_seat()
        with frozen_time(at(hour=11, minute=5)):
            self.login_as(self.student)
            self.assertEqual(
                self.client.post(f'/api/reservations/{reservation.pk}/no-show/').status_code, 403)
            self.assertEqual(
                self.client.get('/api/reservations/lookup/', {'code': reservation.code})
                .status_code, 403)

            self.login_as(self.librarian)
            found = self.client.get(
                '/api/reservations/lookup/', {'code': reservation.code.lower()})
            self.assertEqual(found.data['id'], reservation.pk)
            self.assertEqual(
                self.client.get('/api/reservations/lookup/', {'code': 'NOPE'}).status_code, 404)
            marked = self.client.post(f'/api/reservations/{reservation.pk}/no-show/')
            self.assertEqual(marked.data['status'], 'no_show')

    def test_list_filters(self):
        with frozen_time(at(hour=9)):
            seat_booking = self.book_seat()
            self.book_room(student=self.other_student, start_hour=14)
            services.cancel_reservation(seat_booking, actor=self.student)
            self.login_as(self.librarian)

            def count(**params):
                return self.client.get('/api/reservations/', params).data['count']

            self.assertEqual(count(scope='active'), 1)
            self.assertEqual(count(scope='history'), 1)
            self.assertEqual(count(status='cancelled'), 1)
            self.assertEqual(count(resource_type='room'), 1)
            self.assertEqual(count(search='olive'), 1)
            self.assertEqual(count(search='A01'), 1)
            self.assertEqual(count(date=DAY), 2)
            self.assertEqual(count(date='2026-03-03'), 0)


class AvailabilityApiTests(PortalTestCase):
    def seat_states(self, user, **params):
        self.login_as(user)
        query = {'date': DAY, 'start': '11:00', 'end': '12:00', **params}
        response = self.client.get('/api/seats/availability/', query)
        self.assertEqual(response.status_code, 200, response.data)
        seats = [seat for zone in response.data['zones'] for seat in zone['seats']]
        return response.data, {seat['number']: seat for seat in seats}

    def test_seat_states_follow_reservations(self):
        with frozen_time(at(hour=9)):
            data, seats = self.seat_states(self.student)
            self.assertTrue(data['bookable'])
            self.assertEqual(seats['A01']['state'], 'available')
            self.assertEqual(data['summary']['available'], 2)

            reservation = self.book_seat(student=self.other_student)
            _, seats = self.seat_states(self.student)
            self.assertEqual(seats['A01']['state'], 'reserved')
            self.assertEqual(seats['A02']['state'], 'available')
            _, seats = self.seat_states(self.other_student)
            self.assertEqual(seats['A01']['state'], 'mine')

            # A non-overlapping window is unaffected.
            _, seats = self.seat_states(self.student, start='12:00', end='13:00')
            self.assertEqual(seats['A01']['state'], 'available')

        with frozen_time(at(hour=11)):
            services.check_in(reservation, actor=self.other_student)
            _, seats = self.seat_states(self.student)
            self.assertEqual(seats['A01']['state'], 'occupied')

        with frozen_time(at(hour=11, minute=20)):
            services.check_out(reservation, actor=self.other_student)
            _, seats = self.seat_states(self.student)
            self.assertEqual(seats['A01']['state'], 'available')

    def test_students_cannot_see_who_booked_a_seat(self):
        with frozen_time(at(hour=9)):
            self.book_seat(student=self.other_student)
            _, seats = self.seat_states(self.student)
            block = seats['A01']['blocks'][0]
            self.assertNotIn('student_name', block)
            self.assertNotIn('reservation_id', block)

            _, seats = self.seat_states(self.librarian)
            block = seats['A01']['blocks'][0]
            self.assertEqual(block['student_name'], 'Olive Other')
            self.assertIn('reservation_id', block)

    def test_maintenance_seat_is_unavailable(self):
        self.seat.status = ResourceStatus.MAINTENANCE
        self.seat.save()
        with frozen_time(at(hour=9)):
            _, seats = self.seat_states(self.student)
        self.assertEqual(seats['A01']['state'], 'unavailable')

    def test_unbookable_window_is_flagged_with_a_reason(self):
        with frozen_time(at(hour=5)):
            data, _ = self.seat_states(self.student, start='06:00', end='07:00')
        self.assertFalse(data['bookable'])
        self.assertIn('open from', data['bookable_reason'])

    def test_availability_requires_a_valid_window(self):
        self.login_as(self.student)
        response = self.client.get('/api/seats/availability/', {'date': DAY})
        self.assertEqual(response.status_code, 400)

    def test_room_availability_and_schedule(self):
        with frozen_time(at(hour=9)):
            self.book_room(student=self.other_student, start_hour=13)
            self.login_as(self.student)
            response = self.client.get(
                '/api/study-rooms/availability/', {'date': DAY, 'start': '13:00', 'end': '14:00'})
            self.assertEqual(response.data['rooms'][0]['state'], 'reserved')
            schedule = self.client.get(
                f'/api/study-rooms/{self.room.pk}/schedule/', {'date': DAY})
        self.assertEqual(schedule.data['opens_at'], '08:00')
        self.assertEqual(
            [(b['start_time'], b['end_time']) for b in schedule.data['blocks']],
            [('13:00', '14:00')])
