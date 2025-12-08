from rest_framework import serializers

from .models import Report
from accounts.serializers import UserWithProfileSerializer
from core.image_compressor import compress_image_file
from django.conf import settings


class ReportSerializer(serializers.ModelSerializer):
    user = UserWithProfileSerializer(read_only=True)

    class Meta:
        model = Report
        fields = '__all__'
    
    def validate_screen_shot(self, value):
        """Validate and compress screenshot image"""
        if value:
            # Check file type
            if not value.content_type.startswith('image/'):
                raise serializers.ValidationError('File must be an image.')
            # Compress the image
            try:
                value = compress_image_file(
                    value,
                    quality=settings.IMAGE_COMPRESSION_QUALITY,
                    max_width=settings.IMAGE_COMPRESSION_MAX_WIDTH,
                    max_height=settings.IMAGE_COMPRESSION_MAX_HEIGHT
                )
            except Exception as e:
                # Log error but don't fail validation - use original image
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to compress screenshot: {str(e)}")
        return value