"""What happens to a reservation after it is made."""
from datetime import timedelta

from rest_framework.exceptions import PermissionDenied

from config.exceptions import ApiError
from config.test_utils import MONDAY, PortalTestCase, at, frozen_time
from library.models import ReservationPolicy
from notifications.models import Notification
from reservations import services
from reservations.models import Reservation

Status = Reservation.Status


class CancellationTests(PortalTestCase):
    def test_student_can_cancel_before_the_start(self):
        with frozen_time(at(hour=9)):
            reservation = self.book_seat(start_hour=11)
        with frozen_time(at(hour=10, minute=59)):
            services.cancel_reservation(reservation, actor=self.student, reason='Sick')
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Status.CANCELLED)
        self.assertEqual(reservation.cancel_reason, 'Sick')
        self.assertEqual(reservation.cancelled_by, self.student)
        self.assertFalse(reservation.slots.exists())

    def test_student_cannot_cancel_after_the_start(self):
        with frozen_time(at(hour=9)):
            reservation = self.book_seat(start_hour=11)
        with frozen_time(at(hour=11, minute=5)), self.assertRaises(ApiError) as caught:
            services.cancel_reservation(reservation, actor=self.student)
        self.assertEqual(caught.exception.detail.code, 'cancel_window_closed')

    def test_cancellation_cutoff_is_configurable(self):
        ReservationPolicy.objects.update(cancellation_cutoff_minutes=60)
        with frozen_time(at(hour=9)):
            reservation = self.book_seat(start_hour=11)
        with frozen_time(at(hour=10, minute=30)), self.assertRaises(ApiError):
            services.cancel_reservation(reservation, actor=self.student)
        # Staff are not bound by the cutoff.
        with frozen_time(at(hour=10, minute=30)):
            services.cancel_reservation(reservation, actor=self.librarian, reason='Event')
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Status.CANCELLED)
        self.assertTrue(Notification.objects.filter(
            user=self.student, title='Your reservation was cancelled').exists())

    def test_student_cannot_cancel_someone_elses_reservation(self):
        with frozen_time(at(hour=9)):
            reservation = self.book_seat(start_hour=11)
            with self.assertRaises(PermissionDenied):
                services.cancel_reservation(reservation, actor=self.other_student)

    def test_a_finished_reservation_cannot_be_cancelled(self):
        with frozen_time(at(hour=9)):
            reservation = self.book_seat(start_hour=11)
            services.cancel_reservation(reservation, actor=self.student)
            with self.assertRaises(ApiError) as caught:
                services.cancel_reservation(reservation, actor=self.student)
        self.assertEqual(caught.exception.detail.code, 'invalid_status')


class CheckInTests(PortalTestCase):
    def setUp(self):
        super().setUp()
        with frozen_time(at(hour=9)):
            self.reservation = self.book_seat(start_hour=11, hours=2)

    def test_check_in_window(self):
        # Opens 10 minutes before the start.
        with frozen_time(at(hour=10, minute=45)), self.assertRaises(ApiError) as caught:
            services.check_in(self.reservation, actor=self.student)
        self.assertEqual(caught.exception.detail.code, 'too_early')

        with frozen_time(at(hour=10, minute=52)):
            reservation = services.check_in(self.reservation, actor=self.student)
        self.assertEqual(reservation.status, Status.CHECKED_IN)
        self.assertEqual(reservation.checked_in_by, self.student)
        self.assertTrue(reservation.slots.exists())  # still holds the seat

    def test_check_in_after_the_grace_period_releases_the_seat(self):
        with frozen_time(at(hour=11, minute=16)), self.assertRaises(ApiError) as caught:
            services.check_in(self.reservation, actor=self.student)
        self.assertEqual(caught.exception.detail.code, 'checkin_closed')
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, Status.NO_SHOW)
        self.assertFalse(self.reservation.slots.exists())

    def test_student_cannot_check_in_to_another_students_reservation(self):
        with frozen_time(at(hour=11)), self.assertRaises(PermissionDenied):
            services.check_in(self.reservation, actor=self.other_student)
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, Status.CONFIRMED)

    def test_librarian_can_confirm_a_check_in(self):
        with frozen_time(at(hour=11, minute=5)):
            reservation = services.check_in(self.reservation, actor=self.librarian)
        self.assertEqual(reservation.status, Status.CHECKED_IN)
        self.assertEqual(reservation.checked_in_by, self.librarian)

    def test_self_check_in_can_be_switched_off(self):
        ReservationPolicy.objects.update(allow_self_checkin=False)
        with frozen_time(at(hour=11)):
            with self.assertRaises(ApiError) as caught:
                services.check_in(self.reservation, actor=self.student)
            self.assertEqual(caught.exception.detail.code, 'self_checkin_disabled')
            services.check_in(self.reservation, actor=self.librarian)

    def test_early_check_out_completes_and_frees_the_remaining_time(self):
        with frozen_time(at(hour=11)):
            services.check_in(self.reservation, actor=self.student)
        with frozen_time(at(hour=11, minute=40)):
            reservation = services.check_out(self.reservation, actor=self.student)
            self.assertEqual(reservation.status, Status.COMPLETED)
            self.assertFalse(reservation.slots.exists())
            # The rest of the original window can be booked by someone else.
            again = self.book_seat(student=self.other_student, start_hour=12)
        self.assertEqual(again.status, Status.CONFIRMED)

    def test_check_out_requires_a_check_in(self):
        with frozen_time(at(hour=11)), self.assertRaises(ApiError):
            services.check_out(self.reservation, actor=self.student)

    def test_staff_can_mark_a_no_show_only_after_the_start(self):
        with frozen_time(at(hour=10, minute=30)), self.assertRaises(ApiError):
            services.mark_no_show(self.reservation, actor=self.librarian)
        with frozen_time(at(hour=11, minute=5)):
            reservation = services.mark_no_show(self.reservation, actor=self.librarian)
        self.assertEqual(reservation.status, Status.NO_SHOW)


class AutomaticLifecycleTests(PortalTestCase):
    def test_unattended_reservation_becomes_a_no_show_after_the_grace_period(self):
        with frozen_time(at(hour=9)):
            reservation = self.book_seat(start_hour=11)
        with frozen_time(at(hour=11, minute=14)):
            self.assertEqual(services.process_due_reservations()['no_shows'], 0)
        with frozen_time(at(hour=11, minute=15)):
            self.assertEqual(services.process_due_reservations()['no_shows'], 1)
            reservation.refresh_from_db()
            self.assertEqual(reservation.status, Status.NO_SHOW)
            self.assertFalse(reservation.slots.exists())
            self.assertTrue(Notification.objects.filter(
                user=self.student, title='Reservation marked as no-show').exists())
            # The released seat is immediately bookable for the slot in progress.
            self.book_seat(student=self.other_student, start_hour=11)

    def test_walk_in_grace_period_counts_from_the_booking_time(self):
        with frozen_time(at(hour=11, minute=20)):
            reservation = self.book_seat(start_hour=11)  # slot already in progress
        with frozen_time(at(hour=11, minute=30)):
            services.process_due_reservations()
            reservation.refresh_from_db()
            self.assertEqual(reservation.status, Status.CONFIRMED)
        with frozen_time(at(hour=11, minute=36)):
            services.process_due_reservations()
            reservation.refresh_from_db()
            self.assertEqual(reservation.status, Status.NO_SHOW)

    def test_checked_in_reservation_completes_at_its_end_time(self):
        with frozen_time(at(hour=9)):
            reservation = self.book_seat(start_hour=11)
        with frozen_time(at(hour=11)):
            services.check_in(reservation, actor=self.student)
        with frozen_time(at(hour=12, minute=1)):
            self.assertEqual(services.process_due_reservations()['completed'], 1)
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Status.COMPLETED)
        self.assertEqual(reservation.checked_out_at, reservation.end_at)
        self.assertFalse(reservation.slots.exists())

    def test_reminder_is_sent_once(self):
        with frozen_time(at(hour=9)):
            self.book_seat(start_hour=11)
        with frozen_time(at(hour=10, minute=50)):
            self.assertEqual(services.process_due_reservations()['reminders'], 1)
            self.assertEqual(services.process_due_reservations()['reminders'], 0)
        self.assertEqual(Notification.objects.filter(
            user=self.student, title='Your reservation starts soon').count(), 1)

    def test_sweep_runs_automatically_on_api_requests(self):
        with frozen_time(at(hour=9)):
            reservation = self.book_seat(start_hour=11)
        with frozen_time(at(hour=12)):
            self.login_as(self.librarian)
            self.client.get('/api/reservations/')
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Status.NO_SHOW)


class ScheduleChangeTests(PortalTestCase):
    def test_reservations_outside_new_hours_are_cancelled(self):
        with frozen_time(at(hour=9)):
            kept = self.book_seat(start_hour=11)
            displaced = self.book_seat(
                student=self.other_student, seat=self.seat2, start_hour=18, hours=2)
            self.login_as(self.admin)
            hours = self.client.get('/api/library/hours/').data
            for entry in hours:
                if entry['weekday'] == MONDAY.weekday():
                    entry['closes_at'] = '18:00'
            response = self.client.put('/api/library/hours/', hours)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['cancelled_reservations'], 1)
        kept.refresh_from_db()
        displaced.refresh_from_db()
        self.assertEqual(kept.status, Status.CONFIRMED)
        self.assertEqual(displaced.status, Status.CANCELLED)

    def test_adding_a_closure_cancels_that_days_reservations(self):
        tomorrow = MONDAY + timedelta(days=1)
        with frozen_time(at(hour=9)):
            reservation = self.book_seat(day=tomorrow)
            self.login_as(self.admin)
            response = self.client.post(
                '/api/library/closures/', {'date': tomorrow.isoformat(), 'reason': 'Holiday'})
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['cancelled_reservations'], 1)
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Status.CANCELLED)
