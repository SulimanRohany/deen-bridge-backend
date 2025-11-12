from django.shortcuts import render

from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from django_filters.rest_framework import DjangoFilterBackend

from .serializers import ClassEnrollmentSerializer
from .models import ClassEnrollment
from .filters import ClassEnrollmentFilter
from accounts.models import RoleChoices
from course.models import Class
from core.pagination import CustomPagination



class CourseEnrollmentListCreateView(ListCreateAPIView):
    """
    List and create class enrollments.
    Note: View name kept as 'CourseEnrollment...' for backward compatibility.
    """
    serializer_class = ClassEnrollmentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ClassEnrollmentFilter
    pagination_class = CustomPagination

    def get_queryset(self):
        """
        Filter enrollments based on user role:
        - Teachers: Only see enrollments for their classes
        - Students: Only see their own enrollments
        - Super Admin/Staff: See all enrollments
        """
        user = self.request.user
        
        # If user is not authenticated, return empty queryset
        if not user.is_authenticated:
            return ClassEnrollment.objects.none()
        
        # Super admin and staff can see all enrollments
        if user.role == RoleChoices.SUPER_ADMIN or user.is_staff:
            return ClassEnrollment.objects.all().select_related(
                'student', 'class_enrolled'
            ).order_by('-created_at')
        
        # Teachers can only see enrollments for their classes
        elif user.role == RoleChoices.TEACHER:
            teacher_classes = Class.objects.filter(teacher=user)
            return ClassEnrollment.objects.filter(
                class_enrolled__in=teacher_classes
            ).select_related(
                'student', 'class_enrolled'
            ).order_by('-created_at')
        
        # Students can only see their own enrollments
        elif user.role == RoleChoices.STUDENT:
            return ClassEnrollment.objects.filter(
                student=user
            ).select_related(
                'student', 'class_enrolled'
            ).order_by('-created_at')
        
        # Default: return empty queryset for other roles
        return ClassEnrollment.objects.none()


class CourseEnrollmentRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a class enrollment.
    Note: View name kept as 'CourseEnrollment...' for backward compatibility.
    """
    queryset = ClassEnrollment.objects.all()
    serializer_class = ClassEnrollmentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

