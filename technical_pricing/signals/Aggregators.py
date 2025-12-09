from abc import ABC, abstractmethod
from typing import Any, Dict, List, Type, Optional

# ----------------------------
# Registries
# ----------------------------
AGGREGATOR_REGISTRY: Dict[str, Type["DataAggregator"]] = {}

def register_aggregator(cls: Type["DataAggregator"]) -> Type["DataAggregator"]:
    """Register a data aggregator/analyzer class."""
    AGGREGATOR_REGISTRY[cls.__name__] = cls
    return cls

# ----------------------------
# Base Class
# ----------------------------

class DataAggregator(ABC):
    """
    Base class for data aggregators/analyzers.
    Transforms raw extracted data into standardized, analyzed output.
    """
    @abstractmethod
    def aggregate(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform and analyze raw data.
        
        Args:
            raw_data: Raw data from an extractor
            
        Returns:
            Standardized, aggregated/analyzed data
        """
        raise NotImplementedError
    
    def get_aggregator_metadata(self) -> Dict[str, str]:
        """Optional: Return metadata about the aggregator."""
        return {
            "aggregator_type": self.__class__.__name__,
            "version": "1.0"
        }


# ----------------------------
# Implementations: Maritime Domain
# ----------------------------

# AGGREGATORS
@register_aggregator
class FleetAggregator(DataAggregator):
    """
    Aggregates raw vessel data into standardized fleet statistics.
    Calculates totals, dominant categories, age distribution, etc.
    """
    
    def aggregate(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform raw vessel data into fleet statistics."""
        vessels = raw_data.get("vessels", [])
        
        # Calculate category distribution
        category_counts: Dict[str, int] = {}
        for vessel in vessels:
            cat = vessel.get("category")
            if cat:
                category_counts[cat] = category_counts.get(cat, 0) + 1
        
        # Determine dominant category
        if not category_counts:
            dominant_category = None
            dominance_ratio = 0.0
        else:
            max_count = max(category_counts.values())
            max_cats = [c for c, n in category_counts.items() if n == max_count]
            
            if len(max_cats) == 1:
                dominant_category = max_cats[0]
                dominance_ratio = max_count / len(vessels) if vessels else 0.0
            else:
                dominant_category = "mixed"
                dominance_ratio = max_count / len(vessels) if vessels else 0.0
        
        # Calculate fleet age
        current_year = 2024
        ages = [current_year - v.get("year_built", current_year) for v in vessels if "year_built" in v]
        avg_age = sum(ages) / len(ages) if ages else 0.0
        
        # Calculate total capacity (if available)
        total_dwt = sum(v.get("dwt", 0) for v in vessels)
        
        return {
            "company_name": raw_data.get("company_name"),
            "total_vessels": len(vessels),
            "category_distribution": category_counts,
            "dominant_category": dominant_category,
            "dominance_ratio": round(dominance_ratio, 2),
            "average_fleet_age": round(avg_age, 1),
            "total_dwt": total_dwt,
            "offers_liner_service": raw_data.get("offers_liner_service", False),
            "vessels": vessels,  # Pass through for downstream use
        }


@register_aggregator
class ServiceCapabilityAggregator(DataAggregator):
    """
    Analyzes service capabilities based on vessel types and operational flags.
    """
    
    def aggregate(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze service capabilities."""
        vessels = raw_data.get("vessels", [])
        categories = set(v.get("category") for v in vessels if v.get("category"))
        
        # Determine service capabilities
        capabilities = {
            "liner_service": raw_data.get("offers_liner_service", False),
            "container_capable": "container" in categories,
            "bulk_capable": "bulk" in categories,
            "tanker_capable": "tanker" in categories,
            "multi_modal": len(categories) > 1,
        }
        
        return {
            "company_name": raw_data.get("company_name"),
            "service_capabilities": capabilities,
            "vessel_type_count": len(categories),
            "vessel_types": list(categories),
        }
