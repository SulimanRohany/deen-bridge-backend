from django.shortcuts import render

from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, ListAPIView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404


from django_filters.rest_framework import DjangoFilterBackend

from .serializers import ClassSerializer, LiveSessionSerializer, RecordingSerializer, AttendanceSerializer, CertificateSerializer, LiveSessionResourceSerializer

from .models import Class, LiveSession, Recording, Attendance, Certificate, LiveSessionResource

from .filters import ClassFilter, LiveSessionFilter, RecordingFilter, AttendanceFilter, CertificateFilter, LiveSessionResourceFilter

from core.utils import get_client_ip
from accounts.models import RoleChoices, CustomUser
from core.pagination import CustomPagination
# optional: pip install pyyaml user-agents
from user_agents import parse as parse_ua  # optional




class CourseListCreateView(ListCreateAPIView):
    """
    List and create classes (formerly courses).
    Note: Endpoint name kept as 'course' for backward compatibility.
    """
    serializer_class = ClassSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ClassFilter
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    pagination_class = CustomPagination

    def get_queryset(self):
        """
        Filter classes based on user role:
        - Teachers: Only see their assigned classes
        - Super Admin/Staff: See all classes
        - Others: See all classes (for browsing)
        """
        user = self.request.user
        
        # If user is authenticated and is a teacher, filter their classes
        if user.is_authenticated and user.role == RoleChoices.TEACHER:
            return Class.objects.filter(teacher=user).prefetch_related(
                'teacher', 'subject'
            ).order_by('-created_at')
        
        # For all other cases, return all classes
        return Class.objects.all().prefetch_related(
            'teacher', 'subject'
        ).order_by('-created_at')


class CourseRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a class.
    Note: Class name kept as 'Course...' for backward compatibility.
    """
    queryset = Class.objects.all()
    serializer_class = ClassSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]


class LiveSessionListCreateView(ListCreateAPIView):
    serializer_class = LiveSessionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = LiveSessionFilter
    pagination_class = CustomPagination

    def get_queryset(self):
        """
        Filter live sessions based on user role:
        - Teachers: Only see sessions for their classes
        - Super Admin/Staff: See all sessions
        - Others: See all sessions
        """
        user = self.request.user
        
        # If user is authenticated and is a teacher, filter their sessions
        if user.is_authenticated and user.role == RoleChoices.TEACHER:
            teacher_classes = Class.objects.filter(teacher=user)
            return LiveSession.objects.filter(
                class_session__in=teacher_classes
            ).select_related(
                'class_session'
            ).order_by('-created_at')
        
        # For all other cases, return all sessions
        return LiveSession.objects.all().select_related(
            'class_session'
        ).order_by('-created_at')


class LiveSessionRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    queryset = LiveSession.objects.all()
    serializer_class = LiveSessionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]



class RecordingListCreateView(ListCreateAPIView):
    queryset = Recording.objects.all()
    serializer_class = RecordingSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecordingFilter
    pagination_class = CustomPagination


class RecordingRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    queryset = Recording.objects.all()
    serializer_class = RecordingSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


# class AttendanceListCreateView(ListCreateAPIView):
#     queryset = Attendance.objects.all()
#     serializer_class = AttendanceSerializer
#     permission_classes = [IsAuthenticatedOrReadOnly]

class AttendanceListCreateView(ListCreateAPIView):
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = AttendanceFilter
    pagination_class = CustomPagination

    def get_queryset(self):
        """
        Filter attendance based on user role:
        - Teachers: Only see attendance for their classes
        - Super Admin/Staff: See all attendance
        - Students: See only their own attendance
        """
        user = self.request.user
        
        # If user is not authenticated, return empty queryset
        if not user.is_authenticated:
            return Attendance.objects.none()
        
        # Super admin and staff can see all attendance
        if user.role == RoleChoices.SUPER_ADMIN or user.is_staff:
            return Attendance.objects.all().select_related(
                'class_enrollment', 'session', 'class_enrollment__student'
            ).order_by('-created_at')
        
        # Teachers can only see attendance for their classes
        elif user.role == RoleChoices.TEACHER:
            teacher_classes = Class.objects.filter(teacher=user)
            teacher_sessions = LiveSession.objects.filter(
                class_session__in=teacher_classes
            )
            return Attendance.objects.filter(
                session__in=teacher_sessions
            ).select_related(
                'class_enrollment', 'session', 'class_enrollment__student'
            ).order_by('-created_at')
        
        # Students can only see their own attendance
        elif user.role == RoleChoices.STUDENT:
            return Attendance.objects.filter(
                class_enrollment__student=user
            ).select_related(
                'class_enrollment', 'session', 'class_enrollment__student'
            ).order_by('-created_at')
        
        # Default: return empty queryset
        return Attendance.objects.none()

    def perform_create(self, serializer):
        req = self.request
        # server-observed info
        user_agent = req.META.get('HTTP_USER_AGENT', '')
        ip = get_client_ip(req)
        accept_lang = req.META.get('HTTP_ACCEPT_LANGUAGE')

        device_info = {
            "user_agent": user_agent,
            "ip": ip,
            "accept_language": accept_lang,
            "x_forwarded_for": req.META.get('HTTP_X_FORWARDED_FOR'),
        }

        # optional: if frontend sends extra device details (screen size, timezone, etc.)
        client_side = req.data.get("device_info")
        if isinstance(client_side, dict):
            # merge (client values not trusted blindly; you may sanitize)
            device_info.update(client_side)

        # optional: parse UA for friendly fields
        try:
            ua = parse_ua(user_agent)
            device_info.update({
                "browser": {"family": ua.browser.family, "version": ua.browser.version_string},
                "os": {"family": ua.os.family, "version": ua.os.version_string},
                "device": {"family": ua.device.family, "is_mobile": ua.is_mobile, "is_tablet": ua.is_tablet, "is_pc": ua.is_pc},
            })
        except Exception:
            pass

        # finally save
        serializer.save(device_info=device_info)



class AttendanceRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class CertificateListCreateView(ListCreateAPIView):
    queryset = Certificate.objects.all()
    serializer_class = CertificateSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = CertificateFilter


class CertificateRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    queryset = Certificate.objects.all()
    serializer_class = CertificateSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class SessionJoinView(APIView):
    """Join a live session's SFU room."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, session_id):
        """Join a session's SFU room."""
        session = get_object_or_404(LiveSession, id=session_id)
        
        # Check if user can join this session
        if not session.can_user_join(request.user):
            return Response(
                {'error': 'You are not enrolled in this class or session is not available'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if session status is 'live'
        if session.status != 'live':
            return Response(
                {'error': 'This session is not currently live. You can only join when the session is active.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Use the session directly for SFU operations
        # All sessions use SFU video conferencing
        
        # Return session information for frontend to connect directly
        display_name = request.user.full_name or request.user.email
        role = 'member'  # Students are members, teachers could be moderators
        
        # Check if user is a teacher of this class
        if session.class_session.teacher.filter(id=request.user.id).exists():
            role = 'moderator'
        
        # Check participant limit (simplified check)
        # Note: In a real implementation, you'd track participants in the database
        # For now, we'll allow joining without strict participant limits
        
        return Response({
            'participant_id': f'user_{request.user.id}',
            'session': {
                'id': session.id,
                'title': session.title,
                'status': session.status,
                'class_title': session.class_session.title
            },
            'user': {
                'id': request.user.id,
                'display_name': display_name,
                'role': role
            },
            'mode': 'sfu'
        })


class SessionLeaveView(APIView):
    """Handle user leaving a live session."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, session_id):
        """
        Handle session leave request.
        This endpoint is called when a user navigates away or closes the browser.
        It can be called via sendBeacon for reliability during page unload.
        """
        session = get_object_or_404(LiveSession, id=session_id)
        
        # Log the leave action (optional - can be used for analytics)
        # In a production system, you might want to:
        # 1. Update attendance duration
        # 2. Send webhooks/notifications
        # 3. Clean up any session-specific data
        
        # The SFU server will handle the actual WebRTC cleanup when the 
        # WebSocket disconnects, but this endpoint allows for graceful cleanup
        # and logging before that happens
        
        return Response({
            'success': True,
            'message': 'Successfully left session',
            'session_id': session.id
        }, status=status.HTTP_200_OK)


class SFURoomAccessView(APIView):
    """Validate room access for SFU backend.
    
    This endpoint is called by the SFU backend to verify if a user
    has permission to join a specific room (session).
    The SFU backend calls this in production mode to validate access.
    """
    permission_classes = []  # No auth required - SFU backend handles auth
    
    def post(self, request):
        """Validate if a user has access to a room."""
        user_id = request.data.get('userId')
        room_id = request.data.get('roomId')  # This is the session ID (numeric, not UUID)
        
        if not user_id or not room_id:
            return Response(
                {'allowed': False, 'error': 'userId and roomId are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get the user
            user = CustomUser.objects.get(id=user_id)
            
            # roomId is actually the session ID (numeric)
            # Convert to int if it's a string
            try:
                session_id = int(room_id)
            except (ValueError, TypeError):
                # If it's not a number, it might be a UUID or other format
                # For now, allow it (flexible validation)
                # This handles cases where roomId might be a UUID or other format
                return Response({'allowed': True})
            
            # Check if session exists
            session = LiveSession.objects.filter(id=session_id).first()
            
            if not session:
                return Response({'allowed': False})
            
            # Check if user can join this session
            if session.can_user_join(user):
                return Response({'allowed': True})
            else:
                return Response({'allowed': False})
                
        except CustomUser.DoesNotExist:
            return Response({'allowed': False})
        except Exception as e:
            # Log error but allow access in case of errors (fail open)
            # This prevents blocking users if there's a temporary issue
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f'Error validating room access: {e}', exc_info=True)
            return Response({'allowed': True})


class SessionMonitorView(APIView):
    """Allow super admin to monitor a live session invisibly."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, session_id):
        """
        Join a session as an observer (super admin only).
        Observer mode allows monitoring without being visible to participants.
        """
        # Check if user is super admin
        if not request.user.is_superuser:
            return Response(
                {'error': 'Only super admins can monitor sessions'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        session = get_object_or_404(LiveSession, id=session_id)
        
        # Check if session is live
        if session.status != 'live':
            return Response(
                {'error': 'Can only monitor live sessions'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Return session information for observer to connect
        display_name = f"[Observer] {request.user.full_name or request.user.email}"
        
        return Response({
            'participant_id': f'observer_{request.user.id}',
            'session': {
                'id': session.id,
                'title': session.title,
                'status': session.status,
                'class_title': session.class_session.title
            },
            'user': {
                'id': request.user.id,
                'display_name': display_name,
                'role': 'observer',  # Special observer role
                'is_hidden': True    # Mark as hidden from other participants
            },
            'mode': 'sfu'
        })


class TimetableListView(ListAPIView):
    """
    List timetables (class schedules).
    Since timetable fields are now part of the Class model,
    this view returns class data filtered by course/class ID.
    """
    serializer_class = ClassSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ClassFilter
    pagination_class = CustomPagination

    def get_queryset(self):
        """
        Filter classes based on query parameters.
        Frontend typically passes ?course=<course_id>
        """
        queryset = Class.objects.all().prefetch_related('teacher', 'subject')
        
        # Filter by course/class ID if provided
        course_id = self.request.query_params.get('course')
        if course_id:
            queryset = queryset.filter(id=course_id)
        
        return queryset.order_by('-created_at')


class SessionEnrolledStudentsView(APIView):
    """
    Get all students enrolled in a specific session's class.
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get(self, request, session_id):
        """Get students enrolled in the session's class"""
        from accounts.serializers import CustomUserSerializer
        from enrollments.models import ClassEnrollment, EnrollmentChoices
        
        # Get the session
        session = get_object_or_404(LiveSession, id=session_id)
        
        # Get all students enrolled in this session's class with completed status
        enrolled_students = ClassEnrollment.objects.filter(
            class_enrolled=session.class_session,
            status=EnrollmentChoices.COMPLETED
        ).select_related('student')
        
        # Extract the student users
        students = [enrollment.student for enrollment in enrolled_students]
        
        # Serialize and return
        serializer = CustomUserSerializer(students, many=True)
        return Response({
            'session_id': session_id,
            'session_title': session.title,
            'class_id': session.class_session.id,
            'class_title': session.class_session.title,
            'students': serializer.data
        })


class SessionEnrollmentsView(APIView):
    """
    Get all enrollments for a specific session's class.
    Returns enrollment objects with student information.
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get(self, request, session_id):
        """Get enrollments for the session's class"""
        from enrollments.serializers import ClassEnrollmentSerializer
        from enrollments.models import ClassEnrollment, EnrollmentChoices
        
        # Get the session
        session = get_object_or_404(LiveSession, id=session_id)
        
        # Get all enrollments for this session's class with completed status
        enrollments = ClassEnrollment.objects.filter(
            class_enrolled=session.class_session,
            status=EnrollmentChoices.COMPLETED
        ).select_related('student', 'class_enrolled')
        
        # Serialize and return
        serializer = ClassEnrollmentSerializer(enrollments, many=True)
        return Response({
            'session_id': session_id,
            'session_title': session.title,
            'class_id': session.class_session.id,
            'class_title': session.class_session.title,
            'enrollments': serializer.data
        })


class LiveSessionResourceListCreateView(ListCreateAPIView):
    """
    List and create resources for live sessions.
    - Teachers and super admins can upload resources
    - Students can view resources for sessions they're enrolled in
    """
    serializer_class = LiveSessionResourceSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend]
    filterset_class = LiveSessionResourceFilter
    pagination_class = CustomPagination

    def get_queryset(self):
        """
        Filter resources based on user role:
        - Teachers: See resources for their sessions
        - Super Admin/Staff: See all resources
        - Students: See resources for sessions they're enrolled in
        """
        user = self.request.user
        
        # Super admin and staff can see all resources
        if user.role == RoleChoices.SUPER_ADMIN or user.is_staff:
            queryset = LiveSessionResource.objects.all()
        
        # Teachers can see resources for their sessions
        elif user.role == RoleChoices.TEACHER:
            teacher_classes = Class.objects.filter(teacher=user)
            teacher_sessions = LiveSession.objects.filter(class_session__in=teacher_classes)
            queryset = LiveSessionResource.objects.filter(session__in=teacher_sessions)
        
        # Students can see resources for sessions they're enrolled in
        elif user.role == RoleChoices.STUDENT:
            from enrollments.models import ClassEnrollment, EnrollmentChoices
            enrolled_classes = ClassEnrollment.objects.filter(
                student=user,
                status=EnrollmentChoices.COMPLETED
            ).values_list('class_enrolled', flat=True)
            enrolled_sessions = LiveSession.objects.filter(class_session__in=enrolled_classes)
            queryset = LiveSessionResource.objects.filter(session__in=enrolled_sessions)
        
        else:
            queryset = LiveSessionResource.objects.none()
        
        # Filter by session if provided
        session_id = self.request.query_params.get('session')
        if session_id:
            queryset = queryset.filter(session_id=session_id)
        
        return queryset.select_related('session', 'uploaded_by').order_by('-created_at')
    
    def perform_create(self, serializer):
        """Set the uploaded_by field to current user"""
        user = self.request.user
        session_id = self.request.data.get('session')
        
        # Verify user has permission to upload to this session
        if session_id:
            session = get_object_or_404(LiveSession, id=session_id)
            
            # Only teachers of the class or super admins can upload
            is_teacher = session.class_session.teacher.filter(id=user.id).exists()
            is_admin = user.role == RoleChoices.SUPER_ADMIN or user.is_staff
            
            if not (is_teacher or is_admin):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("Only teachers and administrators can upload resources to this session.")
        
        serializer.save(uploaded_by=user)


class LiveSessionResourceRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a live session resource.
    Only the uploader, class teacher, or admin can modify/delete.
    """
    queryset = LiveSessionResource.objects.all()
    serializer_class = LiveSessionResourceSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_queryset(self):
        """Apply same filtering as list view"""
        user = self.request.user
        
        # Super admin and staff can see all resources
        if user.role == RoleChoices.SUPER_ADMIN or user.is_staff:
            return LiveSessionResource.objects.all()
        
        # Teachers can see resources for their sessions
        elif user.role == RoleChoices.TEACHER:
            teacher_classes = Class.objects.filter(teacher=user)
            teacher_sessions = LiveSession.objects.filter(class_session__in=teacher_classes)
            return LiveSessionResource.objects.filter(session__in=teacher_sessions)
        
        # Students can see resources for sessions they're enrolled in
        elif user.role == RoleChoices.STUDENT:
            from enrollments.models import ClassEnrollment, EnrollmentChoices
            enrolled_classes = ClassEnrollment.objects.filter(
                student=user,
                status=EnrollmentChoices.COMPLETED
            ).values_list('class_enrolled', flat=True)
            enrolled_sessions = LiveSession.objects.filter(class_session__in=enrolled_classes)
            return LiveSessionResource.objects.filter(session__in=enrolled_sessions)
        
        return LiveSessionResource.objects.none()
    
    def perform_update(self, serializer):
        """Only allow uploader, teacher, or admin to update"""
        resource = self.get_object()
        user = self.request.user
        
        is_uploader = resource.uploaded_by.id == user.id
        is_teacher = resource.session.class_session.teacher.filter(id=user.id).exists()
        is_admin = user.role == RoleChoices.SUPER_ADMIN or user.is_staff
        
        if not (is_uploader or is_teacher or is_admin):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You don't have permission to update this resource.")
        
        serializer.save()
    
    def perform_destroy(self, instance):
        """Only allow uploader, teacher, or admin to delete"""
        user = self.request.user
        
        is_uploader = instance.uploaded_by.id == user.id
        is_teacher = instance.session.class_session.teacher.filter(id=user.id).exists()
        is_admin = user.role == RoleChoices.SUPER_ADMIN or user.is_staff
        
        if not (is_uploader or is_teacher or is_admin):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You don't have permission to delete this resource.")
        
        instance.delete()