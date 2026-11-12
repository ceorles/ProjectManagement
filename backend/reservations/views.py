from datetime import time, timedelta

from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from config.exceptions import ApiError
from config.permissions import IsLibraryStaff

from . import services
from .models import Reservation
from .serializers import CancelSerializer, ReservationCreateSerializer, ReservationSerializer
from .windows import build_window, to_datetime

Status = Reservation.Status


class ReservationViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """
    Students see their own reservations (and rooms they were invited to).
    Staff see everyone's. All state changes are delegated to `services`.
    """

    serializer_class = ReservationSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = (
            Reservation.objects
            .select_related('student', 'seat__zone__floor', 'room__floor', 'created_by')
            .prefetch_related('participants__student')
        )
        if not user.is_library_staff:
            queryset = queryset.filter(
                Q(student=user) | Q(participants__student=user)).distinct()
        if self.action != 'list':
            return queryset
        return self._filter(queryset)

    def _filter(self, queryset):
        params = self.request.query_params
        user = self.request.user

        scope = params.get('scope')
        if scope == 'active':
            queryset = queryset.filter(status__in=Reservation.ACTIVE_STATUSES)
        elif scope == 'history':
            queryset = queryset.exclude(status__in=Reservation.ACTIVE_STATUSES)

        statuses = [s for s in params.get('status', '').split(',') if s]
        if statuses:
            queryset = queryset.filter(status__in=statuses)

        if params.get('resource_type'):
            queryset = queryset.filter(resource_type=params['resource_type'])

        day = parse_date(params.get('date', '') or '')
        if day:
            start = to_datetime(day, time.min)
            queryset = queryset.filter(start_at__gte=start, start_at__lt=start + timedelta(days=1))
        date_from = parse_date(params.get('date_from', '') or '')
        if date_from:
            queryset = queryset.filter(start_at__gte=to_datetime(date_from, time.min))
        date_to = parse_date(params.get('date_to', '') or '')
        if date_to:
            queryset = queryset.filter(
                start_at__lt=to_datetime(date_to, time.min) + timedelta(days=1))

        if user.is_library_staff:
            if params.get('student'):
                queryset = queryset.filter(student_id=params['student'])
            search = params.get('search', '').strip()
            if search:
                queryset = queryset.filter(
                    Q(code__icontains=search)
                    | Q(student__first_name__icontains=search)
                    | Q(student__last_name__icontains=search)
                    | Q(student__student_id__icontains=search)
                    | Q(student__email__icontains=search)
                    | Q(seat__number__icontains=search)
                    | Q(room__name__icontains=search)
                    | Q(room__code__icontains=search)
                )

        ordering = params.get('ordering')
        if ordering in ('start_at', '-start_at', 'created_at', '-created_at'):
            queryset = queryset.order_by(ordering, '-id')
        return queryset

    def _respond(self, reservation, http_status=status.HTTP_200_OK):
        fresh = self.get_queryset().get(pk=reservation.pk)
        return Response(self.get_serializer(fresh).data, status=http_status)

    def create(self, request):
        serializer = ReservationCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        reservation = services.create_reservation(
            actor=request.user,
            student=data['student_user'],
            resource_type=data['resource_type'],
            resource_id=data['resource_id'],
            window=build_window(data['date'], data['start_time'], data['end_time']),
            participant_count=data['participant_count'],
            purpose=data['purpose'],
            participants=data['participants'],
            request=request,
        )
        return self._respond(reservation, status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        reservation = self.get_object()
        serializer = CancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.cancel_reservation(
            reservation, actor=request.user, reason=serializer.validated_data['reason'])
        return self._respond(reservation)

    @action(detail=True, methods=['post'], url_path='check-in')
    def check_in(self, request, pk=None):
        reservation = self.get_object()
        services.check_in(reservation, actor=request.user)
        return self._respond(reservation)

    @action(detail=True, methods=['post'], url_path='check-out')
    def check_out(self, request, pk=None):
        reservation = self.get_object()
        services.check_out(reservation, actor=request.user)
        return self._respond(reservation)

    @action(detail=True, methods=['post'], url_path='no-show',
            permission_classes=[IsLibraryStaff])
    def no_show(self, request, pk=None):
        reservation = self.get_object()
        services.mark_no_show(reservation, actor=request.user)
        return self._respond(reservation)

    @action(detail=False, methods=['get'], permission_classes=[IsLibraryStaff])
    def lookup(self, request):
        """Staff: find a reservation by the code the student shows at the desk."""
        code = request.query_params.get('code', '').strip().upper().replace(' ', '')
        if not code:
            raise ApiError('Enter a reservation code.', code='missing_code')
        reservation = self.get_queryset().filter(code=code).first()
        if reservation is None:
            raise NotFound('No reservation has that code.')
        return Response(self.get_serializer(reservation).data)

    @action(detail=False, methods=['get'])
    def limits(self, request):
        """The signed-in student's standing against the booking limits."""
        user = request.user
        policy = services.get_policy()
        now = timezone.now()
        strikes = services.no_show_count(user, policy, now)
        active = Reservation.objects.filter(
            student=user, status__in=Reservation.ACTIVE_STATUSES).count()
        return Response({
            'active_reservations': active,
            'max_active_reservations': policy.max_active_reservations,
            'max_reservations_per_day': policy.max_reservations_per_day,
            'no_shows': strikes,
            'no_show_limit': policy.no_show_limit,
            'no_show_window_days': policy.no_show_window_days,
            'suspended': bool(policy.no_show_limit and strikes >= policy.no_show_limit),
        })
