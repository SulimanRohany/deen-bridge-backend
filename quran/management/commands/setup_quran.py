import requests
import time
from django.core.management.base import BaseCommand
from quran.models import Surah, Verse


# Complete list of all 114 Surahs
SURAHS_DATA = [
    (1, 'الفاتحة', 'Al-Fatihah', 'The Opening', 7, 'meccan'),
    (2, 'البقرة', 'Al-Baqarah', 'The Cow', 286, 'medinan'),
    (3, 'آل عمران', 'Ali \'Imran', 'Family of Imran', 200, 'medinan'),
    (4, 'النساء', 'An-Nisa', 'The Women', 176, 'medinan'),
    (5, 'المائدة', 'Al-Ma\'idah', 'The Table Spread', 120, 'medinan'),
    (6, 'الأنعام', 'Al-An\'am', 'The Cattle', 165, 'meccan'),
    (7, 'الأعراف', 'Al-A\'raf', 'The Heights', 206, 'meccan'),
    (8, 'الأنفال', 'Al-Anfal', 'The Spoils of War', 75, 'medinan'),
    (9, 'التوبة', 'At-Tawbah', 'The Repentance', 129, 'medinan'),
    (10, 'يونس', 'Yunus', 'Jonah', 109, 'meccan'),
    (11, 'هود', 'Hud', 'Hud', 123, 'meccan'),
    (12, 'يوسف', 'Yusuf', 'Joseph', 111, 'meccan'),
    (13, 'الرعد', 'Ar-Ra\'d', 'The Thunder', 43, 'medinan'),
    (14, 'ابراهيم', 'Ibrahim', 'Abraham', 52, 'meccan'),
    (15, 'الحجر', 'Al-Hijr', 'The Rocky Tract', 99, 'meccan'),
    (16, 'النحل', 'An-Nahl', 'The Bee', 128, 'meccan'),
    (17, 'الإسراء', 'Al-Isra', 'The Night Journey', 111, 'meccan'),
    (18, 'الكهف', 'Al-Kahf', 'The Cave', 110, 'meccan'),
    (19, 'مريم', 'Maryam', 'Mary', 98, 'meccan'),
    (20, 'طه', 'Ta-Ha', 'Ta-Ha', 135, 'meccan'),
    (21, 'الأنبياء', 'Al-Anbya', 'The Prophets', 112, 'meccan'),
    (22, 'الحج', 'Al-Hajj', 'The Pilgrimage', 78, 'medinan'),
    (23, 'المؤمنون', 'Al-Mu\'minun', 'The Believers', 118, 'meccan'),
    (24, 'النور', 'An-Nur', 'The Light', 64, 'medinan'),
    (25, 'الفرقان', 'Al-Furqan', 'The Criterion', 77, 'meccan'),
    (26, 'الشعراء', 'Ash-Shu\'ara', 'The Poets', 227, 'meccan'),
    (27, 'النمل', 'An-Naml', 'The Ant', 93, 'meccan'),
    (28, 'القصص', 'Al-Qasas', 'The Stories', 88, 'meccan'),
    (29, 'العنكبوت', 'Al-\'Ankabut', 'The Spider', 69, 'meccan'),
    (30, 'الروم', 'Ar-Rum', 'The Romans', 60, 'meccan'),
    (31, 'لقمان', 'Luqman', 'Luqman', 34, 'meccan'),
    (32, 'السجدة', 'As-Sajdah', 'The Prostration', 30, 'meccan'),
    (33, 'الأحزاب', 'Al-Ahzab', 'The Combined Forces', 73, 'medinan'),
    (34, 'سبإ', 'Saba', 'Sheba', 54, 'meccan'),
    (35, 'فاطر', 'Fatir', 'Originator', 45, 'meccan'),
    (36, 'يس', 'Ya-Sin', 'Ya-Sin', 83, 'meccan'),
    (37, 'الصافات', 'As-Saffat', 'Those who set the Ranks', 182, 'meccan'),
    (38, 'ص', 'Sad', 'Sad', 88, 'meccan'),
    (39, 'الزمر', 'Az-Zumar', 'The Troops', 75, 'meccan'),
    (40, 'غافر', 'Ghafir', 'The Forgiver', 85, 'meccan'),
    (41, 'فصلت', 'Fussilat', 'Explained in Detail', 54, 'meccan'),
    (42, 'الشورى', 'Ash-Shuraa', 'The Consultation', 53, 'meccan'),
    (43, 'الزخرف', 'Az-Zukhruf', 'The Ornaments of Gold', 89, 'meccan'),
    (44, 'الدخان', 'Ad-Dukhan', 'The Smoke', 59, 'meccan'),
    (45, 'الجاثية', 'Al-Jathiyah', 'The Crouching', 37, 'meccan'),
    (46, 'الأحقاف', 'Al-Ahqaf', 'The Wind-Curved Sandhills', 35, 'meccan'),
    (47, 'محمد', 'Muhammad', 'Muhammad', 38, 'medinan'),
    (48, 'الفتح', 'Al-Fath', 'The Victory', 29, 'medinan'),
    (49, 'الحجرات', 'Al-Hujurat', 'The Rooms', 18, 'medinan'),
    (50, 'ق', 'Qaf', 'Qaf', 45, 'meccan'),
    (51, 'الذاريات', 'Adh-Dhariyat', 'The Winnowing Winds', 60, 'meccan'),
    (52, 'الطور', 'At-Tur', 'The Mount', 49, 'meccan'),
    (53, 'النجم', 'An-Najm', 'The Star', 62, 'meccan'),
    (54, 'القمر', 'Al-Qamar', 'The Moon', 55, 'meccan'),
    (55, 'الرحمن', 'Ar-Rahman', 'The Beneficent', 78, 'medinan'),
    (56, 'الواقعة', 'Al-Waqi\'ah', 'The Inevitable', 96, 'meccan'),
    (57, 'الحديد', 'Al-Hadid', 'The Iron', 29, 'medinan'),
    (58, 'المجادلة', 'Al-Mujadila', 'The Pleading Woman', 22, 'medinan'),
    (59, 'الحشر', 'Al-Hashr', 'The Exile', 24, 'medinan'),
    (60, 'الممتحنة', 'Al-Mumtahanah', 'She that is to be examined', 13, 'medinan'),
    (61, 'الصف', 'As-Saf', 'The Ranks', 14, 'medinan'),
    (62, 'الجمعة', 'Al-Jumu\'ah', 'The Congregation', 11, 'medinan'),
    (63, 'المنافقون', 'Al-Munafiqun', 'The Hypocrites', 11, 'medinan'),
    (64, 'التغابن', 'At-Taghabun', 'The Mutual Disillusion', 18, 'medinan'),
    (65, 'الطلاق', 'At-Talaq', 'The Divorce', 12, 'medinan'),
    (66, 'التحريم', 'At-Tahrim', 'The Prohibition', 12, 'medinan'),
    (67, 'الملك', 'Al-Mulk', 'The Sovereignty', 30, 'meccan'),
    (68, 'القلم', 'Al-Qalam', 'The Pen', 52, 'meccan'),
    (69, 'الحاقة', 'Al-Haqqah', 'The Reality', 52, 'meccan'),
    (70, 'المعارج', 'Al-Ma\'arij', 'The Ascending Stairways', 44, 'meccan'),
    (71, 'نوح', 'Nuh', 'Noah', 28, 'meccan'),
    (72, 'الجن', 'Al-Jinn', 'The Jinn', 28, 'meccan'),
    (73, 'المزمل', 'Al-Muzzammil', 'The Enshrouded One', 20, 'meccan'),
    (74, 'المدثر', 'Al-Muddaththir', 'The Cloaked One', 56, 'meccan'),
    (75, 'القيامة', 'Al-Qiyamah', 'The Resurrection', 40, 'meccan'),
    (76, 'الانسان', 'Al-Insan', 'The Man', 31, 'medinan'),
    (77, 'المرسلات', 'Al-Mursalat', 'The Emissaries', 50, 'meccan'),
    (78, 'النبإ', 'An-Naba', 'The Tidings', 40, 'meccan'),
    (79, 'النازعات', 'An-Nazi\'at', 'Those who drag forth', 46, 'meccan'),
    (80, 'عبس', '\'Abasa', 'He frowned', 42, 'meccan'),
    (81, 'التكوير', 'At-Takwir', 'The Overthrowing', 29, 'meccan'),
    (82, 'الإنفطار', 'Al-Infitar', 'The Cleaving', 19, 'meccan'),
    (83, 'المطففين', 'Al-Mutaffifin', 'The Defrauding', 36, 'meccan'),
    (84, 'الإنشقاق', 'Al-Inshiqaq', 'The Sundering', 25, 'meccan'),
    (85, 'البروج', 'Al-Buruj', 'The Mansions of the Stars', 22, 'meccan'),
    (86, 'الطارق', 'At-Tariq', 'The Nightcomer', 17, 'meccan'),
    (87, 'الأعلى', 'Al-A\'la', 'The Most High', 19, 'meccan'),
    (88, 'الغاشية', 'Al-Ghashiyah', 'The Overwhelming', 26, 'meccan'),
    (89, 'الفجر', 'Al-Fajr', 'The Dawn', 30, 'meccan'),
    (90, 'البلد', 'Al-Balad', 'The City', 20, 'meccan'),
    (91, 'الشمس', 'Ash-Shams', 'The Sun', 15, 'meccan'),
    (92, 'الليل', 'Al-Layl', 'The Night', 21, 'meccan'),
    (93, 'الضحى', 'Ad-Duhaa', 'The Morning Hours', 11, 'meccan'),
    (94, 'الشرح', 'Ash-Sharh', 'The Consolation', 8, 'meccan'),
    (95, 'التين', 'At-Tin', 'The Fig', 8, 'meccan'),
    (96, 'العلق', 'Al-\'Alaq', 'The Clot', 19, 'meccan'),
    (97, 'القدر', 'Al-Qadr', 'The Power', 5, 'meccan'),
    (98, 'البينة', 'Al-Bayyinah', 'The Clear Proof', 8, 'medinan'),
    (99, 'الزلزلة', 'Az-Zalzalah', 'The Earthquake', 8, 'medinan'),
    (100, 'العاديات', 'Al-\'Adiyat', 'The Courser', 11, 'meccan'),
    (101, 'القارعة', 'Al-Qari\'ah', 'The Calamity', 11, 'meccan'),
    (102, 'التكاثر', 'At-Takathur', 'The Rivalry in world increase', 8, 'meccan'),
    (103, 'العصر', 'Al-\'Asr', 'The Declining Day', 3, 'meccan'),
    (104, 'الهمزة', 'Al-Humazah', 'The Traducer', 9, 'meccan'),
    (105, 'الفيل', 'Al-Fil', 'The Elephant', 5, 'meccan'),
    (106, 'قريش', 'Quraysh', 'Quraysh', 4, 'meccan'),
    (107, 'الماعون', 'Al-Ma\'un', 'The Small kindnesses', 7, 'meccan'),
    (108, 'الكوثر', 'Al-Kawthar', 'The Abundance', 3, 'meccan'),
    (109, 'الكافرون', 'Al-Kafirun', 'The Disbelievers', 6, 'meccan'),
    (110, 'النصر', 'An-Nasr', 'The Divine Support', 3, 'medinan'),
    (111, 'المسد', 'Al-Masad', 'The Palm Fiber', 5, 'meccan'),
    (112, 'الإخلاص', 'Al-Ikhlas', 'The Sincerity', 4, 'meccan'),
    (113, 'الفلق', 'Al-Falaq', 'The Daybreak', 5, 'meccan'),
    (114, 'الناس', 'An-Nas', 'Mankind', 6, 'meccan'),
]


class Command(BaseCommand):
    help = 'Complete Quran setup - Creates Surahs, fetches verses, and adds audio URLs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-surahs',
            action='store_true',
            help='Skip creating Surahs (use if they already exist)',
        )
        parser.add_argument(
            '--skip-verses',
            action='store_true',
            help='Skip fetching verses from API',
        )
        parser.add_argument(
            '--skip-audio',
            action='store_true',
            help='Skip adding audio URLs',
        )
        parser.add_argument(
            '--reciter',
            type=str,
            default='Alafasy_128kbps',
            help='Reciter folder name for audio URLs (default: Alafasy_128kbps)',
        )

    def handle(self, *args, **options):
        self.stdout.write('=' * 80)
        self.stdout.write(self.style.SUCCESS('🕌 QURAN COMPLETE SETUP'))
        self.stdout.write('=' * 80)
        self.stdout.write('')
        
        # Step 1: Create Surahs
        if not options['skip_surahs']:
            self.create_surahs()
        else:
            self.stdout.write(self.style.WARNING('⏭️  Skipping Surah creation...'))
            self.stdout.write('')
        
        # Step 2: Fetch verses from API
        if not options['skip_verses']:
            self.fetch_verses()
        else:
            self.stdout.write(self.style.WARNING('⏭️  Skipping verse fetching...'))
            self.stdout.write('')
        
        # Step 3: Add audio URLs
        if not options['skip_audio']:
            self.add_audio_urls(options['reciter'])
        else:
            self.stdout.write(self.style.WARNING('⏭️  Skipping audio URL addition...'))
            self.stdout.write('')
        
        # Final Summary
        self.show_summary()

    def create_surahs(self):
        """Step 1: Create all 114 Surahs"""
        self.stdout.write('=' * 80)
        self.stdout.write(self.style.SUCCESS('📚 STEP 1: Creating Surahs'))
        self.stdout.write('=' * 80)
        self.stdout.write('')
        
        # Clear existing data
        self.stdout.write('🗑️  Clearing existing Quran data...')
        Verse.objects.all().delete()
        Surah.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('   ✅ Database cleared'))
        self.stdout.write('')
        
        created_count = 0
        for number, name_arabic, name_transliteration, name_translation, total_verses, revelation_type in SURAHS_DATA:
            surah, created = Surah.objects.get_or_create(
                number=number,
                defaults={
                    'name_arabic': name_arabic,
                    'name_transliteration': name_transliteration,
                    'name_translation': name_translation,
                    'total_verses': total_verses,
                    'revelation_type': revelation_type,
                }
            )
            
            if created:
                created_count += 1
                if created_count % 10 == 0 or created_count == 114:
                    self.stdout.write(
                        self.style.SUCCESS(f'   ✅ Created {created_count}/114 Surahs...')
                    )
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'🎉 Successfully created {created_count} Surahs!'))
        self.stdout.write('')

    def fetch_verses(self):
        """Step 2: Fetch all verses from Al-Quran Cloud API"""
        self.stdout.write('=' * 80)
        self.stdout.write(self.style.SUCCESS('📖 STEP 2: Fetching Verses from API'))
        self.stdout.write('=' * 80)
        self.stdout.write('📡 Source: api.alquran.cloud')
        self.stdout.write('')
        
        successful_surahs = 0
        failed_surahs = []
        total_verses_created = 0
        
        for surah_number in range(1, 115):
            try:
                surah = Surah.objects.get(number=surah_number)
                
                # Show progress every 10 surahs
                if surah_number % 10 == 1 or surah_number == 114:
                    self.stdout.write(
                        f'📖 Fetching Surah {surah_number}: {surah.name_transliteration}...'
                    )
                
                # Fetch Arabic text (Uthmani script)
                arabic_url = f'https://api.alquran.cloud/v1/surah/{surah_number}/ar.alafasy'
                arabic_response = requests.get(arabic_url, timeout=15)
                
                if arabic_response.status_code != 200:
                    raise Exception(f'Failed to fetch Arabic text: {arabic_response.status_code}')
                
                arabic_data = arabic_response.json()
                
                # Small delay to avoid rate limiting
                time.sleep(0.3)
                
                # Fetch English translation (Sahih International)
                english_url = f'https://api.alquran.cloud/v1/surah/{surah_number}/en.sahih'
                english_response = requests.get(english_url, timeout=15)
                
                if english_response.status_code != 200:
                    raise Exception(f'Failed to fetch English translation: {english_response.status_code}')
                
                english_data = english_response.json()
                
                # Create verses
                if arabic_data['code'] == 200 and english_data['code'] == 200:
                    arabic_verses = arabic_data['data']['ayahs']
                    english_verses = english_data['data']['ayahs']
                    
                    for arabic_verse, english_verse in zip(arabic_verses, english_verses):
                        Verse.objects.create(
                            surah=surah,
                            verse_number=arabic_verse['numberInSurah'],
                            text_arabic=arabic_verse['text'],
                            text_translation=english_verse['text']
                        )
                        total_verses_created += 1
                    
                    successful_surahs += 1
                else:
                    raise Exception('API returned non-200 code')
                
                # Delay between surahs
                time.sleep(0.3)
                
            except Surah.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'   ❌ Surah {surah_number} not found in database')
                )
                failed_surahs.append(surah_number)
                
            except requests.exceptions.Timeout:
                self.stdout.write(
                    self.style.ERROR(f'   ❌ Timeout fetching Surah {surah_number}')
                )
                failed_surahs.append(surah_number)
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'   ❌ Error fetching Surah {surah_number}: {str(e)}')
                )
                failed_surahs.append(surah_number)
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'✅ Successfully fetched {successful_surahs} Surahs'))
        self.stdout.write(self.style.SUCCESS(f'📖 Total verses created: {total_verses_created}'))
        
        if failed_surahs:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed Surahs: {failed_surahs}')
            )
        
        self.stdout.write('')

    def add_audio_urls(self, reciter_folder):
        """Step 3: Add audio URLs for all verses"""
        self.stdout.write('=' * 80)
        self.stdout.write(self.style.SUCCESS('🎵 STEP 3: Adding Audio URLs'))
        self.stdout.write('=' * 80)
        self.stdout.write(f'🔊 Reciter: {reciter_folder}')
        self.stdout.write('📡 Source: everyayah.com')
        self.stdout.write('')
        
        BASE_URL = f'https://everyayah.com/data/{reciter_folder}'
        updated_count = 0
        
        for surah in Surah.objects.all():
            verses = Verse.objects.filter(surah=surah)
            
            for verse in verses:
                # Format: 001001.mp3 for Surah 1, Verse 1
                audio_filename = f'{surah.number:03d}{verse.verse_number:03d}.mp3'
                audio_url = f'{BASE_URL}/{audio_filename}'
                
                # Update verse with audio URL
                verse.audio_url = audio_url
                verse.save(update_fields=['audio_url'])
                updated_count += 1
            
            # Show progress every 10 surahs
            if surah.number % 10 == 0 or surah.number == 114:
                self.stdout.write(
                    self.style.SUCCESS(f'   ✅ Processed {surah.number}/114 Surahs...')
                )
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'🎉 Added audio URLs to {updated_count} verses!'))
        self.stdout.write('')

    def show_summary(self):
        """Show final summary of the setup"""
        self.stdout.write('=' * 80)
        self.stdout.write(self.style.SUCCESS('📊 SETUP COMPLETE - SUMMARY'))
        self.stdout.write('=' * 80)
        self.stdout.write('')
        
        total_surahs = Surah.objects.count()
        total_verses = Verse.objects.count()
        verses_with_audio = Verse.objects.exclude(audio_url__isnull=True).exclude(audio_url='').count()
        
        self.stdout.write(f'📚 Total Surahs: {total_surahs}')
        self.stdout.write(f'📖 Total Verses: {total_verses}')
        self.stdout.write(f'🎵 Verses with Audio: {verses_with_audio}')
        self.stdout.write('')
        
        if total_verses > 0:
            self.stdout.write(self.style.SUCCESS('✅ Quran database is ready to use!'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  No verses found. Something may have gone wrong.'))
        
        self.stdout.write('')
        self.stdout.write('📌 Data Sources:')
        self.stdout.write('   - Surah Info: Built-in database')
        self.stdout.write('   - Verses: api.alquran.cloud (Alafasy + Sahih International)')
        self.stdout.write('   - Audio: everyayah.com')
        self.stdout.write('')
        self.stdout.write('💡 To run specific steps, use:')
        self.stdout.write('   --skip-surahs   (skip creating surahs)')
        self.stdout.write('   --skip-verses   (skip fetching verses)')
        self.stdout.write('   --skip-audio    (skip adding audio URLs)')
        self.stdout.write('   --reciter=<folder_name>  (change reciter)')
        self.stdout.write('')

