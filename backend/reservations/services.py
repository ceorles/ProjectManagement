"""
The reservation engine.

Every change of reservation state goes through a function in this module, so
the rules live in one place and the slot ledger (ReservationSlot) is always
updated in the same database transaction as the status.
"""
import secrets
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from activity.services import log_activity
from config.exceptions import ApiError, ConflictError
from library.models import ResourceStatus
from library.services import get_day_schedule, get_policy
from notifications.models import Notification
from notifications.services import notify, notify_many
from seats.models import Seat
from users.models import User

from .models import Reservation, ReservationSeat, ReservationSlot, describe_seats
from .windows import check_bookable, slot_starts

Status = Reservation.Status
ACTIVE = Reservation.ACTIVE_STATUSES

# A request may cover up to one whole table.
MAX_SEATS_PER_REQUEST = 6
# More seats than this need a reason for the librarian to review.
SEATS_WITHOUT_REASON = 2

# No 0/O or 1/I/L, so a code is easy to read aloud and type at the desk.
CODE_ALPHABET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'


# ── Helpers ────────────────────────────────────────────────────────────────

def generate_code():
    while True:
        code = ''.join(secrets.choice(CODE_ALPHABET) for _ in range(8))
        if not Reservation.objects.filter(code=code).exists():
            return code


def describe_time(reservation):
    start = timezone.localtime(reservation.start_at)
    end = timezone.localtime(reservation.end_at)
    return f'{start:%a, %b %d} from {start:%I:%M %p} to {end:%I:%M %p}'.replace(' 0', ' ')


def reservation_link(reservation):
    return f'/reservations/{reservation.pk}'


def checkin_opens_at(reservation, policy):
    return reservation.start_at - timedelta(minutes=policy.checkin_early_minutes)


def checkin_deadline(reservation, policy):
    """
    Moment a reservation that has not been checked in is released: exactly
    15 minutes after its start time, whenever it was booked or approved. A
    request still pending at this moment expires.
    """
    return reservation.start_at + timedelta(minutes=policy.checkin_grace_minutes)


def no_show_count(student, policy, now=None):
    now = now or timezone.now()
    since = now - timedelta(days=policy.no_show_window_days)
    return Reservation.objects.filter(
        student=student, status=Status.NO_SHOW, start_at__gte=since
    ).count()


def reviewers():
    """Everyone who must hear about a new request: active librarians and admins."""
    return list(User.objects.filter(
        role__in=(User.Role.LIBRARIAN, User.Role.ADMIN), is_active=True))


def _locked(reservation):
    return Reservation.objects.select_for_update().get(pk=reservation.pk)


def _release_slots(reservation):
    reservation.slots.all().delete()


# ── Creating a reservation ─────────────────────────────────────────────────

def _lock_seats(seat_ids):
    """Fetch (and row-lock, where the database supports it) the requested seats."""
    ids = list(dict.fromkeys(seat_ids))
    if not ids:
        raise ApiError('Choose at least one seat.', code='resource_not_found')
    # On SQLite the IMMEDIATE transaction already serialises writers.
    seats = list(Seat.objects.select_for_update().filter(pk__in=ids))
    if len(seats) != len(ids):
        raise ApiError('One of the selected seats does not exist.', code='resource_not_found')
    return sorted(seats, key=lambda seat: seat.number)


def _check_seat_request(seats, purpose):
    """The rules about what may be asked for in one seat request."""
    if len(seats) > MAX_SEATS_PER_REQUEST:
        raise ApiError(
            f'One request can cover at most {MAX_SEATS_PER_REQUEST} seats (one table).',
            code='too_many_seats',
        )
    computers = [seat for seat in seats if seat.has_computer]
    if computers and len(seats) > 1:
        raise ApiError('Only one computer can be reserved at a time, on its own.',
                       code='one_computer_only')
    if len({seat.zone_id for seat in seats}) > 1:
        raise ApiError('All seats in one request must be in the same area.',
                       code='mixed_areas')
    for seat in seats:
        if seat.status != ResourceStatus.ACTIVE:
            raise ConflictError(
                f'Seat {seat.number} is currently {seat.get_status_display().lower()}.',
                code='resource_unavailable',
            )
    if len(seats) > SEATS_WITHOUT_REASON and not purpose.strip():
        raise ApiError(
            f'Please give a reason for requesting more than {SEATS_WITHOUT_REASON} seats.',
            code='reason_required',
        )


def _check_student_limits(student, window, policy, now):
    if policy.no_show_limit:
        strikes = no_show_count(student, policy, now)
        if strikes >= policy.no_show_limit:
            raise ApiError(
                f'Booking is suspended: {strikes} reservations were missed in the last '
                f'{policy.no_show_window_days} days. Please see a librarian.',
                code='booking_suspended',
            )

    # Requests waiting for approval count too, so limits cannot be sidestepped.
    active = Reservation.objects.filter(student=student, status__in=ACTIVE).count()
    if active >= policy.max_active_reservations:
        raise ApiError(
            f'The limit is {policy.max_active_reservations} active reservations at a time. '
            'Cancel or finish one before booking another.',
            code='active_limit',
        )

    day_start = window.start_at.replace(hour=0, minute=0)
    same_day = Reservation.objects.filter(
        student=student,
        start_at__gte=day_start,
        start_at__lt=day_start + timedelta(days=1),
    ).exclude(status__in=(Status.CANCELLED, Status.REJECTED)).count()
    if same_day >= policy.max_reservations_per_day:
        raise ApiError(
            f'The limit is {policy.max_reservations_per_day} reservations per day.',
            code='daily_limit',
        )


def _check_conflicts(student, seats, window):
    """Pending requests hold their places just like confirmed reservations."""
    overlapping = Q(status__in=ACTIVE, start_at__lt=window.end_at, end_at__gt=window.start_at)

    taken = sorted(set(
        ReservationSeat.objects
        .filter(seat__in=seats, reservation__status__in=ACTIVE,
                reservation__start_at__lt=window.end_at,
                reservation__end_at__gt=window.start_at)
        .values_list('seat__number', flat=True)
    ))
    if taken:
        which = f'Seat {taken[0]} is' if len(taken) == 1 else f'Seats {", ".join(taken)} are'
        raise ConflictError(
            f'{which} already requested or reserved for all or part of that time. '
            'Please choose again.',
            code='slot_taken',
        )

    clash = Reservation.objects.filter(overlapping, student=student).first()
    if clash:
        raise ConflictError(
            f'There is already a reservation ({clash.code}) that overlaps this time.',
            code='student_conflict',
        )


def _claim_slots(reservation, seats):
    """Insert the slot rows. The unique constraints are the final arbiter."""
    starts = slot_starts(reservation.start_at, reservation.end_at)
    rows = [
        ReservationSlot(
            reservation=reservation, seat=seat, start_at=start,
            # Only the first seat carries the student (see the model).
            student_id=reservation.student_id if index == 0 else None,
        )
        for index, seat in enumerate(seats) for start in starts
    ]
    try:
        with transaction.atomic():
            ReservationSlot.objects.bulk_create(rows)
    except IntegrityError as exc:
        raise ConflictError(
            'That time was just taken by another reservation. Please choose again.',
            code='slot_taken',
        ) from exc


def create_reservation(*, actor, student, window, resource_type=Reservation.ResourceType.SEAT,
                       resource_id=None, seat_ids=None, purpose='', request=None):
    """
    Place a reservation. Raises ApiError/ConflictError if any rule is broken.

    A request made by a student is saved as PENDING and waits for a librarian.
    A booking entered by a librarian or admin on a student's behalf is
    CONFIRMED straight away, because the person who approves made it.

    Only seats and computers can be reserved. The library's room is a common
    space for everyone.
    """
    if resource_type != Reservation.ResourceType.SEAT:
        raise ApiError('Rooms cannot be reserved. Please reserve a seat or a computer.',
                       code='room_not_reservable')
    if actor.is_student:
        if actor.pk != student.pk:
            raise PermissionDenied('You can only make reservations for yourself.')
    elif not actor.can_manage_reservations:
        raise PermissionDenied('Only a librarian can make a reservation for a student.')
    if not (student.is_student and student.is_active):
        raise ApiError('Reservations can only be made for active student accounts.',
                       code='invalid_student')

    process_due_reservations()  # release anything that has just expired
    policy = get_policy()
    now = timezone.now()
    check_bookable(window, policy, now)
    by_staff = actor.can_manage_reservations

    with transaction.atomic():
        seats = _lock_seats(seat_ids if seat_ids else [resource_id])
        _check_seat_request(seats, purpose)
        _check_student_limits(student, window, policy, now)
        _check_conflicts(student, seats, window)

        reservation = Reservation.objects.create(
            code=generate_code(),
            student=student,
            resource_type=resource_type,
            seat=seats[0],
            start_at=window.start_at,
            end_at=window.end_at,
            status=Status.CONFIRMED if by_staff else Status.PENDING,
            participant_count=len(seats),
            purpose=purpose.strip(),
            created_by=actor,
            decided_by=actor if by_staff else None,
            decided_at=now if by_staff else None,
        )
        ReservationSeat.objects.bulk_create(
            [ReservationSeat(reservation=reservation, seat=seat) for seat in seats])
        _claim_slots(reservation, seats)

        when = describe_time(reservation)
        label = describe_seats(seats)
        link = reservation_link(reservation)
        if by_staff:
            notify(
                student, 'Reservation confirmed',
                f'{label} is reserved for you on {when}. Booked by {actor.full_name}.',
                level=Notification.Level.SUCCESS, link=link,
            )
            log_activity(
                'reservation.created',
                f'{label} reserved for {student.full_name} on {when} ({reservation.code}).',
                actor=actor, target=reservation, request=request,
            )
        else:
            notify(
                student, 'Reservation request sent',
                f'Your request for {label} on {when} is waiting for the librarian\'s approval.',
                link=link,
            )
            notify_many(
                reviewers(), 'New reservation request',
                f'{student.full_name} requested {label} on {when}. '
                'It needs to be approved or rejected.',
                level=Notification.Level.WARNING, link=link,
            )
            log_activity(
                'reservation.requested',
                f'{student.full_name} requested {label} on {when} ({reservation.code}).',
                actor=actor, target=reservation, request=request,
            )
    return reservation


# ── The librarian's decision ───────────────────────────────────────────────

def _require_reviewer(actor):
    if not actor.can_manage_reservations:
        raise PermissionDenied('Only a librarian can approve or reject reservations.')


def approve_reservation(reservation, *, actor):
    _require_reviewer(actor)
    now = timezone.now()
    with transaction.atomic():
        reservation = _locked(reservation)
        if reservation.status != Status.PENDING:
            raise ApiError(
                f'This request is already {reservation.get_status_display().lower()}.',
                code='invalid_status',
            )
        if now >= reservation.end_at:
            raise ApiError('The requested time has already passed.', code='in_the_past')
        reservation.status = Status.CONFIRMED
        reservation.decided_by = actor
        reservation.decided_at = now
        reservation.save(update_fields=['status', 'decided_by', 'decided_at', 'updated_at'])

        when = describe_time(reservation)
        label = reservation.resource_label
        notify(
            reservation.student, 'Reservation approved',
            f'Your request for {label} on {when} was approved by {actor.full_name}. '
            'Remember to check in when you arrive.',
            level=Notification.Level.SUCCESS, link=reservation_link(reservation),
        )
        log_activity(
            'reservation.approved',
            f'Approved {label} for {reservation.student.full_name} on {when} '
            f'({reservation.code}).',
            actor=actor, target=reservation,
        )
    return reservation


def reject_reservation(reservation, *, actor, reason=''):
    _require_reviewer(actor)
    now = timezone.now()
    with transaction.atomic():
        reservation = _locked(reservation)
        if reservation.status != Status.PENDING:
            raise ApiError(
                f'This request is already {reservation.get_status_display().lower()}.',
                code='invalid_status',
            )
        reservation.status = Status.REJECTED
        reservation.decided_by = actor
        reservation.decided_at = now
        reservation.decision_note = (reason or '').strip()[:200]
        reservation.save(update_fields=[
            'status', 'decided_by', 'decided_at', 'decision_note', 'updated_at'])
        _release_slots(reservation)  # the places are free for others again

        when = describe_time(reservation)
        label = reservation.resource_label
        detail = f' Reason: {reservation.decision_note}' if reservation.decision_note else ''
        notify(
            reservation.student, 'Reservation request rejected',
            f'Your request for {label} on {when} was not approved.{detail}',
            level=Notification.Level.DANGER, link=reservation_link(reservation),
        )
        log_activity(
            'reservation.rejected',
            f'Rejected {label} for {reservation.student.full_name} on {when} '
            f'({reservation.code}).',
            actor=actor, target=reservation,
        )
    return reservation


# ── Cancelling ─────────────────────────────────────────────────────────────

def _apply_cancel(reservation, actor, reason, now):
    reservation.status = Status.CANCELLED
    reservation.cancelled_at = now
    reservation.cancelled_by = actor
    reservation.cancel_reason = (reason or '').strip()[:200]
    reservation.save(update_fields=[
        'status', 'cancelled_at', 'cancelled_by', 'cancel_reason', 'updated_at'])
    _release_slots(reservation)

    when = describe_time(reservation)
    label = reservation.resource_label
    link = reservation_link(reservation)
    by_student = actor is not None and actor.pk == reservation.student_id
    if by_student:
        notify(reservation.student, 'Reservation cancelled',
               f'You cancelled {label} on {when}.', link=link)
    else:
        detail = f' Reason: {reservation.cancel_reason}' if reservation.cancel_reason else ''
        notify(reservation.student, 'Your reservation was cancelled',
               f'{label} on {when} was cancelled by the library.{detail}',
               level=Notification.Level.DANGER, link=link)
    log_activity(
        'reservation.cancelled',
        f'Cancelled {label} for {reservation.student.full_name} on {when} '
        f'({reservation.code}).',
        actor=actor, target=reservation,
    )


def cancel_reservation(reservation, *, actor, reason=''):
    policy = get_policy()
    now = timezone.now()
    with transaction.atomic():
        reservation = _locked(reservation)
        staff = actor.can_manage_reservations
        if not staff and reservation.student_id != actor.pk:
            raise PermissionDenied('You can only cancel your own reservations.')
        if reservation.status == Status.CHECKED_IN:
            raise ApiError('This reservation is in progress. Check out instead.',
                           code='invalid_status')
        if reservation.status not in (Status.PENDING, Status.CONFIRMED):
            raise ApiError(
                f'This reservation is already {reservation.get_status_display().lower()}.',
                code='invalid_status',
            )
        # A request that is still pending can always be withdrawn.
        if not staff and reservation.status == Status.CONFIRMED:
            cutoff = reservation.start_at - timedelta(
                minutes=policy.cancellation_cutoff_minutes)
            if now > cutoff:
                if policy.cancellation_cutoff_minutes:
                    message = (
                        'Reservations must be cancelled at least '
                        f'{policy.cancellation_cutoff_minutes} minutes before they start.'
                    )
                else:
                    message = 'This reservation has already started and can no longer be cancelled.'
                raise ApiError(message, code='cancel_window_closed')
        _apply_cancel(reservation, actor, reason, now)
    return reservation


UPCOMING = (Status.PENDING, Status.CONFIRMED)


def _cancel_many(queryset, actor, reason):
    now = timezone.now()
    count = 0
    with transaction.atomic():
        ids = list(queryset.values_list('pk', flat=True).distinct())
        for reservation in Reservation.objects.select_for_update().filter(pk__in=ids):
            _apply_cancel(reservation, actor, reason, now)
            count += 1
    return count


def cancel_for_resource(resource, *, actor, reason):
    """Cancel upcoming bookings of a seat that is going out of service."""
    return _cancel_many(
        Reservation.objects.filter(
            status__in=UPCOMING, end_at__gt=timezone.now(), reservation_seats__seat=resource),
        actor, reason,
    )


def cancel_for_student(student, *, actor, reason):
    return _cancel_many(
        Reservation.objects.filter(student=student, status__in=UPCOMING), actor, reason)


def cancel_outside_schedule(*, actor, reason):
    """Cancel upcoming bookings that no longer fit the opening hours/closures."""
    now = timezone.now()
    schedules = {}
    displaced = []
    upcoming = Reservation.objects.filter(status__in=UPCOMING, start_at__gt=now)
    for reservation in upcoming:
        start = timezone.localtime(reservation.start_at)
        end = timezone.localtime(reservation.end_at)
        schedule = schedules.setdefault(start.date(), get_day_schedule(start.date()))
        fits = (
            schedule.is_open
            and start.time() >= schedule.opens_at
            and end.time() <= schedule.closes_at
        )
        if not fits:
            displaced.append(reservation.pk)
    if not displaced:
        return 0
    return _cancel_many(Reservation.objects.filter(pk__in=displaced), actor, reason)


# ── Check-in, check-out, no-show ───────────────────────────────────────────

def _apply_no_show(reservation, now, actor=None):
    """
    Release a confirmed reservation nobody arrived for. With no `actor` this is
    the automatic cancellation after the check-in period.
    """
    policy = get_policy()
    automatic = actor is None
    reservation.status = Status.NO_SHOW
    if automatic:
        reservation.cancel_reason = (
            f'Automatically cancelled: no check-in within {policy.checkin_grace_minutes} '
            'minutes of the start time.'
        )
    reservation.save(update_fields=['status', 'cancel_reason', 'updated_at'])
    _release_slots(reservation)  # every seat of the reservation is free again

    strikes = no_show_count(reservation.student, policy, now)
    if automatic:
        title = 'Reservation automatically cancelled'
        message = (
            f'{reservation.resource_label} on {describe_time(reservation)} was automatically '
            f'cancelled because you did not check in within {policy.checkin_grace_minutes} '
            'minutes of the start time.'
        )
    else:
        title = 'Reservation marked as no-show'
        message = (
            f'You did not arrive for {reservation.resource_label} on '
            f'{describe_time(reservation)}, so the library released it.'
        )
    if policy.no_show_limit:
        message += (
            f' Missed reservations in the last {policy.no_show_window_days} days: '
            f'{strikes} of {policy.no_show_limit}.'
        )
    notify(reservation.student, title, message,
           level=Notification.Level.DANGER, link=reservation_link(reservation))
    log_activity(
        'reservation.no_show',
        f'{reservation.student.full_name} did not check in to {reservation.resource_label} '
        f'({reservation.code})' + ('; cancelled automatically.' if automatic else '.'),
        actor=actor, target=reservation,
    )


def _apply_expire(reservation, now):
    """A request nobody reviewed in time: released, and not counted against the student."""
    reservation.status = Status.CANCELLED
    reservation.cancelled_at = now
    reservation.cancel_reason = 'The request was not reviewed before the reserved time.'
    reservation.save(update_fields=['status', 'cancelled_at', 'cancel_reason', 'updated_at'])
    _release_slots(reservation)
    notify(
        reservation.student, 'Reservation request expired',
        f'Your request for {reservation.resource_label} on {describe_time(reservation)} '
        'was not reviewed in time and has been released. It does not count as a missed '
        'reservation.',
        level=Notification.Level.WARNING, link=reservation_link(reservation),
    )
    log_activity(
        'reservation.expired',
        f'Request by {reservation.student.full_name} for {reservation.resource_label} '
        f'expired without a decision ({reservation.code}).',
        target=reservation,
    )


def check_in(reservation, *, actor):
    policy = get_policy()
    now = timezone.now()
    expired = False
    with transaction.atomic():
        reservation = _locked(reservation)
        staff = actor.is_library_staff  # includes Student Assistants
        if not staff:
            if reservation.student_id != actor.pk:
                raise PermissionDenied('You can only check in to your own reservations.')
            if not policy.allow_self_checkin:
                raise ApiError('Please check in at the librarian desk.',
                               code='self_checkin_disabled')
        if reservation.status == Status.PENDING:
            raise ApiError('This request has not been approved by the librarian yet.',
                           code='not_approved')
        if reservation.status != Status.CONFIRMED:
            raise ApiError(
                f'This reservation is {reservation.get_status_display().lower()} '
                'and cannot be checked in.',
                code='invalid_status',
            )
        opens = checkin_opens_at(reservation, policy)
        if now < opens:
            raise ApiError(
                f'Check-in opens at {timezone.localtime(opens):%I:%M %p}.'.replace(' 0', ' '),
                code='too_early',
            )
        if now >= checkin_deadline(reservation, policy):
            # Too late: release the place now rather than waiting for the sweep.
            _apply_no_show(reservation, now)
            expired = True
        else:
            reservation.status = Status.CHECKED_IN
            reservation.checked_in_at = now
            reservation.checked_in_by = actor
            reservation.save(update_fields=[
                'status', 'checked_in_at', 'checked_in_by', 'updated_at'])
            end = timezone.localtime(reservation.end_at)
            notify(
                reservation.student, 'Checked in',
                f'You are checked in to {reservation.resource_label} until '
                f'{end:%I:%M %p}.'.replace(' 0', ' '),
                level=Notification.Level.SUCCESS, link=reservation_link(reservation),
            )
            log_activity(
                'reservation.checked_in',
                f'{reservation.student.full_name} checked in to {reservation.resource_label} '
                f'({reservation.code}).',
                actor=actor, target=reservation,
            )
    if expired:
        raise ApiError(
            'The 15-minute check-in period has ended, so this reservation was cancelled.',
            code='checkin_closed',
        )
    return reservation


def _apply_complete(reservation, checked_out_at):
    reservation.status = Status.COMPLETED
    reservation.checked_out_at = checked_out_at
    reservation.save(update_fields=['status', 'checked_out_at', 'updated_at'])
    _release_slots(reservation)


def check_out(reservation, *, actor):
    now = timezone.now()
    with transaction.atomic():
        reservation = _locked(reservation)
        if not actor.is_library_staff and reservation.student_id != actor.pk:
            raise PermissionDenied('You can only check out of your own reservations.')
        if reservation.status != Status.CHECKED_IN:
            raise ApiError('Only a checked-in reservation can be checked out.',
                           code='invalid_status')
        _apply_complete(reservation, min(now, reservation.end_at))
        log_activity(
            'reservation.checked_out',
            f'{reservation.student.full_name} checked out of {reservation.resource_label} '
            f'({reservation.code}).',
            actor=actor, target=reservation,
        )
    return reservation


def mark_no_show(reservation, *, actor):
    """Librarian/admin: release a reservation whose student has not arrived."""
    if not actor.can_manage_reservations:
        raise PermissionDenied('Only a librarian can record a no-show.')
    now = timezone.now()
    with transaction.atomic():
        reservation = _locked(reservation)
        if reservation.status != Status.CONFIRMED:
            raise ApiError('Only a confirmed reservation can be marked as a no-show.',
                           code='invalid_status')
        if now < reservation.start_at:
            raise ApiError('This reservation has not started yet. Cancel it instead.',
                           code='too_early')
        _apply_no_show(reservation, now, actor=actor)
    return reservation


# ── Automatic lifecycle ────────────────────────────────────────────────────

def process_due_reservations(now=None):
    """
    Apply everything that happens because time passed:

    * requests still pending when their check-in period ends expire,
    * confirmed reservations whose check-in period ended become no-shows,
    * checked-in reservations whose end time passed are completed,
    * reminders are sent for reservations about to start.

    Safe to call as often as you like; it only touches rows that are due.
    """
    now = now or timezone.now()
    policy = get_policy()
    result = {'expired': 0, 'no_shows': 0, 'completed': 0, 'reminders': 0}

    overdue_start = now - timedelta(minutes=policy.checkin_grace_minutes)
    started = Reservation.objects.filter(
        status__in=(Status.PENDING, Status.CONFIRMED), start_at__lte=overdue_start)
    for pk in list(started.values_list('pk', flat=True)):
        with transaction.atomic():
            reservation = Reservation.objects.select_for_update().get(pk=pk)
            if checkin_deadline(reservation, policy) > now:
                continue
            if reservation.status == Status.PENDING:
                _apply_expire(reservation, now)
                result['expired'] += 1
            elif reservation.status == Status.CONFIRMED:
                _apply_no_show(reservation, now)
                result['no_shows'] += 1

    finished = Reservation.objects.filter(status=Status.CHECKED_IN, end_at__lte=now)
    for pk in list(finished.values_list('pk', flat=True)):
        with transaction.atomic():
            reservation = Reservation.objects.select_for_update().get(pk=pk)
            if reservation.status == Status.CHECKED_IN:
                _apply_complete(reservation, reservation.end_at)
                result['completed'] += 1

    if policy.reminder_minutes:
        lead = timedelta(minutes=policy.reminder_minutes)
        due = Reservation.objects.filter(
            status=Status.CONFIRMED, reminder_sent_at__isnull=True,
            start_at__gt=now, start_at__lte=now + lead,
        ).select_related('student', 'seat', 'room')
        for reservation in due:
            # Claim the reminder first, so two server processes cannot both send it.
            claimed = Reservation.objects.filter(
                pk=reservation.pk, reminder_sent_at__isnull=True,
            ).update(reminder_sent_at=now)
            if not claimed:
                continue
            # No reminder for a booking made inside the reminder window.
            if reservation.created_at <= reservation.start_at - lead:
                start = timezone.localtime(reservation.start_at)
                notify(
                    reservation.student, 'Your reservation starts soon',
                    f'{reservation.resource_label} starts at '
                    f'{start:%I:%M %p}. Remember to check in.'.replace(' 0', ' '),
                    level=Notification.Level.WARNING, link=reservation_link(reservation),
                )
                result['reminders'] += 1

    return result
