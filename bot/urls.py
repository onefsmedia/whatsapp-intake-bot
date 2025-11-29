"""
URL configuration for Bot API endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    IntakeFormViewSet, MessageLogViewSet,
    WhatsAppGroupViewSet, BotResponseViewSet,
    DashboardView, SendMessageView, HealthCheckView
)

router = DefaultRouter()
router.register(r'intake-forms', IntakeFormViewSet, basename='intake-form')
router.register(r'message-logs', MessageLogViewSet, basename='message-log')
router.register(r'groups', WhatsAppGroupViewSet, basename='whatsapp-group')
router.register(r'responses', BotResponseViewSet, basename='bot-response')

urlpatterns = [
    # ViewSet routes
    path('', include(router.urls)),
    
    # Custom endpoints
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('send-message/', SendMessageView.as_view(), name='send-message'),
    path('health/', HealthCheckView.as_view(), name='health-check'),
]
