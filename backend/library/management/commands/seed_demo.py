"""
Fill an empty database with demonstration data.

    python manage.py seed_demo

Creates demo accounts for every role, a three-floor library layout, study
rooms, three weeks of reservation history (so the reports have something to
show) and a few live reservations for today. Safe to run more than once:
anything that already exists is left alone.
"""
import random
from datetime import datetime, time, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from config.exceptions import ApiError
from library.models import Floor, ResourceStatus
from library.services import get_day_schedule, local_now, local_today
from reservations import services
from reservations.models import Reservation
from reservations.windows import SLOT_MINUTES, build_window
from seats.models import Seat, Zone
from study_rooms.models import Facility, StudyRoom
from users.models import User

DEFAULT_PASSWORD = 'LibraryDemo#2026'

STAFF = [
    ('admin@library.edu', 'Alex', 'Reyes', User.Role.ADMIN, False),
    ('librarian@library.edu', 'Maria', 'Santos', User.Role.LIBRARIAN, True),
    ('librarian2@library.edu', 'Jose', 'Garcia', User.Role.LIBRARIAN, False),
]

FIRST_NAMES = [
    'Andrea', 'Miguel', 'Sofia', 'Daniel', 'Bianca', 'Carlo', 'Jasmine', 'Paolo', 'Nicole',
    'Rafael', 'Camille', 'Joshua', 'Patricia', 'Gabriel', 'Angela', 'Marco', 'Kristine',
    'Luis', 'Hannah', 'Vincent', 'Erika', 'Adrian', 'Trisha', 'Kevin',
]
LAST_NAMES = [
    'Cruz', 'Dela Cruz', 'Mendoza', 'Ramos', 'Flores', 'Villanueva', 'Castillo', 'Navarro',
    'Aquino', 'Bautista', 'Domingo', 'Salazar', 'Torres', 'Lim', 'Pascual', 'Rivera',
    'Soriano', 'Valdez', 'Tan', 'Morales', 'Gonzales', 'Fernandez', 'Marquez', 'Santiago',
]
PROGRAMS = [
    'BS Information Technology', 'BS Computer Science', 'BS Accountancy',
    'BS Psychology', 'BS Civil Engineering', 'BS Nursing', 'BA Communication',
]

# name, level
FLOORS = [('Ground Floor', 0), ('Second Floor', 1), ('Third Floor', 2)]

# floor level, name, type, prefix, rows, cols, aisle columns, aisle rows, description
ZONES = [
    (0, 'Reading Hall', 'general', 'A', 5, 11, {4, 8}, {3},
     'Open tables near the main entrance and the circulation desk.'),
    (0, 'Computer Area', 'computer', 'C', 3, 8, set(), {2},
     'Desktop workstations with internet access.'),
    (1, 'Quiet Zone East', 'quiet', 'Q', 5, 9, {5}, {3},
     'Silent individual study. No calls or group discussions.'),
    (1, 'Quiet Zone West', 'quiet', 'W', 4, 8, {3, 6}, set(),
     'Silent study carrels beside the periodicals section.'),
    (2, 'Collaborative Commons', 'collaborative', 'L', 5, 10, {3, 6, 9}, {3},
     'Group tables where quiet conversation is welcome.'),
]

FACILITIES = ['Whiteboard', 'Projector', 'TV display', 'Video conferencing',
              'Power outlets', 'Air conditioning', 'HDMI cable']

# code, name, floor level, capacity, min group, facilities, description
ROOMS = [
    ('SR-201', 'Study Room 201', 1, 4, 2, ['Whiteboard', 'Power outlets', 'Air conditioning'],
     'A small room for pair work and quick group reviews.'),
    ('SR-202', 'Study Room 202', 1, 6, 2,
     ['Whiteboard', 'TV display', 'HDMI cable', 'Power outlets', 'Air conditioning'],
     'Mid-sized room with a wall display for sharing slides.'),
    ('SR-203', 'Focus Room 203', 1, 2, 1, ['Power outlets', 'Air conditioning'],
     'A compact room for one or two people who need privacy for interviews or exams.'),
    ('SR-301', 'Discussion Room 301', 2, 10, 3,
     ['Whiteboard', 'Projector', 'Video conferencing', 'Power outlets', 'Air conditioning'],
     'Large room for project meetings, thesis consultations and presentations.'),
    ('SR-302', 'Study Room 302', 2, 6, 2, ['Whiteboard', 'Power outlets', 'Air conditioning'],
     'Bright corner room beside the Collaborative Commons.'),
    ('SR-303', 'Media Room 303', 2, 8, 2,
     ['TV display', 'Video conferencing', 'HDMI cable', 'Power outlets', 'Air conditioning'],
     'Equipped for video calls and recording group presentations.'),
]


class Command(BaseCommand):
    help = 'Create demo accounts, a library layout and sample reservations.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--password', default=DEFAULT_PASSWORD,
            help='Password given to every demo account that gets created.')
        parser.add_argument(
            '--no-history', action='store_true',
            help='Skip generating past and current reservations.')

    def handle(self, *args, **options):
        self.rng = random.Random(2026)
        password = options['password']

        with transaction.atomic():
            staff, students = self._accounts(password)
            created_layout = self._layout()
        if not options['no_history']:
            if Reservation.objects.exists():
                self.stdout.write('Reservations already exist: history not generated.')
            else:
                with transaction.atomic():
                    history = self._history(students)
                self.stdout.write(f'Created {history} past reservations.')
            # Live reservations are added whenever the library is open and
            # nothing is in progress, so the command can be re-run on the day
            # of a demonstration to populate the seat map.
            if Reservation.objects.filter(status__in=Reservation.ACTIVE_STATUSES).exists():
                self.stdout.write('Active reservations already exist: none added for today.')
            else:
                live = self._live(students, staff[1])
                self.stdout.write(f'Created {live} reservations for right now.')

        self.stdout.write(self.style.SUCCESS('\nDemo data is ready.'))
        if created_layout:
            self.stdout.write(
                f'Layout: {Floor.objects.count()} floors, {Zone.objects.count()} zones, '
                f'{Seat.objects.count()} seats, {StudyRoom.objects.count()} study rooms.')
        self.stdout.write('\nDemo accounts (password for newly created ones: '
                          f'{password})')
        self.stdout.write('  Admin      admin@library.edu')
        self.stdout.write('  Librarian  librarian@library.edu   (may manage seats and rooms)')
        self.stdout.write('  Librarian  librarian2@library.edu  (reservations only)')
        self.stdout.write('  Student    student1@university.edu ... student24@university.edu')

    # ── Accounts ───────────────────────────────────────────────────────────

    def _accounts(self, password):
        staff = []
        for email, first, last, role, manage in STAFF:
            user = User.objects.filter(email=email).first()
            if user is None:
                user = User.objects.create_user(
                    email=email, password=password, first_name=first, last_name=last,
                    role=role, can_manage_resources=manage,
                    is_staff=role == User.Role.ADMIN, is_superuser=role == User.Role.ADMIN,
                )
            staff.append(user)

        students = []
        for index, first in enumerate(FIRST_NAMES, start=1):
            email = f'student{index}@university.edu'
            user = User.objects.filter(email=email).first()
            if user is None:
                user = User.objects.create_user(
                    email=email, password=password, first_name=first,
                    last_name=LAST_NAMES[index - 1], role=User.Role.STUDENT,
                    student_id=f'{2021 + index % 4}-{1000 + index:05d}',
                    program=PROGRAMS[index % len(PROGRAMS)],
                    year_level=1 + index % 4,
                )
            students.append(user)
        return staff, students

    # ── Floors, zones, seats, rooms ────────────────────────────────────────

    def _layout(self):
        if Floor.objects.exists():
            self.stdout.write('A library layout already exists: not creating another.')
            return False

        floors = {level: Floor.objects.create(name=name, level=level) for name, level in FLOORS}

        for level, name, zone_type, prefix, rows, cols, aisle_cols, aisle_rows, text in ZONES:
            zone = Zone.objects.create(
                floor=floors[level], name=name, zone_type=zone_type,
                description=text, rows=rows, cols=cols)
            number = 0
            seats = []
            for row in range(1, rows + 1):
                if row in aisle_rows:
                    continue
                for col in range(1, cols + 1):
                    if col in aisle_cols:
                        continue
                    number += 1
                    seats.append(Seat(
                        zone=zone, number=f'{prefix}{number:02d}', row=row, col=col,
                        has_power_outlet=zone_type == 'computer' or (row + col) % 2 == 0,
                        has_computer=zone_type == 'computer',
                        near_window=col in (1, cols),
                        is_accessible=row == 1 and col <= 2,
                    ))
            Seat.objects.bulk_create(seats)

        # Two seats out of service, so the map shows the "unavailable" state.
        Seat.objects.filter(number='A07').update(
            status=ResourceStatus.MAINTENANCE, status_note='Broken chair - awaiting repair.')
        Seat.objects.filter(number='C05').update(
            status=ResourceStatus.MAINTENANCE, status_note='Computer being re-imaged.')

        facilities = {name: Facility.objects.create(name=name) for name in FACILITIES}
        for code, name, level, capacity, minimum, items, text in ROOMS:
            room = StudyRoom.objects.create(
                code=code, name=name, floor=floors[level], capacity=capacity,
                min_occupancy=minimum, description=text)
            room.facilities.set([facilities[item] for item in items])
        StudyRoom.objects.filter(code='SR-303').update(
            status=ResourceStatus.MAINTENANCE,
            status_note='Display being replaced. Back next week.')
        return True

    # ── Past reservations (for history and reports) ────────────────────────

    def _history(self, students):
        seats = list(Seat.objects.filter(status=ResourceStatus.ACTIVE))
        rooms = list(StudyRoom.objects.filter(status=ResourceStatus.ACTIVE))
        if not seats or not rooms:
            return 0

        today = local_today()
        no_shows = {student.pk: 0 for student in students}
        reservations = []

        for days_ago in range(21, 0, -1):
            day = today - timedelta(days=days_ago)
            schedule = get_day_schedule(day)
            if not schedule.is_open:
                continue
            open_minutes = schedule.opens_at.hour * 60 + schedule.opens_at.minute
            close_minutes = schedule.closes_at.hour * 60 + schedule.closes_at.minute
            busy = set()  # (kind, id, slot) already used on this day

            for _ in range(self.rng.randint(26, 44)):
                student = self.rng.choice(students)
                is_room = self.rng.random() < 0.22
                resource = self.rng.choice(rooms if is_room else seats)
                slots = self.rng.choice([2, 2, 3, 4] if is_room else [1, 2, 2, 3, 4, 6])
                latest = (close_minutes - open_minutes) // SLOT_MINUTES - slots
                if latest < 0:
                    continue
                # Weight towards late morning and mid-afternoon.
                first = min(latest, max(0, int(self.rng.triangular(0, latest, latest * 0.45))))
                wanted = range(first, first + slots)
                keys = (
                    [('r' if is_room else 's', resource.pk, slot) for slot in wanted]
                    + [('u', student.pk, slot) for slot in wanted]
                )
                if any(key in busy for key in keys):
                    continue
                busy.update(keys)

                start = timezone.make_aware(datetime.combine(day, time.min)) + timedelta(
                    minutes=open_minutes + first * SLOT_MINUTES)
                end = start + timedelta(minutes=slots * SLOT_MINUTES)
                roll = self.rng.random()
                # Showcase accounts (the first four) keep a clean record.
                may_miss = student not in students[:4] and no_shows[student.pk] < 2
                extra = {}
                if roll < 0.08 and may_miss:
                    status = Reservation.Status.NO_SHOW
                    no_shows[student.pk] += 1
                elif roll < 0.22:
                    status = Reservation.Status.CANCELLED
                    extra = {
                        'cancelled_at': start - timedelta(hours=self.rng.randint(1, 20)),
                        'cancelled_by': student,
                        'cancel_reason': self.rng.choice(
                            ['Change of plans', 'Class was rescheduled', '', 'Not feeling well']),
                    }
                else:
                    status = Reservation.Status.COMPLETED
                    arrived = start + timedelta(minutes=self.rng.randint(-5, 12))
                    left = end - timedelta(minutes=self.rng.choice([0, 0, 0, 10, 20]))
                    extra = {'checked_in_at': arrived, 'checked_in_by': student,
                             'checked_out_at': left}

                capacity = resource.capacity if is_room else 1
                reservations.append(Reservation(
                    code=services.generate_code(), student=student,
                    resource_type='room' if is_room else 'seat',
                    seat=None if is_room else resource, room=resource if is_room else None,
                    start_at=start, end_at=end, status=status, created_by=student,
                    participant_count=(
                        self.rng.randint(resource.min_occupancy, capacity) if is_room else 1),
                    purpose=self.rng.choice(
                        ['Group project', 'Thesis meeting', 'Exam review', '']) if is_room else '',
                    **extra,
                ))

        # Codes are random; make sure the batch has no duplicates.
        seen = set()
        for reservation in reservations:
            while reservation.code in seen:
                reservation.code = services.generate_code()
            seen.add(reservation.code)

        created = Reservation.objects.bulk_create(reservations)
        for reservation in created:
            reservation.created_at = reservation.start_at - timedelta(
                hours=self.rng.randint(2, 40))
        Reservation.objects.bulk_update(created, ['created_at'])
        return len(created)

    # ── Reservations for today, made through the real booking service ──────

    def _live(self, students, librarian):
        """Book (and partly check in) a few seats and a room for right now."""
        now = local_now()
        schedule = get_day_schedule(now.date())
        if not schedule.is_open:
            self.stdout.write('The library is closed today: no current reservations created.')
            return 0

        slot_start = now.replace(
            minute=now.minute - now.minute % SLOT_MINUTES, second=0, microsecond=0)
        seats = list(Seat.objects.filter(status=ResourceStatus.ACTIVE).order_by('?')[:14])
        rooms = list(StudyRoom.objects.filter(status=ResourceStatus.ACTIVE))
        created = 0

        def book(student, resource_type, resource, start, slots, check_in=False, **kwargs):
            nonlocal created
            end = start + timedelta(minutes=slots * SLOT_MINUTES)
            if start.time() < schedule.opens_at or end.time() > schedule.closes_at \
                    or end.date() != start.date():
                return
            try:
                reservation = services.create_reservation(
                    actor=student, student=student, resource_type=resource_type,
                    resource_id=resource.pk,
                    window=build_window(start.date(), start.time(), end.time()), **kwargs)
                if check_in:
                    services.check_in(reservation, actor=librarian)
                created += 1
            except ApiError:
                pass  # a rule said no (limits, overlap, ...): skip this sample

        # Skip the four showcase students so they start with a clean slate.
        pool = students[4:]
        for index, seat in enumerate(seats[:10]):
            book(pool[index], 'seat', seat, slot_start, self.rng.choice([2, 3, 4]),
                 check_in=index < 7)
        for index, seat in enumerate(seats[10:]):
            book(pool[10 + index], 'seat', seat,
                 slot_start + timedelta(minutes=SLOT_MINUTES * (2 + index)), 2)
        if rooms:
            book(pool[15], 'room', rooms[0], slot_start, 2, check_in=True,
                 participant_count=rooms[0].min_occupancy, purpose='Group project')
        if len(rooms) > 1:
            book(pool[16], 'room', rooms[1], slot_start + timedelta(minutes=2 * SLOT_MINUTES), 2,
                 participant_count=rooms[1].min_occupancy, purpose='Thesis meeting')
        return created
