"""File classification logic."""
from typing import List, Dict
from models.schemas import DetectionResult, FileClassificationResult, Classification, DetectionType
import logging

logger = logging.getLogger(__name__)


class FileClassifier:
    """Classifies files based on sensitive data detections."""
    
    # Sensitivity weights for different detection types
    SENSITIVITY_WEIGHTS = {
        DetectionType.CREDIT_CARD.value: 10,
        DetectionType.SSN.value: 10,
        DetectionType.PASSWORD.value: 9,
        DetectionType.NATIONAL_ID.value: 8,
        DetectionType.PHONE.value: 5,
        DetectionType.EMAIL.value: 4,
        DetectionType.PERSON.value: 3,
        DetectionType.ORGANIZATION.value: 2,
        DetectionType.LOCATION.value: 1,
    }
    
    def classify(self, detections: List[DetectionResult]) -> FileClassificationResult:
        """
        Classify file based on detections.
        
        Classification levels:
        - Public: No sensitive data
        - Internal: Low-sensitivity data (ORG, GPE)
        - Confidential: Medium-sensitivity data (PERSON, EMAIL, PHONE)
        - Restricted: High-sensitivity data (CREDIT_CARD, SSN, PASSWORD)
        
        Args:
            detections: List of detected sensitive items
        
        Returns:
            FileClassificationResult
        """
        if not detections:
            return FileClassificationResult(
                classification=Classification.PUBLIC,
                score=1.0,
                reasoning="No sensitive data detected"
            )
        
        # Calculate sensitivity score
        total_score = 0
        detection_counts = {}
        
        for detection in detections:
            weight = self.SENSITIVITY_WEIGHTS.get(detection.detection_type, 1)
            total_score += weight * detection.confidence
            
            # Count detections by type
            detection_counts[detection.detection_type] = \
                detection_counts.get(detection.detection_type, 0) + 1
        
        # Normalize score
        max_possible_score = len(detections) * 10  # Max weight
        normalized_score = min(total_score / max(max_possible_score, 1), 1.0)
        
        # Determine classification
        classification, reasoning = self._determine_classification(
            normalized_score, detection_counts, len(detections)
        )
        
        logger.info(f"Classified as {classification.value} with score {normalized_score:.2f}")
        
        return FileClassificationResult(
            classification=classification,
            score=normalized_score,
            reasoning=reasoning
        )
    
    def _determine_classification(
        self, 
        score: float, 
        detection_counts: Dict[str, int],
        total_detections: int
    ) -> tuple:
        """Determine classification level and reasoning."""
        
        # Check for high-risk data types
        high_risk_types = {
            DetectionType.CREDIT_CARD.value,
            DetectionType.SSN.value,
            DetectionType.PASSWORD.value
        }
        
        has_high_risk = any(dt in detection_counts for dt in high_risk_types)
        
        if has_high_risk:
            high_risk_items = [dt for dt in high_risk_types if dt in detection_counts]
            return (
                Classification.RESTRICTED,
                f"Contains highly sensitive data: {', '.join(high_risk_items)}. "
                f"Total of {total_detections} sensitive items found."
            )
        
        # Check for medium-risk data
        medium_risk_types = {
            DetectionType.NATIONAL_ID.value,
            DetectionType.PHONE.value,
            DetectionType.EMAIL.value,
            DetectionType.PERSON.value
        }
        
        has_medium_risk = any(dt in detection_counts for dt in medium_risk_types)
        medium_risk_count = sum(
            detection_counts.get(dt, 0) for dt in medium_risk_types
        )
        
        if has_medium_risk and (medium_risk_count >= 5 or score > 0.3):
            medium_risk_items = [dt for dt in medium_risk_types if dt in detection_counts]
            return (
                Classification.CONFIDENTIAL,
                f"Contains confidential data: {', '.join(medium_risk_items)}. "
                f"Found {medium_risk_count} medium-sensitivity items."
            )
        
        # Low-risk data (mostly organizational info)
        if total_detections > 0:
            low_risk_items = list(detection_counts.keys())
            return (
                Classification.INTERNAL,
                f"Contains internal data: {', '.join(low_risk_items)}. "
                f"Low-sensitivity information only."
            )
        
        # No sensitive data
        return (
            Classification.PUBLIC,
            "No sensitive data detected"
        )


# Global classifier instance
classifier = FileClassifier()
