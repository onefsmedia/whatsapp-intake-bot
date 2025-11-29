"""
URL configuration for WhatsApp webhook endpoints.
"""

from django.urls import path
from .webhook_handler import WhatsAppWebhookView

urlpatterns = [
    path('whatsapp/', WhatsAppWebhookView.as_view(), name='whatsapp-webhook'),
]
