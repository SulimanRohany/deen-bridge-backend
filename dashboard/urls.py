from django.urls import path
from .views import DashboardReportView, TeacherDashboardView


urlpatterns = [
    path('report/', DashboardReportView.as_view(), name='dashboard-report'),
    path('teacher/', TeacherDashboardView.as_view(), name='teacher-dashboard'),
]