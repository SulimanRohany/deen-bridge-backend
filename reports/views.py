from django.shortcuts import render


from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated

from django_filters.rest_framework import DjangoFilterBackend

from .models import Report
from .serializers import ReportSerializer
from .filters import ReportFilter
from core.pagination import CustomPagination



class ReportListCreateView(ListCreateAPIView):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ReportFilter
    pagination_class = CustomPagination

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)



class ReportRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]

