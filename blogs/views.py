from django.shortcuts import render

from .models import Post, Comment, PostLike, CommentLike
from .serializers import PostSerializer, CommentSerializer
from .filters import PostFilter

from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, RetrieveAPIView
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework import status
from core.pagination import CustomPagination
from django.shortcuts import get_object_or_404


class PostListCreateView(ListCreateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = PostFilter
    pagination_class = CustomPagination

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class PostRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class PostBySlugView(RetrieveAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'
    lookup_url_kwarg = 'slug'

    def get_queryset(self):
        published_posts = Post.objects.filter(status='published')
        
        # If no published posts, show all posts
        if published_posts.exists():
            return published_posts
        else:
            return Post.objects.all()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class PostRelatedView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, slug):
        # Get the post by slug (similar to PostBySlugView logic)
        published_posts = Post.objects.filter(status='published')
        
        if published_posts.exists():
            queryset = published_posts
        else:
            queryset = Post.objects.all()
        
        post = get_object_or_404(queryset, slug=slug)
        
        # Get related posts
        related_posts = post.get_related_posts(limit=3)
        
        # Serialize the related posts
        serializer = PostSerializer(
            related_posts, 
            many=True, 
            context={'request': request}
        )
        
        return Response(serializer.data, status=status.HTTP_200_OK)


class CommentListCreateView(ListCreateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    
    def get_queryset(self):
        queryset = Comment.objects.all()
        post_id = self.request.query_params.get('post', None)
        if post_id is not None:
            queryset = queryset.filter(post_id=post_id)
        return queryset.filter(parent=None)  # Only return top-level comments
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class CommentRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class PostLikeToggleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        user = request.user

        # Check if like already exists
        like, created = PostLike.objects.get_or_create(post=post, user=user)

        if not created:
            # Like exists, so remove it (unlike)
            like.delete()
            is_liked = False
        else:
            # Like was created, so it's now liked
            is_liked = True

        # Return updated like count and status
        return Response({
            'is_liked': is_liked,
            'likes_count': post.likes_count
        }, status=status.HTTP_200_OK)


class CommentLikeToggleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        comment = get_object_or_404(Comment, pk=pk)
        user = request.user

        # Check if like already exists
        like, created = CommentLike.objects.get_or_create(comment=comment, user=user)

        if not created:
            # Like exists, so remove it (unlike)
            like.delete()
            is_liked = False
        else:
            # Like was created, so it's now liked
            is_liked = True

        # Return updated like count and status
        return Response({
            'is_liked': is_liked,
            'likes_count': comment.likes_count
        }, status=status.HTTP_200_OK)