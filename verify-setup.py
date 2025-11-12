#!/usr/bin/env python
"""
Setup Verification Script for Deen Bridge Backend
This script checks if all production-ready changes are properly configured.
"""

import os
import sys
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}{text.center(60)}{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✓{RESET} {text}")

def print_error(text):
    print(f"{RED}✗{RESET} {text}")

def print_warning(text):
    print(f"{YELLOW}⚠{RESET} {text}")

def check_file_exists(filepath, required=True):
    """Check if a file exists"""
    if Path(filepath).exists():
        print_success(f"Found: {filepath}")
        return True
    else:
        if required:
            print_error(f"Missing: {filepath}")
        else:
            print_warning(f"Optional: {filepath} not found")
        return False

def check_directory_exists(dirpath, required=True):
    """Check if a directory exists"""
    if Path(dirpath).is_dir():
        print_success(f"Found directory: {dirpath}")
        return True
    else:
        if required:
            print_error(f"Missing directory: {dirpath}")
        else:
            print_warning(f"Optional directory: {dirpath} not found")
        return False

def main():
    print_header("Deen Bridge Backend Setup Verification")
    
    errors = 0
    warnings = 0
    
    # Check new settings structure
    print_header("Settings Structure")
    if check_directory_exists("backend/settings", required=True):
        check_file_exists("backend/settings/__init__.py", required=True)
        check_file_exists("backend/settings/base.py", required=True)
        check_file_exists("backend/settings/development.py", required=True)
        check_file_exists("backend/settings/production.py", required=True)
    else:
        errors += 1
    
    # Check configuration files
    print_header("Configuration Files")
    check_file_exists("env.example", required=True) or (errors := errors + 1)
    check_file_exists("requirements.txt", required=True) or (errors := errors + 1)
    check_file_exists("requirements-dev.txt", required=True) or (errors := errors + 1)
    check_file_exists("gunicorn_config.py", required=True) or (errors := errors + 1)
    
    # Check environment file
    if not check_file_exists(".env", required=False):
        print_warning("No .env file found. Copy env.example to .env and configure it.")
        warnings += 1
    
    # Check deployment scripts
    print_header("Deployment Scripts")
    check_file_exists("deploy-production.sh", required=True) or (errors := errors + 1)
    check_file_exists("start-production.sh", required=True) or (errors := errors + 1)
    check_file_exists("start-development.ps1", required=True) or (errors := errors + 1)
    check_file_exists("start-development-with-channels.ps1", required=True) or (errors := errors + 1)
    
    # Check infrastructure files
    print_header("Infrastructure Files")
    check_file_exists("deenbridge.service", required=False) or (warnings := warnings + 1)
    check_file_exists("nginx.conf.example", required=False) or (warnings := warnings + 1)
    
    # Check documentation
    print_header("Documentation")
    check_file_exists("DEPLOYMENT.md", required=True) or (errors := errors + 1)
    check_file_exists("MIGRATION_GUIDE.md", required=True) or (errors := errors + 1)
    check_file_exists("PRODUCTION_CHANGES.md", required=True) or (errors := errors + 1)
    
    # Check application code
    print_header("Application Code")
    check_file_exists("core/exceptions.py", required=True) or (errors := errors + 1)
    check_file_exists("core/middleware.py", required=True) or (errors := errors + 1)
    
    # Check core Django files
    print_header("Core Django Files")
    check_file_exists("manage.py", required=True) or (errors := errors + 1)
    check_file_exists("backend/wsgi.py", required=True) or (errors := errors + 1)
    check_file_exists("backend/asgi.py", required=True) or (errors := errors + 1)
    check_file_exists("backend/urls.py", required=True) or (errors := errors + 1)
    
    # Check Python packages
    print_header("Python Packages Check")
    try:
        import django
        print_success(f"Django {django.VERSION} installed")
    except ImportError:
        print_error("Django not installed")
        errors += 1
    
    try:
        import environ
        print_success("django-environ installed")
    except ImportError:
        print_error("django-environ not installed")
        errors += 1
    
    try:
        import channels
        print_success("channels installed")
    except ImportError:
        print_error("channels not installed")
        errors += 1
    
    try:
        import rest_framework
        print_success("djangorestframework installed")
    except ImportError:
        print_error("djangorestframework not installed")
        errors += 1
    
    # Environment variable check
    print_header("Environment Variables")
    env_file_exists = Path(".env").exists()
    
    if env_file_exists:
        # Try to load and check environment variables
        try:
            import environ
            env = environ.Env()
            environ.Env.read_env('.env')
            
            required_vars = [
                'SECRET_KEY',
                'DEBUG',
                'ALLOWED_HOSTS',
            ]
            
            for var in required_vars:
                if var in os.environ or (env_file_exists and var in open('.env').read()):
                    print_success(f"Environment variable set: {var}")
                else:
                    print_warning(f"Environment variable not set: {var}")
                    warnings += 1
        except Exception as e:
            print_warning(f"Could not verify environment variables: {e}")
            warnings += 1
    else:
        print_warning("No .env file found. Environment variables not checked.")
        warnings += 1
    
    # Summary
    print_header("Verification Summary")
    
    if errors == 0 and warnings == 0:
        print_success("✨ All checks passed! Your setup is production-ready.")
        print_success("Next steps:")
        print(f"   1. Create and configure .env file (copy from env.example)")
        print(f"   2. Set up PostgreSQL database")
        print(f"   3. Run migrations: python manage.py migrate")
        print(f"   4. Collect static files: python manage.py collectstatic")
        print(f"   5. Review DEPLOYMENT.md for production deployment")
        return 0
    elif errors == 0:
        print_warning(f"⚠ Setup complete with {warnings} warning(s)")
        print_warning("Review warnings above and address them if needed.")
        return 0
    else:
        print_error(f"❌ Setup incomplete: {errors} error(s), {warnings} warning(s)")
        print_error("Please fix the errors above before proceeding.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

