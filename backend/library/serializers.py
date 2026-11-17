from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import (
    Closure, Floor, LandingItem, LandingPhoto, LibraryPersonnel, LibraryProfile, OperatingHours,
    ReservationPolicy,
)
from .services import local_today


class FloorSerializer(serializers.ModelSerializer):
    seat_count = serializers.IntegerField(read_only=True, default=0)
    room_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Floor
        fields = ['id', 'name', 'level', 'description', 'seat_count', 'room_count']


class FloorSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Floor
        fields = ['id', 'name', 'level']


class OperatingHoursSerializer(serializers.ModelSerializer):
    weekday_name = serializers.CharField(source='get_weekday_display', read_only=True)
    opens_at = serializers.TimeField(format='%H:%M')
    closes_at = serializers.TimeField(format='%H:%M')

    class Meta:
        model = OperatingHours
        fields = ['weekday', 'weekday_name', 'is_open', 'opens_at', 'closes_at']
        # `weekday` identifies the row in a bulk update; it is not unique-checked here.
        extra_kwargs = {'weekday': {'validators': []}}

    def validate(self, attrs):
        candidate = OperatingHours(**attrs)
        try:
            candidate.clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict) from exc
        return attrs


class ClosureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Closure
        fields = ['id', 'date', 'reason', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_date(self, value):
        if value < local_today():
            raise serializers.ValidationError('A closure cannot be scheduled in the past.')
        return value


class ReservationPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = ReservationPolicy
        exclude = ['id']
        read_only_fields = ['updated_at']

    def validate(self, attrs):
        candidate = ReservationPolicy(**{
            field.name: attrs.get(field.name, getattr(self.instance, field.name, field.default))
            for field in ReservationPolicy._meta.fields
            if field.name not in ('id', 'updated_at')
        })
        try:
            candidate.clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict) from exc
        return attrs


# ── Public landing page content ─────────────────────────────────────────────

class RelativeImageField(serializers.ImageField):
    """
    Returns '/media/...' rather than an absolute URL, so images load through
    whatever host the visitor used (the dev proxy, a phone on the LAN, ...).
    """

    def to_representation(self, value):
        return value.url if value else None


class LibraryProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = LibraryProfile
        exclude = ['id']
        read_only_fields = ['updated_at']


class LandingItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandingItem
        fields = ['id', 'section', 'title', 'description', 'order']


class LibraryPersonnelSerializer(serializers.ModelSerializer):
    photo = RelativeImageField(
        required=False, allow_null=True,
        validators=LibraryPersonnel._meta.get_field('photo').validators)

    class Meta:
        model = LibraryPersonnel
        fields = ['id', 'name', 'position', 'photo', 'order']


class LandingPhotoSerializer(serializers.ModelSerializer):
    image = RelativeImageField(validators=LandingPhoto._meta.get_field('image').validators)

    class Meta:
        model = LandingPhoto
        fields = ['id', 'image', 'caption', 'order']
