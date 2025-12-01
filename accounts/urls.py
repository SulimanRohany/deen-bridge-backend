from django.contrib import admin
from django.urls import path, include

from .views import RegisterView, UserWithProfileRetrieveUpdateDestroyView
from .views import RegisterView, UserWithProfileRetrieveUpdateDestroyView, UserWithProfileListView, CustomTokenObtainPairView
from .views import StudentRegisterView, CreateParentAccountView, PasswordResetRequestView, PasswordResetConfirmView
from .views import EmailVerificationView, ResendVerificationView

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
    path('create-parent-account/', CreateParentAccountView.as_view(), name='create_parent_account'),
    
    path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    path('verify-email/', EmailVerificationView.as_view(), name='email_verification'),
    path('resend-verification/', ResendVerificationView.as_view(), name='resend_verification'),
]