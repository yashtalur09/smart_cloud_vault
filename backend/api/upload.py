"""File upload API endpoints."""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import Optional
from datetime import datetime
import logging
from pathlib import Path

from models.schemas import (
    FileUploadRequest, UploadResponse, FileMetadata,
    Department, Classification, SourceType, EnhancedFileMetadata,
    ContextAwareAnalysisResult, DocumentTypeInfo, SemanticFieldInfo,
    MaskingExplanation
)
from storage.file_storage import file_storage
from storage.storage_factory import storage_manager
from storage.database import get_database
from ai_engine.detector import detector
from ai_engine.classifier import classifier
from ai_engine.context_aware_engine import context_engine
from ai_engine.govt_doc_normalizer import GovernmentDocumentNormalizer
from utils.file_processor import file_processor
from motor.motor_asyncio import AsyncIOMotorDatabase
from config import settings

logger = logging.getLogger(__name__)

# Initialize normalizer for government documents
normalizer = GovernmentDocumentNormalizer()

router = APIRouter(prefix="/api/upload", tags=["upload"])


@router.post("", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    company: str = Form(...),
    department: Department = Form(...),
    uploader_email: str = Form(...),
    uploader_name: Optional[str] = Form(None),
    employee_id: str = Form(...),
    employee_name: str = Form(...),
    employee_email: str = Form(...),
    document_name: Optional[str] = Form(None),
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
        employee_id: Employee ID (required for folder structure)
        employee_name: Employee name (required)
        employee_email: Employee email (required)
        document_name: Document type name (optional, e.g., Aadhaar, PAN, DL)
    
    Returns:
        UploadResponse with file metadata
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Validate employee email format
        if "@" not in employee_email or "." not in employee_email:
            raise HTTPException(status_code=400, detail="Invalid employee email format")
        
        # Validate uploader email format (basic check)
        if "@" not in uploader_email or "." not in uploader_email:
            raise HTTPException(status_code=400, detail="Invalid uploader email format")
        
        # Read file content
        file_content = await file.read()
        
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # Save original file using storage manager (employee_id used for S3 folder structure)
        storage_result = await storage_manager.save_original(
            file_content=file_content,
            file_id=file_storage.generate_file_id(),
            filename=file.filename,
            company=employee_id  # Use employee_id for folder structure in S3
        )
        
        file_id = storage_result['file_id']
        
        # Determine source type (text vs image)
        file_extension = Path(file.filename).suffix.lower()
        is_image = file_extension in ['.jpg', '.jpeg', '.png']
        source_type = SourceType.IMAGE if is_image else SourceType.TEXT
        
        # Create metadata with storage information and employee fields
        metadata = FileMetadata(
            file_id=file_id,
            original_filename=file.filename,
            company=company,
            department=department,
            file_size=storage_result.get('size', len(file_content)),
            upload_date=datetime.now(),
            classification=None,
            is_protected=False,
            scan_completed=False,
            uploader_email=uploader_email,
            uploader_name=uploader_name,
            masked_file_path=None,
            masked_fields=[],
            source_type=source_type,
            ocr_extracted=is_image,
            # Employee fields
            employee_id=employee_id,
            employee_name=employee_name,
            employee_email=employee_email,
            document_name=document_name,
            # Storage backend fields
            storage_type=storage_result.get('storage_type'),
            original_s3_key=storage_result.get('s3_key'),
            original_bucket=storage_result.get('bucket')
        )
        
        # Store metadata in database
        await db.files.insert_one(metadata.dict())
        
        logger.info(f"Uploaded file: {file.filename} for {company}/{department} (storage: {storage_result.get('storage_type')})")
        
        # Trigger scanning automatically
        ocr_text = await _scan_file(file_id, company, db)
        
        # Get updated metadata
        updated_file = await db.files.find_one({"file_id": file_id})
        if updated_file:
            metadata = FileMetadata(**updated_file)
        
        return UploadResponse(
            success=True,
            file_id=file_id,
            message="File uploaded and scanned successfully",
            metadata=metadata,
            ocr_extracted_text=ocr_text if is_image else None
        )
    
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _scan_file(file_id: str, company: str, db: AsyncIOMotorDatabase):
    """Internal function to scan uploaded file and create masked copy. Returns OCR text for images."""
    try:
        # Get file metadata from database to retrieve storage info
        file_doc = await db.files.find_one({"file_id": file_id})
        if not file_doc:
            logger.error(f"File metadata not found: {file_id}")
            return None
        
        storage_type = file_doc.get('storage_type', 'local')
        original_s3_key = file_doc.get('original_s3_key')
        
        # For local storage, get file path; for S3, we'll fetch content
        if storage_type == 'local':
            file_path = file_storage.get_file_path(file_id)
            if not file_path:
                logger.error(f"File not found: {file_id}")
                return None
            file_extension = file_path.suffix
            # Extract text from local file
            text = file_processor.extract_text(str(file_path), file_extension)
        else:
            # S3 storage: fetch file content and extract text
            file_content = await storage_manager.get_original(file_id, original_s3_key)
            if not file_content:
                logger.error(f"File not found in S3: {file_id}")
                return None
            
            # Get file extension from original filename
            original_filename = file_doc.get('original_filename', '')
            file_extension = Path(original_filename).suffix
            
            # For text files, decode directly; for others, save temp and extract
            if file_extension.lower() in ['.txt', '.csv']:
                text = file_content.decode('utf-8', errors='ignore')
            else:
                # Save to temp file for processing
                temp_path = Path(settings.temp_dir) / f"{file_id}{file_extension}"
                temp_path.parent.mkdir(parents=True, exist_ok=True)
                async with __import__('aiofiles').open(temp_path, 'wb') as f:
                    await f.write(file_content)
                text = file_processor.extract_text(str(temp_path), file_extension)
                # Clean up temp file
                temp_path.unlink(missing_ok=True)
        
        
        if not text:
            logger.warning(f"Could not extract text from {file_id}")
            text = ""
        
        # For images, we'll save OCR text initially, but might replace with normalized version
        is_image = file_extension.lower() in ['.jpg', '.jpeg', '.png']
        save_original_later = is_image  # Flag to save after normalization
        
        # ===== CONTEXT-AWARE PROCESSING =====
        # First, check document type to decide if normalization is needed
        logger.info(f"Processing {file_id} with context-aware engine")
        
        # Quick classification pass to check if government document
        preliminary_result = context_engine.process_document(
            text=text,
            apply_masking=False,  # Don't mask yet
            preserve_structure=True
        )
        
        document_context = preliminary_result.get('document_context', {})
        is_govt_doc = document_context.get('type') == 'government_id'
        
        # ===== NORMALIZATION LAYER (GOVERNMENT DOCS ONLY) =====
        normalized_original_text = None
        normalized_masked_text = None
        
        if is_govt_doc:
            logger.info(f"Government document detected - applying normalization layer")
            
            try:
                # Normalize the raw OCR text into standard structure
                normalized_doc = normalizer.normalize_document(text, document_context)
                
                # Generate normalized original (structured but unmasked)
                normalized_original_text = normalizer.format_normalized_document(
                    normalized_doc, 
                    mask=False,
                    raw_text=text
                )
                
                # Generate normalized masked (structured and masked)
                normalized_masked_text = normalizer.format_normalized_document(
                    normalized_doc,
                    mask=True,
                    raw_text=text
                )
                
                logger.info(
                    f"Normalized {normalized_doc.document_type} with "
                    f"{normalized_doc.confidence_score:.2%} confidence"
                )
                
                # Replace original text with normalized version for storage
                text = normalized_original_text
                masked_text = normalized_masked_text
                
                # Store normalization metadata
                normalization_metadata = {
                    "normalized": True,
                    "document_subtype": normalized_doc.document_type,
                    "authority": normalized_doc.authority,
                    "normalization_confidence": normalized_doc.confidence_score,
                    "field_confidences": normalized_doc.field_confidences,
                    "qr_code_present": normalized_doc.qr_code_present,
                    "signature_present": normalized_doc.signature_present
                }
                
            except Exception as e:
                logger.error(f"Normalization failed for {file_id}: {e}")
                # Fallback to regular processing if normalization fails
                is_govt_doc = False
                normalization_metadata = {"normalized": False, "error": str(e)}
        else:
            normalization_metadata = {"normalized": False}
        
        # ===== MASKING (ON NORMALIZED TEXT IF GOVT DOC) =====
        if not is_govt_doc:
            # For non-government docs, use regular context-aware processing
            context_result = context_engine.process_document(
                text=text,
                apply_masking=True,
                preserve_structure=True
            )
            
            masked_text = context_result.get('masked_text', text)
            explanations = context_result.get('explanations', [])
            summary = context_result.get('summary', {})
        else:
            # For government docs, we already have normalized masked text
            # Create minimal explanations for compatibility
            explanations = [
                {
                    "field": "govt_id_number",
                    "original_value": "[REDACTED]",
                    "masked_value": "[MASKED-GOVT-ID]",
                    "reason": "Government-issued identification number",
                    "sensitivity": "CRITICAL",
                    "confidence": normalization_metadata.get("normalization_confidence", 0.95)
                },
                {
                    "field": "date_of_birth",
                    "original_value": "[REDACTED]",
                    "masked_value": "[MASKED-DOB]",
                    "reason": "Personal date of birth",
                    "sensitivity": "CRITICAL",
                    "confidence": normalization_metadata.get("field_confidences", {}).get("date_of_birth", 0.90)
                }
            ]
            summary = {
                "total_fields": len(normalization_metadata.get("field_confidences", {})),
                "fields_masked": sum(1 for v in normalization_metadata.get("field_confidences", {}).values() if v > 0.7),
                "document_normalized": True
            }
        
        # Save original file (normalized if govt doc, raw otherwise)
        # For images with OCR, we replace the image with the text file
        if save_original_later:
            original_text_content = text.encode('utf-8')
            
            if storage_type == 'local':
                # Local storage: use existing method
                await file_storage.save_ocr_text_file(file_id, original_text_content)
                # Delete the original image file - we only keep the text
                file_storage.delete_image_file(file_id, file_extension)
                logger.info(f"Saved {'normalized' if is_govt_doc else 'OCR'} text and deleted original image for {file_id}")
            else:
                # S3 storage: save OCR text to original bucket (replaces image reference)
                original_filename = file_doc.get('original_filename', '')
                filename_base = original_filename.rsplit('.', 1)[0] if '.' in original_filename else original_filename
                txt_filename = f"{filename_base}.txt"
                
                storage_result = await storage_manager.save_original(
                    file_content=original_text_content,
                    file_id=file_id,
                    filename=txt_filename,
                    company=company
                )
                
                # Update S3 key in metadata
                await db.files.update_one(
                    {"file_id": file_id},
                    {"$set": {
                        "original_s3_key": storage_result.get('s3_key'),
                        "original_filename": txt_filename  # Update to reflect text file
                    }}
                )
                logger.info(f"Saved {'normalized' if is_govt_doc else 'OCR'} text to S3 for {file_id}")
        
        # Save masked file using storage manager
        masked_content = masked_text.encode('utf-8')
        
        original_filename = file_doc.get('original_filename', '')
        storage_result = await storage_manager.save_masked(
            file_content=masked_content,
            file_id=file_id,
            filename=original_filename,
            company=company
        )
        
        masked_path = storage_result.get('s3_key') or storage_result.get('path', '')
        
        # Store masked S3 info if using S3
        masked_storage_update = {
            "masked_file_path": masked_path
        }
        
        if storage_type == 's3':
            masked_storage_update.update({
                "masked_s3_key": storage_result.get('s3_key'),
                "masked_bucket": storage_result.get('bucket')
            })
        
        # Also run legacy detector for compatibility (but prefer context-aware results)
        detections = detector.detect(text)
        classification_result = classifier.classify(detections)
        
        # Determine compliance tags based on document type
        compliance_tags = []
        if document_context.get('type') == 'government_id':
            compliance_tags = ["PII", "GOVERNMENT_ID", "HIGH_RISK", "REGULATORY"]
        elif document_context.get('type') in ['hr', 'personal']:
            compliance_tags = ["PII", "CONFIDENTIAL"]
        elif document_context.get('type') in ['financial', 'invoice', 'bill']:
            compliance_tags = ["FINANCIAL", "BUSINESS_CONFIDENTIAL"]
        
        # Store context-aware analysis results (including normalization metadata)
        await db.context_analysis.insert_one({
            "file_id": file_id,
            "document_type": document_context.get('type'),
            "document_confidence": document_context.get('confidence'),
            "keywords": document_context.get('keywords', []),
            "reasoning": document_context.get('reasoning', ''),
            "detected_fields": preliminary_result.get('detected_fields', []) if is_govt_doc else context_result.get('detected_fields', []),
            "explanations": explanations,
            "summary": summary,
            "compliance_tags": compliance_tags,
            "normalization": normalization_metadata,  # Add normalization info
            "analysis_date": datetime.now()
        })
        
        # Store legacy detections for compatibility
        await db.detections.insert_one({
            "file_id": file_id,
            "detections": [det.dict() for det in detections],
            "scan_date": datetime.now()
        })
        
        # Update file metadata with context-aware information
        update_data = {
            "classification": classification_result.classification.value,
            "classification_score": classification_result.score,
            "classification_reasoning": classification_result.reasoning,
            "scan_completed": True,
            "scan_date": datetime.now(),
            "detections_count": len(detections),
            "masked_fields": [exp['field'] for exp in explanations],
            # Context-aware fields
            "document_type": document_context.get('type'),
            "document_type_confidence": document_context.get('confidence'),
            "context_aware_processed": True,
            "semantic_fields_count": summary.get('total_fields_detected', 0),
            "masking_explanations": explanations,
            "compliance_tags": compliance_tags
        }
        
        # Merge masked storage info
        update_data.update(masked_storage_update)
        
        # Add OCR text preview for images (first 500 chars)
        if is_image and text:
            update_data["ocr_text_preview"] = text[:500]
        
        await db.files.update_one(
            {"file_id": file_id},
            {"$set": update_data}
        )
        
        logger.info(
            f"Scanned file {file_id} with context-aware engine: "
            f"{document_context.get('type', 'unknown')} document, "
            f"masked {len(explanations)} fields"
        )
        
        # Return OCR text for image files (for frontend preview)
        return text if is_image else None
    
    except Exception as e:
        logger.error(f"Scan error for {file_id}: {e}")
        return None


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
    
    # Get detections (legacy)
    detections_doc = await db.detections.find_one({"file_id": file_id})
    
    # Get context-aware analysis
    context_doc = await db.context_analysis.find_one({"file_id": file_id})
    
    return {
        "file": file_doc,
        "detections": detections_doc.get("detections", []) if detections_doc else [],
        "context_analysis": context_doc if context_doc else None
    }


@router.get("/files/{file_id}/context-analysis", response_model=ContextAwareAnalysisResult)
async def get_context_analysis(
    file_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get context-aware analysis results for a file.
    
    Returns document type, detected fields, masking explanations, and summary.
    """
    context_doc = await db.context_analysis.find_one({"file_id": file_id})
    
    if not context_doc:
        raise HTTPException(
            status_code=404, 
            detail="Context analysis not found. File may not have been processed with context-aware engine."
        )
    
    # Build response
    document_context = DocumentTypeInfo(
        type=context_doc.get('document_type', 'unknown'),
        confidence=context_doc.get('document_confidence', 0.0),
        keywords=context_doc.get('keywords', []),
        reasoning=context_doc.get('reasoning', '')
    )
    
    detected_fields = [
        SemanticFieldInfo(**field)
        for field in context_doc.get('detected_fields', [])
    ]
    
    explanations = [
        MaskingExplanation(**exp)
        for exp in context_doc.get('explanations', [])
    ]
    
    summary = context_doc.get('summary', {})
    
    return ContextAwareAnalysisResult(
        document_context=document_context,
        detected_fields=detected_fields,
        masked_text=None,  # Don't send full text in response
        explanations=explanations,
        summary=summary
    )


@router.get("/files/{file_id}/masking-explanation")
async def get_masking_explanation(
    file_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get detailed explanation of why fields were masked in a document.
    
    This endpoint provides transparency about the masking decisions.
    """
    file_doc = await db.files.find_one({"file_id": file_id})
    
    if not file_doc:
        raise HTTPException(status_code=404, detail="File not found")
    
    context_doc = await db.context_analysis.find_one({"file_id": file_id})
    
    if not context_doc:
        return {
            "file_id": file_id,
            "context_aware_processed": False,
            "message": "This file was processed with legacy rules, not context-aware engine"
        }
    
    return {
        "file_id": file_id,
        "filename": file_doc.get('original_filename'),
        "document_type": context_doc.get('document_type'),
        "document_confidence": context_doc.get('document_confidence'),
        "context_aware_processed": True,
        "total_fields_masked": len(context_doc.get('explanations', [])),
        "explanations": context_doc.get('explanations', []),
        "summary": context_doc.get('summary', {}),
        "reasoning": context_doc.get('reasoning', '')
    }
