"""Local file storage manager."""
import os
import shutil
import uuid
from pathlib import Path
from typing import Optional, BinaryIO
import aiofiles
from config import settings
import logging

logger = logging.getLogger(__name__)


class FileStorage:
    """Manages local file storage operations."""
    
    def __init__(self):
        self.upload_dir = Path(settings.upload_dir)
        self.protected_dir = Path(settings.protected_dir)
        self.temp_dir = Path(settings.temp_dir)
        self.masked_dir = Path(settings.upload_dir).parent / "masked"
        
        # Ensure directories exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.protected_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.masked_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_file_id(self) -> str:
        """Generate unique file ID."""
        return str(uuid.uuid4())
    
    async def save_file(self, file_content: bytes, filename: str, file_id: Optional[str] = None) -> dict:
        """
        Save uploaded file to local storage.
        
        Args:
            file_content: File binary content
            filename: Original filename
            file_id: Optional file ID (generated if not provided)
        
        Returns:
            dict: File metadata including file_id and path
        """
        if file_id is None:
            file_id = self.generate_file_id()
        
        # Get file extension
        ext = Path(filename).suffix
        stored_filename = f"{file_id}{ext}"
        file_path = self.upload_dir / stored_filename
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)
        
        logger.info(f"Saved file: {filename} as {stored_filename}")
        
        return {
            "file_id": file_id,
            "original_filename": filename,
            "stored_filename": stored_filename,
            "file_path": str(file_path),
            "file_size": len(file_content)
        }
    
    async def get_file(self, file_id: str) -> Optional[bytes]:
        """
        Retrieve file content by file ID.
        
        For image uploads that have been OCR-processed, this returns the .txt file
        (the OCR-extracted text), not the original image.
        
        Args:
            file_id: File identifier
        
        Returns:
            bytes: File content or None if not found
        """
        # Find file with this ID (any extension)
        files = list(self.upload_dir.glob(f"{file_id}.*"))
        
        if not files:
            logger.warning(f"File not found: {file_id}")
            return None
        
        # CRITICAL: For OCR-processed images, prioritize .txt file over image files
        # This ensures the "original" file for image uploads is the OCR text, not binary image data
        txt_file = self.upload_dir / f"{file_id}.txt"
        if txt_file.exists():
            file_path = txt_file
        else:
            file_path = files[0]
        
        async with aiofiles.open(file_path, 'rb') as f:
            content = await f.read()
        
        return content
    
    def get_file_path(self, file_id: str) -> Optional[Path]:
        """Get file path by ID."""
        files = list(self.upload_dir.glob(f"{file_id}.*"))
        return files[0] if files else None
    
    async def save_protected_file(self, file_id: str, protected_content: bytes, suffix: str = "_protected") -> str:
        """
        Save protected (masked/encrypted) file.
        
        Args:
            file_id: Original file ID
            protected_content: Protected file content
            suffix: Suffix to add to filename
        
        Returns:
            str: Protected file path
        """
        # Find original file extension
        original_files = list(self.upload_dir.glob(f"{file_id}.*"))
        ext = original_files[0].suffix if original_files else ""
        
        protected_filename = f"{file_id}{suffix}{ext}"
        protected_path = self.protected_dir / protected_filename
        
        async with aiofiles.open(protected_path, 'wb') as f:
            await f.write(protected_content)
        
        logger.info(f"Saved protected file: {protected_filename}")
        
        return str(protected_path)
    
    async def get_protected_file(self, file_id: str, suffix: str = "_protected") -> Optional[bytes]:
        """Retrieve protected file content."""
        files = list(self.protected_dir.glob(f"{file_id}{suffix}.*"))
        
        if not files:
            logger.warning(f"Protected file not found: {file_id}")
            return None
        
        async with aiofiles.open(files[0], 'rb') as f:
            content = await f.read()
        
        return content
    
    async def save_masked_file(self, file_id: str, masked_content: bytes) -> str:
        """
        Save masked file copy (selective masking - preserves name/email).
        
        Args:
            file_id: Original file ID
            masked_content: Selectively masked file content
        
        Returns:
            str: Masked file path
        """
        # Find original file extension
        original_files = list(self.upload_dir.glob(f"{file_id}.*"))
        ext = original_files[0].suffix if original_files else ""
        
        masked_filename = f"{file_id}_masked{ext}"
        masked_path = self.masked_dir / masked_filename
        
        async with aiofiles.open(masked_path, 'wb') as f:
            await f.write(masked_content)
        
        logger.info(f"Saved masked file: {masked_filename}")
        
        return str(masked_path)
    
    async def get_masked_file(self, file_id: str) -> Optional[bytes]:
        """Retrieve masked file content."""
        files = list(self.masked_dir.glob(f"{file_id}_masked.*"))
        
        if not files:
            logger.warning(f"Masked file not found: {file_id}")
            return None
        
        async with aiofiles.open(files[0], 'rb') as f:
            content = await f.read()
        
        return content
    
    async def save_ocr_text_file(self, file_id: str, text_content: bytes) -> str:
        """
        Save OCR extracted text as a .txt file (replaces image as "original" file).
        
        Args:
            file_id: File ID
            text_content: OCR extracted text as bytes
        
        Returns:
            str: Path to saved text file
        """
        # Save as .txt file in uploads directory
        text_filename = f"{file_id}.txt"
        text_path = self.upload_dir / text_filename
        
        async with aiofiles.open(text_path, 'wb') as f:
            await f.write(text_content)
        
        logger.info(f"Saved OCR text file: {text_filename}")
        
        return str(text_path)
    
    def delete_image_file(self, file_id: str, extension: str) -> bool:
        """
        Delete original image file after OCR processing.
        
        Args:
            file_id: File identifier
            extension: Image file extension (e.g., '.jpg', '.png')
        
        Returns:
            bool: True if file was deleted, False otherwise
        """
        image_path = self.upload_dir / f"{file_id}{extension}"
        
        if image_path.exists():
            image_path.unlink()
            logger.info(f"Deleted original image file: {image_path}")
            return True
        
        return False
    
    def delete_file(self, file_id: str) -> bool:
        """Delete file by ID."""
        files = list(self.upload_dir.glob(f"{file_id}.*"))
        
        for file_path in files:
            file_path.unlink()
            logger.info(f"Deleted file: {file_path}")
        
        return len(files) > 0


# Create singleton instance
file_storage = FileStorage()
