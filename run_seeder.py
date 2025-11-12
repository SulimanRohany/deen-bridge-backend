#!/usr/bin/env python
"""
Simple script to run the database seeder.
Usage: python run_seeder.py [--clear]
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

def main():
    """Run the seeder command"""
    args = ['manage.py', 'seed_data']
    
    # Add --clear flag if provided
    if '--clear' in sys.argv:
        args.append('--clear')
    
    execute_from_command_line(args)

if __name__ == '__main__':
    main()
