from rest_framework.routers import DefaultRouter

from .views import SeatViewSet, ZoneViewSet

router = DefaultRouter()
router.register('zones', ZoneViewSet, basename='zone')
router.register('', SeatViewSet, basename='seat')

urlpatterns = router.urls
