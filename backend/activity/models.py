from django.conf import settings
from django.db import models


class ActivityLog(models.Model):
    """Audit trail of who did what. Rows are written once and never edited."""

    class Category(models.TextChoices):
        AUTH = 'auth', 'Authentication'
        USER = 'user', 'Accounts'
        RESERVATION = 'reservation', 'Reservations'
        RESOURCE = 'resource', 'Seats and rooms'
        SETTINGS = 'settings', 'Library settings'

    # Null actor = the system itself (for example an automatic no-show).
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='activity_logs',
    )
    category = models.CharField(max_length=20, choices=Category.choices)
    action = models.CharField(max_length=60)
    description = models.CharField(max_length=255)
    target_type = models.CharField(max_length=40, blank=True)
    target_id = models.PositiveBigIntegerField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']
        indexes = [
            models.Index(fields=['category', '-created_at']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f'{self.action}: {self.description}'
