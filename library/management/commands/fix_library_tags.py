"""
Management command to fix incorrectly saved tags in library resources.
This splits comma-separated tags that were saved as single tags.
"""
from django.core.management.base import BaseCommand
from library.models import LibraryResource


class Command(BaseCommand):
    help = 'Fix library resource tags that were incorrectly saved as single comma-separated strings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without actually changing anything',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        fixed_count = 0
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Get all library resources
        resources = LibraryResource.objects.all()
        
        for resource in resources:
            # Get current tags
            current_tags = list(resource.tags.names())
            
            # Check if any tag contains a comma (indicating it wasn't split properly)
            has_comma_tags = any(',' in tag for tag in current_tags)
            
            if has_comma_tags:
                self.stdout.write(f'\n📚 Resource: {resource.title}')
                self.stdout.write(f'   Current tags: {current_tags}')
                
                # Split all tags by comma and flatten the list
                new_tags = []
                for tag in current_tags:
                    if ',' in tag:
                        # Split by comma and strip whitespace
                        split_tags = [t.strip() for t in tag.split(',') if t.strip()]
                        new_tags.extend(split_tags)
                    else:
                        new_tags.append(tag)
                
                self.stdout.write(f'   New tags: {new_tags}')
                
                if not dry_run:
                    # Clear existing tags and set new ones
                    resource.tags.clear()
                    resource.tags.add(*new_tags)
                    resource.save()
                    self.stdout.write(self.style.SUCCESS('   ✓ Fixed'))
                else:
                    self.stdout.write(self.style.WARNING('   → Would fix (dry run)'))
                
                fixed_count += 1
        
        if fixed_count == 0:
            self.stdout.write(self.style.SUCCESS('\n✓ No issues found! All tags are properly formatted.'))
        else:
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(f'\n{fixed_count} resource(s) would be fixed. Run without --dry-run to apply changes.')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'\n✓ Successfully fixed {fixed_count} resource(s)!')
                )

