from django.urls import path

from .views import (
    NotificationListCreateView,
    NotificationRetrieveUpdateDestroyView,
    mark_notification_as_read,
    mark_notification_as_unread,
    mark_all_as_read,
    get_unread_count,
    delete_all_notifications
)

urlpatterns = [
    path('', NotificationListCreateView.as_view(), name='notification_list_create_view'),
    path('unread-count/', get_unread_count, name='notification_unread_count'),
    path('mark-all-read/', mark_all_as_read, name='notification_mark_all_read'),
    path('delete-all/', delete_all_notifications, name='notification_delete_all'),
    path('<int:pk>/', NotificationRetrieveUpdateDestroyView.as_view(), name='notification_retrieve_update_destroy_view'),
    path('<int:pk>/mark-read/', mark_notification_as_read, name='notification_mark_read'),
    path('<int:pk>/mark-unread/', mark_notification_as_unread, name='notification_mark_unread'),
]

