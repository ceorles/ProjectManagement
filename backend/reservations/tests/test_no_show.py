"""The 15-minute rule: confirmed reservations nobody checks in to are cancelled by the server."""
import threading
from datetime import timedelta
from unittest import mock

from django.test import override_settings
from django.utils import timezone

from config.exceptions import ApiError
from config.test_utils import MONDAY, PortalTestCase, at, frozen_time
from library.models import ReservationPolicy
from notifications.models import Notification
from reservations import scheduler, services
from reservations.models import Reservation, ReservationSlot
from reservations.windows import build_window

Status = Reservation.Status
TITLE = 'Reservation automatically cancelled'


class AutomaticNoShowTests(PortalTestCase):
    def confirmed(self, seats=None, student=None, purpose=''):
        """Requested the day before, approved by the librarian, 8:00 to 10:00."""
        day_before = at(MONDAY - timedelta(days=1), hour=10)
        with frozen_time(day_before):
            reservation = self.request_seats(
                seats or [self.seat], student, purpose=purpose, start_hour=8, hours=2)
            return services.approve_reservation(reservation, actor=self.librarian)

    def sweep(self, hour, minute, second=0):
        moment = at(hour=hour, minute=minute).replace(second=second)
        with frozen_time(moment):
            return services.process_due_reservations(moment)

    def test_not_cancelled_before_the_15_minutes_are_over(self):
        reservation = self.confirmed()
        self.assertEqual(self.sweep(8, 14, 59)['no_shows'], 0)
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Status.CONFIRMED)

    def test_cancelled_at_exactly_15_minutes_and_the_seat_is_free_again(self):
        reservation = self.confirmed()
        self.assertEqual(self.sweep(8, 15)['no_shows'], 1)
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Status.NO_SHOW)
        self.assertIn('Automatically cancelled', reservation.cancel_reason)
        self.assertFalse(reservation.slots.exists())
        # Available to another student for the remaining time.
        with frozen_time(at(hour=8, minute=20)):
            later = self.request_seats(
                [self.seat], self.other_student, start_hour=8, start_minute=30, hours=1)
        self.assertEqual(later.status, Status.PENDING)

    def test_the_student_is_told_why_exactly_once(self):
        self.confirmed()
        self.sweep(8, 15)
        self.sweep(8, 16)
        self.sweep(9, 0)
        notice = Notification.objects.get(user=self.student, title=TITLE)
        self.assertIn('did not check in within 15 minutes', notice.message)

    def test_the_deadline_does_not_depend_on_when_it_was_booked_or_approved(self):
        with frozen_time(at(hour=8, minute=5)):
            reservation = self.request_seats([self.seat], start_hour=8, hours=2)
        with frozen_time(at(hour=8, minute=12)):
            services.approve_reservation(reservation, actor=self.librarian)
        self.assertEqual(self.sweep(8, 14)['no_shows'], 0)
        self.assertEqual(self.sweep(8, 15)['no_shows'], 1)

    def test_a_student_who_checks_in_at_8_10_is_not_cancelled(self):
        reservation = self.confirmed()
        with frozen_time(at(hour=8, minute=10)):
            services.check_in(reservation, actor=self.student)
        self.assertEqual(self.sweep(8, 16)['no_shows'], 0)
        self.sweep(9, 0)
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Status.CHECKED_IN)
        self.assertTrue(reservation.slots.exists())
        self.assertFalse(Notification.objects.filter(user=self.student, title=TITLE).exists())

    def test_checking_in_after_the_cancellation_is_refused(self):
        reservation = self.confirmed()
        self.sweep(8, 15)
        for actor in (self.student, self.librarian):
            with frozen_time(at(hour=8, minute=16)), self.assertRaises(ApiError) as caught:
                services.check_in(reservation, actor=actor)
            self.assertEqual(caught.exception.detail.code, 'invalid_status')
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Status.NO_SHOW)

    def test_checking_in_late_before_the_sweep_ran_is_also_refused(self):
        reservation = self.confirmed()
        with frozen_time(at(hour=8, minute=15)), self.assertRaises(ApiError) as caught:
            services.check_in(reservation, actor=self.student)
        self.assertEqual(caught.exception.detail.code, 'checkin_closed')
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Status.NO_SHOW)

    def test_a_pending_request_is_not_a_no_show(self):
        with frozen_time(at(MONDAY - timedelta(days=1), hour=10)):
            reservation = self.request_seats([self.seat], start_hour=8, hours=2)
        result = self.sweep(8, 15)
        self.assertEqual((result['no_shows'], result['expired']), (0, 1))
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Status.CANCELLED)  # expired, no strike
        self.assertFalse(Notification.objects.filter(user=self.student, title=TITLE).exists())

    def test_a_manually_cancelled_reservation_stays_cancelled(self):
        reservation = self.confirmed()
        with frozen_time(at(hour=7)):
            services.cancel_reservation(reservation, actor=self.student, reason='Sick')
        self.assertEqual(self.sweep(8, 20)['no_shows'], 0)
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Status.CANCELLED)
        self.assertEqual(reservation.cancel_reason, 'Sick')

    def test_a_completed_reservation_is_left_alone(self):
        reservation = self.confirmed()
        with frozen_time(at(hour=8, minute=5)):
            services.check_in(reservation, actor=self.student)
        with frozen_time(at(hour=8, minute=10)):
            services.check_out(reservation, actor=self.student)
        self.assertEqual(self.sweep(8, 20)['no_shows'], 0)
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Status.COMPLETED)

    def test_a_group_reservation_releases_every_seat(self):
        reservation = self.confirmed(self.table, purpose='Thesis group')
        self.assertEqual(ReservationSlot.objects.filter(reservation=reservation).count(), 24)
        self.assertEqual(self.sweep(8, 15)['no_shows'], 1)
        self.assertFalse(ReservationSlot.objects.exists())
        self.assertEqual(Notification.objects.filter(user=self.student, title=TITLE).count(), 1)
        with frozen_time(at(hour=8, minute=20)):
            self.request_seats(self.table[:2], self.other_student, start_hour=8, start_minute=30)

    def test_a_computer_follows_the_same_rule(self):
        reservation = self.confirmed([self.computer])
        self.sweep(8, 15)
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Status.NO_SHOW)
        self.assertFalse(reservation.slots.exists())

    def test_the_grace_period_cannot_be_changed(self):
        self.login_as(self.admin)
        response = self.client.patch('/api/library/policy/', {'checkin_grace_minutes': 60})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['checkin_grace_minutes'], 15)
        self.assertEqual(ReservationPolicy.load().checkin_grace_minutes, 15)

    def test_the_library_time_zone_is_used(self):
        reservation = self.confirmed()
        self.assertEqual(reservation.start_at.astimezone(timezone.get_default_timezone()).hour, 8)
        self.assertEqual(timezone.get_default_timezone_name(), 'Asia/Manila')
        # 8:00 in Manila is 00:00 UTC.
        self.assertEqual(reservation.start_at.astimezone(timezone.UTC).hour, 0)

    def test_a_slot_whose_check_in_period_is_over_cannot_be_booked(self):
        with frozen_time(at(hour=11, minute=14)):
            self.request_seats([self.seat], start_hour=11)      # still possible
        with frozen_time(at(hour=11, minute=15)), self.assertRaises(ApiError) as caught:
            self.request_seats([self.seat2], self.other_student, start_hour=11)
        self.assertEqual(caught.exception.detail.code, 'in_the_past')


class SchedulerTests(PortalTestCase):
    def overdue(self):
        with frozen_time(at(MONDAY - timedelta(days=1), hour=10)):
            reservation = self.request_seats([self.seat], start_hour=8, hours=2)
            return services.approve_reservation(reservation, actor=self.librarian)

    def test_a_pass_works_without_any_web_request(self):
        reservation = self.overdue()
        with frozen_time(at(hour=8, minute=16)):
            self.assertEqual(scheduler.run_once()['no_shows'], 1)
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Status.NO_SHOW)

    def test_the_loop_repeats_until_stopped_and_processes_once(self):
        reservation = self.overdue()
        stop = threading.Event()
        passes = []

        def counted():
            with frozen_time(at(hour=8, minute=16)):
                passes.append(services.process_due_reservations())
            if len(passes) == 3:
                stop.set()

        with mock.patch('reservations.scheduler.run_once', counted):
            scheduler.run_forever(interval=0.01, stop=stop)
        self.assertEqual([item['no_shows'] for item in passes], [1, 0, 0])
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Status.NO_SHOW)
        self.assertEqual(Notification.objects.filter(user=self.student, title=TITLE).count(), 1)

    def test_a_failed_pass_is_survived(self):
        with mock.patch('reservations.services.process_due_reservations',
                        side_effect=RuntimeError('database is locked')), \
                self.assertLogs('reservations.scheduler', level='ERROR'):
            self.assertIsNone(scheduler.run_once())
        self.assertEqual(scheduler.scheduler_status()['last_error'], 'database is locked')

    @override_settings(RESERVATION_SCHEDULER_ENABLED=False)
    def test_it_can_be_switched_off(self):
        self.assertFalse(scheduler.start_background_scheduler())


class RoomsAreNotReservableTests(PortalTestCase):
    def test_the_room_api_is_gone(self):
        for user in (self.student, self.librarian, self.admin):
            self.login_as(user)
            for url in ('/api/study-rooms/', f'/api/study-rooms/{self.room.pk}/',
                        '/api/study-rooms/availability/', '/api/study-rooms/facilities/'):
                self.assertEqual(self.client.get(url).status_code, 404, url)

    def test_a_room_cannot_be_reserved_through_the_api(self):
        for user, extra in ((self.student, {}), (self.librarian, {'student': self.student.pk})):
            self.login_as(user)
            with frozen_time(at(hour=9)):
                response = self.client.post('/api/reservations/', {
                    'resource_type': 'room', 'room': self.room.pk, 'date': MONDAY.isoformat(),
                    'start_time': '11:00', 'end_time': '12:00', **extra,
                })
            self.assertEqual(response.status_code, 400, response.data)
        self.assertFalse(Reservation.objects.exists())

    def test_the_service_refuses_a_room_as_well(self):
        window = build_window(MONDAY, at(hour=11).time(), at(hour=12).time())
        with frozen_time(at(hour=9)), self.assertRaises(ApiError) as caught:
            services.create_reservation(
                actor=self.student, student=self.student, resource_type='room',
                resource_id=self.room.pk, window=window)
        self.assertEqual(caught.exception.detail.code, 'room_not_reservable')

    def test_past_room_reservations_can_still_be_read(self):
        past = Reservation.objects.create(
            code='ROOMHIST', student=self.student, resource_type='room', room=self.room,
            start_at=at(hour=9), end_at=at(hour=10), status=Status.COMPLETED)
        self.login_as(self.student)
        response = self.client.get(f'/api/reservations/{past.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['resource']['name'], 'Study Room 1')
        self.assertEqual(self.client.get('/api/reservations/').data['count'], 1)
