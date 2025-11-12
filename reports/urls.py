from django.urls import path
from core.communications_views import ReportListCreateView, ReportRetrieveUpdateDestroyView

# Using unified UserCommunication endpoints from core app
urlpatterns = [
    path('', ReportListCreateView.as_view(), name='report_list_create_view'),
    path('<int:pk>/', ReportRetrieveUpdateDestroyView.as_view(), name='report_retrieve_update_destroy_view'),
]