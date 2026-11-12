from django.contrib import admin

from .models import Closure, Floor, OperatingHours, ReservationPolicy

admin.site.register(Floor)
admin.site.register(OperatingHours)
admin.site.register(Closure)
admin.site.register(ReservationPolicy)
