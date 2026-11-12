from django.db import transaction
from django.db.models import Count, Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from activity.services import log_activity
from config.permissions import CanManageResourcesOrReadOnly
from library.models import ResourceStatus
from reservations import availability
from reservations.services import cancel_for_resource
from reservations.windows import parse_day, parse_window

from .models import Seat, Zone
from .serializers import ResourceStatusSerializer, SeatSerializer, ZoneSerializer


class ZoneViewSet(viewsets.ModelViewSet):
    serializer_class = ZoneSerializer
    permission_classes = [CanManageResourcesOrReadOnly]
    pagination_class = None

    def get_queryset(self):
        queryset = Zone.objects.select_related('floor').annotate(seat_count=Count('seats'))
        floor = self.request.query_params.get('floor')
        if floor:
            queryset = queryset.filter(floor_id=floor)
        return queryset

    def perform_create(self, serializer):
        zone = serializer.save()
        log_activity('resource.zone_created', f'Added zone "{zone.name}".',
                     actor=self.request.user, target=zone, request=self.request)

    def perform_update(self, serializer):
        zone = serializer.save()
        log_activity('resource.zone_updated', f'Updated zone "{zone.name}".',
                     actor=self.request.user, target=zone, request=self.request)

    def perform_destroy(self, instance):
        log_activity('resource.zone_deleted', f'Deleted zone "{instance.name}".',
                     actor=self.request.user, request=self.request)
        instance.delete()


class SeatViewSet(viewsets.ModelViewSet):
    serializer_class = SeatSerializer
    permission_classes = [CanManageResourcesOrReadOnly]

    def get_queryset(self):
        queryset = Seat.objects.select_related('zone__floor')
        params = self.request.query_params
        if params.get('zone'):
            queryset = queryset.filter(zone_id=params['zone'])
        if params.get('floor'):
            queryset = queryset.filter(zone__floor_id=params['floor'])
        if params.get('status'):
            queryset = queryset.filter(status=params['status'])
        search = params.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(number__icontains=search) | Q(zone__name__icontains=search))
        return queryset

    def perform_create(self, serializer):
        seat = serializer.save()
        log_activity('resource.seat_created', f'Added seat {seat.number}.',
                     actor=self.request.user, target=seat, request=self.request)

    def perform_update(self, serializer):
        seat = serializer.save()
        log_activity('resource.seat_updated', f'Updated seat {seat.number}.',
                     actor=self.request.user, target=seat, request=self.request)

    def perform_destroy(self, instance):
        # Seats with reservation history are protected by the database; the
        # API then answers 409 and suggests marking the seat inactive.
        number = instance.number
        instance.delete()
        log_activity('resource.seat_deleted', f'Deleted seat {number}.',
                     actor=self.request.user, request=self.request)

    @action(detail=True, methods=['post'], url_path='set-status')
    def set_status(self, request, pk=None):
        """Take a seat out of service or put it back, cancelling affected bookings."""
        seat = self.get_object()
        serializer = ResourceStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data['status']

        cancelled = 0
        with transaction.atomic():
            seat.status = new_status
            seat.status_note = (
                '' if new_status == ResourceStatus.ACTIVE else serializer.validated_data['note']
            )
            seat.save(update_fields=['status', 'status_note', 'updated_at'])
            if new_status != ResourceStatus.ACTIVE:
                cancelled = cancel_for_resource(
                    seat, actor=request.user,
                    reason=f'Seat {seat.number} is {seat.get_status_display().lower()}.',
                )
            log_activity(
                'resource.seat_status',
                f'Set seat {seat.number} to "{seat.get_status_display()}".',
                actor=request.user, target=seat, request=request,
            )
        data = self.get_serializer(seat).data
        data['cancelled_reservations'] = cancelled
        return Response(data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def availability(self, request):
        """Seat map with each seat's state for the requested time window."""
        window = parse_window(request.query_params)
        return Response(availability.seat_availability(
            window,
            viewer=request.user,
            floor_id=request.query_params.get('floor') or None,
            zone_id=request.query_params.get('zone') or None,
        ))

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def schedule(self, request, pk=None):
        """Booked time blocks of one seat on one day."""
        seat = self.get_object()
        day = parse_day(request.query_params)
        return Response(availability.day_schedule(seat, day, viewer=request.user))
