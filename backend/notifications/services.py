from .models import Notification


def notify(user, title, message, *, level=Notification.Level.INFO, link=''):
    """Create an in-app notification for one user."""
    return Notification.objects.create(
        user=user, title=title[:120], message=message[:400], level=level, link=link
    )


def notify_many(users, title, message, *, level=Notification.Level.INFO, link=''):
    Notification.objects.bulk_create([
        Notification(user=user, title=title[:120], message=message[:400], level=level, link=link)
        for user in users
    ])
