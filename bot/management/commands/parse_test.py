"""
Parse a sample message to test the parser.

Usage:
    python manage.py parse_test "Name: John\nPhone: 123\nProject: Test"
"""

from django.core.management.base import BaseCommand
from bot.parser import IntakeFormParser


class Command(BaseCommand):
    help = 'Test the intake form parser with a sample message'

    def add_arguments(self, parser):
        parser.add_argument(
            'message',
            type=str,
            nargs='?',
            default=None,
            help='Message text to parse (use \\n for newlines)',
        )
        parser.add_argument(
            '--file',
            type=str,
            help='Read message from file',
        )

    def handle(self, *args, **options):
        parser = IntakeFormParser()
        
        self.stdout.write("\n=== Intake Form Parser Test ===\n")
        
        # Get message from args or file
        message = options.get('message')
        file_path = options.get('file')
        
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as f:
                message = f.read()
        elif message:
            # Handle escaped newlines
            message = message.replace('\\n', '\n')
        else:
            # Use sample message
            message = """Name: John Doe
Phone: +1234567890
Email: john@example.com
Project: Education Platform
School: Lincoln High School
Teacher: Ms. Smith
Grade: 10th
Subject: Mathematics
Lesson: Algebra Fundamentals
Notes: This is a test submission"""
        
        self.stdout.write("📝 Input Message:")
        self.stdout.write("-" * 40)
        self.stdout.write(message)
        self.stdout.write("-" * 40 + "\n")
        
        # Check if it's an intake form
        is_form = parser.is_intake_form_message(message)
        
        if is_form:
            self.stdout.write(self.style.SUCCESS("✅ Detected as INTAKE FORM"))
        else:
            self.stdout.write(self.style.WARNING("⚠️  Not detected as intake form"))
            self.stdout.write("   (Needs at least 2 field markers)")
        
        # Parse anyway to show results
        result = parser.parse(message)
        
        self.stdout.write("\n📊 Parsed Results:")
        self.stdout.write("-" * 40)
        self.stdout.write(f"  Name:        {result.name or '(empty)'}")
        self.stdout.write(f"  Phone:       {result.phone or '(empty)'}")
        self.stdout.write(f"  Email:       {result.email or '(empty)'}")
        self.stdout.write(f"  Project:     {result.project or '(empty)'}")
        self.stdout.write(f"  School:      {result.school or '(empty)'}")
        self.stdout.write(f"  Teacher:     {result.teacher or '(empty)'}")
        self.stdout.write(f"  Grade:       {result.grade or '(empty)'}")
        self.stdout.write(f"  Subject:     {result.subject or '(empty)'}")
        self.stdout.write(f"  Lessons:     {result.lesson_titles or '(empty)'}")
        self.stdout.write(f"  References:  {result.lesson_references or '(empty)'}")
        self.stdout.write(f"  Notes:       {result.notes or '(empty)'}")
        self.stdout.write("-" * 40)
        
        # Validation
        errors = result.validate()
        if errors:
            self.stdout.write(self.style.ERROR("\n❌ Validation Errors:"))
            for error in errors:
                self.stdout.write(f"   - {error}")
        else:
            self.stdout.write(self.style.SUCCESS("\n✅ Validation Passed"))
        
        self.stdout.write("\n")
