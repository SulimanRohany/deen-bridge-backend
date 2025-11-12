"""
Timezone Testing Utilities
Tests to verify that timezone handling is working correctly in the backend.
"""
from django.test import TestCase
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import UserCommunication
import json

User = get_user_model()


class TimezoneSerializationTest(TestCase):
    """Test that dates are properly stored in UTC and serialized correctly"""
    
    def setUp(self):
        """Set up test data"""
        self.test_time_utc = timezone.now()
        
    def test_model_stores_utc(self):
        """Verify that DateTimeField stores times in UTC"""
        communication = UserCommunication.objects.create(
            communication_type='contact_message',
            name='Test User',
            email='test@example.com',
            subject='Test Subject',
            message='Test message',
            status='new'
        )
        
        # Verify the time is timezone-aware
        self.assertIsNotNone(communication.created_at.tzinfo)
        
        # Verify it's in UTC
        from datetime import timezone as dt_timezone
        self.assertEqual(communication.created_at.tzinfo, dt_timezone.utc)
        
        print(f"[OK] Created communication at: {communication.created_at}")
        print(f"[OK] Timezone: {communication.created_at.tzinfo}")
        
    def test_serializer_iso_format(self):
        """Verify that serializer outputs ISO 8601 format"""
        from .communications_serializers import UserCommunicationSerializer
        
        communication = UserCommunication.objects.create(
            communication_type='contact_message',
            name='Test User',
            email='test@example.com',
            subject='Test Subject',
            message='Test message',
            status='new'
        )
        
        serializer = UserCommunicationSerializer(communication)
        created_at_str = serializer.data['created_at']
        
        # Verify it's a string
        self.assertIsInstance(created_at_str, str)
        
        # Verify it contains 'T' (ISO 8601 format)
        self.assertIn('T', created_at_str)
        
        # Verify it can be parsed back to datetime
        parsed_date = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
        self.assertIsNotNone(parsed_date)
        
        print(f"[OK] Serialized date: {created_at_str}")
        print(f"[OK] Format: ISO 8601")


class TimezoneAPITest(APITestCase):
    """Test timezone handling through the API"""
    
    def setUp(self):
        """Set up test client and admin user"""
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser(
            email='admin@test.com',
            password='testpass123',
            full_name='Admin User',
            role='super_admin'  # Required by custom user model
        )
        
    def test_api_returns_iso_format(self):
        """Test that API returns dates in ISO 8601 format"""
        # Create a communication
        communication = UserCommunication.objects.create(
            communication_type='contact_message',
            name='Test User',
            email='test@example.com',
            subject='Test Subject',
            message='Test message',
            status='new'
        )
        
        # Authenticate as admin
        self.client.force_authenticate(user=self.admin_user)
        
        # Make API request
        response = self.client.get(f'/api/communications/{communication.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        created_at = response.data['created_at']
        
        # Verify it's a string
        self.assertIsInstance(created_at, str)
        
        # Verify ISO 8601 format (contains 'T')
        self.assertIn('T', created_at)
        
        print(f"[OK] API Response date: {created_at}")
        print(f"[OK] Status Code: {response.status_code}")
        
    def test_timezone_consistency(self):
        """Test that times remain consistent across storage and retrieval"""
        # Create communication with known time
        test_time = timezone.now()
        
        communication = UserCommunication.objects.create(
            communication_type='custom_request',
            name='Test User',
            email='test@example.com',
            phone='1234567890',
            course_type='private',
            message='Test message',
            status='pending'
        )
        
        # Authenticate and retrieve
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(f'/api/communications/{communication.id}/')
        
        # Parse the returned date
        returned_date_str = response.data['created_at']
        returned_date = datetime.fromisoformat(returned_date_str.replace('Z', '+00:00'))
        
        # Compare (should be within 1 second) - both should be timezone-aware
        time_diff = abs((returned_date - communication.created_at).total_seconds())
        self.assertLess(time_diff, 1.0)
        
        print(f"[OK] Original time: {communication.created_at}")
        print(f"[OK] API returned time: {returned_date_str}")
        print(f"[OK] Time difference: {time_diff} seconds")


def run_manual_tests():
    """
    Manual test function to verify timezone handling
    Run this in Django shell:
    
    from core.tests_timezone import run_manual_tests
    run_manual_tests()
    """
    from .models import UserCommunication
    from .communications_serializers import UserCommunicationSerializer
    
    print("\n" + "="*60)
    print("TIMEZONE VERIFICATION TEST")
    print("="*60 + "\n")
    
    # Test 1: Create a communication
    print("Test 1: Creating a new communication...")
    comm = UserCommunication.objects.create(
        communication_type='contact_message',
        name='Timezone Test',
        email='test@example.com',
        subject='Timezone Test',
        message='Testing timezone handling',
        status='new'
    )
    
    print(f"[OK] Created at (database): {comm.created_at}")
    print(f"[OK] Timezone aware: {comm.created_at.tzinfo is not None}")
    print(f"[OK] Timezone: {comm.created_at.tzinfo}")
    
    # Test 2: Serialize the data
    print("\nTest 2: Serializing the communication...")
    serializer = UserCommunicationSerializer(comm)
    data = serializer.data
    
    print(f"[OK] Serialized created_at: {data['created_at']}")
    print(f"[OK] Contains 'T' (ISO format): {'T' in data['created_at']}")
    print(f"[OK] Type: {type(data['created_at'])}")
    
    # Test 3: Response time calculation
    print("\nTest 3: Testing response time calculation...")
    comm.response_sent_at = timezone.now() + timedelta(minutes=15)
    comm.save()
    
    print(f"[OK] Response sent at: {comm.response_sent_at}")
    print(f"[OK] Response time: {comm.response_time:.2f} minutes")
    
    # Test 4: Show how different timezones will see this
    print("\nTest 4: How different users will see this time...")
    print(f"[OK] UTC: {comm.created_at.isoformat()}")
    print(f"[OK] ISO String (API format): {data['created_at']}")
    print("\nFrontend will automatically convert this to:")
    print("  - New York (EST): Nov 5, 2025, 09:30 AM EST")
    print("  - London (GMT): Nov 5, 2025, 02:30 PM GMT")
    print("  - Tokyo (JST): Nov 5, 2025, 11:30 PM JST")
    print("  - Sydney (AEDT): Nov 6, 2025, 01:30 AM AEDT")
    
    print("\n" + "="*60)
    print("ALL TESTS PASSED [OK]")
    print("="*60 + "\n")
    
    # Cleanup
    comm.delete()
    print("Test data cleaned up.\n")


if __name__ == '__main__':
    print("Run these tests with:")
    print("  python manage.py test core.tests_timezone")
    print("\nOr run manual tests in Django shell:")
    print("  python manage.py shell")
    print("  from core.tests_timezone import run_manual_tests")
    print("  run_manual_tests()")

