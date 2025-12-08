from rest_framework import serializers

from .models import TeacherProfile, StudentProfile, StudentParentProfile, SuperAdminProfile, StaffProfile

from core.image_compressor import compress_image_file
from django.conf import settings



class BaseProfileSerializer(serializers.ModelSerializer):

    def compress_image(self, validated_data):
        profile_image = validated_data.get('profile_image')
        if profile_image:
            try:
                validated_data['profile_image'] = compress_image_file(
                    profile_image,
                    quality=settings.IMAGE_COMPRESSION_QUALITY,
                    max_width=settings.IMAGE_COMPRESSION_MAX_WIDTH,
                    max_height=settings.IMAGE_COMPRESSION_MAX_HEIGHT
                )
            except Exception as e:
                # Log error but don't fail validation - use original image
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to compress profile image: {str(e)}")
        
        return validated_data
    
    def validate(self, validated_data):
        validated_data = self.compress_image(validated_data)

        instance = self.Meta.model(**validated_data)
        instance.clean()
        return validated_data


class TeacherProfileSerializer(BaseProfileSerializer):
    class Meta:
        model = TeacherProfile
        fields = "__all__"


class StudentProfileSerializer(BaseProfileSerializer):
    class Meta:
        model = StudentProfile
        fields = '__all__'


class StudentParentProfileSerializer(BaseProfileSerializer):
    class Meta:
        model = StudentParentProfile
        fields = "__all__"


class SuperAdminProfileSerializer(BaseProfileSerializer):
    class Meta:
        model = SuperAdminProfile
        fields = "__all__"


class StaffProfileSerializer(BaseProfileSerializer):
    class Meta:
        model = StaffProfile
        fields = "__all__"


