from django.urls import path
from .views import DashboardReportView, TeacherDashboardView, ParentDashboardView, ChildDetailView


urlpatterns = [
    path('report/', DashboardReportView.as_view(), name='dashboard-report'),
    path('teacher/', TeacherDashboardView.as_view(), name='teacher-dashboard'),
    path('parent/', ParentDashboardView.as_view(), name='parent-dashboard'),
    path('parent/child/<int:child_id>/', ChildDetailView.as_view(), name='parent-child-detail'),
]