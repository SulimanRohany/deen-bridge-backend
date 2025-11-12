from django.shortcuts import render

from rest_framework.generics import CreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny,IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from rest_framework import generics, status

from rest_framework_simplejwt.views import TokenObtainPairView

from django_filters.rest_framework import DjangoFilterBackend

from .filters import UserWithProfileFilter
from .serializers import RegisterSerializer, UserWithProfileSerializer, CustomTokenObtainPairSerializer,  StudentRegisterSerializer
from .models import CustomUser
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
        }
        headers = self.get_success_headers(serializer.data)
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)
    



