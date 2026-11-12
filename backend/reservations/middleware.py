import logging

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

SWEEP_KEY = 'reservations:lifecycle-sweep'


class ReservationLifecycleMiddleware:
    """
    Keeps reservation statuses current without a background worker.

    Before an API request is handled, reservations that are due are marked as
    no-shows or completed, at most once every few seconds. Whoever looks at
    the data next therefore always sees it up to date. For a busy production
    deployment the same job can run on a schedule instead:
    `python manage.py process_reservations`.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/api/') and request.method != 'OPTIONS':
            # cache.add only succeeds when the key is absent, so concurrent
            # requests do not all run the sweep.
            if cache.add(SWEEP_KEY, True, settings.RESERVATION_SWEEP_INTERVAL_SECONDS):
                try:
                    from .services import process_due_reservations
                    process_due_reservations()
                except Exception:  # never let housekeeping break a request
                    logger.exception('Reservation lifecycle sweep failed')
        return self.get_response(request)
