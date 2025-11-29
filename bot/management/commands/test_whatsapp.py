"""
Test WhatsApp connection and send a test message.

Usage:
    python manage.py test_whatsapp --phone=+1234567890
"""

from django.core.management.base import BaseCommand
from bot.whatsapp_service import get_whatsapp_service


class Command(BaseCommand):
    help = 'Test WhatsApp API connection and optionally send a test message'

    def add_arguments(self, parser):
        parser.add_argument(
            '--phone',
            type=str,
            help='Phone number to send test message (with country code)',
        )

    def handle(self, *args, **options):
        whatsapp = get_whatsapp_service()
        
        self.stdout.write("\n=== WhatsApp API Configuration Test ===\n")
        
        # Check configuration
        if whatsapp.is_configured:
            self.stdout.write(self.style.SUCCESS("✅ WhatsApp API is configured"))
            self.stdout.write(f"   Phone Number ID: {whatsapp.phone_number_id[:10]}...")
            self.stdout.write(f"   API Version: {whatsapp.api_version}")
        else:
            self.stdout.write(self.style.ERROR("❌ WhatsApp API is NOT configured"))
            self.stdout.write("   Check WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID in .env")
            return
        
        # Send test message if phone provided
        phone = options.get('phone')
        if phone:
            self.stdout.write(f"\n📤 Sending test message to {phone}...")
            
            result = whatsapp.send_text_message(
                to=phone,
                message="🤖 WhatsApp Bot Test\n\nThis is a test message from your WhatsApp Bot. If you received this, your configuration is working correctly!"
            )
            
            if result:
                msg_id = result.get('messages', [{}])[0].get('id', 'unknown')
                self.stdout.write(self.style.SUCCESS(f"✅ Message sent! ID: {msg_id}"))
            else:
                self.stdout.write(self.style.ERROR("❌ Failed to send message"))
        else:
            self.stdout.write("\n💡 To send a test message, use: --phone=+1234567890")
        
        self.stdout.write("\n")
