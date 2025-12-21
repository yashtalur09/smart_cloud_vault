"""Pydantic models for request/response schemas."""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


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
