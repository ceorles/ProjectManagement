from datetime import time

from django.db import migrations


def create_defaults(apps, schema_editor):
    """Every installation starts with opening hours and a booking policy."""
    OperatingHours = apps.get_model('library', 'OperatingHours')
    ReservationPolicy = apps.get_model('library', 'ReservationPolicy')

    for weekday in range(7):
        saturday, sunday = weekday == 5, weekday == 6
        OperatingHours.objects.get_or_create(
            weekday=weekday,
            defaults={
                'is_open': not sunday,
                'opens_at': time(8, 0),
                'closes_at': time(17, 0) if saturday or sunday else time(20, 0),
            },
        )
    ReservationPolicy.objects.get_or_create(pk=1)


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0002_initial'),
    ]

    operations = [
        migrations.RunPython(create_defaults, migrations.RunPython.noop),
    ]
