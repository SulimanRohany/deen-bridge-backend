from rest_framework import serializers

from .models import Post, Comment

from core.image_compressor import compress_image_file

from accounts.serializers import CustomUserSerializer

class PostSerializer(serializers.ModelSerializer):
    author_data = CustomUserSerializer(source='author', read_only=True)

    published_at = serializers.DateTimeField(read_only=True)
    excerpt = serializers.CharField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Post
        fields = "__all__"
    
    def validate(self, validated_data):

        if 'featured_image' in validated_data:
            compressed_image = compress_image_file(validated_data['featured_image'], quality=30)
            validated_data['featured_image'] = compressed_image

        instance = Post(**validated_data)
        instance.clean()
        return validated_data


class CommentSerializer(serializers.ModelSerializer):
    author_data = CustomUserSerializer(source='author', read_only=True)
    post_title = serializers.CharField(source='post.title', read_only=True)
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'author_data', 'post_title', 'parent', 'body', 'created_at', 'updated_at', 'replies']
        read_only_fields = ['id', 'created_at', 'updated_at', 'author_data', 'post_title', 'replies']
    
    def get_replies(self, obj):
        # Only include replies for top-level comments to avoid infinite recursion
        if obj.parent is None:
            replies = obj.replies.all()
            return CommentSerializer(replies, many=True, context=self.context).data
        return []
    
    def create(self, validated_data):
        # Set the author to the current user
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['author'] = request.user
        return super().create(validated_data)


