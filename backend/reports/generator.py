"""Compliance report generator using ReportLab."""
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image
)
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid
import os
import logging
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.schemas import ReportMetadata

logger = logging.getLogger(__name__)


class ComplianceReportGenerator:
    """Generates PDF compliance reports."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.styles = getSampleStyleSheet()
        self._add_custom_styles()
    
    def _add_custom_styles(self):
        """Add custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=1  # Center
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=12,
            spaceBefore=12
        ))
        
        self.styles.add(ParagraphStyle(
            name='BodyText',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=12
        ))
    
    async def generate_report(
        self,
        company: str,
        department: Optional[str] = None,
        include_charts: bool = True,
        include_recommendations: bool = True
    ) -> ReportMetadata:
        """
        Generate comprehensive compliance report.
        
        Args:
            company: Company name
            department: Optional department filter
            include_charts: Whether to include charts
            include_recommendations: Whether to include recommendations
        
        Returns:
            ReportMetadata
        """
        report_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"compliance_report_{company}_{timestamp}.pdf"
        filepath = os.path.join("./storage/reports", filename)
        
        # Ensure reports directory exists
        os.makedirs("./storage/reports", exist_ok=True)
        
        # Create PDF document
        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Build story (content)
        story = []
        
        # Title page
        story.extend(self._create_title_page(company, department))
        
        # Executive summary
        summary_content = await self._create_executive_summary(company, department)
        story.extend(summary_content)
        
        # Company overview
        overview_content = await self._create_company_overview(company)
        story.extend(overview_content)
        
        # Department analysis
        if department:
            dept_content = await self._create_department_analysis(company, department)
            story.extend(dept_content)
        else:
            all_dept_content = await self._create_all_departments_analysis(company)
            story.extend(all_dept_content)
        
        # Charts
        if include_charts:
            charts_content = await self._create_charts_section(company, department)
            story.extend(charts_content)
        
        # Recommendations
        if include_recommendations:
            recs_content = await self._create_recommendations_section(company, department)
            story.extend(recs_content)
        
        # Compliance readiness
        compliance_content = await self._create_compliance_section(company)
        story.extend(compliance_content)
        
        # Build PDF
        doc.build(story)
        
        # Get file size
        file_size = os.path.getsize(filepath)
        
        # Create metadata
        metadata = ReportMetadata(
            report_id=report_id,
            company=company,
            department=department,
            generated_date=datetime.now(),
            file_path=filepath,
            file_size=file_size
        )
        
        # Store metadata in database
        await self.db.reports.insert_one(metadata.dict())
        
        logger.info(f"Generated report: {filename}")
        
        return metadata
    
    def _create_title_page(self, company: str, department: Optional[str]) -> List:
        """Create title page."""
        content = []
        
        # Title
        title = f"Data Security & Compliance Report"
        content.append(Paragraph(title, self.styles['CustomTitle']))
        content.append(Spacer(1, 0.5*inch))
        
        # Company and date
        info = f"<b>Company:</b> {company}<br/>"
        if department:
            info += f"<b>Department:</b> {department}<br/>"
        info += f"<b>Generated:</b> {datetime.now().strftime('%B %d, %Y at %H:%M')}<br/>"
        
        content.append(Paragraph(info, self.styles['BodyText']))
        content.append(Spacer(1, 0.5*inch))
        
        # Divider
        content.append(PageBreak())
        
        return content
    
    async def _create_executive_summary(self, company: str, department: Optional[str]) -> List:
        """Create executive summary section."""
        content = []
        
        content.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        
        # Get company analysis
        analysis = await self.db.analysis.find_one({
            "company": company,
            "department": department,
            "type": "company" if department is None else "department"
        })
        
        if analysis:
            total_files = analysis.get("total_files", 0)
            risk_score = analysis.get("risk_score", 0)
            classification_dist = analysis.get("classification_distribution", {})
            
            summary_text = f"""
            This report provides a comprehensive analysis of data security and compliance 
            status for <b>{company}</b>. 
            <br/><br/>
            <b>Key Findings:</b>
            <ul>
                <li>Total Files Analyzed: {total_files}</li>
                <li>Overall Risk Score: {risk_score:.1f}/100</li>
                <li>Restricted Files: {classification_dist.get('Restricted', 0)}</li>
                <li>Confidential Files: {classification_dist.get('Confidential', 0)}</li>
            </ul>
            <br/>
            The risk score is calculated based on the sensitivity classification distribution 
            and density of sensitive data detections. Scores above 60 indicate high risk requiring 
            immediate attention.
            """
            
            content.append(Paragraph(summary_text, self.styles['BodyText']))
        
        content.append(Spacer(1, 0.3*inch))
        
        return content
    
    async def _create_company_overview(self, company: str) -> List:
        """Create company overview section."""
        content = []
        
        content.append(Paragraph("Company Overview", self.styles['SectionHeader']))
        
        # Get data
        analysis = await self.db.analysis.find_one({
            "company": company,
            "department": None,
            "type": "company"
        })
        
        if analysis:
            dept_breakdown = analysis.get("department_breakdown", {})
            top_sensitive = analysis.get("top_sensitive_types", [])
            
            # Department table
            if dept_breakdown:
                content.append(Paragraph("<b>Files by Department:</b>", self.styles['BodyText']))
                
                table_data = [["Department", "File Count"]]
                for dept, count in dept_breakdown.items():
                    table_data.append([dept, str(count)])
                
                table = Table(table_data, colWidths=[3*inch, 2*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                content.append(table)
                content.append(Spacer(1, 0.3*inch))
            
            # Top sensitive data types
            if top_sensitive:
                content.append(Paragraph("<b>Most Common Sensitive Data Types:</b>", self.styles['BodyText']))
                
                table_data = [["Data Type", "Occurrences"]]
                for item in top_sensitive[:5]:
                    table_data.append([item['type'], str(item['count'])])
                
                table = Table(table_data, colWidths=[3*inch, 2*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                content.append(table)
        
        content.append(Spacer(1, 0.3*inch))
        
        return content
    
    async def _create_department_analysis(self, company: str, department: str) -> List:
        """Create department-specific analysis."""
        content = []
        
        content.append(Paragraph(f"Department Analysis: {department}", self.styles['SectionHeader']))
        
        # Get department files
        files = await self.db.files.find({
            "company": company,
            "department": department
        }).to_list(length=None)
        
        if files:
            content.append(Paragraph(
                f"Total files in {department}: {len(files)}",
                self.styles['BodyText']
            ))
        
        content.append(Spacer(1, 0.3*inch))
        
        return content
    
    async def _create_all_departments_analysis(self, company: str) -> List:
        """Create analysis for all departments."""
        content = []
        
        content.append(Paragraph("Department Risk Analysis", self.styles['SectionHeader']))
        
        # Get all departments
        departments = await self.db.files.distinct("department", {"company": company})
        
        if departments:
            table_data = [["Department", "Total Files", "Risk Level"]]
            
            from collections import defaultdict
            for dept in departments:
                files = await self.db.files.find({
                    "company": company,
                    "department": dept
                }).to_list(length=None)
                
                classification_dist = defaultdict(int)
                for file in files:
                    classification_dist[file.get("classification", "Public")] += 1
                
                # Simple risk calculation
                risk_level = "Low"
                if classification_dist.get("Restricted", 0) > 0:
                    risk_level = "High"
                elif classification_dist.get("Confidential", 0) > len(files) * 0.3:
                    risk_level = "Medium"
                
                table_data.append([dept, str(len(files)), risk_level])
            
            table = Table(table_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            content.append(table)
        
        content.append(Spacer(1, 0.3*inch))
        
        return content
    
    async def _create_charts_section(self, company: str, department: Optional[str]) -> List:
        """Create charts section."""
        content = []
        
        content.append(PageBreak())
        content.append(Paragraph("Data Visualization", self.styles['SectionHeader']))
        
        # Get analysis data
        analysis = await self.db.analysis.find_one({
            "company": company,
            "department": department,
            "type": "company" if department is None else "department"
        })
        
        if analysis:
            classification_dist = analysis.get("classification_distribution", {})
            
            if classification_dist:
                # Create pie chart for classification distribution
                drawing = Drawing(400, 200)
                pie = Pie()
                pie.x = 150
                pie.y = 50
                pie.width = 100
                pie.height = 100
                
                pie.data = list(classification_dist.values())
                pie.labels = list(classification_dist.keys())
                pie.slices.strokeWidth = 0.5
                
                # Color scheme
                colors_list = [
                    colors.HexColor('#27ae60'),  # Green for Public
                    colors.HexColor('#3498db'),  # Blue for Internal
                    colors.HexColor('#f39c12'),  # Orange for Confidential
                    colors.HexColor('#e74c3c')   # Red for Restricted
                ]
                
                for i, color in enumerate(colors_list[:len(pie.data)]):
                    pie.slices[i].fillColor = color
                
                drawing.add(pie)
                content.append(drawing)
                content.append(Spacer(1, 0.3*inch))
        
        return content
    
    async def _create_recommendations_section(self, company: str, department: Optional[str]) -> List:
        """Create recommendations section."""
        content = []
        
        content.append(PageBreak())
        content.append(Paragraph("Security Recommendations", self.styles['SectionHeader']))
        
        # Get recommendations
        query = {"company": company}
        if department:
            query["department"] = department
        
        recommendations = await self.db.recommendations.find(query).to_list(length=None)
        
        if recommendations:
            for i, rec in enumerate(recommendations[:10], 1):
                priority = rec.get("priority", "Medium")
                title = rec.get("title", "")
                description = rec.get("description", "")
                action_items = rec.get("action_items", [])
                
                # Priority color
                priority_color = {
                    "High": colors.HexColor('#e74c3c'),
                    "Medium": colors.HexColor('#f39c12'),
                    "Low": colors.HexColor('#3498db')
                }.get(priority, colors.black)
                
                rec_text = f"""
                <b>{i}. {title}</b> 
                [<font color="{priority_color.hexval()}">Priority: {priority}</font>]
                <br/>
                {description}
                <br/>
                <b>Recommended Actions:</b>
                """
                
                content.append(Paragraph(rec_text, self.styles['BodyText']))
                
                # Action items as bullet points
                for action in action_items[:4]:
                    content.append(Paragraph(f"• {action}", self.styles['BodyText']))
                
                content.append(Spacer(1, 0.2*inch))
        else:
            content.append(Paragraph(
                "No specific recommendations at this time. Continue monitoring.",
                self.styles['BodyText']
            ))
        
        return content
    
    async def _create_compliance_section(self, company: str) -> List:
        """Create compliance readiness section."""
        content = []
        
        content.append(PageBreak())
        content.append(Paragraph("Compliance Readiness Summary", self.styles['SectionHeader']))
        
        # Get analysis
        analysis = await self.db.analysis.find_one({
            "company": company,
            "department": None,
            "type": "company"
        })
        
        if analysis:
            risk_score = analysis.get("risk_score", 0)
            
            # Determine compliance status
            if risk_score < 30:
                status = "Good"
                status_color = colors.green
                message = "Your organization demonstrates good data security practices."
            elif risk_score < 60:
                status = "Fair"
                status_color = colors.orange
                message = "Some improvements needed to enhance data security posture."
            else:
                status = "Needs Improvement"
                status_color = colors.red
                message = "Immediate action required to address security risks."
            
            compliance_text = f"""
            <b>Overall Compliance Status:</b> 
            <font color="{status_color.hexval()}">{status}</font>
            <br/><br/>
            <b>Risk Score:</b> {risk_score:.1f}/100
            <br/><br/>
            {message}
            <br/><br/>
            <b>Next Steps:</b>
            <ul>
                <li>Review and implement security recommendations</li>
                <li>Conduct regular security audits</li>
                <li>Update data handling policies</li>
                <li>Train employees on data security best practices</li>
            </ul>
            """
            
            content.append(Paragraph(compliance_text, self.styles['BodyText']))
        
        content.append(Spacer(1, 0.3*inch))
        
        # Footer
        content.append(Paragraph(
            f"<i>Report generated by SmartCloud Vault - {datetime.now().strftime('%Y')}</i>",
            self.styles['BodyText']
        ))
        
        return content
