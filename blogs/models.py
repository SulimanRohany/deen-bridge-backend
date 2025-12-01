from django.db import models
from django.db.models import Count, Q

from django.core.exceptions import ValidationError

from taggit.managers import TaggableManager

class Post(models.Model):
    author = models.ForeignKey(
        'accounts.CustomUser', 
        on_delete=models.SET_NULL,
        null=True, 
        related_name='posts',
        limit_choices_to={'is_staff': True}  # Only allow staff users to be authors
    )


    title = models.CharField(max_length=255)
    body = models.TextField()

    featured_image = models.ImageField(upload_to='blog/images/%Y/%m/%d', blank=True, null=True)

    status = models.CharField(max_length=20, choices=(('draft', 'Draft'), ('published', 'Published')), default='draft')

    slug = models.SlugField(max_length=255, unique=True, blank=True)

    tags = TaggableManager(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def published_at(self):
        return self.updated_at if self.status == 'published' else None
    

    @property
    def comments_count(self):
        return self.comments.count()

    @property
    def likes_count(self):
        return self.post_likes.count()

    def is_liked_by_user(self, user):
        if not user or not user.is_authenticated:
            return False
        return self.post_likes.filter(user=user).exists()

    @property
    def excerpt(self):
        return self.body[:150] + "..." if len(self.body) > 150 else self.body
    
    def get_related_posts(self, limit=3):
        """
        Get related posts based on matching tags.
        Prioritizes posts with more matching tags, then by recency.
        Falls back to latest published posts if no tags match.
        """
        # Get all tags for this post
        post_tags = self.tags.all()
        
        if not post_tags.exists():
            # If no tags, return latest published posts (excluding current)
            return list(Post.objects.filter(
                status='published'
            ).exclude(id=self.id).order_by('-updated_at', '-created_at')[:limit])
        
        # Get tag names as a list
        tag_names = list(post_tags.values_list('name', flat=True))
        
        # Find published posts that share at least one tag (excluding current post)
        related_posts = Post.objects.filter(
            status='published',
            tags__name__in=tag_names
        ).exclude(id=self.id).distinct()
        
        # Annotate with count of matching tags
        related_posts = related_posts.annotate(
            matching_tags_count=Count('tags', filter=Q(tags__name__in=tag_names))
        ).order_by('-matching_tags_count', '-updated_at', '-created_at')
        
        # Get the limited results
        results = list(related_posts[:limit])
        
        # If we don't have enough results and there were some matching tags,
        # we still return what we have. But if we have no results at all,
        # fallback to latest published posts
        if len(results) == 0:
            return list(Post.objects.filter(
                status='published'
            ).exclude(id=self.id).order_by('-updated_at', '-created_at')[:limit])
        
        return results

    class Meta:
        ordering = ("-updated_at", "-created_at")

    def __str__(self):
        return self.title

    def clean(self):
        if self.featured_image:
            if self.featured_image.size > 5 * 1024 * 1024:
                raise ValidationError({'featured_image': 'Featured image size must be less than 5MB.'})
            if not self.featured_image.name.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                raise ValidationError({'featured_image': 'Featured image must be a JPG, PNG, or WEBP file.'})




class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')

    body = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)
    
    @property
    def likes_count(self):
        return self.comment_likes.count()

    def is_liked_by_user(self, user):
        if not user or not user.is_authenticated:
            return False
        return self.comment_likes.filter(user=user).exists()

    def __str__(self):
        return f"Comment by {self.author or 'Anonymous'} on {self.post.title}"


class PostLike(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_likes')
    user = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name='post_likes'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')
        ordering = ('-created_at',)

    def __str__(self):
        return f"{self.user.email} liked {self.post.title}"


class CommentLike(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='comment_likes')
    user = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name='comment_likes'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('comment', 'user')
        ordering = ('-created_at',)

    def __str__(self):
        return f"{self.user.email} liked comment {self.comment.id}"
