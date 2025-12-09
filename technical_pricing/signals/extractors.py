from abc import ABC, abstractmethod
from typing import Any, Dict, List, Type, Optional

# ----------------------------
# Registry
# ----------------------------

EXTRACTOR_REGISTRY: Dict[str, Type["DataExtractor"]] = {}

def register_extractor(cls: Type["DataExtractor"]) -> Type["DataExtractor"]:
    """Register a data extractor (source) class."""
    EXTRACTOR_REGISTRY[cls.__name__] = cls
    return cls

# ----------------------------
# Base Class
# ----------------------------

class DataExtractor(ABC):
    """
    Base class for data extractors (sources).
    Extracts raw data from various sources (API, database, file, etc.)
    """
    @abstractmethod
    def extract(self) -> Dict[str, Any]:
        """Extract raw data from the source."""
        raise NotImplementedError
    
    def get_source_metadata(self) -> Dict[str, str]:
        """Optional: Return metadata about the data source."""
        return {
            "extractor_type": self.__class__.__name__,
            "source": "unknown"
        }

# ----------------------------
# Implementations: Maritime Domain
# ----------------------------

# EXTRACTORS
@register_extractor
class EquasisAPIExtractor(DataExtractor):
    """
    Simulates extracting vessel data from Equasis API for a marine operator.
    Returns raw API-style payload.
    """

    def __init__(self, company_name: str, offers_liner_service: bool, fleet_spec: Dict[str, int]):
        self.company_name = company_name
        self.offers_liner_service = offers_liner_service
        self.fleet_spec = fleet_spec  # e.g., {"container": 60, "bulk": 10}

    def extract(self) -> Dict[str, Any]:
        """Simulate API call returning raw vessel data."""
        vessels: List[Dict[str, Any]] = []
        imo_seed = abs(hash(self.company_name)) % 1000000
        
        for cat, count in self.fleet_spec.items():
            for i in range(count):
                vessels.append({
                    "imo": imo_seed + i,
                    "category": cat,
                    "dwt": 50000 + (i * 1000),  # Example: deadweight tonnage
                    "year_built": 2010 + (i % 15)
                })
        
        return {
            "company_name": self.company_name,
            "offers_liner_service": self.offers_liner_service,
            "vessels": vessels,
            "data_source": "equasis_api"
        }
    
    def get_source_metadata(self) -> Dict[str, str]:
        return {
            "extractor_type": self.__class__.__name__,
            "source": "Equasis API",
            "company": self.company_name
        }
