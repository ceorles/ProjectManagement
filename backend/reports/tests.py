from config.test_utils import MONDAY, PortalTestCase, at, frozen_time
from reservations import services


class DashboardTests(PortalTestCase):
    def test_dashboards_are_restricted_by_role(self):
        allowed = {
            '/api/reports/student-dashboard/': {self.student},
            '/api/reports/staff-dashboard/': {self.librarian, self.admin},
            '/api/reports/admin-dashboard/': {self.admin},
            '/api/reports/usage/': {self.librarian, self.admin},
        }
        for url, users in allowed.items():
            for user in (self.student, self.librarian, self.admin):
                self.login_as(user)
                expected = 200 if user in users else 403
                self.assertEqual(self.client.get(url).status_code, expected, (url, user.role))

    def test_student_dashboard_reflects_their_reservations(self):
        with frozen_time(at(hour=9)):
            self.book_seat(start_hour=11)
            self.book_seat(start_hour=15)
            self.book_seat(student=self.other_student, seat=self.seat2, start_hour=11)
        self.login_as(self.student)
        with frozen_time(at(hour=10, minute=55)):
            data = self.client.get('/api/reports/student-dashboard/').data
        self.assertEqual(data['current']['start_time'], '11:00')  # check-in is open
        self.assertEqual([r['start_time'] for r in data['upcoming']], ['15:00'])
        self.assertEqual(data['stats']['upcoming'], 2)
        self.assertEqual(data['limits']['active_reservations'], 2)
        self.assertTrue(data['library']['open_now'])
        self.assertEqual(data['occupancy']['seats']['total'], 2)

    def test_staff_dashboard_shows_live_occupancy(self):
        with frozen_time(at(hour=9)):
            first = self.book_seat(start_hour=11)
            self.book_seat(student=self.other_student, seat=self.seat2, start_hour=11)
        with frozen_time(at(hour=11, minute=5)):
            services.check_in(first, actor=self.student)
            self.login_as(self.librarian)
            data = self.client.get('/api/reports/staff-dashboard/').data
        self.assertEqual(data['occupancy']['seats']['occupied'], 1)
        self.assertEqual(data['occupancy']['seats']['reserved'], 1)
        self.assertEqual(data['occupancy']['seats']['available'], 0)
        self.assertEqual(len(data['checked_in']), 1)
        self.assertEqual(len(data['awaiting_check_in']), 1)
        self.assertEqual(data['today']['total'], 2)

    def test_usage_report_counts_by_day_and_status(self):
        with frozen_time(at(hour=9)):
            kept = self.book_seat(start_hour=11)
            dropped = self.book_seat(student=self.other_student, seat=self.seat2, start_hour=11)
            services.cancel_reservation(dropped, actor=self.other_student)
        with frozen_time(at(hour=11)):
            services.check_in(kept, actor=self.student)
        with frozen_time(at(hour=12, minute=30)):
            services.process_due_reservations()
            self.login_as(self.admin)
            data = self.client.get('/api/reports/usage/', {'days': 7}).data
            dashboard = self.client.get('/api/reports/admin-dashboard/').data
        self.assertEqual(data['totals']['total'], 2)
        self.assertEqual(data['totals']['completed'], 1)
        self.assertEqual(data['totals']['cancelled'], 1)
        self.assertEqual(data['totals']['cancellation_rate'], 50.0)
        self.assertEqual(data['totals']['hours_used'], 1.0)
        self.assertEqual(data['daily'][-1]['date'], MONDAY.isoformat())
        self.assertEqual(data['daily'][-1]['total'], 2)
        self.assertEqual(data['top_seats'], [{'label': 'Seat A01', 'count': 1}])
        self.assertEqual(dashboard['totals']['students'], 2)
        self.assertEqual(len(dashboard['trend']), 14)

    def test_usage_report_rejects_unknown_periods(self):
        self.login_as(self.admin)
        self.assertEqual(self.client.get('/api/reports/usage/', {'days': 5}).status_code, 400)
