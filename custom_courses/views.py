from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from .models import CustomCourseRequest
from .serializers import CustomCourseRequestSerializer, CustomCourseRequestCreateSerializer
from .filters import CustomCourseRequestFilter
from core.pagination import CustomPagination


class CustomCourseRequestViewSet(viewsets.ModelViewSet):
    queryset = CustomCourseRequest.objects.all()
    serializer_class = CustomCourseRequestSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = CustomCourseRequestFilter
    pagination_class = CustomPagination

    def get_permissions(self):
        """Allow anyone to create, but only admins to view/edit"""
        if self.action == 'create':
            return [AllowAny()]
        return [IsAdminUser()]

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomCourseRequestCreateSerializer
        return CustomCourseRequestSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        
        return Response(
            {
                'message': 'Your request has been submitted successfully! We will respond within 10 minutes.',
                'data': serializer.data
            },
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def mark_contacted(self, request, pk=None):
        """Admin action to mark request as contacted"""
        instance = self.get_object()
        instance.status = 'contacted'
        instance.response_sent_at = timezone.now()
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def update_status(self, request, pk=None):
        """Admin action to update request status"""
        instance = self.get_object()
        new_status = request.data.get('status')
        admin_notes = request.data.get('admin_notes')
        
        if new_status:
            instance.status = new_status
        if admin_notes:
            instance.admin_notes = admin_notes
        
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def pending(self, request):
        """Get all pending requests"""
        pending_requests = self.queryset.filter(status='pending')
        serializer = self.get_serializer(pending_requests, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def stats(self, request):
        """Get statistics about custom course requests"""
        total = self.queryset.count()
        pending = self.queryset.filter(status='pending').count()
        contacted = self.queryset.filter(status='contacted').count()
        approved = self.queryset.filter(status='approved').count()
        
        # Calculate average response time for contacted requests
        contacted_requests = self.queryset.filter(status='contacted', response_sent_at__isnull=False)
        avg_response_time = None
        if contacted_requests.exists():
            total_time = sum([req.response_time for req in contacted_requests if req.response_time])
            avg_response_time = total_time / contacted_requests.count() if total_time else None
        
        return Response({
            'total_requests': total,
            'pending': pending,
            'contacted': contacted,
            'approved': approved,
            'average_response_time_minutes': round(avg_response_time, 2) if avg_response_time else None
        })

