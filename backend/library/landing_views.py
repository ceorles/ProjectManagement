"""
The public landing page: one read-only endpoint for visitors, and the
endpoints the Admin uses in Library Settings to edit what it shows.
"""
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from activity.services import log_activity
from config.exceptions import ApiError
from config.permissions import IsAdmin

from .models import (
    Closure, LandingItem, LandingPhoto, LibraryPersonnel, LibraryProfile, OperatingHours,
)
from .serializers import (
    ClosureSerializer, LandingItemSerializer, LandingPhotoSerializer,
    LibraryPersonnelSerializer, LibraryProfileSerializer, OperatingHoursSerializer,
)
from .services import ensure_operating_hours, local_now, local_today


class PublicLandingView(APIView):
    """
    Everything the public landing page shows. Open to anyone, signed in or
    not. The opening hours are the same ones that govern reservations.
    """

    permission_classes = [AllowAny]
    authentication_classes = []  # a stale token must not turn this into a 401

    def get(self, request):
        ensure_operating_hours()
        today = local_today()
        items = LandingItem.objects.all()

        def section(name):
            return LandingItemSerializer(
                [item for item in items if item.section == name], many=True).data

        return Response({
            'profile': LibraryProfileSerializer(LibraryProfile.load()).data,
            'services': section(LandingItem.Section.SERVICE),
            'card': section(LandingItem.Section.CARD),
            'rules': section(LandingItem.Section.RULE),
            'personnel': LibraryPersonnelSerializer(LibraryPersonnel.objects.all(), many=True).data,
            'photos': LandingPhotoSerializer(LandingPhoto.objects.all(), many=True).data,
            'hours': OperatingHoursSerializer(OperatingHours.objects.all(), many=True).data,
            'closures': ClosureSerializer(
                Closure.objects.filter(date__gte=today, date__lte=today + timedelta(days=30)),
                many=True).data,
            'time_zone': settings.TIME_ZONE,
            'now': local_now().isoformat(),
        })


class LibraryProfileView(APIView):
    """Admin: the library's name, introduction and contact details."""

    permission_classes = [IsAdmin]

    def get(self, request):
        return Response(LibraryProfileSerializer(LibraryProfile.load()).data)

    def patch(self, request):
        serializer = LibraryProfileSerializer(
            LibraryProfile.load(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        log_activity('settings.landing_updated', 'Updated the library information.',
                     actor=request.user, request=request)
        return Response(serializer.data)


class ReorderSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)


class LandingContentViewSet(viewsets.ModelViewSet):
    """Shared behaviour for the editable lists: Admin only, ordered, re-orderable."""

    permission_classes = [IsAdmin]
    pagination_class = None
    label = 'landing page content'

    def siblings(self, serializer):
        """Records a new one is ordered among (placed after the last of them)."""
        return serializer.Meta.model.objects.all()

    def perform_create(self, serializer):
        last = (self.siblings(serializer).order_by('-order')
                .values_list('order', flat=True).first())
        instance = serializer.save(order=0 if last is None else last + 1)
        self._log(f'Added {self.label}: "{instance}".')

    def perform_update(self, serializer):
        instance = serializer.save()
        self._log(f'Updated {self.label}: "{instance}".')

    def perform_destroy(self, instance):
        self._log(f'Removed {self.label}: "{instance}".')
        instance.delete()

    def _log(self, description):
        log_activity('settings.landing_updated', description[:255],
                     actor=self.request.user, request=self.request)

    @action(detail=False, methods=['post'])
    def reorder(self, request):
        """Body: {"ids": [3, 1, 2]} - the new order of (some of) the records."""
        serializer = ReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = serializer.validated_data['ids']
        records = {record.pk: record for record in self.get_queryset().filter(pk__in=ids)}
        if len(records) != len(set(ids)):
            raise ApiError('Some of these records do not exist.', code='invalid_ids')
        with transaction.atomic():
            for position, pk in enumerate(ids):
                records[pk].order = position
                records[pk].save(update_fields=['order'])
        return Response(self.get_serializer(self.get_queryset(), many=True).data)


class LandingItemViewSet(LandingContentViewSet):
    """Services, library card steps and rules. Filter with ?section=service|card|rule."""

    serializer_class = LandingItemSerializer
    label = 'landing page item'

    def siblings(self, serializer):
        return LandingItem.objects.filter(section=serializer.validated_data['section'])

    def get_queryset(self):
        queryset = LandingItem.objects.all()
        section = self.request.query_params.get('section')
        return queryset.filter(section=section) if section else queryset


class ImageContentViewSet(LandingContentViewSet):
    """Adds file uploads, and removes a replaced or deleted image from disk."""

    parser_classes = [MultiPartParser, FormParser, JSONParser]
    image_field = 'image'

    def perform_update(self, serializer):
        old = getattr(serializer.instance, self.image_field)
        old_name = old.name if old else ''
        super().perform_update(serializer)
        new = getattr(serializer.instance, self.image_field)
        if old_name and (not new or new.name != old_name):
            old.storage.delete(old_name)

    def perform_destroy(self, instance):
        image = getattr(instance, self.image_field)
        name = image.name if image else ''
        super().perform_destroy(instance)
        if name:
            image.storage.delete(name)


class LibraryPersonnelViewSet(ImageContentViewSet):
    queryset = LibraryPersonnel.objects.all()
    serializer_class = LibraryPersonnelSerializer
    image_field = 'photo'
    label = 'library personnel'


class LandingPhotoViewSet(ImageContentViewSet):
    queryset = LandingPhoto.objects.all()
    serializer_class = LandingPhotoSerializer
    label = 'landing page photo'
