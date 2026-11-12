from rest_framework.routers import DefaultRouter

from .views import FacilityViewSet, StudyRoomViewSet

router = DefaultRouter()
router.register('facilities', FacilityViewSet, basename='facility')
router.register('', StudyRoomViewSet, basename='study-room')

urlpatterns = router.urls
