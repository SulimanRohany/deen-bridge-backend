from django.contrib import admin
from .models import Surah, Verse, Bookmark, ReadingHistory


@admin.register(Surah)
class SurahAdmin(admin.ModelAdmin):
    list_display = ['number', 'name_transliteration', 'name_arabic', 'total_verses', 'revelation_type']
    list_filter = ['revelation_type']
    search_fields = ['name_arabic', 'name_transliteration', 'name_translation']
    ordering = ['number']


@admin.register(Verse)
class VerseAdmin(admin.ModelAdmin):
    list_display = ['surah', 'verse_number', 'text_arabic_preview']
    list_filter = ['surah']
    search_fields = ['text_arabic', 'text_translation']
    ordering = ['surah__number', 'verse_number']
    
    def text_arabic_preview(self, obj):
        return obj.text_arabic[:50] + '...' if len(obj.text_arabic) > 50 else obj.text_arabic
    text_arabic_preview.short_description = 'Arabic Text'


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ['user', 'verse', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'verse__text_arabic']
    ordering = ['-created_at']


@admin.register(ReadingHistory)
class ReadingHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'surah', 'last_verse', 'last_read_at']
    list_filter = ['last_read_at']
    search_fields = ['user__username', 'surah__name_transliteration']
    ordering = ['-last_read_at']

