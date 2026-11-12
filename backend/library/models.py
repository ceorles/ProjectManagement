from datetime import time

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

SLOT_MINUTES = settings.RESERVATION_SLOT_MINUTES


class ResourceStatus(models.TextChoices):
    """Shared by seats and study rooms."""

    ACTIVE = 'active', 'Available for booking'
    MAINTENANCE = 'maintenance', 'Under maintenance'
    INACTIVE = 'inactive', 'Out of service'


class Floor(models.Model):
    """A level of the library building. Seats (through zones) and rooms sit on one."""

    name = models.CharField(max_length=60, unique=True)
    level = models.SmallIntegerField(unique=True, help_text='0 = ground floor.')
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['level']

    def __str__(self):
        return self.name


class OperatingHours(models.Model):
    """Opening hours for one day of the week. Exactly seven rows exist."""

    class Weekday(models.IntegerChoices):
        MONDAY = 0, 'Monday'
        TUESDAY = 1, 'Tuesday'
        WEDNESDAY = 2, 'Wednesday'
        THURSDAY = 3, 'Thursday'
        FRIDAY = 4, 'Friday'
        SATURDAY = 5, 'Saturday'
        SUNDAY = 6, 'Sunday'

    weekday = models.PositiveSmallIntegerField(choices=Weekday.choices, unique=True)
    is_open = models.BooleanField(default=True)
    opens_at = models.TimeField(default=time(8, 0))
    closes_at = models.TimeField(default=time(20, 0))

    class Meta:
        ordering = ['weekday']
        verbose_name_plural = 'operating hours'

    def __str__(self):
        if not self.is_open:
            return f'{self.get_weekday_display()}: closed'
        return f'{self.get_weekday_display()}: {self.opens_at:%H:%M}-{self.closes_at:%H:%M}'

    def clean(self):
        for label, value in (('opens_at', self.opens_at), ('closes_at', self.closes_at)):
            if value.minute % SLOT_MINUTES or value.second:
                raise ValidationError({label: f'Use {SLOT_MINUTES}-minute steps.'})
        if self.is_open and self.opens_at >= self.closes_at:
            raise ValidationError({'closes_at': 'Closing time must be after opening time.'})


class Closure(models.Model):
    """A date the library is closed all day (holiday, event, repairs)."""

    date = models.DateField(unique=True)
    reason = models.CharField(max_length=120)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='+',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f'{self.date}: {self.reason}'


def _slot_multiple(value):
    if value % SLOT_MINUTES:
        raise ValidationError(f'Must be a multiple of {SLOT_MINUTES} minutes.')


class ReservationPolicy(models.Model):
    """The booking rules. A single row (pk=1) that the Admin edits."""

    min_duration_minutes = models.PositiveSmallIntegerField(
        default=30, validators=[MinValueValidator(SLOT_MINUTES), _slot_multiple])
    max_seat_duration_minutes = models.PositiveSmallIntegerField(
        default=240, validators=[MinValueValidator(SLOT_MINUTES), _slot_multiple])
    max_room_duration_minutes = models.PositiveSmallIntegerField(
        default=120, validators=[MinValueValidator(SLOT_MINUTES), _slot_multiple])
    max_advance_days = models.PositiveSmallIntegerField(
        default=7, validators=[MaxValueValidator(60)],
        help_text='How many days ahead a reservation can be made. 0 = same day only.')
    max_active_reservations = models.PositiveSmallIntegerField(
        default=3, validators=[MinValueValidator(1)],
        help_text='Upcoming or in-progress reservations a student may hold at once.')
    max_reservations_per_day = models.PositiveSmallIntegerField(
        default=2, validators=[MinValueValidator(1)])
    checkin_early_minutes = models.PositiveSmallIntegerField(
        default=10, validators=[MaxValueValidator(60)],
        help_text='How long before the start time check-in opens.')
    checkin_grace_minutes = models.PositiveSmallIntegerField(
        default=15, validators=[MinValueValidator(5), MaxValueValidator(120)],
        help_text='Minutes after the start time before a reservation becomes a no-show.')
    cancellation_cutoff_minutes = models.PositiveSmallIntegerField(
        default=0, validators=[MaxValueValidator(1440)],
        help_text='Students must cancel at least this long before the start time.')
    no_show_limit = models.PositiveSmallIntegerField(
        default=3, help_text='No-shows allowed before booking is suspended. 0 disables.')
    no_show_window_days = models.PositiveSmallIntegerField(
        default=30, validators=[MinValueValidator(1), MaxValueValidator(365)])
    reminder_minutes = models.PositiveSmallIntegerField(
        default=15, validators=[MaxValueValidator(240)],
        help_text='Send a reminder this long before the start time. 0 disables.')
    allow_self_checkin = models.BooleanField(
        default=True, help_text='Let students check themselves in from the app.')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'reservation policy'

    def __str__(self):
        return 'Reservation policy'

    def clean(self):
        for field in ('max_seat_duration_minutes', 'max_room_duration_minutes'):
            if getattr(self, field) < self.min_duration_minutes:
                raise ValidationError({field: 'Cannot be shorter than the minimum duration.'})

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('The reservation policy cannot be deleted.')

    @classmethod
    def load(cls):
        policy, _ = cls.objects.get_or_create(pk=1)
        return policy
