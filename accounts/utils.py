"""
Utility functions for accounts app
"""
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string


def send_password_reset_email(user, token):
    """
    Send password reset email to user
    
    Args:
        user: CustomUser instance
        token: Password reset token string
    """
    # Get frontend URL from settings
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    reset_link = f"{frontend_url}/reset-password/{token}"
    
    # Get logo URL - use frontend URL to access the logo
    # In production, this should be your actual domain
    logo_url = f"{frontend_url}/Transparent Version of Logo.png"
    
    # Prepare email context
    context = {
        'user': user,
        'reset_link': reset_link,
        'expiration_hours': 1,
        'logo_url': logo_url,
    }
    
    # Render email template
    subject = 'Reset Your Password - Deen Bridge'
    html_message = render_to_string('accounts/password_reset_email.html', context)
    plain_message = f"""
Hello {user.full_name},

You requested to reset your password for your Deen Bridge account.

Click the following link to reset your password:
{reset_link}

This link will expire in 1 hour.

If you did not request this password reset, please ignore this email.

Best regards,
Deen Bridge Team
"""
    
    # Send email
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
    except Exception as e:
        # Log error but don't fail silently - raise to caller
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
        raise


def send_email_verification(user, token):
    """
    Send email verification email to user
    
    Args:
        user: CustomUser instance
        token: Email verification token string
    """
    # Get frontend URL from settings
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    verification_link = f"{frontend_url}/verify-email/{token}"
    
    # Get logo URL - use frontend URL to access the logo
    # In production, this should be your actual domain
    logo_url = f"{frontend_url}/Transparent Version of Logo.png"
    
    # Prepare email context
    context = {
        'user': user,
        'verification_link': verification_link,
        'expiration_hours': 24,
        'logo_url': logo_url,
    }
    
    # Render email template
    subject = 'Verify Your Email Address - Deen Bridge'
    html_message = render_to_string('accounts/email_verification.html', context)
    plain_message = f"""
Hello {user.full_name},

Welcome to Deen Bridge! Thank you for registering with us.

To complete your registration and activate your account, please verify your email address by clicking the following link:

{verification_link}

This link will expire in 24 hours for your security.

If you didn't create an account with us, please ignore this email.

Best regards,
Deen Bridge Team
"""
    
    # Send email
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
    except Exception as e:
        # Log error but don't fail silently - raise to caller
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send email verification to {user.email}: {str(e)}")
        raise


