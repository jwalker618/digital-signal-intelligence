from abc import ABC, abstractmethod
from typing import Any, Dict, List, Type, Optional

# ----------------------------
# Registry
# ----------------------------

CATEGORIZER_REGISTRY: Dict[str, Type["DataCategorizer"]] = {}

def register_categorizer(cls: Type["DataCategorizer"]) -> Type["DataCategorizer"]:
    """Register a data categorizer/scorer class."""
    CATEGORIZER_REGISTRY[cls.__name__] = cls
    return cls

# ----------------------------
# Base Class
# ----------------------------

class DataCategorizer(ABC):
    """
    Base class for data categorizers/scorers.
    Takes aggregated data and produces classifications, scores, or categories.
    """
    @abstractmethod
    def categorize(self, coverage, cov_configuration, aggregated_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Categorize or score the aggregated data.
        
        Args:
            coverage: the specific coverage handed into the categoriser from technical_pricing/coverages/##/config.yaml
            cov_configuration: the specific configuration definition under the coverage handed into the categoriser from technical_pricing/coverages/##/config.yaml
            aggregated_data: Standardised data from an aggregator
            
        Returns:
            Category, score, or classification result
        """
        raise NotImplementedError
    
    def get_categorizer_metadata(self) -> Dict[str, str]:
        """Optional: Return metadata about the categorizer."""
        return {
            "categorizer_type": self.__class__.__name__,
            "version": "1.0"
        }

# ----------------------------
# Implementations: Maritime Domain
# ----------------------------

# CATEGORIZERS
@register_categorizer
class CompanySizeCategorizer(DataCategorizer):
    """
    Categorizes companies by fleet size.
    """
    
    def __init__(self, small_threshold: int = 10, medium_threshold: int = 30, large_threshold: int = 50):
        self.small_threshold = small_threshold
        self.medium_threshold = medium_threshold
        self.large_threshold = large_threshold
    
    def categorize(self, aggregated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Categorize by fleet size."""
        fleet_size = aggregated_data.get("total_vessels", 0)
        
        if fleet_size < self.small_threshold:
            category = "small"
        elif fleet_size < self.medium_threshold:
            category = "medium"
        elif fleet_size < self.large_threshold:
            category = "large"
        else:
            category = "major"
        
        return {
            "company_name": aggregated_data.get("company_name"),
            "size_category": category,
            "fleet_size": fleet_size,
            "thresholds": {
                "small": f"< {self.small_threshold}",
                "medium": f"{self.small_threshold}-{self.medium_threshold-1}",
                "large": f"{self.medium_threshold}-{self.large_threshold-1}",
                "major": f">= {self.large_threshold}"
            }
        }


@register_categorizer
class OperatorTypeCategorizer(DataCategorizer):
    """
    Categorizes shipping companies by operational type:
    - Major Liner: Container-focused, large fleet, offers liner service
    - Major Tanker: Tanker-focused, medium+ fleet
    - Specialized: Single vessel type dominance
    - Diversified: Multiple vessel types with no clear dominance
    """
    
    def __init__(self, liner_fleet_threshold: int = 50, tanker_fleet_threshold: int = 30, 
                 dominance_threshold: float = 0.6):
        self.liner_fleet_threshold = liner_fleet_threshold
        self.tanker_fleet_threshold = tanker_fleet_threshold
        self.dominance_threshold = dominance_threshold
    
    def categorize(self, aggregated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Categorize by operator type."""
        fleet_size = aggregated_data.get("total_vessels", 0)
        dominant_cat = aggregated_data.get("dominant_category")
        dominance_ratio = aggregated_data.get("dominance_ratio", 0.0)
        offers_liner = aggregated_data.get("offers_liner_service", False)
        
        category = "uncategorized"
        reasons: List[str] = []
        confidence = 0.0
        
        # Major Liner classification
        if (dominant_cat == "container" and 
            fleet_size >= self.liner_fleet_threshold and 
            offers_liner):
            category = "major_liner"
            confidence = min(0.9, dominance_ratio + 0.2)
            reasons = [
                f"Container dominance ({dominance_ratio:.0%})",
                f"Fleet size >= {self.liner_fleet_threshold}",
                "Offers liner service"
            ]
        
        # Major Tanker classification
        elif dominant_cat == "tanker" and fleet_size >= self.tanker_fleet_threshold:
            category = "major_tanker"
            confidence = min(0.9, dominance_ratio + 0.1)
            reasons = [
                f"Tanker dominance ({dominance_ratio:.0%})",
                f"Fleet size >= {self.tanker_fleet_threshold}"
            ]
        
        # Specialized operator
        elif dominance_ratio >= self.dominance_threshold and fleet_size >= 5:
            category = "specialized"
            confidence = dominance_ratio
            reasons = [
                f"{dominant_cat.title()} dominance ({dominance_ratio:.0%})",
                f"Above dominance threshold ({self.dominance_threshold:.0%})"
            ]
        
        # Diversified operator
        elif dominant_cat == "mixed" or dominance_ratio < self.dominance_threshold:
            category = "diversified"
            confidence = 1.0 - dominance_ratio
            reasons = [
                f"No clear vessel type dominance ({dominance_ratio:.0%})",
                "Multi-vessel portfolio"
            ]
        
        else:
            reasons = [
                f"Dominant category: {dominant_cat}",
                f"Fleet size: {fleet_size}",
                f"Liner service: {offers_liner}",
                f"Dominance ratio: {dominance_ratio:.0%}"
            ]
        
        return {
            "company_name": aggregated_data.get("company_name"),
            "operator_type": category,
            "confidence": round(confidence, 2),
            "classification_reasons": reasons,
            "supporting_data": {
                "dominant_category": dominant_cat,
                "fleet_size": fleet_size,
                "dominance_ratio": dominance_ratio,
                "offers_liner_service": offers_liner
            }
        }


@register_categorizer
class FleetModernityScorer(DataCategorizer):
    """
    Scores fleet modernity based on average age.
    """
    
    def __init__(self, modern_threshold: float = 5.0, aging_threshold: float = 15.0):
        self.modern_threshold = modern_threshold
        self.aging_threshold = aging_threshold
    
    def categorize(self, aggregated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Score fleet modernity."""
        avg_age = aggregated_data.get("average_fleet_age", 0.0)
        
        if avg_age <= self.modern_threshold:
            rating = "modern"
            score = 100
        elif avg_age <= self.aging_threshold:
            rating = "moderate"
            # Linear interpolation
            score = int(100 - ((avg_age - self.modern_threshold) / 
                              (self.aging_threshold - self.modern_threshold)) * 50)
        else:
            rating = "aging"
            score = max(0, int(50 - (avg_age - self.aging_threshold) * 2))
        
        return {
            "company_name": aggregated_data.get("company_name"),
            "modernity_rating": rating,
            "modernity_score": score,
            "average_fleet_age": avg_age,
            "assessment": f"{rating.title()} fleet ({avg_age:.1f} years avg)"
        }


@register_categorizer
class RiskProfileCategorizer(DataCategorizer):
    """
    Assesses operational risk profile based on multiple factors.
    """
    
    def categorize(self, aggregated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate risk profile."""
        fleet_size = aggregated_data.get("total_vessels", 0)
        avg_age = aggregated_data.get("average_fleet_age", 0.0)
        dominant_cat = aggregated_data.get("dominant_category")
        dominance_ratio = aggregated_data.get("dominance_ratio", 0.0)
        
        risk_score = 0
        risk_factors: List[str] = []
        
        # Fleet size risk (smaller = higher risk)
        if fleet_size < 5:
            risk_score += 30
            risk_factors.append("Very small fleet (<5 vessels)")
        elif fleet_size < 15:
            risk_score += 15
            risk_factors.append("Small fleet (<15 vessels)")
        
        # Age risk
        if avg_age > 20:
            risk_score += 30
            risk_factors.append(f"Aging fleet ({avg_age:.1f} years)")
        elif avg_age > 15:
            risk_score += 15
            risk_factors.append(f"Moderately old fleet ({avg_age:.1f} years)")
        
        # Diversification risk
        if dominance_ratio > 0.9:
            risk_score += 20
            risk_factors.append("Highly concentrated fleet")
        elif dominance_ratio < 0.4:
            risk_score += 10
            risk_factors.append("Highly diversified (may lack focus)")
        
        # Determine risk level
        if risk_score >= 50:
            risk_level = "high"
        elif risk_score >= 25:
            risk_level = "moderate"
        else:
            risk_level = "low"
        
        return {
            "company_name": aggregated_data.get("company_name"),
            "risk_level": risk_level,
            "risk_score": risk_score,
            "risk_factors": risk_factors if risk_factors else ["No significant risk factors identified"],
            "recommendation": self._get_recommendation(risk_level)
        }
    
    def _get_recommendation(self, risk_level: str) -> str:
        recommendations = {
            "high": "Requires detailed due diligence and enhanced monitoring",
            "moderate": "Standard due diligence recommended",
            "low": "Suitable for streamlined review process"
        }
        return recommendations.get(risk_level, "Review required")
    
