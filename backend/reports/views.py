from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from activity.models import ActivityLog
from activity.serializers import ActivityLogSerializer
from config.exceptions import ApiError
from config.permissions import IsAdmin, IsLibraryStaff, IsStudent
from library.services import get_policy, local_today
from reservations.availability import occupancy_now
from reservations.models import Reservation
from reservations.serializers import ReservationSerializer
from reservations.services import checkin_opens_at, no_show_count

from . import selectors

Status = Reservation.Status
ACTIVE = Reservation.ACTIVE_STATUSES


def _serialize(request, reservations):
    return ReservationSerializer(reservations, many=True, context={'request': request}).data


class StudentDashboardView(APIView):
    permission_classes = [IsStudent]

    def get(self, request):
        user = request.user
        now = timezone.now()
        policy = get_policy()
        mine = selectors.reservation_queryset().filter(student=user)

        active = list(mine.filter(status__in=ACTIVE, end_at__gt=now).order_by('start_at'))
        # "Current" = already checked in, or check-in is open right now.
        current = next(
            (r for r in active
             if r.status == Status.CHECKED_IN or checkin_opens_at(r, policy) <= now),
            None,
        )
        upcoming = [r for r in active if r is not current]
        strikes = no_show_count(user, policy, now)
        counts = selectors.status_counts(Reservation.objects.filter(student=user))

        return Response({
            'current': _serialize(request, [current])[0] if current else None,
            'upcoming': _serialize(request, upcoming[:5]),
            'recent': _serialize(
                request, mine.exclude(status__in=ACTIVE).order_by('-start_at')[:5]),
            'stats': {
                **counts,
                'upcoming': len(active),
                'hours_studied': selectors.hours_used(Reservation.objects.filter(student=user)),
            },
            'limits': {
                'active_reservations': len(active),
                'max_active_reservations': policy.max_active_reservations,
                'no_shows': strikes,
                'no_show_limit': policy.no_show_limit,
                'no_show_window_days': policy.no_show_window_days,
                'suspended': bool(policy.no_show_limit and strikes >= policy.no_show_limit),
            },
            'library': selectors.library_today(),
            'occupancy': occupancy_now(now),
        })


class StaffDashboardView(APIView):
    """The librarian's operational view of today."""

    permission_classes = [IsLibraryStaff]

    def get(self, request):
        now = timezone.now()
        today_start, today_end = selectors.day_bounds(local_today())
        queryset = selectors.reservation_queryset()
        today = queryset.filter(start_at__gte=today_start, start_at__lt=today_end)

        recent = ActivityLog.objects.select_related('actor').filter(
            category=ActivityLog.Category.RESERVATION)[:10]

        return Response({
            'library': selectors.library_today(),
            'occupancy': occupancy_now(now),
            'today': selectors.status_counts(today),
            'checked_in': _serialize(
                request, queryset.filter(status=Status.CHECKED_IN).order_by('end_at')[:20]),
            # Started but nobody has arrived yet: needs a check-in or becomes a no-show.
            'awaiting_check_in': _serialize(
                request,
                queryset.filter(status=Status.CONFIRMED, start_at__lte=now)
                .order_by('start_at')[:20]),
            'upcoming': _serialize(
                request,
                today.filter(status=Status.CONFIRMED, start_at__gt=now)
                .order_by('start_at')[:10]),
            'recent_activity': ActivityLogSerializer(recent, many=True).data,
        })


class AdminDashboardView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        report = selectors.period_report(14)
        month = selectors.period_report(30)
        recent = ActivityLog.objects.select_related('actor')[:10]
        return Response({
            'library': selectors.library_today(),
            'totals': selectors.system_totals(),
            'occupancy': occupancy_now(),
            'trend': report['daily'],
            'last_30_days': month['totals'],
            'top_seats': month['top_seats'][:5],
            'top_rooms': month['top_rooms'][:5],
            'recent_activity': ActivityLogSerializer(recent, many=True).data,
        })


class ReportView(APIView):
    """Usage report for a period. Available to all library staff."""

    permission_classes = [IsLibraryStaff]
    ALLOWED_DAYS = (7, 14, 30, 90)

    def get(self, request):
        try:
            days = int(request.query_params.get('days', 30))
        except ValueError as exc:
            raise ApiError('`days` must be a number.', code='invalid_days') from exc
        if days not in self.ALLOWED_DAYS:
            raise ApiError('`days` must be 7, 14, 30 or 90.', code='invalid_days')
        return Response(selectors.period_report(days))
