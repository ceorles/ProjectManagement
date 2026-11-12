from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from library.models import Floor, ResourceStatus


class Zone(models.Model):
    """
    A named seating area on a floor (for example "Quiet Zone A"). Its seats
    are arranged on a rows x cols grid, which is what the seat map draws.
    """

    class ZoneType(models.TextChoices):
        QUIET = 'quiet', 'Quiet study'
        GENERAL = 'general', 'General study'
        COLLABORATIVE = 'collaborative', 'Collaborative'
        COMPUTER = 'computer', 'Computer area'

    floor = models.ForeignKey(Floor, on_delete=models.PROTECT, related_name='zones')
    name = models.CharField(max_length=60)
    zone_type = models.CharField(max_length=20, choices=ZoneType.choices, default=ZoneType.GENERAL)
    description = models.CharField(max_length=200, blank=True)
    rows = models.PositiveSmallIntegerField(
        default=4, validators=[MinValueValidator(1), MaxValueValidator(20)])
    cols = models.PositiveSmallIntegerField(
        default=6, validators=[MinValueValidator(1), MaxValueValidator(20)])

    class Meta:
        ordering = ['floor__level', 'name']
        constraints = [
            models.UniqueConstraint(fields=['floor', 'name'], name='unique_zone_name_per_floor'),
        ]

    def __str__(self):
        return f'{self.name} ({self.floor.name})'


class Seat(models.Model):
    zone = models.ForeignKey(Zone, on_delete=models.PROTECT, related_name='seats')
    number = models.CharField(max_length=12, unique=True, help_text='Label shown on the seat.')
    # 1-based position on the zone grid.
    row = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    col = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    has_power_outlet = models.BooleanField(default=False)
    has_computer = models.BooleanField(default=False)
    near_window = models.BooleanField(default=False)
    is_accessible = models.BooleanField(default=False, help_text='Wheelchair accessible.')
    status = models.CharField(
        max_length=20, choices=ResourceStatus.choices, default=ResourceStatus.ACTIVE)
    status_note = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['zone', 'row', 'col']
        constraints = [
            models.UniqueConstraint(fields=['zone', 'row', 'col'], name='unique_seat_position'),
        ]
        indexes = [models.Index(fields=['zone', 'status'])]

    def __str__(self):
        return f'Seat {self.number}'

    @property
    def location_label(self):
        return f'{self.zone.name}, {self.zone.floor.name}'
