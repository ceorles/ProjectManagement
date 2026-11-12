from django.contrib import admin

from .models import Reservation, ReservationParticipant


class ParticipantInline(admin.TabularInline):
    model = ReservationParticipant
    extra = 0


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    """Read-only: reservations must change through the API so the rules apply."""

    list_display = ('code', 'student', 'resource_type', 'seat', 'room', 'start_at', 'end_at',
                    'status')
    list_filter = ('status', 'resource_type')
    search_fields = ('code', 'student__email', 'student__student_id')
    inlines = [ParticipantInline]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
