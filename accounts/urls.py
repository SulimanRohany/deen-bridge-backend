from django.contrib import admin
from django.urls import path, include

from .views import RegisterView, UserWithProfileRetrieveUpdateDestroyView
from .views import RegisterView, UserWithProfileRetrieveUpdateDestroyView, UserWithProfileListView, CustomTokenObtainPairView
from .views import StudentRegisterView

from rest_framework_simplejwt.views import (
    TokenRefreshView
)

urlpatterns = [

    path('registration/', RegisterView.as_view(), name='account_register'),
    path('user/<int:pk>/', UserWithProfileRetrieveUpdateDestroyView.as_view(), name='user_with_profile_rud'),
    path('user/', UserWithProfileListView.as_view(), name='user_with_profile_list'),


    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('student/register/', StudentRegisterView.as_view(), name='student_register'),
]