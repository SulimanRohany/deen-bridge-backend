from django.shortcuts import render
from django.db import transaction
from django.core.exceptions import ValidationError

from rest_framework.generics import CreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework import generics, status

from rest_framework_simplejwt.views import TokenObtainPairView

from django_filters.rest_framework import DjangoFilterBackend

from .filters import UserWithProfileFilter
from .serializers import (
    RegisterSerializer, UserWithProfileSerializer, CustomTokenObtainPairSerializer,
    StudentRegisterSerializer, PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    CreateParentAccountSerializer, EmailVerificationSerializer, ResendVerificationSerializer
)
from .models import CustomUser, RoleChoices
from profiles.models import StudentProfile, StudentParentProfile
from core.pagination import CustomPagination



class RegisterView(CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        data = {
            'user': serializer.to_representation(user),
            'message': 'Registration successful! Please check your email to verify your account before logging in.',
            'email_verified': user.email_verified,
        }
        headers = self.get_success_headers(serializer.data)
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)



class UserWithProfileRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserWithProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Optionally, restrict to self only: return self.request.user
        return super().get_object()

# --- UserWithProfile List View ---
class UserWithProfileListView(ListAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserWithProfileSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = UserWithProfileFilter
    pagination_class = CustomPagination


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer



class StudentRegisterView(CreateAPIView):
    serializer_class = StudentRegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        data = {
            'user': serializer.to_representation(user),
            'message': 'Registration successful! Please check your email to verify your account before logging in.',
            'email_verified': user.email_verified,
        }
        headers = self.get_success_headers(serializer.data)
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)


class CreateParentAccountView(APIView):
    """
    Create or link a parent account for a student.
    Only accessible by super admin.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def post(self, request, *args, **kwargs):
        serializer = CreateParentAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        student_id = serializer.validated_data['student_id']
        parent_email = serializer.validated_data['parent_email']
        parent_full_name = serializer.validated_data['parent_full_name']
        relationship = serializer.validated_data.get('relationship', '')
        link_to_existing = serializer.validated_data.get('link_to_existing', False)
        password = serializer.validated_data.get('password')
        
        try:
            with transaction.atomic():
                # Get student
                student = CustomUser.objects.get(id=student_id, role=RoleChoices.STUDENT)
                student_profile = student.studentprofile_profile
                
                # Check if parent exists
                parent_exists = CustomUser.objects.filter(email=parent_email).exists()
                
                if parent_exists and link_to_existing:
                    # Link to existing parent
                    parent_user = CustomUser.objects.get(email=parent_email, role=RoleChoices.PARENT)
                    
                    # Check if relationship already exists
                    if StudentParentProfile.objects.filter(user=parent_user, student=student_profile).exists():
                        return Response({
                            'error': 'This student is already linked to this parent account.'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Create relationship
                    parent_relationship = StudentParentProfile.objects.create(
                        user=parent_user,
                        student=student_profile,
                        relationship=relationship,
                    )
                    
                    return Response({
                        'message': 'Student successfully linked to existing parent account.',
                        'parent': UserWithProfileSerializer(parent_user).data,
                        'relationship': {
                            'id': parent_relationship.id,
                            'relationship': parent_relationship.relationship,
                            'created_at': parent_relationship.created_at,
                        },
                        'student': {
                            'id': student.id,
                            'full_name': student.full_name,
                            'email': student.email,
                        }
                    }, status=status.HTTP_200_OK)
                
                else:
                    # Create new parent account
                    if not password:
                        return Response({
                            'error': 'Password is required when creating a new parent account.'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    parent_user = CustomUser.objects.create_user(
                        email=parent_email,
                        password=password,
                        full_name=parent_full_name,
                        role=RoleChoices.PARENT,
                    )
                    
                    # Create relationship
                    parent_relationship = StudentParentProfile.objects.create(
                        user=parent_user,
                        student=student_profile,
                        relationship=relationship,
                    )
                    
                    return Response({
                        'message': 'Parent account created and student linked successfully.',
                        'parent': UserWithProfileSerializer(parent_user).data,
                        'relationship': {
                            'id': parent_relationship.id,
                            'relationship': parent_relationship.relationship,
                            'created_at': parent_relationship.created_at,
                        },
                        'student': {
                            'id': student.id,
                            'full_name': student.full_name,
                            'email': student.email,
                        }
                    }, status=status.HTTP_201_CREATED)
                    
        except CustomUser.DoesNotExist:
            return Response({
                'error': 'Student not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': f'An error occurred: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

class PasswordResetRequestView(CreateAPIView):
    """View to request a password reset via email"""
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result, status=status.HTTP_200_OK)


class PasswordResetConfirmView(CreateAPIView):
    """View to confirm password reset with token"""
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result, status=status.HTTP_200_OK)


class EmailVerificationView(CreateAPIView):
    """View to verify email address with token"""
    serializer_class = EmailVerificationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result, status=status.HTTP_200_OK)


class ResendVerificationView(CreateAPIView):
    """View to resend email verification"""
    serializer_class = ResendVerificationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result, status=status.HTTP_200_OK)



