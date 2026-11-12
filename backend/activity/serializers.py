from rest_framework import serializers

from .models import ActivityLog


class ActivityLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()
    actor_role = serializers.SerializerMethodField()
    category_label = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = ActivityLog
        fields = [
            'id', 'actor', 'actor_name', 'actor_role', 'category', 'category_label',
            'action', 'description', 'target_type', 'target_id', 'created_at',
        ]

    def get_actor_name(self, obj):
        return obj.actor.full_name if obj.actor else 'System'

    def get_actor_role(self, obj):
        return obj.actor.role if obj.actor else 'system'
