"""Read-only availability queries behind the seat map and the room list."""
from collections import defaultdict
from datetime import time, timedelta

from django.utils import timezone

from config.exceptions import ApiError
from library.models import ResourceStatus
from library.services import get_day_schedule, get_policy
from seats.models import Seat, Zone
from study_rooms.models import StudyRoom

from .models import Reservation
from .windows import check_bookable, to_datetime

ACTIVE = Reservation.ACTIVE_STATUSES

# States a seat or room can be in for a requested time window.
AVAILABLE = 'available'      # free for the whole window
RESERVED = 'reserved'        # booked by someone, not yet checked in
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


def _bookable(window, resource_type):
    """Whether the window itself can be booked, and if not, why."""
    try:
        check_bookable(window, resource_type, get_policy())
    except ApiError as exc:
        return False, str(exc.detail)
    return True, ''


def _window_header(window, resource_type):
    bookable, reason = _bookable(window, resource_type)
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

    seats = Seat.objects.filter(zone__in=zones).order_by('row', 'col')
    by_seat = defaultdict(list)
    for reservation in _overlapping(
        window.start_at, window.end_at,
        resource_type=Reservation.ResourceType.SEAT, seat__zone__in=zones,
    ):
        by_seat[reservation.seat_id].append(reservation)

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
            'near_window': seat.near_window,
            'is_accessible': seat.is_accessible,
            'status': seat.status,
            'status_note': seat.status_note,
            'state': state,
            'blocks': [_block(r, viewer) for r in reservations],
        })

    payload = _window_header(window, Reservation.ResourceType.SEAT)
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


def room_availability(window, *, viewer, floor_id=None):
    rooms = StudyRoom.objects.select_related('floor').prefetch_related('facilities')
    if floor_id:
        rooms = rooms.filter(floor_id=floor_id)
    rooms = list(rooms)

    by_room = defaultdict(list)
    for reservation in _overlapping(
        window.start_at, window.end_at,
        resource_type=Reservation.ResourceType.ROOM, room__in=rooms,
    ):
        by_room[reservation.room_id].append(reservation)

    items = []
    for room in rooms:
        reservations = by_room.get(room.pk, [])
        items.append({
            'id': room.pk,
            'name': room.name,
            'code': room.code,
            'floor': {'id': room.floor_id, 'name': room.floor.name, 'level': room.floor.level},
            'capacity': room.capacity,
            'min_occupancy': room.min_occupancy,
            'description': room.description,
            'facilities': [facility.name for facility in room.facilities.all()],
            'status': room.status,
            'status_note': room.status_note,
            'state': _state(room, reservations, viewer),
            'blocks': [_block(r, viewer) for r in reservations],
        })

    payload = _window_header(window, Reservation.ResourceType.ROOM)
    payload['summary'] = _tally([item['state'] for item in items])
    payload['rooms'] = items
    return payload


def day_schedule(resource, day, *, viewer):
    """Opening hours and every booked interval of one seat/room on one day."""
    schedule = get_day_schedule(day)
    day_start = to_datetime(day, time.min)
    field = 'seat' if isinstance(resource, Seat) else 'room'
    reservations = _overlapping(day_start, day_start + timedelta(days=1), **{field: resource})
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
    """Live counts of seats and rooms for the dashboards."""
    now = now or timezone.now()
    current = Reservation.objects.filter(status__in=ACTIVE, start_at__lte=now, end_at__gt=now)

    def tally(resource_type, total, unavailable):
        rows = current.filter(resource_type=resource_type)
        occupied = rows.filter(status=Reservation.Status.CHECKED_IN).count()
        reserved = rows.filter(status=Reservation.Status.CONFIRMED).count()
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
        'seats': tally(
            Reservation.ResourceType.SEAT,
            Seat.objects.count(),
            Seat.objects.exclude(status=ResourceStatus.ACTIVE).count(),
        ),
        'rooms': tally(
            Reservation.ResourceType.ROOM,
            StudyRoom.objects.count(),
            StudyRoom.objects.exclude(status=ResourceStatus.ACTIVE).count(),
        ),
    }
