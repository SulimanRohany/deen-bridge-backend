"""
Test script for the notification system

This script can be run to test the notification functionality.
It creates test users and verifies that notifications are sent correctly.
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db import models
from notifications.models import Notification, NotificationType
from notifications.utils import send_notification, send_notification_to_multiple_users
from accounts.models import RoleChoices

User = get_user_model()


def test_single_notification():
    """Test sending a notification to a single user"""
    print("\n=== Testing Single Notification ===")
    
    # Get or create a test user
    user, created = User.objects.get_or_create(
        email='test@example.com',
        defaults={
            'full_name': 'Test User',
            'role': RoleChoices.STUDENT,
        }
    )
    
    if created:
        user.set_password('password123')
        user.save()
        print(f"Created test user: {user.email}")
    else:
        print(f"Using existing test user: {user.email}")
    
    # Send a test notification
    notification = send_notification(
        user=user,
        title="Test Notification",
        body="This is a test notification to verify the system is working.",
        notification_type=NotificationType.INFO,
        action_url="/test/",
        metadata={'test': True}
    )
    
    print(f"✓ Notification created: ID={notification.id}")
    print(f"  Title: {notification.title}")
    print(f"  Body: {notification.body}")
    print(f"  Type: {notification.type}")
    print(f"  Sent at: {notification.sent_at}")
    
    return notification


def test_super_admin_notification():
    """Test that super admins receive notifications when a new user is created"""
    print("\n=== Testing Super Admin Notification on User Registration ===")
    
    # Get or create a super admin
    super_admin, created = User.objects.get_or_create(
        email='admin@example.com',
        defaults={
            'full_name': 'Super Admin',
            'role': RoleChoices.SUPER_ADMIN,
            'is_staff': True,
            'is_superuser': True,
        }
    )
    
    if created:
        super_admin.set_password('admin123')
        super_admin.save()
        print(f"Created super admin: {super_admin.email}")
    else:
        print(f"Using existing super admin: {super_admin.email}")
    
    # Get count of notifications before
    notification_count_before = Notification.objects.filter(user=super_admin).count()
    print(f"Super admin notifications before: {notification_count_before}")
    
    # Create a new user (this should trigger the signal)
    new_user = User.objects.create(
        email=f'newuser_{User.objects.count()}@example.com',
        full_name='New Test User',
        role=RoleChoices.TEACHER,
    )
    new_user.set_password('password123')
    new_user.save()
    
    print(f"✓ Created new user: {new_user.email} ({new_user.role})")
    
    # Check if notification was created
    notification_count_after = Notification.objects.filter(user=super_admin).count()
    print(f"Super admin notifications after: {notification_count_after}")
    
    if notification_count_after > notification_count_before:
        latest_notification = Notification.objects.filter(user=super_admin).latest('created_at')
        print(f"✓ New notification created:")
        print(f"  ID: {latest_notification.id}")
        print(f"  Title: {latest_notification.title}")
        print(f"  Body: {latest_notification.body}")
        print(f"  Type: {latest_notification.type}")
        print(f"  Metadata: {latest_notification.metadata}")
        print(f"  Action URL: {latest_notification.action_url}")
        return True
    else:
        print("✗ No new notification created!")
        return False


def test_multiple_super_admins():
    """Test that multiple super admins receive notifications"""
    print("\n=== Testing Multiple Super Admins ===")
    
    # Create multiple super admins
    super_admins = []
    for i in range(3):
        email = f'superadmin{i}@example.com'
        super_admin, created = User.objects.get_or_create(
            email=email,
            defaults={
                'full_name': f'Super Admin {i}',
                'role': RoleChoices.SUPER_ADMIN,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            super_admin.set_password('admin123')
            super_admin.save()
            print(f"Created super admin: {email}")
        else:
            print(f"Using existing super admin: {email}")
        super_admins.append(super_admin)
    
    # Get notification counts before
    counts_before = [Notification.objects.filter(user=sa).count() for sa in super_admins]
    print(f"Notification counts before: {counts_before}")
    
    # Create a new user
    new_user = User.objects.create(
        email=f'multitest_{User.objects.count()}@example.com',
        full_name='Multi Test User',
        role=RoleChoices.STUDENT,
    )
    new_user.set_password('password123')
    new_user.save()
    
    print(f"✓ Created new user: {new_user.email}")
    
    # Check notification counts after
    counts_after = [Notification.objects.filter(user=sa).count() for sa in super_admins]
    print(f"Notification counts after: {counts_after}")
    
    # Verify all super admins got a notification
    all_received = all(after > before for before, after in zip(counts_before, counts_after))
    
    if all_received:
        print(f"✓ All {len(super_admins)} super admins received the notification!")
        return True
    else:
        print("✗ Not all super admins received the notification!")
        return False


def test_notification_utilities():
    """Test the notification utility functions"""
    print("\n=== Testing Notification Utilities ===")
    
    # Create test users
    users = []
    for role in [RoleChoices.STUDENT, RoleChoices.TEACHER, RoleChoices.PARENT]:
        user, created = User.objects.get_or_create(
            email=f'util_test_{role}@example.com',
            defaults={
                'full_name': f'Util Test {role}',
                'role': role,
            }
        )
        if created:
            user.set_password('password123')
            user.save()
        users.append(user)
    
    print(f"Created/retrieved {len(users)} test users")
    
    # Test send_notification_to_multiple_users
    notifications = send_notification_to_multiple_users(
        users=users,
        title="Bulk Test Notification",
        body="This notification was sent to multiple users at once.",
        notification_type=NotificationType.SYSTEM,
        action_url="/system/announcement/",
        metadata={'bulk_test': True}
    )
    
    print(f"✓ Sent {len(notifications)} notifications")
    for notif in notifications:
        print(f"  - User: {notif.user.email}, ID: {notif.id}")
    
    return len(notifications) == len(users)


def cleanup_test_data():
    """Clean up test data (optional)"""
    print("\n=== Cleanup Test Data ===")
    response = input("Do you want to delete test users and notifications? (yes/no): ")
    
    if response.lower() == 'yes':
        # Delete test notifications
        test_notifications = Notification.objects.filter(
            models.Q(metadata__test=True) | models.Q(metadata__bulk_test=True)
        )
        notif_count = test_notifications.count()
        test_notifications.delete()
        print(f"Deleted {notif_count} test notifications")
        
        # Delete test users
        test_users = User.objects.filter(email__contains='test')
        user_count = test_users.count()
        test_users.delete()
        print(f"Deleted {user_count} test users")
    else:
        print("Skipping cleanup")


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("NOTIFICATION SYSTEM TEST SUITE")
    print("=" * 60)
    
    results = []
    
    # Test 1: Single notification
    try:
        test_single_notification()
        results.append(("Single Notification", True))
    except Exception as e:
        print(f"✗ Error: {e}")
        results.append(("Single Notification", False))
    
    # Test 2: Super admin notification on user registration
    try:
        success = test_super_admin_notification()
        results.append(("Super Admin Notification", success))
    except Exception as e:
        print(f"✗ Error: {e}")
        results.append(("Super Admin Notification", False))
    
    # Test 3: Multiple super admins
    try:
        success = test_multiple_super_admins()
        results.append(("Multiple Super Admins", success))
    except Exception as e:
        print(f"✗ Error: {e}")
        results.append(("Multiple Super Admins", False))
    
    # Test 4: Notification utilities
    try:
        success = test_notification_utilities()
        results.append(("Notification Utilities", success))
    except Exception as e:
        print(f"✗ Error: {e}")
        results.append(("Notification Utilities", False))
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status} - {test_name}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 60)


if __name__ == '__main__':
    run_all_tests()
    # Optionally cleanup
    # cleanup_test_data()

