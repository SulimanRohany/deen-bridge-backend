from rest_framework import serializers
from .models import Surah, Verse, Bookmark, ReadingHistory


class VerseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Verse
        fields = ['id', 'verse_number', 'text_arabic', 'text_translation', 'text_transliteration', 'audio_url']


class SurahListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing surahs"""
    class Meta:
        model = Surah
        fields = ['id', 'number', 'name_arabic', 'name_transliteration', 
                  'name_translation', 'total_verses', 'revelation_type']


class SurahDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer without verses (for pagination support)"""
    
    class Meta:
        model = Surah
        fields = ['id', 'number', 'name_arabic', 'name_transliteration', 
                  'name_translation', 'total_verses', 'revelation_type']


class SurahWithVersesSerializer(serializers.ModelSerializer):
    """Serializer with all verses (legacy support)"""
    verses = VerseSerializer(many=True, read_only=True)
    
    class Meta:
        model = Surah
        fields = ['id', 'number', 'name_arabic', 'name_transliteration', 
                  'name_translation', 'total_verses', 'revelation_type', 'verses']


class BookmarkSerializer(serializers.ModelSerializer):
    verse_detail = VerseSerializer(source='verse', read_only=True)
    surah_name = serializers.CharField(source='verse.surah.name_transliteration', read_only=True)
    surah_number = serializers.IntegerField(source='verse.surah.number', read_only=True)
    verse_number = serializers.IntegerField(source='verse.verse_number', read_only=True)
    
    class Meta:
        model = Bookmark
        fields = ['id', 'verse', 'verse_detail', 'surah_name', 'surah_number', 
                  'verse_number', 'notes', 'created_at']
        read_only_fields = ['created_at']


class ReadingHistorySerializer(serializers.ModelSerializer):
    surah_detail = SurahListSerializer(source='surah', read_only=True)
    
    class Meta:
        model = ReadingHistory
        fields = ['id', 'surah', 'surah_detail', 'last_verse', 'last_read_at']
        read_only_fields = ['last_read_at']

