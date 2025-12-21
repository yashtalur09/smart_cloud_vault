"""File access and download API with email-based access control."""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import Optional
import logging
from io import BytesIO

from models.schemas import FileAccessRequest
from storage.file_storage import file_storage
from storage.database import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/files", tags=["files"])


@router.post("/access")
async def access_file(
    request: FileAccessRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Access/download a file based on email matching.
    
    Rules:
    - If requester_email matches uploader_email → return original file
    - If requester_email does NOT match → return masked file
    
    Args:
        request: FileAccessRequest with file_id and requester_email
    
    Returns:
        File content (original or masked based on email match)
    """
    try:
        # Validate email format
        if "@" not in request.requester_email or "." not in request.requester_email:
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        # Get file metadata from database
        file_doc = await db.files.find_one({"file_id": request.file_id})
        
        if not file_doc:
            raise HTTPException(status_code=404, detail="File not found")
        
        uploader_email = file_doc.get("uploader_email")
        original_filename = file_doc.get("original_filename", "file")
        
        # Check email match
        email_matches = (request.requester_email.lower() == uploader_email.lower())
        
        if email_matches:
            # Return original file
            logger.info(f"Access granted: {request.requester_email} matches uploader for {request.file_id}")
            file_content = await file_storage.get_file(request.file_id)
            file_type = "original"
        else:
            # Return masked file
            logger.info(f"Access restricted: {request.requester_email} != {uploader_email} for {request.file_id}, returning masked version")
            file_content = await file_storage.get_masked_file(request.file_id)
            file_type = "masked"
        
        if not file_content:
            raise HTTPException(status_code=404, detail=f"{file_type.capitalize()} file not found")
        
        # Determine content type
        filename_lower = original_filename.lower()
        if filename_lower.endswith('.pdf'):
            media_type = "application/pdf"
        elif filename_lower.endswith('.docx'):
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif filename_lower.endswith('.csv'):
            media_type = "text/csv"
        else:
            media_type = "text/plain"
        
        # Create filename for download
        if file_type == "masked":
            filename_parts = original_filename.rsplit('.', 1)
            if len(filename_parts) == 2:
                download_filename = f"{filename_parts[0]}_masked.{filename_parts[1]}"
            else:
                download_filename = f"{original_filename}_masked"
        else:
            download_filename = original_filename
        
        # Return file as streaming response
        return StreamingResponse(
            BytesIO(file_content),
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{download_filename}"',
                "X-File-Type": file_type,  # Custom header to indicate which version
                "X-Email-Match": str(email_matches)
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File access error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/info/{file_id}")
async def get_file_info(
    file_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get file information (without downloading).
    
    Args:
        file_id: File identifier
    
    Returns:
        File metadata (excluding sensitive paths)
    """
    file_doc = await db.files.find_one({"file_id": file_id})
    
    if not file_doc:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Return safe metadata (don't expose file paths)
    return {
        "file_id": file_doc.get("file_id"),
        "original_filename": file_doc.get("original_filename"),
        "company": file_doc.get("company"),
        "department": file_doc.get("department"),
        "classification": file_doc.get("classification"),
        "upload_date": file_doc.get("upload_date"),
        "uploader_name": file_doc.get("uploader_name"),  # OK to show name
        "file_size": file_doc.get("file_size"),
        "masked_fields": file_doc.get("masked_fields", []),
        "has_masked_version": file_doc.get("masked_file_path") is not None
    }
