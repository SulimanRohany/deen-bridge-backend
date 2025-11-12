from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.db import transaction

from profiles.serializers import (
    TeacherProfileSerializer, StudentProfileSerializer, StudentParentProfileSerializer,
    StaffProfileSerializer, SuperAdminProfileSerializer
)

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


from .models import CustomUser, RoleChoices
from .user_serializers import CustomUserSerializer


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = CustomUser
        fields = ("email", "full_name", "role", "password")

    
    def validate_email(self, value):
        value = value.lower()
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value
    

    
    def validate(self, attrs):
        # Validate password strength
        validate_password(attrs.get("password"))

        # role must be one of RoleChoices
        allowed_roles = [choice[0] for choice in RoleChoices.choices]
        role = attrs.get("role")
        if role not in allowed_roles:
            raise serializers.ValidationError({"role": f"Invalid role. Allowed: {allowed_roles}"})

        return attrs
    


    def create(self, validated_data):
        password = validated_data.pop("password")
        
        # Remove is_staff and is_superuser if present to prevent unauthorized privilege escalation
        validated_data.pop("is_staff", None)
        validated_data.pop("is_superuser", None)

        # Use transaction to ensure user and profile are created atomically
        with transaction.atomic():
            # create_user expects email, password, full_name, role, plus extra fields
            # CustomUserManager.create_user normalizes email internally if provided
            user = CustomUser.objects.create_user(
                email=validated_data.get("email"),
                password=password,
                full_name=validated_data.get("full_name"),
                role=validated_data.get("role"),
                **{k: v for k, v in validated_data.items() if k not in ("email", "full_name", "role")}
            )
        return user
    

    def to_representation(self, instance):
        # Use a minimal public representation (no password fields)
        return {
            "id": getattr(instance, "pk", None),
            "email": instance.email,
            "full_name": instance.full_name,
            "role": instance.role,
            "created_at": getattr(instance, "created_at", None),
            "is_active": instance.is_active,
        }
    

class UserWithProfileSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ("id", "email", "full_name", "role", "is_active", "created_at", "profile")
        read_only_fields = ("id", "created_at")
    
    def update(self, instance, validated_data):
        # Remove is_staff and is_superuser if present to prevent unauthorized privilege escalation
        validated_data.pop("is_staff", None)
        validated_data.pop("is_superuser", None)
        return super().update(instance, validated_data)

    def get_profile(self, obj):
        role = obj.role
        profile = None
        # Use correct related_name from profile models: "studentprofile_profile", etc.
        if role == RoleChoices.TEACHER and hasattr(obj, "teacherprofile_profile"):
            profile = obj.teacherprofile_profile
            serializer = TeacherProfileSerializer(profile)
        elif role == RoleChoices.STUDENT and hasattr(obj, "studentprofile_profile"):
            profile = obj.studentprofile_profile
            serializer = StudentProfileSerializer(profile)
        elif role == RoleChoices.PARENT and hasattr(obj, "studentparentprofile_profile"):
            profile = obj.studentparentprofile_profile
            serializer = StudentParentProfileSerializer(profile)
        elif role == RoleChoices.STAFF and hasattr(obj, "staffprofile_profile"):
            profile = obj.staffprofile_profile
            serializer = StaffProfileSerializer(profile)
        elif role == RoleChoices.SUPER_ADMIN and hasattr(obj, "superadminprofile_profile"):
            profile = obj.superadminprofile_profile
            serializer = SuperAdminProfileSerializer(profile)
        else:
            return None
        return serializer.data







class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        # Add user data to the access token payload
        user = self.user
        user_data = UserWithProfileSerializer(user).data
        token = self.get_token(user)
        token['user'] = user_data

        # Serialize the access token to a string
        data['access'] = str(token.access_token)

        return data

    def get_token(self, user):
        token = super().get_token(user)

        # Add custom claims to the token
        user_data = UserWithProfileSerializer(user).data
        token['user'] = user_data

        return token



class StudentRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = CustomUser
        fields = ("email", "full_name", "password")

    def validate_email(self, value):
        """Normalize email and check for duplicates"""
        value = value.lower()
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

    def validate(self, attrs):
        # Validate password strength
        validate_password(attrs.get("password"))

        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        
        # Use transaction to ensure user and profile are created atomically
        with transaction.atomic():
            user = CustomUser.objects.create_user(
                email=validated_data.get("email"),
                password=password,
                full_name=validated_data.get("full_name"),
                role=RoleChoices.STUDENT,
            )
        return user

    def to_representation(self, instance):
        """Provide consistent response format"""
        return {
            "id": getattr(instance, "pk", None),
            "email": instance.email,
            "full_name": instance.full_name,
            "role": instance.role,
            "created_at": getattr(instance, "created_at", None),
            "is_active": instance.is_active,
        }