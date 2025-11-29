"""
REST API Serializers for WhatsApp Bot.
"""

from rest_framework import serializers
from .models import IntakeForm, MessageLog, WhatsAppGroup, BotResponse


class IntakeFormSerializer(serializers.ModelSerializer):
    """Serializer for IntakeForm model."""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = IntakeForm
        fields = [
            'id', 'name', 'phone', 'email', 'project', 'notes',
            'school', 'teacher', 'grade', 'subject', 
            'lesson_titles', 'lesson_references',
            'whatsapp_from', 'whatsapp_timestamp', 
            'group_id', 'group_name',
            'status', 'status_display', 'confidence_score',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'whatsapp_message_id', 'whatsapp_from', 'whatsapp_timestamp',
            'group_id', 'group_name', 'raw_message', 'confidence_score',
            'created_at', 'updated_at'
        ]


class IntakeFormListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    
    class Meta:
        model = IntakeForm
        fields = [
            'id', 'name', 'phone', 'project', 'school', 
            'status', 'confidence_score', 'created_at'
        ]


class MessageLogSerializer(serializers.ModelSerializer):
    """Serializer for MessageLog model."""
    
    message_type_display = serializers.CharField(source='get_message_type_display', read_only=True)
    
    class Meta:
        model = MessageLog
        fields = [
            'id', 'message_id', 'from_number', 'from_name', 'timestamp',
            'is_group_message', 'group_id', 'group_name',
            'message_type', 'message_type_display', 'content',
            'was_processed', 'intake_form', 'processing_notes',
            'created_at'
        ]


class WhatsAppGroupSerializer(serializers.ModelSerializer):
    """Serializer for WhatsAppGroup model."""
    
    class Meta:
        model = WhatsAppGroup
        fields = [
            'id', 'group_id', 'group_name', 'is_active',
            'auto_reply', 'require_all_fields',
            'total_forms_received', 'last_message_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['total_forms_received', 'last_message_at', 'created_at', 'updated_at']


class BotResponseSerializer(serializers.ModelSerializer):
    """Serializer for BotResponse model."""
    
    trigger_display = serializers.CharField(source='get_trigger_display', read_only=True)
    
    class Meta:
        model = BotResponse
        fields = [
            'id', 'trigger', 'trigger_display', 
            'message_template', 'is_active',
            'created_at', 'updated_at'
        ]


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics."""
    
    total_forms = serializers.IntegerField()
    forms_today = serializers.IntegerField()
    forms_this_week = serializers.IntegerField()
    forms_by_status = serializers.DictField()
    forms_by_project = serializers.ListField()
    total_messages = serializers.IntegerField()
    messages_today = serializers.IntegerField()
    active_groups = serializers.IntegerField()


class SendMessageSerializer(serializers.Serializer):
    """Serializer for sending WhatsApp messages."""
    
    to = serializers.CharField(max_length=50, help_text="Phone number with country code")
    message = serializers.CharField(max_length=4096, help_text="Message text")
    
    def validate_to(self, value):
        """Validate phone number format."""
        # Remove common formatting
        value = value.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        if not value.replace('+', '').isdigit():
            raise serializers.ValidationError("Invalid phone number format")
        return value
