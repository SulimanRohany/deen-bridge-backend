from django.contrib import admin
from .models import ClassEnrollment

@admin.register(ClassEnrollment)
class ClassEnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'class_enrolled', 'status', 'enrolled_at', 'price', 'created_at']
    list_filter = ['status', 'enrolled_at', 'created_at']
    search_fields = ['student__email', 'class_enrolled__title', 'payment_ref']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Enrollment Information', {
            'fields': ('student', 'class_enrolled', 'status', 'enrolled_at')
        }),
        ('Payment Information', {
            'fields': ('price', 'payment_ref'),
            'description': 'Amount paid cannot exceed the class price. For free classes, enter 0 or leave empty.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
