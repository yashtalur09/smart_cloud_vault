"""Data protection API endpoints."""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
from typing import Optional
import logging

from models.schemas import ProtectionRequest
from storage.file_storage import file_storage
from storage.database import get_database
from utils.protection import protection_manager
from utils.file_processor import file_processor
from motor.motor_asyncio import AsyncIOMotorDatabase

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
        
        # Get file content
        file_content = await file_storage.get_file(file_id)
        
        if not file_content:
            raise HTTPException(status_code=404, detail="File content not found")
        
        # Get file path for text extraction
        file_path = file_storage.get_file_path(file_id)
        file_extension = file_path.suffix if file_path else ".txt"
        
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
