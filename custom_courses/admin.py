from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import CustomCourseRequest


@admin.register(CustomCourseRequest)
class CustomCourseRequestAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'name',
        'email',
        'phone',
        'course_type_badge',
        'status_badge',
        'created_at',
        'response_time_display',
        'action_buttons'
    ]
    list_filter = ['status', 'courseType', 'preferredSchedule', 'created_at']
    search_fields = ['name', 'email', 'phone', 'subjects', 'message']
    readonly_fields = ['created_at', 'updated_at', 'response_time_display']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('name', 'email', 'phone')
        }),
        ('Course Details', {
            'fields': ('courseType', 'numberOfStudents', 'preferredSchedule', 'subjects', 'message')
        }),
        ('Status & Management', {
            'fields': ('status', 'admin_notes', 'response_sent_at')
        }),
        ('Metadata', {
            'fields': ('user', 'created_at', 'updated_at', 'response_time_display'),
            'classes': ('collapse',)
        }),
    )

    def course_type_badge(self, obj):
        colors = {
            'family': '#10b981',
            'private': '#3b82f6',
            'group': '#8b5cf6',
            'corporate': '#f59e0b',
        }
        color = colors.get(obj.courseType, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 600;">{}</span>',
            color,
            obj.get_courseType_display()
        )
    course_type_badge.short_description = 'Course Type'

    def status_badge(self, obj):
        colors = {
            'pending': '#ef4444',
            'reviewed': '#f59e0b',
            'contacted': '#3b82f6',
            'approved': '#10b981',
            'rejected': '#6b7280',
            'completed': '#059669',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 600;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def response_time_display(self, obj):
        if obj.response_time:
            minutes = obj.response_time
            if minutes < 10:
                color = '#10b981'  # Green for within 10 minutes
            elif minutes < 60:
                color = '#f59e0b'  # Orange for within 1 hour
            else:
                color = '#ef4444'  # Red for more than 1 hour
            
            return format_html(
                '<span style="color: {}; font-weight: 600;">{:.1f} minutes</span>',
                color,
                minutes
            )
        return '-'
    response_time_display.short_description = 'Response Time'

    def action_buttons(self, obj):
        whatsapp_url = f"https://wa.me/{obj.phone.replace('+', '')}"
        return format_html(
            '<a href="{}" target="_blank" style="background-color: #25D366; color: white; padding: 4px 8px; border-radius: 4px; text-decoration: none; font-size: 11px; margin-right: 4px;">WhatsApp</a>'
            '<a href="mailto:{}" style="background-color: #3b82f6; color: white; padding: 4px 8px; border-radius: 4px; text-decoration: none; font-size: 11px;">Email</a>',
            whatsapp_url,
            obj.email
        )
    action_buttons.short_description = 'Actions'

    actions = ['mark_as_contacted', 'mark_as_approved', 'mark_as_completed']

    def mark_as_contacted(self, request, queryset):
        for obj in queryset:
            obj.status = 'contacted'
            if not obj.response_sent_at:
                obj.response_sent_at = timezone.now()
            obj.save()
        self.message_user(request, f"{queryset.count()} requests marked as contacted.")
    mark_as_contacted.short_description = "Mark selected as Contacted"

    def mark_as_approved(self, request, queryset):
        queryset.update(status='approved')
        self.message_user(request, f"{queryset.count()} requests marked as approved.")
    mark_as_approved.short_description = "Mark selected as Approved"

    def mark_as_completed(self, request, queryset):
        queryset.update(status='completed')
        self.message_user(request, f"{queryset.count()} requests marked as completed.")
    mark_as_completed.short_description = "Mark selected as Completed"

