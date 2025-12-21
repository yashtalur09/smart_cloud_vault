"""Sensitive data detection engine using regex and AI."""
import re
from typing import List, Dict, Any, Set
import logging
from models.schemas import DetectionResult, DetectionType

logger = logging.getLogger(__name__)


class RegexDetector:
    """Rule-based sensitive data detection using regex patterns."""
    
    def __init__(self):
        # Email pattern
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        
        # Phone patterns (various formats)
        self.phone_patterns = [
            re.compile(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'),  # US format
            re.compile(r'\b\(\d{3}\)\s?\d{3}[-.\s]?\d{4}\b'),  # (123) 456-7890
            re.compile(r'\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b'),  # International
        ]
        
        # Credit card patterns (Luhn algorithm not implemented, basic pattern)
        self.credit_card_patterns = [
            re.compile(r'\b(?:4[0-9]{12}(?:[0-9]{3})?)\b'),  # Visa
            re.compile(r'\b(?:5[1-5][0-9]{14})\b'),  # MasterCard
            re.compile(r'\b(?:3[47][0-9]{13})\b'),  # Amex
            re.compile(r'\b(?:6(?:011|5[0-9]{2})[0-9]{12})\b'),  # Discover
            re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),  # Generic 16-digit
        ]
        
        # SSN pattern
        self.ssn_pattern = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
        
        # National ID patterns (generic)
        self.national_id_patterns = [
            re.compile(r'\b[A-Z]{2}\d{6,10}\b'),  # Generic format
            re.compile(r'\bID[-\s]?\d{8,12}\b', re.IGNORECASE),
        ]
        
        # Password-related keywords
        self.password_keywords = [
            'password', 'passwd', 'pwd', 'pass', 'secret', 'token',
            'api_key', 'apikey', 'auth', 'credentials'
        ]
    
    def detect(self, text: str) -> List[DetectionResult]:
        """
        Detect sensitive data using regex patterns.
        
        Args:
            text: Input text to analyze
        
        Returns:
            List of DetectionResult objects
        """
        detections = []
        
        # Email detection
        for match in self.email_pattern.finditer(text):
            detections.append(DetectionResult(
                detection_type=DetectionType.EMAIL.value,
                value=match.group(),
                start=match.start(),
                end=match.end(),
                confidence=1.0,
                source="regex"
            ))
        
        # Phone detection
        for pattern in self.phone_patterns:
            for match in pattern.finditer(text):
                detections.append(DetectionResult(
                    detection_type=DetectionType.PHONE.value,
                    value=match.group(),
                    start=match.start(),
                    end=match.end(),
                    confidence=1.0,
                    source="regex"
                ))
        
        # Credit card detection
        for pattern in self.credit_card_patterns:
            for match in pattern.finditer(text):
                detections.append(DetectionResult(
                    detection_type=DetectionType.CREDIT_CARD.value,
                    value=match.group(),
                    start=match.start(),
                    end=match.end(),
                    confidence=1.0,
                    source="regex"
                ))
        
        # SSN detection
        for match in self.ssn_pattern.finditer(text):
            detections.append(DetectionResult(
                detection_type=DetectionType.SSN.value,
                value=match.group(),
                start=match.start(),
                end=match.end(),
                confidence=1.0,
                source="regex"
            ))
        
        # National ID detection
        for pattern in self.national_id_patterns:
            for match in pattern.finditer(text):
                detections.append(DetectionResult(
                    detection_type=DetectionType.NATIONAL_ID.value,
                    value=match.group(),
                    start=match.start(),
                    end=match.end(),
                    confidence=0.8,
                    source="regex"
                ))
        
        # Password keyword detection
        text_lower = text.lower()
        for keyword in self.password_keywords:
            pattern = re.compile(rf'\b{keyword}\b', re.IGNORECASE)
            for match in pattern.finditer(text):
                # Check for assignment pattern (e.g., "password = xyz")
                context_start = max(0, match.start() - 10)
                context_end = min(len(text), match.end() + 50)
                context = text[context_start:context_end]
                
                if '=' in context or ':' in context:
                    detections.append(DetectionResult(
                        detection_type=DetectionType.PASSWORD.value,
                        value=match.group(),
                        start=match.start(),
                        end=match.end(),
                        confidence=0.9,
                        source="regex"
                    ))
        
        logger.info(f"Regex detection found {len(detections)} items")
        return detections


class AIDetector:
    """AI-based sensitive data detection using NLP models."""
    
    def __init__(self):
        self.spacy_nlp = None
        self.transformer_pipeline = None
        self.models_loaded = False
    
    def load_models(self):
        """Load AI models (spaCy and HuggingFace)."""
        if self.models_loaded:
            return
        
        try:
            # Load spaCy model
            import spacy
            try:
                self.spacy_nlp = spacy.load("en_core_web_sm")
            except OSError:
                logger.warning("Downloading spaCy model...")
                import subprocess
                subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
                self.spacy_nlp = spacy.load("en_core_web_sm")
            
            logger.info("Loaded spaCy model")
            
            # Load HuggingFace transformer
            from transformers import pipeline
            self.transformer_pipeline = pipeline(
                "ner",
                model="dslim/bert-base-NER",
                aggregation_strategy="simple"
            )
            logger.info("Loaded HuggingFace transformer model")
            
            self.models_loaded = True
            
        except Exception as e:
            logger.error(f"Failed to load AI models: {e}")
            logger.warning("AI detection will be limited")
    
    def detect_with_spacy(self, text: str) -> List[DetectionResult]:
        """Detect entities using spaCy."""
        if not self.spacy_nlp:
            return []
        
        detections = []
        doc = self.spacy_nlp(text)
        
        for ent in doc.ents:
            # Map spaCy entity types to our detection types
            detection_type = ent.label_
            
            if detection_type == "PERSON":
                detection_type = DetectionType.PERSON.value
            elif detection_type == "ORG":
                detection_type = DetectionType.ORGANIZATION.value
            elif detection_type == "GPE":  # Geo-political entity
                detection_type = DetectionType.LOCATION.value
            else:
                continue  # Skip other entity types
            
            detections.append(DetectionResult(
                detection_type=detection_type,
                value=ent.text,
                start=ent.start_char,
                end=ent.end_char,
                confidence=0.85,
                source="spacy"
            ))
        
        return detections
    
    def detect_with_transformer(self, text: str) -> List[DetectionResult]:
        """Detect entities using HuggingFace transformer."""
        if not self.transformer_pipeline:
            return []
        
        detections = []
        
        try:
            # Limit text length for transformer (max 512 tokens)
            max_length = 2000
            if len(text) > max_length:
                text = text[:max_length]
            
            results = self.transformer_pipeline(text)
            
            for entity in results:
                # Map transformer labels to our types
                entity_label = entity['entity_group']
                
                if entity_label == "PER":
                    detection_type = DetectionType.PERSON.value
                elif entity_label == "ORG":
                    detection_type = DetectionType.ORGANIZATION.value
                elif entity_label == "LOC":
                    detection_type = DetectionType.LOCATION.value
                else:
                    continue
                
                detections.append(DetectionResult(
                    detection_type=detection_type,
                    value=entity['word'],
                    start=entity['start'],
                    end=entity['end'],
                    confidence=entity['score'],
                    source="transformer"
                ))
        
        except Exception as e:
            logger.error(f"Transformer detection error: {e}")
        
        return detections
    
    def detect(self, text: str) -> List[DetectionResult]:
        """
        Detect sensitive data using AI models.
        
        Args:
            text: Input text to analyze
        
        Returns:
            List of DetectionResult objects
        """
        if not self.models_loaded:
            self.load_models()
        
        detections = []
        
        # Detect with spaCy
        detections.extend(self.detect_with_spacy(text))
        
        # Detect with transformer
        detections.extend(self.detect_with_transformer(text))
        
        logger.info(f"AI detection found {len(detections)} items")
        return detections


class SensitiveDataDetector:
    """Main detector that combines regex and AI detection."""
    
    def __init__(self):
        self.regex_detector = RegexDetector()
        self.ai_detector = AIDetector()
    
    def initialize(self):
        """Initialize AI models."""
        self.ai_detector.load_models()
    
    def detect(self, text: str) -> List[DetectionResult]:
        """
        Detect all sensitive data in text.
        
        Args:
            text: Input text to analyze
        
        Returns:
            Deduplicated list of DetectionResult objects
        """
        all_detections = []
        
        # Regex detection
        all_detections.extend(self.regex_detector.detect(text))
        
        # AI detection
        all_detections.extend(self.ai_detector.detect(text))
        
        # Deduplicate overlapping detections
        deduplicated = self._deduplicate_detections(all_detections)
        
        logger.info(f"Total detections after deduplication: {len(deduplicated)}")
        return deduplicated
    
    def _deduplicate_detections(self, detections: List[DetectionResult]) -> List[DetectionResult]:
        """Remove overlapping detections, keeping higher confidence ones."""
        if not detections:
            return []
        
        # Sort by start position
        sorted_detections = sorted(detections, key=lambda x: (x.start, -x.confidence))
        
        result = []
        last_end = -1
        
        for detection in sorted_detections:
            # If this detection doesn't overlap with the last one, add it
            if detection.start >= last_end:
                result.append(detection)
                last_end = detection.end
            # If it overlaps, keep it only if it's significantly different
            elif detection.detection_type != (result[-1].detection_type if result else None):
                # Different type of detection at same location - keep both
                result.append(detection)
        
        return result


# Global detector instance
detector = SensitiveDataDetector()
