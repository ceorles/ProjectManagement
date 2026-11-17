from django.core.management.base import BaseCommand

from library.layout import apply_library_layout
from library.models import Floor
from seats.models import Seat, Zone
from study_rooms.models import StudyRoom


class Command(BaseCommand):
    help = (
        'Set the seating up as it is in the real library: First Floor only, a Reading Hall '
        'with 15 tables of 6 chairs (90 seats) and a Computer Area with 4 computers. '
        'Anything else is archived (kept for history, hidden everywhere). Safe to re-run.'
    )

    def handle(self, *args, **options):
        summary = apply_library_layout()
        changed = {key: value for key, value in summary.items() if value}
        self.stdout.write(f'Changes made: {changed or "none (already up to date)"}')
        for zone in Zone.objects.select_related('floor'):
            seats = Seat.objects.filter(zone=zone)
            tables = seats.exclude(table_number=None).values('table_number').distinct().count()
            detail = f'{tables} tables, ' if tables else ''
            self.stdout.write(f'  {zone.name} ({zone.floor.name}): {detail}{seats.count()} seats')
        self.stdout.write(
            f'  Floors: {", ".join(Floor.objects.values_list("name", flat=True))} | '
            f'Study rooms: {StudyRoom.objects.count()}')
        self.stdout.write(self.style.SUCCESS('Library layout is in place.'))
