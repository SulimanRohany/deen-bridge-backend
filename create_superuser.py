#!/usr/bin/env python
"""
Script to create a superuser for Deen Bridge
Run from the backend directory: python create_superuser.py
"""
import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.development')
django.setup()

from accounts.models import CustomUser, RoleChoices

def create_superuser():
    email = input("Email: ").strip()
    full_name = input("Full name: ").strip()
    password = input("Password: ").strip()
    password_confirm = input("Password (again): ").strip()
    
    if password != password_confirm:
        print("❌ Error: Passwords don't match!")
        return
    
    if not email or not full_name or not password:
        print("❌ Error: All fields are required!")
        return
    
    # Check if user already exists
    if CustomUser.objects.filter(email=email).exists():
        print(f"❌ Error: User with email '{email}' already exists!")
        return
    
    try:
        # Create superuser
        user = CustomUser.objects.create_superuser(
            email=email,
            full_name=full_name,
            password=password
        )
        print(f"✅ Superuser '{email}' created successfully!")
        print(f"   - Full name: {user.full_name}")
        print(f"   - Role: {user.role}")
        print(f"   - Is staff: {user.is_staff}")
        print(f"   - Is superuser: {user.is_superuser}")
    except Exception as e:
        print(f"❌ Error creating superuser: {e}")
        sys.exit(1)

if __name__ == '__main__':
    print("=" * 50)
    print("Create Superuser for Deen Bridge")
    print("=" * 50)
    create_superuser()

