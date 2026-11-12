from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from library.models import Floor, ResourceStatus


class Facility(models.Model):
    """Equipment a room can offer (whiteboard, projector, ...)."""

    name = models.CharField(max_length=60, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'facilities'

    def __str__(self):
        return self.name


class StudyRoom(models.Model):
    name = models.CharField(max_length=80)
    code = models.CharField(max_length=12, unique=True, help_text='Room number, e.g. SR-201.')
    floor = models.ForeignKey(Floor, on_delete=models.PROTECT, related_name='study_rooms')
    capacity = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)])
    min_occupancy = models.PositiveSmallIntegerField(
        default=1, validators=[MinValueValidator(1)],
        help_text='Smallest group that may book this room.')
    description = models.TextField(blank=True)
    facilities = models.ManyToManyField(Facility, blank=True, related_name='rooms')
    status = models.CharField(
        max_length=20, choices=ResourceStatus.choices, default=ResourceStatus.ACTIVE)
    status_note = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['floor__level', 'code']
        indexes = [models.Index(fields=['status'])]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(min_occupancy__lte=models.F('capacity')),
                name='room_min_occupancy_within_capacity',
            ),
        ]

    def __str__(self):
        return f'{self.name} ({self.code})'

    def clean(self):
        if self.min_occupancy and self.capacity and self.min_occupancy > self.capacity:
            raise ValidationError(
                {'min_occupancy': 'Minimum group size cannot exceed the capacity.'})

    @property
    def location_label(self):
        return self.floor.name
