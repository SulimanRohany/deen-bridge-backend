"""
Django management command to seed the database with sample data.
Usage: python manage.py seed_data [--clear]
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from seed_data import main, clear_existing_data

class Command(BaseCommand):
    help = 'Seed the database with sample data for all models'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding (use with caution!)',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(
                self.style.WARNING('Clearing existing data...')
            )
            clear_existing_data()
        
        self.stdout.write(
            self.style.SUCCESS('Starting database seeding...')
        )
        
        try:
            main()
            self.stdout.write(
                self.style.SUCCESS('Database seeding completed successfully!')
            )
        except Exception as e:
            raise CommandError(f'Error during seeding: {str(e)}')
