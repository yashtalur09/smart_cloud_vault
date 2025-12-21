"""Recommendations API endpoints."""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
import logging

from storage.database import get_database
from recommendations.engine import PolicyRecommendationEngine
from models.schemas import Recommendation
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


@router.post("/generate")
async def generate_recommendations(
    company: str = Query(..., description="Company name"),
    department: Optional[str] = Query(None, description="Optional department"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Generate security policy recommendations.
    
    Args:
        company: Company name
        department: Optional department name
    
    Returns:
        List of recommendations
    """
    try:
        engine = PolicyRecommendationEngine(db)
        recommendations = await engine.generate_recommendations(company, department)
        
        return {
            "success": True,
            "count": len(recommendations),
            "recommendations": [rec.dict() for rec in recommendations]
        }
    
    except Exception as e:
        logger.error(f"Recommendation generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def get_recommendations(
    company: str = Query(..., description="Company name"),
    department: Optional[str] = Query(None, description="Optional department filter"),
    priority: Optional[str] = Query(None, description="Optional priority filter (High/Medium/Low)"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get stored recommendations.
    
    Args:
        company: Company name
        department: Optional department filter
        priority: Optional priority filter
    
    Returns:
        List of recommendations
    """
    try:
        engine = PolicyRecommendationEngine(db)
        recommendations = await engine.get_recommendations(company, department, priority)
        
        return {
            "count": len(recommendations),
            "recommendations": [rec.dict() for rec in recommendations]
        }
    
    except Exception as e:
        logger.error(f"Get recommendations error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{recommendation_id}")
async def get_recommendation_details(
    recommendation_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get detailed information about a specific recommendation."""
    rec = await db.recommendations.find_one({"id": recommendation_id})
    
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    
    return Recommendation(**rec).dict()
