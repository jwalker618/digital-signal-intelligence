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
