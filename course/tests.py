from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from course.models import Class, LiveSession, SessionStatus
from enrollments.models import ClassEnrollment, EnrollmentChoices
from datetime import datetime, timedelta
from django.utils import timezone

User = get_user_model()


class SessionJoinSecurityTestCase(TestCase):
    """Test cases to ensure users can only join live sessions."""
    
    def setUp(self):
        """Set up test data."""
        # Create users
        self.teacher = User.objects.create_user(
            email='teacher@test.com',
            password='testpass123',
            role='teacher',
            full_name='Test Teacher'
        )
        
        self.student = User.objects.create_user(
            email='student@test.com',
            password='testpass123',
            role='student',
            full_name='Test Student'
        )
        
        # Create a class
        self.test_class = Class.objects.create(
            title='Test Class',
            description='Test Description',
            capacity=30,
            start_time=timezone.now().time(),
            end_time=(timezone.now() + timedelta(hours=1)).time(),
            days_of_week=[1, 3, 5]  # Monday, Wednesday, Friday
        )
        self.test_class.teacher.add(self.teacher)
        
        # Enroll the student
        ClassEnrollment.objects.create(
            student=self.student,
            class_enrolled=self.test_class,
            status=EnrollmentChoices.COMPLETED
        )
        
        # Create sessions with different statuses
        self.scheduled_session = LiveSession.objects.create(
            title='Scheduled Session',
            class_session=self.test_class,
            scheduled_date=timezone.now().date() + timedelta(days=1),
            status=SessionStatus.SCHEDULED
        )
        
        self.live_session = LiveSession.objects.create(
            title='Live Session',
            class_session=self.test_class,
            scheduled_date=timezone.now().date(),
            status=SessionStatus.LIVE
        )
        
        self.completed_session = LiveSession.objects.create(
            title='Completed Session',
            class_session=self.test_class,
            scheduled_date=timezone.now().date() - timedelta(days=1),
            status=SessionStatus.COMPLETED
        )
        
        self.cancelled_session = LiveSession.objects.create(
            title='Cancelled Session',
            class_session=self.test_class,
            scheduled_date=timezone.now().date(),
            status=SessionStatus.CANCELLED
        )
        
        # Set up API client
        self.client = APIClient()
    
    def test_cannot_join_scheduled_session(self):
        """Test that users cannot join a scheduled session."""
        self.client.force_authenticate(user=self.student)
        response = self.client.post(f'/api/course/session/{self.scheduled_session.id}/join/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('not currently live', response.data['error'].lower())
    
    def test_cannot_join_completed_session(self):
        """Test that users cannot join a completed session."""
        self.client.force_authenticate(user=self.student)
        response = self.client.post(f'/api/course/session/{self.completed_session.id}/join/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('not currently live', response.data['error'].lower())
    
    def test_cannot_join_cancelled_session(self):
        """Test that users cannot join a cancelled session."""
        self.client.force_authenticate(user=self.student)
        response = self.client.post(f'/api/course/session/{self.cancelled_session.id}/join/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('not currently live', response.data['error'].lower())
    
    def test_can_join_live_session_when_enrolled(self):
        """Test that enrolled users can join a live session."""
        self.client.force_authenticate(user=self.student)
        response = self.client.post(f'/api/course/session/{self.live_session.id}/join/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('session', response.data)
        self.assertEqual(response.data['session']['status'], 'live')
    
    def test_teacher_can_join_live_session(self):
        """Test that teachers can join their live sessions."""
        self.client.force_authenticate(user=self.teacher)
        response = self.client.post(f'/api/course/session/{self.live_session.id}/join/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['role'], 'moderator')
    
    def test_teacher_cannot_join_non_live_session(self):
        """Test that even teachers cannot join sessions that are not live."""
        self.client.force_authenticate(user=self.teacher)
        response = self.client.post(f'/api/course/session/{self.scheduled_session.id}/join/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('not currently live', response.data['error'].lower())
    
    def test_unauthenticated_user_cannot_join(self):
        """Test that unauthenticated users cannot join any session."""
        response = self.client.post(f'/api/course/session/{self.live_session.id}/join/')
        
        # DRF's IsAuthenticated returns 403 for unauthenticated users
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
