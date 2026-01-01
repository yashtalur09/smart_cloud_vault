"""Pydantic models for request/response schemas."""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class SourceType(str, Enum):
    """File source type enumeration."""
    TEXT = "text"
    IMAGE = "image"


class Department(str, Enum):
    """Department enumeration."""
    HR = "HR"
    FINANCE = "Finance"
    SALES = "Sales"
    IT = "IT"
    LEGAL = "Legal"
    MARKETING = "Marketing"
    OPERATIONS = "Operations"


class Classification(str, Enum):
    """File classification levels."""
    PUBLIC = "Public"
    INTERNAL = "Internal"
    CONFIDENTIAL = "Confidential"
    RESTRICTED = "Restricted"


class DetectionType(str, Enum):
    """Types of sensitive data detection."""
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    CREDIT_CARD = "CREDIT_CARD"
    SSN = "SSN"
    PERSON = "PERSON"
    ORGANIZATION = "ORG"
    LOCATION = "GPE"
    PASSWORD = "PASSWORD"
    NATIONAL_ID = "NATIONAL_ID"


class FileUploadRequest(BaseModel):
    """File upload metadata."""
    company: str = Field(..., description="Company name")
    department: Department = Field(..., description="Department")
    uploader_email: str = Field(..., description="Uploader email address")
    uploader_name: Optional[str] = Field(None, description="Uploader name (optional)")


class DetectionResult(BaseModel):
    """Individual sensitive data detection."""
    detection_type: str = Field(..., description="Type of detection")
    value: str = Field(..., description="Detected value")
    start: int = Field(..., description="Start position in text")
    end: int = Field(..., description="End position in text")
    confidence: float = Field(default=1.0, description="Detection confidence score")
    source: str = Field(..., description="Detection source (regex/spacy/transformer)")


class FileClassificationResult(BaseModel):
    """File classification result."""
    classification: Classification
    score: float = Field(..., description="Classification confidence score")
    reasoning: str = Field(..., description="Explanation for classification")


class ScanResult(BaseModel):
    """Complete scan result for a file."""
    file_id: str
    detections: List[DetectionResult]
    classification: FileClassificationResult
    scan_date: datetime
    total_detections: int
    sensitive_data_types: List[str]


class FileMetadata(BaseModel):
    """Complete file metadata."""
    file_id: str
    original_filename: str
    company: str
    department: Department
    file_size: int
    upload_date: datetime
    classification: Optional[Classification] = None
    is_protected: bool = False
    scan_completed: bool = False
    uploader_email: str
    uploader_name: Optional[str] = None
    masked_file_path: Optional[str] = None
    masked_fields: List[str] = []
    source_type: SourceType = SourceType.TEXT
    ocr_extracted: bool = False
    ocr_text_preview: Optional[str] = None
    
    # Employee fields (NEW)
    employee_id: Optional[str] = Field(None, description="Employee ID")
    employee_name: Optional[str] = Field(None, description="Employee name")
    employee_email: Optional[str] = Field(None, description="Employee email")
    document_name: Optional[str] = Field(None, description="Document type name (e.g., Aadhaar, PAN, DL)")
    
    # Storage backend fields (S3 or local)
    storage_type: Optional[str] = Field(None, description="Storage type: 'local' or 's3'")
    original_s3_key: Optional[str] = Field(None, description="S3 key for original file")
    masked_s3_key: Optional[str] = Field(None, description="S3 key for masked file")
    original_bucket: Optional[str] = Field(None, description="S3 bucket for original file")
    masked_bucket: Optional[str] = Field(None, description="S3 bucket for masked file")


class ProtectionRequest(BaseModel):
    """Request to protect a file."""
    file_id: str
    mask: bool = Field(default=True, description="Apply masking")
    encrypt: bool = Field(default=False, description="Apply encryption")


class AnalysisFilter(BaseModel):
    """Filters for analysis queries."""
    company: Optional[str] = None
    department: Optional[Department] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class CompanyAnalysisResult(BaseModel):
    """Company-level analysis result."""
    company: str
    total_files: int
    classification_distribution: Dict[str, int]
    department_breakdown: Dict[str, int]
    top_sensitive_types: List[Dict[str, Any]]
    risk_score: float
    last_updated: datetime


class DepartmentAnalysisResult(BaseModel):
    """Department-level analysis result."""
    company: str
    department: str
    total_files: int
    classification_distribution: Dict[str, int]
    sensitive_data_summary: Dict[str, int]
    risk_score: float
    recommendations_count: int


class Recommendation(BaseModel):
    """Policy recommendation."""
    id: str
    company: str
    department: Optional[str] = None
    priority: str = Field(..., description="High/Medium/Low")
    title: str
    description: str
    rationale: str
    action_items: List[str]
    created_date: datetime


class ReportGenerationRequest(BaseModel):
    """Request to generate compliance report."""
    company: str
    department: Optional[str] = None
    include_charts: bool = True
    include_recommendations: bool = True


class ReportMetadata(BaseModel):
    """Report metadata."""
    report_id: str
    company: str
    department: Optional[str] = None
    generated_date: datetime
    file_path: str
    file_size: int


class FileAccessRequest(BaseModel):
    """Request to access/download a file."""
    file_id: str = Field(..., description="File identifier")
    requester_email: str = Field(..., description="Email of person requesting file")


class UploadResponse(BaseModel):
    """Response after file upload."""
    success: bool
    file_id: str
    message: str
    metadata: FileMetadata
    ocr_extracted_text: Optional[str] = None


class DocumentTypeInfo(BaseModel):
    """Document type classification information."""
    type: str = Field(..., description="Document type (invoice, financial, hr, etc.)")
    confidence: float = Field(..., description="Classification confidence score")
    keywords: List[str] = Field(default=[], description="Matched keywords")
    reasoning: str = Field(..., description="Classification reasoning")


class SemanticFieldInfo(BaseModel):
    """Semantic field detection information."""
    name: str = Field(..., description="Field name/type")
    value_preview: str = Field(..., description="Preview of detected value")
    sensitivity: str = Field(..., description="Sensitivity level (low/medium/high/critical)")
    confidence: float = Field(..., description="Detection confidence")
    reason: str = Field(..., description="Why this field is sensitive")


class MaskingExplanation(BaseModel):
    """Explanation for a masked field."""
    field: str = Field(..., description="Field name")
    original_value: str = Field(..., description="Original value preview")
    masked_value: str = Field(..., description="Masked representation")
    reason: str = Field(..., description="Why this was masked")
    sensitivity: str = Field(..., description="Sensitivity level")
    confidence: float = Field(..., description="Confidence score")
    position: str = Field(..., description="Position in document")


class ContextAwareAnalysisResult(BaseModel):
    """Result from context-aware document analysis."""
    document_context: DocumentTypeInfo
    detected_fields: List[SemanticFieldInfo]
    masked_text: Optional[str] = Field(None, description="Masked document text")
    explanations: List[MaskingExplanation] = Field(default=[], description="Masking explanations")
    summary: Dict[str, Any] = Field(..., description="Analysis summary statistics")


class EnhancedFileMetadata(BaseModel):
    """File metadata with context-aware information."""
    file_id: str
    original_filename: str
    company: str
    department: Department
    file_size: int
    upload_date: datetime
    classification: Optional[Classification] = None
    is_protected: bool = False
    scan_completed: bool = False
    uploader_email: str
    uploader_name: Optional[str] = None
    masked_file_path: Optional[str] = None
    masked_fields: List[str] = []
    source_type: SourceType = SourceType.TEXT
    ocr_extracted: bool = False
    ocr_text_preview: Optional[str] = None
    
    # Storage backend fields (S3 or local)
    storage_type: Optional[str] = Field(None, description="Storage type: 'local' or 's3'")
    original_s3_key: Optional[str] = Field(None, description="S3 key for original file")
    masked_s3_key: Optional[str] = Field(None, description="S3 key for masked file")
    original_bucket: Optional[str] = Field(None, description="S3 bucket for original file")
    masked_bucket: Optional[str] = Field(None, description="S3 bucket for masked file")
    
    # Context-aware fields
    document_type: Optional[str] = Field(None, description="Detected document type")
    document_type_confidence: Optional[float] = Field(None, description="Document classification confidence")
    context_aware_processed: bool = Field(False, description="Whether context-aware engine was used")
    semantic_fields_count: Optional[int] = Field(None, description="Number of semantic fields detected")
    masking_explanations: List[MaskingExplanation] = Field(default=[], description="Why fields were masked")


class UserRole(str, Enum):
    """User role enumeration for access control."""
    EMPLOYEE = "employee"
    HR = "hr"
    ADMIN = "admin"
    AUDITOR = "auditor"


class EmployeeAccessRequest(BaseModel):
    """Request for employee to access their own documents."""
    employee_id: str = Field(..., description="Employee ID")
    employee_name: str = Field(..., description="Employee name")
    employee_email: str = Field(..., description="Employee email")
    file_id: str = Field(..., description="File ID to access")


class AuthorityAccessRequest(BaseModel):
    """Request for company authority to access employee documents."""
    name: str = Field(..., description="Authority name")
    email: str = Field(..., description="Authority email")
    role: UserRole = Field(..., description="Authority role (HR/Admin/Auditor)")
    employee_id: str = Field(..., description="Employee ID to access")
    file_id: str = Field(..., description="File ID to access")


class EmployeeFilesResponse(BaseModel):
    """Response containing employee's files."""
    employee_id: str
    employee_name: Optional[str] = None
    employee_email: Optional[str] = None
    files: List[Dict[str, Any]]
    total_count: int
