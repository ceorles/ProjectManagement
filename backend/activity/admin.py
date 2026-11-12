from django.contrib import admin

from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'actor', 'action', 'description')
    list_filter = ('category',)
    search_fields = ('description', 'actor__email')
    readonly_fields = [field.name for field in ActivityLog._meta.fields]

    def has_add_permission(self, request):
        return False
