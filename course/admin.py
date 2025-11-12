from django.contrib import admin
from .models import Class, LiveSession, Recording, Attendance, Certificate, LiveSessionResource


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ['title', 'capacity', 'price', 'is_special_class', 'get_days_display', 'start_time', 'end_time', 'is_active', 'created_at']
    list_filter = ['is_special_class', 'is_active', 'timezone', 'created_at']
    search_fields = ['title', 'description']
    filter_horizontal = ['teacher', 'subject']
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'cover_image', 'is_special_class')
        }),
        ('Teacher & Subject', {
            'fields': ('teacher', 'subject')
        }),
        ('Capacity & Pricing', {
            'fields': ('capacity', 'price')
        }),
        ('Schedule & Timing', {
            'fields': ('days_of_week', 'start_time', 'end_time', 'timezone', 'is_active')
        }),
    )


@admin.register(LiveSession)
class LiveSessionAdmin(admin.ModelAdmin):
    list_display = ['get_session_number', 'title', 'class_session', 'get_scheduled_datetime', 'status', 'get_days_until']
    list_filter = ['status', 'scheduled_date', 'class_session', 'created_at']
    search_fields = ['title', 'class_session__title']
    readonly_fields = ['created_at', 'updated_at', 'get_class_schedule_info', 'get_suggested_dates']
    date_hierarchy = 'scheduled_date'
    ordering = ['scheduled_date', '-created_at']
    
    fieldsets = (
        ('Session Details', {
            'fields': ('class_session', 'title'),
            'description': 'Select the class first, then set the session details.'
        }),
        ('Schedule This Session', {
            'fields': ('get_class_schedule_info', 'get_suggested_dates', 'scheduled_date', 'status', 'reminder_sent'),
            'description': '<strong style="color: #2563eb; font-size: 14px;">📅 Set the specific date when this session will occur:</strong><br>'
                          '• <strong>Auto-calculate:</strong> Leave "Scheduled date" blank - system will pick the next available day from the class schedule<br>'
                          '• <strong>Manual override:</strong> Pick a specific date below (useful for makeup classes or special sessions)'
        }),
        ('Recording Options', {
            'fields': ('auto_record', 'recording_url', 'recording_available'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_session_number(self, obj):
        """Display session number for this class"""
        if obj and obj.class_session:
            session_count = LiveSession.objects.filter(
                class_session=obj.class_session,
                scheduled_date__lte=obj.scheduled_date or obj.created_at
            ).count()
            return f"Session #{session_count}"
        return "-"
    get_session_number.short_description = '#'
    get_session_number.admin_order_field = 'scheduled_date'
    
    def get_scheduled_datetime(self, obj):
        """Display the scheduled date and time prominently"""
        if obj and obj.scheduled_date:
            date_str = obj.scheduled_date.strftime('%a, %b %d, %Y')
            if obj.class_session:
                time_str = f"{obj.class_session.start_time.strftime('%I:%M %p')} - {obj.class_session.end_time.strftime('%I:%M %p')}"
                return f"📅 {date_str} ⏰ {time_str}"
            return f"📅 {date_str}"
        return "⚠️ No date set"
    get_scheduled_datetime.short_description = 'Scheduled For'
    get_scheduled_datetime.admin_order_field = 'scheduled_date'
    
    def get_days_until(self, obj):
        """Show how many days until the session"""
        if obj and obj.scheduled_date:
            from datetime import date
            today = date.today()
            delta = (obj.scheduled_date - today).days
            
            if delta < 0:
                return f"⏱️ {abs(delta)} days ago"
            elif delta == 0:
                return "🔴 TODAY"
            elif delta == 1:
                return "🟡 TOMORROW"
            elif delta <= 7:
                return f"🟢 In {delta} days"
            else:
                return f"In {delta} days"
        return "-"
    get_days_until.short_description = 'Status'
    
    def get_class_schedule_info(self, obj):
        """Display the class's recurring schedule for reference"""
        if obj and obj.class_session:
            days_display = obj.class_session.get_days_display()
            time_range = f"{obj.class_session.start_time.strftime('%I:%M %p')} - {obj.class_session.end_time.strftime('%I:%M %p')}"
            return f"📚 This class meets: {days_display}, {time_range} ({obj.class_session.timezone})"
        return "Select a class first"
    get_class_schedule_info.short_description = 'Class Recurring Schedule'
    
    def get_suggested_dates(self, obj):
        """Show suggested upcoming dates based on class schedule"""
        if obj and obj.class_session:
            from datetime import date, timedelta
            
            class_days = obj.class_session.days_of_week
            if not class_days:
                return "⚠️ Class has no scheduled days set"
            
            # Get next 5 possible dates
            suggestions = []
            start_date = obj.scheduled_date if obj.scheduled_date else date.today()
            check_date = start_date
            
            while len(suggestions) < 5:
                if check_date.weekday() in class_days and check_date >= date.today():
                    day_name = check_date.strftime('%A, %b %d, %Y')
                    suggestions.append(day_name)
                check_date += timedelta(days=1)
            
            return "💡 Suggested dates (based on class schedule):\n" + "\n".join(f"  • {s}" for s in suggestions)
        return "Select a class first"
    get_suggested_dates.short_description = 'Suggested Dates'


@admin.register(Recording)
class RecordingAdmin(admin.ModelAdmin):
    list_display = ['title', 'session', 'created_at']
    list_filter = ['created_at']
    search_fields = ['title', 'description', 'session__title']


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['class_enrollment', 'session', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['class_enrollment__student__email', 'session__title']


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ['student', 'class_completed', 'certificate_code', 'issued_at']
    list_filter = ['issued_at', 'created_at']
    search_fields = ['student__email', 'class_completed__title', 'certificate_code']
    readonly_fields = ['certificate_code']


@admin.register(LiveSessionResource)
class LiveSessionResourceAdmin(admin.ModelAdmin):
    list_display = ['title', 'session', 'file_type', 'uploaded_by', 'file_size_display', 'created_at']
    list_filter = ['file_type', 'created_at']
    search_fields = ['title', 'description', 'session__title', 'uploaded_by__email']
    readonly_fields = ['file_size', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'session')
        }),
        ('File Details', {
            'fields': ('file', 'file_type', 'file_size', 'uploaded_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def file_size_display(self, obj):
        """Display human-readable file size"""
        return obj.get_file_size_display()
    file_size_display.short_description = 'File Size'
