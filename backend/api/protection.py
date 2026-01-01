"""Data protection API endpoints."""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
from typing import Optional
from pathlib import Path
import logging

from models.schemas import ProtectionRequest
from storage.file_storage import file_storage
from storage.storage_factory import storage_manager
from storage.database import get_database
from utils.protection import protection_manager
from utils.file_processor import file_processor
from motor.motor_asyncio import AsyncIOMotorDatabase
from config import settings
import aiofiles

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/protect", tags=["protection"])


@router.post("/{file_id}")
async def protect_file(
    file_id: str,
    mask: bool = True,
    encrypt: bool = False,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Apply protection to a file (masking and/or encryption).
    
    Args:
        file_id: File identifier
        mask: Whether to mask sensitive data
        encrypt: Whether to encrypt the file
    
    Returns:
        Protection status
    """
    try:
        # Get file metadata
        file_doc = await db.files.find_one({"file_id": file_id})
        
        if not file_doc:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get storage info
        storage_type = file_doc.get('storage_type', 'local')
        original_s3_key = file_doc.get('original_s3_key')
        original_filename = file_doc.get('original_filename', '')
        
        # Get file content using storage manager
        file_content = await storage_manager.get_original(file_id, original_s3_key)
        
        if not file_content:
            raise HTTPException(status_code=404, detail="File content not found")
        
        # For S3 storage, we need to save to temp file for text extraction
        # For local storage, get the file path directly
        if storage_type == 's3':
            # Save to temp file for processing
            file_extension = Path(original_filename).suffix
            temp_path = Path(settings.temp_dir) / f"{file_id}{file_extension}"
            temp_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(temp_path, 'wb') as f:
                await f.write(file_content)
            
            # Extract text from temp file
            text = file_processor.extract_text(str(temp_path), file_extension)
            
            # Clean up temp file
            temp_path.unlink(missing_ok=True)
        else:
            # Local storage: get file path
            file_path = file_storage.get_file_path(file_id)
            if not file_path:
                raise HTTPException(status_code=404, detail="File path not found")
            
            file_extension = file_path.suffix
            # Extract text
            text = file_processor.extract_text(str(file_path), file_extension)
        
        if not text:
            raise HTTPException(status_code=400, detail="Could not extract text from file")
        
        # Get detections
        detections_doc = await db.detections.find_one({"file_id": file_id})
        
        if not detections_doc:
            raise HTTPException(status_code=400, detail="File not scanned yet")
        
        from models.schemas import DetectionResult
        detections = [DetectionResult(**d) for d in detections_doc.get("detections", [])]
        
        # Apply protection
        protected_content, metadata = protection_manager.protect_text(
            text,
            detections,
            mask=mask,
            encrypt=encrypt
        )
        
        # Save protected file
        protected_path = await file_storage.save_protected_file(
            file_id,
            protected_content,
            suffix="_protected"
        )
        
        # Update file metadata
        await db.files.update_one(
            {"file_id": file_id},
            {
                "$set": {
                    "is_protected": True,
                    "protection_metadata": metadata,
                    "protected_file_path": protected_path
                }
            }
        )
        
        logger.info(f"Protected file {file_id}: mask={mask}, encrypt={encrypt}")
        
        return {
            "success": True,
            "file_id": file_id,
            "message": "File protected successfully",
            "metadata": metadata
        }
    
    except Exception as e:
        logger.error(f"Protection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{file_id}/download")
async def download_protected_file(
    file_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Download protected file.
    
    Args:
        file_id: File identifier
    
    Returns:
        Protected file content
    """
    try:
        # Get file metadata
        file_doc = await db.files.find_one({"file_id": file_id})
        
        if not file_doc:
            raise HTTPException(status_code=404, detail="File not found")
        
        if not file_doc.get("is_protected"):
            raise HTTPException(status_code=400, detail="File not protected")
        
        # Get protected file
        protected_content = await file_storage.get_protected_file(file_id, suffix="_protected")
        
        if not protected_content:
            raise HTTPException(status_code=404, detail="Protected file not found")
        
        # Determine content type
        original_filename = file_doc.get("original_filename", "protected.txt")
        
        return Response(
            content=protected_content,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename=protected_{original_filename}"
            }
        )
    
    except Exception as e:
        logger.error(f"Download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
