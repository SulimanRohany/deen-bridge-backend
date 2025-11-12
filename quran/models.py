from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Surah(models.Model):
    """Represents a chapter (Surah) of the Quran"""
    
    REVELATION_TYPES = (
        ('meccan', 'Meccan'),
        ('medinan', 'Medinan'),
    )
    
    number = models.IntegerField(unique=True, db_index=True)
    name_arabic = models.CharField(max_length=100)
    name_transliteration = models.CharField(max_length=100)
    name_translation = models.CharField(max_length=200)
    total_verses = models.IntegerField()
    revelation_type = models.CharField(max_length=10, choices=REVELATION_TYPES)
    
    class Meta:
        ordering = ['number']
        verbose_name = 'Surah'
        verbose_name_plural = 'Surahs'
    
    def __str__(self):
        return f"{self.number}. {self.name_transliteration}"


class Verse(models.Model):
    """Represents a verse (Ayah) of the Quran"""
    
    surah = models.ForeignKey(Surah, on_delete=models.CASCADE, related_name='verses')
    verse_number = models.IntegerField()
    text_arabic = models.TextField()
    text_translation = models.TextField()
    text_transliteration = models.TextField(blank=True, null=True)
    audio_url = models.URLField(max_length=500, blank=True, null=True)
    
    class Meta:
        ordering = ['surah__number', 'verse_number']
        unique_together = ['surah', 'verse_number']
        verbose_name = 'Verse'
        verbose_name_plural = 'Verses'
    
    def __str__(self):
        return f"{self.surah.name_transliteration} {self.verse_number}"


class Bookmark(models.Model):
    """User bookmarks for verses"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quran_bookmarks')
    verse = models.ForeignKey(Verse, on_delete=models.CASCADE)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'verse']
    
    def __str__(self):
        return f"{self.user.username} - {self.verse}"


class ReadingHistory(models.Model):
    """Track user's reading history"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quran_history')
    surah = models.ForeignKey(Surah, on_delete=models.CASCADE)
    last_verse = models.IntegerField(default=1)
    last_read_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-last_read_at']
        unique_together = ['user', 'surah']
        verbose_name = 'Reading History'
        verbose_name_plural = 'Reading Histories'
    
    def __str__(self):
        return f"{self.user.username} - {self.surah.name_transliteration}"

