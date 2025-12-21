"""Analysis engine for company and department level insights."""
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import defaultdict
import logging
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.schemas import (
    CompanyAnalysisResult, DepartmentAnalysisResult,
    Classification, AnalysisFilter
)

logger = logging.getLogger(__name__)


class CompanyAnalyzer:
    """Analyzes files at company level."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def analyze_company(
        self, 
        company: str,
        filters: Optional[AnalysisFilter] = None
    ) -> CompanyAnalysisResult:
        """
        Perform company-level analysis.
        
        Args:
            company: Company name
            filters: Optional filters for analysis
        
        Returns:
            CompanyAnalysisResult with comprehensive metrics
        """
        # Build query
        query = {"company": company}
        
        if filters:
            if filters.start_date:
                query["upload_date"] = {"$gte": filters.start_date}
            if filters.end_date:
                if "upload_date" in query:
                    query["upload_date"]["$lte"] = filters.end_date
                else:
                    query["upload_date"] = {"$lte": filters.end_date}
        
        # Get all files for this company
        files = await self.db.files.find(query).to_list(length=None)
        
        if not files:
            return CompanyAnalysisResult(
                company=company,
                total_files=0,
                classification_distribution={},
                department_breakdown={},
                top_sensitive_types=[],
                risk_score=0.0,
                last_updated=datetime.now()
            )
        
        # Calculate metrics
        total_files = len(files)
        
        # Classification distribution
        classification_dist = defaultdict(int)
        for file in files:
            classification = file.get("classification", "Public")
            classification_dist[classification] += 1
        
        # Department breakdown
        department_breakdown = defaultdict(int)
        for file in files:
            dept = file.get("department", "Unknown")
            department_breakdown[dept] += 1
        
        # Get all detections for these files
        file_ids = [f["file_id"] for f in files]
        detections = await self.db.detections.find(
            {"file_id": {"$in": file_ids}}
        ).to_list(length=None)
        
        # Count sensitive data types
        sensitive_type_counts = defaultdict(int)
        for detection in detections:
            for det in detection.get("detections", []):
                sensitive_type_counts[det["detection_type"]] += 1
        
        # Sort and get top 10
        top_sensitive_types = [
            {"type": k, "count": v}
            for k, v in sorted(
                sensitive_type_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        ]
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(
            classification_dist,
            total_files,
            len(detections)
        )
        
        result = CompanyAnalysisResult(
            company=company,
            total_files=total_files,
            classification_distribution=dict(classification_dist),
            department_breakdown=dict(department_breakdown),
            top_sensitive_types=top_sensitive_types,
            risk_score=risk_score,
            last_updated=datetime.now()
        )
        
        # Cache the result
        await self._cache_analysis(company, None, result.dict())
        
        logger.info(f"Completed analysis for company: {company}")
        
        return result
    
    def _calculate_risk_score(
        self, 
        classification_dist: Dict[str, int],
        total_files: int,
        total_detections: int
    ) -> float:
        """
        Calculate risk score (0-100).
        
        Based on:
        - Percentage of Restricted files
        - Percentage of Confidential files
        - Total detections per file ratio
        """
        if total_files == 0:
            return 0.0
        
        # Classification-based score (0-60)
        restricted_pct = classification_dist.get("Restricted", 0) / total_files
        confidential_pct = classification_dist.get("Confidential", 0) / total_files
        
        classification_score = (restricted_pct * 40 + confidential_pct * 20) * 100
        
        # Detection density score (0-40)
        detections_per_file = total_detections / total_files
        density_score = min(detections_per_file * 5, 40)
        
        total_score = classification_score + density_score
        
        return round(min(total_score, 100), 2)
    
    async def _cache_analysis(self, company: str, department: Optional[str], data: dict):
        """Cache analysis results in database."""
        await self.db.analysis.update_one(
            {
                "company": company,
                "department": department,
                "type": "company" if department is None else "department"
            },
            {
                "$set": {
                    **data,
                    "timestamp": datetime.now()
                }
            },
            upsert=True
        )


class DepartmentAnalyzer:
    """Analyzes files at department level."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def analyze_department(
        self,
        company: str,
        department: str,
        filters: Optional[AnalysisFilter] = None
    ) -> DepartmentAnalysisResult:
        """
        Perform department-level analysis.
        
        Args:
            company: Company name
            department: Department name
            filters: Optional filters
        
        Returns:
            DepartmentAnalysisResult with metrics
        """
        # Build query
        query = {
            "company": company,
            "department": department
        }
        
        if filters:
            if filters.start_date:
                query["upload_date"] = {"$gte": filters.start_date}
            if filters.end_date:
                if "upload_date" in query:
                    query["upload_date"]["$lte"] = filters.end_date
                else:
                    query["upload_date"] = {"$lte": filters.end_date}
        
        # Get files
        files = await self.db.files.find(query).to_list(length=None)
        
        if not files:
            return DepartmentAnalysisResult(
                company=company,
                department=department,
                total_files=0,
                classification_distribution={},
                sensitive_data_summary={},
                risk_score=0.0,
                recommendations_count=0
            )
        
        total_files = len(files)
        
        # Classification distribution
        classification_dist = defaultdict(int)
        for file in files:
            classification = file.get("classification", "Public")
            classification_dist[classification] += 1
        
        # Get detections
        file_ids = [f["file_id"] for f in files]
        detections = await self.db.detections.find(
            {"file_id": {"$in": file_ids}}
        ).to_list(length=None)
        
        # Summarize sensitive data types
        sensitive_data_summary = defaultdict(int)
        for detection in detections:
            for det in detection.get("detections", []):
                sensitive_data_summary[det["detection_type"]] += 1
        
        # Calculate risk score
        risk_score = self._calculate_department_risk(
            classification_dist,
            total_files,
            len(detections)
        )
        
        # Get recommendations count
        recommendations = await self.db.recommendations.count_documents({
            "company": company,
            "department": department
        })
        
        return DepartmentAnalysisResult(
            company=company,
            department=department,
            total_files=total_files,
            classification_distribution=dict(classification_dist),
            sensitive_data_summary=dict(sensitive_data_summary),
            risk_score=risk_score,
            recommendations_count=recommendations
        )
    
    def _calculate_department_risk(
        self,
        classification_dist: Dict[str, int],
        total_files: int,
        total_detections: int
    ) -> float:
        """Calculate department risk score (0-100)."""
        if total_files == 0:
            return 0.0
        
        restricted_pct = classification_dist.get("Restricted", 0) / total_files
        confidential_pct = classification_dist.get("Confidential", 0) / total_files
        
        classification_score = (restricted_pct * 50 + confidential_pct * 25) * 100
        
        detections_per_file = total_detections / total_files
        density_score = min(detections_per_file * 5, 50)
        
        return round(min(classification_score + density_score, 100), 2)
    
    async def get_all_departments_analysis(self, company: str) -> List[DepartmentAnalysisResult]:
        """Get analysis for all departments in a company."""
        # Get unique departments
        departments = await self.db.files.distinct("department", {"company": company})
        
        results = []
        for dept in departments:
            result = await self.analyze_department(company, dept)
            results.append(result)
        
        return results


class AnalysisEngine:
    """Main analysis engine."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.company_analyzer = CompanyAnalyzer(db)
        self.department_analyzer = DepartmentAnalyzer(db)
    
    async def analyze_company(self, company: str, filters: Optional[AnalysisFilter] = None):
        """Analyze company."""
        return await self.company_analyzer.analyze_company(company, filters)
    
    async def analyze_department(
        self, 
        company: str, 
        department: str, 
        filters: Optional[AnalysisFilter] = None
    ):
        """Analyze department."""
        return await self.department_analyzer.analyze_department(company, department, filters)
    
    async def get_all_companies(self, db: AsyncIOMotorDatabase) -> List[str]:
        """Get list of all companies."""
        return await db.files.distinct("company")
