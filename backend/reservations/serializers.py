from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from library.services import get_policy
from users.models import User

from .models import Reservation
from .services import checkin_deadline, checkin_opens_at

Status = Reservation.Status


class ReservationSerializer(serializers.ModelSerializer):
    """
    A reservation as shown to the person asking. The `can_*` flags tell the
    frontend which actions to offer; the services enforce them again.
    """

    status_label = serializers.CharField(source='get_status_display', read_only=True)
    resource = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    start_time = serializers.SerializerMethodField()
    end_time = serializers.SerializerMethodField()
    duration_minutes = serializers.SerializerMethodField()
    student = serializers.SerializerMethodField()
    participants = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    booked_by_staff = serializers.SerializerMethodField()
    checkin_opens_at = serializers.SerializerMethodField()
    checkin_deadline = serializers.SerializerMethodField()
    can_cancel = serializers.SerializerMethodField()
    can_check_in = serializers.SerializerMethodField()
    can_check_out = serializers.SerializerMethodField()
    can_mark_no_show = serializers.SerializerMethodField()

    class Meta:
        model = Reservation
        fields = [
            'id', 'code', 'resource_type', 'resource', 'date', 'start_time', 'end_time',
            'start_at', 'end_at', 'duration_minutes', 'status', 'status_label',
            'participant_count', 'purpose', 'student', 'participants', 'is_owner',
            'booked_by_staff', 'created_at', 'checked_in_at', 'checked_out_at',
            'cancelled_at', 'cancel_reason', 'checkin_opens_at', 'checkin_deadline',
            'can_cancel', 'can_check_in', 'can_check_out', 'can_mark_no_show',
        ]
        read_only_fields = fields

    # Shared per-serialization state (one policy lookup, one "now").
    @property
    def _policy(self):
        if 'policy' not in self.context:
            self.context['policy'] = get_policy()
        return self.context['policy']

    @property
    def _now(self):
        if 'now' not in self.context:
            self.context['now'] = timezone.now()
        return self.context['now']

    @property
    def _viewer(self):
        return self.context['request'].user

    def get_resource(self, obj):
        if obj.resource_type == Reservation.ResourceType.SEAT:
            seat = obj.seat
            return {
                'type': 'seat', 'id': seat.pk, 'name': f'Seat {seat.number}',
                'code': seat.number, 'location': seat.location_label,
                'zone': seat.zone.name, 'floor': seat.zone.floor.name,
            }
        room = obj.room
        return {
            'type': 'room', 'id': room.pk, 'name': room.name, 'code': room.code,
            'location': room.location_label, 'floor': room.floor.name,
            'capacity': room.capacity,
        }

    def get_date(self, obj):
        return timezone.localtime(obj.start_at).date().isoformat()

    def get_start_time(self, obj):
        return timezone.localtime(obj.start_at).strftime('%H:%M')

    def get_end_time(self, obj):
        return timezone.localtime(obj.end_at).strftime('%H:%M')

    def get_duration_minutes(self, obj):
        return int((obj.end_at - obj.start_at).total_seconds() // 60)

    def get_student(self, obj):
        student = obj.student
        data = {'id': student.pk, 'full_name': student.full_name}
        if self._viewer.is_library_staff or student.pk == self._viewer.pk:
            data.update({
                'student_id': student.student_id, 'email': student.email,
                'program': student.program, 'year_level': student.year_level,
            })
        return data

    def get_participants(self, obj):
        return [
            {'id': p.student_id, 'full_name': p.student.full_name,
             'student_id': p.student.student_id}
            for p in obj.participants.all()
        ]

    def get_is_owner(self, obj):
        return obj.student_id == self._viewer.pk

    def get_booked_by_staff(self, obj):
        return obj.created_by_id is not None and obj.created_by_id != obj.student_id

    def get_checkin_opens_at(self, obj):
        return checkin_opens_at(obj, self._policy)

    def get_checkin_deadline(self, obj):
        return checkin_deadline(obj, self._policy)

    def _staff_or_owner(self, obj):
        return self._viewer.is_library_staff or obj.student_id == self._viewer.pk

    def get_can_cancel(self, obj):
        if obj.status != Status.CONFIRMED:
            return False
        if self._viewer.is_library_staff:
            return True
        cutoff = obj.start_at - timedelta(minutes=self._policy.cancellation_cutoff_minutes)
        return obj.student_id == self._viewer.pk and self._now <= cutoff

    def get_can_check_in(self, obj):
        if obj.status != Status.CONFIRMED:
            return False
        in_window = (
            checkin_opens_at(obj, self._policy) <= self._now < checkin_deadline(obj, self._policy)
        )
        if not in_window:
            return False
        if self._viewer.is_library_staff:
            return True
        return obj.student_id == self._viewer.pk and self._policy.allow_self_checkin

    def get_can_check_out(self, obj):
        return obj.status == Status.CHECKED_IN and self._staff_or_owner(obj)

    def get_can_mark_no_show(self, obj):
        return (
            self._viewer.is_library_staff
            and obj.status == Status.CONFIRMED
            and self._now >= obj.start_at
        )


class ReservationCreateSerializer(serializers.Serializer):
    """Shape and existence checks only; the booking rules live in services."""

    resource_type = serializers.ChoiceField(choices=Reservation.ResourceType.choices)
    seat = serializers.IntegerField(required=False, allow_null=True)
    room = serializers.IntegerField(required=False, allow_null=True)
    date = serializers.DateField()
    start_time = serializers.TimeField(input_formats=['%H:%M', '%H:%M:%S'])
    end_time = serializers.TimeField(input_formats=['%H:%M', '%H:%M:%S'])
    participant_count = serializers.IntegerField(min_value=1, max_value=100, default=1)
    purpose = serializers.CharField(max_length=200, allow_blank=True, default='')
    participant_student_ids = serializers.ListField(
        child=serializers.CharField(max_length=20), required=False, default=list,
        max_length=50,
    )
    # Staff only: the student the reservation is for.
    student = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, attrs):
        field = attrs['resource_type']
        if not attrs.get(field):
            raise serializers.ValidationError({field: f'Choose a {field} to reserve.'})
        attrs['resource_id'] = attrs[field]

        viewer = self.context['request'].user
        if viewer.is_library_staff:
            student = User.objects.filter(
                pk=attrs.get('student'), role=User.Role.STUDENT).first()
            if student is None:
                raise serializers.ValidationError(
                    {'student': 'Choose the student this reservation is for.'})
            attrs['student_user'] = student
        else:
            attrs['student_user'] = viewer  # a student always books for themself

        participants = []
        for raw in dict.fromkeys(s.strip() for s in attrs['participant_student_ids']):
            if not raw:
                continue
            person = User.objects.filter(
                role=User.Role.STUDENT, is_active=True, student_id__iexact=raw).first()
            if person is None:
                raise serializers.ValidationError(
                    {'participant_student_ids': f'No active student has the ID "{raw}".'})
            participants.append(person)
        attrs['participants'] = participants
        return attrs


class CancelSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=200, required=False, allow_blank=True, default='')
