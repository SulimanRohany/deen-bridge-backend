from django.apps import AppConfig


class CustomCoursesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'custom_courses'
    verbose_name = 'Custom Course Requests'

