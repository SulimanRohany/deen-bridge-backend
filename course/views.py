from django.shortcuts import render
import hmac
import hashlib
import json
import os
import logging
import requests

from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, ListAPIView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone


from django_filters.rest_framework import DjangoFilterBackend

from .serializers import ClassSerializer, LiveSessionSerializer, RecordingSerializer, AttendanceSerializer, CertificateSerializer, LiveSessionResourceSerializer

from .models import Class, LiveSession, Recording, Attendance, Certificate, LiveSessionResource

from .filters import ClassFilter, LiveSessionFilter, RecordingFilter, AttendanceFilter, CertificateFilter, LiveSessionResourceFilter

from core.utils import get_client_ip
from accounts.models import RoleChoices, CustomUser
from core.pagination import CustomPagination
# optional: pip install pyyaml user-agents
from user_agents import parse as parse_ua  # optional

logger = logging.getLogger(__name__)




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
    throttle_classes = []  # Exempt from rate limiting - critical user action
    
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
    throttle_classes = []  # Exempt from rate limiting - called by SFU backend
    
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
            
            # Allow superusers and super admins to access any room (for monitoring)
            # This matches the behavior in development mode where all access is allowed
            # and enables super admins to monitor live sessions
            if user.is_superuser or user.role == RoleChoices.SUPER_ADMIN:
                return Response({'allowed': True})
            
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
            
            # Check if user can join this session (for regular users)
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
    throttle_classes = []  # Exempt from rate limiting - critical user action
    
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


class SessionStartRecordingView(APIView):
    """Start recording for a live session (teacher only)."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, session_id):
        """Start recording for a live session."""
        logger.info(f'Start recording request received for session_id: {session_id}, user: {request.user.id}')
        try:
            session = get_object_or_404(LiveSession, id=session_id)
            
            # Check if user is a teacher of the class or super admin
            is_teacher = session.class_session.teacher.filter(id=request.user.id).exists()
            is_admin = request.user.is_superuser or request.user.role == RoleChoices.SUPER_ADMIN
            
            if not (is_teacher or is_admin):
                return Response(
                    {'error': 'Only teachers and administrators can start recording'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Check if session is live
            if session.status != 'live':
                return Response(
                    {'error': 'Can only start recording for live sessions'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if already recording
            if session.is_recording:
                return Response(
                    {'error': 'Recording is already in progress'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Call SFU backend to start recording
            sfu_base_url = os.environ.get('SFU_BASE_URL', 'http://localhost:3001')
            room_id = str(session.id)  # Use session ID as room ID
            
            try:
                response = requests.post(
                    f'{sfu_base_url}/api/rooms/{room_id}/recording/start',
                    json={
                        'sessionId': session.id,
                        'startedBy': request.user.id
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    # Update session state (will be confirmed by webhook)
                    session.is_recording = True
                    session.recording_started_at = timezone.now()
                    session.save(update_fields=['is_recording', 'recording_started_at'])
                    
                    return Response({
                        'success': True,
                        'message': 'Recording started',
                        'session_id': session.id,
                        'is_recording': True,
                        'recording_started_at': session.recording_started_at.isoformat()
                    }, status=status.HTTP_200_OK)
                else:
                    error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                    return Response(
                        {'error': error_data.get('error', 'Failed to start recording on SFU server')}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            except requests.exceptions.ConnectionError as e:
                logger.error(f'Error connecting to SFU server at {sfu_base_url}: {e}', exc_info=True)
                return Response(
                    {
                        'error': 'Failed to connect to SFU server. Please ensure the SFU backend is running.',
                        'details': f'Connection refused to {sfu_base_url}. Make sure the SFU backend server is started.'
                    }, 
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            except requests.exceptions.RequestException as e:
                logger.error(f'Error starting recording: {e}', exc_info=True)
                return Response(
                    {'error': 'Failed to connect to SFU server. Please check if the SFU backend is running.'}, 
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
        except Exception as e:
            logger.error(f'Unexpected error in start recording: {e}', exc_info=True)
            return Response(
                {'error': f'An unexpected error occurred: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SessionStopRecordingView(APIView):
    """Stop recording for a live session (teacher only)."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, session_id):
        """Stop recording for a live session."""
        logger.info(f'Stop recording request received for session_id: {session_id}, user: {request.user.id}')
        try:
            session = get_object_or_404(LiveSession, id=session_id)
            
            # Check if user is a teacher of the class or super admin
            is_teacher = session.class_session.teacher.filter(id=request.user.id).exists()
            is_admin = request.user.is_superuser or request.user.role == RoleChoices.SUPER_ADMIN
            
            if not (is_teacher or is_admin):
                return Response(
                    {'error': 'Only teachers and administrators can stop recording'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Note: We don't check session.is_recording here because the SFU backend
            # is the source of truth. It will handle the case where no recording is active.
            # This allows stopping even if there's a state sync issue.
            
            # Call SFU backend to stop recording
            sfu_base_url = os.environ.get('SFU_BASE_URL', 'http://localhost:3001')
            room_id = str(session.id)  # Use session ID as room ID
            
            logger.info(f'Attempting to stop recording on SFU backend: {sfu_base_url}/api/rooms/{room_id}/recording/stop')
            
            try:
                response = requests.post(
                    f'{sfu_base_url}/api/rooms/{room_id}/recording/stop',
                    json={
                        'sessionId': session.id,
                        'stoppedBy': request.user.id
                    },
                    timeout=30  # Longer timeout for file processing
                )
                
                logger.info(f'SFU backend response status: {response.status_code}')
                
                if response.status_code == 200:
                    response_data = response.json()
                    logger.info(f'Recording stopped successfully: {response_data}')
                    
                    # Update session state immediately to reflect UI changes
                    session.is_recording = False
                    session.save(update_fields=['is_recording'])
                    
                    # State will be further updated/confirmed by webhook when recording file is received
                    return Response({
                        'success': True,
                        'message': 'Recording stopped. Processing file...',
                        'session_id': session.id,
                        'duration': response_data.get('duration'),
                        'fileUrl': response_data.get('fileUrl')
                    }, status=status.HTTP_200_OK)
                else:
                    error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                    error_msg = error_data.get('error') or error_data.get('message') or 'Failed to stop recording on SFU server'
                    logger.error(f'SFU backend error: {response.status_code} - {error_msg}')
                    return Response(
                        {'error': error_msg}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            except requests.exceptions.ConnectionError as e:
                logger.error(f'Error connecting to SFU server at {sfu_base_url}: {e}', exc_info=True)
                return Response(
                    {
                        'error': 'Failed to connect to SFU server. Please ensure the SFU backend is running.',
                        'details': f'Connection refused to {sfu_base_url}. Make sure the SFU backend server is started.'
                    }, 
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            except requests.exceptions.RequestException as e:
                logger.error(f'Error stopping recording: {e}', exc_info=True)
                return Response(
                    {'error': 'Failed to connect to SFU server. Please check if the SFU backend is running.'}, 
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
        except Exception as e:
            logger.error(f'Unexpected error in stop recording: {e}', exc_info=True)
            return Response(
                {'error': f'An unexpected error occurred: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SessionRecordingStatusView(APIView):
    """Get recording status for a live session."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, session_id):
        """Get current recording status."""
        session = get_object_or_404(LiveSession, id=session_id)
        
        # Check if user can view this session
        if not session.can_user_join(request.user):
            return Response(
                {'error': 'You do not have access to this session'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        recording_duration = None
        if session.is_recording and session.recording_started_at:
            duration = timezone.now() - session.recording_started_at
            recording_duration = int(duration.total_seconds())
        
        return Response({
            'is_recording': session.is_recording,
            'recording_started_at': session.recording_started_at.isoformat() if session.recording_started_at else None,
            'recording_duration': recording_duration,
            'recording_file': session.recording_file.url if session.recording_file else None,
            'recording_available': session.recording_available
        }, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
class SFUWebhookView(APIView):
    """Receive webhooks from SFU backend.
    
    Handles events like participant.joined, participant.left, room.created, etc.
    """
    permission_classes = []  # No auth required - signature verification instead
    throttle_classes = []  # Exempt from rate limiting - called by SFU backend
    
    def verify_signature(self, event_data, signature_header):
        """Verify webhook signature using HMAC SHA256.
        
        The SFU backend signs the event object (event + data), not the full payload.
        JavaScript's JSON.stringify preserves insertion order, so we reconstruct the object
        in the same order: {'event': ..., 'data': ...}
        """
        webhook_secret = os.environ.get('SFU_WEBHOOK_SECRET', '')
        if not webhook_secret:
            logger.warning('SFU_WEBHOOK_SECRET not set in environment variables')
            return False
        
        # Remove 'sha256=' prefix if present
        signature = signature_header.replace('sha256=', '')
        
        # Reconstruct event object in the same order as JavaScript (event first, then data)
        # This matches how the SFU backend creates and signs the event object
        ordered_event = {'event': event_data['event'], 'data': event_data['data']}
        
        # Calculate expected signature from the event object (event + data)
        # Don't use sort_keys to match JavaScript's JSON.stringify behavior
        event_json = json.dumps(ordered_event, separators=(',', ':'))
        expected_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            event_json.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(signature, expected_signature)
    
    def post(self, request):
        """Handle webhook events from SFU backend."""
        logger.error("=== SFU WEBHOOK HIT ===")
        logger.error(f"Headers: {dict(request.headers)}")
        logger.error(f"Body: {request.body}")
        logger.error(f"Secret from header: {request.headers.get('X-Webhook-Secret')}")
        
        # Check webhook secret first (simpler validation)
        secret = request.headers.get('X-Webhook-Secret')
        expected_secret = os.environ.get('SFU_WEBHOOK_SECRET', '')
        
        if not expected_secret:
            logger.error('SFU_WEBHOOK_SECRET not set in environment variables')
            return Response({'error': 'webhook secret not configured'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        if secret != expected_secret:
            logger.error(f"Invalid secret! Expected: {expected_secret}, Got: {secret}")
            return Response({"error": "invalid secret"}, status=status.HTTP_403_FORBIDDEN)
        
        # Get signature from header (for backward compatibility if needed)
        signature = request.headers.get('X-SFU-Signature', '')
        event_type = request.headers.get('X-SFU-Event', '')
        timestamp = request.headers.get('X-SFU-Timestamp', '')
        
        # Extract event and data from the payload
        event = request.data.get('event')
        data = request.data.get('data', {})
        
        # Reconstruct the event object that was signed (event + data, without timestamp/signature)
        event_object = {
            'event': event,
            'data': data
        }
        
        # Verify signature (optional - secret check above may be sufficient)
        # Uncomment if you want to keep signature verification
        # if not self.verify_signature(event_object, signature):
        #     logger.warning(f'Invalid webhook signature for event: {event_type}')
        #     return Response(
        #         {'error': 'Invalid signature'},
        #         status=status.HTTP_401_UNAUTHORIZED
        #     )
        
        try:
            if event == 'participant.joined':
                self.handle_participant_joined(data)
            elif event == 'participant.left':
                self.handle_participant_left(data)
            elif event == 'room.created':
                self.handle_room_created(data)
            elif event == 'room.ended':
                self.handle_room_ended(data)
            elif event == 'recording.started':
                self.handle_recording_started(data)
            elif event == 'recording.stopped':
                self.handle_recording_stopped(data)
            else:
                logger.info(f'Received unhandled webhook event: {event}')
            
            return Response({'status': 'ok'}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f'Error handling webhook event {event}: {e}', exc_info=True)
            # Still return 200 to prevent SFU from retrying
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_200_OK)
    
    def handle_participant_joined(self, data):
        """Handle participant.joined event."""
        room_id = data.get('roomId')
        user_id = data.get('userId')
        participant_id = data.get('participantId')
        display_name = data.get('displayName')
        joined_at = data.get('joinedAt')
        
        logger.info(f'Participant joined: room={room_id}, user={user_id}, participant={participant_id}, display_name={display_name}')
        
        # You can add database logging or other actions here
        # For example, update session participant count or log to database
    
    def handle_participant_left(self, data):
        """Handle participant.left event."""
        room_id = data.get('roomId')
        user_id = data.get('userId')
        participant_id = data.get('participantId')
        left_at = data.get('leftAt')
        
        logger.info(f'Participant left: room={room_id}, user={user_id}, participant={participant_id}')
    
    def handle_room_created(self, data):
        """Handle room.created event."""
        room_id = data.get('roomId')
        name = data.get('name')
        created_by = data.get('createdBy')
        
        logger.info(f'Room created: room={room_id}, name={name}, created_by={created_by}')
    
    def handle_room_ended(self, data):
        """Handle room.ended event."""
        room_id = data.get('roomId')
        ended_at = data.get('endedAt')
        
        logger.info(f'Room ended: room={room_id}, ended_at={ended_at}')
    
    def handle_recording_started(self, data):
        """Handle recording.started event."""
        room_id = data.get('roomId')
        recording_id = data.get('recordingId')
        started_at = data.get('startedAt')
        session_id = data.get('sessionId')
        
        logger.info(f'Recording started: room={room_id}, recording={recording_id}, session={session_id}, started_at={started_at}')
        
        # Update LiveSession recording state
        try:
            # room_id is the session ID (string)
            session_id_int = int(room_id) if room_id else None
            if session_id:
                session_id_int = int(session_id)
            
            if session_id_int:
                session = LiveSession.objects.filter(id=session_id_int).first()
                if session:
                    session.is_recording = True
                    if started_at:
                        from datetime import datetime
                        try:
                            # Parse ISO format datetime
                            session.recording_started_at = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
                        except:
                            session.recording_started_at = timezone.now()
                    else:
                        session.recording_started_at = timezone.now()
                    session.save(update_fields=['is_recording', 'recording_started_at'])
                    logger.info(f'Updated session {session_id_int} recording state to active')
        except Exception as e:
            logger.error(f'Error updating recording state: {e}', exc_info=True)
    
    def handle_recording_stopped(self, data):
        """Handle recording.stopped event."""
        room_id = data.get('roomId')
        recording_id = data.get('recordingId')
        stopped_at = data.get('stoppedAt')
        duration = data.get('duration')
        session_id = data.get('sessionId')
        file_url = data.get('fileUrl')  # URL to download the file from SFU
        file_path = data.get('filePath')  # Local path if file is uploaded directly
        
        logger.info(f'Recording stopped: room={room_id}, recording={recording_id}, session={session_id}, stopped_at={stopped_at}, duration={duration}')
        
        try:
            # Get session ID
            session_id_int = int(room_id) if room_id else None
            if session_id:
                try:
                    session_id_int = int(session_id)
                except (ValueError, TypeError):
                    pass
            
            if not session_id_int:
                logger.error('No session ID provided in recording.stopped webhook')
                return
            
            session = LiveSession.objects.filter(id=session_id_int).first()
            if not session:
                logger.error(f'Session {session_id_int} not found')
                return
            
            # Update recording state
            session.is_recording = False
            session.save(update_fields=['is_recording'])
            
            # If file URL is provided, download and save the file
            # Note: File should already be uploaded via RecordingUploadView, but we can handle URL as fallback
            if file_url and not session.recording_file:
                try:
                    # Download file from SFU backend
                    response = requests.get(file_url, timeout=300, stream=True)  # 5 minute timeout for large files
                    if response.status_code == 200:
                        from django.core.files.base import ContentFile
                        
                        # Generate filename
                        filename = f'session_{session_id_int}_{recording_id or timezone.now().strftime("%Y%m%d_%H%M%S")}.webm'
                        
                        # Save file
                        file_content = ContentFile(response.content)
                        session.recording_file.save(filename, file_content, save=True)
                        
                        logger.info(f'Saved recording file for session {session_id_int}: {session.recording_file.name}')
                    else:
                        logger.error(f'Failed to download recording file: HTTP {response.status_code}')
                except Exception as e:
                    logger.error(f'Error downloading recording file: {e}', exc_info=True)
            
            # Create Recording object only if we have a file
            if session.recording_file:
                recording_title = f'{session.title} - Recording'
                if stopped_at:
                    from datetime import datetime
                    try:
                        stop_time = datetime.fromisoformat(stopped_at.replace('Z', '+00:00'))
                        recording_title = f'{session.title} - {stop_time.strftime("%Y-%m-%d %H:%M")}'
                    except:
                        pass
                
                # Check if recording already exists for this session
                existing_recording = Recording.objects.filter(session=session).order_by('-created_at').first()
                if existing_recording and not existing_recording.video_url:
                    # Update existing recording
                    existing_recording.video_url = session.recording_file.url
                    existing_recording.title = recording_title
                    existing_recording.save()
                    logger.info(f'Updated Recording object {existing_recording.id} for session {session_id_int}')
                else:
                    # Create new recording
                    recording = Recording.objects.create(
                        session=session,
                        title=recording_title,
                        description=f'Recording of live session: {session.title}',
                        video_url=session.recording_file.url
                    )
                    logger.info(f'Created Recording object {recording.id} for session {session_id_int}')
            
        except Exception as e:
            logger.error(f'Error handling recording stopped: {e}', exc_info=True)


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


@method_decorator(csrf_exempt, name='dispatch')
class RecordingUploadView(APIView):
    """Receive recording file uploads from SFU backend."""
    permission_classes = []  # No auth required - webhook secret validation instead
    throttle_classes = []  # Exempt from rate limiting - called by SFU backend
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        """Handle recording file upload from SFU backend."""
        # Verify webhook secret
        secret = request.headers.get('X-Webhook-Secret', '')
        expected_secret = os.environ.get('SFU_WEBHOOK_SECRET', '')
        
        if not expected_secret or secret != expected_secret:
            logger.warning('Invalid webhook secret for recording upload')
            return Response(
                {'error': 'Invalid webhook secret'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Get file and metadata
            recording_file = request.FILES.get('file')
            room_id = request.data.get('roomId')
            session_id = request.data.get('sessionId')
            
            if not recording_file:
                return Response(
                    {'error': 'No file provided'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if file is empty
            if recording_file.size == 0:
                logger.warning(f'Empty recording file received for room {room_id}')
                return Response(
                    {'error': 'Recording file is empty'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if file is too small to be a valid video (less than 1KB)
            if recording_file.size < 1024:
                logger.warning(f'Recording file too small ({recording_file.size} bytes) for room {room_id}')
                # Still allow it, but log a warning
            
            if not room_id:
                return Response(
                    {'error': 'roomId is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get session
            try:
                session_id_int = int(session_id) if session_id else int(room_id)
                session = LiveSession.objects.get(id=session_id_int)
            except (LiveSession.DoesNotExist, ValueError):
                logger.error(f'Session not found: {session_id_int}')
                return Response(
                    {'error': 'Session not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Save file to session
            session.recording_file = recording_file
            session.save(update_fields=['recording_file'])
            
            # Build file URL
            file_url = request.build_absolute_uri(session.recording_file.url) if session.recording_file else None
            
            logger.info(f'Recording file uploaded for session {session_id_int}: {session.recording_file.name}')
            
            return Response({
                'success': True,
                'fileUrl': file_url,
                'sessionId': session.id,
                'message': 'Recording file uploaded successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f'Error uploading recording file: {e}', exc_info=True)
            return Response(
                {'error': 'Failed to upload recording file'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )