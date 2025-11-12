from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import LibraryCategory, LibraryResource, ResourceRating

User = get_user_model()


class LibraryCategoryTestCase(TestCase):
    """Test cases for LibraryCategory model"""
    
    def setUp(self):
        self.category = LibraryCategory.objects.create(
            name='Tafsir',
            name_arabic='تفسير',
            description='Quranic exegesis and interpretation'
        )
    
    def test_category_creation(self):
        """Test that category is created successfully"""
        self.assertEqual(self.category.name, 'Tafsir')
        self.assertEqual(self.category.name_arabic, 'تفسير')
    
    def test_category_str(self):
        """Test string representation"""
        self.assertEqual(str(self.category), 'Tafsir')


class LibraryResourceTestCase(TestCase):
    """Test cases for LibraryResource model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            full_name='Admin User',
            role='super_admin'
        )
        
        self.category = LibraryCategory.objects.create(
            name='Hadith',
            name_arabic='حديث'
        )
        
        self.resource = LibraryResource.objects.create(
            title='Sahih Bukhari',
            title_arabic='صحيح البخاري',
            author='Imam Bukhari',
            author_arabic='الإمام البخاري',
            category=self.category,
            resource_type='book',
            language='arabic',
            description='The most authentic hadith collection',
            external_link='https://example.com/bukhari',
            added_by=self.user
        )
    
    def test_resource_creation(self):
        """Test that resource is created successfully"""
        self.assertEqual(self.resource.title, 'Sahih Bukhari')
        self.assertEqual(self.resource.author, 'Imam Bukhari')
        self.assertEqual(self.resource.category, self.category)
    
    def test_resource_str(self):
        """Test string representation"""
        self.assertEqual(str(self.resource), 'Sahih Bukhari')
    
    def test_initial_ratings(self):
        """Test initial rating values"""
        self.assertEqual(self.resource.total_ratings, 0)
        self.assertEqual(self.resource.average_rating, 0.00)


class ResourceRatingTestCase(TestCase):
    """Test cases for ResourceRating model"""
    
    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            full_name='Admin User',
            role='super_admin'
        )
        
        self.student = User.objects.create_user(
            email='student@test.com',
            password='testpass123',
            full_name='Student User',
            role='student'
        )
        
        self.category = LibraryCategory.objects.create(name='Fiqh')
        
        self.resource = LibraryResource.objects.create(
            title='Test Book',
            author='Test Author',
            category=self.category,
            external_link='https://example.com/book',
            added_by=self.admin
        )
    
    def test_rating_creation(self):
        """Test that rating is created successfully"""
        rating = ResourceRating.objects.create(
            resource=self.resource,
            student=self.student,
            rating=5,
            review='Excellent book!'
        )
        
        self.assertEqual(rating.rating, 5)
        self.assertEqual(rating.review, 'Excellent book!')
        
        # Refresh resource to check updated rating
        self.resource.refresh_from_db()
        self.assertEqual(self.resource.total_ratings, 1)
        self.assertEqual(self.resource.average_rating, 5.00)
    
    def test_rating_update(self):
        """Test rating update recalculates average"""
        rating1 = ResourceRating.objects.create(
            resource=self.resource,
            student=self.student,
            rating=5
        )
        
        # Create another student
        student2 = User.objects.create_user(
            email='student2@test.com',
            password='testpass123',
            full_name='Student 2',
            role='student'
        )
        
        rating2 = ResourceRating.objects.create(
            resource=self.resource,
            student=student2,
            rating=3
        )
        
        # Refresh resource
        self.resource.refresh_from_db()
        self.assertEqual(self.resource.total_ratings, 2)
        self.assertEqual(self.resource.average_rating, 4.00)  # (5+3)/2

