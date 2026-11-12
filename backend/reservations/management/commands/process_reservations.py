from django.core.management.base import BaseCommand

from reservations.services import process_due_reservations


class Command(BaseCommand):
    help = (
        'Mark overdue reservations as no-shows, complete finished ones and send '
        'reminders. Schedule it every minute in production (cron / Task Scheduler).'
    )

    def handle(self, *args, **options):
        result = process_due_reservations()
        self.stdout.write(self.style.SUCCESS(
            f"No-shows: {result['no_shows']}, completed: {result['completed']}, "
            f"reminders: {result['reminders']}"
        ))
