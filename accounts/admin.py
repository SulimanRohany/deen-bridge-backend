from django.contrib import admin

from .models import CustomUser, TeacherUser, StudentUser, ParentUser, StaffUser, SuperAdminUser, PasswordResetToken, EmailVerificationToken


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'created_at', 'expires_at', 'used', 'is_valid')
    list_filter = ('used', 'created_at', 'expires_at')
    search_fields = ('user__email', 'token')
    readonly_fields = ('token', 'created_at', 'expires_at')
    ordering = ('-created_at',)

    def is_valid(self, obj):
        return obj.is_valid()
    is_valid.boolean = True
    is_valid.short_description = 'Valid'


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'created_at', 'expires_at', 'used', 'is_valid')
    list_filter = ('used', 'created_at', 'expires_at')
    search_fields = ('user__email', 'token')
    readonly_fields = ('token', 'created_at', 'expires_at')
    ordering = ('-created_at',)

    def is_valid(self, obj):
        return obj.is_valid()
    is_valid.boolean = True
    is_valid.short_description = 'Valid'


admin.site.register(CustomUser)
admin.site.register(TeacherUser)
admin.site.register(StudentUser)
admin.site.register(ParentUser)
admin.site.register(StaffUser)
admin.site.register(SuperAdminUser)

