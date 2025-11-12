from rest_framework import serializers
from .models import CustomUser

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ("id", "email", "full_name", "role", "is_active", "created_at")
        read_only_fields = ("id", "created_at")
