"""The command that sets the seating up as it is in the real library."""
from collections import Counter

from config.test_utils import PortalTestCase, at, frozen_time
from library.layout import apply_library_layout
from library.models import Floor
from reservations.models import Reservation
from seats.models import Seat, Zone
from study_rooms.models import StudyRoom
from users.models import User


class LibraryLayoutTests(PortalTestCase):
    """Starts from the fixtures' made-up layout, as an existing database would."""

    def setUp(self):
        super().setUp()
        self.second_floor = Floor.objects.create(name='Second Floor', level=1)
        self.old_zone = Zone.objects.create(
            floor=self.second_floor, name='Quiet Zone East', rows=1, cols=2)
        Seat.objects.create(zone=self.old_zone, number='Q01', row=1, col=1)
        StudyRoom.objects.create(
            name='Study Room 9', code='SR-9', floor=self.second_floor, capacity=4)
        with frozen_time(at(hour=9)):
            self.history = self.book_seat()          # on seat A01, to be retired
            self.upcoming = self.book_seat(  # on a seat of a retired zone too
                student=self.other_student, seat=self.seat2, start_hour=14)
        self.users_before = User.objects.count()
        with frozen_time(at(hour=9)):   # both bookings are still in the future
            apply_library_layout()

    def test_exactly_the_real_library_remains(self):
        self.assertEqual(list(Floor.objects.values_list('name', flat=True)), ['First Floor'])
        self.assertEqual(
            sorted(Zone.objects.values_list('name', flat=True)), ['Computer Area', 'Reading Hall'])
        hall = Zone.objects.get(name='Reading Hall')
        computers = Zone.objects.get(name='Computer Area')
        self.assertEqual(hall.floor.name, 'First Floor')
        self.assertEqual(computers.floor.name, 'First Floor')

        chairs = Seat.objects.filter(zone=hall)
        self.assertEqual(chairs.count(), 90)
        per_table = Counter(chairs.values_list('table_number', flat=True))
        self.assertEqual(sorted(per_table), list(range(1, 16)))      # tables 1..15
        self.assertEqual(set(per_table.values()), {6})               # six chairs each
        self.assertEqual(chairs.filter(has_computer=True).count(), 0)
        self.assertEqual(len(set(chairs.values_list('number', flat=True))), 90)
        self.assertTrue(chairs.filter(number='T01-1').exists())
        self.assertTrue(chairs.filter(number='T15-6').exists())
        # No two chairs share a position on the map.
        self.assertEqual(len(set(chairs.values_list('row', 'col'))), 90)

        pcs = Seat.objects.filter(zone=computers)
        self.assertEqual(sorted(pcs.values_list('number', flat=True)),
                         ['PC-1', 'PC-2', 'PC-3', 'PC-4'])
        self.assertEqual(pcs.filter(has_computer=True).count(), 4)
        self.assertEqual(Seat.objects.count(), 94)   # 90 chairs + 4 computers, nothing else

        self.assertEqual(StudyRoom.objects.count(), 0)   # no room is reservable

    def test_old_resources_are_archived_not_deleted_and_history_survives(self):
        self.assertTrue(Zone.all_objects.filter(name='Quiet Zone East (retired)').exists())
        self.assertTrue(Seat.all_objects.get(number='A01').is_archived)
        self.assertTrue(Floor.all_objects.get(name='Second Floor').is_archived)
        self.assertTrue(StudyRoom.all_objects.get(code='SR-9').is_archived)
        self.assertEqual(User.objects.count(), self.users_before)

        self.history.refresh_from_db()
        self.assertEqual(self.history.seat.number, 'A01')   # still readable
        # It was an upcoming booking on a seat that no longer exists: cancelled, kept.
        self.assertEqual(self.history.status, Reservation.Status.CANCELLED)
        self.upcoming.refresh_from_db()
        self.assertEqual(self.upcoming.status, Reservation.Status.CANCELLED)

    def test_retired_places_disappear_from_the_api(self):
        self.login_as(self.student)
        with frozen_time(at(hour=9)):
            self.assertEqual(len(self.client.get('/api/library/overview/').data['floors']), 1)
            zones = self.client.get('/api/seats/zones/').data
            self.assertEqual(sorted(zone['name'] for zone in zones),
                             ['Computer Area', 'Reading Hall'])
            self.assertEqual({zone['name']: zone['seat_count'] for zone in zones},
                             {'Reading Hall': 90, 'Computer Area': 4})
            self.assertEqual(self.client.get('/api/seats/', {'page_size': 200}).data['count'], 94)
            self.assertEqual(self.client.get('/api/study-rooms/').status_code, 404)
            availability = self.client.get(
                '/api/seats/availability/', {'date': '2026-03-02', 'start': '13:00', 'end': '14:00'})
            self.assertEqual(availability.data['summary']['total'], 94)
            # A retired seat can no longer be requested...
            old = Seat.all_objects.get(number='A02')
            response = self.client.post('/api/reservations/', {
                'resource_type': 'seat', 'seat': old.pk, 'date': '2026-03-02',
                'start_time': '15:00', 'end_time': '16:00'})
            self.assertEqual(response.status_code, 400)
            # ...but its past reservation can still be opened.
            detail = self.client.get(f'/api/reservations/{self.history.pk}/')
            self.assertEqual(detail.status_code, 200)
            self.assertEqual(detail.data['resource']['name'], 'Seat A01')
            self.login_as(self.admin)
            report = self.client.get('/api/reports/usage/', {'days': 7}).data
            self.assertEqual(report['by_zone'], [])
            self.assertEqual(report['top_seats'], [])

    def test_running_it_again_changes_nothing(self):
        ids = sorted(Seat.objects.values_list('pk', flat=True))
        summary = apply_library_layout()
        self.assertFalse(any(summary.values()), summary)
        self.assertEqual(sorted(Seat.objects.values_list('pk', flat=True)), ids)
        self.assertEqual(Seat.all_objects.count(), 94 + 11)  # 11 retired fixture seats kept
        # A retired seat that used a real seat number gave it up.
        self.assertEqual(Seat.all_objects.filter(number__startswith='T01-1').count(), 2)
