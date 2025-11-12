"""
Django Seeder Script for Backend Models
This script creates sample data for all models in the backend application.
Run with: python manage.py shell < seed_data.py
"""

import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from accounts.models import CustomUser, RoleChoices
from subjects.models import Subject
from core.models import CompanySetting, CompanyContact
from profiles.models import TeacherProfile, StudentProfile, SuperAdminProfile, StaffProfile, StudentParentProfile, GenderChoices
from course.models import Course, CourseTimeTable, LiveSession, Recording, Attendance, Certificate, MeetChoices, SessionStatus, AttendanceStatus
from enrollments.models import CourseEnrollment, EnrollmentChoices
from blogs.models import Post, Comment
from notifications.models import Notification, NotificationChannels, NotificationStatus
from reports.models import Report
from sfu.models import SessionParticipant, Track, SignalingMessage

User = get_user_model()

def create_sample_image():
    """Create a simple test image file"""
    # Create a minimal 1x1 pixel PNG
    png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xdd\x8d\xb4\x1c\x00\x00\x00\x00IEND\xaeB`\x82'
    return SimpleUploadedFile("test.png", png_data, content_type="image/png")

def clear_existing_data():
    """Clear existing data (optional - be careful in production!)"""
    print("Clearing existing data...")
    
    # Clear in reverse dependency order
    SignalingMessage.objects.all().delete()
    Track.objects.all().delete()
    SessionParticipant.objects.all().delete()
    Attendance.objects.all().delete()
    Recording.objects.all().delete()
    LiveSession.objects.all().delete()
    CourseEnrollment.objects.all().delete()
    Certificate.objects.all().delete()
    Comment.objects.all().delete()
    Post.objects.all().delete()
    Notification.objects.all().delete()
    Report.objects.all().delete()
    StudentParentProfile.objects.all().delete()
    StudentProfile.objects.all().delete()
    TeacherProfile.objects.all().delete()
    SuperAdminProfile.objects.all().delete()
    StaffProfile.objects.all().delete()
    CourseTimeTable.objects.all().delete()
    Course.objects.all().delete()
    Subject.objects.all().delete()
    CompanySetting.objects.all().delete()
    CompanyContact.objects.all().delete()
    CustomUser.objects.all().delete()
    
    print("Existing data cleared.")

def create_users():
    """Create sample users for all roles"""
    print("Creating users...")
    
    users = {}
    
    # Super Admin
    users['super_admin'] = User.objects.create_user(
        email='admin@deenbridge.com',
        password='admin123',
        full_name='Super Admin',
        role=RoleChoices.SUPER_ADMIN,
        is_staff=True,
        is_superuser=True
    )
    
    # Staff
    users['staff1'] = User.objects.create_user(
        email='staff1@deenbridge.com',
        password='staff123',
        full_name='John Staff',
        role=RoleChoices.STAFF,
        is_staff=True
    )
    
    users['staff2'] = User.objects.create_user(
        email='staff2@deenbridge.com',
        password='staff123',
        full_name='Jane Staff',
        role=RoleChoices.STAFF,
        is_staff=True
    )
    
    # Teachers
    users['teacher1'] = User.objects.create_user(
        email='teacher1@deenbridge.com',
        password='teacher123',
        full_name='Dr. Ahmed Hassan',
        role=RoleChoices.TEACHER
    )
    
    users['teacher2'] = User.objects.create_user(
        email='teacher2@deenbridge.com',
        password='teacher123',
        full_name='Ustadha Fatima Ali',
        role=RoleChoices.TEACHER
    )
    
    users['teacher3'] = User.objects.create_user(
        email='teacher3@deenbridge.com',
        password='teacher123',
        full_name='Sheikh Omar Ibrahim',
        role=RoleChoices.TEACHER
    )
    
    # Students
    users['student1'] = User.objects.create_user(
        email='student1@deenbridge.com',
        password='student123',
        full_name='Aisha Mohammed',
        role=RoleChoices.STUDENT
    )
    
    users['student2'] = User.objects.create_user(
        email='student2@deenbridge.com',
        password='student123',
        full_name='Hassan Ali',
        role=RoleChoices.STUDENT
    )
    
    users['student3'] = User.objects.create_user(
        email='student3@deenbridge.com',
        password='student123',
        full_name='Maryam Ahmed',
        role=RoleChoices.STUDENT
    )
    
    users['student4'] = User.objects.create_user(
        email='student4@deenbridge.com',
        password='student123',
        full_name='Yusuf Ibrahim',
        role=RoleChoices.STUDENT
    )
    
    # Parents
    users['parent1'] = User.objects.create_user(
        email='parent1@deenbridge.com',
        password='parent123',
        full_name='Mohammed Ali (Parent)',
        role=RoleChoices.PARENT
    )
    
    users['parent2'] = User.objects.create_user(
        email='parent2@deenbridge.com',
        password='parent123',
        full_name='Amina Hassan (Parent)',
        role=RoleChoices.PARENT
    )
    
    print(f"Created {len(users)} users")
    return users

def create_company_data():
    """Create company settings and contacts"""
    print("Creating company data...")
    
    # Create company contacts
    contact1 = CompanyContact.objects.create(
        department='Academic Affairs',
        email='academic@deenbridge.com',
        phone_number='+1-555-0101'
    )
    
    contact2 = CompanyContact.objects.create(
        department='Technical Support',
        email='support@deenbridge.com',
        phone_number='+1-555-0102'
    )
    
    contact3 = CompanyContact.objects.create(
        department='Student Services',
        email='students@deenbridge.com',
        phone_number='+1-555-0103'
    )
    
    # Create company settings
    company_setting = CompanySetting.objects.create(
        default_timezone='America/New_York'
    )
    company_setting.contact.add(contact1, contact2, contact3)
    
    print("Company data created")
    return company_setting

def create_subjects():
    """Create sample subjects"""
    print("Creating subjects...")
    
    subjects = {}
    subject_data = [
        ('Quran Recitation', 'Learn proper Quran recitation with Tajweed rules'),
        ('Arabic Language', 'Comprehensive Arabic language learning'),
        ('Islamic History', 'Study of Islamic civilization and history'),
        ('Fiqh', 'Islamic jurisprudence and legal studies'),
        ('Hadith', 'Study of Prophet Muhammad\'s sayings and traditions'),
        ('Tafseer', 'Quranic interpretation and exegesis'),
        ('Aqeedah', 'Islamic creed and theology'),
        ('Seerah', 'Biography of Prophet Muhammad (PBUH)'),
        ('Memorization', 'Quran memorization techniques and practice'),
        ('Islamic Ethics', 'Moral and ethical teachings in Islam')
    ]
    
    for name, description in subject_data:
        subjects[name.lower().replace(' ', '_')] = Subject.objects.create(
            name=name,
            description=description
        )
    
    print(f"Created {len(subjects)} subjects")
    return subjects

def create_profiles(users):
    """Create user profiles"""
    print("Creating user profiles...")
    
    # Super Admin Profile
    SuperAdminProfile.objects.create(
        user=users['super_admin'],
        address='123 Admin Street, City, State',
        gender=GenderChoices.MALE,
        phone_number='+1-555-0000',
        date_of_birth=timezone.now().date() - timedelta(days=30*365),
        preferred_timezone='America/New_York',
        preferred_language='en'
    )
    
    # Staff Profiles
    StaffProfile.objects.create(
        user=users['staff1'],
        address='456 Staff Avenue, City, State',
        gender=GenderChoices.MALE,
        phone_number='+1-555-1001',
        date_of_birth=timezone.now().date() - timedelta(days=25*365),
        position='Academic Coordinator',
        preferred_timezone='America/New_York',
        preferred_language='en'
    )
    
    StaffProfile.objects.create(
        user=users['staff2'],
        address='789 Staff Boulevard, City, State',
        gender=GenderChoices.FEMALE,
        phone_number='+1-555-1002',
        date_of_birth=timezone.now().date() - timedelta(days=28*365),
        position='Student Affairs Manager',
        preferred_timezone='America/New_York',
        preferred_language='en'
    )
    
    # Teacher Profiles
    TeacherProfile.objects.create(
        user=users['teacher1'],
        address='321 Teacher Lane, City, State',
        gender=GenderChoices.MALE,
        phone_number='+1-555-2001',
        date_of_birth=timezone.now().date() - timedelta(days=35*365),
        department='Quran Studies',
        specialization='Tajweed and Quran Recitation',
        qualification='PhD in Islamic Studies, Al-Azhar University',
        bio='Experienced Quran teacher with over 15 years of teaching experience.',
        preferred_timezone='America/New_York',
        preferred_language='en'
    )
    
    TeacherProfile.objects.create(
        user=users['teacher2'],
        address='654 Teacher Street, City, State',
        gender=GenderChoices.FEMALE,
        phone_number='+1-555-2002',
        date_of_birth=timezone.now().date() - timedelta(days=32*365),
        department='Arabic Language',
        specialization='Modern Standard Arabic and Classical Arabic',
        qualification='MA in Arabic Language, University of Damascus',
        bio='Dedicated Arabic language instructor specializing in both classical and modern Arabic.',
        preferred_timezone='America/New_York',
        preferred_language='ar'
    )
    
    TeacherProfile.objects.create(
        user=users['teacher3'],
        address='987 Teacher Avenue, City, State',
        gender=GenderChoices.MALE,
        phone_number='+1-555-2003',
        date_of_birth=timezone.now().date() - timedelta(days=40*365),
        department='Islamic Studies',
        specialization='Fiqh and Islamic History',
        qualification='PhD in Islamic Jurisprudence, Islamic University of Medina',
        bio='Scholar with extensive knowledge in Islamic jurisprudence and history.',
        preferred_timezone='America/New_York',
        preferred_language='en'
    )
    
    # Student Profiles
    student1_profile = StudentProfile.objects.create(
        user=users['student1'],
        address='111 Student Street, City, State',
        gender=GenderChoices.FEMALE,
        phone_number='+1-555-3001',
        date_of_birth=timezone.now().date() - timedelta(days=18*365),
        is_paid=True,
        is_minor=False,
        preferred_timezone='America/New_York',
        preferred_language='en'
    )
    
    student2_profile = StudentProfile.objects.create(
        user=users['student2'],
        address='222 Student Avenue, City, State',
        gender=GenderChoices.MALE,
        phone_number='+1-555-3002',
        date_of_birth=timezone.now().date() - timedelta(days=20*365),
        is_paid=True,
        is_minor=False,
        preferred_timezone='America/New_York',
        preferred_language='en'
    )
    
    student3_profile = StudentProfile.objects.create(
        user=users['student3'],
        address='333 Student Lane, City, State',
        gender=GenderChoices.FEMALE,
        phone_number='+1-555-3003',
        date_of_birth=timezone.now().date() - timedelta(days=14*365),  # Minor
        is_paid=False,
        is_minor=True,
        preferred_timezone='America/New_York',
        preferred_language='en'
    )
    
    student4_profile = StudentProfile.objects.create(
        user=users['student4'],
        address='444 Student Boulevard, City, State',
        gender=GenderChoices.MALE,
        phone_number='+1-555-3004',
        date_of_birth=timezone.now().date() - timedelta(days=22*365),
        is_paid=True,
        is_minor=False,
        preferred_timezone='America/New_York',
        preferred_language='en'
    )
    
    # Parent Profiles
    StudentParentProfile.objects.create(
        user=users['parent1'],
        student=student3_profile,
        relationship='Father',
        preferred_language='en'
    )
    
    StudentParentProfile.objects.create(
        user=users['parent2'],
        student=student1_profile,
        relationship='Mother',
        preferred_language='en'
    )
    
    print("User profiles created")
    return {
        'student1': student1_profile,
        'student2': student2_profile,
        'student3': student3_profile,
        'student4': student4_profile
    }

def create_courses_and_timetables(users, subjects):
    """Create courses and their timetables"""
    print("Creating courses and timetables...")
    
    courses = {}
    
    # Course 1: Quran Recitation
    course1 = Course.objects.create(
        title='Quran Recitation with Tajweed',
        description='Learn proper Quran recitation with correct pronunciation and Tajweed rules.',
        capacity=15,
        price=Decimal('150.00'),
        is_special_class=False
    )
    course1.teacher.add(users['teacher1'])
    course1.subject.add(subjects['quran_recitation'])
    
    # Course 2: Arabic Language
    course2 = Course.objects.create(
        title='Modern Standard Arabic',
        description='Comprehensive Arabic language course covering reading, writing, and conversation.',
        capacity=20,
        price=Decimal('200.00'),
        is_special_class=False
    )
    course2.teacher.add(users['teacher2'])
    course2.subject.add(subjects['arabic_language'])
    
    # Course 3: Islamic History
    course3 = Course.objects.create(
        title='Islamic Civilization and History',
        description='Study the rich history of Islamic civilization from its inception to modern times.',
        capacity=25,
        price=Decimal('120.00'),
        is_special_class=False
    )
    course3.teacher.add(users['teacher3'])
    course3.subject.add(subjects['islamic_history'])
    
    # Course 4: Special Fiqh Course
    course4 = Course.objects.create(
        title='Advanced Fiqh Studies',
        description='Advanced study of Islamic jurisprudence for serious students.',
        capacity=10,
        price=Decimal('300.00'),
        is_special_class=True
    )
    course4.teacher.add(users['teacher3'])
    course4.subject.add(subjects['fiqh'])
    
    courses = {
        'quran': course1,
        'arabic': course2,
        'history': course3,
        'fiqh': course4
    }
    
    # Create timetables
    timetables = {}
    
    # Quran Course Timetable (Monday, Wednesday, Friday)
    timetables['quran'] = CourseTimeTable.objects.create(
        course=course1,
        days_of_week=[0, 2, 4],  # Monday, Wednesday, Friday
        start_time=timezone.now().time().replace(hour=18, minute=0),
        end_time=timezone.now().time().replace(hour=19, minute=30),
        timezone='America/New_York',
        is_active=True
    )
    
    # Arabic Course Timetable (Tuesday, Thursday)
    timetables['arabic'] = CourseTimeTable.objects.create(
        course=course2,
        days_of_week=[1, 3],  # Tuesday, Thursday
        start_time=timezone.now().time().replace(hour=19, minute=0),
        end_time=timezone.now().time().replace(hour=20, minute=30),
        timezone='America/New_York',
        is_active=True
    )
    
    # History Course Timetable (Saturday, Sunday)
    timetables['history'] = CourseTimeTable.objects.create(
        course=course3,
        days_of_week=[5, 6],  # Saturday, Sunday
        start_time=timezone.now().time().replace(hour=10, minute=0),
        end_time=timezone.now().time().replace(hour=11, minute=30),
        timezone='America/New_York',
        is_active=True
    )
    
    # Fiqh Course Timetable (Monday, Wednesday)
    timetables['fiqh'] = CourseTimeTable.objects.create(
        course=course4,
        days_of_week=[0, 2],  # Monday, Wednesday
        start_time=timezone.now().time().replace(hour=20, minute=0),
        end_time=timezone.now().time().replace(hour=21, minute=30),
        timezone='America/New_York',
        is_active=True
    )
    
    print(f"Created {len(courses)} courses and {len(timetables)} timetables")
    return courses, timetables

def create_enrollments(users, timetables):
    """Create course enrollments"""
    print("Creating enrollments...")
    
    enrollments = []
    
    # Student 1 enrollments
    enrollments.append(CourseEnrollment.objects.create(
        student=users['student1'],
        timetable=timetables['quran'],
        status=EnrollmentChoices.COMPLETED,
        enrolled_at=timezone.now() - timedelta(days=30),
        price=Decimal('150.00'),
        payment_ref='PAY-001'
    ))
    
    enrollments.append(CourseEnrollment.objects.create(
        student=users['student1'],
        timetable=timetables['arabic'],
        status=EnrollmentChoices.COMPLETED,
        enrolled_at=timezone.now() - timedelta(days=25),
        price=Decimal('200.00'),
        payment_ref='PAY-002'
    ))
    
    # Student 2 enrollments
    enrollments.append(CourseEnrollment.objects.create(
        student=users['student2'],
        timetable=timetables['quran'],
        status=EnrollmentChoices.COMPLETED,
        enrolled_at=timezone.now() - timedelta(days=28),
        price=Decimal('150.00'),
        payment_ref='PAY-003'
    ))
    
    enrollments.append(CourseEnrollment.objects.create(
        student=users['student2'],
        timetable=timetables['history'],
        status=EnrollmentChoices.COMPLETED,
        enrolled_at=timezone.now() - timedelta(days=20),
        price=Decimal('120.00'),
        payment_ref='PAY-004'
    ))
    
    # Student 3 enrollments (minor - pending parent approval)
    enrollments.append(CourseEnrollment.objects.create(
        student=users['student3'],
        timetable=timetables['quran'],
        status=EnrollmentChoices.PENDING,
        price=Decimal('150.00')
    ))
    
    # Student 4 enrollments
    enrollments.append(CourseEnrollment.objects.create(
        student=users['student4'],
        timetable=timetables['arabic'],
        status=EnrollmentChoices.COMPLETED,
        enrolled_at=timezone.now() - timedelta(days=15),
        price=Decimal('200.00'),
        payment_ref='PAY-005'
    ))
    
    enrollments.append(CourseEnrollment.objects.create(
        student=users['student4'],
        timetable=timetables['fiqh'],
        status=EnrollmentChoices.COMPLETED,
        enrolled_at=timezone.now() - timedelta(days=10),
        price=Decimal('300.00'),
        payment_ref='PAY-006'
    ))
    
    print(f"Created {len(enrollments)} enrollments")
    return enrollments

def create_live_sessions(timetables):
    """Create live sessions"""
    print("Creating live sessions...")
    
    sessions = []
    
    # Create sessions for the past week and upcoming week
    for i in range(14):  # 2 weeks
        date = timezone.now().date() - timedelta(days=7-i)
        
        for timetable_name, timetable in timetables.items():
            # Check if this day of week matches the timetable
            if date.weekday() in timetable.days_of_week:
                session = LiveSession.objects.create(
                    title=f'{timetable.course.title} - Session {i+1}',
                    timetable=timetable,
                    auto_record=True,
                    status=SessionStatus.COMPLETED if i < 7 else SessionStatus.SCHEDULED
                )
                sessions.append(session)
    
    print(f"Created {len(sessions)} live sessions")
    return sessions

def create_recordings(sessions):
    """Create recordings for completed sessions"""
    print("Creating recordings...")
    
    recordings = []
    completed_sessions = [s for s in sessions if s.status == SessionStatus.COMPLETED]
    
    for i, session in enumerate(completed_sessions[:5]):  # Only first 5 completed sessions
        recording = Recording.objects.create(
            session=session,
            title=f'Recording of {session.title}',
            description=f'Full recording of the {session.title} session',
            video_url=f'https://recordings.deenbridge.com/session_{session.id}.mp4'
        )
        recordings.append(recording)
    
    print(f"Created {len(recordings)} recordings")
    return recordings

def create_attendance(enrollments, sessions):
    """Create attendance records"""
    print("Creating attendance records...")
    
    attendance_records = []
    completed_sessions = [s for s in sessions if s.status == SessionStatus.COMPLETED]
    
    for session in completed_sessions:
        # Find enrollments for this session's course
        session_enrollments = [e for e in enrollments if e.timetable == session.timetable]
        
        for enrollment in session_enrollments:
            # Randomly assign attendance status
            import random
            status = random.choice([AttendanceStatus.PRESENT, AttendanceStatus.ABSENT])
            
            if status == AttendanceStatus.PRESENT:
                joined_at = session.created_at + timedelta(minutes=random.randint(0, 10))
                left_at = joined_at + timedelta(minutes=random.randint(60, 90))
            else:
                joined_at = None
                left_at = None
            
            attendance = Attendance.objects.create(
                course_enrollment=enrollment,
                session=session,
                joined_at=joined_at,
                left_at=left_at,
                status=status,
                device_info={'browser': 'Chrome', 'os': 'Windows'}
            )
            attendance_records.append(attendance)
    
    print(f"Created {len(attendance_records)} attendance records")
    return attendance_records

def create_certificates(users, courses):
    """Create certificates for completed courses"""
    print("Creating certificates...")
    
    certificates = []
    
    # Student 1 certificates
    certificates.append(Certificate.objects.create(
        student=users['student1'],
        course=courses['quran'],
        issued_at=timezone.now() - timedelta(days=5),
        pdf_url='https://certificates.deenbridge.com/cert_001.pdf'
    ))
    
    certificates.append(Certificate.objects.create(
        student=users['student1'],
        course=courses['arabic'],
        issued_at=timezone.now() - timedelta(days=2),
        pdf_url='https://certificates.deenbridge.com/cert_002.pdf'
    ))
    
    # Student 2 certificates
    certificates.append(Certificate.objects.create(
        student=users['student2'],
        course=courses['quran'],
        issued_at=timezone.now() - timedelta(days=3),
        pdf_url='https://certificates.deenbridge.com/cert_003.pdf'
    ))
    
    print(f"Created {len(certificates)} certificates")
    return certificates

def create_blog_posts(users):
    """Create blog posts and comments"""
    print("Creating blog posts...")
    
    posts = []
    
    # Create blog posts (only staff can be authors)
    post1 = Post.objects.create(
        author=users['staff1'],
        title='Welcome to Deen Bridge Online Learning Platform',
        body='We are excited to announce the launch of our comprehensive online Islamic education platform. Our mission is to provide quality Islamic education to students worldwide through modern technology and traditional teaching methods.',
        status='published',
        slug='welcome-deen-bridge-platform'
    )
    post1.tags.add('announcement', 'welcome', 'education')
    posts.append(post1)
    
    post2 = Post.objects.create(
        author=users['staff2'],
        title='Tips for Effective Online Learning',
        body='Online learning requires discipline and effective study habits. Here are some proven strategies to help you succeed in your Islamic studies journey: 1. Create a dedicated study space, 2. Set a regular schedule, 3. Take notes actively, 4. Participate in discussions, 5. Review regularly.',
        status='published',
        slug='tips-effective-online-learning'
    )
    post2.tags.add('tips', 'learning', 'study', 'education')
    posts.append(post2)
    
    post3 = Post.objects.create(
        author=users['staff1'],
        title='The Importance of Tajweed in Quran Recitation',
        body='Tajweed is the set of rules for the correct pronunciation of the Quran. It is essential for every Muslim to learn Tajweed as it ensures the proper recitation of Allah\'s words. Our comprehensive Tajweed course covers all aspects of proper Quran recitation.',
        status='published',
        slug='importance-tajweed-quran-recitation'
    )
    post3.tags.add('tajweed', 'quran', 'recitation', 'islamic-studies')
    posts.append(post3)
    
    # Create comments
    comments = []
    for post in posts:
        # Student comments
        comments.append(Comment.objects.create(
            post=post,
            author=users['student1'],
            body='This is very helpful information. Thank you for sharing!'
        ))
        
        comments.append(Comment.objects.create(
            post=post,
            author=users['student2'],
            body='I agree with the points mentioned. Looking forward to more such posts.'
        ))
        
        # Teacher comment
        comments.append(Comment.objects.create(
            post=post,
            author=users['teacher1'],
            body='Excellent article! This will be very beneficial for our students.'
        ))
    
    print(f"Created {len(posts)} blog posts and {len(comments)} comments")
    return posts, comments

def create_notifications(users):
    """Create sample notifications"""
    print("Creating notifications...")
    
    notifications = []
    
    # Notifications for students
    for student in [users['student1'], users['student2'], users['student3'], users['student4']]:
        notifications.append(Notification.objects.create(
            user=student,
            channel=NotificationChannels.EMAIL,
            title='New Course Available',
            body='A new course "Advanced Arabic Grammar" is now available for enrollment.',
            status=NotificationStatus.SENT,
            sent_at=timezone.now() - timedelta(hours=2)
        ))
        
        notifications.append(Notification.objects.create(
            user=student,
            channel=NotificationChannels.PUSH,
            title='Class Reminder',
            body='Your Quran Recitation class starts in 30 minutes.',
            status=NotificationStatus.SENT,
            sent_at=timezone.now() - timedelta(minutes=30)
        ))
    
    # Notifications for teachers
    for teacher in [users['teacher1'], users['teacher2'], users['teacher3']]:
        notifications.append(Notification.objects.create(
            user=teacher,
            channel=NotificationChannels.EMAIL,
            title='New Student Enrollment',
            body='A new student has enrolled in your course.',
            status=NotificationStatus.SENT,
            sent_at=timezone.now() - timedelta(hours=1)
        ))
    
    print(f"Created {len(notifications)} notifications")
    return notifications

def create_reports(users):
    """Create sample reports"""
    print("Creating reports...")
    
    reports = []
    
    # Student reports
    reports.append(Report.objects.create(
        user=users['student1'],
        report_type='bug',
        title='Video playback issue',
        content='I am experiencing issues with video playback during live sessions. The video freezes frequently.',
        is_resolved=False
    ))
    
    reports.append(Report.objects.create(
        user=users['student2'],
        report_type='suggestion',
        title='Mobile app feature request',
        content='It would be great to have a mobile app for easier access to courses and notifications.',
        is_resolved=False
    ))
    
    reports.append(Report.objects.create(
        user=users['student3'],
        report_type='feedback',
        title='Course content feedback',
        content='The Arabic language course is excellent! The teacher explains everything very clearly.',
        is_resolved=True
    ))
    
    print(f"Created {len(reports)} reports")
    return reports

def create_sfu_data(sessions, users):
    """Create SFU-related data"""
    print("Creating SFU data...")
    
    participants = []
    tracks = []
    messages = []
    
    for session in sessions[:5]:  # Only for first 5 sessions
        # Create participants
        for user in [users['teacher1'], users['student1'], users['student2']]:
            if user.role in ['teacher', 'student']:
                participant = SessionParticipant.objects.create(
                    session=session,
                    user=user,
                    display_name=user.full_name,
                    role='teacher' if user.role == 'teacher' else 'student',
                    is_connected=True,
                    joined_at=session.created_at + timedelta(minutes=1),
                    left_at=session.created_at + timedelta(minutes=90)
                )
                participants.append(participant)
        
        # Create tracks for each participant
        for participant in participants[-3:]:  # Last 3 participants
            for kind in ['audio', 'video']:
                track = Track.objects.create(
                    session=session,
                    publisher=participant,
                    kind=kind,
                    active=True,
                    mid=f'{kind}_{participant.id}',
                    rid=f'rid_{participant.id}_{kind}',
                    ssrc=f'{participant.id}{kind}'
                )
                tracks.append(track)
        
        # Create signaling messages
        for participant in participants[-3:]:
            message = SignalingMessage.objects.create(
                session=session,
                message_type='outbox',
                participant=participant,
                action='join',
                payload={'user_id': participant.user.id, 'display_name': participant.display_name},
                processed=True,
                processed_at=timezone.now()
            )
            messages.append(message)
    
    print(f"Created {len(participants)} participants, {len(tracks)} tracks, {len(messages)} messages")
    return participants, tracks, messages

def main():
    """Main seeder function"""
    print("Starting Django Seeder...")
    print("=" * 50)
    
    # Clear existing data (optional)
    # clear_existing_data()
    
    # Create data in dependency order
    users = create_users()
    company_data = create_company_data()
    subjects = create_subjects()
    student_profiles = create_profiles(users)
    courses, timetables = create_courses_and_timetables(users, subjects)
    enrollments = create_enrollments(users, timetables)
    sessions = create_live_sessions(timetables)
    recordings = create_recordings(sessions)
    attendance_records = create_attendance(enrollments, sessions)
    certificates = create_certificates(users, courses)
    posts, comments = create_blog_posts(users)
    notifications = create_notifications(users)
    reports = create_reports(users)
    participants, tracks, messages = create_sfu_data(sessions, users)
    
    print("=" * 50)
    print("Seeder completed successfully!")
    print(f"Created:")
    print(f"- {CustomUser.objects.count()} users")
    print(f"- {Subject.objects.count()} subjects")
    print(f"- {Course.objects.count()} courses")
    print(f"- {CourseTimeTable.objects.count()} timetables")
    print(f"- {CourseEnrollment.objects.count()} enrollments")
    print(f"- {LiveSession.objects.count()} live sessions")
    print(f"- {Recording.objects.count()} recordings")
    print(f"- {Attendance.objects.count()} attendance records")
    print(f"- {Certificate.objects.count()} certificates")
    print(f"- {Post.objects.count()} blog posts")
    print(f"- {Comment.objects.count()} comments")
    print(f"- {Notification.objects.count()} notifications")
    print(f"- {Report.objects.count()} reports")
    print(f"- {SessionParticipant.objects.count()} SFU participants")
    print(f"- {Track.objects.count()} SFU tracks")
    print(f"- {SignalingMessage.objects.count()} SFU messages")

if __name__ == '__main__':
    main()
