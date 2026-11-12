"""Read access to the library's schedule and rules, used by every other app."""
from dataclasses import dataclass
from datetime import date, time

from django.utils import timezone

from .models import Closure, OperatingHours, ReservationPolicy


def get_policy():
    return ReservationPolicy.load()


def local_now():
    """Current time in the library's time zone."""
    return timezone.localtime()


def local_today():
    return timezone.localdate()


@dataclass(frozen=True)
class DaySchedule:
    day: date
    is_open: bool
    opens_at: time | None = None
    closes_at: time | None = None
    closed_reason: str = ''


def get_day_schedule(day):
    """Opening hours for one calendar date, taking closures into account."""
    closure = Closure.objects.filter(date=day).first()
    if closure:
        return DaySchedule(day, False, closed_reason=closure.reason)
    hours = OperatingHours.objects.filter(weekday=day.weekday()).first()
    if hours is None or not hours.is_open:
        return DaySchedule(day, False, closed_reason='The library is closed on this day.')
    return DaySchedule(day, True, hours.opens_at, hours.closes_at)


def ensure_operating_hours():
    """Make sure all seven weekday rows exist (Sunday closed by default)."""
    for weekday, _label in OperatingHours.Weekday.choices:
        OperatingHours.objects.get_or_create(
            weekday=weekday,
            defaults={'is_open': weekday != OperatingHours.Weekday.SUNDAY},
        )
