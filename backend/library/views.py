from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import Count
from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from activity.services import log_activity
from config.exceptions import ApiError
from config.permissions import CanManageResourcesOrReadOnly, IsAdminOrReadOnly

from .models import Closure, Floor, OperatingHours
from .serializers import (
    ClosureSerializer,
    FloorSerializer,
    FloorSummarySerializer,
    OperatingHoursSerializer,
    ReservationPolicySerializer,
)
from .services import ensure_operating_hours, get_policy, local_now, local_today


def _cancel_displaced_reservations(actor, reason):
    """Cancel upcoming reservations that no longer fit the library schedule."""
    # Imported here: the reservations app depends on library, not vice versa.
    from reservations.services import cancel_outside_schedule

    return cancel_outside_schedule(actor=actor, reason=reason)


class LibraryOverviewView(APIView):
    """Everything the booking screens need to know about the library, in one call."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        ensure_operating_hours()
        today = local_today()
        closures = Closure.objects.filter(
            date__gte=today, date__lte=today + timedelta(days=90)
        )
        return Response({
            'time_zone': settings.TIME_ZONE,
            'now': local_now().isoformat(),
            'today': today.isoformat(),
            'slot_minutes': settings.RESERVATION_SLOT_MINUTES,
            'hours': OperatingHoursSerializer(OperatingHours.objects.all(), many=True).data,
            'closures': ClosureSerializer(closures, many=True).data,
            'policy': ReservationPolicySerializer(get_policy()).data,
            'floors': FloorSummarySerializer(Floor.objects.all(), many=True).data,
        })


class OperatingHoursView(APIView):
    """GET the weekly hours; PUT (Admin) replaces all seven days at once."""

    permission_classes = [IsAdminOrReadOnly]

    def get(self, request):
        ensure_operating_hours()
        return Response(OperatingHoursSerializer(OperatingHours.objects.all(), many=True).data)

    def put(self, request):
        ensure_operating_hours()
        serializer = OperatingHoursSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        weekdays = [item['weekday'] for item in serializer.validated_data]
        if sorted(weekdays) != list(range(7)):
            raise ApiError('Send exactly one entry for each day of the week.',
                           code='invalid_hours')

        with transaction.atomic():
            for item in serializer.validated_data:
                OperatingHours.objects.filter(weekday=item['weekday']).update(
                    is_open=item['is_open'],
                    opens_at=item['opens_at'],
                    closes_at=item['closes_at'],
                )
            cancelled = _cancel_displaced_reservations(
                request.user, 'The library opening hours changed.'
            )
            log_activity('settings.hours_updated', 'Updated the library operating hours.',
                         actor=request.user, request=request)
        return Response({
            'hours': OperatingHoursSerializer(OperatingHours.objects.all(), many=True).data,
            'cancelled_reservations': cancelled,
        })


class ClosureViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = ClosureSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = None

    def get_queryset(self):
        queryset = Closure.objects.all()
        if self.request.query_params.get('include_past') != 'true':
            queryset = queryset.filter(date__gte=local_today())
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            closure = serializer.save(created_by=request.user)
            cancelled = _cancel_displaced_reservations(
                request.user, f'The library is closed on this date: {closure.reason}'
            )
            log_activity('settings.closure_added',
                         f'Scheduled a closure on {closure.date:%b %d, %Y} ({closure.reason}).',
                         actor=request.user, target=closure, request=request)
        data = self.get_serializer(closure).data
        data['cancelled_reservations'] = cancelled
        return Response(data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        log_activity('settings.closure_removed',
                     f'Removed the closure on {instance.date:%b %d, %Y}.',
                     actor=self.request.user, request=self.request)
        instance.delete()


class ReservationPolicyView(APIView):
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request):
        return Response(ReservationPolicySerializer(get_policy()).data)

    def patch(self, request):
        policy = get_policy()
        serializer = ReservationPolicySerializer(policy, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        log_activity('settings.policy_updated', 'Updated the reservation rules.',
                     actor=request.user, request=request)
        return Response(serializer.data)


class FloorViewSet(viewsets.ModelViewSet):
    serializer_class = FloorSerializer
    permission_classes = [CanManageResourcesOrReadOnly]
    pagination_class = None

    def get_queryset(self):
        return Floor.objects.annotate(
            seat_count=Count('zones__seats', distinct=True),
            room_count=Count('study_rooms', distinct=True),
        )

    def perform_create(self, serializer):
        floor = serializer.save()
        log_activity('resource.floor_created', f'Added floor "{floor.name}".',
                     actor=self.request.user, target=floor, request=self.request)

    def perform_update(self, serializer):
        floor = serializer.save()
        log_activity('resource.floor_updated', f'Updated floor "{floor.name}".',
                     actor=self.request.user, target=floor, request=self.request)

    def perform_destroy(self, instance):
        log_activity('resource.floor_deleted', f'Deleted floor "{instance.name}".',
                     actor=self.request.user, request=self.request)
        instance.delete()
