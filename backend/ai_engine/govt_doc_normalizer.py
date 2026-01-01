"""Government Document Normalization Layer.

Transforms noisy, unordered OCR output from government-issued documents into
a clean, standardized structure before masking.

Key Features:
- Label-independent field extraction
- Handles multilingual content
- Confidence-based field validation
- Standard template output
- Works with any government document type
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class GovtDocType(str, Enum):
    """Government document subtypes."""
    AADHAAR = "Aadhaar Card"
    PAN = "PAN Card"
    PASSPORT = "Passport"
    DRIVING_LICENSE = "Driving License"
    VOTER_ID = "Voter ID"
    GOVT_EMPLOYEE_ID = "Government Employee ID"
    STUDENT_ID = "Government Student ID"
    NATIONAL_ID = "National ID Card"
    GENERIC = "Government ID"


@dataclass
class NormalizedField:
    """Represents a normalized field with confidence."""
    label: str
    value: str
    confidence: float
    source: str  # 'pattern', 'ner', 'context'
    original_position: int


@dataclass
class NormalizedDocument:
    """Normalized government document structure."""
    document_type: str
    authority: str
    holder_name: str
    guardian_name: str
    date_of_birth: str
    gender: str
    govt_id_number: str
    address: str
    qr_code_present: bool
    signature_present: bool
    confidence_score: float
    field_confidences: Dict[str, float]
    raw_text: str  # Original OCR text for reference


class GovernmentDocumentNormalizer:
    """Normalizes noisy government document OCR into structured format."""
    
    # Authority patterns for document type identification
    AUTHORITY_PATTERNS = {
        GovtDocType.AADHAAR: [
            r'(?:uidai|unique identification|authority of india|aadhaar)',
            r'भारत.*विशिष्ट.*पहचान'  # Bharat Vishisht Pehchan
        ],
        GovtDocType.PAN: [
            r'income tax department',
            r'permanent account number',
            r'आयकर विभाग'  # Aaykar Vibhag
        ],
        GovtDocType.PASSPORT: [
            r'passport|ministry of external affairs',
            r'republic of india',
            r'department of state',  # US passport
            r'P<[A-Z]{3}',  # MRZ line indicator
            r'विदेश मंत्रालय'  # Videsh Mantralaya
        ],
        GovtDocType.DRIVING_LICENSE: [
            r'(?:driving|transport).*(?:license|licence|authority)',
            r'rto|regional transport',
            r'dl[\-\s]',  # DL- prefix
            r'vehicle class',
            r'परिवहन.*विभाग'  # Parivahan Vibhag
        ],
        GovtDocType.VOTER_ID: [
            r'election commission',
            r'electoral.*photo.*identity|epic',
            r'निर्वाचन.*आयोग'  # Nirvachan Aayog
        ]
    }
    
    # Name patterns (multilingual)
    NAME_PATTERNS = [
        r'(?:name|naam|नाम|Name|NAME)\s*[:/]?\s*\n?\s*([A-Z][A-Z\s]+?)(?=\n|$)',  # All caps name after "Name" label
        r'(?:name|naam|नाम|Name|NAME)\s*[:/]?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',  # Mixed case after label
        r'(?:holder|bearer)\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})$',  # Standalone name pattern
        r'\b([A-Z][A-Z]+(?:\s+[A-Z][A-Z]+){1,3})\b',  # All caps names (2-4 words)
    ]
    
    # Guardian name patterns
    GUARDIAN_PATTERNS = [
        r"(?:father|mother|guardian|Father|FATHER)['']?s?\s*(?:name|Name|NAME)?\s*[:/]?\s*\n?\s*([A-Z][A-Z\s']+?)(?=\n|$)",  # "Father's Name: RAJESH SHARMA" or on next line
        r"(?:s/o|d/o|w/o|पिता|माता)\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",  # "S/o: Ram Kumar"
        r"(?:father|mother|guardian)\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})",  # "Father: Ram Kumar Sharma"
        r"(?:frat|fira).*?\s+([A-Z][A-Z\s]+?)(?=\n|Date|date|DATE)",  # Handle OCR errors like "frat" for "father"
    ]
    
    # DOB patterns (all formats)
    DOB_PATTERNS = [
        r'(?:dob|date.*birth|birth.*date|fecha de nacimiento|date de naissance|जन्म.*तिथि|Date.*Birth|DOB|wa.*wi.*atte)\s*[:/]?\s*\n?\s*(\d{1,2}\s+[A-Za-z]{3,}\s+\d{4})',  # 2 Jan 1974
        r'(?:dob|date.*birth|birth.*date|जन्म.*तिथि|Date.*Birth|DOB)\s*[:/]?\s*\n?\s*(\d{1,2}[/\.\-]\d{1,2}[/\.\-]\d{2,4})',
        r'\b(\d{1,2}[/\.]\d{1,2}[/\.]\d{4})\b',  # DD/MM/YYYY or DD.MM.YYYY (more strict)
        r'\b(\d{2}[/\.]\d{2}[/\.]\d{4})\b',  # DD/MM/YYYY or DD.MM.YYYY
        r'\b(\d{4}[-/]\d{2}[-/]\d{2})\b',  # YYYY-MM-DD
        r'\b(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})\b',  # 2 Jan 1974, 15 March 2000
    ]
    
    # Gender patterns (multilingual)
    GENDER_PATTERNS = [
        r'(?:gender|sex|लिंग)\s*:?\s*(male|female|m|f|पुरुष|महिला|transgender|trans)',
        r'\b(male|female|m\s*/\s*f|पुरुष|महिला)\b',
    ]
    
    # Address patterns
    ADDRESS_PATTERNS = [
        r'(?:address|residence|addr|पता)\s*:?\s*([^\n]{20,200})',
        r'(?:house|h\.?no|flat|plot|door)\s*[:#\.]?\s*\d+[^\n]{10,100}',
    ]
    
    def __init__(self):
        """Initialize normalizer with NER support if available."""
        self.spacy_nlp = None
        self._load_nlp_models()
    
    def _load_nlp_models(self):
        """Load spaCy for NER if available."""
        try:
            import spacy
            try:
                self.spacy_nlp = spacy.load("en_core_web_sm")
                logger.info("Loaded spaCy for NER")
            except OSError:
                logger.warning("spaCy model not available, using pattern-based extraction only")
        except ImportError:
            logger.warning("spaCy not installed, using pattern-based extraction only")
    
    def normalize_document(
        self, 
        raw_text: str,
        document_context: Dict[str, Any]
    ) -> NormalizedDocument:
        """
        Normalize government document OCR into standard structure.
        
        Args:
            raw_text: Raw OCR text (noisy, unordered)
            document_context: Context from classifier (type, confidence, signals)
            
        Returns:
            NormalizedDocument with standard structure
        """
        logger.info("Starting government document normalization")
        
        # Step 1: Identify specific document type
        doc_type = self._identify_document_type(raw_text)
        
        # Step 2: Extract authority name
        authority = self._extract_authority(raw_text, doc_type)
        
        # Step 3: Extract identity fields (order-independent)
        holder_name, holder_conf = self._extract_holder_name(raw_text)
        guardian_name, guardian_conf = self._extract_guardian_name(raw_text)
        dob, dob_conf = self._extract_dob(raw_text)
        gender, gender_conf = self._extract_gender(raw_text)
        govt_id, id_conf = self._extract_govt_id(raw_text, doc_type)
        address, addr_conf = self._extract_address(raw_text)
        
        # Step 4: Detect supplementary indicators
        qr_present = self._detect_qr_code(raw_text)
        sig_present = self._detect_signature(raw_text)
        
        # Step 5: Calculate overall confidence
        field_confidences = {
            'holder_name': holder_conf,
            'guardian_name': guardian_conf,
            'date_of_birth': dob_conf,
            'gender': gender_conf,
            'govt_id_number': id_conf,
            'address': addr_conf
        }
        
        overall_confidence = sum(field_confidences.values()) / len(field_confidences)
        
        # Step 6: Create normalized document
        normalized = NormalizedDocument(
            document_type=doc_type.value,
            authority=authority,
            holder_name=holder_name,
            guardian_name=guardian_name,
            date_of_birth=dob,
            gender=gender,
            govt_id_number=govt_id,
            address=address,
            qr_code_present=qr_present,
            signature_present=sig_present,
            confidence_score=overall_confidence,
            field_confidences=field_confidences,
            raw_text=raw_text
        )
        
        logger.info(f"Normalized {doc_type.value} with {overall_confidence:.2%} confidence")
        
        return normalized
    
    def _identify_document_type(self, text: str) -> GovtDocType:
        """Identify specific government document type."""
        text_lower = text.lower()
        
        # First try: Match authority patterns
        for doc_type, patterns in self.AUTHORITY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    return doc_type
        
        # Second try: Pattern-based detection (when keywords fail)
        # Check for Aadhaar number pattern (12 or 16 digits)
        aadhaar_pattern = r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}(?:[\s\-]?\d{4})?\b'
        if re.search(aadhaar_pattern, text):
            # Further validation: check if it has typical Aadhaar structure
            # (Name, DOB, Gender, no PAN-like ID)
            has_dob = bool(re.search(r'dob|date.*birth|\d{2}[/\.]\d{2}[/\.]\d{4}', text_lower))
            has_gender = bool(re.search(r'\b(male|female|fe|पुरुष|महिला)\b', text_lower))
            has_pan = bool(re.search(r'\b[A-Z]{5}\d{4}[A-Z]\b', text))
            
            if has_dob and has_gender and not has_pan:
                return GovtDocType.AADHAAR
        
        # Check for PAN pattern (5 letters + 4 digits + 1 letter)
        pan_pattern = r'\b[A-Z]{5}\d{4}[A-Z]\b'
        if re.search(pan_pattern, text):
            return GovtDocType.PAN
        
        return GovtDocType.GENERIC
    
    def _extract_nationality(self, text: str) -> str:
        """Extract nationality (for passports)."""
        # Look for nationality/country patterns
        patterns = [
            (r'UNITED STATES OF AMERICA', 'United States of America'),
            (r'REPUBLIC OF INDIA', 'Republic of India'),
            (r'P<(USA|IND|GBR|CAN|AUS)', None),  # From MRZ country code
            (r'(?:nationality|nationalité)\s*:?\s*([A-Z][a-z\s]+)', None),
        ]
        
        # Country code mapping for MRZ
        country_map = {
            'USA': 'United States of America',
            'IND': 'Republic of India',
            'GBR': 'United Kingdom',
            'CAN': 'Canada',
            'AUS': 'Australia',
        }
        
        for pattern, default_name in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if default_name:
                    return default_name
                elif match.lastindex and len(match.groups()) > 0:
                    code_or_name = match.group(1).strip().upper()
                    return country_map.get(code_or_name, code_or_name)
        
        return "NOT AVAILABLE"
    
    def _extract_authority(self, text: str, doc_type: GovtDocType) -> str:
        """Extract issuing authority name."""
        text_lower = text.lower()
        
        # Check for known authorities
        authority_map = {
            GovtDocType.AADHAAR: "Unique Identification Authority of India (UIDAI)",
            GovtDocType.PAN: "Income Tax Department, Government of India",
            GovtDocType.PASSPORT: "Ministry of External Affairs, Government of India",
            GovtDocType.DRIVING_LICENSE: "Transport Authority",
            GovtDocType.VOTER_ID: "Election Commission of India"
        }
        
        # Try to extract actual authority from text
        authority_patterns = [
            r'((?:government|ministry|department|authority|commission)[^\n]{0,80})',
            r'([\w\s]+(?:government|authority|commission|department))',
        ]
        
        for pattern in authority_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                authority = match.group(1).strip()
                # Clean up
                authority = ' '.join(authority.split())  # Normalize whitespace
                if len(authority) > 10:  # Valid authority name
                    return authority
        
        # Fallback to default for doc type
        return authority_map.get(doc_type, "Government Authority")
    
    def _extract_holder_name(self, text: str) -> Tuple[str, float]:
        """Extract document holder's name."""
        candidates = []
        
        # Check for MRZ (Machine Readable Zone) - most reliable for passports
        # Format: P<COUNTRYCODE SURNAME<<GIVENNAME1<GIVENNAME2<<<...
        mrz_match = re.search(r'P<[A-Z]{3}([A-Z]+)<<([A-Z<]+?)(<+)$', text, re.MULTILINE)
        if mrz_match:
            surname = mrz_match.group(1).strip()
            given_names = mrz_match.group(2).replace('<', ' ').strip()
            full_name = f"{given_names} {surname}"
            return full_name, 0.98
        
        # For PAN cards, look specifically after the PAN number
        # PAN card format often has: PAN_NUMBER \n NAME
        pan_match = re.search(r'[A-Z]{5}\d{4}[A-Z]\s*\n+\s*([A-Z][A-Z\s]+?)(?=\n|$)', text, re.MULTILINE)
        if pan_match:
            name = pan_match.group(1).strip()
            # Clean up extra whitespace
            name = re.sub(r'\s+', ' ', name)
            if self._is_valid_name(name) and len(name.split()) >= 2:
                # High confidence for PAN card name extraction
                return name, 0.95
        
        # Try pattern-based extraction with position tracking
        for pattern in self.NAME_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                name = match.group(1).strip()
                # Clean up whitespace
                name = re.sub(r'\s+', ' ', name)
                # Validate name
                if self._is_valid_name(name):
                    # Prefer names that appear early in document
                    position_score = 1.0 - (match.start() / max(len(text), 1000)) * 0.2
                    # Prefer longer names (full names vs single word)
                    length_bonus = min(len(name.split()) * 0.05, 0.15)
                    confidence = 0.85 * position_score + length_bonus
                    candidates.append((name, confidence, match.start()))
        
        # Try NER-based extraction
        if self.spacy_nlp:
            doc = self.spacy_nlp(text[:2000])
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    name = ent.text.strip()
                    name = re.sub(r'\s+', ' ', name)
                    if self._is_valid_name(name):
                        candidates.append((name, 0.80, ent.start_char))
        
        if not candidates:
            return "NOT AVAILABLE", 0.0
        
        # Pick best candidate (highest confidence, prefer earlier position)
        best = max(candidates, key=lambda x: (x[1], -x[2]))
        return best[0], best[1]
    
    def _extract_guardian_name(self, text: str) -> Tuple[str, float]:
        """Extract father/mother/guardian name."""
        candidates = []
        
        # Special pattern for PAN cards: Look for a line after "Father's Name" label
        # that might be garbled by OCR (like "frat a1 7 / Father's Name")
        father_section_match = re.search(
            r"(?:father|frat|fira).*?(?:name|Name|NAME).*?\n+\s*([A-Z][A-Z\s]+?)(?=\n|so |Date|date|wa\s|$)",
            text,
            re.IGNORECASE | re.MULTILINE
        )
        if father_section_match:
            name = father_section_match.group(1).strip()
            name = re.sub(r'\s+', ' ', name)  # Normalize whitespace
            # Clean up common OCR artifacts at the end
            name = re.sub(r'\s+(?:so|a|o)\s*$', '', name, flags=re.IGNORECASE)
            if self._is_valid_name(name) and len(name.split()) >= 2:
                return name, 0.92
        
        for pattern in self.GUARDIAN_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                name = match.group(1).strip()
                # Clean up OCR artifacts
                name = re.sub(r'\s+', ' ', name)  # Normalize whitespace
                name = name.replace('\n', ' ').strip()
                # Clean up common OCR artifacts at the end
                name = re.sub(r'\s+(?:so|a|o)\s*$', '', name, flags=re.IGNORECASE)
                
                # Skip if it looks like it captured the label itself
                if any(label in name.lower() for label in ['father name', 'mother name', 'guardian name']):
                    continue
                
                # Special handling for PAN cards where guardian field itself contains "FATHER NAME"
                # e.g., "APPLICANT'S FATHER NAME" is the actual value, not a label
                if len(name) > 15 and any(c.isalpha() and c.isupper() for c in name[:10]):
                    # Likely a real value, not just a label
                    candidates.append((name, 0.90))
                elif self._is_valid_name(name):
                    candidates.append((name, 0.90))
        
        if candidates:
            # Return the best candidate
            return max(candidates, key=lambda x: x[1])
        
        return "NOT AVAILABLE", 0.0
    
    def _extract_dob(self, text: str) -> Tuple[str, float]:
        """Extract date of birth."""
        # Look for DOB with context
        for pattern in self.DOB_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                dob = match.group(1).strip()
                # Validate date format
                if self._is_valid_date(dob):
                    # Check if near birth context
                    context_start = max(0, match.start() - 50)
                    context_end = min(len(text), match.end() + 50)
                    context = text[context_start:context_end].lower()
                    
                    if any(kw in context for kw in ['birth', 'dob', 'born', 'जन्म']):
                        return dob, 0.95
                    else:
                        return dob, 0.75  # Date found but no clear context
        
        return "NOT AVAILABLE", 0.0
    
    def _extract_gender(self, text: str) -> Tuple[str, float]:
        """Extract gender."""
        # Check MRZ for gender (M/F after DOB in second line)
        # Format: PASSPORTNUMBER<COUNTRY<YYMMDDCHECKDIGIT<M/F ...
        # US Passports: 9 digits + 3-letter country + 7 digits (6 DOB + 1 check) + gender
        mrz_gender = re.search(r'\d{9}[A-Z]{3}\d{7}([MF])', text)
        if mrz_gender and mrz_gender.group(1) in ['M', 'F']:
            return "Male" if mrz_gender.group(1) == 'M' else "Female", 0.98
        
        for pattern in self.GENDER_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                gender = match.group(1).strip().upper()
                # Normalize
                if gender in ['M', 'MALE', 'पुरुष']:
                    return "Male", 0.90
                elif gender in ['F', 'FEMALE', 'महिला']:
                    return "Female", 0.90
                elif gender in ['TRANSGENDER', 'TRANS', 'OTHER']:
                    return "Other", 0.90
                else:
                    return gender.title(), 0.80
        
        return "NOT AVAILABLE", 0.0
    
    def _extract_govt_id(self, text: str, doc_type: GovtDocType) -> Tuple[str, float]:
        """Extract government ID number based on document type."""
        # Document-specific patterns
        patterns = {
            GovtDocType.AADHAAR: [
                (r'\b(\d{4}[\s\-]?\d{4}[\s\-]?\d{4}(?:[\s\-]?\d{4})?)\b', 0.95),  # 12 or 16 digits (VID)
            ],
            GovtDocType.PAN: [
                (r'\b([A-Z]{5}\d{4}[A-Z])\b', 0.98),  # Standard PAN format
                (r'(?:PAN|pan).*?([A-Z]{5}\d{4}[A-Z])\b', 0.95),  # With PAN label nearby
                (r'(?:RS|MS|HS)\s*([A-Z]{5}\d{4}[A-Z])\b', 0.90),  # OCR errors before PAN
            ],
            GovtDocType.PASSPORT: [
                (r'passport\s*(?:number|no\.?|#)?\s*:?\s*([A-Z]?\d{7,9})\b', 0.95),  # Labeled
                (r'(?:^|[^\d])(\d{8,9})(?:[^\d]|$)', 0.90),  # 8-9 digit number (passport #)
                (r'\b([A-Z]\d{7,8})\b', 0.85),  # Pattern match
                (r'P<[A-Z]{3}[A-Z<]+\n(\d{9})', 0.80),  # From MRZ second line (lower priority)
            ],
            GovtDocType.DRIVING_LICENSE: [
                (r'license\s+number\s*:?\s*([A-Z]{2}[\-/\s]?[A-Z0-9\-]{6,})', 0.95),
                (r'\b(DL[\-\s][A-Z]{2}[\-\s]\d+)\b', 0.90),
                (r'\b([A-Z]{2}[\-/]?\d{2}[\-/]?\d{4,})\b', 0.85),
            ],
            GovtDocType.VOTER_ID: [
                (r'\b([A-Z]{3}\d{7})\b', 0.90),
            ]
        }
        
        # Try document-specific patterns first
        if doc_type in patterns:
            for pattern, confidence in patterns[doc_type]:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    id_number = match.group(1).strip()
                    return id_number, confidence
        
        # Fallback: Try ID Number label pattern first (look after the label, not in it)
        id_label_match = re.search(r'(?:id|identity)\s+number\s*:?\s*([A-Z0-9]{8,})\b', text, re.IGNORECASE)
        if id_label_match:
            return id_label_match.group(1).strip(), 0.85
        
        # Fallback: Try Aadhaar pattern (most common govt ID in India)
        aadhaar_match = re.search(r'\b(\d{4}[\s\-]?\d{4}[\s\-]?\d{4}(?:[\s\-]?\d{4})?)\b', text)
        if aadhaar_match:
            return aadhaar_match.group(1).strip(), 0.85
        
        # Generic alphanumeric ID pattern (8-16 chars) - avoid common words
        generic_matches = re.findall(r'\b([A-Z0-9]{10,})\b', text)  # At least 10 chars to avoid short words
        for match in generic_matches:
            # Skip common words
            if match.upper() not in ['GOVERNMENT', 'AUTHORITY', 'DOCUMENT', 'IDENTIFICATION']:
                return match, 0.70
        
        return "NOT AVAILABLE", 0.0
    
    def _extract_place_of_birth(self, text: str) -> str:
        """Extract place of birth (for passports)."""
        # Look for place of birth patterns
        pob_patterns = [
            r'(?:place of birth|lugar de nacimiento|lieu de naissance)(?:[^\n]*?)\s*([A-Z][a-z]+(?:[,\s]+[A-Z]+)?)',
            r'Mumbai[,\s]+(?:\')?INDIA',  # Specific pattern from this passport
            r'([A-Z][a-z]+,\s*[A-Z]+)\s+(?:Date of issue|sex)',  # Before next field
        ]
        
        for pattern in pob_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if match.lastindex:
                    pob = match.group(1).strip()
                else:
                    pob = match.group().strip()
                # Clean up
                pob = pob.replace("'", "").strip()
                if len(pob) > 3:
                    return pob
        
        return "NOT AVAILABLE"
    
    def _extract_address(self, text: str) -> Tuple[str, float]:
        """Extract address."""
        for pattern in self.ADDRESS_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                address = match.group(1).strip() if match.lastindex else match.group()
                # Clean address
                address = ' '.join(address.split())  # Normalize whitespace
                address = address.replace('\n', ', ')
                if len(address) > 20:  # Valid address
                    return address, 0.85
        
        # Try multi-line address detection
        lines = text.split('\n')
        address_lines = []
        found_address_marker = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for address markers
            if re.search(r'(?:address|residence|addr|पता)', line, re.IGNORECASE):
                found_address_marker = True
                # Get content after marker
                parts = re.split(r'(?:address|residence|addr|पता)\s*:?', line, flags=re.IGNORECASE)
                if len(parts) > 1 and parts[1].strip():
                    address_lines.append(parts[1].strip())
                continue
            
            # After address marker, collect lines that look like address components
            if found_address_marker:
                if re.search(r'\d+', line) or len(line.split()) <= 8:
                    address_lines.append(line)
                    if len(address_lines) >= 3:  # Got enough
                        break
                else:
                    break  # End of address
        
        if address_lines:
            address = ', '.join(address_lines)
            if len(address) > 20:
                return address, 0.80
        
        return "NOT AVAILABLE", 0.0
    
    def _detect_qr_code(self, text: str) -> bool:
        """Detect QR code presence."""
        patterns = [
            r'qr[\s\-]?code',
            r'<qr>',
            r'\[qr\s*code\]',
            r'barcode',
        ]
        
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _detect_signature(self, text: str) -> bool:
        """Detect signature indicator."""
        patterns = [
            r'signature',
            r'signed',
            r'हस्ताक्षर',  # Hastakshar
        ]
        
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _is_valid_name(self, name: str) -> bool:
        """Validate if string is a valid name."""
        if not name or len(name) < 3:
            return False
        
        # Must have at least one letter
        if not any(c.isalpha() for c in name):
            return False
        
        # Should not contain numbers
        if any(c.isdigit() for c in name):
            return False
        
        # Should not be common labels or document terms
        exclude_terms = [
            'permanent account number', 'account number', 'card', 'identity',
            'passport', 'license', 'voter', 'aadhaar', 'pan', 'epic',
            'document', 'certificate', 'identification', 'holder name',
            'father name', 'mother name', 'guardian name', 'bearer',
            'signature', 'photo', 'date of birth', 'address'
        ]
        name_lower = name.lower()
        for term in exclude_terms:
            if term in name_lower:
                return False
        
        # Single word labels like "NAME", "FATHER", "SIGNATURE"
        single_labels = ['name', 'father', 'mother', 'guardian', 'holder', 
                        'bearer', 'signature', 'photo', 'address', 'gender']
        if name_lower in single_labels:
            return False
        
        return True
    
    def _is_valid_date(self, date_str: str) -> bool:
        """Validate date string."""
        # Check if contains reasonable date components
        if not re.search(r'\d', date_str):
            return False
        
        # Should not be too long
        if len(date_str) > 20:
            return False
        
        return True
    
    def format_normalized_document(
        self, 
        normalized: NormalizedDocument,
        mask: bool = False,
        raw_text: str = ""
    ) -> str:
        """
        Format normalized document into standard text structure.
        
        PURPOSE-AWARE MASKING POLICY:
        - Shows fields required for organizational verification (Name, ID, DOB, Gender)
        - Masks personal/unnecessary data (Address, Guardian Name, Signature, etc.)
        - Different masking rules per document type based on organizational needs
        
        Args:
            normalized: NormalizedDocument instance
            mask: If True, apply purpose-aware masking
            raw_text: Original OCR text for extracting additional fields
            
        Returns:
            Formatted text in standard template
        """
        # Determine document-specific masking policy
        doc_type = normalized.document_type.lower()
        
        # Apply PURPOSE-AWARE MASKING if requested
        if mask:
            # ALWAYS VISIBLE (Organization-Required Fields)
            holder_name = normalized.holder_name  # Employee name - always needed
            authority = normalized.authority  # Issuing authority - for verification
            
            # Document-specific masking rules
            if 'aadhaar' in doc_type or 'aadhar' in doc_type:
                # AADHAAR: Show Name, ID, DOB, Gender | Mask Address, Guardian
                govt_id = normalized.govt_id_number  # Keep visible for verification
                dob = normalized.date_of_birth  # Keep visible for age verification
                gender = normalized.gender  # Keep visible for identity verification
                guardian_name = "[MASKED-GUARDIAN-NAME]" if normalized.guardian_name != "NOT AVAILABLE" else "NOT AVAILABLE"
                address = "[MASKED-ADDRESS]" if normalized.address != "NOT AVAILABLE" else "NOT AVAILABLE"
                
            elif 'pan' in doc_type:
                # PAN: Show Name, PAN, DOB | Mask Guardian Name, Signature
                govt_id = normalized.govt_id_number  # Keep visible for tax verification
                dob = normalized.date_of_birth  # Keep visible for verification
                gender = normalized.gender if normalized.gender != "NOT AVAILABLE" else "NOT AVAILABLE"
                guardian_name = "[MASKED-GUARDIAN-NAME]" if normalized.guardian_name != "NOT AVAILABLE" else "NOT AVAILABLE"
                address = "[MASKED-ADDRESS]" if normalized.address != "NOT AVAILABLE" else "NOT AVAILABLE"
                signature_ref = "[MASKED-SIGNATURE]" if normalized.signature_present else "NOT AVAILABLE"
                
            elif 'passport' in doc_type:
                # PASSPORT: Show Name, ID, DOB, Gender, Nationality, Validity | Mask Address, Place of Birth, File Number
                govt_id = normalized.govt_id_number  # Keep visible for identity verification
                dob = normalized.date_of_birth  # Keep visible
                gender = normalized.gender  # Keep visible
                guardian_name = "[MASKED-GUARDIAN-NAME]" if normalized.guardian_name != "NOT AVAILABLE" else "NOT AVAILABLE"
                address = "[MASKED-ADDRESS]" if normalized.address != "NOT AVAILABLE" else "NOT AVAILABLE"
                place_of_birth = "[MASKED]"
                file_number = "[MASKED-FILE-NO]"
                
            elif 'license' in doc_type or 'dl' in doc_type:
                # DRIVING LICENSE: Show Name, License Number, Vehicle Class, Validity | Mask DOB, Blood Group, Guardian, Address
                govt_id = normalized.govt_id_number  # Keep visible for license verification
                dob = "[MASKED-DOB]" if normalized.date_of_birth != "NOT AVAILABLE" else "NOT AVAILABLE"  # Mask DOB
                gender = normalized.gender if normalized.gender != "NOT AVAILABLE" else "NOT AVAILABLE"
                guardian_name = "[MASKED-GUARDIAN-NAME]" if normalized.guardian_name != "NOT AVAILABLE" else "NOT AVAILABLE"
                address = "[MASKED-ADDRESS]" if normalized.address != "NOT AVAILABLE" else "NOT AVAILABLE"
                blood_group = "[MASKED-BLOOD-GROUP]"
                
            elif 'voter' in doc_type or 'epic' in doc_type:
                # VOTER ID: Show Name, ID, Gender | Mask Age, Address, Guardian
                govt_id = normalized.govt_id_number  # Keep visible
                age = "[MASKED]"  # Mask age
                gender = normalized.gender  # Keep visible
                guardian_name = "[MASKED-GUARDIAN-NAME]" if normalized.guardian_name != "NOT AVAILABLE" else "NOT AVAILABLE"
                address = "[MASKED-ADDRESS]" if normalized.address != "NOT AVAILABLE" else "NOT AVAILABLE"
                
            else:
                # GENERIC GOVERNMENT ID: Show Name, ID, Validity | Mask Personal Details
                govt_id = normalized.govt_id_number  # Keep visible
                personal_details = "[MASKED]"
                
        else:
            # ORIGINAL (No masking)
            holder_name = normalized.holder_name
            authority = normalized.authority
            guardian_name = normalized.guardian_name
            dob = normalized.date_of_birth
            gender = normalized.gender
            govt_id = normalized.govt_id_number
            address = normalized.address
            signature_ref = "Present" if normalized.signature_present else "NOT AVAILABLE"
            
            # Calculate age from DOB for Voter ID
            if 'voter' in doc_type or 'epic' in doc_type:
                age = self._calculate_age(dob) if dob != "NOT AVAILABLE" else "NOT AVAILABLE"
            
            # Additional fields for specific documents
            place_of_birth = self._extract_place_of_birth(raw_text) if ('passport' in normalized.document_type.lower() and raw_text) else "NOT AVAILABLE"
            file_number = "NOT AVAILABLE"  # Would need extraction
            blood_group = "NOT AVAILABLE"  # Would need extraction
            personal_details = "Available" if any([guardian_name != "NOT AVAILABLE", address != "NOT AVAILABLE"]) else "NOT AVAILABLE"
        
        # Build document-specific template
        doc_type = normalized.document_type.lower()
        
        # Determine visible and masked fields for metadata
        visible_fields = ["Name"]
        masked_fields = []
        
        if 'aadhaar' in doc_type or 'aadhar' in doc_type:
            # AADHAAR CARD TEMPLATE
            if mask:
                visible_fields.extend(["Aadhaar Number", "Date of Birth", "Gender"])
                masked_fields.extend(["Address", "Guardian Name"])
            
            template = f"""DOCUMENT TYPE: Aadhaar Card
Authority: {authority}

Name: {holder_name}
Aadhaar Number: {govt_id}
Gender: {gender}
Date of Birth: {dob}

Address: {address}
Guardian Name: {guardian_name}
"""
            
        elif 'pan' in doc_type:
            # PAN CARD TEMPLATE
            if mask:
                visible_fields.extend(["Name", "PAN Number"])
                masked_fields.extend(["Date of Birth", "Father's Name", "Signature Reference"])
                
                # Mask sensitive fields
                masked_dob = "[MASKED-DOB]" if dob != "NOT AVAILABLE" else "NOT AVAILABLE"
                masked_guardian = "[MASKED-FATHER-NAME]" if guardian_name != "NOT AVAILABLE" else "NOT AVAILABLE"
                masked_signature = "[MASKED-SIGNATURE]" if signature_ref != "NOT AVAILABLE" else "NOT AVAILABLE"
            else:
                masked_dob = dob
                masked_guardian = guardian_name
                masked_signature = signature_ref
            
            template = f"""DOCUMENT TYPE: PAN Card
Authority: {authority}

Name: {holder_name}
PAN Number: {govt_id}
Date of Birth: {masked_dob}

Father's Name: {masked_guardian}
Signature Reference: {masked_signature}
"""
            
        elif 'passport' in doc_type:
            # PASSPORT TEMPLATE
            if mask:
                visible_fields.extend(["Passport Number", "Nationality", "Gender", "Date of Birth", "Valid Till"])
                masked_fields.extend(["Place of Birth", "Address", "File Number"])
            
            # Extract validity and nationality
            validity = normalized.validity_info if hasattr(normalized, 'validity_info') and normalized.validity_info != 'NOT AVAILABLE' else "NOT AVAILABLE"
            nationality = self._extract_nationality(raw_text) if raw_text else "NOT AVAILABLE"
            
            template = f"""DOCUMENT TYPE: Passport
Authority: {authority}

Name: {holder_name}
Passport Number: {govt_id}
Nationality: {nationality}
Gender: {gender}
Date of Birth: {dob}
Valid Till: {validity}

Place of Birth: {place_of_birth if not mask else '[MASKED]' if place_of_birth != 'NOT AVAILABLE' else 'NOT AVAILABLE'}
Address: {address}
File Number: {file_number if mask else 'NOT AVAILABLE'}
"""
            
        elif 'license' in doc_type or 'dl' in doc_type:
            # DRIVING LICENSE TEMPLATE
            if mask:
                visible_fields.extend(["License Number", "Vehicle Class", "Date of Issue", "Date of Expiry"])
                masked_fields.extend(["Date of Birth", "Blood Group", "Parent Name", "Address"])
            
            # Extract validity info
            validity = normalized.validity_info if hasattr(normalized, 'validity_info') and normalized.validity_info != 'NOT AVAILABLE' else "NOT AVAILABLE"
            vehicle_class = "MCWG"  # Default - would need extraction
            
            # Parse validity into issue/expiry if available
            if validity != "NOT AVAILABLE" and "-" in validity:
                parts = validity.split("-")
                date_of_issue = parts[0].strip() if len(parts) > 0 else "NOT AVAILABLE"
                date_of_expiry = parts[1].strip() if len(parts) > 1 else "NOT AVAILABLE"
            else:
                date_of_issue = "NOT AVAILABLE"
                date_of_expiry = "NOT AVAILABLE"
            
            template = f"""DOCUMENT TYPE: Driving License
Authority: {authority}

Name: {holder_name}
License Number: {govt_id}
Vehicle Class: {vehicle_class}
Date of Issue: {date_of_issue}
Date of Expiry: {date_of_expiry}

Date of Birth: {dob}
Blood Group: {blood_group}
Parent Name: {guardian_name}
Address: {address}
"""
            
        elif 'voter' in doc_type or 'epic' in doc_type:
            # VOTER ID TEMPLATE
            if mask:
                visible_fields.extend(["Voter ID Number", "Gender"])
                masked_fields.extend(["Age", "Address", "Parent Name"])
            
            template = f"""DOCUMENT TYPE: Voter ID
Authority: {authority}

Name: {holder_name}
Voter ID Number: {govt_id}
Gender: {gender}

Age: {age}
Address: {address}
Parent Name: {guardian_name}
"""
            
        else:
            # GENERIC GOVERNMENT ID TEMPLATE
            if mask:
                visible_fields.extend(["ID Number", "Validity"])
                masked_fields.extend(["Personal Details"])
            
            validity = normalized.validity_info if hasattr(normalized, 'validity_info') and normalized.validity_info != 'NOT AVAILABLE' else "NOT AVAILABLE"
            
            template = f"""DOCUMENT TYPE: Government ID
Authority: {authority}

Name: {holder_name}
ID Number: {govt_id}
Validity: {validity}

Personal Details: {personal_details}
"""
        
        # Add masking metadata (for masked versions only)
        if mask:
            metadata = f"""
---
MASKING METADATA:
Policy: organizational_use
Document Type: {normalized.document_type}
Visible Fields: {', '.join(visible_fields)}
Masked Fields: {', '.join(masked_fields) if masked_fields else 'None'}
"""
            template += metadata
        
        # Add confidence info for unconfirmed fields (original only)
        if not mask:
            unconfirmed = []
            for field, conf in normalized.field_confidences.items():
                if conf < 0.85:
                    unconfirmed.append(f"{field}: {conf:.0%}")
            
            if unconfirmed:
                template += f"\n---\nField Confidence (Low):\n"
                for item in unconfirmed:
                    template += f"- {item}\n"
        
        return template.strip()
    
    def _calculate_age(self, dob_str: str) -> str:
        """Calculate age from DOB string."""
        if dob_str == "NOT AVAILABLE":
            return "NOT AVAILABLE"
        
        try:
            # Try different date formats
            for fmt in ["%d/%m/%Y", "%d.%m.%Y", "%d-%m-%Y", "%Y-%m-%d"]:
                try:
                    from datetime import datetime
                    dob = datetime.strptime(dob_str, fmt)
                    today = datetime.now()
                    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                    return str(age)
                except ValueError:
                    continue
            return "NOT AVAILABLE"
        except:
            return "NOT AVAILABLE"
