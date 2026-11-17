"""Librarian approval, group/table requests, computers, and the Student Assistant role."""
from rest_framework.exceptions import PermissionDenied

from config.exceptions import ApiError, ConflictError
from config.test_utils import MONDAY, PASSWORD, PortalTestCase, at, frozen_time
from notifications.models import Notification
from reservations import services
from reservations.models import Reservation, ReservationSlot
from users.models import User

Status = Reservation.Status
DAY = MONDAY.isoformat()


def titles(user):
    return list(Notification.objects.filter(user=user).values_list('title', flat=True))


class ApprovalWorkflowTests(PortalTestCase):
    def test_student_request_is_pending_never_confirmed(self):
        with frozen_time(at(hour=9)):
            reservation = self.request_seats([self.seat])
        self.assertEqual(reservation.status, Status.PENDING)
        self.assertIsNone(reservation.decided_by)
        self.assertIn('Reservation request sent', titles(self.student))
        self.assertNotIn('Reservation confirmed', titles(self.student))

    def test_librarians_and_admins_are_notified_of_a_new_request(self):
        second_librarian = User.objects.create_user(
            email='lib2@test.edu', password=PASSWORD, first_name='Lee', last_name='Two',
            role=User.Role.LIBRARIAN)
        inactive = User.objects.create_user(
            email='gone@test.edu', password=PASSWORD, first_name='Gone', last_name='Away',
            role=User.Role.LIBRARIAN, is_active=False)
        with frozen_time(at(hour=9)):
            reservation = self.request_seats([self.seat])
        for reviewer in (self.librarian, second_librarian, self.admin):
            notice = Notification.objects.get(user=reviewer, title='New reservation request')
            self.assertIn('Sam Student', notice.message)
            self.assertEqual(notice.link, f'/reservations/{reservation.pk}')
            self.assertFalse(notice.is_read)
        # Not the people who cannot decide.
        for other in (self.assistant, self.other_student, inactive):
            self.assertNotIn('New reservation request', titles(other))

    def test_librarian_approves_and_the_student_is_told(self):
        with frozen_time(at(hour=9)):
            reservation = self.request_seats([self.seat])
            approved = services.approve_reservation(reservation, actor=self.librarian)
        self.assertEqual(approved.status, Status.CONFIRMED)
        self.assertEqual(approved.decided_by, self.librarian)
        self.assertIsNotNone(approved.decided_at)
        self.assertTrue(approved.slots.exists())  # still holds the seat
        self.assertIn('Reservation approved', titles(self.student))

    def test_librarian_rejects_the_seat_is_released_and_the_student_is_told(self):
        with frozen_time(at(hour=9)):
            reservation = self.request_seats([self.seat])
            rejected = services.reject_reservation(
                reservation, actor=self.librarian, reason='Reserved for a class')
            self.assertEqual(rejected.status, Status.REJECTED)
            self.assertEqual(rejected.decision_note, 'Reserved for a class')
            self.assertFalse(rejected.slots.exists())
            notice = Notification.objects.get(
                user=self.student, title='Reservation request rejected')
            self.assertIn('Reserved for a class', notice.message)
            # Someone else can now request the same seat and time.
            self.request_seats([self.seat], student=self.other_student)

    def test_a_pending_request_holds_the_seat(self):
        """Two students cannot both be waiting on the same seat."""
        with frozen_time(at(hour=9)):
            self.request_seats([self.seat])
            with self.assertRaises(ConflictError) as caught:
                self.request_seats([self.seat], student=self.other_student)
        self.assertEqual(caught.exception.detail.code, 'slot_taken')

    def test_only_librarians_and_admins_can_decide(self):
        with frozen_time(at(hour=9)):
            reservation = self.request_seats([self.seat])
            for actor in (self.student, self.other_student, self.assistant):
                with self.assertRaises(PermissionDenied):
                    services.approve_reservation(reservation, actor=actor)
                with self.assertRaises(PermissionDenied):
                    services.reject_reservation(reservation, actor=actor)
            reservation.refresh_from_db()
            self.assertEqual(reservation.status, Status.PENDING)
            services.approve_reservation(reservation, actor=self.admin)

    def test_a_decision_cannot_be_made_twice(self):
        with frozen_time(at(hour=9)):
            reservation = self.request_seats([self.seat])
            services.reject_reservation(reservation, actor=self.librarian)
            for decide in (services.approve_reservation, services.reject_reservation):
                with self.assertRaises(ApiError) as caught:
                    decide(reservation, actor=self.librarian)
                self.assertEqual(caught.exception.detail.code, 'invalid_status')

    def test_pending_request_cannot_be_checked_in(self):
        with frozen_time(at(hour=9)):
            reservation = self.request_seats([self.seat])
        with frozen_time(at(hour=11)):
            for actor in (self.student, self.librarian):
                with self.assertRaises(ApiError) as caught:
                    services.check_in(reservation, actor=actor)
                self.assertEqual(caught.exception.detail.code, 'not_approved')

    def test_student_can_withdraw_a_pending_request(self):
        with frozen_time(at(hour=9)):
            reservation = self.request_seats([self.seat])
            services.cancel_reservation(reservation, actor=self.student)
            reservation.refresh_from_db()
            self.assertEqual(reservation.status, Status.CANCELLED)
            self.assertFalse(reservation.slots.exists())

    def test_unreviewed_request_expires_without_a_strike(self):
        with frozen_time(at(hour=9)):
            reservation = self.request_seats([self.seat])
        with frozen_time(at(hour=11, minute=20)):
            self.assertEqual(services.process_due_reservations()['expired'], 1)
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Status.CANCELLED)
        self.assertFalse(reservation.slots.exists())
        self.assertIn('Reservation request expired', titles(self.student))
        self.assertEqual(
            Reservation.objects.filter(student=self.student, status=Status.NO_SHOW).count(), 0)

    def test_grace_period_counts_from_a_late_approval(self):
        with frozen_time(at(hour=9)):
            reservation = self.request_seats([self.seat], hours=2)
        with frozen_time(at(hour=11, minute=10)):
            services.approve_reservation(reservation, actor=self.librarian)
        with frozen_time(at(hour=11, minute=20)):
            services.process_due_reservations()
            reservation.refresh_from_db()
            self.assertEqual(reservation.status, Status.CONFIRMED)  # still inside the grace period
            services.check_in(reservation, actor=self.student)

    def test_booking_entered_by_a_librarian_is_confirmed_at_once(self):
        with frozen_time(at(hour=9)):
            reservation = services.create_reservation(
                actor=self.librarian, student=self.student, resource_type='seat',
                seat_ids=[self.seat.pk], window=self.window())
        self.assertEqual(reservation.status, Status.CONFIRMED)
        self.assertEqual(reservation.decided_by, self.librarian)
        self.assertIn('Reservation confirmed', titles(self.student))

    def test_pending_requests_count_towards_the_active_limit(self):
        with frozen_time(at(hour=9)):
            self.request_seats([self.seat], start_hour=11)
            self.request_seats([self.seat], start_hour=13)
            with self.assertRaises(ApiError) as caught:
                self.request_seats([self.seat], start_hour=15)
        self.assertEqual(caught.exception.detail.code, 'daily_limit')


class ApprovalApiTests(PortalTestCase):
    def setUp(self):
        super().setUp()
        with frozen_time(at(hour=9)):
            self.reservation = self.request_seats([self.seat])
        self.url = f'/api/reservations/{self.reservation.pk}'

    def test_full_scenario_over_http(self):
        with frozen_time(at(hour=9)):
            # The librarian sees the notification and the pending request...
            self.login_as(self.librarian)
            self.assertEqual(self.client.get('/api/notifications/unread-count/').data['unread'], 1)
            notice = self.client.get('/api/notifications/').data['results'][0]
            self.assertEqual(notice['title'], 'New reservation request')
            self.assertEqual(notice['link'], f'/reservations/{self.reservation.pk}')
            dashboard = self.client.get('/api/reports/staff-dashboard/').data
            self.assertEqual(dashboard['pending_count'], 1)
            detail = self.client.get(f'{self.url}/').data
            self.assertEqual(detail['status'], 'pending')
            self.assertEqual(detail['student']['full_name'], 'Sam Student')
            self.assertEqual(detail['student']['student_id'], '2024-0001')
            self.assertTrue(detail['can_approve'])
            # ...and approves it.
            approved = self.client.post(f'{self.url}/approve/')
            self.assertEqual(approved.status_code, 200, approved.data)
            self.assertEqual(approved.data['status'], 'confirmed')
            self.assertEqual(approved.data['decided_by_name'], 'Lia Brarian')
            self.assertEqual(
                self.client.get('/api/reports/staff-dashboard/').data['pending_count'], 0)

            # The student is told, and the seat is taken for everyone else.
            self.login_as(self.student)
            self.assertEqual(
                self.client.get('/api/notifications/').data['results'][0]['title'],
                'Reservation approved')
            self.login_as(self.other_student)
            clash = self.client.post('/api/reservations/', self.seat_payload())
            self.assertEqual(clash.status_code, 409)

    def test_reject_over_http_frees_the_seat(self):
        with frozen_time(at(hour=9)):
            self.login_as(self.librarian)
            rejected = self.client.post(f'{self.url}/reject/', {'reason': 'Maintenance planned'})
            self.assertEqual(rejected.data['status'], 'rejected')
            self.assertEqual(rejected.data['decision_note'], 'Maintenance planned')
            self.login_as(self.other_student)
            again = self.client.post('/api/reservations/', self.seat_payload())
            self.assertEqual(again.status_code, 201)
            self.assertEqual(again.data['status'], 'pending')

    def test_students_and_assistants_cannot_approve_or_reject(self):
        with frozen_time(at(hour=9)):
            for user, expected in ((self.student, 403), (self.other_student, 403),
                                   (self.assistant, 403)):
                self.login_as(user)
                for action in ('approve', 'reject'):
                    response = self.client.post(f'{self.url}/{action}/')
                    self.assertEqual(response.status_code, expected, (user.role, action))
            self.reservation.refresh_from_db()
            self.assertEqual(self.reservation.status, Status.PENDING)
            self.login_as(self.student)
            self.assertFalse(self.client.get(f'{self.url}/').data['can_approve'])

    def test_admin_can_also_decide(self):
        with frozen_time(at(hour=9)):
            self.login_as(self.admin)
            self.assertEqual(self.client.post(f'{self.url}/approve/').data['status'], 'confirmed')


class GroupAndTableTests(PortalTestCase):
    def test_reason_is_required_only_above_two_seats(self):
        with frozen_time(at(hour=9)):
            self.assertEqual(self.request_seats(self.table[:1], start_hour=9).participant_count, 1)
        with frozen_time(at(hour=9)):
            two = self.request_seats(self.table[2:4], student=self.other_student, start_hour=9)
            self.assertEqual(two.participant_count, 2)
            for count in (3, 4, 5, 6):
                with self.assertRaises(ApiError) as caught:
                    self.request_seats(self.table[:count], start_hour=13)
                self.assertEqual(caught.exception.detail.code, 'reason_required', count)
                with self.assertRaises(ApiError):
                    self.request_seats(self.table[:count], purpose='   ', start_hour=13)

    def test_whole_table_request(self):
        with frozen_time(at(hour=9)):
            reservation = self.request_seats(self.table, purpose='Thesis group meeting')
        self.assertEqual(reservation.status, Status.PENDING)
        self.assertEqual(reservation.participant_count, 6)
        self.assertEqual(reservation.resource_label, 'Table 1 (6 seats)')
        self.assertEqual(reservation.reservation_seats.count(), 6)
        # One slot row per seat per half hour: 6 seats x 2 slots.
        self.assertEqual(ReservationSlot.objects.filter(reservation=reservation).count(), 12)
        notice = Notification.objects.get(user=self.librarian, title='New reservation request')
        self.assertIn('Table 1 (6 seats)', notice.message)

    def test_partial_group_is_described_by_its_seats(self):
        with frozen_time(at(hour=9)):
            reservation = self.request_seats(self.table[:3], purpose='Review session')
        self.assertEqual(reservation.resource_label, 'Seats T01-1, T01-2, T01-3')

    def test_every_seat_of_a_request_is_blocked_for_others(self):
        with frozen_time(at(hour=9)):
            self.request_seats(self.table, purpose='Group study')
            for seat in (self.table[0], self.table[5]):
                with self.assertRaises(ConflictError) as caught:
                    self.request_seats([seat], student=self.other_student)
                self.assertEqual(caught.exception.detail.code, 'slot_taken')

    def test_a_table_cannot_be_requested_if_one_chair_is_taken(self):
        with frozen_time(at(hour=9)):
            self.request_seats([self.table[2]], student=self.other_student)
            with self.assertRaises(ConflictError) as caught:
                self.request_seats(self.table, purpose='Group study')
        self.assertIn('T01-3', str(caught.exception.detail))
        self.assertEqual(Reservation.objects.filter(student=self.student).count(), 0)

    def test_rejecting_a_table_request_frees_all_six_chairs(self):
        with frozen_time(at(hour=9)):
            reservation = self.request_seats(self.table, purpose='Group study')
            services.reject_reservation(reservation, actor=self.librarian)
            self.assertFalse(ReservationSlot.objects.exists())
            self.request_seats(self.table[3:5], student=self.other_student)

    def test_request_is_limited_to_six_seats_in_one_area(self):
        with frozen_time(at(hour=9)):
            with self.assertRaises(ApiError) as caught:
                self.request_seats(self.table + [self.seat], purpose='Big group')
            self.assertEqual(caught.exception.detail.code, 'too_many_seats')
            with self.assertRaises(ApiError) as caught:
                self.request_seats([self.table[0], self.seat])
            self.assertEqual(caught.exception.detail.code, 'mixed_areas')

    def test_group_request_over_http_shows_the_reason_to_the_librarian(self):
        self.login_as(self.student)
        payload = {
            'resource_type': 'seat', 'seats': [seat.pk for seat in self.table], 'date': DAY,
            'start_time': '13:00', 'end_time': '15:00',
        }
        with frozen_time(at(hour=9)):
            missing = self.client.post('/api/reservations/', payload)
            self.assertEqual(missing.status_code, 400)
            self.assertEqual(self.error_code(missing), 'reason_required')
            created = self.client.post(
                '/api/reservations/', {**payload, 'purpose': 'Capstone defence practice'})
            self.assertEqual(created.status_code, 201, created.data)
            self.assertEqual(created.data['status'], 'pending')
            self.assertEqual(created.data['resource']['name'], 'Table 1 (6 seats)')
            self.assertEqual(len(created.data['seats']), 6)

            self.login_as(self.librarian)
            detail = self.client.get(f'/api/reservations/{created.data["id"]}/').data
            self.assertEqual(detail['purpose'], 'Capstone defence practice')
            self.assertEqual(detail['participant_count'], 6)
            self.assertIsNotNone(detail['created_at'])

            # The map shows all six chairs as taken.
            self.login_as(self.other_student)
            seats = [
                seat for zone in self.client.get(
                    '/api/seats/availability/', {'date': DAY, 'start': '13:00', 'end': '14:00'}
                ).data['zones'] for seat in zone['seats'] if seat['table_number'] == 1
            ]
            self.assertEqual({seat['state'] for seat in seats}, {'reserved'})
            self.assertEqual(len(seats), 6)


class ComputerTests(PortalTestCase):
    def test_one_computer_can_be_requested(self):
        with frozen_time(at(hour=9)):
            reservation = self.request_seats([self.computer])
        self.assertEqual(reservation.resource_label, 'Computer PC-1')
        self.assertEqual(reservation.status, Status.PENDING)

    def test_two_computers_in_one_request_are_refused(self):
        with frozen_time(at(hour=9)):
            for seats in ([self.computer, self.computer2], [self.computer, self.table[0]]):
                with self.assertRaises(ApiError) as caught:
                    self.request_seats(seats)
                self.assertEqual(caught.exception.detail.code, 'one_computer_only')

    def test_a_student_cannot_hold_two_computers_at_the_same_time(self):
        with frozen_time(at(hour=9)):
            self.request_seats([self.computer])
            with self.assertRaises(ConflictError) as caught:
                self.request_seats([self.computer2])
        self.assertEqual(caught.exception.detail.code, 'student_conflict')

    def test_a_computer_cannot_be_double_booked(self):
        with frozen_time(at(hour=9)):
            self.request_seats([self.computer], hours=2)
            with self.assertRaises(ConflictError):
                self.request_seats([self.computer], student=self.other_student, start_hour=12)
            # Straight after is fine.
            self.request_seats([self.computer], student=self.other_student, start_hour=13)


class StudentAssistantTests(PortalTestCase):
    def test_public_registration_cannot_create_an_assistant(self):
        response = self.client.post('/api/auth/register/', {
            'email': 'sneak@test.edu', 'first_name': 'Sne', 'last_name': 'Aky',
            'student_id': '2025-0900', 'password': PASSWORD, 'confirm_password': PASSWORD,
            'role': 'assistant',
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(User.objects.get(email='sneak@test.edu').role, User.Role.STUDENT)

    def test_admin_creates_an_assistant_account(self):
        self.login_as(self.admin)
        response = self.client.post('/api/users/', {
            'email': 'helper@test.edu', 'first_name': 'Hel', 'last_name': 'Per',
            'role': 'assistant', 'student_id': '2023-0777', 'password': PASSWORD,
        })
        self.assertEqual(response.status_code, 201, response.data)
        helper = User.objects.get(email='helper@test.edu')
        self.assertEqual(helper.role, User.Role.ASSISTANT)
        self.assertEqual(helper.student_id, '2023-0777')
        self.assertFalse(helper.can_manage_resources)
        self.login_as(self.librarian)
        self.assertEqual(self.client.post('/api/users/', {}).status_code, 403)

    def test_assistant_can_sign_in_and_see_operations(self):
        login = self.client.post(
            '/api/auth/login/', {'email': 'assistant@test.edu', 'password': PASSWORD})
        self.assertEqual(login.data['user']['role'], 'assistant')
        with frozen_time(at(hour=9)):
            reservation = self.book_seat()
            self.login_as(self.assistant)
            self.assertEqual(self.client.get('/api/reports/staff-dashboard/').status_code, 200)
            listing = self.client.get('/api/reservations/')
            self.assertEqual(listing.data['count'], 1)
            self.assertEqual(listing.data['results'][0]['student']['student_id'], '2024-0001')
            found = self.client.get('/api/reservations/lookup/', {'code': reservation.code})
            self.assertEqual(found.status_code, 200)
            zones = self.client.get(
                '/api/seats/availability/', {'date': DAY, 'start': '11:00', 'end': '12:00'}
            ).data['zones']
            seat = next(s for zone in zones for s in zone['seats'] if s['number'] == 'A01')
            self.assertEqual(seat['blocks'][0]['student_name'], 'Sam Student')
            self.assertEqual(self.client.get('/api/users/students/').status_code, 200)

    def test_assistant_helps_with_check_in_and_check_out(self):
        with frozen_time(at(hour=9)):
            reservation = self.book_seat()
        with frozen_time(at(hour=11)):
            self.login_as(self.assistant)
            checked_in = self.client.post(f'/api/reservations/{reservation.pk}/check-in/')
            self.assertEqual(checked_in.data['status'], 'checked_in')
            checked_out = self.client.post(f'/api/reservations/{reservation.pk}/check-out/')
            self.assertEqual(checked_out.data['status'], 'completed')

    def test_assistant_cannot_decide_cancel_book_or_administer(self):
        with frozen_time(at(hour=9)):
            pending = self.request_seats([self.seat])
            confirmed = self.book_seat(student=self.other_student, seat=self.seat2)
        with frozen_time(at(hour=11, minute=5)):
            self.login_as(self.assistant)
            refused = {
                f'/api/reservations/{pending.pk}/approve/': {},
                f'/api/reservations/{pending.pk}/reject/': {},
                f'/api/reservations/{pending.pk}/cancel/': {},
                f'/api/reservations/{confirmed.pk}/no-show/': {},
                '/api/reservations/': self.seat_payload(
                    seat=self.table[0].pk, student=self.student.pk, start_time='15:00',
                    end_time='16:00'),
                '/api/users/': {'email': 'x@test.edu', 'role': 'librarian'},
                '/api/seats/': {'number': 'Z1', 'zone': self.zone.pk, 'row': 2, 'col': 1},
                f'/api/seats/{self.seat.pk}/set-status/': {'status': 'maintenance'},
                '/api/library/closures/': {'date': '2026-03-20', 'reason': 'x'},
            }
            for url, body in refused.items():
                self.assertEqual(self.client.post(url, body).status_code, 403, url)
            for url in ('/api/users/', '/api/activity/', '/api/reports/admin-dashboard/',
                        '/api/reports/usage/'):
                self.assertEqual(self.client.get(url).status_code, 403, url)
            self.assertEqual(
                self.client.patch('/api/library/policy/', {'max_advance_days': 9}).status_code, 403)
            detail = self.client.get(f'/api/reservations/{pending.pk}/').data
            self.assertFalse(detail['can_approve'])
            self.assertFalse(detail['can_cancel'])
        pending.refresh_from_db()
        self.assertEqual(pending.status, Status.PENDING)
