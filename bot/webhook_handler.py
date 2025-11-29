"""
WhatsApp Webhook Handler.
Receives and processes incoming WhatsApp messages via Meta's webhook.

The webhook:
1. Receives ALL messages from connected WhatsApp number/groups
2. Filters to identify intake form messages (ignores regular chat)
3. Parses and stores valid intake forms
4. Optionally sends confirmation replies
"""

import json
import logging
from datetime import datetime
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
from django.utils import timezone

from .models import IntakeForm, MessageLog, WhatsAppGroup, BotResponse
from .parser import parse_message, ParseResult
from .whatsapp_service import get_whatsapp_service

logger = logging.getLogger('bot.webhook')


@method_decorator(csrf_exempt, name='dispatch')
class WhatsAppWebhookView(View):
    """
    WhatsApp Cloud API Webhook endpoint.
    
    Handles:
    - GET: Webhook verification (required by Meta)
    - POST: Incoming messages and status updates
    """
    
    def get(self, request):
        """
        Webhook verification endpoint.
        Meta sends a GET request to verify the webhook URL.
        """
        verify_token = settings.WHATSAPP_CONFIG.get('VERIFY_TOKEN', '')
        
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        
        if mode == 'subscribe' and token == verify_token:
            logger.info("Webhook verified successfully")
            return HttpResponse(challenge, content_type='text/plain')
        else:
            logger.warning(f"Webhook verification failed: mode={mode}, token_match={token == verify_token}")
            return HttpResponse('Forbidden', status=403)
    
    def post(self, request):
        """
        Handle incoming webhook events (messages, status updates, etc.)
        """
        try:
            payload = json.loads(request.body.decode('utf-8'))
            logger.debug(f"Webhook received: {json.dumps(payload)[:500]}")
            
            # Process the webhook payload
            self._process_webhook(payload)
            
            # Always return 200 to acknowledge receipt
            return HttpResponse('OK', status=200)
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in webhook: {e}")
            return HttpResponse('Bad Request', status=400)
        except Exception as e:
            logger.exception(f"Error processing webhook: {e}")
            # Still return 200 to prevent Meta from retrying
            return HttpResponse('OK', status=200)
    
    def _process_webhook(self, payload: dict):
        """
        Process the webhook payload and extract messages.
        """
        # WhatsApp Cloud API structure
        entry = payload.get('entry', [])
        
        for entry_item in entry:
            changes = entry_item.get('changes', [])
            
            for change in changes:
                value = change.get('value', {})
                
                # Check for messages
                messages = value.get('messages', [])
                contacts = value.get('contacts', [])
                metadata = value.get('metadata', {})
                
                # Build contact lookup
                contact_map = {
                    c.get('wa_id'): c.get('profile', {}).get('name', '')
                    for c in contacts
                }
                
                for message in messages:
                    self._process_message(message, contact_map, metadata)
    
    def _process_message(self, message: dict, contacts: dict, metadata: dict):
        """
        Process a single incoming message.
        
        This method:
        1. Logs the message
        2. Determines if it's an intake form
        3. If form: parse, validate, store, and optionally reply
        4. If not form: just log and ignore
        """
        message_id = message.get('id', '')
        from_number = message.get('from', '')
        timestamp_str = message.get('timestamp', '')
        message_type = message.get('type', 'unknown')
        
        # Get sender name from contacts
        from_name = contacts.get(from_number, '')
        
        # Parse timestamp
        try:
            timestamp = datetime.fromtimestamp(int(timestamp_str), tz=timezone.utc)
        except (ValueError, TypeError):
            timestamp = timezone.now()
        
        # Check for group context
        context = message.get('context', {})
        is_group = 'group_id' in message or 'group' in message
        group_id = message.get('group_id', '') or message.get('group', {}).get('id', '')
        group_name = message.get('group', {}).get('subject', '')
        
        # Extract message content based on type
        content = self._extract_content(message, message_type)
        
        if not content:
            logger.debug(f"Skipping message {message_id}: no text content (type={message_type})")
            return
        
        # Determine message classification
        log_type = 'unknown'
        
        if message_type == 'text':
            # Parse the message to see if it's an intake form
            parse_result = parse_message(content, from_number)
            
            if parse_result.is_intake_form:
                log_type = 'intake_form'
                self._handle_intake_form(
                    parse_result, message_id, from_number, from_name,
                    timestamp, group_id, group_name, content
                )
            else:
                log_type = 'chat'
                logger.debug(f"Message {message_id} is regular chat, ignoring")
        
        elif message_type in ['image', 'video', 'audio', 'document', 'sticker']:
            log_type = 'media'
        
        elif message_type == 'reaction':
            log_type = 'reaction'
        
        # Log the message (all messages are logged for audit)
        self._log_message(
            message_id=message_id,
            from_number=from_number,
            from_name=from_name,
            timestamp=timestamp,
            is_group=is_group,
            group_id=group_id,
            group_name=group_name,
            message_type=log_type,
            content=content,
            was_processed=(log_type == 'intake_form')
        )
    
    def _extract_content(self, message: dict, message_type: str) -> str:
        """Extract text content from message based on type."""
        if message_type == 'text':
            return message.get('text', {}).get('body', '')
        
        elif message_type == 'button':
            return message.get('button', {}).get('text', '')
        
        elif message_type == 'interactive':
            interactive = message.get('interactive', {})
            interactive_type = interactive.get('type', '')
            
            if interactive_type == 'button_reply':
                return interactive.get('button_reply', {}).get('title', '')
            elif interactive_type == 'list_reply':
                return interactive.get('list_reply', {}).get('title', '')
        
        elif message_type in ['image', 'video', 'audio', 'document']:
            # Return caption if available
            return message.get(message_type, {}).get('caption', f'[{message_type}]')
        
        return ''
    
    def _handle_intake_form(
        self, 
        parse_result: ParseResult,
        message_id: str,
        from_number: str,
        from_name: str,
        timestamp: datetime,
        group_id: str,
        group_name: str,
        raw_message: str
    ):
        """
        Handle a detected intake form message.
        """
        logger.info(f"Intake form detected from {from_number}: {parse_result.name} - {parse_result.project}")
        
        # Check if we should process (group whitelist, etc.)
        if group_id:
            group = WhatsAppGroup.objects.filter(group_id=group_id, is_active=True).first()
            if not group:
                logger.info(f"Message from unregistered/inactive group {group_id}, skipping")
                return
        
        # Check if form is valid
        if not parse_result.is_valid:
            logger.warning(f"Intake form invalid: {parse_result.error_message}")
            self._send_form_incomplete_reply(from_number, parse_result)
            return
        
        # Check for duplicate (same message_id)
        if IntakeForm.objects.filter(whatsapp_message_id=message_id).exists():
            logger.debug(f"Duplicate message {message_id}, skipping")
            return
        
        # Create IntakeForm record
        intake_form = IntakeForm.objects.create(
            name=parse_result.name,
            phone=parse_result.phone or from_number,
            email=parse_result.email,
            project=parse_result.project,
            notes=parse_result.notes,
            school=parse_result.school,
            teacher=parse_result.teacher,
            grade=parse_result.grade,
            subject=parse_result.subject,
            lesson_titles=parse_result.lesson_titles,
            lesson_references=parse_result.lesson_references,
            whatsapp_message_id=message_id,
            whatsapp_from=from_number,
            whatsapp_timestamp=timestamp,
            group_id=group_id,
            group_name=group_name,
            raw_message=raw_message,
            confidence_score=parse_result.confidence,
            status='new'
        )
        
        logger.info(f"IntakeForm created: ID={intake_form.id}")
        
        # Update group stats if applicable
        if group_id:
            WhatsAppGroup.objects.filter(group_id=group_id).update(
                total_forms_received=models.F('total_forms_received') + 1,
                last_message_at=timezone.now()
            )
        
        # Send confirmation reply
        self._send_form_received_reply(from_number, parse_result)
    
    def _send_form_received_reply(self, to: str, parse_result: ParseResult):
        """Send confirmation that form was received."""
        try:
            response = BotResponse.objects.filter(
                trigger='form_received', 
                is_active=True
            ).first()
            
            if response:
                message = response.format_message(
                    name=parse_result.name,
                    project=parse_result.project,
                    school=parse_result.school or 'N/A',
                    teacher=parse_result.teacher or 'N/A'
                )
            else:
                message = (
                    f"✅ *Form Received!*\n\n"
                    f"Thank you, {parse_result.name}!\n"
                    f"Your request for *{parse_result.project}* has been recorded.\n\n"
                    f"We will process it shortly."
                )
            
            whatsapp = get_whatsapp_service()
            whatsapp.send_text_message(to, message)
            
        except Exception as e:
            logger.error(f"Failed to send form received reply: {e}")
    
    def _send_form_incomplete_reply(self, to: str, parse_result: ParseResult):
        """Send message about missing fields."""
        try:
            response = BotResponse.objects.filter(
                trigger='form_incomplete', 
                is_active=True
            ).first()
            
            if response:
                message = response.format_message(
                    missing_fields=', '.join(parse_result.missing_fields)
                )
            else:
                message = (
                    f"⚠️ *Form Incomplete*\n\n"
                    f"Your form is missing required fields:\n"
                    f"• {', '.join(parse_result.missing_fields)}\n\n"
                    f"Please resend with all required information."
                )
            
            whatsapp = get_whatsapp_service()
            whatsapp.send_text_message(to, message)
            
        except Exception as e:
            logger.error(f"Failed to send form incomplete reply: {e}")
    
    def _log_message(
        self,
        message_id: str,
        from_number: str,
        from_name: str,
        timestamp: datetime,
        is_group: bool,
        group_id: str,
        group_name: str,
        message_type: str,
        content: str,
        was_processed: bool
    ):
        """Log message to database."""
        try:
            # Avoid duplicates
            if MessageLog.objects.filter(message_id=message_id).exists():
                return
            
            MessageLog.objects.create(
                message_id=message_id,
                from_number=from_number,
                from_name=from_name,
                timestamp=timestamp,
                is_group_message=is_group,
                group_id=group_id,
                group_name=group_name,
                message_type=message_type,
                content=content[:5000],  # Limit content length
                was_processed=was_processed
            )
        except Exception as e:
            logger.error(f"Failed to log message: {e}")


# Import models at runtime to avoid circular import
from django.db import models
