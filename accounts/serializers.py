from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils import timezone

from profiles.serializers import (
    TeacherProfileSerializer, StudentProfileSerializer, StudentParentProfileSerializer,
    StaffProfileSerializer, SuperAdminProfileSerializer
)

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


from .models import CustomUser, RoleChoices, PasswordResetToken, EmailVerificationToken
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
        fields = ("id", "email", "full_name", "role", "is_active", "email_verified", "created_at", "profile")
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
        elif role == RoleChoices.PARENT:
            # Parent can have multiple student relationships
            relationships = obj.student_parent_relationships.all()
            if relationships.exists():
                # Return the first relationship for backwards compatibility
                # In the future, we might want to return all relationships
                serializer = StudentParentProfileSerializer(relationships.first())
            else:
                return None
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

        # Check if user's email is verified (skip check for superusers)
        user = self.user
        if not user.email_verified and not user.is_superuser:
            from rest_framework.exceptions import ValidationError
            from django.core.cache import cache
            
            # Check if user can resend verification (not rate-limited)
            cache_key = f'resend_verification_{user.email}'
            request_count = cache.get(cache_key, 0)
            can_resend = request_count < 3
            
            raise ValidationError({
                'email_verified': 'Your email address has not been verified. Please check your email for a verification link.',
                'user_email': user.email,
                'verification_required': True,
                'can_resend': can_resend
            })

        # Add user data to the access token payload
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


class CreateParentAccountSerializer(serializers.Serializer):
    student_id = serializers.IntegerField(required=True)
    parent_email = serializers.EmailField(required=True)
    parent_full_name = serializers.CharField(required=True, max_length=255)
    relationship = serializers.CharField(required=False, max_length=100, allow_blank=True)
    password = serializers.CharField(write_only=True, required=False, style={'input_type': 'password'})
    link_to_existing = serializers.BooleanField(default=False)

    def validate_student_id(self, value):
        """Validate that student exists and is actually a student"""
        try:
            student = CustomUser.objects.get(id=value, role=RoleChoices.STUDENT)
            # Check if student profile exists
            if not hasattr(student, 'studentprofile_profile'):
                raise serializers.ValidationError("Student profile not found for this user.")
            return value
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("Student with this ID does not exist or is not a student.")

    def validate_parent_email(self, value):
        """Normalize email"""
        return value.lower()

    def validate(self, attrs):
        """Validate password is provided when creating new account"""
        parent_email = attrs.get('parent_email')
        link_to_existing = attrs.get('link_to_existing', False)
        password = attrs.get('password')
        
        # Check if parent email exists
        parent_exists = CustomUser.objects.filter(email=parent_email).exists()
        
        if parent_exists:
            parent_user = CustomUser.objects.get(email=parent_email)
            if parent_user.role != RoleChoices.PARENT:
                raise serializers.ValidationError({
                    'parent_email': 'A user with this email exists but is not a parent account.'
                })
            
            if not link_to_existing:
                raise serializers.ValidationError({
                    'link_to_existing': 'A parent account with this email already exists. Set link_to_existing to true to link the student to this parent.'
                })
        else:
            # Creating new account - password is required
            if not password:
                raise serializers.ValidationError({
                    'password': 'Password is required when creating a new parent account.'
                })
            # Validate password strength
            validate_password(password)
        
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for requesting a password reset"""
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        """Normalize email to lowercase"""
        return value.lower()

    def save(self):
        """Generate token and send email if user exists"""
        email = self.validated_data['email']
        try:
            user = CustomUser.objects.get(email=email, is_active=True)
            # Create password reset token
            reset_token = PasswordResetToken.create_for_user(user, expiration_hours=1)
            # Send email (import here to avoid circular imports)
            from .utils import send_password_reset_email
            send_password_reset_email(user, reset_token.token)
        except CustomUser.DoesNotExist:
            # Don't reveal if email exists for security
            pass
        # Always return success to prevent email enumeration
        return {'message': 'If an account with that email exists, a password reset link has been sent.'}


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for confirming password reset with token"""
    token = serializers.CharField(required=True, max_length=255)
    password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        """Validate token and passwords"""
        token = attrs.get('token')
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')

        # Check if passwords match
        if password != password_confirm:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})

        # Validate password strength
        validate_password(password)

        # Validate token
        try:
            reset_token = PasswordResetToken.objects.get(token=token)
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError({"token": "Invalid or expired reset token."})

        # Check if token is valid
        if not reset_token.is_valid():
            raise serializers.ValidationError({"token": "Invalid or expired reset token."})

        # Store token instance for use in save method
        attrs['reset_token'] = reset_token
        return attrs

    def save(self):
        """Reset user password and mark token as used"""
        reset_token = self.validated_data['reset_token']
        password = self.validated_data['password']
        user = reset_token.user

        # Update user password
        user.set_password(password)
        user.save()

        # Mark token as used
        reset_token.mark_as_used()

        return {'message': 'Password has been reset successfully.'}


class EmailVerificationSerializer(serializers.Serializer):
    """Serializer for verifying email address with token"""
    token = serializers.CharField(required=True, max_length=255)

    def validate_token(self, value):
        """Validate token format and existence"""
        import logging
        logger = logging.getLogger(__name__)
        
        if not value or len(value) < 20:
            raise serializers.ValidationError("Invalid token format.")
        
        # Validate token exists and is valid
        try:
            verification_token = EmailVerificationToken.objects.get(token=value)
        except EmailVerificationToken.DoesNotExist:
            logger.warning(f"Verification attempt with non-existent token: {value[:10]}...")
            raise serializers.ValidationError("Invalid or expired verification token.")
        
        user = verification_token.user
        
        # Check for verification attempt locks
        from .models import EmailVerificationAttempt
        attempt_record = EmailVerificationAttempt.get_or_create_for_email(
            user.email,
            ip_address=self.context.get('ip_address')
        )
        
        # Check if email is locked
        if attempt_record.is_locked():
            logger.warning(f"Verification attempt for locked email: {user.email}")
            raise serializers.ValidationError(
                "Too many verification attempts. Please try again later."
            )
        
        # Check if token is valid
        if not verification_token.is_valid():
            # Increment failed attempts
            attempt_record.increment_attempts(self.context.get('ip_address'))
            logger.warning(f"Failed verification attempt for {user.email} - Invalid/expired token")
            raise serializers.ValidationError("Invalid or expired verification token.")
        
        # Store token instance and attempt record for use in save method
        self.verification_token = verification_token
        self.attempt_record = attempt_record
        return value

    def save(self):
        """Verify user email and mark token as used"""
        import logging
        logger = logging.getLogger(__name__)
        
        verification_token = self.verification_token
        user = verification_token.user
        attempt_record = self.attempt_record
        
        # Check if already verified
        if user.email_verified:
            logger.info(f"Email already verified for {user.email}")
            return {
                'message': 'Email address is already verified.',
                'email_verified': True
            }
        
        # Update user email_verified status
        user.email_verified = True
        user.save(update_fields=['email_verified'])
        
        # Mark token as used
        verification_token.mark_as_used()
        
        # Reset attempt count on successful verification
        attempt_record.reset_attempts()
        
        logger.info(f"Email successfully verified for {user.email} from IP {self.context.get('ip_address')}")
        
        return {
            'message': 'Email address has been successfully verified.',
            'email_verified': True
        }


class ResendVerificationSerializer(serializers.Serializer):
    """Serializer for resending email verification"""
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        """Normalize email to lowercase"""
        return value.lower()

    def validate(self, attrs):
        """Check rate limiting and validate user exists"""
        from django.core.cache import cache
        from .models import EmailVerificationAttempt
        import logging
        logger = logging.getLogger(__name__)
        
        email = attrs.get('email')
        
        # Check for verification attempt locks
        attempt_record = EmailVerificationAttempt.get_or_create_for_email(
            email,
            ip_address=self.context.get('ip_address')
        )
        
        if attempt_record.is_locked():
            logger.warning(f"Resend verification attempt for locked email: {email}")
            time_remaining = (attempt_record.locked_until - timezone.now()).total_seconds() / 60
            raise serializers.ValidationError({
                'email': f'Too many verification attempts. Account locked. Please try again in {int(time_remaining)} minutes.'
            })
        
        # Rate limiting: max 3 requests per hour per email
        cache_key = f'resend_verification_{email}'
        request_count = cache.get(cache_key, 0)
        max_requests = 3
        rate_limit_window = 3600  # 1 hour in seconds
        
        if request_count >= max_requests:
            logger.warning(f"Rate limit exceeded for resend verification: {email}")
            raise serializers.ValidationError({
                'email': f'Too many verification email requests. Please wait before requesting another email.',
                'rate_limited': True
            })
        
        # Store request count in cache
        cache.set(cache_key, request_count + 1, rate_limit_window)
        
        # Check if user exists and is not verified (but don't reveal if email doesn't exist)
        try:
            user = CustomUser.objects.get(email=email, is_active=True)
            if user.email_verified:
                # User is already verified - don't reveal this for security
                pass
            # Store user for save method
            self.user = user
        except CustomUser.DoesNotExist:
            # Don't reveal if email exists - always return success
            pass
        
        return attrs

    def save(self):
        """Generate new token and send verification email"""
        import logging
        logger = logging.getLogger(__name__)
        
        email = self.validated_data['email']
        
        try:
            user = getattr(self, 'user', None)
            if not user:
                # User doesn't exist - but don't reveal this
                logger.info(f"Resend verification requested for non-existent email: {email}")
                return {
                    'message': 'If an account with this email exists and is not verified, a verification email has been sent.'
                }
            
            # Check if already verified
            if user.email_verified:
                # Don't reveal this - return generic message
                logger.info(f"Resend verification requested for already verified email: {email}")
                return {
                    'message': 'If an account with this email exists and is not verified, a verification email has been sent.'
                }
            
            # Invalidate old tokens (mark as used)
            EmailVerificationToken.objects.filter(
                user=user,
                used=False
            ).update(used=True)
            
            # Create new verification token (24 hour expiration)
            verification_token = EmailVerificationToken.create_for_user(user, expiration_hours=24)
            
            # Send verification email
            from .utils import send_email_verification
            send_email_verification(user, verification_token.token)
            
            logger.info(f"Verification email resent to {email} from IP {self.context.get('ip_address')}")
            
        except Exception as e:
            # Log error but don't reveal details
            logger.error(f"Failed to resend verification email to {email}: {str(e)}")
            # Don't raise - always return success to prevent enumeration
        
        # Always return success to prevent email enumeration
        return {
            'message': 'If an account with this email exists and is not verified, a verification email has been sent.'
        }