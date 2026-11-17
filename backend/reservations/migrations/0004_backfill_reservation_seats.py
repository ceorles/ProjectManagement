from django.db import migrations


def backfill(apps, schema_editor):
    """
    Seat reservations used to point at exactly one seat. They can now cover
    several, listed in ReservationSeat. Give every existing seat reservation
    its one row there, so old and new reservations are read the same way.
    """
    Reservation = apps.get_model('reservations', 'Reservation')
    ReservationSeat = apps.get_model('reservations', 'ReservationSeat')
    existing = set(ReservationSeat.objects.values_list('reservation_id', flat=True))
    rows = [
        ReservationSeat(reservation_id=reservation_id, seat_id=seat_id)
        for reservation_id, seat_id in Reservation.objects
        .filter(seat__isnull=False).values_list('pk', 'seat_id')
        if reservation_id not in existing
    ]
    ReservationSeat.objects.bulk_create(rows, batch_size=500)


class Migration(migrations.Migration):

    dependencies = [
        ('reservations', '0003_library_revision'),
    ]

    operations = [
        migrations.RunPython(backfill, migrations.RunPython.noop),
    ]
