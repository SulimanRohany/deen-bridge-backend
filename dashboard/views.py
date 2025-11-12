from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser  # Assuming admin access for dashboard

from django.utils.timezone import now
from datetime import timedelta
from dateutil.parser import parse as date_parse
from django.db.models import Sum, Q, Count
from django.db.models.functions import ExtractMonth, ExtractYear

from accounts.models import CustomUser, RoleChoices
from course.models import Class, LiveSession
from enrollments.models import ClassEnrollment, EnrollmentChoices

class DashboardReportView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]  # Restrict to admins/staff

    def get(self, request):
        current_time = now()
        start_str = request.query_params.get('start_date')
        end_str = request.query_params.get('end_date')

        try:
            if start_str:
                start_date = date_parse(start_str).replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=current_time.tzinfo)
            else:
                start_date = current_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            if end_str:
                end_date = date_parse(end_str).replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=current_time.tzinfo)
            else:
                end_date = current_time

            if start_date > end_date:
                raise ValueError("Start date cannot be after end date")
        except (ValueError, TypeError) as e:
            return Response({'error': 'Invalid date format or values'}, status=400)

        period_delta = end_date - start_date
        prev_end = start_date - timedelta(seconds=1)
        prev_start = prev_end - period_delta

        # Helper to calculate growth
        def calculate_growth(current, previous):
            if previous == 0:
                return 100.0 if current > 0 else 0.0
            return round(((current - previous) / previous) * 100, 2)

        # Students
        total_students = CustomUser.objects.filter(role=RoleChoices.STUDENT).count()
        pre_students = CustomUser.objects.filter(role=RoleChoices.STUDENT, created_at__lt=start_date).count()
        at_end_students = CustomUser.objects.filter(role=RoleChoices.STUDENT, created_at__lte=end_date).count()
        new_students = at_end_students - pre_students
        students_growth = calculate_growth(at_end_students, pre_students)

        # Teachers (active)
        total_active_teachers = CustomUser.objects.filter(role=RoleChoices.TEACHER, is_active=True).count()
        pre_teachers = CustomUser.objects.filter(role=RoleChoices.TEACHER, is_active=True, created_at__lt=start_date).count()
        at_end_teachers = CustomUser.objects.filter(role=RoleChoices.TEACHER, is_active=True, created_at__lte=end_date).count()
        new_teachers = at_end_teachers - pre_teachers
        teachers_growth = calculate_growth(at_end_teachers, pre_teachers)

        # Classes (formerly courses)
        total_classes = Class.objects.count()
        pre_classes = Class.objects.filter(created_at__lt=start_date).count()
        at_end_classes = Class.objects.filter(created_at__lte=end_date).count()
        new_classes = at_end_classes - pre_classes
        classes_growth = calculate_growth(at_end_classes, pre_classes)

        # Revenue
        total_revenue_qs = ClassEnrollment.objects.filter(status=EnrollmentChoices.COMPLETED).aggregate(total=Sum('price'))['total'] or 0.0
        new_revenue_qs = ClassEnrollment.objects.filter(
            status=EnrollmentChoices.COMPLETED,
            enrolled_at__gte=start_date,
            enrolled_at__lte=end_date
        ).aggregate(total=Sum('price'))['total'] or 0.0
        previous_revenue_qs = ClassEnrollment.objects.filter(
            status=EnrollmentChoices.COMPLETED,
            enrolled_at__gte=prev_start,
            enrolled_at__lte=prev_end
        ).aggregate(total=Sum('price'))['total'] or 0.0
        revenue_growth = calculate_growth(new_revenue_qs, previous_revenue_qs)

        # 5 Recent Enrollments
        recent_enrollments = ClassEnrollment.objects.order_by('-created_at')[:5]
        recent_enrollments_data = [
            {
                'id': enrollment.id,
                'student_email': enrollment.student.email,
                'class_title': enrollment.class_enrolled.title,
                'status': enrollment.status,
                'enrolled_at': enrollment.enrolled_at,
                'price': enrollment.price,
                'created_at': enrollment.created_at
            } for enrollment in recent_enrollments
        ]

        # Ongoing/Live Sessions (currently happening)
        ongoing_sessions = LiveSession.objects.filter(status='live').order_by('-updated_at')[:5]
        ongoing_sessions_data = [
            {
                'id': session.id,
                'title': session.title,
                'class_title': session.class_session.title,
                'days_of_week': session.class_session.get_days_display(),
                'start_time': session.class_session.start_time,
                'end_time': session.class_session.end_time,
                'status': session.status,
                'created_at': session.created_at
            } for session in ongoing_sessions
        ]

        # 5 Upcoming Live Sessions (ordered by created_at for most recently scheduled sessions)
        upcoming_sessions = LiveSession.objects.filter(
            status='scheduled'
        ).order_by('-created_at')[:5]
        upcoming_sessions_data = [
            {
                'id': session.id,
                'title': session.title,
                'class_title': session.class_session.title,
                'days_of_week': session.class_session.get_days_display(),
                'start_time': session.class_session.start_time,
                'end_time': session.class_session.end_time,
                'status': session.status,
                'created_at': session.created_at
            } for session in upcoming_sessions
        ]

        # Popular Classes (top 5 by percentage of total students enrolled)
        popular_classes_qs = Class.objects.annotate(
            enrolled=Count('enrollments__student', distinct=True, filter=Q(enrollments__status=EnrollmentChoices.COMPLETED))
        ).order_by('-enrolled')[:5]
        popular_classes_data = [
            {
                'title': class_obj.title,
                'enrolled': class_obj.enrolled,
                'percentage': round((class_obj.enrolled / total_students * 100), 2) if total_students > 0 else 0.0
            } for class_obj in popular_classes_qs
        ]

        data = {
            'students': {
                'total': total_students,
                'new': new_students,
                'growth': students_growth
            },
            'teachers': {
                'total_active': total_active_teachers,
                'new': new_teachers,
                'growth': teachers_growth
            },
            'classes': {
                'total_offered': total_classes,
                'new': new_classes,
                'growth': classes_growth
            },
            'revenue': {
                'total': total_revenue_qs,
                'new': new_revenue_qs,
                'growth': revenue_growth
            },
            'recent_enrollments': recent_enrollments_data,
            'ongoing_live_sessions': ongoing_sessions_data,
            'upcoming_live_sessions': upcoming_sessions_data,
            'popular_classes': popular_classes_data
        }

        return Response(data)


class TeacherDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Ensure the user is a teacher
        if user.role != RoleChoices.TEACHER:
            return Response({'error': 'Access denied. Only teachers can access this dashboard.'}, status=403)
        
        # Helper to calculate growth
        def calculate_growth(current, previous):
            if previous == 0:
                return 100.0 if current > 0 else 0.0
            return round(((current - previous) / previous) * 100, 2)
        
        # Get current date and calculate period for growth comparison (last 30 days)
        current_time = now()
        period_start = current_time - timedelta(days=30)
        prev_period_start = period_start - timedelta(days=30)
        
        # Get classes taught by this teacher
        teacher_classes = Class.objects.filter(teacher=user)
        
        # Get all enrollments for classes taught by this teacher
        enrollments = ClassEnrollment.objects.filter(
            class_enrolled__teacher=user
        ).select_related('student', 'class_enrolled').order_by('-enrolled_at')
        
        # Get live sessions for this teacher
        live_sessions = LiveSession.objects.filter(
            class_session__teacher=user
        ).select_related('class_session').order_by('-created_at')
        
        # Calculate statistics with growth
        total_students = enrollments.filter(status=EnrollmentChoices.COMPLETED).values('student').distinct().count()
        new_students = enrollments.filter(
            status=EnrollmentChoices.COMPLETED,
            enrolled_at__gte=period_start
        ).values('student').distinct().count()
        prev_students = enrollments.filter(
            status=EnrollmentChoices.COMPLETED,
            enrolled_at__gte=prev_period_start,
            enrolled_at__lt=period_start
        ).values('student').distinct().count()
        students_growth = calculate_growth(new_students, prev_students)
        
        total_classes = teacher_classes.count()
        new_classes = teacher_classes.filter(created_at__gte=period_start).count()
        prev_classes = teacher_classes.filter(
            created_at__gte=prev_period_start,
            created_at__lt=period_start
        ).count()
        classes_growth = calculate_growth(new_classes, prev_classes)
        
        total_sessions = live_sessions.count()
        new_sessions = live_sessions.filter(created_at__gte=period_start).count()
        prev_sessions = live_sessions.filter(
            created_at__gte=prev_period_start,
            created_at__lt=period_start
        ).count()
        sessions_growth = calculate_growth(new_sessions, prev_sessions)
        
        # Calculate attendance rate (using a simple metric: students enrolled / total classes * 20 as baseline capacity)
        # You may need to adjust this based on your actual attendance tracking model
        baseline_capacity_per_class = 20  # Adjust this value as needed
        total_capacity = total_classes * baseline_capacity_per_class if total_classes > 0 else 1
        attendance_rate = round((total_students / total_capacity * 100), 2) if total_capacity > 0 else 0.0
        attendance_rate = min(attendance_rate, 100.0)  # Cap at 100%
        attendance_growth = 0.0  # Placeholder - adjust based on your needs
        
        # Format enrollments data
        enrollments_data = [
            {
                'id': enrollment.id,
                'student_name': enrollment.student.full_name,
                'student_email': enrollment.student.email,
                'class_title': enrollment.class_enrolled.title,
                'status': enrollment.status,
                'enrolled_at': enrollment.enrolled_at,
                'price': enrollment.price,
            } for enrollment in enrollments[:10]  # Limit to 10 recent enrollments
        ]
        
        # Format ongoing live sessions data
        ongoing_sessions = live_sessions.filter(
            status='live'
        ).order_by('-created_at')[:10]
        ongoing_sessions_data = [
            {
                'id': session.id,
                'title': session.title,
                'class_title': session.class_session.title,
                'days_of_week': session.class_session.get_days_display(),
                'start_time': session.class_session.start_time,
                'end_time': session.class_session.end_time,
                'status': session.status,
                'created_at': session.created_at
            } for session in ongoing_sessions
        ]
        
        # Format upcoming live sessions data
        upcoming_sessions = live_sessions.filter(
            status='scheduled'
        ).order_by('-created_at')[:10]
        sessions_data = [
            {
                'id': session.id,
                'title': session.title,
                'class_title': session.class_session.title,
                'days_of_week': session.class_session.get_days_display(),
                'start_time': session.class_session.start_time,
                'end_time': session.class_session.end_time,
                'status': session.status,
                'created_at': session.created_at
            } for session in upcoming_sessions
        ]
        
        # Format popular classes data (classes with most enrollments)
        popular_classes_qs = Class.objects.filter(teacher=user).annotate(
            enrolled=Count('enrollments__student', distinct=True, 
                          filter=Q(enrollments__status=EnrollmentChoices.COMPLETED))
        ).order_by('-enrolled')[:5]
        
        # Use baseline capacity for percentage calculation
        baseline_capacity = 30  # Adjust this value based on your typical class capacity
        popular_classes_data = [
            {
                'title': class_obj.title,
                'enrolled': class_obj.enrolled,
                'capacity': baseline_capacity,
                'percentage': round((class_obj.enrolled / baseline_capacity) * 100, 2) if baseline_capacity > 0 else 0.0
            } for class_obj in popular_classes_qs
        ]
        
        data = {
            'classes': {
                'total': total_classes,
                'new': new_classes,
                'growth': classes_growth
            },
            'students': {
                'total': total_students,
                'new': new_students,
                'growth': students_growth
            },
            'sessions': {
                'total': total_sessions,
                'new': new_sessions,
                'growth': sessions_growth
            },
            'attendance': {
                'rate': attendance_rate,
                'growth': attendance_growth
            },
            'recent_enrollments': enrollments_data,
            'ongoing_live_sessions': ongoing_sessions_data,
            'upcoming_sessions': sessions_data,
            'popular_classes': popular_classes_data,
        }
        
        return Response(data)