"""Views for the unified UserCommunication model"""
from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.renderers import JSONRenderer
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import UserCommunication
from .communications_serializers import (
    UserCommunicationSerializer,
    UserCommunicationListSerializer,
    UserCommunicationUpdateSerializer,
    CustomCourseRequestSerializer,
    ContactMessageSerializer,
    ReportSerializer,
)
from .communications_filters import UserCommunicationFilter
from .pagination import CustomPagination


class UserCommunicationViewSet(viewsets.ModelViewSet):
    """
    Unified ViewSet for all user communications
    Handles custom course requests, contact messages, and reports
    """
    queryset = UserCommunication.objects.all()
    serializer_class = UserCommunicationSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = UserCommunicationFilter
    search_fields = ['name', 'email', 'subject', 'title', 'message']
    ordering_fields = ['created_at', 'status', 'communication_type']
    ordering = ['-created_at']
    pagination_class = CustomPagination
    renderer_classes = [JSONRenderer]

    def get_permissions(self):
        """
        Allow anyone to create, but only admins to view/edit
        Exception: Authenticated users can view their own reports
        """
        if self.action == 'create':
            return [AllowAny()]
        elif self.action in ['list', 'retrieve', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAdminUser()]

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action in ['update', 'partial_update']:
            return UserCommunicationUpdateSerializer
        elif self.action == 'list':
            return UserCommunicationListSerializer
        return UserCommunicationSerializer

    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
        
        # Admin users see everything
        if self.request.user.is_staff:
            return queryset
        
        # Authenticated users see only their own communications
        if self.request.user.is_authenticated:
            return queryset.filter(user=self.request.user)
        
        return queryset.none()

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def mark_contacted(self, request, pk=None):
        """Admin action to mark communication as contacted"""
        instance = self.get_object()
        instance.status = 'contacted'
        instance.response_sent_at = timezone.now()
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def update_status(self, request, pk=None):
        """Admin action to update communication status"""
        instance = self.get_object()
        serializer = UserCommunicationUpdateSerializer(
            instance, 
            data=request.data, 
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(
            UserCommunicationSerializer(instance).data
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def mark_resolved(self, request, pk=None):
        """Admin action to mark communication as resolved"""
        instance = self.get_object()
        instance.is_resolved = True
        instance.status = 'resolved'
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def pending(self, request):
        """Get all pending communications"""
        pending = self.queryset.filter(status__in=['pending', 'new'])
        page = self.paginate_queryset(pending)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(pending, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def stats(self, request):
        """Get statistics about user communications"""
        # Overall stats
        total = self.queryset.count()
        pending = self.queryset.filter(status__in=['pending', 'new']).count()
        
        # By communication type
        custom_requests = self.queryset.filter(communication_type='custom_request').count()
        contact_messages = self.queryset.filter(communication_type='contact_message').count()
        reports = self.queryset.filter(communication_type='report').count()
        
        # Custom course request specific stats
        ccr_pending = self.queryset.filter(
            communication_type='custom_request', 
            status='pending'
        ).count()
        ccr_contacted = self.queryset.filter(
            communication_type='custom_request', 
            status='contacted'
        ).count()
        ccr_approved = self.queryset.filter(
            communication_type='custom_request', 
            status='approved'
        ).count()
        
        # Calculate average response time for contacted custom requests
        contacted_requests = self.queryset.filter(
            communication_type='custom_request',
            status='contacted',
            response_sent_at__isnull=False
        )
        avg_response_time = None
        if contacted_requests.exists():
            total_time = sum([req.response_time for req in contacted_requests if req.response_time])
            avg_response_time = total_time / contacted_requests.count() if total_time else None
        
        # Contact message stats
        cm_new = self.queryset.filter(
            communication_type='contact_message', 
            status='new'
        ).count()
        cm_replied = self.queryset.filter(
            communication_type='contact_message', 
            status='replied'
        ).count()
        
        # Report stats
        reports_resolved = self.queryset.filter(
            communication_type='report',
            is_resolved=True
        ).count()
        reports_pending = self.queryset.filter(
            communication_type='report',
            is_resolved=False
        ).count()
        
        return Response({
            'overall': {
                'total': total,
                'pending': pending,
            },
            'by_type': {
                'custom_requests': custom_requests,
                'contact_messages': contact_messages,
                'reports': reports,
            },
            'custom_requests': {
                'total': custom_requests,
                'pending': ccr_pending,
                'contacted': ccr_contacted,
                'approved': ccr_approved,
                'average_response_time_minutes': round(avg_response_time, 2) if avg_response_time else None,
            },
            'contact_messages': {
                'total': contact_messages,
                'new': cm_new,
                'replied': cm_replied,
            },
            'reports': {
                'total': reports,
                'resolved': reports_resolved,
                'pending': reports_pending,
            },
        })


class CustomCourseRequestCreateView(generics.CreateAPIView):
    """Public endpoint for creating custom course requests"""
    queryset = UserCommunication.objects.filter(communication_type='custom_request')
    serializer_class = CustomCourseRequestSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    renderer_classes = [JSONRenderer]

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


class ContactMessageCreateView(generics.CreateAPIView):
    """Public endpoint for creating contact messages"""
    queryset = UserCommunication.objects.filter(communication_type='contact_message')
    serializer_class = ContactMessageSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    renderer_classes = [JSONRenderer]

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response({
                'message': 'Your message has been sent successfully! We will get back to you within 24 hours.',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        except Exception as exc:
            return Response({
                'message': 'Failed to submit your message.',
                'error': str(exc)
            }, status=status.HTTP_400_BAD_REQUEST)


class ReportListCreateView(generics.ListCreateAPIView):
    """Endpoint for creating and listing reports (authenticated users only)"""
    queryset = UserCommunication.objects.filter(communication_type='report')
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['report_type', 'is_resolved', 'status']
    search_fields = ['title', 'message']
    ordering_fields = ['created_at', 'is_resolved']
    ordering = ['-created_at']
    pagination_class = CustomPagination
    renderer_classes = [JSONRenderer]

    def get_queryset(self):
        """Users can only see their own reports, admins see all"""
        queryset = super().get_queryset()
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Automatically set the user when creating a report"""
        serializer.save()
    
    def create(self, request, *args, **kwargs):
        """Override create to ensure JSON response even on error"""
        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                'error': str(e),
                'detail': 'Failed to create report'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReportRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """Endpoint for retrieving, updating, and deleting reports"""
    queryset = UserCommunication.objects.filter(communication_type='report')
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Users can only access their own reports, admins can access all"""
        queryset = super().get_queryset()
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(user=self.request.user)

