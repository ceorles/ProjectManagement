"""
Taking seats and whole tables out of service, and putting them back.

`Seat.status` is what students and the booking rules see. When a whole table
goes out of service, each seat that was in service is switched off and flagged
`out_with_table`; a seat that was already out of service on its own is left
alone. Restoring the table switches back on only the flagged seats, so a broken
chair stays out of service.

A reservation is never cancelled silently: if places are held, the change is
refused until the user has seen the list and confirmed it, and each student is
notified. A seat someone is sitting in cannot be taken out of service.
"""
from collections import defaultdict

from django.db import transaction
from django.db.models import F
from django.utils import timezone
from rest_framework.exceptions import NotFound

from activity.services import log_activity
from config.exceptions import ConflictError
from library.models import ResourceStatus
from reservations.models import Reservation, ReservationSeat
from reservations.services import cancel_for_resource

from .models import Seat

Status = Reservation.Status


def _held_links(seats):
    """Links from these seats to reservations that are in use or still to come."""
    return (
        ReservationSeat.objects
        .filter(seat__in=seats, reservation__status__in=Reservation.ACTIVE_STATUSES,
                reservation__end_at__gt=timezone.now())
        .select_related('seat', 'reservation__student')
        .order_by('reservation__start_at')
    )


def _describe(reservation, seat_numbers):
    start = timezone.localtime(reservation.start_at)
    end = timezone.localtime(reservation.end_at)
    return {
        'id': reservation.pk,
        'code': reservation.code,
        'status': reservation.status,
        'status_label': reservation.get_status_display(),
        'student_name': reservation.student.full_name,
        'student_id': reservation.student.student_id,
        'date': start.date().isoformat(),
        'start_time': start.strftime('%H:%M'),
        'end_time': end.strftime('%H:%M'),
        'seats': sorted(seat_numbers),
    }


def affected_reservations(seats):
    """Reservations holding any of these seats, soonest first."""
    numbers = defaultdict(set)
    reservations = {}
    for link in _held_links(seats):
        numbers[link.reservation_id].add(link.seat.number)
        reservations[link.reservation_id] = link.reservation
    return [_describe(item, numbers[pk]) for pk, item in reservations.items()]


def _check_safe_to_close(seats, confirmed):
    """Refuse the change while it would affect someone who has not been considered."""
    affected = affected_reservations(seats)
    in_use = [item for item in affected if item['status'] == Status.CHECKED_IN]
    if in_use:
        raise ConflictError(
            f'{in_use[0]["student_name"]} is checked in here right now. '
            'Check the student out first.',
            code='seat_in_use',
        )
    if affected and not confirmed:
        count = len(affected)
        raise ConflictError(
            f'{count} active or upcoming reservation{"s" if count != 1 else ""} would be '
            'cancelled. Review and confirm to continue.',
            code='reservations_affected',
        )


def _table_state(seats, affected):
    off = [seat for seat in seats if seat.status != ResourceStatus.ACTIVE]
    if len(off) == len(seats):
        return 'out_of_service'
    if off:
        return 'partial'
    return 'reserved' if affected else 'available'


def _table_payload(zone_id, number, seats, links_by_seat):
    affected = {}
    seat_rows = []
    for seat in seats:
        links = links_by_seat.get(seat.pk, [])
        for link in links:
            entry = affected.setdefault(
                link.reservation_id, {'reservation': link.reservation, 'seats': set()})
            entry['seats'].add(seat.number)
        seat_rows.append({
            'id': seat.pk,
            'number': seat.number,
            'status': seat.status,
            'status_label': seat.get_status_display(),
            'status_note': seat.status_note,
            'out_with_table': seat.out_with_table,
            'reservation_count': len(links),
        })
    return {
        'zone': zone_id,
        'table_number': number,
        'state': _table_state(seats, affected),
        'available_seats': sum(seat.status == ResourceStatus.ACTIVE for seat in seats),
        'total_seats': len(seats),
        'can_restore': any(seat.out_with_table for seat in seats),
        'seats': seat_rows,
        'reservations': [
            _describe(entry['reservation'], entry['seats']) for entry in affected.values()
        ],
    }


def tables_overview(zone_id):
    """Every table of a zone with its seats, state and held reservations."""
    seats = list(
        Seat.objects.filter(zone_id=zone_id, table_number__isnull=False)
        .order_by(F('table_number'), 'number')
    )
    links_by_seat = defaultdict(list)
    for link in _held_links(seats):
        links_by_seat[link.seat_id].append(link)
    tables = defaultdict(list)
    for seat in seats:
        tables[seat.table_number].append(seat)
    return [
        _table_payload(zone_id, number, group, links_by_seat)
        for number, group in sorted(tables.items())
    ]


def _one_table(zone_id, table_number):
    return next(
        (item for item in tables_overview(zone_id) if item['table_number'] == table_number),
        None,
    )


def set_seat_status(seat, *, status, note, confirmed, actor, request=None):
    """Change one seat. The other seats of its table are not touched."""
    cancelled = 0
    with transaction.atomic():
        seat = Seat.objects.select_for_update().get(pk=seat.pk)
        if status == ResourceStatus.ACTIVE:
            if seat.out_with_table:
                raise ConflictError(
                    f'Table {seat.table_number} is out of service. Restore the table first.',
                    code='table_out_of_service',
                )
        else:
            _check_safe_to_close([seat], confirmed)
            cancelled = cancel_for_resource(
                seat, actor=actor, reason=f'Seat {seat.number} is out of service.')
        seat.status = status
        seat.status_note = '' if status == ResourceStatus.ACTIVE else note
        # From now on this seat is out of service in its own right.
        seat.out_with_table = False
        seat.save(update_fields=['status', 'status_note', 'out_with_table', 'updated_at'])
        log_activity(
            'resource.seat_status', f'Set seat {seat.number} to "{seat.get_status_display()}".',
            actor=actor, target=seat, request=request,
        )
    return seat, cancelled


def set_table_status(zone_id, table_number, *, status, note, confirmed, actor, request=None):
    """Take a whole table out of service or restore it: all of it, or nothing."""
    cancelled = restored = 0
    with transaction.atomic():
        seats = list(
            Seat.objects.select_for_update()
            .filter(zone_id=zone_id, table_number=table_number).order_by('number')
        )
        if not seats:
            raise NotFound('That table does not exist.')

        if status == ResourceStatus.INACTIVE:
            _check_safe_to_close(seats, confirmed)
            reason = f'Table {table_number} is out of service.'
            for seat in seats:
                cancelled += cancel_for_resource(seat, actor=actor, reason=reason)
                if seat.status == ResourceStatus.ACTIVE:
                    seat.status = ResourceStatus.INACTIVE
                    seat.status_note = note
                    seat.out_with_table = True
                    seat.save(update_fields=[
                        'status', 'status_note', 'out_with_table', 'updated_at'])
            verb = 'Took table {} out of service.'
        else:
            for seat in seats:
                if seat.out_with_table:
                    seat.status = ResourceStatus.ACTIVE
                    seat.status_note = ''
                    seat.out_with_table = False
                    seat.save(update_fields=[
                        'status', 'status_note', 'out_with_table', 'updated_at'])
                    restored += 1
            verb = 'Restored table {} to service.'
        log_activity('resource.table_status', verb.format(table_number),
                     actor=actor, request=request)

    payload = _one_table(zone_id, table_number)
    payload['cancelled_reservations'] = cancelled
    payload['restored_seats'] = restored
    return payload
