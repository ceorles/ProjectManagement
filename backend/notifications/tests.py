from config.test_utils import PortalTestCase
from notifications.models import Notification
from notifications.services import notify


class NotificationTests(PortalTestCase):
    def setUp(self):
        super().setUp()
        self.mine = notify(self.student, 'Hello', 'For the student')
        self.theirs = notify(self.other_student, 'Hello', 'For someone else')

    def test_user_only_sees_their_own_notifications(self):
        self.login_as(self.student)
        response = self.client.get('/api/notifications/')
        self.assertEqual([n['id'] for n in response.data['results']], [self.mine.pk])
        self.assertEqual(self.client.get('/api/notifications/unread-count/').data['unread'], 1)

    def test_user_cannot_touch_another_users_notification(self):
        self.login_as(self.student)
        self.assertEqual(
            self.client.post(f'/api/notifications/{self.theirs.pk}/read/').status_code, 404)
        self.assertEqual(
            self.client.delete(f'/api/notifications/{self.theirs.pk}/').status_code, 404)
        self.theirs.refresh_from_db()
        self.assertFalse(self.theirs.is_read)

    def test_mark_read_and_read_all(self):
        notify(self.student, 'Second', 'Another one')
        self.login_as(self.student)
        self.client.post(f'/api/notifications/{self.mine.pk}/read/')
        self.assertEqual(self.client.get('/api/notifications/unread-count/').data['unread'], 1)
        self.assertEqual(self.client.post('/api/notifications/read-all/').data['updated'], 1)
        self.assertFalse(Notification.objects.filter(user=self.student, is_read=False).exists())
        # The other student's notification is untouched.
        self.assertTrue(
            Notification.objects.filter(user=self.other_student, is_read=False).exists())
