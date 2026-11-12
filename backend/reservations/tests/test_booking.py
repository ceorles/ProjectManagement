"""Creating reservations: the booking rules and double-booking protection."""
from datetime import time, timedelta

from django.db import IntegrityError, transaction
from rest_framework.exceptions import PermissionDenied

from config.exceptions import ApiError, ConflictError
from config.test_utils import MONDAY, PortalTestCase, at, frozen_time
from library.models import Closure, OperatingHours, ReservationPolicy, ResourceStatus
from notifications.models import Notification
from reservations import services
from reservations.models import Reservation, ReservationSlot
from reservations.windows import build_window

Status = Reservation.Status


class BookingRuleTests(PortalTestCase):
    def assertRejected(self, code, **window_kwargs):
        with self.assertRaises(ApiError) as caught:
            self.book_seat(**window_kwargs)
        self.assertEqual(caught.exception.detail.code, code)

    def test_successful_booking_claims_one_slot_per_half_hour(self):
        with frozen_time(at(hour=9)):
            reservation = self.book_seat(start_hour=11, hours=2)
        self.assertEqual(reservation.status, Status.CONFIRMED)
        self.assertEqual(len(reservation.code), 8)
        self.assertEqual(reservation.slots.count(), 4)
        self.assertTrue(
            Notification.objects.filter(user=self.student, title='Reservation confirmed').exists())

    def test_past_times_are_rejected(self):
        with frozen_time(at(hour=12)):
            self.assertRejected('in_the_past', start_hour=9)
            self.assertRejected('in_the_past', day=MONDAY - timedelta(days=1))

    def test_slot_in_progress_can_still_be_booked(self):
        with frozen_time(at(hour=11, minute=10)):
            reservation = self.book_seat(start_hour=11)
        self.assertEqual(reservation.status, Status.CONFIRMED)

    def test_advance_booking_limit(self):
        with frozen_time(at(hour=9)):
            self.assertRejected('too_far_ahead', day=MONDAY + timedelta(days=8))
            self.book_seat(day=MONDAY + timedelta(days=7))  # exactly at the limit

    def test_duration_limits(self):
        ReservationPolicy.objects.update(max_seat_duration_minutes=120, min_duration_minutes=60)
        with frozen_time(at(hour=9)):
            self.assertRejected('too_long', hours=3)
            with self.assertRaises(ApiError) as caught:
                services.create_reservation(
                    actor=self.student, student=self.student, resource_type='seat',
                    resource_id=self.seat.pk,
                    window=build_window(MONDAY, time(11, 0), time(11, 30)))
            self.assertEqual(caught.exception.detail.code, 'too_short')

    def test_times_must_sit_on_slot_boundaries(self):
        with self.assertRaises(ApiError) as caught:
            build_window(MONDAY, time(11, 15), time(12, 0))
        self.assertEqual(caught.exception.detail.code, 'invalid_time')
        with self.assertRaises(ApiError):
            build_window(MONDAY, time(12, 0), time(11, 0))

    def test_operating_hours_are_enforced(self):
        with frozen_time(at(hour=7)):
            self.assertRejected('outside_hours', start_hour=7)
            self.assertRejected('outside_hours', start_hour=19, hours=2)
            self.book_seat(start_hour=19, hours=1)  # ends exactly at closing time

    def test_closed_weekday_and_closure_dates_are_rejected(self):
        sunday = MONDAY + timedelta(days=6)
        self.assertFalse(OperatingHours.objects.get(weekday=6).is_open)
        Closure.objects.create(date=MONDAY + timedelta(days=1), reason='Foundation Day')
        with frozen_time(at(hour=9)):
            self.assertRejected('library_closed', day=sunday)
            self.assertRejected('library_closed', day=MONDAY + timedelta(days=1))

    def test_unavailable_seat_cannot_be_booked(self):
        self.seat.status = ResourceStatus.MAINTENANCE
        self.seat.save()
        with frozen_time(at(hour=9)):
            self.assertRejected('resource_unavailable')

    def test_active_reservation_limit(self):
        ReservationPolicy.objects.update(max_active_reservations=2, max_reservations_per_day=5)
        with frozen_time(at(hour=9)):
            self.book_seat(start_hour=11)
            self.book_seat(start_hour=13)
            self.assertRejected('active_limit', start_hour=15)

    def test_daily_reservation_limit(self):
        with frozen_time(at(hour=9)):
            self.book_seat(start_hour=11)
            self.book_seat(start_hour=13)
            self.assertRejected('daily_limit', start_hour=15)
            # A different day is still allowed.
            self.book_seat(day=MONDAY + timedelta(days=1))

    def test_cancelled_reservations_do_not_count_towards_the_daily_limit(self):
        with frozen_time(at(hour=9)):
            first = self.book_seat(start_hour=11)
            self.book_seat(start_hour=13)
            services.cancel_reservation(first, actor=self.student)
            self.book_seat(start_hour=15)

    def test_repeated_no_shows_suspend_booking(self):
        ReservationPolicy.objects.update(no_show_limit=2, max_reservations_per_day=5)
        with frozen_time(at(hour=8)):
            self.book_seat(start_hour=9)
            self.book_seat(start_hour=11)
        with frozen_time(at(hour=13)):
            services.process_due_reservations()
            self.assertEqual(
                Reservation.objects.filter(student=self.student, status=Status.NO_SHOW).count(), 2)
            self.assertRejected('booking_suspended', start_hour=15)

    def test_student_cannot_book_for_someone_else(self):
        with frozen_time(at(hour=9)), self.assertRaises(PermissionDenied):
            services.create_reservation(
                actor=self.student, student=self.other_student, resource_type='seat',
                resource_id=self.seat.pk, window=self.window())

    def test_staff_can_book_on_behalf_of_a_student(self):
        with frozen_time(at(hour=9)):
            reservation = services.create_reservation(
                actor=self.librarian, student=self.student, resource_type='seat',
                resource_id=self.seat.pk, window=self.window())
        self.assertEqual(reservation.student, self.student)
        self.assertEqual(reservation.created_by, self.librarian)

    def test_reservations_cannot_be_made_for_staff_accounts(self):
        with frozen_time(at(hour=9)), self.assertRaises(ApiError) as caught:
            services.create_reservation(
                actor=self.admin, student=self.librarian, resource_type='seat',
                resource_id=self.seat.pk, window=self.window())
        self.assertEqual(caught.exception.detail.code, 'invalid_student')


class ConflictTests(PortalTestCase):
    def test_overlapping_booking_of_the_same_seat_is_rejected(self):
        with frozen_time(at(hour=9)):
            self.book_seat(start_hour=11, hours=2)
            for start_hour, hours in ((11, 2), (10, 2), (12, 2), (11, 1), (10, 4)):
                with self.assertRaises(ConflictError) as caught:
                    self.book_seat(student=self.other_student, start_hour=start_hour, hours=hours)
                self.assertEqual(caught.exception.detail.code, 'slot_taken')

    def test_adjacent_bookings_are_allowed(self):
        with frozen_time(at(hour=9)):
            self.book_seat(start_hour=11, hours=1)
            self.book_seat(student=self.other_student, start_hour=12, hours=1)
            self.book_seat(student=self.other_student, start_hour=10, hours=1)
        self.assertEqual(Reservation.objects.filter(seat=self.seat).count(), 3)

    def test_student_cannot_hold_two_places_at_the_same_time(self):
        with frozen_time(at(hour=9)):
            self.book_seat(start_hour=11, hours=2)
            with self.assertRaises(ConflictError) as caught:
                self.book_seat(seat=self.seat2, start_hour=12, hours=1)
            self.assertEqual(caught.exception.detail.code, 'student_conflict')
            with self.assertRaises(ConflictError):
                self.book_room(start_hour=11, hours=1)

    def test_database_rejects_a_double_booking_even_without_the_service_checks(self):
        """The unique slot constraint is the last line of defence against races."""
        with frozen_time(at(hour=9)):
            reservation = self.book_seat(start_hour=11)
        rival = Reservation.objects.create(
            code='RIVAL001', student=self.other_student, resource_type='seat', seat=self.seat,
            start_at=reservation.start_at, end_at=reservation.end_at)
        with self.assertRaises(IntegrityError), transaction.atomic():
            ReservationSlot.objects.create(
                reservation=rival, seat=self.seat, student=self.other_student,
                start_at=reservation.start_at)

    def test_lost_race_is_reported_as_a_conflict_and_leaves_no_trace(self):
        """Simulate a rival whose slots land after our overlap check passed."""
        with frozen_time(at(hour=9)):
            first = self.book_seat(start_hour=11)
            # Hide the first booking from the overlap check, as if it had not
            # been committed yet when the second request looked.
            Reservation.objects.filter(pk=first.pk).update(status=Status.COMPLETED)
            with self.assertRaises(ConflictError) as caught:
                self.book_seat(student=self.other_student, start_hour=11)
        self.assertEqual(caught.exception.detail.code, 'slot_taken')
        self.assertFalse(Reservation.objects.filter(student=self.other_student).exists())
        self.assertFalse(Notification.objects.filter(user=self.other_student).exists())

    def test_cancelling_frees_the_seat_for_someone_else(self):
        with frozen_time(at(hour=9)):
            reservation = self.book_seat(start_hour=11)
            services.cancel_reservation(reservation, actor=self.student)
            again = self.book_seat(student=self.other_student, start_hour=11)
        self.assertEqual(again.status, Status.CONFIRMED)

    def test_a_room_and_a_seat_do_not_block_each_other(self):
        with frozen_time(at(hour=9)):
            self.book_seat(start_hour=11)
            self.book_room(student=self.other_student, start_hour=11)


class RoomBookingTests(PortalTestCase):
    def test_group_size_must_fit_the_room(self):
        with frozen_time(at(hour=9)):
            for count, code in ((1, 'under_occupancy'), (5, 'over_capacity')):
                with self.assertRaises(ApiError) as caught:
                    self.book_room(participant_count=count)
                self.assertEqual(caught.exception.detail.code, code)
            self.assertEqual(self.book_room(participant_count=4).participant_count, 4)

    def test_invited_classmates_are_recorded_and_notified(self):
        with frozen_time(at(hour=9)):
            reservation = self.book_room(participants=[self.other_student])
        self.assertEqual(reservation.participants.count(), 1)
        self.assertTrue(Notification.objects.filter(
            user=self.other_student,
            title='You were added to a study room reservation').exists())

    def test_room_duration_limit_differs_from_seats(self):
        with frozen_time(at(hour=9)):
            with self.assertRaises(ApiError) as caught:
                self.book_room(hours=3)  # rooms: 2 hours by default
            self.assertEqual(caught.exception.detail.code, 'too_long')
            self.book_seat(hours=3)      # seats: up to 4 hours
