from activity.models import ActivityLog
from config.test_utils import PortalTestCase, at, frozen_time


class ActivityLogTests(PortalTestCase):
    def test_reservation_actions_are_logged(self):
        with frozen_time(at(hour=9)):
            reservation = self.book_seat()
        entry = ActivityLog.objects.get(action='reservation.created')
        self.assertEqual(entry.actor, self.student)
        self.assertEqual(entry.category, 'reservation')
        self.assertEqual(entry.target_id, reservation.pk)

    def test_only_admin_can_read_the_audit_trail(self):
        with frozen_time(at(hour=9)):
            self.book_seat()
            for user in (self.student, self.librarian):
                self.login_as(user)
                self.assertEqual(self.client.get('/api/activity/').status_code, 403)
            self.login_as(self.admin)
            response = self.client.get('/api/activity/', {'category': 'reservation'})
            self.assertEqual(response.data['count'], 1)
            self.assertEqual(response.data['results'][0]['actor_name'], 'Sam Student')
            self.assertEqual(
                self.client.get('/api/activity/', {'category': 'settings'}).data['count'], 0)
