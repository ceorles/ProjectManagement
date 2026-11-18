from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import StudentSearchView, UserViewSet

router = DefaultRouter()
router.register('', UserViewSet, basename='user')

urlpatterns = [
    path('students/', StudentSearchView.as_view(), name='student-search'),
    *router.urls,
]
