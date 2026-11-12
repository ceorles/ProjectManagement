"""Time windows: parsing, slot arithmetic and the "is this bookable?" rules."""
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_time

from config.exceptions import ApiError
from library.services import get_day_schedule

SLOT = timedelta(minutes=settings.RESERVATION_SLOT_MINUTES)
SLOT_MINUTES = settings.RESERVATION_SLOT_MINUTES


@dataclass(frozen=True)
class Window:
    """A time range on one calendar day, in the library's time zone."""

    day: date
    start_time: time
    end_time: time
    start_at: datetime
    end_at: datetime

    @property
    def minutes(self):
        return int((self.end_at - self.start_at).total_seconds() // 60)


def to_datetime(day, moment):
    return timezone.make_aware(datetime.combine(day, moment))


def build_window(day, start_time, end_time):
    """Validate the shape of a window (not whether it is bookable)."""
    for label, value in (('Start', start_time), ('End', end_time)):
        if value.minute % SLOT_MINUTES or value.second or value.microsecond:
            raise ApiError(
                f'{label} time must be on a {SLOT_MINUTES}-minute boundary.',
                code='invalid_time',
            )
    if end_time <= start_time:
        raise ApiError('The end time must be after the start time.', code='invalid_time')
    return Window(day, start_time, end_time,
                  to_datetime(day, start_time), to_datetime(day, end_time))


def parse_day(params):
    day = parse_date(params.get('date', '') or '')
    if day is None:
        raise ApiError('A valid date (YYYY-MM-DD) is required.', code='invalid_date')
    return day


def parse_window(params):
    """Read `date`, `start` and `end` (HH:MM) from query parameters."""
    day = parse_day(params)
    try:
        start_time = parse_time(params.get('start', '') or '')
        end_time = parse_time(params.get('end', '') or '')
    except ValueError:
        start_time = end_time = None
    if start_time is None or end_time is None:
        raise ApiError('Valid start and end times (HH:MM) are required.', code='invalid_time')
    return build_window(day, start_time, end_time)


def slot_starts(start_at, end_at):
    """Start of every slot covered by [start_at, end_at)."""
    starts = []
    cursor = start_at
    while cursor < end_at:
        starts.append(cursor)
        cursor += SLOT
    return starts


def format_duration(minutes):
    hours, rest = divmod(minutes, 60)
    if hours and rest:
        return f'{hours} h {rest} min'
    if hours:
        return f'{hours} hour' + ('s' if hours != 1 else '')
    return f'{rest} minutes'


def check_bookable(window, resource_type, policy, now=None):
    """
    Raise ApiError unless a new reservation may be placed in this window.

    Covers the rules that do not depend on a particular seat, room or
    student: the past, the advance-booking limit, duration limits, and the
    library's opening hours and closures.
    """
    now = now or timezone.now()
    today = timezone.localtime(now).date()

    if window.day < today or window.end_at <= now:
        raise ApiError('That time has already passed.', code='in_the_past')
    # The slot currently in progress may still be booked (walk-ins), but
    # nothing earlier than that.
    if window.start_at + SLOT <= now:
        raise ApiError('That start time has already passed.', code='in_the_past')

    latest = today + timedelta(days=policy.max_advance_days)
    if window.day > latest:
        raise ApiError(
            f'Reservations can be made up to {policy.max_advance_days} day(s) in advance '
            f'(until {latest:%b %d, %Y}).',
            code='too_far_ahead',
        )

    if window.minutes < policy.min_duration_minutes:
        raise ApiError(
            f'The minimum reservation is {format_duration(policy.min_duration_minutes)}.',
            code='too_short',
        )
    maximum = (policy.max_seat_duration_minutes if resource_type == 'seat'
               else policy.max_room_duration_minutes)
    if window.minutes > maximum:
        kind = 'seat' if resource_type == 'seat' else 'study room'
        raise ApiError(
            f'A {kind} can be reserved for at most {format_duration(maximum)}.',
            code='too_long',
        )

    schedule = get_day_schedule(window.day)
    if not schedule.is_open:
        raise ApiError(
            f'The library is closed on {window.day:%A, %b %d}. {schedule.closed_reason}'.strip(),
            code='library_closed',
        )
    if window.start_time < schedule.opens_at or window.end_time > schedule.closes_at:
        raise ApiError(
            f'On {window.day:%A} the library is open from {schedule.opens_at:%I:%M %p} '
            f'to {schedule.closes_at:%I:%M %p}.',
            code='outside_hours',
        )
