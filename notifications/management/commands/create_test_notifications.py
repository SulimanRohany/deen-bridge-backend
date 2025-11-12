from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from notifications.models import Notification, NotificationType, NotificationChannels
from datetime import datetime, timedelta
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Create test notifications for all users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Create notifications for a specific user ID',
        )
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Number of notifications to create per user (default: 10)',
        )

    def handle(self, *args, **options):
        user_id = options.get('user_id')
        count = options.get('count')

        if user_id:
            try:
                users = [User.objects.get(id=user_id)]
                self.stdout.write(f"Creating notifications for user ID {user_id}...")
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"User with ID {user_id} not found"))
                return
        else:
            users = User.objects.all()
            self.stdout.write(f"Creating notifications for all {users.count()} users...")

        notification_templates = [
            {
                'type': NotificationType.COURSE,
                'title': 'New Course Available',
                'body': 'A new Islamic Studies course has been added to the catalog. Check it out!',
                'action_url': '/courses',
            },
            {
                'type': NotificationType.ENROLLMENT,
                'title': 'Enrollment Confirmed',
                'body': 'Your enrollment in "Tajweed Basics" has been confirmed. Classes start next week.',
                'action_url': '/my-learning',
            },
            {
                'type': NotificationType.SESSION,
                'title': 'Upcoming Session',
                'body': 'You have a live session starting in 1 hour. Make sure to join on time!',
                'action_url': '/sessions',
            },
            {
                'type': NotificationType.LIBRARY,
                'title': 'New Book Added',
                'body': 'A new book "The Life of Prophet Muhammad (PBUH)" has been added to the library.',
                'action_url': '/library',
            },
            {
                'type': NotificationType.SUCCESS,
                'title': 'Assignment Submitted',
                'body': 'Your assignment has been successfully submitted and is under review.',
                'action_url': '/profile',
            },
            {
                'type': NotificationType.WARNING,
                'title': 'Payment Due',
                'body': 'Your course payment is due in 3 days. Please complete the payment to continue.',
                'action_url': '/profile',
            },
            {
                'type': NotificationType.INFO,
                'title': 'System Maintenance',
                'body': 'The platform will undergo maintenance on Sunday from 2 AM to 4 AM.',
                'action_url': None,
            },
            {
                'type': NotificationType.COURSE,
                'title': 'Course Update',
                'body': 'New materials have been added to your "Quran Memorization" course.',
                'action_url': '/courses',
            },
            {
                'type': NotificationType.SESSION,
                'title': 'Session Recorded',
                'body': 'Your last session recording is now available. You can review it anytime.',
                'action_url': '/recordings',
            },
            {
                'type': NotificationType.SUCCESS,
                'title': 'Certificate Earned',
                'body': 'Congratulations! You\'ve earned a certificate for completing "Arabic Basics".',
                'action_url': '/profile',
            },
            {
                'type': NotificationType.ENROLLMENT,
                'title': 'New Student Enrolled',
                'body': 'A new student has enrolled in your class. Welcome them!',
                'action_url': '/dashboard',
            },
            {
                'type': NotificationType.LIBRARY,
                'title': 'Book Review Posted',
                'body': 'Someone reviewed the book you recommended. Check out what they said!',
                'action_url': '/library',
            },
        ]

        total_created = 0

        for user in users:
            # Create random notifications
            for i in range(count):
                template = random.choice(notification_templates)
                
                # Randomly decide if notification should be read
                is_read = random.choice([True, False, False])  # 33% read, 67% unread
                
                notification = Notification.objects.create(
                    user=user,
                    channel=NotificationChannels.IN_APP,
                    type=template['type'],
                    title=template['title'],
                    body=template['body'],
                    action_url=template['action_url'],
                    status='sent',
                    sent_at=datetime.now(),
                    read_at=datetime.now() if is_read else None,
                )
                
                total_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {total_created} test notifications for {len(users)} user(s)"
            )
        )

