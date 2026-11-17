from django.conf import settings
from django.db import models
from django.db.models import Q

from seats.models import Seat
from study_rooms.models import StudyRoom


class Reservation(models.Model):
    """
    A request by one student for seats (one to six, e.g. a whole table), one
    computer, or the study room, for a time window.

    Status flow:

        PENDING --librarian approves--> CONFIRMED --check in--> CHECKED_IN
           |                               |                        |
           |-- librarian rejects           |-- cancelled            | check out,
           |     --> REJECTED              |     --> CANCELLED      | or end time
           |-- withdrawn, or not           |-- no check-in          v
               reviewed in time                  --> NO_SHOW     COMPLETED
                 --> CANCELLED

    A student's request always starts as PENDING. It is never CONFIRMED until
    a librarian has approved it.

    PENDING, CONFIRMED and CHECKED_IN are the "active" statuses: they hold the
    requested places, so nobody else can take them while a request is waiting.
    Every other status has released them.
    """

    class ResourceType(models.TextChoices):
        SEAT = 'seat', 'Seat'
        ROOM = 'room', 'Study room'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        CHECKED_IN = 'checked_in', 'Checked in'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
        REJECTED = 'rejected', 'Rejected'
        NO_SHOW = 'no_show', 'No-show'

    ACTIVE_STATUSES = (Status.PENDING, Status.CONFIRMED, Status.CHECKED_IN)

    # Short human-friendly reference, also used as the check-in code.
    code = models.CharField(max_length=10, unique=True, editable=False)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='reservations')
    resource_type = models.CharField(max_length=10, choices=ResourceType.choices)
    # For a seat reservation this is the first requested seat; the full list
    # (one to six seats) is in ReservationSeat.
    seat = models.ForeignKey(
        Seat, null=True, blank=True, on_delete=models.PROTECT, related_name='reservations')
    room = models.ForeignKey(
        StudyRoom, null=True, blank=True, on_delete=models.PROTECT, related_name='reservations')
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    participant_count = models.PositiveSmallIntegerField(default=1)
    # Purpose of a room booking, or the reason for requesting more than two seats.
    purpose = models.CharField(max_length=200, blank=True)

    # The librarian's decision on a student's request.
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='+')
    decided_at = models.DateTimeField(null=True, blank=True)
    decision_note = models.CharField(max_length=200, blank=True)

    # Who entered the booking: the student, or a staff member on their behalf.
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    checked_in_at = models.DateTimeField(null=True, blank=True)
    checked_in_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='+')
    checked_out_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='+')
    cancel_reason = models.CharField(max_length=200, blank=True)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-start_at', '-id']
        constraints = [
            models.CheckConstraint(
                condition=Q(end_at__gt=models.F('start_at')),
                name='reservation_ends_after_start',
            ),
            models.CheckConstraint(
                condition=(
                    Q(resource_type='seat', seat__isnull=False, room__isnull=True)
                    | Q(resource_type='room', room__isnull=False, seat__isnull=True)
                ),
                name='reservation_has_exactly_one_resource',
            ),
            models.CheckConstraint(
                condition=Q(participant_count__gte=1),
                name='reservation_has_participants',
            ),
        ]
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['status', 'start_at']),
            models.Index(fields=['seat', 'start_at']),
            models.Index(fields=['room', 'start_at']),
            models.Index(fields=['start_at']),
        ]

    def __str__(self):
        return f'{self.code} - {self.resource_label}'

    @property
    def resource(self):
        return self.seat if self.resource_type == self.ResourceType.SEAT else self.room

    def seat_list(self):
        """Every seat of a seat reservation, in seat-number order."""
        seats = [link.seat for link in self.reservation_seats.all()]
        if not seats and self.seat_id:
            seats = [self.seat]
        return sorted(seats, key=lambda seat: seat.number)

    @property
    def resource_label(self):
        if self.resource_type != self.ResourceType.SEAT:
            return self.room.name
        return describe_seats(self.seat_list())

    @property
    def is_active(self):
        return self.status in self.ACTIVE_STATUSES


def describe_seats(seats):
    """'Seat T03-2', 'Computer PC-1', 'Table 3 (6 seats)' or 'Seats T03-1, T03-2'."""
    if len(seats) == 1:
        seat = seats[0]
        return f'Computer {seat.number}' if seat.has_computer else f'Seat {seat.number}'
    tables = {seat.table_number for seat in seats}
    if len(tables) == 1 and None not in tables:
        table = tables.pop()
        whole = Seat.all_objects.filter(zone_id=seats[0].zone_id, table_number=table).count()
        if whole == len(seats):
            return f'Table {table} ({len(seats)} seats)'
    return 'Seats ' + ', '.join(seat.number for seat in seats)


class ReservationSeat(models.Model):
    """One seat of a seat reservation (a request may cover up to a whole table)."""

    reservation = models.ForeignKey(
        Reservation, on_delete=models.CASCADE, related_name='reservation_seats')
    seat = models.ForeignKey(Seat, on_delete=models.PROTECT, related_name='seat_reservations')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['reservation', 'seat'],
                                    name='unique_seat_per_reservation'),
        ]

    def __str__(self):
        return f'{self.reservation.code}: {self.seat.number}'


class ReservationSlot(models.Model):
    """
    The double-booking guard.

    An active reservation owns one row here for every 30-minute slot of every
    seat (or the room) it covers. The unique constraints make it impossible, at database level, for
    two active reservations to hold the same seat or room in the same slot,
    or for one student to hold two places at once. Rows are deleted the
    moment a reservation stops being active, which frees the slots.
    """

    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='slots')
    seat = models.ForeignKey(Seat, null=True, blank=True, on_delete=models.CASCADE,
                             related_name='+')
    room = models.ForeignKey(StudyRoom, null=True, blank=True, on_delete=models.CASCADE,
                             related_name='+')
    # Set on the rows of the first seat only, so that a request for several
    # seats does not collide with itself on the per-student constraint.
    student = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                on_delete=models.CASCADE, related_name='+')
    start_at = models.DateTimeField()

    class Meta:
        constraints = [
            # NULLs are distinct in a unique index, so seat rows do not clash
            # with room rows (where `seat` is NULL), and vice versa.
            models.UniqueConstraint(fields=['seat', 'start_at'], name='one_booking_per_seat_slot'),
            models.UniqueConstraint(fields=['room', 'start_at'], name='one_booking_per_room_slot'),
            models.UniqueConstraint(fields=['student', 'start_at'],
                                    name='one_booking_per_student_slot'),
        ]

    def __str__(self):
        return f'{self.reservation.code} @ {self.start_at:%Y-%m-%d %H:%M}'


class ReservationParticipant(models.Model):
    """A classmate invited to a study-room reservation."""

    reservation = models.ForeignKey(
        Reservation, on_delete=models.CASCADE, related_name='participants')
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='invitations')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['reservation', 'student'],
                                    name='unique_reservation_participant'),
        ]

    def __str__(self):
        return f'{self.student} in {self.reservation.code}'
