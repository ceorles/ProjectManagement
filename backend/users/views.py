"""Account management for Admins, plus student search/lookup."""
from django.db import transaction
from django.db.models import Q
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from activity.services import log_activity
from config.exceptions import ApiError
from config.permissions import IsAdmin, IsLibraryStaff
from notifications.models import Notification
from notifications.services import notify

from .models import User
from .serializers import (
    ManagedUserSerializer,
    SetPasswordSerializer,
    StudentLookupSerializer,
    StudentSummarySerializer,
)


class UserViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    Admin-only. Accounts are never deleted (their reservation history must
    survive); they are deactivated instead.
    """

    serializer_class = ManagedUserSerializer
    permission_classes = [IsAdmin]
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_queryset(self):
        queryset = User.objects.all()
        params = self.request.query_params

        role = params.get('role')
        if role:
            queryset = queryset.filter(role=role)

        status_filter = params.get('status')
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)

        search = params.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(email__icontains=search)
                | Q(student_id__icontains=search)
            )

        ordering = params.get('ordering')
        allowed = {'last_name', '-last_name', 'date_joined', '-date_joined', 'email', '-email'}
        if ordering in allowed:
            queryset = queryset.order_by(ordering, 'id')
        return queryset

    def perform_create(self, serializer):
        user = serializer.save()
        log_activity(
            'user.created',
            f'Created {user.get_role_display().lower()} account for {user.full_name}.',
            actor=self.request.user, target=user, request=self.request,
        )

    def perform_update(self, serializer):
        user = serializer.save()
        log_activity('user.updated', f'Updated the account of {user.full_name}.',
                     actor=self.request.user, target=user, request=self.request)

    @action(detail=True, methods=['post'], url_path='set-password')
    def set_password(self, request, pk=None):
        user = self.get_object()
        serializer = SetPasswordSerializer(data=request.data, context={'target_user': user})
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data['new_password'])
        user.save(update_fields=['password'])
        log_activity('user.password_reset', f'Reset the password of {user.full_name}.',
                     actor=request.user, target=user, request=request)
        notify(user, 'Password changed',
               'An administrator set a new password for your account.',
               level=Notification.Level.WARNING, link='/profile')
        return Response({'message': f'Password updated for {user.full_name}.'})

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        # Imported here: the reservations app depends on users, not vice versa.
        from reservations.services import cancel_for_student

        user = self.get_object()
        if user.pk == request.user.pk:
            raise ApiError('You cannot deactivate your own account.', code='self_action')
        if user.is_admin and not User.objects.filter(
            role=User.Role.ADMIN, is_active=True
        ).exclude(pk=user.pk).exists():
            raise ApiError('The last active administrator cannot be deactivated.',
                           code='last_admin')

        with transaction.atomic():
            user.is_active = False
            user.save(update_fields=['is_active'])
            cancelled = 0
            if user.is_student:
                cancelled = cancel_for_student(
                    user, actor=request.user, reason='Account deactivated.'
                )
            log_activity('user.deactivated', f'Deactivated the account of {user.full_name}.',
                         actor=request.user, target=user, request=request)
        data = self.get_serializer(user).data
        data['cancelled_reservations'] = cancelled
        return Response(data)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        user = self.get_object()
        user.is_active = True
        user.save(update_fields=['is_active'])
        log_activity('user.activated', f'Reactivated the account of {user.full_name}.',
                     actor=request.user, target=user, request=request)
        return Response(self.get_serializer(user).data)


class StudentSearchView(APIView):
    """Staff: find a student to view or to book on their behalf."""

    permission_classes = [IsLibraryStaff]

    def get(self, request):
        search = request.query_params.get('search', '').strip()
        queryset = User.objects.filter(role=User.Role.STUDENT, is_active=True)
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(email__icontains=search)
                | Q(student_id__icontains=search)
            )
        return Response(StudentSummarySerializer(queryset[:20], many=True).data)


class StudentLookupView(APIView):
    """
    Any signed-in user: resolve an exact student ID to a name, used when
    inviting classmates to a study room. Exact match only, so the endpoint
    cannot be used to browse the student list.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        student_id = request.query_params.get('student_id', '').strip()
        if not student_id:
            raise ApiError('Enter a student ID.', code='missing_student_id')
        student = User.objects.filter(
            role=User.Role.STUDENT, is_active=True, student_id__iexact=student_id
        ).first()
        if student is None:
            raise NotFound('No active student has that ID.')
        return Response(StudentLookupSerializer(student).data)
