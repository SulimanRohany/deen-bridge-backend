from django.db import models


class Report(models.Model):
    REPORT_TYPES = [
        ('bug', 'Bug/Issue'),
        ('content', 'Inappropriate Content'),
        ('feedback', 'Feedback'),
        ('suggestion', 'Suggestion'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='reports')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES, default='other')
    title = models.CharField(max_length=255)
    content = models.TextField()

    screen_shot = models.ImageField(upload_to='reports/screen_shots/', blank=True, null=True)

    is_resolved = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Report by {self.user} - {self.report_type}"
    
    class Meta:
        ordering = ['-created_at']

