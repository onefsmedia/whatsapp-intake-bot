"""
REST API Views for WhatsApp Bot.
"""

from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import IntakeForm, MessageLog, WhatsAppGroup, BotResponse
from .serializers import (
    IntakeFormSerializer, IntakeFormListSerializer,
    MessageLogSerializer, WhatsAppGroupSerializer,
    BotResponseSerializer, DashboardStatsSerializer,
    SendMessageSerializer
)
from .whatsapp_service import get_whatsapp_service


class IntakeFormViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Intake Forms.
    
    Endpoints:
    - GET /api/intake-forms/ - List all forms
    - GET /api/intake-forms/{id}/ - Get single form
    - PATCH /api/intake-forms/{id}/ - Update form (e.g., change status)
    - DELETE /api/intake-forms/{id}/ - Delete form
    - GET /api/intake-forms/by-status/?status=new - Filter by status
    - GET /api/intake-forms/by-project/?project=X - Filter by project
    """
    
    queryset = IntakeForm.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return IntakeFormListSerializer
        return IntakeFormSerializer
    
    def get_queryset(self):
        queryset = IntakeForm.objects.all()
        
        # Filter by status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filter by project
        project = self.request.query_params.get('project')
        if project:
            queryset = queryset.filter(project__icontains=project)
        
        # Filter by school
        school = self.request.query_params.get('school')
        if school:
            queryset = queryset.filter(school__icontains=school)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def by_status(self, request):
        """Get forms filtered by status."""
        status_param = request.query_params.get('status', 'new')
        forms = self.get_queryset().filter(status=status_param)
        serializer = IntakeFormListSerializer(forms, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export forms as JSON (can extend to CSV)."""
        forms = self.get_queryset()
        serializer = IntakeFormSerializer(forms, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_complete(self, request, pk=None):
        """Mark a form as completed."""
        form = self.get_object()
        form.status = 'completed'
        form.save()
        return Response({'status': 'completed'})
    
    @action(detail=True, methods=['post'])
    def mark_processing(self, request, pk=None):
        """Mark a form as processing."""
        form = self.get_object()
        form.status = 'processing'
        form.save()
        return Response({'status': 'processing'})


class MessageLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing Message Logs (read-only).
    
    Endpoints:
    - GET /api/message-logs/ - List all logs
    - GET /api/message-logs/{id}/ - Get single log
    - GET /api/message-logs/intake-forms/ - Only intake form messages
    - GET /api/message-logs/chat/ - Only chat messages
    """
    
    queryset = MessageLog.objects.all()
    serializer_class = MessageLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = MessageLog.objects.all()
        
        # Filter by type
        message_type = self.request.query_params.get('type')
        if message_type:
            queryset = queryset.filter(message_type=message_type)
        
        # Filter by phone
        phone = self.request.query_params.get('phone')
        if phone:
            queryset = queryset.filter(from_number__icontains=phone)
        
        # Filter by processed status
        processed = self.request.query_params.get('processed')
        if processed is not None:
            queryset = queryset.filter(was_processed=(processed.lower() == 'true'))
        
        return queryset.order_by('-timestamp')
    
    @action(detail=False, methods=['get'])
    def intake_forms(self, request):
        """Get only intake form messages."""
        logs = self.get_queryset().filter(message_type='intake_form')
        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def chat(self, request):
        """Get only chat messages (non-forms)."""
        logs = self.get_queryset().filter(message_type='chat')
        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)


class WhatsAppGroupViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing WhatsApp Groups.
    """
    
    queryset = WhatsAppGroup.objects.all()
    serializer_class = WhatsAppGroupSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle group active status."""
        group = self.get_object()
        group.is_active = not group.is_active
        group.save()
        return Response({'is_active': group.is_active})


class BotResponseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Bot Response templates.
    """
    
    queryset = BotResponse.objects.all()
    serializer_class = BotResponseSerializer
    permission_classes = [IsAuthenticated]


class DashboardView(APIView):
    """
    Dashboard statistics endpoint.
    
    GET /api/dashboard/
    Returns aggregated statistics for the dashboard.
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        now = timezone.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = today - timedelta(days=7)
        
        # Form statistics
        total_forms = IntakeForm.objects.count()
        forms_today = IntakeForm.objects.filter(created_at__gte=today).count()
        forms_this_week = IntakeForm.objects.filter(created_at__gte=week_ago).count()
        
        # Forms by status
        forms_by_status = dict(
            IntakeForm.objects.values('status')
            .annotate(count=Count('id'))
            .values_list('status', 'count')
        )
        
        # Top projects
        forms_by_project = list(
            IntakeForm.objects.values('project')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )
        
        # Message statistics
        total_messages = MessageLog.objects.count()
        messages_today = MessageLog.objects.filter(timestamp__gte=today).count()
        
        # Active groups
        active_groups = WhatsAppGroup.objects.filter(is_active=True).count()
        
        data = {
            'total_forms': total_forms,
            'forms_today': forms_today,
            'forms_this_week': forms_this_week,
            'forms_by_status': forms_by_status,
            'forms_by_project': forms_by_project,
            'total_messages': total_messages,
            'messages_today': messages_today,
            'active_groups': active_groups,
        }
        
        serializer = DashboardStatsSerializer(data)
        return Response(serializer.data)


class SendMessageView(APIView):
    """
    Send a WhatsApp message manually.
    
    POST /api/send-message/
    """
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        to = serializer.validated_data['to']
        message = serializer.validated_data['message']
        
        whatsapp = get_whatsapp_service()
        
        if not whatsapp.is_configured:
            return Response(
                {'error': 'WhatsApp API not configured'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        result = whatsapp.send_text_message(to, message)
        
        if result:
            return Response({
                'status': 'sent',
                'message_id': result.get('messages', [{}])[0].get('id')
            })
        else:
            return Response(
                {'error': 'Failed to send message'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class HealthCheckView(APIView):
    """
    Health check endpoint (public).
    
    GET /api/health/
    """
    
    permission_classes = [AllowAny]
    
    def get(self, request):
        whatsapp = get_whatsapp_service()
        
        return Response({
            'status': 'healthy',
            'whatsapp_configured': whatsapp.is_configured,
            'timestamp': timezone.now().isoformat()
        })
