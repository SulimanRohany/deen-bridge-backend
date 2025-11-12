from django.contrib import admin
from django.utils.html import format_html
from .models import ContactMessage, CompanyContact, CompanySetting, UserCommunication


@admin.register(UserCommunication)
class UserCommunicationAdmin(admin.ModelAdmin):
    """Admin interface for the unified UserCommunication model"""
    list_display = [
        'name', 
        'email', 
        'communication_type_badge',
        'status_badge', 
        'created_at',
        'is_resolved_badge'
    ]
    list_filter = [
        'communication_type',
        'status',
        'is_resolved',
        'course_type',
        'report_type',
        'created_at'
    ]
    search_fields = [
        'name', 
        'email', 
        'phone',
        'subject', 
        'title',
        'message'
    ]
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'ip_address',
        'user_agent',
        'response_time'
    ]
    list_per_page = 25
    ordering = ['-created_at']
    
    fieldsets = (
        ('Communication Type', {
            'fields': ('communication_type',)
        }),
        ('Contact Information', {
            'fields': ('user', 'name', 'email', 'phone')
        }),
        ('Message Content', {
            'fields': ('message',)
        }),
        ('Contact Message Specific', {
            'fields': ('subject',),
            'classes': ('collapse',)
        }),
        ('Custom Course Request Specific', {
            'fields': (
                'course_type',
                'number_of_students',
                'preferred_schedule',
                'subjects'
            ),
            'classes': ('collapse',)
        }),
        ('Report Specific', {
            'fields': (
                'report_type',
                'title',
                'screen_shot',
                'is_resolved'
            ),
            'classes': ('collapse',)
        }),
        ('Status & Admin Response', {
            'fields': (
                'status',
                'admin_notes',
                'response_sent_at',
                'response_time'
            )
        }),
        ('Tracking Information', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    def communication_type_badge(self, obj):
        """Display communication type with color coding"""
        colors = {
            'custom_request': '#3498db',
            'contact_message': '#2ecc71',
            'report': '#e74c3c',
        }
        color = colors.get(obj.communication_type, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_communication_type_display()
        )
    communication_type_badge.short_description = 'Type'
    
    def status_badge(self, obj):
        """Display status with color coding"""
        status_colors = {
            'pending': '#f39c12',
            'new': '#3498db',
            'read': '#9b59b6',
            'reviewed': '#16a085',
            'contacted': '#27ae60',
            'replied': '#2ecc71',
            'approved': '#27ae60',
            'rejected': '#e74c3c',
            'completed': '#95a5a6',
            'closed': '#7f8c8d',
            'resolved': '#2ecc71',
        }
        color = status_colors.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def is_resolved_badge(self, obj):
        """Display resolved status for reports"""
        if obj.communication_type == 'report':
            if obj.is_resolved:
                return format_html(
                    '<span style="color: green; font-weight: bold;">✓ Resolved</span>'
                )
            else:
                return format_html(
                    '<span style="color: red; font-weight: bold;">✗ Pending</span>'
                )
        return '-'
    is_resolved_badge.short_description = 'Resolved'


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    """DEPRECATED: Use UserCommunication instead"""
    list_display = ['name', 'email', 'subject', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    readonly_fields = ['id', 'created_at', 'updated_at', 'ip_address', 'user_agent']
    list_editable = ['status']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email', 'phone')
        }),
        ('Message Details', {
            'fields': ('subject', 'message')
        }),
        ('Status & Tracking', {
            'fields': ('status', 'ip_address', 'user_agent')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


@admin.register(CompanyContact)
class CompanyContactAdmin(admin.ModelAdmin):
    list_display = ['department', 'email', 'phone_number', 'created_at']
    search_fields = ['department', 'email']
    ordering = ['department']


@admin.register(CompanySetting)
class CompanySettingAdmin(admin.ModelAdmin):
    list_display = ['default_timezone', 'updated_at']
    filter_horizontal = ['contact']