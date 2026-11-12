from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'title', 'level', 'is_read')
    list_filter = ('level', 'is_read')
    search_fields = ('title', 'message', 'user__email')
