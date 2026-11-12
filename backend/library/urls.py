from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    ClosureViewSet,
    FloorViewSet,
    LibraryOverviewView,
    OperatingHoursView,
    ReservationPolicyView,
)

router = DefaultRouter()
router.register('closures', ClosureViewSet, basename='closure')
router.register('floors', FloorViewSet, basename='floor')

urlpatterns = [
    path('overview/', LibraryOverviewView.as_view(), name='library-overview'),
    path('hours/', OperatingHoursView.as_view(), name='library-hours'),
    path('policy/', ReservationPolicyView.as_view(), name='library-policy'),
    *router.urls,
]
