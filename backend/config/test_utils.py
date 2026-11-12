"""Shared fixtures for the test suites of every app."""
from contextlib import contextmanager
from datetime import datetime, time, timedelta
from unittest import mock

from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APITestCase

from library.models import Floor
from reservations import services
from reservations.windows import build_window
from seats.models import Seat, Zone
from study_rooms.models import StudyRoom
from users.models import User

PASSWORD = 'Str0ng!Passw0rd'

# A Monday morning, inside the default opening hours (08:00-20:00).
MONDAY = datetime(2026, 3, 2).date()


def at(day=MONDAY, hour=10, minute=0):
    """An aware datetime in the library's time zone."""
    return timezone.make_aware(datetime.combine(day, time(hour, minute)))


@contextmanager
def frozen_time(moment):
    """Make `timezone.now()` return `moment` everywhere."""
    with mock.patch('django.utils.timezone.now', return_value=moment):
        yield moment


class PortalTestCase(APITestCase):
    """Creates one account per role plus a small library to book."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(
            email='admin@test.edu', password=PASSWORD, first_name='Ada', last_name='Admin',
            role=User.Role.ADMIN)
        cls.librarian = User.objects.create_user(
            email='librarian@test.edu', password=PASSWORD, first_name='Lia', last_name='Brarian',
            role=User.Role.LIBRARIAN)
        cls.student = User.objects.create_user(
            email='student@test.edu', password=PASSWORD, first_name='Sam', last_name='Student',
            role=User.Role.STUDENT, student_id='2024-0001')
        cls.other_student = User.objects.create_user(
            email='other@test.edu', password=PASSWORD, first_name='Olive', last_name='Other',
            role=User.Role.STUDENT, student_id='2024-0002')

        cls.floor = Floor.objects.create(name='Ground Floor', level=0)
        cls.zone = Zone.objects.create(floor=cls.floor, name='Quiet Zone', rows=2, cols=3)
        cls.seat = Seat.objects.create(zone=cls.zone, number='A01', row=1, col=1)
        cls.seat2 = Seat.objects.create(zone=cls.zone, number='A02', row=1, col=2)
        cls.room = StudyRoom.objects.create(
            name='Study Room 1', code='SR-1', floor=cls.floor, capacity=4, min_occupancy=2)

    def setUp(self):
        cache.clear()  # throttle counters and the sweep timer

    def login_as(self, user):
        self.client.force_authenticate(user=user)

    # Booking helpers -------------------------------------------------------

    def window(self, start_hour=11, hours=1, day=MONDAY, start_minute=0):
        start = datetime.combine(day, time(start_hour, start_minute))
        end = start + timedelta(hours=hours)
        return build_window(day, start.time(), end.time())

    def book_seat(self, student=None, seat=None, **window_kwargs):
        student = student or self.student
        return services.create_reservation(
            actor=student, student=student, resource_type='seat',
            resource_id=(seat or self.seat).pk, window=self.window(**window_kwargs))

    def book_room(self, student=None, participant_count=2, participants=(), **window_kwargs):
        student = student or self.student
        return services.create_reservation(
            actor=student, student=student, resource_type='room', resource_id=self.room.pk,
            window=self.window(**window_kwargs), participant_count=participant_count,
            participants=participants)

    def seat_payload(self, **overrides):
        payload = {
            'resource_type': 'seat', 'seat': self.seat.pk, 'date': MONDAY.isoformat(),
            'start_time': '11:00', 'end_time': '12:00',
        }
        payload.update(overrides)
        return payload

    def error_code(self, response):
        return response.data['error']['code']
