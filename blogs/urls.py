from django.urls import path

from .views import PostListCreateView, PostRetrieveUpdateDestroyView, CommentListCreateView, CommentRetrieveUpdateDestroyView, PostBySlugView, PostRelatedView, PostLikeToggleView, CommentLikeToggleView

urlpatterns = [
    path('post/', PostListCreateView.as_view(), name='post_list_create_view'),
    path('post/<int:pk>/', PostRetrieveUpdateDestroyView.as_view(), name='post_retrieve_update_destroy'),
    path('post/<int:pk>/like/', PostLikeToggleView.as_view(), name='post_like_toggle'),
    path('post/slug/<slug:slug>/', PostBySlugView.as_view(), name='post_by_slug'),
    path('post/slug/<slug:slug>/related/', PostRelatedView.as_view(), name='post_related'),

    path('comment/', CommentListCreateView.as_view(), name='comment_list_create_view'),
    path('comment/<int:pk>/', CommentRetrieveUpdateDestroyView.as_view(), name='comment_retrieve_update_destroy_view'),
    path('comment/<int:pk>/like/', CommentLikeToggleView.as_view(), name='comment_like_toggle'),
]