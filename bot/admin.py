"""
Django Admin configuration for WhatsApp Bot models.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import IntakeForm, MessageLog, WhatsAppGroup, BotResponse


@admin.register(IntakeForm)
class IntakeFormAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'project', 'school', 'phone', 'status', 
        'confidence_score_display', 'created_at'
    ]
    list_filter = ['status', 'school', 'subject', 'created_at']
    search_fields = ['name', 'phone', 'email', 'project', 'school', 'teacher']
    readonly_fields = [
        'whatsapp_message_id', 'whatsapp_from', 'whatsapp_timestamp',
        'group_id', 'group_name', 'raw_message', 'confidence_score',
        'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'phone', 'email')
        }),
        ('Project Details', {
            'fields': ('project', 'notes', 'status')
        }),
        ('Educational Information', {
            'fields': ('school', 'teacher', 'grade', 'subject', 'lesson_titles', 'lesson_references')
        }),
        ('WhatsApp Metadata', {
            'fields': ('whatsapp_message_id', 'whatsapp_from', 'whatsapp_timestamp', 'group_id', 'group_name'),
            'classes': ('collapse',)
        }),
        ('Processing Info', {
            'fields': ('raw_message', 'confidence_score', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def confidence_score_display(self, obj):
        score = obj.confidence_score
        if score >= 0.8:
            color = 'green'
        elif score >= 0.5:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {};">{:.0%}</span>',
            color, score
        )
    confidence_score_display.short_description = 'Confidence'
    
    actions = ['mark_completed', 'mark_processing', 'mark_rejected']
    
    @admin.action(description='Mark selected as Completed')
    def mark_completed(self, request, queryset):
        queryset.update(status='completed')
    
    @admin.action(description='Mark selected as Processing')
    def mark_processing(self, request, queryset):
        queryset.update(status='processing')
    
    @admin.action(description='Mark selected as Rejected')
    def mark_rejected(self, request, queryset):
        queryset.update(status='rejected')


@admin.register(MessageLog)
class MessageLogAdmin(admin.ModelAdmin):
    list_display = [
        'from_number', 'message_type', 'is_group_message', 
        'was_processed', 'timestamp', 'content_preview'
    ]
    list_filter = ['message_type', 'is_group_message', 'was_processed', 'timestamp']
    search_fields = ['from_number', 'from_name', 'content', 'group_name']
    readonly_fields = [
        'message_id', 'from_number', 'from_name', 'timestamp',
        'is_group_message', 'group_id', 'group_name', 'content',
        'message_type', 'was_processed', 'intake_form', 'processing_notes',
        'created_at'
    ]
    
    def content_preview(self, obj):
        content = obj.content[:100]
        if len(obj.content) > 100:
            content += '...'
        return content
    content_preview.short_description = 'Content'
    
    def has_add_permission(self, request):
        return False  # Logs are created automatically
    
    def has_change_permission(self, request, obj=None):
        return False  # Logs should not be modified


@admin.register(WhatsAppGroup)
class WhatsAppGroupAdmin(admin.ModelAdmin):
    list_display = [
        'group_name', 'is_active', 'auto_reply', 
        'total_forms_received', 'last_message_at'
    ]
    list_filter = ['is_active', 'auto_reply']
    search_fields = ['group_name', 'group_id']
    readonly_fields = ['total_forms_received', 'last_message_at', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Group Information', {
            'fields': ('group_id', 'group_name', 'is_active')
        }),
        ('Settings', {
            'fields': ('auto_reply', 'require_all_fields')
        }),
        ('Statistics', {
            'fields': ('total_forms_received', 'last_message_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BotResponse)
class BotResponseAdmin(admin.ModelAdmin):
    list_display = ['trigger', 'is_active', 'message_preview', 'updated_at']
    list_filter = ['trigger', 'is_active']
    
    def message_preview(self, obj):
        msg = obj.message_template[:80]
        if len(obj.message_template) > 80:
            msg += '...'
        return msg
    message_preview.short_description = 'Message'


# Admin site customization
admin.site.site_header = 'WhatsApp Bot Administration'
admin.site.site_title = 'WhatsApp Bot Admin'
admin.site.index_title = 'Dashboard'
