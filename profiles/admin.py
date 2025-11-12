from django.contrib import admin

from .models import TeacherProfile, StudentProfile, StudentParentProfile, StaffProfile, SuperAdminProfile

admin.site.register(TeacherProfile)
admin.site.register(StudentProfile)
admin.site.register(StudentParentProfile)
admin.site.register(StaffProfile)
admin.site.register(SuperAdminProfile)
