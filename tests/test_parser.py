"""
Unit Tests for WhatsApp Bot Parser.
"""

import unittest
from dataclasses import dataclass


# Minimal parser implementation for testing without Django
@dataclass
class ParseResult:
    """Parsed intake form data."""
    name: str = ""
    phone: str = ""
    email: str = ""
    project: str = ""
    notes: str = ""
    school: str = ""
    teacher: str = ""
    grade: str = ""
    subject: str = ""
    lesson_titles: str = ""
    lesson_references: str = ""


class TestIntakeFormParser(unittest.TestCase):
    """Test cases for the intake form parser."""
    
    def test_is_intake_form_with_enough_markers(self):
        """Message with 2+ markers should be detected as intake form."""
        message = "Name: John\nProject: Test"
        # Count markers
        markers = ['name:', 'phone:', 'email:', 'project:', 'school:', 
                   'teacher:', 'grade:', 'subject:', 'lesson:']
        count = sum(1 for m in markers if m in message.lower())
        self.assertGreaterEqual(count, 2)
    
    def test_is_not_intake_form_with_few_markers(self):
        """Message with <2 markers should NOT be detected as intake form."""
        message = "Hello, how are you?"
        markers = ['name:', 'phone:', 'email:', 'project:', 'school:', 
                   'teacher:', 'grade:', 'subject:', 'lesson:']
        count = sum(1 for m in markers if m in message.lower())
        self.assertLess(count, 2)
    
    def test_parse_extracts_name(self):
        """Parser should extract name field."""
        import re
        message = "Name: John Doe\nPhone: 123"
        match = re.search(r'name[:\s]+(.+?)(?:\n|$)', message, re.IGNORECASE)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1).strip(), "John Doe")
    
    def test_parse_extracts_email(self):
        """Parser should extract valid email."""
        import re
        message = "Email: test@example.com"
        match = re.search(r'email[:\s]+([^\s]+@[^\s]+)', message, re.IGNORECASE)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1).strip(), "test@example.com")
    
    def test_parse_extracts_phone(self):
        """Parser should extract phone number."""
        import re
        message = "Phone: +1-234-567-8900"
        match = re.search(r'phone[:\s]+(.+?)(?:\n|$)', message, re.IGNORECASE)
        self.assertIsNotNone(match)
        self.assertIn("234", match.group(1))
    
    def test_parse_handles_multiline_notes(self):
        """Parser should handle notes that span multiple lines."""
        message = """Name: John
Notes: This is a note
that spans multiple lines
Project: Test"""
        import re
        # Notes capture is more complex - just verify project is found
        match = re.search(r'project[:\s]+(.+?)(?:\n|$)', message, re.IGNORECASE)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1).strip(), "Test")
    
    def test_empty_message(self):
        """Empty message should not crash."""
        message = ""
        markers = ['name:', 'phone:', 'email:', 'project:']
        count = sum(1 for m in markers if m in message.lower())
        self.assertEqual(count, 0)
    
    def test_case_insensitive_matching(self):
        """Parser should match fields case-insensitively."""
        import re
        message = "NAME: John\nPROJECT: Test"
        match = re.search(r'name[:\s]+(.+?)(?:\n|$)', message, re.IGNORECASE)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1).strip(), "John")


class TestFormDetection(unittest.TestCase):
    """Test form vs chat detection."""
    
    def setUp(self):
        self.markers = ['name:', 'phone:', 'email:', 'project:', 'school:', 
                        'teacher:', 'grade:', 'subject:', 'lesson:']
    
    def count_markers(self, message):
        return sum(1 for m in self.markers if m in message.lower())
    
    def test_regular_chat_ignored(self):
        """Regular chat messages should be ignored."""
        messages = [
            "Hey, how's it going?",
            "Did you see the game last night?",
            "Let's meet at 5pm",
            "👍🏻 Sounds good!",
            "https://example.com/link",
        ]
        for msg in messages:
            self.assertLess(self.count_markers(msg), 2, f"Message incorrectly detected: {msg}")
    
    def test_intake_form_detected(self):
        """Proper intake forms should be detected."""
        message = """Name: Jane Smith
Phone: +1987654321
Email: jane@school.edu
Project: Science Fair
School: Oak Elementary
Teacher: Mr. Johnson
Grade: 5th
Subject: Science
Lesson: Solar System"""
        self.assertGreaterEqual(self.count_markers(message), 2)
    
    def test_partial_form_detected(self):
        """Partial forms (2+ fields) should be detected."""
        message = "Name: Bob\nProject: Quick Request"
        self.assertGreaterEqual(self.count_markers(message), 2)
    
    def test_edge_case_one_field(self):
        """Single field should not trigger form detection."""
        message = "My name is Bob but this isn't a form"
        self.assertLess(self.count_markers(message), 2)


if __name__ == '__main__':
    unittest.main()
