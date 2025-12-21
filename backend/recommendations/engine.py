"""Policy recommendation engine."""
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import logging
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.schemas import Recommendation, CompanyAnalysisResult, DepartmentAnalysisResult

logger = logging.getLogger(__name__)


class PolicyRecommendationEngine:
    """Generates security policy recommendations based on analysis."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def generate_recommendations(
        self,
        company: str,
        department: Optional[str] = None
    ) -> List[Recommendation]:
        """
        Generate policy recommendations.
        
        Args:
            company: Company name
            department: Optional department name
        
        Returns:
            List of recommendations
        """
        recommendations = []
        
        if department:
            # Department-specific recommendations
            recs = await self._generate_department_recommendations(company, department)
            recommendations.extend(recs)
        else:
            # Company-wide recommendations
            recs = await self._generate_company_recommendations(company)
            recommendations.extend(recs)
        
        # Store recommendations in database
        for rec in recommendations:
            await self._store_recommendation(rec)
        
        logger.info(f"Generated {len(recommendations)} recommendations for {company}")
        
        return recommendations
    
    async def _generate_company_recommendations(
        self,
        company: str
    ) -> List[Recommendation]:
        """Generate company-wide recommendations."""
        recommendations = []
        
        # Get company analysis
        company_analysis = await self.db.analysis.find_one({
            "company": company,
            "department": None,
            "type": "company"
        })
        
        if not company_analysis:
            return recommendations
        
        total_files = company_analysis.get("total_files", 0)
        classification_dist = company_analysis.get("classification_distribution", {})
        risk_score = company_analysis.get("risk_score", 0)
        
        if total_files == 0:
            return recommendations
        
        # Rule 1: High percentage of Restricted files
        restricted_count = classification_dist.get("Restricted", 0)
        restricted_pct = (restricted_count / total_files) * 100
        
        if restricted_pct > 20:
            recommendations.append(Recommendation(
                id=str(uuid.uuid4()),
                company=company,
                department=None,
                priority="High",
                title="Enable Mandatory Encryption for Restricted Files",
                description=(
                    f"{restricted_pct:.1f}% of your files are classified as Restricted. "
                    "These files contain highly sensitive data that requires encryption."
                ),
                rationale=(
                    f"With {restricted_count} Restricted files, there is significant risk "
                    "of data breach if files are accessed without proper protection."
                ),
                action_items=[
                    "Enable automatic encryption for all Restricted files",
                    "Implement access controls for encrypted files",
                    "Set up encryption key management system",
                    "Train employees on handling Restricted data"
                ],
                created_date=datetime.now()
            ))
        
        # Rule 2: High risk score
        if risk_score > 60:
            recommendations.append(Recommendation(
                id=str(uuid.uuid4()),
                company=company,
                department=None,
                priority="High",
                title="Implement Data Loss Prevention (DLP) Policy",
                description=(
                    f"Company risk score is {risk_score:.1f}/100, indicating high exposure "
                    "to data security risks."
                ),
                rationale=(
                    "High risk scores indicate the presence of significant amounts of "
                    "sensitive data that could lead to regulatory violations if exposed."
                ),
                action_items=[
                    "Conduct security audit of all departments",
                    "Implement DLP monitoring tools",
                    "Create incident response plan",
                    "Review and update data handling policies"
                ],
                created_date=datetime.now()
            ))
        
        # Rule 3: Multiple departments with sensitive data
        dept_breakdown = company_analysis.get("department_breakdown", {})
        if len(dept_breakdown) >= 3:
            recommendations.append(Recommendation(
                id=str(uuid.uuid4()),
                company=company,
                department=None,
                priority="Medium",
                title="Establish Department-Specific Security Policies",
                description=(
                    f"Sensitive data detected across {len(dept_breakdown)} departments. "
                    "Each department may require specialized security controls."
                ),
                rationale=(
                    "Different departments handle different types of sensitive data "
                    "requiring tailored security approaches."
                ),
                action_items=[
                    "Review each department's data handling needs",
                    "Create department-specific security guidelines",
                    "Assign data protection officers per department",
                    "Conduct regular department security training"
                ],
                created_date=datetime.now()
            ))
        
        return recommendations
    
    async def _generate_department_recommendations(
        self,
        company: str,
        department: str
    ) -> List[Recommendation]:
        """Generate department-specific recommendations."""
        recommendations = []
        
        # Get department analysis
        dept_query = {
            "company": company,
            "department": department
        }
        files = await self.db.files.find(dept_query).to_list(length=None)
        
        if not files:
            return recommendations
        
        total_files = len(files)
        
        # Get classification distribution
        from collections import defaultdict
        classification_dist = defaultdict(int)
        for file in files:
            classification_dist[file.get("classification", "Public")] += 1
        
        # Get detections
        file_ids = [f["file_id"] for f in files]
        all_detections = await self.db.detections.find(
            {"file_id": {"$in": file_ids}}
        ).to_list(length=None)
        
        # Count sensitive data types
        sensitive_types = defaultdict(int)
        for det_doc in all_detections:
            for det in det_doc.get("detections", []):
                sensitive_types[det["detection_type"]] += 1
        
        # Department-specific rules
        
        # HR Department
        if department.upper() == "HR":
            if sensitive_types.get("PERSON", 0) > 10:
                recommendations.append(Recommendation(
                    id=str(uuid.uuid4()),
                    company=company,
                    department=department,
                    priority="High",
                    title="Enable Auto-Masking for Personal Identifiable Information (PII)",
                    description=(
                        f"HR department has {sensitive_types['PERSON']} instances of "
                        "personal names detected. PII protection is critical."
                    ),
                    rationale=(
                        "GDPR and privacy regulations require strict protection of "
                        "employee personal information."
                    ),
                    action_items=[
                        "Enable automatic PII masking for HR documents",
                        "Implement role-based access to unmasked data",
                        "Conduct GDPR compliance review",
                        "Update employee data handling procedures"
                    ],
                    created_date=datetime.now()
                ))
        
        # Finance Department
        if department.upper() == "FINANCE":
            if sensitive_types.get("CREDIT_CARD", 0) > 0 or sensitive_types.get("SSN", 0) > 0:
                recommendations.append(Recommendation(
                    id=str(uuid.uuid4()),
                    company=company,
                    department=department,
                    priority="High",
                    title="Implement PCI-DSS Compliance Measures",
                    description=(
                        "Finance department handles credit card and/or SSN data. "
                        "PCI-DSS compliance is mandatory."
                    ),
                    rationale=(
                        "Payment card data requires stringent security controls to "
                        "prevent fraud and maintain compliance."
                    ),
                    action_items=[
                        "Enable encryption for all financial documents",
                        "Implement secure card data handling procedures",
                        "Conduct PCI-DSS compliance audit",
                        "Restrict access to financial data"
                    ],
                    created_date=datetime.now()
                ))
        
        # General: High percentage of Confidential files
        confidential_pct = (classification_dist.get("Confidential", 0) / total_files) * 100
        if confidential_pct > 30:
            recommendations.append(Recommendation(
                id=str(uuid.uuid4()),
                company=company,
                department=department,
                priority="Medium",
                title="Restrict Access to Confidential Files",
                description=(
                    f"{confidential_pct:.1f}% of {department} files are Confidential. "
                    "Access controls should be tightened."
                ),
                rationale=(
                    "Confidential files contain sensitive business information that "
                    "should only be accessible to authorized personnel."
                ),
                action_items=[
                    "Review and update access control lists",
                    "Implement multi-factor authentication",
                    "Enable audit logging for file access",
                    "Set up alerts for unauthorized access attempts"
                ],
                created_date=datetime.now()
            ))
        
        return recommendations
    
    async def _store_recommendation(self, recommendation: Recommendation):
        """Store recommendation in database."""
        await self.db.recommendations.update_one(
            {"id": recommendation.id},
            {"$set": recommendation.dict()},
            upsert=True
        )
    
    async def get_recommendations(
        self,
        company: str,
        department: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[Recommendation]:
        """
        Retrieve stored recommendations.
        
        Args:
            company: Company name
            department: Optional department filter
            priority: Optional priority filter (High/Medium/Low)
        
        Returns:
            List of recommendations
        """
        query = {"company": company}
        
        if department:
            query["department"] = department
        
        if priority:
            query["priority"] = priority
        
        recs = await self.db.recommendations.find(query).sort(
            "created_date", -1
        ).to_list(length=None)
        
        return [Recommendation(**rec) for rec in recs]
