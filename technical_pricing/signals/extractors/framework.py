"""
Signal Data Extraction Framework

Provides base classes, registries, and utilities for all extraction functions.
"""

from __future__ import annotations

import hashlib
import random
import string
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Type, Tuple, Union

# =============================================================================
# TTL CONFIGURATION
# =============================================================================

class TTLCategory(Enum):
    """Time-to-live categories for signal freshness requirements."""
    REAL_TIME = "real_time"      # 1 hour - sanctions, breaking events
    DYNAMIC = "dynamic"          # 24 hours - inspections, incidents, violations
    SEMI_STATIC = "semi_static"  # 7 days - ratings, certifications, fleet data
    STATIC = "static"            # 90 days - registrations, long-term relationships

@dataclass
class TTLConfig:
    """TTL configuration for an extractor or signal."""
    category: TTLCategory
    ttl_seconds: int
    description: str = ""
    
    @classmethod
    def real_time(cls, description: str = "") -> "TTLConfig":
        return cls(TTLCategory.REAL_TIME, 3600, description)
    
    @classmethod
    def dynamic(cls, description: str = "") -> "TTLConfig":
        return cls(TTLCategory.DYNAMIC, 86400, description)
    
    @classmethod
    def semi_static(cls, description: str = "") -> "TTLConfig":
        return cls(TTLCategory.SEMI_STATIC, 604800, description)
    
    @classmethod
    def static(cls, description: str = "") -> "TTLConfig":
        return cls(TTLCategory.STATIC, 7776000, description)
    
    def is_stale(self, last_fetched: datetime) -> bool:
        """Check if data needs refresh based on TTL."""
        age_seconds = (datetime.now() - last_fetched).total_seconds()
        return age_seconds > self.ttl_seconds

@dataclass
class DataSource:
    """Represents a single data source for a signal."""
    source_type: str  # api, scrape, filing, dns, scan, satellite, correlation, registry
    provider: str
    endpoint: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1  # Lower = higher priority for fallback
    
    def __str__(self) -> str:
        return f"{self.source_type}:{self.provider}" + (f"/{self.endpoint}" if self.endpoint else "")


# =============================================================================
# SIGNAL RESULT HANDLING
# =============================================================================

@dataclass
class SignalResult:
    """Result from extracting a single signal."""
    signal_id: str
    value: Optional[Any]
    confidence: float  # 0.0 to 1.0
    source_used: Optional[DataSource]
    ttl_config: TTLConfig
    fetched_at: datetime
    is_missing: bool = False
    error: Optional[str] = None
    all_sources_tried: List[str] = field(default_factory=list)
    
    @classmethod
    def missing(cls, signal_id: str, ttl: TTLConfig, error: str = "Signal not available") -> "SignalResult":
        """Create a missing signal result."""
        return cls(
            signal_id=signal_id,
            value=None,
            confidence=0.0,
            source_used=None,
            ttl_config=ttl,
            fetched_at=datetime.now(),
            is_missing=True,
            error=error
        )

@dataclass
class ExtractionResult:
    """Complete extraction result with all signals."""
    source: str
    source_type: str
    timestamp: str
    raw_data: Dict[str, Any]
    signals: Dict[str, SignalResult] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    ttl_config: Optional[TTLConfig] = None

# =============================================================================
# MISSING SIGNAL HANDLING STRATEGIES
# =============================================================================

class MissingSignalStrategy(Enum):
    """How to handle missing signals in composite calculations."""
    EXCLUDE = "exclude"           # Remove from weighted calculation
    USE_DEFAULT = "use_default"   # Use coverage-specific default value
    PENALIZE = "penalize"         # Apply penalty score
    REQUIRE = "require"           # Fail the entire calculation


@dataclass
class SignalWeightConfig:
    """Configuration for signal weighting in composites."""
    weight: float
    missing_strategy: MissingSignalStrategy = MissingSignalStrategy.EXCLUDE
    default_value: Optional[float] = None
    penalty_value: float = 25.0  # Score to use if PENALISE strategy
    min_confidence: float = 0.5  # Minimum confidence to include signal

# =============================================================================
# REGISTRIES
# =============================================================================

EXTRACTOR_REGISTRY: Dict[str, Type["DataExtractor"]] = {}

def register_extractor(cls: Type["DataExtractor"]) -> Type["DataExtractor"]:
    """Decorator to register extractor classes."""
    EXTRACTOR_REGISTRY[cls.__name__] = cls
    return cls

# =============================================================================
# DATA CLASSES
# =============================================================================

class DataExtractor(ABC):
    """
    Base class for all data extractors.
    
    Each extractor must define:
    - source_name: Primary data source identifier
    - coverage: Coverage line (marine, aerospace, cyber, etc.)
    - signals: List of signals this extractor provides
    - ttl_config: Time-to-live configuration
    - alternative_sources: List of alternative DataSource objects for fallback
    """
    
    def __init__(self, seed: Optional[str] = None, **kwargs: Any):
        self.seed = seed
        self.kwargs = kwargs
        self._rng = self._create_rng(seed)
        self._last_fetch: Optional[datetime] = None
    
    def _create_rng(self, seed: Optional[str]) -> random.Random:
        rng = random.Random()
        if seed:
            rng.seed(int(hashlib.md5(seed.encode()).hexdigest(), 16))
        return rng
    
    def _random_date(self, start_days_ago: int = 365, end_days_ago: int = 0) -> str:
        days_ago = self._rng.randint(min(end_days_ago, start_days_ago), max(end_days_ago, start_days_ago))
        return (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    
    def _weighted_choice(self, choices: List[Tuple[Any, float]]) -> Any:
        items, weights = zip(*choices)
        return self._rng.choices(items, weights=weights, k=1)[0]
    
    def _random_id(self, prefix: str = "", length: int = 8) -> str:
        chars = string.ascii_uppercase + string.digits
        return f"{prefix}{''.join(self._rng.choices(chars, k=length))}"
    
    def _random_company_name(self, industry: str = "Corp") -> str:
        prefixes = ["Global", "Premier", "Pacific", "Atlantic", "Continental", "United", "Allied", "National"]
        suffixes = ["Holdings", "Group", "Partners", "Corp", "Ltd", "Inc", "LLC"]
        return f"{self._rng.choice(prefixes)} {industry} {self._rng.choice(suffixes)}"
    
    def needs_refresh(self) -> bool:
        """Check if data needs refresh based on TTL."""
        if self._last_fetch is None:
            return True
        return self.ttl_config.is_stale(self._last_fetch)
    
    @abstractmethod
    def extract(self) -> ExtractionResult:
        """Extract data from source(s). Implement in subclasses."""
        raise NotImplementedError
    
    @property
    @abstractmethod
    def source_name(self) -> str:
        """Primary source identifier."""
        raise NotImplementedError
    
    @property
    @abstractmethod
    def coverage(self) -> str:
        """Coverage line this extractor serves."""
        raise NotImplementedError
    
    @property
    @abstractmethod
    def signals(self) -> List[str]:
        """List of signals this extractor provides."""
        raise NotImplementedError
    
    @property
    @abstractmethod
    def ttl_config(self) -> TTLConfig:
        """TTL configuration for this extractor."""
        raise NotImplementedError
    
    @property
    def alternative_sources(self) -> List[DataSource]:
        """Alternative data sources for fallback. Override in subclasses."""
        return []
