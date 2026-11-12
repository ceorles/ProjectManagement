from django.conf import settings
from django.db import models
from django.db.models import Q

from seats.models import Seat
from study_rooms.models import StudyRoom


class Reservation(models.Model):
    """
    A booking of one seat or one study room by one student for a time window.

    Status flow:

        CONFIRMED --check in--> CHECKED_IN --check out / end time--> COMPLETED
            |-- cancelled by student or staff ----------------------> CANCELLED
            |-- not checked in before the grace period ends --------> NO_SHOW

    CONFIRMED and CHECKED_IN are the "active" statuses: only they hold the
    resource. Every other status has released it.
    """

    class ResourceType(models.TextChoices):
        SEAT = 'seat', 'Seat'
        ROOM = 'room', 'Study room'

    class Status(models.TextChoices):
        CONFIRMED = 'confirmed', 'Confirmed'
        CHECKED_IN = 'checked_in', 'Checked in'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
        NO_SHOW = 'no_show', 'No-show'

    ACTIVE_STATUSES = (Status.CONFIRMED, Status.CHECKED_IN)

    # Short human-friendly reference, also used as the check-in code.
    code = models.CharField(max_length=10, unique=True, editable=False)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='reservations')
    resource_type = models.CharField(max_length=10, choices=ResourceType.choices)
    seat = models.ForeignKey(
        Seat, null=True, blank=True, on_delete=models.PROTECT, related_name='reservations')
    room = models.ForeignKey(
        StudyRoom, null=True, blank=True, on_delete=models.PROTECT, related_name='reservations')
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.CONFIRMED)
    participant_count = models.PositiveSmallIntegerField(default=1)
    purpose = models.CharField(max_length=200, blank=True)

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

    @property
    def resource_label(self):
        if self.resource_type == self.ResourceType.SEAT:
            return f'Seat {self.seat.number}'
        return self.room.name

    @property
    def is_active(self):
        return self.status in self.ACTIVE_STATUSES


class ReservationSlot(models.Model):
    """
    The double-booking guard.

    An active reservation owns one row here for every 30-minute slot it
    covers. The unique constraints make it impossible, at database level, for
    two active reservations to hold the same seat or room in the same slot,
    or for one student to hold two places at once. Rows are deleted the
    moment a reservation stops being active, which frees the slots.
    """

    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='slots')
    seat = models.ForeignKey(Seat, null=True, blank=True, on_delete=models.CASCADE,
                             related_name='+')
    room = models.ForeignKey(StudyRoom, null=True, blank=True, on_delete=models.CASCADE,
                             related_name='+')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='+')
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
