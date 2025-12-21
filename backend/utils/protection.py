"""Data protection utilities for masking and encryption."""
from cryptography.fernet import Fernet
from typing import List, Tuple
import base64
import os
import logging
from models.schemas import DetectionResult

logger = logging.getLogger(__name__)


class DataMasker:
    """Masks sensitive data in text files."""
    
    @staticmethod
    def mask_text(text: str, detections: List[DetectionResult]) -> str:
        """
        Mask detected sensitive data in text.
        
        Args:
            text: Original text
            detections: List of detections to mask
        
        Returns:
            Masked text with [REDACTED] placeholders
        """
        if not detections:
            return text
        
        # Sort detections by start position in reverse order
        # This way we can replace from end to start without affecting positions
        sorted_detections = sorted(detections, key=lambda x: x.start, reverse=True)
        
        masked_text = text
        masked_count = 0
        
        for detection in sorted_detections:
            # Add detection type to redaction for clarity
            redaction = f"[REDACTED-{detection.detection_type}]"
            
            # Replace the detected text
            masked_text = (
                masked_text[:detection.start] +
                redaction +
                masked_text[detection.end:]
            )
            masked_count += 1
        
        logger.info(f"Masked {masked_count} sensitive items")
        return masked_text
    
    @staticmethod
    def mask_partial(text: str, detections: List[DetectionResult], keep_chars: int = 4) -> str:
        """
        Partially mask sensitive data (e.g., show last 4 digits of credit card).
        
        Args:
            text: Original text
            detections: List of detections to mask
            keep_chars: Number of characters to keep visible
        
        Returns:
            Partially masked text
        """
        if not detections:
            return text
        
        sorted_detections = sorted(detections, key=lambda x: x.start, reverse=True)
        masked_text = text
        
        for detection in sorted_detections:
            original_value = detection.value
            
            if len(original_value) <= keep_chars:
                masked_value = "*" * len(original_value)
            else:
                # Show last N characters
                visible_part = original_value[-keep_chars:]
                masked_part = "*" * (len(original_value) - keep_chars)
                masked_value = masked_part + visible_part
            
            masked_text = (
                masked_text[:detection.start] +
                masked_value +
                masked_text[detection.end:]
            )
        
        return masked_text
    
    @staticmethod
    def selective_mask(text: str, detections: List[DetectionResult]) -> Tuple[str, List[str]]:
        """
        Selectively mask sensitive data while preserving name and email.
        
        DO NOT MASK: PERSON (names), EMAIL
        MUST MASK: PHONE, CREDIT_CARD, SSN, PASSWORD, NATIONAL_ID
        
        Args:
            text: Original text
            detections: List of detections
        
        Returns:
            Tuple of (masked_text, list of masked field types)
        """
        # Types to preserve (NOT mask)
        PRESERVE_TYPES = {"PERSON", "EMAIL", "ORG", "GPE"}
        
        # Types to mask
        MASK_TYPES = {
            "PHONE", "CREDIT_CARD", "SSN", 
            "PASSWORD", "NATIONAL_ID"
        }
        
        if not detections:
            return text, []
        
        # Filter detections - only mask sensitive types
        detections_to_mask = [
            d for d in detections 
            if d.detection_type in MASK_TYPES
        ]
        
        if not detections_to_mask:
            return text, []
        
        # Sort by start position in reverse order
        sorted_detections = sorted(detections_to_mask, key=lambda x: x.start, reverse=True)
        
        masked_text = text
        masked_types = set()
        
        for detection in sorted_detections:
            # Mask with type indicator
            redaction = f"[MASKED-{detection.detection_type}]"
            
            # Replace the detected text
            masked_text = (
                masked_text[:detection.start] +
                redaction +
                masked_text[detection.end:]
            )
            masked_types.add(detection.detection_type)
        
        logger.info(f"Selectively masked {len(sorted_detections)} items, preserved names/emails")
        return masked_text, list(masked_types)


class FileEncryptor:
    """Encrypts and decrypts files."""
    
    def __init__(self, key: bytes = None):
        """
        Initialize encryptor.
        
        Args:
            key: Encryption key (generated if not provided)
        """
        if key is None:
            self.key = Fernet.generate_key()
        else:
            self.key = key
        
        self.cipher = Fernet(self.key)
    
    @staticmethod
    def generate_key() -> bytes:
        """Generate a new encryption key."""
        return Fernet.generate_key()
    
    def encrypt(self, data: bytes) -> bytes:
        """
        Encrypt data.
        
        Args:
            data: Raw data to encrypt
        
        Returns:
            Encrypted data
        """
        encrypted = self.cipher.encrypt(data)
        logger.info(f"Encrypted {len(data)} bytes")
        return encrypted
    
    def decrypt(self, encrypted_data: bytes) -> bytes:
        """
        Decrypt data.
        
        Args:
            encrypted_data: Encrypted data
        
        Returns:
            Decrypted data
        """
        decrypted = self.cipher.decrypt(encrypted_data)
        logger.info(f"Decrypted {len(encrypted_data)} bytes")
        return decrypted
    
    def encrypt_file(self, file_content: bytes) -> Tuple[bytes, bytes]:
        """
        Encrypt file content.
        
        Args:
            file_content: Original file content
        
        Returns:
            Tuple of (encrypted_content, encryption_key)
        """
        encrypted = self.encrypt(file_content)
        return encrypted, self.key
    
    @staticmethod
    def decrypt_file(encrypted_content: bytes, key: bytes) -> bytes:
        """
        Decrypt file content.
        
        Args:
            encrypted_content: Encrypted content
            key: Encryption key
        
        Returns:
            Decrypted content
        """
        cipher = Fernet(key)
        return cipher.decrypt(encrypted_content)


class ProtectionManager:
    """Manages data protection operations."""
    
    def __init__(self):
        self.masker = DataMasker()
        self.encryptor = FileEncryptor()
    
    def protect_text(
        self, 
        text: str, 
        detections: List[DetectionResult],
        mask: bool = True,
        encrypt: bool = False
    ) -> Tuple[bytes, dict]:
        """
        Apply protection to text content.
        
        Args:
            text: Original text
            detections: Detected sensitive items
            mask: Whether to mask sensitive data
            encrypt: Whether to encrypt the result
        
        Returns:
            Tuple of (protected_content, metadata)
        """
        metadata = {
            "masked": mask,
            "encrypted": encrypt,
            "detections_count": len(detections)
        }
        
        # Apply masking if requested
        if mask:
            text = self.masker.mask_text(text, detections)
            metadata["masking_applied"] = True
        
        # Convert to bytes
        content_bytes = text.encode('utf-8')
        
        # Apply encryption if requested
        if encrypt:
            content_bytes, key = self.encryptor.encrypt_file(content_bytes)
            metadata["encryption_applied"] = True
            metadata["encryption_key"] = base64.b64encode(key).decode('utf-8')
        
        return content_bytes, metadata
    
    def unprotect_content(
        self, 
        protected_content: bytes, 
        metadata: dict
    ) -> str:
        """
        Decrypt protected content if encrypted.
        
        Args:
            protected_content: Protected content
            metadata: Protection metadata
        
        Returns:
            Unprotected text (still masked if masking was applied)
        """
        content = protected_content
        
        # Decrypt if needed
        if metadata.get("encrypted"):
            key_b64 = metadata.get("encryption_key")
            if key_b64:
                key = base64.b64decode(key_b64)
                content = FileEncryptor.decrypt_file(content, key)
        
        # Decode to text
        return content.decode('utf-8')


# Global protection manager
protection_manager = ProtectionManager()
