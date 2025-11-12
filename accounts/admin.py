from django.contrib import admin

from .models import CustomUser, TeacherUser, StudentUser, ParentUser, StaffUser, SuperAdminUser


admin.site.register(CustomUser)
admin.site.register(TeacherUser)
admin.site.register(StudentUser)
admin.site.register(ParentUser)
admin.site.register(StaffUser)
admin.site.register(SuperAdminUser)

