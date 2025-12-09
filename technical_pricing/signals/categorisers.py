from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from typing import TypedDict

# ---------------- REGISTRY ----------------
CATEGORIZER_REGISTRY: Dict[str, Type["DataCategorizer"]] = {}

def register_categorizer(cls: Type["DataCategorizer"]) -> Type["DataCategorizer"]:
    """Register a data categorizer/scorer class by its class name."""
    CATEGORIZER_REGISTRY[cls.__name__] = cls
    return cls

# ---------------- ARTIFACTS ----------------
class Threshold(TypedDict):
    label: str
    value: float  # inclusive lower bound

# ---------------- BASE CATEGORIZER ----------------
class DataCategorizer(ABC):
    """Base interface for data categorisers/scorers."""
    
    @abstractmethod
    def categorize(self, aggregated_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Categorise or score the aggregated data.
        
        Args:
            aggregated_data: standardised data from an aggregator
            
        Returns:
            A dict with category/score and any supporting fields
        """
        raise NotImplementedError
    
    def get_categorizer_metadata(self) -> Dict[str, str]:
        """Optional: Return metadata about the categorizer."""
        return {
            "categorizer_type": self.__class__.__name__,
            "version": "1.0",
        }

# ---------------- DEFAULTS ----------------

THRESHOLD_DEFAULTS: Dict[str, List[Threshold]] = {
    # Coverage profiles
    "aerospace": [
        {"label": "small",  "value": 10},
        {"label": "medium", "value": 20},
        {"label": "large",  "value": 30},
    ],
    "aerospace_general": [
        {"label": "micro",  "value": 10},
        {"label": "small",  "value": 20},
        {"label": "medium", "value": 30},
        {"label": "extra",  "value": 40},
    ],
}

# ---------------- SPECIFIC CATEGORIZER ----------------
@register_categorizer
class ClientSizeCategorizer(DataCategorizer):
    """
    Categorises clients by size using coverage/profile-specific thresholds.
    
    Buckets use inclusive lower bounds. The highest matching bucket wins:
        size >= last_threshold  -> last bucket
        size >= previous        -> previous bucket
        ...
        else                    -> 'uncategorised'
    
    Examples:
        >>> categorizer = ClientSizeCategorizer(coverage="aerospace")
        >>> result = categorizer.categorize({"client_name": "ABC Corp", "client_size": 25})
        >>> result["category"]
        'large'
        
        >>> result = categorizer.categorize({"client_name": "XYZ Ltd", "client_size": 5})
        >>> result["category"]
        'uncategorised'
    """
    
    def __init__(
        self,
        coverage: Optional[str] = None,
        configuration: Optional[str] = None
    ):
        """
        Args:
            coverage: e.g., 'aerospace'
            configuration: underlying coverage configuration, e.g., 'aerospace_general'
        
        Raises:
            ValueError: If neither coverage nor configuration is provided
            ValueError: If the specified profile doesn't exist in THRESHOLD_DEFAULTS
        """
        profile_key = configuration or coverage
        
        # Enforce requirement for coverage or configuration
        if profile_key is None:
            raise ValueError(
                "You must specify either coverage or configuration."
            )
        
        # Validate profile exists
        if profile_key not in THRESHOLD_DEFAULTS:
            available = ", ".join(THRESHOLD_DEFAULTS.keys())
            raise ValueError(
                f"Unknown profile '{profile_key}'. "
                f"Available profiles: {available}"
            )
        
        # Store profile key and normalise thresholds
        self.profile_key = profile_key
        self.thresholds: List[Threshold] = sorted(
            THRESHOLD_DEFAULTS[profile_key], 
            key=lambda t: t["value"]
        )
        
        # Optional: Validate thresholds
        self._validate_thresholds()
    
    def _validate_thresholds(self) -> None:
        """Validate threshold configuration for consistency."""
        if not self.thresholds:
            raise ValueError("Thresholds list cannot be empty")
        
        # Check for duplicate values
        values = [t["value"] for t in self.thresholds]
        if len(values) != len(set(values)):
            raise ValueError(
                f"Threshold values must be unique in profile '{self.profile_key}'"
            )
        
        # Check for duplicate labels
        labels = [t["label"] for t in self.thresholds]
        if len(labels) != len(set(labels)):
            raise ValueError(
                f"Threshold labels must be unique in profile '{self.profile_key}'"
            )
    
    def categorize(self, aggregated_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Categorise by size based on configured thresholds.
        
        Args:
            aggregated_data: Must contain 'client_size' (numeric) and optionally 'client_name'
            
        Returns:
            Dict containing:
                - client: client name (if provided)
                - category: matched category label or 'uncategorised'
                - criteria: threshold value that was matched (or None)
                - size: the actual size value
                - profile: the profile key used for categorization
        """
        size = aggregated_data.get("client_size", 0)
        
        # Iterate descending: highest threshold first
        matched_label: Optional[str] = None
        matched_value: Optional[float] = None
        
        for th in reversed(self.thresholds):
            if size >= th["value"]:
                matched_label = th["label"]
                matched_value = th["value"]
                break
        
        if matched_label is None:
            category = "uncategorised"
            criteria = None
        else:
            category = matched_label
            criteria = matched_value
        
        return {
            "client": aggregated_data.get("client_name"),
            "category": category,
            "criteria": criteria,
            "size": size,
            "profile": self.profile_key
        }
    
    def get_categorizer_metadata(self) -> Dict[str, Any]:
        """Return metadata including threshold configuration."""
        return {
            "categorizer_type": self.__class__.__name__,
            "version": "1.0",
            "profile": self.profile_key,
            "num_thresholds": len(self.thresholds),
            "threshold_range": f"{self.thresholds[0]['value']} - {self.thresholds[-1]['value']}"
        }


























































## DEFINE SPECIFIC CATEGORISERS ----------------

@register_categorizer
class ClientSizeCategorizer:
    """
    Categorises clients by sise using coverage, and potential underlying configuration, specific thresholds.

    Categories are ordered by threshold:  Threshold_Tuple_8 > Threshold_Tuple_7 > Threshold_Tuple_6 ... else 'uncategorised'., and used inclusive lower bounds:
        - Variable: size >= Threshold_Tuple_8      
        - Variable: size >= Threshold_Tuple_7
        - Variable: size >= Threshold_Tuple_6
        - ...
        - else:   'uncategorised'

    The returned 'thresholds' field provides human-readable ranges consistent with the logic.
    """

    THRESHOLD_DEFAULTS: Dict[str, Thresholds] = {
        "aerospace": {
            "Threshold_Tuple_1": ("label": "small", "value": 10), 
            "Threshold_Tuple_2": ("label": "medium", "value": 20), 
            "Threshold_Tuple_3": ("label": "large", "value": 30), 
        },
        "aerospace_general": {
            "Threshold_Tuple_1": ("label": "micro", "value": 10), 
            "Threshold_Tuple_2": ("label": "small", "value": 20), 
            "Threshold_Tuple_3": ("label": "medium", "value": 30), 
            "Threshold_Tuple_4": ("label": "extra", "value": 40), 
        },
    }

    def __init__(self, coverage: str, cov_configuration: Optional[str] = None):

        if coverage is None && cov_configuration is None:
            raise TypeError("a coverage or underlying configuration is required")
        elif cov_configuration:
            base = self.THRESHOLD_DEFAULTS.get(cov_configuration).copy()
        else:
            base = self.THRESHOLD_DEFAULTS.get(coverage).copy()

    def categorize(self, aggregated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Categorise by size based on configured thresholds."""
        
        size = aggregated_data.get("client_size", 0)

        if self.Threshold_Tuple_8 is not None and size >= self.Threshold_Tuple_8.get("value"):
            category = self.Threshold_Tuple_8.get("label")
            criteria = self.Threshold_Tuple_8.get("value")
        elif self.Threshold_Tuple_7 is not None and size >= self.Threshold_Tuple_7.get("value"):
            category = self.Threshold_Tuple_7.get("label")
            criteria = self.Threshold_Tuple_7.get("value")
        elif self.Threshold_Tuple_6 is not None and size >= self.Threshold_Tuple_6.get("value"):
            category = self.Threshold_Tuple_6.get("label")
            criteria = self.Threshold_Tuple_6.get("value")
        elif self.Threshold_Tuple_5 is not None and size >= self.Threshold_Tuple_5.get("value"):
            category = self.Threshold_Tuple_5.get("label")
            criteria = self.Threshold_Tuple_5.get("value")
        elif self.Threshold_Tuple_4 is not None and size >= self.Threshold_Tuple_4.get("value"):
            category = self.Threshold_Tuple_4.get("label")
            criteria = self.Threshold_Tuple_4.get("value")
        elif self.Threshold_Tuple_3 is not None and size >= self.Threshold_Tuple_3.get("value"):
            category = self.Threshold_Tuple_3.get("label")
            criteria = self.Threshold_Tuple_3.get("value")
        elif self.Threshold_Tuple_2 is not None and size >= self.Threshold_Tuple_2.get("value"):
            category = self.Threshold_Tuple_2.get("label")
            criteria = self.Threshold_Tuple_2.get("value")
        elif self.Threshold_Tuple_1 is not None and size >= self.Threshold_Tuple_1.get("value"):
            category = self.Threshold_Tuple_1.get("label")
            criteria = self.Threshold_Tuple_1.get("value")
        else:
            category = "uncategorized"
            criteria = None
 
        return {
            "client": aggregated_data.get("client_name"),
            "category": category,
            "criteria": criteria,
            "size": size,
        }






# ----------------------------
# Implementations: Maritime Domain
# ----------------------------

# CATEGORIZERS
@register_categorizer
class ClientSizeCategorizer(DataCategorizer):
    """
    Categorises clients by size.
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
    
