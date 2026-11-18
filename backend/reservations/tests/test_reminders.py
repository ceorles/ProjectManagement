"""A reminder is sent once, however many server processes run the sweep."""
from datetime import timedelta
from unittest import mock

from config.test_utils import MONDAY, PortalTestCase, at, frozen_time
from notifications.models import Notification
from reservations import services
from reservations.models import Reservation

TITLE = 'Your reservation starts soon'


class ReminderTests(PortalTestCase):
    def setUp(self):
        with frozen_time(at(MONDAY - timedelta(days=1), hour=10)):
            request = self.request_seats([self.seat], start_hour=10, hours=1)
            self.reservation = services.approve_reservation(request, actor=self.librarian)
        self.moment = at(hour=9, minute=55)

    def sweep(self):
        with frozen_time(self.moment):
            return services.process_due_reservations(self.moment)

    def sent(self):
        return Notification.objects.filter(title=TITLE).count()

    def test_repeated_sweeps_send_one_reminder(self):
        self.sweep()
        self.sweep()
        self.assertEqual(self.sent(), 1)

    def test_a_reminder_claimed_by_another_process_is_not_sent_again(self):
        real_notify = services.notify

        def other_process_got_there_first(*args, **kwargs):
            return real_notify(*args, **kwargs)

        Reservation.objects.filter(pk=self.reservation.pk).update(reminder_sent_at=self.moment)
        with mock.patch.object(services, 'notify', side_effect=other_process_got_there_first) as sent:
            self.sweep()
        sent.assert_not_called()
