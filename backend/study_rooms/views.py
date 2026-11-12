from django.db import transaction
from django.db.models import Q
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
from seats.serializers import ResourceStatusSerializer

from .models import Facility, StudyRoom
from .serializers import FacilitySerializer, StudyRoomSerializer


class FacilityViewSet(viewsets.ModelViewSet):
    queryset = Facility.objects.all()
    serializer_class = FacilitySerializer
    permission_classes = [CanManageResourcesOrReadOnly]
    pagination_class = None


class StudyRoomViewSet(viewsets.ModelViewSet):
    serializer_class = StudyRoomSerializer
    permission_classes = [CanManageResourcesOrReadOnly]

    def get_queryset(self):
        queryset = StudyRoom.objects.select_related('floor').prefetch_related('facilities')
        params = self.request.query_params
        if params.get('floor'):
            queryset = queryset.filter(floor_id=params['floor'])
        if params.get('status'):
            queryset = queryset.filter(status=params['status'])
        search = params.get('search', '').strip()
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(code__icontains=search))
        return queryset

    def perform_create(self, serializer):
        room = serializer.save()
        log_activity('resource.room_created', f'Added study room {room.code}.',
                     actor=self.request.user, target=room, request=self.request)

    def perform_update(self, serializer):
        room = serializer.save()
        log_activity('resource.room_updated', f'Updated study room {room.code}.',
                     actor=self.request.user, target=room, request=self.request)

    def perform_destroy(self, instance):
        code = instance.code
        instance.delete()
        log_activity('resource.room_deleted', f'Deleted study room {code}.',
                     actor=self.request.user, request=self.request)

    @action(detail=True, methods=['post'], url_path='set-status')
    def set_status(self, request, pk=None):
        room = self.get_object()
        serializer = ResourceStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data['status']

        cancelled = 0
        with transaction.atomic():
            room.status = new_status
            room.status_note = (
                '' if new_status == ResourceStatus.ACTIVE else serializer.validated_data['note']
            )
            room.save(update_fields=['status', 'status_note', 'updated_at'])
            if new_status != ResourceStatus.ACTIVE:
                cancelled = cancel_for_resource(
                    room, actor=request.user,
                    reason=f'{room.name} is {room.get_status_display().lower()}.',
                )
            log_activity(
                'resource.room_status',
                f'Set study room {room.code} to "{room.get_status_display()}".',
                actor=request.user, target=room, request=request,
            )
        data = self.get_serializer(room).data
        data['cancelled_reservations'] = cancelled
        return Response(data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def availability(self, request):
        """All rooms with their state for the requested time window."""
        window = parse_window(request.query_params)
        return Response(availability.room_availability(
            window,
            viewer=request.user,
            floor_id=request.query_params.get('floor') or None,
        ))

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def schedule(self, request, pk=None):
        """Booked time blocks of one room on one day."""
        room = self.get_object()
        day = parse_day(request.query_params)
        return Response(availability.day_schedule(room, day, viewer=request.user))
