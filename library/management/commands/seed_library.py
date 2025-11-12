"""
Management command to seed the Islamic Digital Library with sample data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from library.models import (
    LibraryCategory, LibraryResource, ResourceType, Language
)
from subjects.models import Subject

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds the Islamic Digital Library with sample resources'

    def handle(self, *args, **kwargs):
        self.stdout.write('🌱 Starting Library seed...\n')
        
        # Get or create a super admin user for adding resources
        admin, created = User.objects.get_or_create(
            email='library@deenbridge.com',
            defaults={
                'full_name': 'Library Admin',
                'role': 'super_admin',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write(self.style.SUCCESS(f'✅ Created admin user: {admin.email}'))
        
        # Create Categories
        self.stdout.write('\n📚 Creating categories...')
        
        categories_data = [
            {'name': 'Quran', 'name_arabic': 'القرآن الكريم', 'icon': 'IconBook2', 'order': 1},
            {'name': 'Tafsir', 'name_arabic': 'تفسير', 'icon': 'IconBook', 'order': 2},
            {'name': 'Hadith', 'name_arabic': 'حديث', 'icon': 'IconScroll', 'order': 3},
            {'name': 'Fiqh', 'name_arabic': 'فقه', 'icon': 'IconScale', 'order': 4},
            {'name': 'Aqeedah', 'name_arabic': 'عقيدة', 'icon': 'IconStar', 'order': 5},
            {'name': 'Seerah', 'name_arabic': 'سيرة', 'icon': 'IconUser', 'order': 6},
            {'name': 'Islamic History', 'name_arabic': 'تاريخ إسلامي', 'icon': 'IconClock', 'order': 7},
            {'name': 'Arabic Language', 'name_arabic': 'اللغة العربية', 'icon': 'IconLanguage', 'order': 8},
            {'name': 'Spirituality', 'name_arabic': 'روحانية', 'icon': 'IconHeart', 'order': 9},
            {'name': 'Islamic Finance', 'name_arabic': 'المالية الإسلامية', 'icon': 'IconCoin', 'order': 10},
            {'name': 'Contemporary Issues', 'name_arabic': 'قضايا معاصرة', 'icon': 'IconNews', 'order': 11},
            {'name': 'Childrens Books', 'name_arabic': 'كتب الأطفال', 'icon': 'IconBalloon', 'order': 12},
        ]
        
        categories = {}
        for cat_data in categories_data:
            category, created = LibraryCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'name_arabic': cat_data['name_arabic'],
                    'icon': cat_data['icon'],
                    'display_order': cat_data['order'],
                    'description': f'Resources related to {cat_data["name"]}'
                }
            )
            categories[cat_data['name']] = category
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✅ Created category: {category.name}'))
        
        # Create Resources
        self.stdout.write('\n📚 Creating library resources...')
        
        resources_data = [
            # Quran
            {
                'title': 'The Noble Quran - English Translation',
                'title_arabic': 'القرآن الكريم - ترجمة إنجليزية',
                'author': 'Multiple Translators',
                'author_arabic': 'مترجمون متعددون',
                'category': 'Quran',
                'type': ResourceType.BOOK,
                'language': Language.ENGLISH,
                'description': 'Complete English translation of the Holy Quran with Arabic text. Multiple translations available for comparison and deeper understanding.',
                'publisher': 'Islamic Publications',
                'year': 2020,
                'pages': 600,
                'is_featured': True,
                'featured_order': 1,
                'tags': ['quran', 'translation', 'english'],
            },
            {
                'title': 'Tafsir Ibn Kathir',
                'title_arabic': 'تفسير ابن كثير',
                'author': 'Ibn Kathir',
                'author_arabic': 'ابن كثير',
                'category': 'Tafsir',
                'type': ResourceType.BOOK,
                'language': Language.ARABIC,
                'description': 'One of the most comprehensive and authentic tafsir (exegesis) of the Quran. Written by the renowned scholar Imam Ibn Kathir.',
                'publisher': 'Dar al-Tayyibah',
                'year': 1999,
                'pages': 4000,
                'is_featured': True,
                'featured_order': 2,
                'tags': ['tafsir', 'ibn-kathir', 'classical'],
            },
            {
                'title': 'Sahih al-Bukhari',
                'title_arabic': 'صحيح البخاري',
                'author': 'Imam al-Bukhari',
                'author_arabic': 'الإمام البخاري',
                'category': 'Hadith',
                'type': ResourceType.BOOK,
                'language': Language.ARABIC,
                'description': 'The most authentic collection of hadith of Prophet Muhammad (peace be upon him). Considered the second most important book in Islam after the Quran.',
                'publisher': 'Dar al-Salam',
                'year': 1997,
                'pages': 3200,
                'is_featured': True,
                'featured_order': 3,
                'tags': ['hadith', 'bukhari', 'authentic', 'sahih'],
            },
            {
                'title': 'Sahih Muslim',
                'title_arabic': 'صحيح مسلم',
                'author': 'Imam Muslim',
                'author_arabic': 'الإمام مسلم',
                'category': 'Hadith',
                'type': ResourceType.BOOK,
                'language': Language.ARABIC,
                'description': 'The second most authentic hadith collection after Sahih al-Bukhari. Compiled by Imam Muslim ibn al-Hajjaj.',
                'publisher': 'Dar Ihya al-Turath',
                'year': 1998,
                'pages': 2800,
                'is_featured': True,
                'featured_order': 4,
                'tags': ['hadith', 'muslim', 'authentic', 'sahih'],
            },
            {
                'title': 'Al-Fiqh al-Muyassar',
                'title_arabic': 'الفقه الميسر',
                'author': 'Various Scholars',
                'author_arabic': 'علماء متعددون',
                'category': 'Fiqh',
                'type': ResourceType.BOOK,
                'language': Language.ARABIC,
                'description': 'Simplified Islamic jurisprudence covering all aspects of worship and daily life according to Quran and Sunnah.',
                'publisher': 'Dar al-Watan',
                'year': 2015,
                'pages': 450,
                'is_featured': False,
                'tags': ['fiqh', 'jurisprudence', 'worship'],
            },
            {
                'title': 'The Sealed Nectar (Ar-Raheeq Al-Makhtum)',
                'title_arabic': 'الرحيق المختوم',
                'author': 'Safiur Rahman Mubarakpuri',
                'author_arabic': 'صفي الرحمن المباركفوري',
                'category': 'Seerah',
                'type': ResourceType.BOOK,
                'language': Language.ENGLISH,
                'description': 'Biography of Prophet Muhammad (peace be upon him). Winner of first prize in the worldwide competition on the biography of the Prophet organized by the Muslim World League.',
                'publisher': 'Darussalam',
                'year': 2002,
                'pages': 624,
                'is_featured': True,
                'featured_order': 5,
                'tags': ['seerah', 'biography', 'prophet', 'muhammad'],
            },
            {
                'title': 'Fortress of the Muslim (Hisnul Muslim)',
                'title_arabic': 'حصن المسلم',
                'author': 'Said bin Ali bin Wahf Al-Qahtani',
                'author_arabic': 'سعيد بن علي بن وهف القحطاني',
                'category': 'Spirituality',
                'type': ResourceType.BOOK,
                'language': Language.ARABIC,
                'description': 'Collection of authentic supplications and remembrance from Quran and Sunnah for daily life.',
                'publisher': 'Darussalam',
                'year': 2010,
                'pages': 280,
                'is_featured': False,
                'tags': ['dua', 'supplication', 'dhikr', 'spirituality'],
            },
            {
                'title': 'Kitab al-Tawhid',
                'title_arabic': 'كتاب التوحيد',
                'author': 'Muhammad ibn Abdul Wahhab',
                'author_arabic': 'محمد بن عبد الوهاب',
                'category': 'Aqeedah',
                'type': ResourceType.BOOK,
                'language': Language.ARABIC,
                'description': 'Comprehensive book on Islamic monotheism (Tawhid), the most fundamental concept in Islam.',
                'publisher': 'Dar al-Maarif',
                'year': 2005,
                'pages': 320,
                'is_featured': False,
                'tags': ['tawhid', 'aqeedah', 'monotheism', 'belief'],
            },
            {
                'title': 'Riyad al-Salihin',
                'title_arabic': 'رياض الصالحين',
                'author': 'Imam an-Nawawi',
                'author_arabic': 'الإمام النووي',
                'category': 'Hadith',
                'type': ResourceType.BOOK,
                'language': Language.ARABIC,
                'description': 'Gardens of the Righteous - collection of hadith on ethics, manners, and spirituality.',
                'publisher': 'Dar Ibn Hazm',
                'year': 2003,
                'pages': 850,
                'is_featured': False,
                'tags': ['hadith', 'nawawi', 'ethics', 'manners'],
            },
            {
                'title': 'The Complete Guide to Tajweed',
                'title_arabic': 'الدليل الكامل للتجويد',
                'author': 'Dr. Abdul Aziz Khamees',
                'author_arabic': 'د. عبد العزيز خميس',
                'category': 'Quran',
                'type': ResourceType.BOOK,
                'language': Language.ENGLISH,
                'description': 'Comprehensive guide to Tajweed rules with practical examples and exercises for proper Quran recitation.',
                'publisher': 'Islamic Foundation',
                'year': 2018,
                'pages': 380,
                'is_featured': False,
                'tags': ['tajweed', 'quran', 'recitation', 'rules'],
            },
            {
                'title': 'Islamic Economics Made Easy',
                'title_arabic': 'الاقتصاد الإسلامي المبسط',
                'author': 'Dr. Muhammad Ayub',
                'author_arabic': 'د. محمد أيوب',
                'category': 'Islamic Finance',
                'type': ResourceType.BOOK,
                'language': Language.ENGLISH,
                'description': 'Introduction to Islamic economics and finance principles, covering halal investment, riba, and Islamic banking.',
                'publisher': 'International Islamic Publishing House',
                'year': 2019,
                'pages': 520,
                'is_featured': False,
                'tags': ['economics', 'finance', 'halal', 'riba'],
            },
            {
                'title': 'Muslim Scientists and Scholars',
                'title_arabic': 'علماء المسلمين',
                'author': 'Various Authors',
                'author_arabic': 'مؤلفون متعددون',
                'category': 'Islamic History',
                'type': ResourceType.BOOK,
                'language': Language.ENGLISH,
                'description': 'Contributions of Muslim scholars to science, mathematics, medicine, and philosophy throughout history.',
                'publisher': 'Kube Publishing',
                'year': 2017,
                'pages': 440,
                'is_featured': False,
                'tags': ['history', 'science', 'scholars', 'golden-age'],
            },
            {
                'title': 'Learn Arabic - Level 1',
                'title_arabic': 'تعلم العربية - المستوى الأول',
                'author': 'Arabic Institute',
                'author_arabic': 'معهد اللغة العربية',
                'category': 'Arabic Language',
                'type': ResourceType.BOOK,
                'language': Language.ENGLISH,
                'description': 'Beginner-friendly Arabic language course with exercises and audio support. Perfect for those starting their Arabic journey.',
                'publisher': 'Arabic Learning Press',
                'year': 2021,
                'pages': 200,
                'is_featured': False,
                'tags': ['arabic', 'language', 'learning', 'beginner'],
            },
            {
                'title': 'Stories of the Prophets',
                'title_arabic': 'قصص الأنبياء',
                'author': 'Ibn Kathir',
                'author_arabic': 'ابن كثير',
                'category': 'Islamic History',
                'type': ResourceType.BOOK,
                'language': Language.ENGLISH,
                'description': 'Collection of stories of all prophets mentioned in the Quran, from Adam to Muhammad (peace be upon them all).',
                'publisher': 'Darussalam',
                'year': 2003,
                'pages': 580,
                'is_featured': True,
                'featured_order': 6,
                'tags': ['prophets', 'stories', 'history', 'quran'],
            },
            {
                'title': 'My First Quran Stories',
                'title_arabic': 'قصص القرآن للأطفال',
                'author': 'Saniyasnain Khan',
                'author_arabic': 'سانية سنين خان',
                'category': 'Childrens Books',
                'type': ResourceType.BOOK,
                'language': Language.ENGLISH,
                'description': 'Beautiful illustrated Quran stories for children. Simple language and colorful pictures make learning fun.',
                'publisher': 'Goodword Books',
                'year': 2015,
                'pages': 120,
                'is_featured': False,
                'tags': ['children', 'stories', 'quran', 'illustrated'],
            },
        ]
        
        created_count = 0
        for res_data in resources_data:
            category = categories.get(res_data['category'])
            if not category:
                continue
            
            resource, created = LibraryResource.objects.get_or_create(
                title=res_data['title'],
                defaults={
                    'title_arabic': res_data.get('title_arabic', ''),
                    'author': res_data['author'],
                    'author_arabic': res_data.get('author_arabic', ''),
                    'category': category,
                    'resource_type': res_data['type'],
                    'language': res_data['language'],
                    'description': res_data['description'],
                    'publisher': res_data.get('publisher', ''),
                    'publication_year': res_data.get('year'),
                    'pages': res_data.get('pages'),
                    'is_featured': res_data.get('is_featured', False),
                    'featured_order': res_data.get('featured_order', 0),
                    'is_published': True,
                    'added_by': admin,
                }
            )
            
            if created:
                # Add tags
                for tag in res_data.get('tags', []):
                    resource.tags.add(tag)
                
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  ✅ Created resource: {resource.title}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n✨ Library seeding completed!'))
        self.stdout.write(f'   - Categories: {len(categories)}')
        self.stdout.write(f'   - Resources created: {created_count}')
        self.stdout.write(self.style.SUCCESS('\n🎉 Done! Islamic Digital Library is ready.\n'))

