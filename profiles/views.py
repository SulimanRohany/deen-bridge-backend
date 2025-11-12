from django.shortcuts import render

from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from rest_framework.parsers import FormParser, JSONParser, MultiPartParser

from .serializers import TeacherProfileSerializer, StudentProfileSerializer, StudentParentProfileSerializer, SuperAdminProfileSerializer, StaffProfileSerializer

from .models import TeacherProfile, StudentProfile, StudentParentProfile, SuperAdminProfile, StaffProfile


# teacher
class TeacherProfileListCreateView(ListCreateAPIView):
    queryset = TeacherProfile.objects.all()
    serializer_class = TeacherProfileSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    


class TeacherProfileRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    queryset = TeacherProfile.objects.all()
    serializer_class = TeacherProfileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]


# student 
class StudentProfileListCreateView(ListCreateAPIView):
    queryset = StudentProfile.objects.all()
    serializer_class = StudentProfileSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    


class StudentProfileRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    queryset = StudentProfile.objects.all()
    serializer_class = StudentProfileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]


# student parent
class StudentParentListCreateView(ListCreateAPIView):
    queryset = StudentParentProfile.objects.all()
    serializer_class = StudentParentProfileSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]


class StudentParentRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    queryset = StudentParentProfile.objects.all()
    serializer_class = StudentParentProfileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]


# staff profile
class StaffProfileListCreateView(ListCreateAPIView):
    queryset = StaffProfile.objects.all()
    serializer_class= StaffProfileSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]


class StaffProfileRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    queryset = StaffProfile.objects.all()
    serializer_class = StaffProfileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]


# super admin 
class SuperAdminProfileListCreateView(ListCreateAPIView):
    queryset = SuperAdminProfile.objects.all()
    serializer_class = SuperAdminProfileSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]


class SuperAdminProfileRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    queryset = SuperAdminProfile.objects.all()
    serializer_class = SuperAdminProfileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]