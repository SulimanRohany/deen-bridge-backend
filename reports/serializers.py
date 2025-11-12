from rest_framework import serializers

from .models import Report
from accounts.serializers import UserWithProfileSerializer


class ReportSerializer(serializers.ModelSerializer):
    user = UserWithProfileSerializer(read_only=True)

    class Meta:
        model = Report
        fields = '__all__'