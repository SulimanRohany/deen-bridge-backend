from django.urls import path

from .views import CourseEnrollmentListCreateView, CourseEnrollmentRetrieveUpdateDestroyView

urlpatterns = [
    path('', CourseEnrollmentListCreateView.as_view(), name='course_enrollment_list_create_view'),
    path('<int:pk>/', CourseEnrollmentRetrieveUpdateDestroyView.as_view(), name='course_enrollment_retrieve_update_destroy_view')
]

