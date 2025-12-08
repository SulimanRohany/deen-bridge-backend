#!/usr/bin/env python
"""
Diagnostic script to check email configuration
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.development')
django.setup()

from django.conf import settings
from pathlib import Path

print("=" * 60)
print("EMAIL CONFIGURATION DIAGNOSTIC")
print("=" * 60)
print()

# Check .env file
env_file = Path('.env')
print(f"📁 .env file exists: {env_file.exists()}")
if env_file.exists():
    print(f"📁 .env file path: {env_file.absolute()}")
    print()
    print("📄 EMAIL-related variables in .env:")
    with open('.env', 'r') as f:
        lines = f.readlines()
        email_lines = [l.strip() for l in lines if 'EMAIL' in l.upper()]
        if email_lines:
            for line in email_lines:
                # Mask password values
                if 'PASSWORD' in line.upper() and '=' in line:
                    key, value = line.split('=', 1)
                    masked_value = '***' if value.strip() else '(empty)'
                    print(f"   {key}={masked_value}")
                else:
                    print(f"   {line}")
        else:
            print("   ⚠️  No EMAIL variables found in .env")
else:
    print("   ⚠️  .env file not found!")

print()
print("=" * 60)
print("CURRENT DJANGO SETTINGS")
print("=" * 60)
print()

print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
print(f"EMAIL_HOST_USER: '{settings.EMAIL_HOST_USER}' {'✅' if settings.EMAIL_HOST_USER else '❌ EMPTY'}")
print(f"EMAIL_HOST_PASSWORD: {'✅ SET (' + str(len(settings.EMAIL_HOST_PASSWORD)) + ' chars)' if settings.EMAIL_HOST_PASSWORD else '❌ EMPTY'}")
print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
print(f"SERVER_EMAIL: {settings.SERVER_EMAIL}")
print()

print("=" * 60)
print("DIAGNOSIS")
print("=" * 60)
print()

issues = []
if not settings.EMAIL_HOST_USER:
    issues.append("❌ EMAIL_HOST_USER is empty - you need to set this in .env")
if not settings.EMAIL_HOST_PASSWORD:
    issues.append("❌ EMAIL_HOST_PASSWORD is empty - you need to set this in .env")

if issues:
    print("⚠️  ISSUES FOUND:")
    for issue in issues:
        print(f"   {issue}")
    print()
    print("📝 TO FIX:")
    print("   1. Open backend/.env file")
    print("   2. Add or update these lines:")
    print("      EMAIL_HOST_USER=your-brevo-email@example.com")
    print("      EMAIL_HOST_PASSWORD=your-brevo-smtp-key")
    print("   3. Restart your Daphne server")
else:
    print("✅ All email credentials are set!")
    print("   If you're still getting authentication errors:")
    print("   - Verify your Brevo SMTP key is correct")
    print("   - Check that EMAIL_HOST_USER matches your Brevo account email")

print()
