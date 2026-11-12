from django.conf import settings
from django.db import models


class Notification(models.Model):
    """An in-app message for one user, shown in the notification bell."""

    class Level(models.TextChoices):
        INFO = 'info', 'Info'
        SUCCESS = 'success', 'Success'
        WARNING = 'warning', 'Warning'
        DANGER = 'danger', 'Important'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications'
    )
    level = models.CharField(max_length=10, choices=Level.choices, default=Level.INFO)
    title = models.CharField(max_length=120)
    message = models.CharField(max_length=400)
    # Path inside the frontend to open when the notification is clicked.
    link = models.CharField(max_length=200, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']
        indexes = [models.Index(fields=['user', 'is_read', '-created_at'])]

    def __str__(self):
        return f'{self.user}: {self.title}'
