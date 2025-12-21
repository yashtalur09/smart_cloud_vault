"""File upload API endpoints."""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import Optional
from datetime import datetime
import logging
from pathlib import Path

from models.schemas import (
    FileUploadRequest, UploadResponse, FileMetadata,
    Department, Classification
)
from storage.file_storage import file_storage
from storage.database import get_database
from ai_engine.detector import detector
from ai_engine.classifier import classifier
from utils.file_processor import file_processor
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/upload", tags=["upload"])


@router.post("", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    company: str = Form(...),
    department: Department = Form(...),
    uploader_email: str = Form(...),
    uploader_name: Optional[str] = Form(None),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Upload a file for scanning.
    
    Args:
        file: Uploaded file
        company: Company name
        department: Department name
        uploader_email: Email of person uploading file (required)
        uploader_name: Name of person uploading file (optional)
    
    Returns:
        UploadResponse with file metadata
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Validate email format (basic check)
        if "@" not in uploader_email or "." not in uploader_email:
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        # Read file content
        file_content = await file.read()
        
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # Save file
        file_data = await file_storage.save_file(file_content, file.filename)
        
        # Create metadata
        metadata = FileMetadata(
            file_id=file_data["file_id"],
            original_filename=file_data["original_filename"],
            company=company,
            department=department,
            file_size=file_data["file_size"],
            upload_date=datetime.now(),
            classification=None,
            is_protected=False,
            scan_completed=False,
            uploader_email=uploader_email,
            uploader_name=uploader_name,
            masked_file_path=None,
            masked_fields=[]
        )
        
        # Store metadata in database
        await db.files.insert_one(metadata.dict())
        
        logger.info(f"Uploaded file: {file.filename} for {company}/{department}")
        
        # Trigger scanning automatically
        await _scan_file(file_data["file_id"], db)
        
        # Get updated metadata
        updated_file = await db.files.find_one({"file_id": file_data["file_id"]})
        if updated_file:
            metadata = FileMetadata(**updated_file)
        
        return UploadResponse(
            success=True,
            file_id=file_data["file_id"],
            message="File uploaded and scanned successfully",
            metadata=metadata
        )
    
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _scan_file(file_id: str, db: AsyncIOMotorDatabase):
    """Internal function to scan uploaded file and create masked copy."""
    try:
        # Get file path
        file_path = file_storage.get_file_path(file_id)
        
        if not file_path:
            logger.error(f"File not found: {file_id}")
            return
        
        # Extract text
        file_extension = file_path.suffix
        text = file_processor.extract_text(str(file_path), file_extension)
        
        if not text:
            logger.warning(f"Could not extract text from {file_id}")
            text = ""
        
        # Detect sensitive data
        detections = detector.detect(text)
        
        # Classify file
        classification_result = classifier.classify(detections)
        
        # Create masked file copy (selective masking) 
        from utils.protection import DataMasker
        masked_text, masked_fields = DataMasker.selective_mask(text, detections)
        masked_content = masked_text.encode('utf-8')
        
        # Save masked file
        masked_path = await file_storage.save_masked_file(file_id, masked_content)
        
        # Store detections
        await db.detections.insert_one({
            "file_id": file_id,
            "detections": [det.dict() for det in detections],
            "scan_date": datetime.now()
        })
        
        # Update file metadata with classification and masked file info
        await db.files.update_one(
            {"file_id": file_id},
            {
                "$set": {
                    "classification": classification_result.classification.value,
                    "classification_score": classification_result.score,
                    "classification_reasoning": classification_result.reasoning,
                    "scan_completed": True,
                    "scan_date": datetime.now(),
                    "detections_count": len(detections),
                    "masked_file_path": masked_path,
                    "masked_fields": masked_fields
                }
            }
        )
        
        logger.info(f"Scanned file {file_id}: {classification_result.classification.value}, masked {len(masked_fields)} field types")
    
    except Exception as e:
        logger.error(f"Scan error for {file_id}: {e}")


@router.get("/files")
async def list_files(
    company: Optional[str] = None,
    department: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    List uploaded files.
    
    Args:
        company: Optional company filter
        department: Optional department filter
    
    Returns:
        List of file metadata
    """
    query = {}
    
    if company:
        query["company"] = company
    
    if department:
        query["department"] = department
    
    files = await db.files.find(query).sort("upload_date", -1).to_list(length=100)
    
    return {"files": files, "count": len(files)}


@router.get("/files/{file_id}")
async def get_file_details(
    file_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get detailed information about a file."""
    file_doc = await db.files.find_one({"file_id": file_id})
    
    if not file_doc:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Get detections
    detections_doc = await db.detections.find_one({"file_id": file_id})
    
    return {
        "file": file_doc,
        "detections": detections_doc.get("detections", []) if detections_doc else []
    }
