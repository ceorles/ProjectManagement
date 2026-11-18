from django.db import migrations
from django.utils import timezone

REASON = 'The library room is a common space and can no longer be reserved.'


def retire_rooms(apps, schema_editor):
    """
    Rooms can no longer be reserved. Anything still open on a room is cancelled
    and its student told; past room reservations stay on record untouched.
    """
    Reservation = apps.get_model('reservations', 'Reservation')
    ReservationSlot = apps.get_model('reservations', 'ReservationSlot')
    Notification = apps.get_model('notifications', 'Notification')
    StudyRoom = apps.get_model('study_rooms', 'StudyRoom')

    now = timezone.now()
    still_open = Reservation.objects.filter(
        resource_type='room', status__in=['pending', 'confirmed', 'checked_in'])
    for reservation in still_open:
        Notification.objects.create(
            user_id=reservation.student_id, level='warning',
            title='Your reservation was cancelled', message=REASON,
            link=f'/reservations/{reservation.pk}',
        )
        ReservationSlot.objects.filter(reservation=reservation).delete()
    still_open.update(status='cancelled', cancelled_at=now, cancel_reason=REASON)
    StudyRoom.objects.update(is_archived=True)


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0002_initial'),
        ('reservations', '0004_backfill_reservation_seats'),
        ('study_rooms', '0002_library_revision'),
    ]

    operations = [
        migrations.RunPython(retire_rooms, migrations.RunPython.noop),
    ]
