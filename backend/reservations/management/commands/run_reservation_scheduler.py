from django.conf import settings
from django.core.management.base import BaseCommand

from reservations.scheduler import run_forever


class Command(BaseCommand):
    help = (
        'Run the reservation scheduler as its own process (no-shows, completions, reminders). '
        'Not needed normally: it already runs inside the web server.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval', type=int, default=settings.RESERVATION_SCHEDULER_INTERVAL_SECONDS,
            help='Seconds between runs.')

    def handle(self, *args, **options):
        self.stdout.write(f'Reservation scheduler running every {options["interval"]} seconds. '
                          'Press Ctrl+C to stop.')
        try:
            run_forever(options['interval'])
        except KeyboardInterrupt:
            self.stdout.write('Stopped.')
