"""File access and download API with email-based and role-based access control."""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import Optional, List
import logging
from io import BytesIO

from models.schemas import FileAccessRequest, EmployeeAccessRequest, AuthorityAccessRequest, EmployeeFilesResponse, UserRole
from storage.file_storage import file_storage
from storage.storage_factory import storage_manager
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
        storage_type = file_doc.get("storage_type", "local")
        
        # Check email match
        email_matches = (request.requester_email.lower() == uploader_email.lower())
        
        # Check if this is an image-based OCR file
        source_type = file_doc.get("source_type", "text")
        is_ocr_file = (source_type == "image")
        
        if email_matches:
            # Return original file
            logger.info(f"Access granted: {request.requester_email} matches uploader for {request.file_id}")
            
            # Get storage key for original file
            storage_key = file_doc.get("original_s3_key") if storage_type == "s3" else None
            file_content = await storage_manager.get_original(request.file_id, storage_key)
            file_type = "original"
        else:
            # Return masked file
            logger.info(f"Access restricted: {request.requester_email} != {uploader_email} for {request.file_id}, returning masked version")
            
            # Get storage key for masked file
            storage_key = file_doc.get("masked_s3_key") if storage_type == "s3" else None
            file_content = await storage_manager.get_masked(request.file_id, storage_key)
            file_type = "masked"
        
        if not file_content:
            # Fallback logic: if original file missing, try masked
            if file_type == "original":
                logger.warning(f"Original file not found for {request.file_id}, falling back to masked version")
                storage_key = file_doc.get("masked_s3_key") if storage_type == "s3" else None
                file_content = await storage_manager.get_masked(request.file_id, storage_key)
                file_type = "masked"
            
            if not file_content:
                raise HTTPException(status_code=404, detail=f"File not found (tried {file_type})")
        
        # For OCR files, always return as .txt (the OCR extracted text)
        if is_ocr_file:
            media_type = "text/plain"
            # Change extension to .txt for image-based files
            filename_base = original_filename.rsplit('.', 1)[0] if '.' in original_filename else original_filename
            if file_type == "masked":
                download_filename = f"{filename_base}_masked.txt"
            else:
                download_filename = f"{filename_base}.txt"
        else:
            # Determine content type for non-OCR files
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
                "X-Email-Match": str(email_matches),
                "X-Source-Type": source_type  # Indicate if this was OCR-processed
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


@router.post("/employee/access")
async def employee_access_file(
    request: EmployeeAccessRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Employee accesses their own files (ORIGINAL versions from original bucket).
    
    Validation:
    - Employee ID must exist in database
    - Employee name and email must match records
    
    Args:
        request: EmployeeAccessRequest with employee_id, employee_name, employee_email, file_id
    
    Returns:
        Original file content from S3 original bucket
    """
    try:
        # Validate email format
        if "@" not in request.employee_email or "." not in request.employee_email:
            raise HTTPException(status_code=400, detail="Invalid employee email format")
        
        # Get file metadata from database
        file_doc = await db.files.find_one({"file_id": request.file_id})
        
        if not file_doc:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Verify employee credentials match
        stored_employee_id = file_doc.get("employee_id")
        stored_employee_name = file_doc.get("employee_name")
        stored_employee_email = file_doc.get("employee_email")
        
        if not stored_employee_id:
            raise HTTPException(status_code=400, detail="File does not have employee information")
        
        # Log the comparison for debugging
        logger.debug(f"Validating employee access - Request: id={request.employee_id}, name={request.employee_name}, email={request.employee_email}")
        logger.debug(f"Stored in DB: id={stored_employee_id}, name={stored_employee_name}, email={stored_employee_email}")
        
        # Strict validation: all fields must match
        if request.employee_id != stored_employee_id:
            logger.warning(f"Employee ID mismatch: '{request.employee_id}' != '{stored_employee_id}'")
            raise HTTPException(status_code=403, detail=f"Employee ID does not match file records. Provided: '{request.employee_id}', Expected: '{stored_employee_id}'")
        
        if request.employee_name.lower() != stored_employee_name.lower():
            logger.warning(f"Employee name mismatch: '{request.employee_name}' != '{stored_employee_name}'")
            raise HTTPException(status_code=403, detail=f"Employee name does not match file records. Provided: '{request.employee_name}', Expected: '{stored_employee_name}'")
        
        if request.employee_email.lower() != stored_employee_email.lower():
            logger.warning(f"Employee email mismatch: '{request.employee_email}' != '{stored_employee_email}'")
            raise HTTPException(status_code=403, detail=f"Employee email does not match file records. Provided: '{request.employee_email}', Expected: '{stored_employee_email}'")
        
        logger.info(f"Employee access granted: {request.employee_id} accessing their own file {request.file_id}")
        
        # Get ORIGINAL file from S3 original bucket
        storage_type = file_doc.get("storage_type", "local")
        storage_key = file_doc.get("original_s3_key") if storage_type == "s3" else None
        file_content = await storage_manager.get_original(request.file_id, storage_key)
        
        if not file_content:
            raise HTTPException(status_code=404, detail="Original file not found")
        
        original_filename = file_doc.get("original_filename", "file")
        source_type = file_doc.get("source_type", "text")
        is_ocr_file = (source_type == "image")
        
        # Determine content type
        if is_ocr_file:
            media_type = "text/plain"
            filename_base = original_filename.rsplit('.', 1)[0] if '.' in original_filename else original_filename
            download_filename = f"{filename_base}.txt"
        else:
            filename_lower = original_filename.lower()
            if filename_lower.endswith('.pdf'):
                media_type = "application/pdf"
            elif filename_lower.endswith('.docx'):
                media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            elif filename_lower.endswith('.csv'):
                media_type = "text/csv"
            else:
                media_type = "text/plain"
            download_filename = original_filename
        
        # Return original file
        return StreamingResponse(
            BytesIO(file_content),
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{download_filename}"',
                "X-File-Type": "original",
                "X-Access-Type": "employee",
                "X-Employee-ID": request.employee_id
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Employee file access error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/authority/access")
async def authority_access_file(
    request: AuthorityAccessRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Company authority (HR/Admin/Auditor) accesses employee files (MASKED versions from masked bucket).
    
    Args:
        request: AuthorityAccessRequest with name, email, role, employee_id, file_id
    
    Returns:
        Masked file content from S3 masked bucket
    """
    try:
        # Validate email format
        if "@" not in request.email or "." not in request.email:
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        # Validate role
        if request.role not in [UserRole.HR, UserRole.ADMIN, UserRole.AUDITOR]:
            raise HTTPException(status_code=403, detail="Invalid role for authority access")
        
        # Get file metadata from database
        file_doc = await db.files.find_one({"file_id": request.file_id})
        
        if not file_doc:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Verify employee_id matches the file
        stored_employee_id = file_doc.get("employee_id")
        
        if not stored_employee_id:
            raise HTTPException(status_code=400, detail="File does not have employee information")
        
        if request.employee_id != stored_employee_id:
            raise HTTPException(status_code=403, detail="Employee ID does not match file records")
        
        logger.info(f"Authority access granted: {request.role.value} {request.name} accessing employee {request.employee_id} file {request.file_id}")
        
        # Get MASKED file from S3 masked bucket
        storage_type = file_doc.get("storage_type", "local")
        storage_key = file_doc.get("masked_s3_key") if storage_type == "s3" else None
        file_content = await storage_manager.get_masked(request.file_id, storage_key)
        
        if not file_content:
            # Do NOT fallback to original - authority should only access masked files
            logger.error(f"Masked file not found for {request.file_id} - this should not happen")
            raise HTTPException(status_code=404, detail="Masked file not found. File may not have been processed correctly.")
        
        original_filename = file_doc.get("original_filename", "file")
        source_type = file_doc.get("source_type", "text")
        is_ocr_file = (source_type == "image")
        
        # Determine content type
        if is_ocr_file:
            media_type = "text/plain"
            filename_base = original_filename.rsplit('.', 1)[0] if '.' in original_filename else original_filename
            download_filename = f"{filename_base}_masked.txt"
        else:
            filename_lower = original_filename.lower()
            if filename_lower.endswith('.pdf'):
                media_type = "application/pdf"
            elif filename_lower.endswith('.docx'):
                media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            elif filename_lower.endswith('.csv'):
                media_type = "text/csv"
            else:
                media_type = "text/plain"
            
            # Add _masked suffix to filename
            filename_parts = original_filename.rsplit('.', 1)
            if len(filename_parts) == 2:
                download_filename = f"{filename_parts[0]}_masked.{filename_parts[1]}"
            else:
                download_filename = f"{original_filename}_masked"
        
        # Return masked file
        return StreamingResponse(
            BytesIO(file_content),
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{download_filename}"',
                "X-File-Type": "masked",
                "X-Access-Type": "authority",
                "X-Authority-Role": request.role.value,
                "X-Employee-ID": request.employee_id
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authority file access error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/employee/files/{employee_id}")
async def list_employee_files(
    employee_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    List all files for a specific employee.
    
    Args:
        employee_id: Employee ID (case-insensitive)
    
    Returns:
        List of files belonging to the employee
    """
    try:
        # Find all files for this employee (case-insensitive search)
        cursor = db.files.find({"employee_id": {"$regex": f"^{employee_id}$", "$options": "i"}})
        files = await cursor.to_list(length=None)
        
        if not files:
            return EmployeeFilesResponse(
                employee_id=employee_id,
                employee_name=None,
                employee_email=None,
                files=[],
                total_count=0
            )
        
        # Get employee info from first file
        first_file = files[0]
        employee_name = first_file.get("employee_name")
        employee_email = first_file.get("employee_email")
        
        # Build file list
        file_list = []
        for file_doc in files:
            file_list.append({
                "file_id": file_doc.get("file_id"),
                "original_filename": file_doc.get("original_filename"),
                "document_name": file_doc.get("document_name"),
                "upload_date": file_doc.get("upload_date"),
                "file_size": file_doc.get("file_size"),
                "classification": file_doc.get("classification"),
                "is_protected": file_doc.get("is_protected", False),
                "masked_fields": file_doc.get("masked_fields", [])
            })
        
        return EmployeeFilesResponse(
            employee_id=employee_id,
            employee_name=employee_name,
            employee_email=employee_email,
            files=file_list,
            total_count=len(file_list)
        )
    
    except Exception as e:
        logger.error(f"Error listing employee files: {e}")
        raise HTTPException(status_code=500, detail=str(e))
