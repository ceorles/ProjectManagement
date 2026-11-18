from django.db.models import Count, F, Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from activity.services import log_activity
from config.exceptions import ApiError
from config.permissions import CanManageResources, CanManageResourcesOrReadOnly
from reservations import availability
from reservations.windows import parse_day, parse_window

from . import services
from .models import Seat, Zone
from .serializers import (
    ResourceStatusSerializer, SeatSerializer, TableStatusSerializer, ZoneSerializer,
)


class ZoneViewSet(viewsets.ModelViewSet):
    serializer_class = ZoneSerializer
    permission_classes = [CanManageResourcesOrReadOnly]
    pagination_class = None

    def get_queryset(self):
        queryset = Zone.objects.select_related('floor').annotate(
            seat_count=Count('seats', filter=Q(seats__is_archived=False)))
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
        # All the chairs of one table together, table after table.
        queryset = Seat.objects.select_related('zone__floor').order_by(
            'zone', F('table_number').asc(nulls_last=True), 'number')
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
        """Take one seat out of service or put it back. Its table is not touched."""
        seat = self.get_object()
        serializer = ResourceStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        seat, cancelled = services.set_seat_status(
            seat, status=data['status'], note=data['note'],
            confirmed=data['confirm_cancellations'], actor=request.user, request=request,
        )
        payload = self.get_serializer(seat).data
        payload['cancelled_reservations'] = cancelled
        return Response(payload)

    @action(detail=True, methods=['get'], url_path='affected-reservations',
            permission_classes=[CanManageResources])
    def affected_reservations(self, request, pk=None):
        """Reservations that taking this seat out of service would affect."""
        return Response(services.affected_reservations([self.get_object()]))

    @action(detail=False, methods=['get'], permission_classes=[CanManageResources])
    def tables(self, request):
        """Every table of a zone (?zone=id) with its seats, state and reservations."""
        zone = request.query_params.get('zone')
        if not zone or not zone.isdigit():
            raise ApiError('Choose a zone.', code='missing_zone')
        return Response(services.tables_overview(int(zone)))

    @action(detail=False, methods=['post'], url_path='tables/set-status',
            permission_classes=[CanManageResources])
    def set_table_status(self, request):
        """Take a whole table out of service or restore it, as one operation."""
        serializer = TableStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        return Response(services.set_table_status(
            data['zone'], data['table_number'], status=data['status'], note=data['note'],
            confirmed=data['confirm_cancellations'], actor=request.user, request=request,
        ))

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
