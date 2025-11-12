from django.urls import path

from .views import SubjectListCreateView, SubjectRetrieveUpdateDestroyView

urlpatterns = [
    path('', SubjectListCreateView.as_view(), name='subject_list_create_view'),
    path('<int:pk>/', SubjectRetrieveUpdateDestroyView.as_view(), name='subject_retrieve_update_destroy_view'),
]