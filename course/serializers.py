from datetime import date, datetime
from rest_framework import serializers

from .models import Class, LiveSession, Recording, Attendance, Certificate, LiveSessionResource

from accounts.models import CustomUser
from subjects.models import Subject
from enrollments.models import ClassEnrollment

from accounts.serializers import CustomUserSerializer
from subjects.serializers import SubjectSerializer
from core.image_compressor import compress_image_file
from django.conf import settings


class ClassSerializer(serializers.ModelSerializer):

    # Read-only fields for displaying nested data
    teachers = CustomUserSerializer(source='teacher', many=True, read_only=True)
    subjects = SubjectSerializer(source='subject', many=True, read_only=True)
    
    # Write-only fields for accepting IDs during create/update
    teacher = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=CustomUser.objects.filter(role='teacher'),
        write_only=True,
        required=False
    )
    subject = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Subject.objects.all(),
        write_only=True,
        required=False
    )

    enrolled_students = serializers.SerializerMethodField(read_only=True)

    enrolled_count = serializers.IntegerField(read_only=True)
    seat_left = serializers.IntegerField(read_only=True)
    is_enrolled = serializers.SerializerMethodField(read_only=True)
    
    # Timing fields display
    days_display = serializers.SerializerMethodField(read_only=True)
    is_on_weekend = serializers.BooleanField(read_only=True)

    def get_days_display(self, obj):
        """Return formatted day names"""
        return obj.get_days_display()

    def get_enrolled_students(self, obj):
        # return users who have an active enrollment for this class
        qs = CustomUser.objects.filter(
            class_enrollments__class_enrolled=obj,
            class_enrollments__status='completed'
        ).distinct()
        return CustomUserSerializer(qs, many=True).data

    def get_is_enrolled(self, obj):
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return False
        user = request.user
        # Check if user has a completed enrollment for this class
        from enrollments.models import ClassEnrollment, EnrollmentChoices
        return ClassEnrollment.objects.filter(
            student=user,
            class_enrolled=obj,
            status=EnrollmentChoices.COMPLETED
        ).exists()

    def validate_cover_image(self, value):
        """Validate and compress cover image"""
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
                logger.warning(f"Failed to compress cover image: {str(e)}")
        return value
    
    def validate(self, validated_data):
        # Compress cover_image if present
        if 'cover_image' in validated_data and validated_data.get('cover_image'):
            try:
                validated_data['cover_image'] = compress_image_file(
                    validated_data['cover_image'],
                    quality=settings.IMAGE_COMPRESSION_QUALITY,
                    max_width=settings.IMAGE_COMPRESSION_MAX_WIDTH,
                    max_height=settings.IMAGE_COMPRESSION_MAX_HEIGHT
                )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to compress cover image in validate: {str(e)}")
        
        # Create a temporary instance for validation, excluding ManyToMany fields
        temp_data = validated_data.copy()
        temp_data.pop('teacher', None)
        temp_data.pop('subject', None)
        
        instance = Class(**temp_data)
        instance.clean()
        return validated_data

    def create(self, validated_data):
        """Handle ManyToMany fields properly during creation"""
        # Extract ManyToMany fields
        teachers = validated_data.pop('teacher', [])
        subjects = validated_data.pop('subject', [])
        
        # Create the class instance
        class_instance = Class.objects.create(**validated_data)
        
        # Set ManyToMany relationships using .set()
        if teachers:
            class_instance.teacher.set(teachers)
        if subjects:
            class_instance.subject.set(subjects)
        
        return class_instance

    def update(self, instance, validated_data):
        """Handle ManyToMany fields properly during update"""
        # Extract ManyToMany fields
        teachers = validated_data.pop('teacher', None)
        subjects = validated_data.pop('subject', None)
        
        # Update regular fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update ManyToMany relationships using .set()
        if teachers is not None:
            instance.teacher.set(teachers)
        if subjects is not None:
            instance.subject.set(subjects)
        
        return instance

    class Meta:
        model = Class
        fields = [
            'id', 'title', 'description', 'cover_image',
            'teacher', 'teachers', 'subject', 'subjects',
            'capacity', 'price', 'is_special_class',
            'days_of_week', 'start_time', 'end_time', 'timezone', 'is_active',
            'enrolled_students', 'enrolled_count', 'seat_left', 'is_enrolled',
            'days_display', 'is_on_weekend',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at',
            'teachers', 'subjects', 'enrolled_students',
            'enrolled_count', 'seat_left', 'is_enrolled',
            'days_display', 'is_on_weekend'
        ]


# Legacy alias for backward compatibility
CourseSerializer = ClassSerializer

    


class LiveSessionSerializer(serializers.ModelSerializer):
    class_title = serializers.CharField(source='class_session.title', read_only=True)
    class_id = serializers.IntegerField(source='class_session.id', read_only=True)
    class_teacher = serializers.SerializerMethodField(read_only=True)
    duration = serializers.SerializerMethodField()
    can_join = serializers.SerializerMethodField()
    join_url = serializers.SerializerMethodField()
    
    # Add class info for frontend display
    class_info = serializers.SerializerMethodField()

    def get_class_teacher(self, obj):
        """Get first teacher's full name"""
        if obj.class_session and obj.class_session.teacher.exists():
            first_teacher = obj.class_session.teacher.first()
            return first_teacher.full_name if first_teacher else None
        return None

    def get_class_info(self, obj):
        """Return formatted class information"""
        if obj.class_session:
            return {
                'class_title': obj.class_session.title,
                'class_id': obj.class_session.id,
                'days_display': obj.class_session.get_days_display(),
                'start_time': obj.class_session.start_time,
                'end_time': obj.class_session.end_time,
                'timezone': obj.class_session.timezone,
            }
        return None

    def get_duration(self, obj):
        if obj.class_session and obj.class_session.start_time and obj.class_session.end_time:
            start = datetime.combine(date.today(), obj.class_session.start_time)
            end = datetime.combine(date.today(), obj.class_session.end_time)
            return (end - start).seconds // 60  # duration in minutes
        return None
    
    def get_can_join(self, obj):
        """Check if current user can join this session."""
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return False
        return obj.can_user_join(request.user)
    
    def get_join_url(self, obj):
        """Get the join URL for this session."""
        request = self.context.get('request')
        if not request or not request.user:
            return None
        return obj.get_session_join_url(request.user)

    class Meta:
        model = LiveSession
        fields = "__all__"
        read_only_fields = ['reminder_sent', 'created_at', 'updated_at', 'is_recording', 'recording_started_at', 'recording_file']


class RecordingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recording
        fields = "__all__"


class AttendanceSerializer(serializers.ModelSerializer):
    device_info = serializers.JSONField(read_only=True)

    class_data = ClassSerializer(source='class_enrollment.class_enrolled', read_only=True)
    session_data = LiveSessionSerializer(source='session', read_only=True)
    
    # Additional fields for easier frontend access
    student_email = serializers.EmailField(source='class_enrollment.student.email', read_only=True)
    student_name = serializers.SerializerMethodField()
    student_id = serializers.IntegerField(source='class_enrollment.student.id', read_only=True)
    session_title = serializers.CharField(source='session.title', read_only=True)
    class_title = serializers.CharField(source='class_enrollment.class_enrolled.title', read_only=True)
    session_id = serializers.IntegerField(source='session.id', read_only=True)
    class_id = serializers.IntegerField(source='class_enrollment.class_enrolled.id', read_only=True)
    
    # Write-only fields for easier attendance creation
    student = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.filter(role='student'),
        write_only=True,
        required=False,
        help_text="Student ID - used with session to automatically find enrollment"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Force class_enrollment to be not required after auto-generation
        if 'class_enrollment' in self.fields:
            self.fields['class_enrollment'].required = False
            self.fields['class_enrollment'].allow_null = True
        
        # Remove UniqueTogetherValidator that enforces class_enrollment as required
        # We'll handle uniqueness validation manually in the validate() method
        from rest_framework.validators import UniqueTogetherValidator
        self.validators = [
            v for v in self.validators 
            if not isinstance(v, UniqueTogetherValidator)
        ]

    def get_student_name(self, obj):
        """Get full name of the student"""
        if obj.class_enrollment and obj.class_enrollment.student:
            student = obj.class_enrollment.student
            return student.full_name if student.full_name else student.email
        return 'N/A'

    class Meta:
        model = Attendance
        fields = [
            'id', 'class_enrollment', 'session', 'status', 'device_info',
            'created_at', 'updated_at',
            # Read-only fields
            'student', 'class_data', 'session_data', 'student_email', 'student_name',
            'student_id', 'session_title', 'class_title', 'session_id', 'class_id'
        ]
        extra_kwargs = {
            'class_enrollment': {'required': False, 'allow_null': True}
        }

    def validate(self, validated_data):
        from enrollments.models import ClassEnrollment, EnrollmentChoices
        
        # If student is provided instead of class_enrollment, find the enrollment
        student = validated_data.pop('student', None)
        session = validated_data.get('session')
        
        # If student is provided, find the enrollment
        if student and session:
            try:
                enrollment = ClassEnrollment.objects.get(
                    student=student,
                    class_enrolled=session.class_session,
                    status=EnrollmentChoices.COMPLETED
                )
                validated_data['class_enrollment'] = enrollment
            except ClassEnrollment.DoesNotExist:
                raise serializers.ValidationError({
                    'student': f'Student {student.full_name} ({student.email}) is not enrolled in the class for this session.'
                })
            except ClassEnrollment.MultipleObjectsReturned:
                # If multiple enrollments exist (shouldn't happen due to unique_together), get the first one
                enrollment = ClassEnrollment.objects.filter(
                    student=student,
                    class_enrolled=session.class_session,
                    status=EnrollmentChoices.COMPLETED
                ).first()
                validated_data['class_enrollment'] = enrollment
        
        # Validate that class_enrollment exists
        if 'class_enrollment' not in validated_data:
            raise serializers.ValidationError({
                'class_enrollment': 'Either class_enrollment or (student + session) must be provided.'
            })
        
        # Check for duplicate attendance (only on create, not on update)
        class_enrollment = validated_data.get('class_enrollment')
        if class_enrollment and session:
            # If this is an update (instance exists), exclude the current instance
            existing_query = Attendance.objects.filter(
                class_enrollment=class_enrollment,
                session=session
            )
            
            # If updating, exclude current instance
            if self.instance:
                existing_query = existing_query.exclude(pk=self.instance.pk)
            
            if existing_query.exists():
                student_name = class_enrollment.student.full_name or class_enrollment.student.email
                session_title = session.title
                raise serializers.ValidationError({
                    'non_field_errors': f'Attendance already exists for {student_name} in session "{session_title}". A student can only have one attendance record per session.'
                })
        
        return validated_data


class CertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificate
        fields = "__all__"


class LiveSessionResourceSerializer(serializers.ModelSerializer):
    """Serializer for LiveSessionResource model"""
    
    # Read-only fields for display
    uploaded_by_name = serializers.SerializerMethodField()
    uploaded_by_email = serializers.CharField(source='uploaded_by.email', read_only=True)
    file_size_display = serializers.SerializerMethodField()
    file_extension = serializers.SerializerMethodField()
    session_title = serializers.CharField(source='session.title', read_only=True)
    
    # File URL for download
    file_url = serializers.SerializerMethodField()
    
    def get_uploaded_by_name(self, obj):
        """Get the uploader's full name"""
        if obj.uploaded_by:
            return obj.uploaded_by.full_name or obj.uploaded_by.email
        return 'Unknown'
    
    def get_file_size_display(self, obj):
        """Get human-readable file size"""
        return obj.get_file_size_display()
    
    def get_file_extension(self, obj):
        """Get file extension"""
        return obj.get_file_extension()
    
    def get_file_url(self, obj):
        """Get the file URL"""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
    
    class Meta:
        model = LiveSessionResource
        fields = [
            'id', 'session', 'title', 'description', 'file', 'file_type',
            'file_size', 'uploaded_by', 'created_at', 'updated_at',
            # Read-only fields
            'uploaded_by_name', 'uploaded_by_email', 'file_size_display',
            'file_extension', 'session_title', 'file_url'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'file_size',
            'uploaded_by_name', 'uploaded_by_email', 'file_size_display',
            'file_extension', 'session_title', 'file_url'
        ]
        extra_kwargs = {
            'uploaded_by': {'required': False}  # Will be set automatically in view
        }


