from django.urls import path

from .views import (
    CourseListCreateView,
    CourseRetrieveUpdateDestroyView,
    LiveSessionListCreateView,
    LiveSessionRetrieveUpdateDestroyView,
    RecordingListCreateView,
    RecordingRetrieveUpdateDestroyView,
    AttendanceListCreateView,
    AttendanceRetrieveUpdateDestroyView,
    CertificateListCreateView,
    CertificateRetrieveUpdateDestroyView,
    SessionJoinView,
    SessionLeaveView,
    SessionMonitorView,
    TimetableListView,
    SessionEnrolledStudentsView,
    SessionEnrollmentsView,
    LiveSessionResourceListCreateView,
    LiveSessionResourceRetrieveUpdateDestroyView
)

urlpatterns = [
    # Class endpoints (kept as 'course' for backward compatibility)
    path('', CourseListCreateView.as_view(), name='course_list_create_view'),
    path('<int:pk>/', CourseRetrieveUpdateDestroyView.as_view(), name='course_retrieve_update_destroy_view'),
    
    # Timetable endpoint (returns class schedule data)
    path('timetable/', TimetableListView.as_view(), name='timetable_list_view'),
    
    # Live session endpoints
    path('live_session/', LiveSessionListCreateView.as_view(), name='live_session_list_create_view'),
    path('live_session/<int:pk>/', LiveSessionRetrieveUpdateDestroyView.as_view(), name='live_session_retrieve_update_destroy_view'),
    
    # Recording endpoints
    path('recording/', RecordingListCreateView.as_view(), name='recording_list_create_view'),
    path('recording/<int:pk>/', RecordingRetrieveUpdateDestroyView.as_view(), name='recording_retrieve_update_destroy_view'),
    
    # Attendance endpoints
    path('attendance/', AttendanceListCreateView.as_view(), name='attendance_list_create_view'),
    path('attendance/<int:pk>/', AttendanceRetrieveUpdateDestroyView.as_view(), name='attendance_retrieve_update_destroy_view'),
    
    # Certificate endpoints
    path('certificate/', CertificateListCreateView.as_view(), name='certificate_list_create_view'),
    path('certificate/<int:pk>/', CertificateRetrieveUpdateDestroyView.as_view(), name='certificate_retrieve_update_destroy_view'),
    
    # Session join/leave endpoints
    path('session/<int:session_id>/join/', SessionJoinView.as_view(), name='session_join_view'),
    path('session/<int:session_id>/leave/', SessionLeaveView.as_view(), name='session_leave_view'),
    path('session/<int:session_id>/monitor/', SessionMonitorView.as_view(), name='session_monitor_view'),
    
    # Session students/enrollments endpoints
    path('session/<int:session_id>/students/', SessionEnrolledStudentsView.as_view(), name='session_enrolled_students'),
    path('session/<int:session_id>/enrollments/', SessionEnrollmentsView.as_view(), name='session_enrollments'),
    
    # Live session resources endpoints
    path('session/resources/', LiveSessionResourceListCreateView.as_view(), name='live_session_resource_list_create'),
    path('session/resources/<int:pk>/', LiveSessionResourceRetrieveUpdateDestroyView.as_view(), name='live_session_resource_detail')
]