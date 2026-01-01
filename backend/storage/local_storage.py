"""Local file storage backend (backward compatible wrapper).

This wraps the existing FileStorage class to implement the StorageBackend interface,
providing backward compatibility while supporting the new storage abstraction.
"""
from typing import Optional, Dict
from pathlib import Path
import logging

from storage.storage_interface import StorageBackend
from storage.file_storage import file_storage

logger = logging.getLogger(__name__)


class LocalStorage(StorageBackend):
    """
    Local file storage backend.
    
    This wraps the existing FileStorage implementation to support
    the new storage abstraction layer.
    """
    
    def __init__(self):
        """Initialize local storage backend."""
        self.file_storage = file_storage
        logger.info("Initialized local storage backend")
    
    async def save_original(self, file_content: bytes, file_id: str, filename: str, company: Optional[str] = None) -> Dict[str, str]:
        """
        Save original file to local storage.
        
        Args:
            file_content: File binary content
            file_id: Unique file identifier
            filename: Original filename
            company: Company name (not used for local storage)
        
        Returns:
            dict: Storage metadata
        """
        result = await self.file_storage.save_file(file_content, filename, file_id)
        
        return {
            'storage_type': 'local',
            'file_id': result['file_id'],
            'filename': result['original_filename'],
            'path': result['file_path'],
            'size': result['file_size']
        }
    
    async def save_masked(self, file_content: bytes, file_id: str, filename: str, company: Optional[str] = None) -> Dict[str, str]:
        """
        Save masked file to local storage.
        
        Args:
            file_content: Masked file binary content
            file_id: Unique file identifier
            filename: Original filename
            company: Company name (not used for local storage)
        
        Returns:
            dict: Storage metadata
        """
        masked_path = await self.file_storage.save_masked_file(file_id, file_content)
        
        return {
            'storage_type': 'local',
            'file_id': file_id,
            'filename': filename,
            'path': masked_path,
            'size': len(file_content)
        }
    
    async def get_original(self, file_id: str, storage_key: Optional[str] = None) -> Optional[bytes]:
        """
        Retrieve original file from local storage.
        
        Args:
            file_id: File identifier
            storage_key: Not used for local storage
        
        Returns:
            bytes: File content or None if not found
        """
        return await self.file_storage.get_file(file_id)
    
    async def get_masked(self, file_id: str, storage_key: Optional[str] = None) -> Optional[bytes]:
        """
        Retrieve masked file from local storage.
        
        Args:
            file_id: File identifier
            storage_key: Not used for local storage
        
        Returns:
            bytes: File content or None if not found
        """
        return await self.file_storage.get_masked_file(file_id)
    
    def get_original_path(self, file_id: str, storage_key: Optional[str] = None) -> Optional[Path]:
        """
        Get original file path.
        
        Args:
            file_id: File identifier
            storage_key: Not used for local storage
        
        Returns:
            Path or None
        """
        return self.file_storage.get_file_path(file_id)
    
    async def delete_original(self, file_id: str, storage_key: Optional[str] = None) -> bool:
        """
        Delete original file from local storage.
        
        Args:
            file_id: File identifier
            storage_key: Not used for local storage
        
        Returns:
            bool: True if deleted, False otherwise
        """
        return self.file_storage.delete_file(file_id)
    
    async def delete_masked(self, file_id: str, storage_key: Optional[str] = None) -> bool:
        """
        Delete masked file from local storage.
        
        Args:
            file_id: File identifier
            storage_key: Not used for local storage
        
        Returns:
            bool: True if deleted, False otherwise
        """
        # Delete masked file
        masked_path = self.file_storage.masked_dir / f"{file_id}_masked.*"
        import glob
        masked_files = glob.glob(str(masked_path))
        
        if not masked_files:
            return False
        
        for file_path in masked_files:
            Path(file_path).unlink()
            logger.info(f"Deleted masked file: {file_path}")
        
        return True
