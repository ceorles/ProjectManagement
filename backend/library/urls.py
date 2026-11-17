from django.urls import path
from rest_framework.routers import DefaultRouter

from .landing_views import (
    LandingItemViewSet, LandingPhotoViewSet, LibraryPersonnelViewSet, LibraryProfileView,
    PublicLandingView,
)

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
router.register('landing-items', LandingItemViewSet, basename='landing-item')
router.register('personnel', LibraryPersonnelViewSet, basename='personnel')
router.register('photos', LandingPhotoViewSet, basename='landing-photo')

urlpatterns = [
    path('overview/', LibraryOverviewView.as_view(), name='library-overview'),
    path('hours/', OperatingHoursView.as_view(), name='library-hours'),
    path('policy/', ReservationPolicyView.as_view(), name='library-policy'),
    # The public landing page (no sign-in needed) and its library information.
    path('public/', PublicLandingView.as_view(), name='library-public'),
    path('profile/', LibraryProfileView.as_view(), name='library-profile'),
    *router.urls,
]
