from django.urls import path

from .views import AdminDashboardView, ReportView, StaffDashboardView, StudentDashboardView

urlpatterns = [
    path('student-dashboard/', StudentDashboardView.as_view(), name='student-dashboard'),
    path('staff-dashboard/', StaffDashboardView.as_view(), name='staff-dashboard'),
    path('admin-dashboard/', AdminDashboardView.as_view(), name='admin-dashboard'),
    path('usage/', ReportView.as_view(), name='usage-report'),
]
