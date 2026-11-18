"""
Runs the reservation lifecycle on a timer, on the server.

Every 30 seconds (RESERVATION_SCHEDULER_INTERVAL_SECONDS) it cancels confirmed
reservations nobody checked in to, expires unreviewed requests, completes
finished reservations and sends reminders. It needs no browser and no visitor.

It starts by itself with the web server (`config/wsgi.py` and `config/asgi.py`),
so `python manage.py runserver`, waitress or gunicorn all include it. Anything
missed while the server was off is processed on the first run after it starts.

To run it as its own process instead, set RESERVATION_SCHEDULER_ENABLED=False
and run `python manage.py run_reservation_scheduler`.

Running several copies at once is safe: each reservation is re-checked inside a
locked transaction, so it is only ever processed, and notified about, once.
"""
import logging
import sys
import threading

from django.conf import settings
from django.db import close_old_connections
from django.utils import timezone

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_thread = None
_last_run = None
_last_error = None


def run_once():
    """One pass. Errors are logged, and the next pass simply tries again."""
    global _last_run, _last_error
    from .services import process_due_reservations

    close_old_connections()
    try:
        result = process_due_reservations()
    except Exception as exc:  # e.g. the database is briefly busy
        _last_error = str(exc)
        logger.exception('Reservation scheduler pass failed')
        return None
    finally:
        close_old_connections()
    _last_run = timezone.now()
    _last_error = None
    if any(result.values()):
        logger.info('Reservation scheduler: %s', result)
    return result


def run_forever(interval=None, stop=None):
    """Run a pass now, then one every `interval` seconds until `stop` is set."""
    interval = interval or settings.RESERVATION_SCHEDULER_INTERVAL_SECONDS
    stop = stop or threading.Event()
    while not stop.is_set():
        run_once()
        stop.wait(interval)


def start_background_scheduler():
    """Start the timer inside this server process (once). Returns True if started."""
    global _thread
    if not settings.RESERVATION_SCHEDULER_ENABLED or 'test' in sys.argv:
        return False
    with _lock:
        if _thread is not None and _thread.is_alive():
            return False
        _thread = threading.Thread(
            target=run_forever, name='reservation-scheduler', daemon=True)
        _thread.start()
    return True


def scheduler_status():
    """Shown by /api/health/, to confirm the scheduler is really running."""
    return {
        'running': bool(_thread is not None and _thread.is_alive()),
        'interval_seconds': settings.RESERVATION_SCHEDULER_INTERVAL_SECONDS,
        'last_run': _last_run,
        'last_error': _last_error,
    }
