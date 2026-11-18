"""
The library as it actually is.

One floor (First Floor) with two areas:

* Reading Hall  - 15 tables, 6 chairs each = 90 seats
* Computer Area - 4 computers

The library's one room is a common space for everyone and is not reservable.

`apply_library_layout()` brings any database to exactly that. It is safe to
run more than once. Floors, zones, seats and rooms that are not part of the
real library are *archived*, never deleted, so reservation history survives.
"""
from django.db import transaction

from library.models import Floor
from seats.models import Seat, Zone
from study_rooms.models import StudyRoom

FLOOR_NAME = 'First Floor'
READING_HALL = 'Reading Hall'
COMPUTER_AREA = 'Computer Area'

TABLES = 15
SEATS_PER_TABLE = 6
COMPUTERS = 4

# Tables are drawn three across. Each table takes a block of 3 columns x 3
# rows on the map (chairs along the top and bottom, the table top between
# them), followed by an aisle.
TABLES_PER_ROW = 3
BLOCK = 4  # 3 cells of table + 1 aisle


def reading_hall_seats():
    """(number, table, row, col) for all 90 chairs: T01-1 ... T15-6."""
    seats = []
    for table in range(1, TABLES + 1):
        top = ((table - 1) // TABLES_PER_ROW) * BLOCK + 1
        left = ((table - 1) % TABLES_PER_ROW) * BLOCK + 1
        for chair in range(1, SEATS_PER_TABLE + 1):
            row = top if chair <= 3 else top + 2
            col = left + (chair - 1) % 3
            seats.append((f'T{table:02d}-{chair}', table, row, col))
    return seats


def _is_current(zone, expected, tables):
    """Whether a zone already holds exactly the seats the library has."""
    if zone is None:
        return False
    seats = list(zone.seats.all())
    numbers = {seat.number for seat in seats}
    return numbers == expected and (
        not tables or len({seat.table_number for seat in seats}) == TABLES)


def _retire_zone(zone, summary, reserved_numbers):
    from reservations.services import cancel_for_resource

    for seat in zone.seats.all():
        summary['reservations_cancelled'] += cancel_for_resource(
            seat, actor=None, reason='This seat is no longer part of the library layout.')
        if seat.number in reserved_numbers:
            # Seat numbers are unique. Hand this one over to the real seat.
            seat.number = f'{seat.number}~{seat.pk}'[:12]
            seat.save(update_fields=['number'])
    summary['seats_archived'] += Seat.objects.filter(zone=zone).update(is_archived=True)
    # Free the name so the real area can use it on the same floor.
    name = f'{zone.name} (retired)'
    if Zone.all_objects.filter(floor=zone.floor, name=name).exclude(pk=zone.pk).exists():
        name = f'{zone.name} (retired {zone.pk})'
    zone.name = name[:60]
    zone.is_archived = True
    zone.save(update_fields=['name', 'is_archived'])
    summary['zones_archived'] += 1


@transaction.atomic
def apply_library_layout():
    summary = {
        'floors_archived': 0, 'zones_archived': 0, 'seats_archived': 0, 'rooms_archived': 0,
        'seats_created': 0, 'reservations_cancelled': 0,
    }

    # ── One floor ────────────────────────────────────────────────────────────
    floor = Floor.objects.filter(name=FLOOR_NAME).first() or Floor.objects.order_by('level').first()
    if floor is None:
        floor = Floor.objects.create(name=FLOOR_NAME, level=0)
    elif floor.name != FLOOR_NAME:
        floor.name = FLOOR_NAME
        floor.save(update_fields=['name'])

    # ── Two areas with exactly the real seats ────────────────────────────────
    hall_numbers = {number for number, *_ in reading_hall_seats()}
    computer_numbers = {f'PC-{index}' for index in range(1, COMPUTERS + 1)}
    hall = Zone.objects.filter(floor=floor, name=READING_HALL).first()
    computers = Zone.objects.filter(floor=floor, name=COMPUTER_AREA).first()
    keep = set()
    if _is_current(hall, hall_numbers, tables=True):
        keep.add(hall.pk)
    if _is_current(computers, computer_numbers, tables=False):
        keep.add(computers.pk)

    for zone in Zone.objects.exclude(pk__in=keep):
        _retire_zone(zone, summary, hall_numbers | computer_numbers)

    if not (hall and hall.pk in keep):
        hall = Zone.objects.create(
            floor=floor, name=READING_HALL, zone_type=Zone.ZoneType.GENERAL,
            description='15 study tables with 6 chairs each.',
            rows=(TABLES // TABLES_PER_ROW) * BLOCK - 1, cols=TABLES_PER_ROW * BLOCK - 1)
        Seat.objects.bulk_create([
            Seat(zone=hall, number=number, table_number=table, row=row, col=col)
            for number, table, row, col in reading_hall_seats()
        ])
        summary['seats_created'] += TABLES * SEATS_PER_TABLE

    if not (computers and computers.pk in keep):
        computers = Zone.objects.create(
            floor=floor, name=COMPUTER_AREA, zone_type=Zone.ZoneType.COMPUTER,
            description='4 computers. One computer per student at a time.',
            rows=1, cols=COMPUTERS)
        Seat.objects.bulk_create([
            Seat(zone=computers, number=f'PC-{index}', row=1, col=index,
                 has_computer=True, has_power_outlet=True)
            for index in range(1, COMPUTERS + 1)
        ])
        summary['seats_created'] += COMPUTERS

    # ── Rooms are not reservable: keep them only for past reservations ───────
    summary['rooms_archived'] = StudyRoom.objects.update(is_archived=True)

    # ── Floors that do not exist ─────────────────────────────────────────────
    summary['floors_archived'] = Floor.objects.exclude(pk=floor.pk).update(is_archived=True)
    return summary
