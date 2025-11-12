from django.db import models

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
    def excerpt(self):
        return self.body[:150] + "..." if len(self.body) > 150 else self.body
    

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
    
    def __str__(self):
        return f"Comment by {self.author or 'Anonymous'} on {self.post.title}"
