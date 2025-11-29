"""
URL configuration for WhatsApp Bot project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('bot.urls')),
    path('webhook/', include('bot.webhook_urls')),
]
