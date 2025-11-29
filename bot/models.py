"""
Database models for WhatsApp Bot.
Stores parsed intake forms and message logs.
"""

from django.db import models
from django.utils import timezone


class IntakeForm(models.Model):
    """
    Stores successfully parsed intake form submissions.
    Only messages that match the intake form pattern are stored here.
    """
    
    STATUS_CHOICES = [
        ('new', 'New'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]
    
    # Core fields from intake form
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=50)
    email = models.EmailField(blank=True, default='')
    project = models.CharField(max_length=255)
    notes = models.TextField(blank=True, default='')
    
    # Educational fields
    school = models.CharField(max_length=255, blank=True, default='')
    teacher = models.CharField(max_length=255, blank=True, default='')
    grade = models.CharField(max_length=50, blank=True, default='')
    subject = models.CharField(max_length=255, blank=True, default='')
    lesson_titles = models.TextField(blank=True, default='')
    lesson_references = models.TextField(blank=True, default='')
    
    # WhatsApp metadata
    whatsapp_message_id = models.CharField(max_length=255, unique=True)
    whatsapp_from = models.CharField(max_length=50, help_text="Sender's WhatsApp number")
    whatsapp_timestamp = models.DateTimeField()
    group_id = models.CharField(max_length=255, blank=True, default='', help_text="WhatsApp group ID if from group")
    group_name = models.CharField(max_length=255, blank=True, default='')
    
    # Processing metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    raw_message = models.TextField(help_text="Original message text")
    confidence_score = models.FloatField(default=1.0, help_text="Parser confidence 0-1")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Intake Form'
        verbose_name_plural = 'Intake Forms'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['whatsapp_from']),
            models.Index(fields=['created_at']),
            models.Index(fields=['school']),
            models.Index(fields=['project']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.project} ({self.created_at.strftime('%Y-%m-%d')})"


class MessageLog(models.Model):
    """
    Logs ALL incoming WhatsApp messages for audit purposes.
    Both matched (intake forms) and unmatched (regular chat) messages.
    """
    
    MESSAGE_TYPE_CHOICES = [
        ('intake_form', 'Intake Form'),
        ('chat', 'Regular Chat'),
        ('media', 'Media/Attachment'),
        ('reaction', 'Reaction'),
        ('system', 'System Message'),
        ('unknown', 'Unknown'),
    ]
    
    # WhatsApp data
    message_id = models.CharField(max_length=255, unique=True)
    from_number = models.CharField(max_length=50)
    from_name = models.CharField(max_length=255, blank=True, default='')
    timestamp = models.DateTimeField()
    
    # Group info (if applicable)
    is_group_message = models.BooleanField(default=False)
    group_id = models.CharField(max_length=255, blank=True, default='')
    group_name = models.CharField(max_length=255, blank=True, default='')
    
    # Message content
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default='unknown')
    content = models.TextField()
    
    # Processing
    was_processed = models.BooleanField(default=False)
    intake_form = models.ForeignKey(
        IntakeForm, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='message_logs'
    )
    processing_notes = models.TextField(blank=True, default='')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Message Log'
        verbose_name_plural = 'Message Logs'
        indexes = [
            models.Index(fields=['message_type']),
            models.Index(fields=['from_number']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['was_processed']),
        ]
    
    def __str__(self):
        return f"{self.from_number} - {self.message_type} ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"


class WhatsAppGroup(models.Model):
    """
    Registered WhatsApp groups that the bot monitors.
    Only messages from registered groups are processed.
    """
    
    group_id = models.CharField(max_length=255, unique=True)
    group_name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True, help_text="Whether to process messages from this group")
    
    # Settings
    auto_reply = models.BooleanField(default=True, help_text="Send confirmation when form is received")
    require_all_fields = models.BooleanField(default=False, help_text="Require all fields or just name+project")
    
    # Stats
    total_forms_received = models.IntegerField(default=0)
    last_message_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'WhatsApp Group'
        verbose_name_plural = 'WhatsApp Groups'
    
    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"{self.group_name} ({status})"


class BotResponse(models.Model):
    """
    Configurable bot response templates.
    """
    
    TRIGGER_CHOICES = [
        ('form_received', 'Form Successfully Received'),
        ('form_incomplete', 'Form Missing Required Fields'),
        ('form_invalid', 'Form Invalid Format'),
        ('help', 'Help Command'),
        ('welcome', 'Welcome Message'),
    ]
    
    trigger = models.CharField(max_length=50, choices=TRIGGER_CHOICES, unique=True)
    message_template = models.TextField(help_text="Use {name}, {project}, etc. for placeholders")
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Bot Response'
        verbose_name_plural = 'Bot Responses'
    
    def __str__(self):
        return f"{self.get_trigger_display()}"
    
    def format_message(self, **kwargs):
        """Format the template with provided data."""
        try:
            return self.message_template.format(**kwargs)
        except KeyError:
            return self.message_template
