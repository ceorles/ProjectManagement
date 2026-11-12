from config.test_utils import PortalTestCase, at, frozen_time
from reservations.models import Reservation
from study_rooms.models import Facility


class StudyRoomManagementTests(PortalTestCase):
    def payload(self, **overrides):
        data = {'name': 'Study Room 2', 'code': 'sr-2', 'floor': self.floor.pk,
                'capacity': 6, 'min_occupancy': 2}
        data.update(overrides)
        return data

    def test_students_can_browse_rooms_and_facilities(self):
        Facility.objects.create(name='Whiteboard')
        self.login_as(self.student)
        self.assertEqual(self.client.get('/api/study-rooms/').data['count'], 1)
        self.assertEqual(len(self.client.get('/api/study-rooms/facilities/').data), 1)

    def test_admin_can_create_a_room_with_facilities(self):
        self.login_as(self.admin)
        facility = self.client.post('/api/study-rooms/facilities/', {'name': 'Projector'})
        self.assertEqual(facility.status_code, 201)
        response = self.client.post(
            '/api/study-rooms/', self.payload(facilities=[facility.data['id']]))
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['code'], 'SR-2')
        self.assertEqual(response.data['facility_details'][0]['name'], 'Projector')

    def test_room_validation(self):
        self.login_as(self.admin)
        too_big = self.client.post('/api/study-rooms/', self.payload(min_occupancy=9))
        self.assertIn('min_occupancy', too_big.data['error']['fields'])
        duplicate = self.client.post('/api/study-rooms/', self.payload(code='SR-1'))
        self.assertIn('code', duplicate.data['error']['fields'])

    def test_only_resource_managers_can_change_rooms(self):
        for user in (self.student, self.librarian):
            self.login_as(user)
            self.assertEqual(
                self.client.post('/api/study-rooms/', self.payload()).status_code, 403)
            self.assertEqual(
                self.client.post(f'/api/study-rooms/{self.room.pk}/set-status/',
                                 {'status': 'inactive'}).status_code, 403)

    def test_taking_a_room_out_of_service_cancels_reservations(self):
        with frozen_time(at(hour=9)):
            reservation = self.book_room()
            self.login_as(self.admin)
            response = self.client.post(
                f'/api/study-rooms/{self.room.pk}/set-status/',
                {'status': 'maintenance', 'note': 'Aircon repair'})
        self.assertEqual(response.data['cancelled_reservations'], 1)
        self.assertEqual(response.data['status_note'], 'Aircon repair')
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Reservation.Status.CANCELLED)
