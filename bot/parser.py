"""
Smart Message Parser for WhatsApp Intake Forms.

This parser:
1. Detects if a message is an intake form (vs regular chat)
2. Extracts structured data from intake form messages
3. Validates required fields
4. Ignores non-form messages completely
"""

import re
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List, Tuple
import logging

logger = logging.getLogger('bot.parser')


@dataclass
class ParseResult:
    """Result of parsing a WhatsApp message."""
    
    # Whether this message is an intake form
    is_intake_form: bool = False
    confidence: float = 0.0
    
    # Extracted fields (only populated if is_intake_form=True)
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
    
    # Validation
    is_valid: bool = False
    missing_fields: List[str] = field(default_factory=list)
    error_message: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class IntakeFormParser:
    """
    Parser that detects and extracts intake form data from WhatsApp messages.
    
    The parser uses heuristics to determine if a message is an intake form:
    1. Must contain at least 2 recognized field patterns (Key: Value)
    2. Must have minimum confidence score based on matched fields
    3. Regular chat messages are ignored (returned with is_intake_form=False)
    """
    
    # Field mappings: normalized key -> list of variations
    FIELD_MAPPINGS = {
        'name': [
            'name', 'nom', 'full name', 'fullname', 'customer name', 
            'student name', 'client name', 'contact name'
        ],
        'phone': [
            'phone', 'telephone', 'tel', 'mobile', 'cell', 'number', 
            'phone number', 'téléphone', 'contact', 'whatsapp'
        ],
        'email': [
            'email', 'e-mail', 'mail', 'email address', 'courriel'
        ],
        'project': [
            'project', 'projet', 'project name', 'project type', 
            'request', 'demande', 'service'
        ],
        'notes': [
            'notes', 'note', 'comments', 'comment', 'remarques', 
            'additional info', 'details', 'description', 'message'
        ],
        'school': [
            'school', 'école', 'ecole', 'institution', 'school name',
            'establishment', 'établissement'
        ],
        'teacher': [
            'teacher', 'enseignant', 'professeur', 'instructor', 
            'teacher name', 'prof', 'facilitator'
        ],
        'grade': [
            'grade', 'class', 'classe', 'level', 'year', 'form',
            'niveau', 'grade level'
        ],
        'subject': [
            'subject', 'matière', 'matiere', 'course', 'subject area',
            'discipline', 'topic'
        ],
        'lesson_titles': [
            'lesson titles', 'lesson title', 'lessons', 'lesson', 
            'titres de leçon', 'titres', 'titre de leçon', 'lesson name'
        ],
        'lesson_references': [
            'lesson references', 'lesson reference', 'references', 
            'reference', 'références', 'ref', 'source', 'textbook'
        ]
    }
    
    # Required fields for a valid form
    REQUIRED_FIELDS = ['name', 'project']
    
    # Minimum fields to consider message as potential intake form
    MIN_FIELDS_FOR_DETECTION = 2
    
    # Confidence thresholds
    MIN_CONFIDENCE_THRESHOLD = 0.3
    
    # Regex patterns
    EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    PHONE_CLEANUP_REGEX = re.compile(r'[\s\-\.\(\)]+')
    
    # Patterns that indicate this is likely a regular chat message
    CHAT_INDICATORS = [
        r'^(hi|hello|hey|bonjour|salut|good morning|good afternoon)\s*[!.,]?\s*$',
        r'^(ok|okay|yes|no|sure|thanks|thank you|merci)\s*[!.,]?\s*$',
        r'^\d{1,3}\s*$',  # Just a number
        r'^[👍👎❤️😀😊🙏]+$',  # Just emojis
        r'^https?://',  # Just a link
    ]
    
    def __init__(self):
        # Build reverse mapping for faster lookup
        self._reverse_mapping: Dict[str, str] = {}
        for normalized_key, variations in self.FIELD_MAPPINGS.items():
            for variation in variations:
                self._reverse_mapping[variation.lower()] = normalized_key
        
        # Compile chat indicator patterns
        self._chat_patterns = [re.compile(p, re.IGNORECASE) for p in self.CHAT_INDICATORS]
    
    def _is_likely_chat_message(self, message: str) -> bool:
        """
        Quick check if message is obviously a regular chat message.
        Returns True if message should be ignored.
        """
        message = message.strip()
        
        # Very short messages are usually chat
        if len(message) < 10:
            return True
        
        # Check against chat patterns
        for pattern in self._chat_patterns:
            if pattern.match(message):
                return True
        
        # No colons at all usually means not a form
        if ':' not in message and '-' not in message and '=' not in message:
            return True
        
        return False
    
    def _extract_key_value_pairs(self, message: str) -> List[Tuple[str, str]]:
        """
        Extract all key-value pairs from message.
        Supports formats: "Key: Value", "Key - Value", "Key = Value"
        """
        pairs = []
        lines = message.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Try different separators
            for separator in [':', '=', '-']:
                if separator in line:
                    parts = line.split(separator, 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip()
                        
                        # Key should be reasonable length (not a sentence)
                        if 1 <= len(key) <= 30 and value:
                            pairs.append((key, value))
                            break
        
        return pairs
    
    def _normalize_key(self, key: str) -> Optional[str]:
        """Normalize a field key to its standard form."""
        key_lower = key.lower().strip()
        return self._reverse_mapping.get(key_lower)
    
    def _validate_email(self, email: str) -> str:
        """Validate and normalize email address."""
        email = email.strip().lower()
        if email and not self.EMAIL_REGEX.match(email):
            return ""
        return email
    
    def _normalize_phone(self, phone: str, fallback: str = "") -> str:
        """Normalize phone number format."""
        phone = phone.strip() if phone else fallback.strip()
        if not phone:
            return ""
        
        # Keep + for country code
        has_plus = phone.startswith('+')
        phone = self.PHONE_CLEANUP_REGEX.sub('', phone)
        if has_plus and not phone.startswith('+'):
            phone = '+' + phone
        return phone
    
    def _normalize_name(self, value: str) -> str:
        """Normalize name to title case."""
        return value.strip().title() if value else ""
    
    def parse(self, message: str, sender_phone: str = "") -> ParseResult:
        """
        Parse a WhatsApp message and determine if it's an intake form.
        
        Args:
            message: The raw WhatsApp message text
            sender_phone: Sender's phone number (used as fallback)
            
        Returns:
            ParseResult with is_intake_form=True if form detected, False otherwise
        """
        result = ParseResult()
        
        if not message or not message.strip():
            result.is_intake_form = False
            result.error_message = "Empty message"
            return result
        
        # Quick check for obvious chat messages
        if self._is_likely_chat_message(message):
            result.is_intake_form = False
            return result
        
        # Extract key-value pairs
        pairs = self._extract_key_value_pairs(message)
        
        if len(pairs) < self.MIN_FIELDS_FOR_DETECTION:
            result.is_intake_form = False
            return result
        
        # Match pairs to known fields
        matched_fields = {}
        matched_count = 0
        
        for key, value in pairs:
            normalized_key = self._normalize_key(key)
            if normalized_key:
                matched_fields[normalized_key] = value
                matched_count += 1
        
        # Calculate confidence based on matched fields
        total_possible = len(self.FIELD_MAPPINGS)
        confidence = matched_count / total_possible
        
        # Also boost confidence if required fields are present
        has_name = 'name' in matched_fields
        has_project = 'project' in matched_fields
        
        if has_name and has_project:
            confidence += 0.3
        elif has_name or has_project:
            confidence += 0.15
        
        confidence = min(confidence, 1.0)
        result.confidence = confidence
        
        # Determine if this is an intake form
        if confidence < self.MIN_CONFIDENCE_THRESHOLD:
            result.is_intake_form = False
            return result
        
        if matched_count < self.MIN_FIELDS_FOR_DETECTION:
            result.is_intake_form = False
            return result
        
        # This IS an intake form - extract and normalize all fields
        result.is_intake_form = True
        
        # Extract each field with normalization
        result.name = self._normalize_name(matched_fields.get('name', ''))
        result.phone = self._normalize_phone(matched_fields.get('phone', ''), sender_phone)
        result.email = self._validate_email(matched_fields.get('email', ''))
        result.project = matched_fields.get('project', '').strip()
        result.notes = matched_fields.get('notes', '').strip()
        result.school = self._normalize_name(matched_fields.get('school', ''))
        result.teacher = self._normalize_name(matched_fields.get('teacher', ''))
        result.grade = matched_fields.get('grade', '').strip()
        result.subject = matched_fields.get('subject', '').strip()
        result.lesson_titles = matched_fields.get('lesson_titles', '').strip()
        result.lesson_references = matched_fields.get('lesson_references', '').strip()
        
        # Validate required fields
        missing = []
        if not result.name:
            missing.append('name')
        if not result.project:
            missing.append('project')
        
        result.missing_fields = missing
        result.is_valid = len(missing) == 0
        
        if not result.is_valid:
            result.error_message = f"Missing required field(s): {', '.join(missing)}"
        
        logger.info(f"Parsed intake form: name={result.name}, project={result.project}, confidence={confidence:.2f}")
        
        return result


# Singleton parser instance
_parser_instance = None


def get_parser() -> IntakeFormParser:
    """Get singleton parser instance."""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = IntakeFormParser()
    return _parser_instance


def parse_message(message: str, sender_phone: str = "") -> ParseResult:
    """Convenience function to parse a message."""
    return get_parser().parse(message, sender_phone)
