"""
Fill the database with demonstration data.

    python manage.py seed_demo

Sets up the real library layout (see `library/layout.py`), creates demo
accounts for every role, three weeks of reservation history (so the reports
have something to show) and a few reservations and pending requests for
today. Safe to run more than once: anything that already exists is left alone.
"""
import random
from datetime import datetime, time, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from config.exceptions import ApiError
from library.layout import apply_library_layout
from library.models import Floor, ResourceStatus
from library.services import get_day_schedule, get_policy, local_now, local_today
from reservations import services
from reservations.models import Reservation, ReservationSeat
from reservations.windows import SLOT_MINUTES, build_window
from seats.models import Seat
from study_rooms.models import Facility, StudyRoom
from users.models import User

DEFAULT_PASSWORD = 'LibraryDemo#2026'

STAFF = [
    ('admin@library.edu', 'Alex', 'Reyes', User.Role.ADMIN, False),
    ('librarian@library.edu', 'Maria', 'Santos', User.Role.LIBRARIAN, True),
    ('librarian2@library.edu', 'Jose', 'Garcia', User.Role.LIBRARIAN, False),
    ('assistant@library.edu', 'Carla', 'Reyes', User.Role.ASSISTANT, False),
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
GROUP_REASONS = [
    'Group study for our midterm exam', 'Thesis group meeting', 'Capstone project work',
    'Review session with classmates',
]


class Command(BaseCommand):
    help = 'Set up the library layout and create demo accounts and sample reservations.'

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

        layout = apply_library_layout()
        if any(layout.values()):
            self.stdout.write(f'Library layout updated: { {k: v for k, v in layout.items() if v} }')
        with transaction.atomic():
            staff, students = self._accounts(password)
            self._room()

        if not options['no_history']:
            # History is generated once for the current seats. Reservations on
            # retired seats are left exactly as they are.
            on_current_seats = Reservation.objects.filter(
                reservation_seats__seat__is_archived=False).exists()
            if on_current_seats:
                self.stdout.write('Reservations already exist: history not generated.')
            else:
                with transaction.atomic():
                    history = self._history(students, staff[1])
                self.stdout.write(f'Created {history} past reservations.')
            # Live reservations are added whenever the library is open and
            # nothing is in progress, so the command can be re-run on the day
            # of a demonstration to populate the seat map.
            if Reservation.objects.filter(status__in=Reservation.ACTIVE_STATUSES).exists():
                self.stdout.write('Active reservations already exist: none added for today.')
            else:
                live = self._live(students, staff[1])
                self.stdout.write(f'Created {live} reservations and requests for right now.')

        self.stdout.write(self.style.SUCCESS('\nDemo data is ready.'))
        self.stdout.write(
            f'Layout: {", ".join(Floor.objects.values_list("name", flat=True))} | '
            f'{Seat.objects.filter(has_computer=False).count()} seats at '
            f'{Seat.objects.exclude(table_number=None).values("table_number").distinct().count()} '
            f'tables | {Seat.objects.filter(has_computer=True).count()} computers | '
            f'{StudyRoom.objects.count()} study room')
        self.stdout.write(f'\nDemo accounts (password for newly created ones: {password})')
        self.stdout.write('  Admin              admin@library.edu')
        self.stdout.write('  Librarian          librarian@library.edu   (may manage seats)')
        self.stdout.write('  Librarian          librarian2@library.edu')
        self.stdout.write('  Student Assistant  assistant@library.edu')
        self.stdout.write('  Student            student1@university.edu ... student24@university.edu')

    # ── Accounts ───────────────────────────────────────────────────────────

    def _accounts(self, password):
        staff = []
        for email, first, last, role, manage in STAFF:
            user = User.objects.filter(email=email).first()
            if user is None:
                user = User.objects.create_user(
                    email=email, password=password, first_name=first, last_name=last,
                    role=role, can_manage_resources=manage,
                    student_id='2022-00900' if role == User.Role.ASSISTANT else None,
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

    def _room(self):
        """The library's one room, if the database does not have it yet."""
        if StudyRoom.objects.exists():
            return
        room = StudyRoom.objects.create(
            code='SR-101', name='Study Room', floor=Floor.objects.first(), capacity=6,
            min_occupancy=2, description='The library\'s study room for small group work.')
        room.facilities.set([
            Facility.objects.get_or_create(name=name)[0]
            for name in ('Whiteboard', 'Power outlets', 'Air conditioning')
        ])

    # ── Past reservations (for history and reports) ────────────────────────

    def _history(self, students, librarian):
        seats = list(Seat.objects.filter(status=ResourceStatus.ACTIVE, has_computer=False))
        computers = list(Seat.objects.filter(status=ResourceStatus.ACTIVE, has_computer=True))
        rooms = list(StudyRoom.objects.filter(status=ResourceStatus.ACTIVE))
        if not seats:
            return 0
        by_table = {}
        for seat in seats:
            by_table.setdefault(seat.table_number, []).append(seat)

        today = local_today()
        policy = get_policy()
        # Never push a student over the no-show limit, counting what they already have.
        no_shows = {
            student.pk: services.no_show_count(student, policy) for student in students}
        records = []  # (Reservation, [seats])

        for days_ago in range(21, 0, -1):
            day = today - timedelta(days=days_ago)
            schedule = get_day_schedule(day)
            if not schedule.is_open:
                continue
            open_minutes = schedule.opens_at.hour * 60 + schedule.opens_at.minute
            close_minutes = schedule.closes_at.hour * 60 + schedule.closes_at.minute
            busy = set()  # (kind, id, slot) already used on this day

            for _ in range(self.rng.randint(24, 40)):
                student = self.rng.choice(students)
                roll = self.rng.random()
                room = self.rng.choice(rooms) if rooms and roll < 0.08 else None
                reason = ''
                if room:
                    chosen = []
                    slots = self.rng.choice([2, 2, 3, 4])
                    reason = self.rng.choice(['Group project', 'Thesis meeting', 'Exam review'])
                elif roll < 0.20 and computers:
                    chosen = [self.rng.choice(computers)]
                    slots = self.rng.choice([1, 2, 2])
                elif roll < 0.32:
                    # A group at one table: three to six chairs, with a reason.
                    table = self.rng.choice(list(by_table.values()))
                    chosen = table[:self.rng.choice([3, 4, 6, 6])]
                    slots = self.rng.choice([2, 3, 4])
                    reason = self.rng.choice(GROUP_REASONS)
                else:
                    table = self.rng.choice(list(by_table.values()))
                    chosen = self.rng.sample(table, self.rng.choice([1, 1, 1, 2]))
                    slots = self.rng.choice([1, 2, 2, 3, 4, 6])
                latest = (close_minutes - open_minutes) // SLOT_MINUTES - slots
                if latest < 0:
                    continue
                # Weight towards late morning and mid-afternoon.
                first = min(latest, max(0, int(self.rng.triangular(0, latest, latest * 0.45))))
                wanted = range(first, first + slots)
                keys = [('u', student.pk, slot) for slot in wanted]
                keys += [('r', room.pk, slot) for slot in wanted] if room else [
                    ('s', seat.pk, slot) for seat in chosen for slot in wanted]
                if any(key in busy for key in keys):
                    continue
                busy.update(keys)

                start = timezone.make_aware(datetime.combine(day, time.min)) + timedelta(
                    minutes=open_minutes + first * SLOT_MINUTES)
                end = start + timedelta(minutes=slots * SLOT_MINUTES)
                created = start - timedelta(hours=self.rng.randint(2, 40))
                outcome = self.rng.random()
                # Showcase accounts (the first four) keep a clean record.
                may_miss = student not in students[:4] and no_shows[student.pk] < 2
                extra = {'decided_by': librarian, 'decided_at': created + timedelta(minutes=20)}
                if outcome < 0.05:
                    status = Reservation.Status.REJECTED
                    extra['decision_note'] = self.rng.choice(
                        ['The area is reserved for an event', 'Please request fewer seats'])
                elif outcome < 0.11 and may_miss:
                    status = Reservation.Status.NO_SHOW
                    no_shows[student.pk] += 1
                elif outcome < 0.24:
                    status = Reservation.Status.CANCELLED
                    extra.update(
                        cancelled_at=start - timedelta(hours=1), cancelled_by=student,
                        cancel_reason=self.rng.choice(
                            ['Change of plans', 'Class was rescheduled', '', 'Not feeling well']))
                else:
                    status = Reservation.Status.COMPLETED
                    extra.update(
                        checked_in_at=start + timedelta(minutes=self.rng.randint(-5, 12)),
                        checked_in_by=student,
                        checked_out_at=end - timedelta(minutes=self.rng.choice([0, 0, 0, 10, 20])))

                records.append((Reservation(
                    code=services.generate_code(), student=student,
                    resource_type='room' if room else 'seat',
                    seat=chosen[0] if chosen else None, room=room,
                    start_at=start, end_at=end, status=status, created_by=student,
                    participant_count=(
                        self.rng.randint(room.min_occupancy, room.capacity) if room
                        else len(chosen)),
                    purpose=reason, **extra,
                ), chosen, created))

        # Codes are random; make sure the batch has no duplicates.
        seen = set()
        for reservation, _, _ in records:
            while reservation.code in seen:
                reservation.code = services.generate_code()
            seen.add(reservation.code)

        created = Reservation.objects.bulk_create([record[0] for record in records])
        for reservation, (_, _, created_at) in zip(created, records):
            reservation.created_at = created_at
        Reservation.objects.bulk_update(created, ['created_at'])
        ReservationSeat.objects.bulk_create([
            ReservationSeat(reservation=reservation, seat=seat)
            for reservation, (_, chosen, _) in zip(created, records) for seat in chosen
        ])
        return len(created)

    # ── Today: bookings and requests made through the real services ────────

    def _live(self, students, librarian):
        """
        Seats in use right now (booked and checked in by the librarian), and a
        few student requests still waiting for approval.
        """
        now = local_now()
        schedule = get_day_schedule(now.date())
        if not schedule.is_open:
            self.stdout.write('The library is closed today: no current reservations created.')
            return 0

        slot_start = now.replace(
            minute=now.minute - now.minute % SLOT_MINUTES, second=0, microsecond=0)
        seats = list(Seat.objects.filter(
            status=ResourceStatus.ACTIVE, has_computer=False).order_by('?')[:12])
        computers = list(Seat.objects.filter(status=ResourceStatus.ACTIVE, has_computer=True))
        tables = {}
        for seat in Seat.objects.filter(status=ResourceStatus.ACTIVE).exclude(table_number=None):
            tables.setdefault(seat.table_number, []).append(seat)
        created = 0

        def book(actor, student, chosen, start, slots, check_in=False, reason=''):
            nonlocal created
            end = start + timedelta(minutes=slots * SLOT_MINUTES)
            if start.time() < schedule.opens_at or end.time() > schedule.closes_at \
                    or end.date() != start.date():
                return
            try:
                reservation = services.create_reservation(
                    actor=actor, student=student, resource_type='seat',
                    seat_ids=[seat.pk for seat in chosen], purpose=reason,
                    window=build_window(start.date(), start.time(), end.time()))
                if check_in:
                    services.check_in(reservation, actor=librarian)
                created += 1
            except ApiError:
                pass  # a rule said no (limits, overlap, ...): skip this sample

        # Skip the four showcase students so they start with a clean slate.
        pool = students[4:]
        for index, seat in enumerate(seats[:8]):
            book(librarian, pool[index], [seat], slot_start, self.rng.choice([2, 3, 4]),
                 check_in=index < 6)
        if computers:
            book(librarian, pool[8], [computers[0]], slot_start, 2, check_in=True)

        # Requests waiting for the librarian (made by the students themselves).
        later = slot_start + timedelta(minutes=2 * SLOT_MINUTES)
        if len(seats) > 9:
            book(pool[10], pool[10], [seats[9]], later, 2)
        if len(computers) > 1:
            book(pool[11], pool[11], [computers[1]], later, 2)
        whole_table = next((group for group in tables.values()
                            if len(group) == 6 and not set(group) & set(seats)), None)
        if whole_table:
            book(pool[12], pool[12], whole_table, later, 3, reason=self.rng.choice(GROUP_REASONS))
        return created
