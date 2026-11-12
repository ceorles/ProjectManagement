from django.db.models import Max
from rest_framework import serializers

from library.models import ResourceStatus
from library.serializers import FloorSummarySerializer

from .models import Seat, Zone


class ZoneSerializer(serializers.ModelSerializer):
    floor_detail = FloorSummarySerializer(source='floor', read_only=True)
    zone_type_label = serializers.CharField(source='get_zone_type_display', read_only=True)
    seat_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Zone
        fields = [
            'id', 'name', 'floor', 'floor_detail', 'zone_type', 'zone_type_label',
            'description', 'rows', 'cols', 'seat_count',
        ]

    def validate(self, attrs):
        instance = self.instance
        floor = attrs.get('floor', instance.floor if instance else None)
        name = attrs.get('name', instance.name if instance else '')
        duplicate = Zone.objects.filter(floor=floor, name__iexact=name)
        if instance:
            duplicate = duplicate.exclude(pk=instance.pk)
        if duplicate.exists():
            raise serializers.ValidationError(
                {'name': 'This floor already has a zone with that name.'})

        if instance:
            # A zone cannot shrink below the seats already placed on it.
            used = instance.seats.aggregate(max_row=Max('row'), max_col=Max('col'))
            rows = attrs.get('rows', instance.rows)
            cols = attrs.get('cols', instance.cols)
            if used['max_row'] and rows < used['max_row']:
                raise serializers.ValidationError(
                    {'rows': f'Seats already occupy row {used["max_row"]}.'})
            if used['max_col'] and cols < used['max_col']:
                raise serializers.ValidationError(
                    {'cols': f'Seats already occupy column {used["max_col"]}.'})
        return attrs


class SeatSerializer(serializers.ModelSerializer):
    zone_name = serializers.CharField(source='zone.name', read_only=True)
    floor_name = serializers.CharField(source='zone.floor.name', read_only=True)
    floor = serializers.IntegerField(source='zone.floor_id', read_only=True)
    status_label = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Seat
        fields = [
            'id', 'number', 'zone', 'zone_name', 'floor', 'floor_name', 'row', 'col',
            'has_power_outlet', 'has_computer', 'near_window', 'is_accessible',
            'status', 'status_label', 'status_note', 'created_at', 'updated_at',
        ]
        # Status changes go through the set-status action so that affected
        # reservations are cancelled and students are told.
        read_only_fields = ['status', 'status_note', 'created_at', 'updated_at']
        extra_kwargs = {'number': {'validators': []}}

    def validate_number(self, value):
        number = value.strip().upper()
        duplicate = Seat.objects.filter(number__iexact=number)
        if self.instance:
            duplicate = duplicate.exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise serializers.ValidationError('Another seat already uses this number.')
        return number

    def validate(self, attrs):
        instance = self.instance
        zone = attrs.get('zone', instance.zone if instance else None)
        row = attrs.get('row', instance.row if instance else None)
        col = attrs.get('col', instance.col if instance else None)
        if row > zone.rows:
            raise serializers.ValidationError({'row': f'This zone has {zone.rows} rows.'})
        if col > zone.cols:
            raise serializers.ValidationError({'col': f'This zone has {zone.cols} columns.'})
        taken = Seat.objects.filter(zone=zone, row=row, col=col)
        if instance:
            taken = taken.exclude(pk=instance.pk)
        if taken.exists():
            raise serializers.ValidationError(
                {'col': f'Seat {taken.first().number} is already at this position.'})
        return attrs


class ResourceStatusSerializer(serializers.Serializer):
    """Body of the set-status action for seats and study rooms."""

    status = serializers.ChoiceField(choices=ResourceStatus.choices)
    note = serializers.CharField(max_length=200, required=False, allow_blank=True, default='')
