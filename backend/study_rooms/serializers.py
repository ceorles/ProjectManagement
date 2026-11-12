from rest_framework import serializers

from library.serializers import FloorSummarySerializer

from .models import Facility, StudyRoom


class FacilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Facility
        fields = ['id', 'name']

    def validate_name(self, value):
        name = value.strip()
        duplicate = Facility.objects.filter(name__iexact=name)
        if self.instance:
            duplicate = duplicate.exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise serializers.ValidationError('This facility already exists.')
        return name


class StudyRoomSerializer(serializers.ModelSerializer):
    floor_detail = FloorSummarySerializer(source='floor', read_only=True)
    facilities = serializers.PrimaryKeyRelatedField(
        queryset=Facility.objects.all(), many=True, required=False)
    facility_details = FacilitySerializer(source='facilities', many=True, read_only=True)
    status_label = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = StudyRoom
        fields = [
            'id', 'name', 'code', 'floor', 'floor_detail', 'capacity', 'min_occupancy',
            'description', 'facilities', 'facility_details',
            'status', 'status_label', 'status_note', 'created_at', 'updated_at',
        ]
        # Status changes go through the set-status action (see seats).
        read_only_fields = ['status', 'status_note', 'created_at', 'updated_at']
        extra_kwargs = {'code': {'validators': []}}

    def validate_code(self, value):
        code = value.strip().upper()
        duplicate = StudyRoom.objects.filter(code__iexact=code)
        if self.instance:
            duplicate = duplicate.exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise serializers.ValidationError('Another room already uses this room number.')
        return code

    def validate(self, attrs):
        instance = self.instance
        capacity = attrs.get('capacity', instance.capacity if instance else None)
        min_occupancy = attrs.get('min_occupancy', instance.min_occupancy if instance else 1)
        if min_occupancy > capacity:
            raise serializers.ValidationError(
                {'min_occupancy': 'Minimum group size cannot exceed the capacity.'})
        return attrs
