"""
Read-only statistics for dashboards and reports.

This app owns no tables: it only summarises data that belongs to the other
apps. Grouping by day and hour is done in Python on the library's local
time, which keeps the queries simple and identical on every database.
"""
from collections import Counter, OrderedDict
from datetime import time, timedelta

from django.utils import timezone

from library.services import get_day_schedule, local_now, local_today
from reservations.models import Reservation
from reservations.windows import to_datetime
from seats.models import Seat
from study_rooms.models import StudyRoom
from users.models import User

Status = Reservation.Status
ACTIVE = Reservation.ACTIVE_STATUSES
WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']


def reservation_queryset():
    return (
        Reservation.objects
        .select_related('student', 'seat__zone__floor', 'room__floor', 'created_by')
        .prefetch_related('participants__student')
    )


def library_today():
    """Today's opening hours and whether the library is open right now."""
    now = local_now()
    schedule = get_day_schedule(now.date())
    open_now = bool(
        schedule.is_open and schedule.opens_at <= now.time() < schedule.closes_at)
    return {
        'date': now.date().isoformat(),
        'is_open': schedule.is_open,
        'open_now': open_now,
        'opens_at': schedule.opens_at.strftime('%H:%M') if schedule.is_open else None,
        'closes_at': schedule.closes_at.strftime('%H:%M') if schedule.is_open else None,
        'closed_reason': schedule.closed_reason,
    }


def day_bounds(day):
    start = to_datetime(day, time.min)
    return start, start + timedelta(days=1)


def status_counts(queryset):
    counts = Counter(queryset.values_list('status', flat=True))
    data = {status: counts.get(status, 0) for status in Status.values}
    data['total'] = sum(counts.values())
    return data


def hours_used(queryset):
    """Hours actually spent in completed reservations."""
    total = timedelta()
    rows = queryset.filter(status=Status.COMPLETED).values_list(
        'start_at', 'end_at', 'checked_in_at', 'checked_out_at')
    for start_at, end_at, checked_in_at, checked_out_at in rows:
        begin = max(start_at, checked_in_at) if checked_in_at else start_at
        finish = checked_out_at or end_at
        if finish > begin:
            total += finish - begin
    return round(total.total_seconds() / 3600, 1)


def rates(counts):
    """Cancellation and no-show share of all reservations in `counts`."""
    total = counts['total']
    if not total:
        return {'cancellation_rate': 0, 'no_show_rate': 0, 'completion_rate': 0}
    return {
        'cancellation_rate': round(100 * counts[Status.CANCELLED] / total, 1),
        'no_show_rate': round(100 * counts[Status.NO_SHOW] / total, 1),
        'completion_rate': round(100 * counts[Status.COMPLETED] / total, 1),
    }


def period_report(days):
    """Everything the reports page shows for the last `days` days (incl. today)."""
    today = local_today()
    first_day = today - timedelta(days=days - 1)
    start, _ = day_bounds(first_day)
    _, end = day_bounds(today)
    queryset = Reservation.objects.filter(start_at__gte=start, start_at__lt=end)

    daily = OrderedDict()
    for offset in range(days):
        day = first_day + timedelta(days=offset)
        daily[day] = {
            'date': day.isoformat(), 'total': 0, 'seat': 0, 'room': 0,
            Status.COMPLETED: 0, Status.CANCELLED: 0, Status.NO_SHOW: 0,
        }
    by_hour = Counter()
    by_weekday = Counter()
    seat_use = Counter()
    room_use = Counter()
    zone_use = Counter()
    students = set()
    booked_minutes = 0

    rows = queryset.values_list(
        'start_at', 'end_at', 'status', 'resource_type', 'seat__number', 'seat__zone__name',
        'room__name', 'student_id',
    )
    for start_at, end_at, status, resource_type, seat_number, zone_name, room_name, student in rows:
        local_start = timezone.localtime(start_at)
        bucket = daily.get(local_start.date())
        if bucket is None:
            continue
        bucket['total'] += 1
        bucket[resource_type] += 1
        if status in bucket:
            bucket[status] += 1
        if status == Status.CANCELLED:
            continue  # cancelled bookings do not count as usage
        by_hour[local_start.hour] += 1
        by_weekday[local_start.weekday()] += 1
        students.add(student)
        booked_minutes += int((end_at - start_at).total_seconds() // 60)
        if resource_type == Reservation.ResourceType.SEAT:
            seat_use[f'Seat {seat_number}'] += 1
            zone_use[zone_name] += 1
        else:
            room_use[room_name] += 1

    counts = status_counts(queryset)
    hours = sorted(by_hour) or [8]
    return {
        'range': {'from': first_day.isoformat(), 'to': today.isoformat(), 'days': days},
        'totals': {
            **counts,
            **rates(counts),
            'seat': sum(day['seat'] for day in daily.values()),
            'room': sum(day['room'] for day in daily.values()),
            'unique_students': len(students),
            'hours_booked': round(booked_minutes / 60, 1),
            'hours_used': hours_used(queryset),
        },
        'daily': list(daily.values()),
        'by_hour': [
            {'hour': hour, 'count': by_hour.get(hour, 0)}
            for hour in range(min(hours), max(hours) + 1)
        ],
        'by_weekday': [
            {'weekday': index, 'label': label, 'count': by_weekday.get(index, 0)}
            for index, label in enumerate(WEEKDAYS)
        ],
        'top_seats': [{'label': k, 'count': v} for k, v in seat_use.most_common(8)],
        'top_rooms': [{'label': k, 'count': v} for k, v in room_use.most_common(8)],
        'by_zone': [{'label': k, 'count': v} for k, v in zone_use.most_common()],
    }


def system_totals():
    today_start, today_end = day_bounds(local_today())
    return {
        'students': User.objects.filter(role=User.Role.STUDENT, is_active=True).count(),
        'librarians': User.objects.filter(role=User.Role.LIBRARIAN, is_active=True).count(),
        'admins': User.objects.filter(role=User.Role.ADMIN, is_active=True).count(),
        'inactive_accounts': User.objects.filter(is_active=False).count(),
        'seats': Seat.objects.count(),
        'rooms': StudyRoom.objects.count(),
        'active_reservations': Reservation.objects.filter(status__in=ACTIVE).count(),
        'reservations_today': Reservation.objects.filter(
            start_at__gte=today_start, start_at__lt=today_end).count(),
    }
