from django.contrib import admin

from .models import (
    Closure, Floor, LandingItem, LandingPhoto, LibraryPersonnel, LibraryProfile, OperatingHours,
    ReservationPolicy,
)

admin.site.register(Floor)
admin.site.register(OperatingHours)
admin.site.register(Closure)
admin.site.register(ReservationPolicy)
admin.site.register(LibraryProfile)
admin.site.register(LandingItem)
admin.site.register(LibraryPersonnel)
admin.site.register(LandingPhoto)
