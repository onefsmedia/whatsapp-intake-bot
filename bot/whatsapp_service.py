"""
WhatsApp Cloud API Service.
Handles sending messages and interacting with Meta's WhatsApp Business API.
"""

import requests
import logging
from typing import Optional, Dict, Any
from django.conf import settings

logger = logging.getLogger('bot.whatsapp')


class WhatsAppService:
    """
    Service class for WhatsApp Cloud API interactions.
    """
    
    def __init__(self):
        self.config = settings.WHATSAPP_CONFIG
        self.access_token = self.config['ACCESS_TOKEN']
        self.phone_number_id = self.config['PHONE_NUMBER_ID']
        self.api_version = self.config['API_VERSION']
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
    
    @property
    def is_configured(self) -> bool:
        """Check if WhatsApp API is properly configured."""
        return bool(self.access_token and self.phone_number_id)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers for API requests."""
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def send_text_message(self, to: str, message: str) -> Optional[Dict[str, Any]]:
        """
        Send a text message to a WhatsApp number.
        
        Args:
            to: Recipient's phone number (with country code, e.g., "237600000000")
            message: Text message to send
            
        Returns:
            API response dict or None if failed
        """
        if not self.is_configured:
            logger.warning("WhatsApp API not configured, message not sent")
            return None
        
        # Remove + from phone number if present
        to = to.lstrip('+')
        
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message
            }
        }
        
        try:
            response = requests.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            result = response.json()
            logger.info(f"Message sent to {to}: {result.get('messages', [{}])[0].get('id', 'unknown')}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send message to {to}: {e}")
            return None
    
    def send_template_message(
        self, 
        to: str, 
        template_name: str, 
        language_code: str = "en",
        components: Optional[list] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Send a pre-approved template message.
        
        Args:
            to: Recipient's phone number
            template_name: Name of the approved template
            language_code: Language code (e.g., "en", "fr")
            components: Template components (header, body, buttons)
            
        Returns:
            API response dict or None if failed
        """
        if not self.is_configured:
            logger.warning("WhatsApp API not configured")
            return None
        
        to = to.lstrip('+')
        
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code}
            }
        }
        
        if components:
            payload["template"]["components"] = components
        
        try:
            response = requests.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send template to {to}: {e}")
            return None
    
    def send_interactive_button_message(
        self, 
        to: str, 
        body_text: str,
        buttons: list,
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Send an interactive message with buttons.
        
        Args:
            to: Recipient's phone number
            body_text: Main message body
            buttons: List of button dicts with 'id' and 'title'
            header_text: Optional header
            footer_text: Optional footer
            
        Returns:
            API response dict or None if failed
        """
        if not self.is_configured:
            logger.warning("WhatsApp API not configured")
            return None
        
        to = to.lstrip('+')
        
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        interactive = {
            "type": "button",
            "body": {"text": body_text},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": btn['id'], "title": btn['title']}}
                    for btn in buttons[:3]  # Max 3 buttons
                ]
            }
        }
        
        if header_text:
            interactive["header"] = {"type": "text", "text": header_text}
        if footer_text:
            interactive["footer"] = {"text": footer_text}
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": interactive
        }
        
        try:
            response = requests.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send interactive message to {to}: {e}")
            return None
    
    def mark_message_as_read(self, message_id: str) -> bool:
        """
        Mark a message as read (shows blue ticks).
        
        Args:
            message_id: The WhatsApp message ID to mark as read
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_configured:
            return False
        
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        
        try:
            response = requests.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to mark message {message_id} as read: {e}")
            return False


# Singleton instance
_whatsapp_service = None


def get_whatsapp_service() -> WhatsAppService:
    """Get singleton WhatsApp service instance."""
    global _whatsapp_service
    if _whatsapp_service is None:
        _whatsapp_service = WhatsAppService()
    return _whatsapp_service
