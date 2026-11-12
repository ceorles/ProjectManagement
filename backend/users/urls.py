from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import StudentLookupView, StudentSearchView, UserViewSet

router = DefaultRouter()
router.register('', UserViewSet, basename='user')

urlpatterns = [
    path('students/', StudentSearchView.as_view(), name='student-search'),
    path('lookup/', StudentLookupView.as_view(), name='student-lookup'),
    *router.urls,
]
