from django.contrib import admin

from .models import Seat, Zone


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'floor', 'zone_type', 'rows', 'cols')
    list_filter = ('floor', 'zone_type')


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ('number', 'zone', 'row', 'col', 'status')
    list_filter = ('status', 'zone')
    search_fields = ('number',)
