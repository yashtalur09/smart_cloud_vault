"""Reports API endpoints."""
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import FileResponse
from typing import Optional
import logging
import os

from storage.database import get_database
from reports.generator import ComplianceReportGenerator
from models.schemas import ReportGenerationRequest, ReportMetadata
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("/generate")
async def generate_report(
    company: str = Query(..., description="Company name"),
    department: Optional[str] = Query(None, description="Optional department"),
    include_charts: bool = Query(True, description="Include charts"),
    include_recommendations: bool = Query(True, description="Include recommendations"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Generate compliance report.
    
    Args:
        company: Company name
        department: Optional department filter
        include_charts: Whether to include charts
        include_recommendations: Whether to include recommendations
    
    Returns:
        Report metadata
    """
    try:
        generator = ComplianceReportGenerator(db)
        
        metadata = await generator.generate_report(
            company=company,
            department=department,
            include_charts=include_charts,
            include_recommendations=include_recommendations
        )
        
        return {
            "success": True,
            "message": "Report generated successfully",
            "report": metadata.dict()
        }
    
    except Exception as e:
        logger.error(f"Report generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{report_id}")
async def download_report(
    report_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Download generated report.
    
    Args:
        report_id: Report identifier
    
    Returns:
        PDF file
    """
    try:
        # Get report metadata
        report_doc = await db.reports.find_one({"report_id": report_id})
        
        if not report_doc:
            raise HTTPException(status_code=404, detail="Report not found")
        
        file_path = report_doc.get("file_path")
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Report file not found")
        
        filename = os.path.basename(file_path)
        
        return FileResponse(
            path=file_path,
            media_type="application/pdf",
            filename=filename
        )
    
    except Exception as e:
        logger.error(f"Download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_reports(
    company: Optional[str] = Query(None, description="Optional company filter"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get list of generated reports."""
    query = {}
    
    if company:
        query["company"] = company
    
    reports = await db.reports.find(query).sort("generated_date", -1).to_list(length=50)
    
    return {
        "count": len(reports),
        "reports": reports
    }
