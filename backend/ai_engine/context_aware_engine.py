"""Context-Aware Sensitive Data Intelligence Engine.

This module provides intelligent, context-based detection and masking of sensitive 
information without requiring explicit field names or hardcoded rules.

Features:
- Automatic document type classification
- Semantic field detection using NLP/NER
- Sensitivity scoring with confidence levels
- Adaptive masking based on document context
- Explainability for all masking decisions
"""

import re
import logging
import difflib
from typing import List, Dict, Tuple, Optional, Any, Set
from dataclasses import dataclass, field as dataclass_field
from enum import Enum
from collections import Counter

logger = logging.getLogger(__name__)


class DocumentType(str, Enum):
    """Document type classifications."""
    INVOICE = "invoice"
    FINANCIAL = "financial"
    HR = "hr"
    LEGAL = "legal"
    PERSONAL = "personal"
    RECEIPT = "receipt"
    BILL = "bill"
    GOVERNMENT_ID = "government_id"
    GENERIC = "generic"


class SensitivityLevel(str, Enum):
    """Sensitivity levels for detected fields."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SemanticField:
    """Represents a semantically detected field."""
    field_name: str
    value: str
    start: int
    end: int
    sensitivity: SensitivityLevel
    confidence: float
    reason: str
    context: str
    field_type: str
    line_number: int = 0
    proximity_score: float = 0.0


@dataclass
class DocumentContext:
    """Document context information."""
    document_type: DocumentType
    confidence: float
    keywords: List[str]
    structure_hints: List[str]
    reasoning: str
    identity_signals: Dict[str, Any] = dataclass_field(default_factory=dict)


class DocumentTypeClassifier:
    """Classifies documents based on content, keywords, and structure."""
    
    # Document type signatures
    DOCUMENT_SIGNATURES = {
        DocumentType.INVOICE: {
            'keywords': [
                'invoice', 'invoice number', 'invoice #', 'inv#', 'bill to',
                'ship to', 'purchase order', 'po number', 'po#', 'terms',
                'due date', 'payment terms', 'subtotal', 'tax', 'total amount',
                'amount due', 'remit to', 'vendor', 'customer', 'qty', 'quantity',
                'unit price', 'line item', 'payment due'
            ],
            'patterns': [
                r'invoice\s*(?:number|#|no\.?)\s*:?\s*\w+',
                r'po\s*(?:number|#|no\.?)\s*:?\s*\w+',
                r'total\s*amount\s*:?\s*\$?[\d,]+\.?\d*',
                r'bill\s+to\s*:',
                r'ship\s+to\s*:'
            ],
            'weight': 1.0
        },
        DocumentType.RECEIPT: {
            'keywords': [
                'receipt', 'purchased', 'store', 'transaction', 'payment method',
                'visa', 'mastercard', 'cash', 'credit', 'debit', 'change',
                'tender', 'thank you for your purchase'
            ],
            'patterns': [
                r'receipt\s*(?:number|#|no\.?)',
                r'transaction\s*(?:id|number)',
                r'total\s*:?\s*\$?[\d,]+\.?\d*',
                r'change\s*:?\s*\$?[\d,]+\.?\d*'
            ],
            'weight': 0.9
        },
        DocumentType.BILL: {
            'keywords': [
                'bill', 'statement', 'account number', 'billing period',
                'previous balance', 'current charges', 'amount due',
                'payment due date', 'minimum payment', 'account summary'
            ],
            'patterns': [
                r'account\s*(?:number|#|no\.?)\s*:?\s*\w+',
                r'billing\s+period',
                r'amount\s+due\s*:?\s*\$?[\d,]+\.?\d*'
            ],
            'weight': 0.95
        },
        DocumentType.FINANCIAL: {
            'keywords': [
                'bank', 'account', 'balance', 'deposit', 'withdrawal',
                'transaction', 'credit', 'debit', 'statement', 'routing number',
                'account holder', 'financial', 'assets', 'liabilities',
                'equity', 'portfolio', 'investment'
            ],
            'patterns': [
                r'account\s*(?:number|#)\s*:?\s*\d+',
                r'routing\s*(?:number|#)\s*:?\s*\d+',
                r'balance\s*:?\s*\$?[\d,]+\.?\d*'
            ],
            'weight': 1.0
        },
        DocumentType.HR: {
            'keywords': [
                'employee', 'position', 'department', 'hire date', 'salary',
                'compensation', 'performance review', 'termination', 'resignation',
                'personnel', 'human resources', 'benefits', 'payroll',
                'employee id', 'supervisor', 'job title'
            ],
            'patterns': [
                r'employee\s*(?:id|number|#)\s*:?\s*\w+',
                r'salary\s*:?\s*\$?[\d,]+\.?\d*',
                r'hire\s+date\s*:?\s*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'
            ],
            'weight': 1.0
        },
        DocumentType.LEGAL: {
            'keywords': [
                'contract', 'agreement', 'party', 'parties', 'whereas',
                'jurisdiction', 'hereby', 'aforementioned', 'witness',
                'signature', 'notary', 'plaintiff', 'defendant', 'court',
                'legal', 'attorney', 'lawyer', 'counsel'
            ],
            'patterns': [
                r'party\s+(?:a|b|i|ii)',
                r'case\s*(?:number|#|no\.?)\s*:?\s*\w+',
                r'dated\s+this\s+\d+\w*\s+day'
            ],
            'weight': 1.0
        },
        DocumentType.PERSONAL: {
            'keywords': [
                'social security', 'ssn', 'date of birth', 'dob', 'address',
                'phone', 'email', 'driver license', 'passport', 'citizenship',
                'marital status', 'emergency contact', 'blood type'
            ],
            'patterns': [
                r'\d{3}-\d{2}-\d{4}',  # SSN
                r'date\s+of\s+birth',
                r'emergency\s+contact'
            ],
            'weight': 0.9
        },
        DocumentType.GOVERNMENT_ID: {
            'keywords': [
                'aadhaar', 'aadhar', 'uid', 'uidai', 'unique identification',
                'pan card', 'permanent account number', 'income tax',
                'voter id', 'election commission', 'epic', 'electoral',
                'driving license', 'driving licence', 'dl number', 'transport authority',
                'passport', 'passport number', 'ministry of external affairs',
                'republic of india', 'government of india', 'govt of',
                'national identity', 'national id', 'identity card',
                'issued by', 'authority', 'valid until', 'date of issue',
                'father name', 'mother name', 'guardian', 'nationality',
                'blood group', 'photo', 'signature', 'hologram',
                'document number', 'id number', 'identification number',
                'citizen', 'resident', 'bearer', 'holder'
            ],
            'patterns': [
                r'\d{4}\s*\d{4}\s*\d{4}(?:\s*\d{4})?',  # Aadhaar pattern (12 or 16 digits for VID)
                r'[A-Z]{5}\d{4}[A-Z]',  # PAN pattern
                r'[A-Z]{3}\d{7}',  # Voter ID pattern
                r'[A-Z]\d{14}',  # Passport pattern (example)
                r'[A-Z]{2}[-/]?\d{2,}',  # DL pattern
                r'(?:aadhaar|aadhar|uid)\s*(?:no\.?|number|#)\s*:?\s*\d',
                r'(?:pan|permanent account)\s*(?:no\.?|number|card)\s*:?',  # Improved PAN detection
                r'income\s+tax\s+department',  # PAN card authority
                r'(?:voter|epic)\s*(?:id|no\.?|number)\s*:?',
                r'(?:passport|dl|license)\s*(?:no\.?|number)\s*:?',
                r'date\s+of\s+(?:birth|issue)',
                r'valid\s+(?:upto|until|till)',
                r'(?:father|mother|guardian)\s*(?:name|s\.?)?\s*:',
                r'dob\s*:?\s*\d',  # DOB label
                r'(?:male|female)',  # Gender
                r'\b(?:name)\b'  # Name label (flexible)
            ],
            'weight': 1.0
        }
    }
    
    def classify(self, text: str) -> DocumentContext:
        """
        Classify document type based on content analysis.
        
        Args:
            text: Document text content
            
        Returns:
            DocumentContext with classification results
        """
        text_lower = text.lower()
        scores = {}
        matched_keywords = {}
        
        # Calculate scores for each document type
        for doc_type, signature in self.DOCUMENT_SIGNATURES.items():
            score = 0.0
            keywords_found = []
            
            # Check keywords
            for keyword in signature['keywords']:
                if keyword in text_lower:
                    score += 1.0
                    keywords_found.append(keyword)
            
            # Check patterns
            for pattern in signature['patterns']:
                if re.search(pattern, text_lower):
                    score += 2.0  # Patterns are stronger indicators
            
            # Apply weight
            weighted_score = score * signature['weight']
            scores[doc_type] = weighted_score
            matched_keywords[doc_type] = keywords_found
        
        # Determine best match
        if not scores or max(scores.values()) == 0:
            return DocumentContext(
                document_type=DocumentType.GENERIC,
                confidence=0.5,
                keywords=[],
                structure_hints=[],
                reasoning="No specific document type indicators found"
            )
        
        best_type = max(scores, key=scores.get)
        max_score = scores[best_type]
        
        # Special handling for government ID detection with identity signals
        identity_signals = self._detect_identity_signals(text, text_lower)
        if identity_signals['score'] >= 3 and best_type != DocumentType.GOVERNMENT_ID:
            # Override classification if strong identity signals present
            best_type = DocumentType.GOVERNMENT_ID
            max_score = identity_signals['score'] * 2
            matched_keywords[best_type] = identity_signals['indicators']
        
        # Additional boost for Aadhaar number pattern (12 or 16 digits)
        aadhaar_pattern = r'\d{4}\s+\d{4}\s+\d{4}(?:\s+\d{4})?'
        if re.search(aadhaar_pattern, text) and scores.get(DocumentType.GOVERNMENT_ID, 0) > 0:
            # If we have Aadhaar pattern + any other govt ID indicator, boost it
            if best_type != DocumentType.GOVERNMENT_ID:
                best_type = DocumentType.GOVERNMENT_ID
                max_score = max(max_score, 6.0)  # Minimum boost
                if not matched_keywords.get(DocumentType.GOVERNMENT_ID):
                    matched_keywords[DocumentType.GOVERNMENT_ID] = []
                matched_keywords[DocumentType.GOVERNMENT_ID].append('aadhaar number pattern')
            else:
                # Already classified as govt ID, boost the score
                max_score += 4.0
        
        # Calculate confidence (normalize by potential maximum)
        potential_max = len(self.DOCUMENT_SIGNATURES[best_type]['keywords']) + \
                       len(self.DOCUMENT_SIGNATURES[best_type]['patterns']) * 2
        confidence = min(max_score / potential_max, 1.0)
        
        # Boost confidence for government docs with strong identity signals
        if best_type == DocumentType.GOVERNMENT_ID and identity_signals['score'] >= 4:
            confidence = min(confidence * 1.2, 0.95)
        
        # Require minimum confidence threshold (lower for government IDs)
        min_threshold = 0.08 if best_type == DocumentType.GOVERNMENT_ID else 0.15
        if confidence < min_threshold:
            return DocumentContext(
                document_type=DocumentType.GENERIC,
                confidence=confidence,
                keywords=matched_keywords[best_type][:5],
                structure_hints=[],
                reasoning=f"Low confidence ({confidence:.2f}) for {best_type.value}",
                identity_signals=identity_signals
            )
        
        reasoning = f"Identified as {best_type.value} based on {len(matched_keywords[best_type])} matching keywords"
        if best_type == DocumentType.GOVERNMENT_ID:
            reasoning += f" and {identity_signals['score']} identity signals"
        
        logger.info(f"Classified document as {best_type.value} with confidence {confidence:.2f}")
        
        return DocumentContext(
            document_type=best_type,
            confidence=confidence,
            keywords=matched_keywords[best_type][:10],
            structure_hints=self._extract_structure_hints(text, best_type),
            reasoning=reasoning,
            identity_signals=identity_signals
        )
    
    def _extract_structure_hints(self, text: str, doc_type: DocumentType) -> List[str]:
        """Extract structural hints from document."""
        hints = []
        
        # Check for table-like structures
        if re.search(r'\n.*\|.*\|.*\n', text):
            hints.append("table_structure")
        
        # Check for labeled fields (key: value patterns)
        if re.search(r'\w+\s*:\s*\w+', text):
            hints.append("labeled_fields")
        
        # Check for numbered lists
        if re.search(r'\n\s*\d+[\.)]\s+', text):
            hints.append("numbered_list")
        
        return hints
    
    def _detect_identity_signals(self, text: str, text_lower: str) -> Dict[str, Any]:
        """Detect identity signals for government document classification.
        
        Returns dict with:
            - score: Number of signals detected
            - indicators: List of detected indicators
            - has_qr: Whether QR code detected
            - has_photo: Whether photo indicator detected
            - layout_score: Formal layout score
        """
        signals = {
            'score': 0,
            'indicators': [],
            'has_qr': False,
            'has_photo': False,
            'layout_score': 0
        }
        
        # Signal 1: Personal attributes (Name + DOB + Gender)
        has_name = bool(re.search(r'(?:name|naam|\u0928\u093e\u092e)\s*:', text_lower))
        has_dob = bool(re.search(r'(?:dob|date.*birth|birth.*date|\u091c\u0928\u094d\u092e)', text_lower))
        has_gender = bool(re.search(r'(?:gender|sex|male|female|\u0932\u093f\u0902\u0917|\u092a\u0941\u0930\u0941\u0937|\u092e\u0939\u093f\u0932\u093e)', text_lower))
        
        if has_name and (has_dob or has_gender):
            signals['score'] += 2
            signals['indicators'].append('personal_attributes')
        
        # Signal 2: High-confidence ID number patterns
        id_patterns = [
            (r'\d{4}[\s-]\d{4}[\s-]\d{4}', 'aadhaar_pattern'),  # Aadhaar
            (r'[A-Z]{5}\d{4}[A-Z]', 'pan_pattern'),  # PAN
            (r'[A-Z]{2,3}\d{7,14}', 'generic_id_pattern'),  # Generic govt ID
            (r'\d{8,12}', 'numeric_id_pattern')  # Numeric ID
        ]
        
        for pattern, name in id_patterns:
            if re.search(pattern, text):
                signals['score'] += 1
                signals['indicators'].append(name)
                break  # Count only once
        
        # Signal 3: Official headers/emblems
        official_markers = [
            'government of', 'govt of', 'republic of', 'ministry',
            'department of', 'authority', 'commission', 'issued by',
            '\u0938\u0930\u0915\u093e\u0930',  # sarkar (government)
            '\u092d\u093e\u0930\u0924 \u0938\u0930\u0915\u093e\u0930'  # bharat sarkar
        ]
        for marker in official_markers:
            if marker in text_lower:
                signals['score'] += 1
                signals['indicators'].append('official_header')
                break
        
        # Signal 4: QR code presence
        if re.search(r'(?:qr|<qr>|\[qr|barcode)', text_lower):
            signals['score'] += 1
            signals['indicators'].append('qr_code')
            signals['has_qr'] = True
        
        # Signal 5: Photo/signature indicators
        if re.search(r'(?:photo|photograph|signature|holder.*photo)', text_lower):
            signals['score'] += 1
            signals['indicators'].append('photo_signature')
            signals['has_photo'] = True
        
        # Signal 6: Formal ID layout (multiple labeled fields)
        labeled_fields = len(re.findall(r'\w+\s*:', text))
        if labeled_fields >= 5:
            signals['layout_score'] = min(labeled_fields / 10, 1.0)
            signals['score'] += 1
            signals['indicators'].append('formal_layout')
        
        # Signal 7: Validity period
        if re.search(r'(?:valid|expiry|expires|issue.*date)', text_lower):
            signals['score'] += 1
            signals['indicators'].append('validity_period')
        
        return signals


class SemanticFieldDetector:
    """Detects sensitive fields using semantic understanding and NER."""
    
    # Financial field patterns
    FINANCIAL_PATTERNS = {
        'invoice_number': {
            'patterns': [
                r'invoice\s*(?:number|no\.?|#)\s*:?\s*([A-Z0-9\-]+)',
                r'inv\s*#?\s*:?\s*([A-Z0-9\-]+)',
            ],
            'sensitivity': SensitivityLevel.HIGH,
            'reason': 'Unique financial transaction identifier'
        },
        'po_number': {
            'patterns': [
                r'(?:purchase\s+order|po)\s*(?:number|no\.?|#)\s*:?\s*([A-Z0-9\-]+)',
                r'po\s*#?\s*:?\s*([A-Z0-9\-]+)',
            ],
            'sensitivity': SensitivityLevel.HIGH,
            'reason': 'Business confidential procurement reference'
        },
        'account_number': {
            'patterns': [
                r'account\s*(?:number|no\.?|#)\s*:?\s*([A-Z0-9\-]+)',
                r'acct\s*#?\s*:?\s*([A-Z0-9\-]+)',
            ],
            'sensitivity': SensitivityLevel.CRITICAL,
            'reason': 'Financial account identifier'
        },
        'routing_number': {
            'patterns': [
                r'routing\s*(?:number|no\.?|#)\s*:?\s*(\d{9})',
            ],
            'sensitivity': SensitivityLevel.CRITICAL,
            'reason': 'Bank routing information'
        },
        'payment_reference': {
            'patterns': [
                r'(?:payment|transaction|reference)\s*(?:number|no\.?|#|id)\s*:?\s*([A-Z0-9\-]+)',
            ],
            'sensitivity': SensitivityLevel.HIGH,
            'reason': 'Payment transaction identifier'
        },
        'amount': {
            'patterns': [
                r'(?:total|amount|balance|subtotal|sum)\s*(?:due|amount)?\s*:?\s*\$?\s*([\d,]+\.?\d*)',
                r'\$\s*([\d,]+\.?\d{2})\s*(?:total|due|amount)?',
            ],
            'sensitivity': SensitivityLevel.MEDIUM,
            'reason': 'Financial transaction amount'
        },
        'tax_id': {
            'patterns': [
                r'(?:tax|vat|ein)\s*(?:id|number|#)\s*:?\s*([A-Z0-9\-]+)',
            ],
            'sensitivity': SensitivityLevel.HIGH,
            'reason': 'Tax identification number'
        },
    }
    
    # Personal information patterns
    PERSONAL_PATTERNS = {
        'address': {
            'patterns': [
                r'(?:address|location|residence)\s*:?\s*([^\n]{20,100})',
                r'\d+\s+[A-Za-z\s]+(?:street|st|avenue|ave|road|rd|drive|dr|lane|ln|boulevard|blvd)[^\n]{0,50}',
            ],
            'sensitivity': SensitivityLevel.HIGH,
            'reason': 'Personal identifiable location information'
        },
        'employee_id': {
            'patterns': [
                r'employee\s*(?:id|number|#)\s*:?\s*([A-Z0-9\-]+)',
                r'emp\s*#?\s*:?\s*([A-Z0-9\-]+)',
            ],
            'sensitivity': SensitivityLevel.HIGH,
            'reason': 'Employee identification number'
        },
        'date_of_birth': {
            'patterns': [
                r'(?:date\s+of\s+birth|dob|birth\s+date)\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            ],
            'sensitivity': SensitivityLevel.CRITICAL,
            'reason': 'Personal date of birth'
        },
        'salary': {
            'patterns': [
                r'(?:salary|compensation|wage)\s*:?\s*\$?\s*([\d,]+\.?\d*)',
            ],
            'sensitivity': SensitivityLevel.CRITICAL,
            'reason': 'Confidential compensation information'
        },
    }
    
    # Business confidential patterns
    BUSINESS_PATTERNS = {
        'customer_id': {
            'patterns': [
                r'customer\s*(?:id|number|#)\s*:?\s*([A-Z0-9\-]+)',
            ],
            'sensitivity': SensitivityLevel.MEDIUM,
            'reason': 'Customer identification reference'
        },
        'vendor_id': {
            'patterns': [
                r'vendor\s*(?:id|number|#)\s*:?\s*([A-Z0-9\-]+)',
            ],
            'sensitivity': SensitivityLevel.MEDIUM,
            'reason': 'Vendor identification reference'
        },
    }
    
    # Government ID patterns (CRITICAL SENSITIVITY) - UNIVERSAL FORMAT SUPPORT
    GOVERNMENT_ID_PATTERNS = {
        'aadhaar_number': {
            'patterns': [
                r'(?:aadhaar|aadhar|uid|आधार)\s*(?:no\.?|number|#|नंबर)?\s*:?\s*(\d{4}[\s-]?\d{4}[\s-]?\d{4})',
                r'(?:aadhaar|aadhar|uid)\s*(?:no\.?|number|#)?\s*:?\s*(\d{12})',
                r'\b(\d{4}[\s-]\d{4}[\s-]\d{4})\b',  # Standalone pattern
            ],
            'sensitivity': SensitivityLevel.CRITICAL,
            'reason': 'Government-issued unique identification number (Aadhaar)',
            'validation': lambda v: len(re.sub(r'[\s-]', '', v)) == 12
        },
        'pan_number': {
            'patterns': [
                r'(?:pan|permanent\s+account)\s*(?:no\.?|number|#)?\s*:?\s*([A-Z]{5}\d{4}[A-Z])',
                r'\b([A-Z]{5}\d{4}[A-Z])\b',  # Standalone PAN pattern
            ],
            'sensitivity': SensitivityLevel.CRITICAL,
            'reason': 'Government-issued tax identification number (PAN)',
            'validation': lambda v: len(v) == 10 and v[0:5].isalpha() and v[5:9].isdigit() and v[9].isalpha()
        },
        'voter_id': {
            'patterns': [
                r'(?:voter|epic|electoral)\s*(?:id|no\.?|number|#)?\s*:?\s*([A-Z]{3}\d{7})',
                r'(?:voter|epic|electoral)\s*(?:id|no\.?|number|#)?\s*:?\s*([A-Z0-9]{10,})',
            ],
            'sensitivity': SensitivityLevel.CRITICAL,
            'reason': 'Government-issued voter identification number'
        },
        'passport_number': {
            'patterns': [
                r'passport\s*(?:no\.?|number|#)?\s*:?\s*([A-Z]\d{7,8})',
                r'passport\s*(?:no\.?|number|#)?\s*:?\s*([A-Z]{1,2}\d{6,8})',
            ],
            'sensitivity': SensitivityLevel.CRITICAL,
            'reason': 'Government-issued passport number'
        },
        'driving_license': {
            'patterns': [
                r'(?:driving\s+licen[cs]e|dl)\s*(?:no\.?|number|#)?\s*:?\s*([A-Z]{2}[-/]?\d{2}[-/]?\d{4,})',
                r'(?:driving\s+licen[cs]e|dl)\s*(?:no\.?|number|#)?\s*:?\s*([A-Z0-9]{8,16})',
            ],
            'sensitivity': SensitivityLevel.CRITICAL,
            'reason': 'Government-issued driving license number'
        },
        'national_id': {
            'patterns': [
                r'(?:national\s+id|identity\s+card|id\s+card)\s*(?:no\.?|number|#)?\s*:?\s*([A-Z0-9\-]{8,20})',
                r'(?:citizen|identification)\s*(?:no\.?|number|#)?\s*:?\s*([A-Z0-9\-]{8,20})',
            ],
            'sensitivity': SensitivityLevel.CRITICAL,
            'reason': 'Government-issued national identity number'
        },
        'govt_document_number': {
            'patterns': [
                r'document\s*(?:no\.?|number|#)\s*:?\s*([A-Z0-9\-]{8,20})',
                r'(?:id|identification)\s*(?:no\.?|number|#)\s*:?\s*([A-Z0-9\-]{8,20})',
            ],
            'sensitivity': SensitivityLevel.CRITICAL,
            'reason': 'Government document identification number'
        },
        'govt_dob': {
            'patterns': [
                r'(?:date\s+of\s+birth|dob|birth\s+date|जन्म.*तिथि)\s*:?\s*(\d{1,2}[/\-.\s]\d{1,2}[/\-.\s]\d{2,4})',
                r'\b(\d{2}[/\.]\d{2}[/\.]\d{4})\b',  # DD/MM/YYYY or DD.MM.YYYY
                r'\b(\d{4}[-/]\d{2}[-/]\d{2})\b',  # YYYY-MM-DD
                r'\b(\d{1,2}[\s-](?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s-]\d{2,4})\b',  # DD Mon YYYY
            ],
            'sensitivity': SensitivityLevel.CRITICAL,
            'reason': 'Date of birth on government-issued document',
            'context_keywords': ['birth', 'dob', 'born', 'जन्म']
        },
        'govt_gender': {
            'patterns': [
                r'(?:gender|sex|लिंग)\s*:?\s*(male|female|other|m|f|o|transgender|पुरुष|महिला|अन्य|trans)',
                r'\b(male|female|m/f|m\s*/\s*f|पुरुष|महिला)\b',  # Standalone gender
            ],
            'sensitivity': SensitivityLevel.HIGH,
            'reason': 'Gender information on government-issued document',
            'context_keywords': ['gender', 'sex', 'लिंग']
        },
        'father_mother_name': {
            'patterns': [
                r'(?:father|mother|guardian)\s*(?:name|s\.?)?\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            ],
            'sensitivity': SensitivityLevel.HIGH,
            'reason': 'Parent/Guardian name on government-issued document'
        },
        'govt_address': {
            'patterns': [
                r'address\s*:?\s*([^\n]{20,150})',
                r'residence\s*:?\s*([^\n]{20,150})',
            ],
            'sensitivity': SensitivityLevel.HIGH,
            'reason': 'Residential address on government-issued document'
        },
        'issue_date': {
            'patterns': [
                r'(?:date\s+of\s+issue|issued\s+on|issue\s+date)\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            ],
            'sensitivity': SensitivityLevel.MEDIUM,
            'reason': 'Document issue date'
        },
        'valid_until': {
            'patterns': [
                r'(?:valid\s+(?:upto|until|till)|expiry\s+date|expires)\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            ],
            'sensitivity': SensitivityLevel.MEDIUM,
            'reason': 'Document validity period'
        },
        'qr_code_ref': {
            'patterns': [
                r'qr\s*(?:code|ref|reference)\s*:?\s*([A-Z0-9]+)',
                r'reference\s*(?:code|number|#)\s*:?\s*([A-Z0-9\-]{8,})',
                r'<QR>',  # QR code placeholder in OCR
                r'\[QR\s+CODE\]',
            ],
            'sensitivity': SensitivityLevel.HIGH,
            'reason': 'QR code or reference number on government document'
        },
        # Universal ID number detection (no label required)
        'universal_id': {
            'patterns': [
                r'\b([A-Z]{2,3}\d{6,14})\b',  # Generic alphanumeric ID
                r'\b(\d{8,16})\b',  # Numeric ID (8-16 digits)
            ],
            'sensitivity': SensitivityLevel.HIGH,
            'reason': 'Potential government-issued identification number',
            'requires_proximity': True  # Must be near identity markers
        },
    }
    
    def __init__(self):
        """Initialize detector with AI models."""
        self.spacy_nlp = None
        self.models_loaded = False
    
    def load_models(self):
        """Load NLP models for entity recognition."""
        if self.models_loaded:
            return
        
        try:
            import spacy
            try:
                self.spacy_nlp = spacy.load("en_core_web_sm")
            except OSError:
                logger.warning("spaCy model not available, using pattern-based detection only")
                self.spacy_nlp = None
            
            if self.spacy_nlp:
                logger.info("Loaded spaCy model for NER")
                self.models_loaded = True
        except ImportError:
            logger.warning("spaCy not available, using pattern-based detection only")
    
    def detect_fields(
        self, 
        text: str, 
        document_context: DocumentContext
    ) -> List[SemanticField]:
        """
        Detect sensitive fields based on document context.
        
        Args:
            text: Document text
            document_context: Classified document context
            
        Returns:
            List of detected semantic fields
        """
        fields = []
        
        # Split text into lines for proximity analysis
        lines = text.split('\n')
        
        # Pattern-based detection (always available)
        fields.extend(self._detect_with_patterns(text, document_context, lines))
        
        # NER-based detection (if models available)
        if self.spacy_nlp:
            fields.extend(self._detect_with_ner(text, document_context, lines))
        
        # Validate proximity for fields requiring context
        if document_context.document_type == DocumentType.GOVERNMENT_ID:
            fields = self._validate_field_proximity(fields, text, lines, document_context)
        
        # Deduplicate overlapping fields
        fields = self._deduplicate_fields(fields)
        
        logger.info(f"Detected {len(fields)} semantic fields")
        return fields
    
    def _detect_with_patterns(
        self, 
        text: str, 
        document_context: DocumentContext,
        lines: List[str]
    ) -> List[SemanticField]:
        """Detect fields using regex patterns with confidence scoring."""
        fields = []
        
        # Select pattern sets based on document type
        pattern_sets = []
        
        if document_context.document_type in [DocumentType.INVOICE, DocumentType.BILL, 
                                               DocumentType.RECEIPT, DocumentType.FINANCIAL]:
            pattern_sets.append(self.FINANCIAL_PATTERNS)
            pattern_sets.append(self.BUSINESS_PATTERNS)
        
        if document_context.document_type in [DocumentType.HR, DocumentType.PERSONAL]:
            pattern_sets.append(self.PERSONAL_PATTERNS)
        
        # GOVERNMENT ID DOCUMENTS - Use government patterns with strict masking
        if document_context.document_type == DocumentType.GOVERNMENT_ID:
            pattern_sets.append(self.GOVERNMENT_ID_PATTERNS)
            pattern_sets.append(self.PERSONAL_PATTERNS)  # Also check personal patterns
        
        # If generic or low confidence, use all patterns
        if document_context.document_type == DocumentType.GENERIC or \
           document_context.confidence < 0.5:
            pattern_sets = [self.FINANCIAL_PATTERNS, self.PERSONAL_PATTERNS, 
                           self.BUSINESS_PATTERNS, self.GOVERNMENT_ID_PATTERNS]
        
        # Apply patterns
        for pattern_set in pattern_sets:
            for field_name, field_config in pattern_set.items():
                for pattern in field_config['patterns']:
                    for match in re.finditer(pattern, text, re.IGNORECASE):
                        # Extract the captured value
                        value = match.group(1) if match.groups() else match.group()
                        
                        # Calculate base confidence
                        base_confidence = 0.9
                        
                        # Check if pattern has validation function
                        if 'validation' in field_config:
                            try:
                                if not field_config['validation'](value):
                                    base_confidence = 0.7  # Lower confidence if validation fails
                            except:
                                pass
                        
                        # Check context keywords if specified
                        context_start = max(0, match.start() - 50)
                        context_end = min(len(text), match.end() + 50)
                        context = text[context_start:context_end]
                        
                        if 'context_keywords' in field_config:
                            context_lower = context.lower()
                            has_context = any(kw in context_lower for kw in field_config['context_keywords'])
                            if has_context:
                                base_confidence = min(base_confidence + 0.05, 0.98)
                            elif field_config.get('requires_proximity', False):
                                # Skip if proximity required but no context
                                continue
                        
                        # Calculate line number
                        line_num = text[:match.start()].count('\n')
                        
                        fields.append(SemanticField(
                            field_name=field_name,
                            value=value,
                            start=match.start(),
                            end=match.end(),
                            sensitivity=field_config['sensitivity'],
                            confidence=base_confidence,
                            reason=field_config['reason'],
                            context=context,
                            field_type='pattern',
                            line_number=line_num
                        ))
        
        return fields
    
    def _detect_with_ner(
        self, 
        text: str, 
        document_context: DocumentContext,
        lines: List[str]
    ) -> List[SemanticField]:
        """Detect fields using Named Entity Recognition with confidence scoring."""
        if not self.spacy_nlp:
            return []
        
        fields = []
        doc = self.spacy_nlp(text[:10000])  # Limit text length
        
        for ent in doc.ents:
            sensitivity, reason = self._classify_entity(ent, document_context)
            
            if sensitivity:
                context_start = max(0, ent.start_char - 50)
                context_end = min(len(text), ent.end_char + 50)
                context = text[context_start:context_end]
                
                # Calculate line number
                line_num = text[:ent.start_char].count('\n')
                
                fields.append(SemanticField(
                    field_name=f"{ent.label_.lower()}_entity",
                    value=ent.text,
                    start=ent.start_char,
                    end=ent.end_char,
                    sensitivity=sensitivity,
                    confidence=0.85,
                    reason=reason,
                    context=context,
                    field_type='ner',
                    line_number=line_num
                ))
        
        return fields
    
    def _classify_entity(
        self, 
        entity, 
        document_context: DocumentContext
    ) -> Tuple[Optional[SensitivityLevel], str]:
        """Classify entity sensitivity based on type and document context."""
        label = entity.label_
        
        # Person names
        if label == "PERSON":
            # GOVERNMENT ID - Person names are CRITICAL
            if document_context.document_type == DocumentType.GOVERNMENT_ID:
                return SensitivityLevel.CRITICAL, "Identity holder name on government-issued document"
            elif document_context.document_type in [DocumentType.HR, DocumentType.LEGAL]:
                return SensitivityLevel.HIGH, "Personal identification in sensitive document"
            elif document_context.document_type in [DocumentType.INVOICE, DocumentType.BILL]:
                return SensitivityLevel.MEDIUM, "Customer/vendor name on business document"
            return SensitivityLevel.LOW, "Person name mentioned"
        
        # Organizations
        elif label == "ORG":
            if document_context.document_type in [DocumentType.LEGAL, DocumentType.FINANCIAL]:
                return SensitivityLevel.MEDIUM, "Business entity in confidential document"
            return SensitivityLevel.LOW, "Organization name"
        
        # Locations (addresses)
        elif label == "GPE" or label == "LOC":
            # GOVERNMENT ID - Addresses are CRITICAL
            if document_context.document_type == DocumentType.GOVERNMENT_ID:
                return SensitivityLevel.CRITICAL, "Residential address on government-issued document"
            elif document_context.document_type in [DocumentType.HR, DocumentType.PERSONAL]:
                return SensitivityLevel.HIGH, "Personal address information"
            elif document_context.document_type in [DocumentType.INVOICE, DocumentType.BILL]:
                return SensitivityLevel.MEDIUM, "Billing/shipping address"
            return SensitivityLevel.LOW, "Location mention"
        
        # Money amounts
        elif label == "MONEY":
            if document_context.document_type in [DocumentType.FINANCIAL, DocumentType.HR]:
                return SensitivityLevel.HIGH, "Financial amount in sensitive context"
            elif document_context.document_type in [DocumentType.INVOICE, DocumentType.BILL]:
                return SensitivityLevel.MEDIUM, "Transaction amount"
            return SensitivityLevel.LOW, "Money amount"
        
        # Dates
        elif label == "DATE":
            # GOVERNMENT ID - All dates are potentially sensitive
            if document_context.document_type == DocumentType.GOVERNMENT_ID:
                return SensitivityLevel.CRITICAL, "Date on government-issued document"
            # Dates are generally low sensitivity unless in specific contexts
            elif document_context.document_type == DocumentType.HR and \
               any(keyword in entity.text.lower() for keyword in ['birth', 'dob']):
                return SensitivityLevel.CRITICAL, "Date of birth"
            return None, ""  # Don't mask regular dates
        
        return None, ""
    
    def _deduplicate_fields(self, fields: List[SemanticField]) -> List[SemanticField]:
        """Remove overlapping fields, keeping higher sensitivity ones."""
        if not fields:
            return []
        
        # Sort by start position, then by sensitivity priority
        sensitivity_order = {
            SensitivityLevel.CRITICAL: 0,
            SensitivityLevel.HIGH: 1,
            SensitivityLevel.MEDIUM: 2,
            SensitivityLevel.LOW: 3
        }
        
        sorted_fields = sorted(
            fields, 
            key=lambda x: (x.start, sensitivity_order[x.sensitivity])
        )
        
        result = []
        last_end = -1
        
        for field in sorted_fields:
            # No overlap with previous field
            if field.start >= last_end:
                result.append(field)
                last_end = field.end
            # Overlaps but has higher sensitivity - replace
            elif result and sensitivity_order[field.sensitivity] < \
                 sensitivity_order[result[-1].sensitivity]:
                result[-1] = field
                last_end = field.end
        
        return result
    
    def _validate_field_proximity(
        self, 
        fields: List[SemanticField], 
        text: str,
        lines: List[str],
        document_context: DocumentContext
    ) -> List[SemanticField]:
        """Validate that detected fields are contextually related using proximity analysis.
        
        For government IDs, ensure ID numbers, DOB, gender, address are near each other.
        """
        if not fields or document_context.document_type != DocumentType.GOVERNMENT_ID:
            return fields
        
        # Categorize fields by type
        identity_markers = []  # Name, ID number
        personal_attrs = []  # DOB, gender, address
        
        for field in fields:
            if field.field_name in ['aadhaar_number', 'pan_number', 'passport_number', 
                                    'driving_license', 'voter_id', 'national_id', 'universal_id',
                                    'person_entity']:
                identity_markers.append(field)
            elif field.field_name in ['govt_dob', 'govt_gender', 'govt_address', 
                                      'father_mother_name', 'date_of_birth']:
                personal_attrs.append(field)
        
        # If no identity markers, reduce confidence of personal attrs
        if not identity_markers:
            for field in personal_attrs:
                field.confidence *= 0.7
                field.reason += " (isolated - no ID number context)"
            return fields
        
        # Calculate proximity scores for personal attributes
        validated_fields = []
        for field in fields:
            if field in personal_attrs:
                # Find closest identity marker
                min_line_distance = float('inf')
                for marker in identity_markers:
                    line_distance = abs(field.line_number - marker.line_number)
                    min_line_distance = min(min_line_distance, line_distance)
                
                # Update proximity score
                if min_line_distance <= 2:
                    # Very close - high proximity
                    field.proximity_score = 1.0
                    field.confidence = min(field.confidence + 0.05, 0.98)
                elif min_line_distance <= 5:
                    # Moderate proximity
                    field.proximity_score = 0.7
                elif min_line_distance <= 10:
                    # Distant but possible
                    field.proximity_score = 0.4
                    field.confidence *= 0.9
                else:
                    # Too far - likely false positive
                    field.proximity_score = 0.2
                    field.confidence *= 0.6
                
                validated_fields.append(field)
            else:
                # Not a personal attribute - keep as is
                validated_fields.append(field)
        
        return validated_fields if validated_fields else fields


class SensitivityScorer:
    """Scores field sensitivity with confidence levels."""
    
    @staticmethod
    def score_field(
        field: SemanticField, 
        document_context: DocumentContext
    ) -> Tuple[SensitivityLevel, float]:
        """
        Calculate final sensitivity score for a field.
        
        Args:
            field: Semantic field to score
            document_context: Document context
            
        Returns:
            Tuple of (final_sensitivity_level, confidence_score)
        """
        base_sensitivity = field.sensitivity
        confidence = field.confidence
        
        # Adjust based on document type and confidence
        if document_context.confidence > 0.7:
            # High confidence in document type - trust field sensitivity
            return base_sensitivity, min(confidence * 1.1, 1.0)
        else:
            # Lower confidence - be more conservative
            if base_sensitivity == SensitivityLevel.CRITICAL:
                return SensitivityLevel.HIGH, confidence * 0.9
            return base_sensitivity, confidence * 0.9
    
    @staticmethod
    def should_mask(
        field: SemanticField,
        document_context: DocumentContext,
        min_sensitivity: SensitivityLevel = SensitivityLevel.MEDIUM,
        confidence_threshold: float = 0.85
    ) -> bool:
        """
        Determine if a field should be masked based on sensitivity and confidence.
        
        Args:
            field: Semantic field
            document_context: Document context
            min_sensitivity: Minimum sensitivity level to mask
            confidence_threshold: Minimum confidence required to mask (default 0.85)
            
        Returns:
            True if field should be masked
        """
        # Check confidence threshold first
        if field.confidence < confidence_threshold:
            # Don't mask if confidence too low
            logger.debug(f"Skipping mask for {field.field_name}: confidence {field.confidence:.2f} < {confidence_threshold}")
            return False
        
        sensitivity_order = {
            SensitivityLevel.LOW: 0,
            SensitivityLevel.MEDIUM: 1,
            SensitivityLevel.HIGH: 2,
            SensitivityLevel.CRITICAL: 3
        }
        
        # For CRITICAL sensitivity, lower threshold to 0.7 (always mask high-risk data)
        if field.sensitivity == SensitivityLevel.CRITICAL:
            confidence_threshold = 0.7
            if field.confidence < confidence_threshold:
                return False
        
        return sensitivity_order[field.sensitivity] >= sensitivity_order[min_sensitivity]


class ContextAwareMasker:
    """Applies intelligent masking while preserving layout and readability."""
    
    @staticmethod
    def mask_document(
        text: str,
        fields: List[SemanticField],
        document_context: DocumentContext,
        preserve_structure: bool = True
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Apply context-aware masking to document.
        
        Args:
            text: Original document text
            fields: Detected semantic fields
            document_context: Document context
            preserve_structure: Whether to preserve formatting
            
        Returns:
            Tuple of (masked_text, masking_explanations)
        """
        if not fields:
            return text, []
        
        # Sort fields by position (reverse order for replacement)
        sorted_fields = sorted(fields, key=lambda x: x.start, reverse=True)
        
        masked_text = text
        explanations = []
        masked_count = 0
        
        for field in sorted_fields:
            # Determine if this field should be masked
            if not SensitivityScorer.should_mask(field, document_context):
                continue
            
            # Generate appropriate mask based on field type
            mask = ContextAwareMasker._generate_mask(field, preserve_structure)
            
            # Apply masking
            masked_text = (
                masked_text[:field.start] +
                mask +
                masked_text[field.end:]
            )
            
            # Record explanation
            explanations.append({
                'field': field.field_name,
                'original_value': field.value[:50],  # Limit for privacy
                'masked_value': mask,
                'reason': field.reason,
                'sensitivity': field.sensitivity.value,
                'confidence': field.confidence,
                'position': f"{field.start}-{field.end}"
            })
            
            masked_count += 1
        
        logger.info(f"Masked {masked_count} fields in {document_context.document_type.value} document")
        
        return masked_text, explanations
    
    @staticmethod
    def _generate_mask(field: SemanticField, preserve_structure: bool) -> str:
        """Generate appropriate mask for a field."""
        # Map field names to mask labels
        mask_labels = {
            'invoice_number': 'INVOICE-ID',
            'po_number': 'PO',
            'account_number': 'ACCOUNT',
            'routing_number': 'ROUTING',
            'payment_reference': 'PAYMENT-REF',
            'amount': 'AMOUNT',
            'tax_id': 'TAX-ID',
            'address': 'ADDRESS',
            'employee_id': 'EMP-ID',
            'date_of_birth': 'DOB',
            'salary': 'SALARY',
            'customer_id': 'CUSTOMER-ID',
            'vendor_id': 'VENDOR-ID',
            'person_entity': 'NAME',
            'org_entity': 'ORG',
            'gpe_entity': 'LOCATION',
            'money_entity': 'AMOUNT',
            # Government ID specific masks
            'aadhaar_number': 'GOVT-ID',
            'pan_number': 'GOVT-ID',
            'voter_id': 'GOVT-ID',
            'passport_number': 'GOVT-ID',
            'driving_license': 'GOVT-ID',
            'national_id': 'GOVT-ID',
            'govt_document_number': 'GOVT-ID',
            'govt_dob': 'DOB',
            'govt_gender': 'GENDER',
            'father_mother_name': 'PARENT-NAME',
            'govt_address': 'ADDRESS',
            'issue_date': 'ISSUE-DATE',
            'valid_until': 'EXPIRY-DATE',
            'qr_code_ref': 'QR-REF',
        }
        
        label = mask_labels.get(field.field_name, field.field_name.upper())
        
        if preserve_structure:
            # Preserve approximate length for layout
            if len(field.value) > 20:
                return f"[MASKED-{label}]"
            else:
                # Short mask for short values
                return f"[{label}]"
        else:
            return f"[MASKED-{label}]"


class ContextAwareEngine:
    """Main context-aware sensitive data intelligence engine."""
    
    def __init__(self):
        """Initialize the engine components."""
        self.document_classifier = DocumentTypeClassifier()
        self.field_detector = SemanticFieldDetector()
        self.sensitivity_scorer = SensitivityScorer()
        self.masker = ContextAwareMasker()
        self.initialized = False
    
    def initialize(self):
        """Initialize AI models."""
        if not self.initialized:
            self.field_detector.load_models()
            self.initialized = True
            logger.info("Context-aware engine initialized")
    
    def process_document(
        self,
        text: str,
        apply_masking: bool = True,
        min_sensitivity: SensitivityLevel = SensitivityLevel.MEDIUM,
        preserve_structure: bool = True
    ) -> Dict[str, Any]:
        """
        Process document with context-aware intelligence.
        
        Args:
            text: Document text content
            apply_masking: Whether to apply masking
            min_sensitivity: Minimum sensitivity level to mask
            preserve_structure: Whether to preserve document structure
            
        Returns:
            Dictionary containing:
                - document_context: DocumentContext
                - detected_fields: List[SemanticField]
                - masked_text: str (if apply_masking=True)
                - explanations: List[Dict] (masking reasons)
                - summary: Dict (statistics)
        """
        if not self.initialized:
            self.initialize()
        
        # Step 1: Classify document type
        document_context = self.document_classifier.classify(text)
        
        # Step 2: Detect semantic fields
        detected_fields = self.field_detector.detect_fields(text, document_context)
        
        # Step 3: Score sensitivity
        scored_fields = []
        for field in detected_fields:
            sensitivity, confidence = self.sensitivity_scorer.score_field(
                field, document_context
            )
            # Update field with scored values
            field.sensitivity = sensitivity
            field.confidence = confidence
            scored_fields.append(field)
        
        # Step 4: Apply masking if requested
        masked_text = None
        explanations = []
        
        if apply_masking:
            # Filter fields to mask based on minimum sensitivity
            fields_to_mask = [
                f for f in scored_fields 
                if self.sensitivity_scorer.should_mask(f, document_context, min_sensitivity)
            ]
            
            masked_text, explanations = self.masker.mask_document(
                text, fields_to_mask, document_context, preserve_structure
            )
        
        # Step 5: Generate summary
        sensitivity_counts = Counter(f.sensitivity.value for f in scored_fields)
        field_type_counts = Counter(f.field_name for f in scored_fields)
        
        summary = {
            'document_type': document_context.document_type.value,
            'document_confidence': document_context.confidence,
            'total_fields_detected': len(scored_fields),
            'fields_masked': len(explanations),
            'sensitivity_distribution': dict(sensitivity_counts),
            'field_types': dict(field_type_counts),
            'keywords_matched': document_context.keywords[:5]
        }
        
        result = {
            'document_context': {
                'type': document_context.document_type.value,
                'confidence': document_context.confidence,
                'keywords': document_context.keywords,
                'reasoning': document_context.reasoning
            },
            'detected_fields': [
                {
                    'name': f.field_name,
                    'value_preview': f.value[:30] + '...' if len(f.value) > 30 else f.value,
                    'sensitivity': f.sensitivity.value,
                    'confidence': f.confidence,
                    'reason': f.reason
                }
                for f in scored_fields
            ],
            'masked_text': masked_text,
            'explanations': explanations,
            'summary': summary
        }
        
        logger.info(f"Processed document: {summary}")
        
        return result


# Global engine instance
context_engine = ContextAwareEngine()
