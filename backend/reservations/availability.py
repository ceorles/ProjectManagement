"""Read-only availability queries behind the seat map and the room list."""
from collections import defaultdict
from datetime import time, timedelta

from django.db.models import F
from django.utils import timezone

from config.exceptions import ApiError
from library.models import ResourceStatus
from library.services import get_day_schedule, get_policy
from seats.models import Seat, Zone

from .models import Reservation, ReservationSeat
from .windows import check_bookable, to_datetime

ACTIVE = Reservation.ACTIVE_STATUSES

# States a seat or room can be in for a requested time window.
AVAILABLE = 'available'      # free for the whole window
RESERVED = 'reserved'        # requested (pending) or confirmed, not yet checked in
OCCUPIED = 'occupied'        # someone is checked in
MINE = 'mine'                # the viewer's own reservation
UNAVAILABLE = 'unavailable'  # under maintenance / out of service


def _hhmm(moment):
    return timezone.localtime(moment).strftime('%H:%M')


def _block(reservation, viewer):
    """One booked interval. Students never see who booked it; staff do."""
    is_mine = reservation.student_id == viewer.pk
    block = {
        'start_time': _hhmm(reservation.start_at),
        'end_time': _hhmm(reservation.end_at),
        'status': reservation.status,
        'is_mine': is_mine,
    }
    if is_mine or viewer.is_library_staff:
        block['reservation_id'] = reservation.pk
    if viewer.is_library_staff:
        block['code'] = reservation.code
        block['student_name'] = reservation.student.full_name
        block['student_id'] = reservation.student.student_id
    return block


def _state(resource, reservations, viewer):
    if resource.status != ResourceStatus.ACTIVE:
        return UNAVAILABLE
    if not reservations:
        return AVAILABLE
    if any(r.student_id == viewer.pk for r in reservations):
        return MINE
    if any(r.status == Reservation.Status.CHECKED_IN for r in reservations):
        return OCCUPIED
    return RESERVED


def _overlapping(window_start, window_end, **filters):
    return (
        Reservation.objects
        .filter(status__in=ACTIVE, start_at__lt=window_end, end_at__gt=window_start, **filters)
        .select_related('student')
        .order_by('start_at')
    )


def _bookable(window):
    """Whether the window itself can be booked, and if not, why."""
    try:
        check_bookable(window, get_policy())
    except ApiError as exc:
        return False, str(exc.detail)
    return True, ''


def _window_header(window):
    bookable, reason = _bookable(window)
    return {
        'date': window.day.isoformat(),
        'start_time': window.start_time.strftime('%H:%M'),
        'end_time': window.end_time.strftime('%H:%M'),
        'bookable': bookable,
        'bookable_reason': reason,
        'generated_at': timezone.now().isoformat(),
    }


def _tally(states):
    summary = {key: 0 for key in (AVAILABLE, RESERVED, OCCUPIED, MINE, UNAVAILABLE)}
    for state in states:
        summary[state] += 1
    summary['total'] = len(states)
    return summary


def seat_availability(window, *, viewer, floor_id=None, zone_id=None):
    zones = Zone.objects.select_related('floor')
    if floor_id:
        zones = zones.filter(floor_id=floor_id)
    if zone_id:
        zones = zones.filter(pk=zone_id)
    zones = list(zones)

    # All the chairs of one table together, table after table.
    seats = Seat.objects.filter(zone__in=zones).order_by(
        F('table_number').asc(nulls_last=True), 'number')
    # A request can cover several seats, so availability is looked up per seat.
    by_seat = defaultdict(list)
    links = (
        ReservationSeat.objects
        .filter(seat__zone__in=zones, reservation__status__in=ACTIVE,
                reservation__start_at__lt=window.end_at,
                reservation__end_at__gt=window.start_at)
        .select_related('reservation__student')
        .order_by('reservation__start_at')
    )
    for link in links:
        by_seat[link.seat_id].append(link.reservation)

    seats_by_zone = defaultdict(list)
    all_states = []
    for seat in seats:
        reservations = by_seat.get(seat.pk, [])
        state = _state(seat, reservations, viewer)
        all_states.append(state)
        seats_by_zone[seat.zone_id].append({
            'id': seat.pk,
            'number': seat.number,
            'row': seat.row,
            'col': seat.col,
            'has_power_outlet': seat.has_power_outlet,
            'has_computer': seat.has_computer,
            'table_number': seat.table_number,
            'is_accessible': seat.is_accessible,
            'status': seat.status,
            'status_note': seat.status_note,
            'state': state,
            'blocks': [_block(r, viewer) for r in reservations],
        })

    payload = _window_header(window)
    payload['summary'] = _tally(all_states)
    payload['zones'] = [
        {
            'id': zone.pk,
            'name': zone.name,
            'zone_type': zone.zone_type,
            'zone_type_label': zone.get_zone_type_display(),
            'description': zone.description,
            'floor': {'id': zone.floor_id, 'name': zone.floor.name, 'level': zone.floor.level},
            'rows': zone.rows,
            'cols': zone.cols,
            'summary': _tally([seat['state'] for seat in seats_by_zone[zone.pk]]),
            'seats': seats_by_zone[zone.pk],
        }
        for zone in zones
    ]
    return payload


def day_schedule(resource, day, *, viewer):
    """Opening hours and every booked interval of one seat on one day."""
    schedule = get_day_schedule(day)
    day_start = to_datetime(day, time.min)
    reservations = _overlapping(
        day_start, day_start + timedelta(days=1), reservation_seats__seat=resource)
    return {
        'date': day.isoformat(),
        'is_open': schedule.is_open,
        'opens_at': schedule.opens_at.strftime('%H:%M') if schedule.is_open else None,
        'closes_at': schedule.closes_at.strftime('%H:%M') if schedule.is_open else None,
        'closed_reason': schedule.closed_reason,
        'resource_status': resource.status,
        'blocks': [_block(r, viewer) for r in reservations],
    }


def occupancy_now(now=None):
    """Live counts of Reading Hall seats and computers for the dashboards."""
    now = now or timezone.now()
    current = Reservation.objects.filter(status__in=ACTIVE, start_at__lte=now, end_at__gt=now)

    def tally(places):
        # Count seats, not reservations: one request may hold a whole table.
        rows = ReservationSeat.objects.filter(reservation__in=current, seat__in=places)
        occupied = rows.filter(reservation__status=Reservation.Status.CHECKED_IN).count()
        reserved = rows.exclude(reservation__status=Reservation.Status.CHECKED_IN).count()
        total = places.count()
        unavailable = places.exclude(status=ResourceStatus.ACTIVE).count()
        bookable = total - unavailable
        return {
            'total': total,
            'occupied': occupied,
            'reserved': reserved,
            'unavailable': unavailable,
            'available': max(bookable - occupied - reserved, 0),
            'occupancy_rate': round(100 * (occupied + reserved) / bookable) if bookable else 0,
        }

    return {
        'seats': tally(Seat.objects.filter(has_computer=False)),
        'computers': tally(Seat.objects.filter(has_computer=True)),
    }
