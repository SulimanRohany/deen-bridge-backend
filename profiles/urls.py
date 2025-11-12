from django.urls import path

from . import views

urlpatterns = [
    # Teacher profile
    path('teacher/', views.TeacherProfileListCreateView.as_view(), name='teacher_profile_list_create_view'),
    path('teacher/<int:pk>/', views.TeacherProfileRetrieveUpdateDestroyView.as_view(), name='teacher_profile_retrieve_update_destroy_view'),

    # Student profile
    path('student/', views.StudentProfileListCreateView.as_view(), name='student_profile_list_create_view'),
    path('student/<int:pk>/', views.StudentProfileRetrieveUpdateDestroyView.as_view(), name='student_profile_retrieve_update_destroy_view'),

    # Student parent profile
    path('parent/', views.StudentParentListCreateView.as_view(), name='student_parent_profile_list_create_view'),
    path('parent/<int:pk>/', views.StudentParentRetrieveUpdateDestroyView.as_view(), name='student_parent_profile_retrieve_update_destroy_view'),

    # Staff profile
    path('staff/', views.StaffProfileListCreateView.as_view(), name='staff_profile_list_create_view'),
    path('staff/<int:pk>/', views.StaffProfileRetrieveUpdateDestroyView.as_view(), name='staff_profile_retrieve_update_destroy_view'),

    # Super admin profile
    path('superadmin/', views.SuperAdminProfileListCreateView.as_view(), name='superadmin_profile_list_create_view'),
    path('superadmin/<int:pk>/', views.SuperAdminProfileRetrieveUpdateDestroyView.as_view(), name='superadmin_profile_retrieve_update_destroy_view'),
]