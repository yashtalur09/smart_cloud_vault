"""Analysis API endpoints."""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
import logging

from storage.database import get_database
from analysis.analyzer import AnalysisEngine
from models.schemas import AnalysisFilter, Department
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.get("/company")
async def get_company_analysis(
    company: str = Query(..., description="Company name"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get company-level analysis.
    
    Args:
        company: Company name
    
    Returns:
        Company analysis results
    """
    try:
        engine = AnalysisEngine(db)
        result = await engine.analyze_company(company)
        
        return result.dict()
    
    except Exception as e:
        logger.error(f"Company analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/department")
async def get_department_analysis(
    company: str = Query(..., description="Company name"),
    department: str = Query(..., description="Department name"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get department-level analysis.
    
    Args:
        company: Company name
        department: Department name
    
    Returns:
        Department analysis results
    """
    try:
        engine = AnalysisEngine(db)
        result = await engine.analyze_department(company, department)
        
        return result.dict()
    
    except Exception as e:
        logger.error(f"Department analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/companies")
async def list_companies(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get list of all companies with data."""
    companies = await db.files.distinct("company")
    
    return {"companies": companies, "count": len(companies)}


@router.get("/departments")
async def list_departments(
    company: Optional[str] = Query(None, description="Optional company filter"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get list of departments."""
    query = {}
    
    if company:
        query["company"] = company
    
    departments = await db.files.distinct("department", query)
    
    return {"departments": departments, "count": len(departments)}


@router.get("/overview")
async def get_overview(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get system-wide overview statistics.
    
    Returns:
        Overall statistics across all companies
    """
    try:
        # Total files
        total_files = await db.files.count_documents({})
        
        # Total companies
        companies = await db.files.distinct("company")
        
        # Classification distribution
        from collections import defaultdict
        classification_dist = defaultdict(int)
        
        all_files = await db.files.find({}).to_list(length=None)
        for file in all_files:
            classification = file.get("classification", "Public")
            classification_dist[classification] += 1
        
        # Total detections
        total_detections = await db.detections.count_documents({})
        
        return {
            "total_files": total_files,
            "total_companies": len(companies),
            "total_detections": total_detections,
            "classification_distribution": dict(classification_dist),
            "companies": companies
        }
    
    except Exception as e:
        logger.error(f"Overview error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
