from django.urls import path

from .views import PostListCreateView, PostRetrieveUpdateDestroyView, CommentListCreateView, CommentRetrieveUpdateDestroyView, PostBySlugView

urlpatterns = [
    path('post/', PostListCreateView.as_view(), name='post_list_create_view'),
    path('post/<int:pk>/', PostRetrieveUpdateDestroyView.as_view(), name='post_retrieve_update_destroy'),
    path('post/slug/<slug:slug>/', PostBySlugView.as_view(), name='post_by_slug'),

    path('comment/', CommentListCreateView.as_view(), name='comment_list_create_view'),
    path('comment/<int:pk>/', CommentRetrieveUpdateDestroyView.as_view(), name='comment_retrieve_update_destroy_view'),
]