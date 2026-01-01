"""Storage abstraction layer for SmartCloud Vault.

This module provides a unified interface for file storage operations,
supporting both local storage and cloud storage (AWS S3).
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """Abstract base class for storage backends."""
    
    @abstractmethod
    async def save_original(self, file_content: bytes, file_id: str, filename: str, company: Optional[str] = None) -> Dict[str, str]:
        """
        Save original (unmasked) file.
        
        Args:
            file_content: File binary content
            file_id: Unique file identifier
            filename: Original filename
            company: Company name (optional, for organizing files)
        
        Returns:
            dict: Storage metadata (storage_key, location, etc.)
        """
        pass
    
    @abstractmethod
    async def save_masked(self, file_content: bytes, file_id: str, filename: str, company: Optional[str] = None) -> Dict[str, str]:
        """
        Save masked/encrypted file.
        
        Args:
            file_content: Masked file binary content
            file_id: Unique file identifier
            filename: Original filename
            company: Company name (optional, for organizing files)
        
        Returns:
            dict: Storage metadata (storage_key, location, etc.)
        """
        pass
    
    @abstractmethod
    async def get_original(self, file_id: str, storage_key: Optional[str] = None) -> Optional[bytes]:
        """
        Retrieve original file content.
        
        Args:
            file_id: File identifier
            storage_key: Optional storage-specific key/path
        
        Returns:
            bytes: File content or None if not found
        """
        pass
    
    @abstractmethod
    async def get_masked(self, file_id: str, storage_key: Optional[str] = None) -> Optional[bytes]:
        """
        Retrieve masked file content.
        
        Args:
            file_id: File identifier
            storage_key: Optional storage-specific key/path
        
        Returns:
            bytes: File content or None if not found
        """
        pass
    
    @abstractmethod
    def get_original_path(self, file_id: str, storage_key: Optional[str] = None) -> Optional[Path]:
        """
        Get original file path (for local storage) or None (for cloud storage).
        
        Args:
            file_id: File identifier
            storage_key: Optional storage-specific key
        
        Returns:
            Path or None
        """
        pass
    
    @abstractmethod
    async def delete_original(self, file_id: str, storage_key: Optional[str] = None) -> bool:
        """
        Delete original file.
        
        Args:
            file_id: File identifier
            storage_key: Optional storage-specific key
        
        Returns:
            bool: True if deleted, False otherwise
        """
        pass
    
    @abstractmethod
    async def delete_masked(self, file_id: str, storage_key: Optional[str] = None) -> bool:
        """
        Delete masked file.
        
        Args:
            file_id: File identifier
            storage_key: Optional storage-specific key
        
        Returns:
            bool: True if deleted, False otherwise
        """
        pass


class StorageManager:
    """
    Unified storage manager that delegates to the appropriate backend.
    
    This provides backward compatibility and allows switching between
    local and cloud storage seamlessly.
    """
    
    def __init__(self, backend: StorageBackend):
        """
        Initialize storage manager with a backend.
        
        Args:
            backend: Storage backend implementation (LocalStorage or S3Storage)
        """
        self.backend = backend
        logger.info(f"Initialized storage manager with backend: {backend.__class__.__name__}")
    
    async def save_original(self, file_content: bytes, file_id: str, filename: str, company: Optional[str] = None) -> Dict[str, str]:
        """Save original file using configured backend."""
        return await self.backend.save_original(file_content, file_id, filename, company)
    
    async def save_masked(self, file_content: bytes, file_id: str, filename: str, company: Optional[str] = None) -> Dict[str, str]:
        """Save masked file using configured backend."""
        return await self.backend.save_masked(file_content, file_id, filename, company)
    
    async def get_original(self, file_id: str, storage_key: Optional[str] = None) -> Optional[bytes]:
        """Get original file using configured backend."""
        return await self.backend.get_original(file_id, storage_key)
    
    async def get_masked(self, file_id: str, storage_key: Optional[str] = None) -> Optional[bytes]:
        """Get masked file using configured backend."""
        return await self.backend.get_masked(file_id, storage_key)
    
    def get_original_path(self, file_id: str, storage_key: Optional[str] = None) -> Optional[Path]:
        """Get original file path (returns None for cloud storage)."""
        return self.backend.get_original_path(file_id, storage_key)
    
    async def delete_original(self, file_id: str, storage_key: Optional[str] = None) -> bool:
        """Delete original file using configured backend."""
        return await self.backend.delete_original(file_id, storage_key)
    
    async def delete_masked(self, file_id: str, storage_key: Optional[str] = None) -> bool:
        """Delete masked file using configured backend."""
        return await self.backend.delete_masked(file_id, storage_key)
