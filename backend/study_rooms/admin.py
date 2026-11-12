from django.contrib import admin

from .models import Facility, StudyRoom

admin.site.register(Facility)


@admin.register(StudyRoom)
class StudyRoomAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'floor', 'capacity', 'status')
    list_filter = ('status', 'floor')
    search_fields = ('code', 'name')
