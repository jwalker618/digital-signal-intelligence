"""
Exposure Layer - Core Data Types (v2.0)

Defines types for exposure assessment based on
exposure_tier_bands in coverage configurations.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from enum import Enum


def utcnow() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


class ExposureBandLabel(Enum):
    """Standard exposure band labels."""
    SMALL = "SMALL"
    MEDIUM = "MEDIUM"
    LARGE = "LARGE"
    VERY_LARGE = "VERY_LARGE"


class ExposureMethod(Enum):
    """Methods for applying exposure adjustments."""
    MODIFIER = "MODIFIER"       # Multiplicative modifier to premium
    MULTIPLIER = "MULTIPLIER"   # Rate × exposure basis value


@dataclass
class ExposureSignalOutput:
    """Output from a single exposure signal extraction."""
    signal_id: str
    signal_name: str
    raw_value: float
    normalized_score: float  # 0-100 normalized
    confidence: float
    data_sources: List[str] = field(default_factory=list)
    extracted_at: datetime = field(default_factory=utcnow)
    error: Optional[str] = None


@dataclass
class ExposureBandResult:
    """Result of mapping an exposure value to a band."""
    band_id: int
    label: str
    method: str
    applied: float
    raw_value: float
    description: str = ""


@dataclass
class ExposureAssessmentResult:
    """Complete exposure assessment output."""
    # Exposure value and band
    exposure_value: float
    exposure_band: Optional[ExposureBandResult] = None

    # Signal outputs
    signal_outputs: List[ExposureSignalOutput] = field(default_factory=list)

    # Composite scores
    magnitude_score: float = 50.0
    complexity_score: float = 50.0
    composite_exposure_score: float = 50.0

    # Modifier to apply
    exposure_modifier: float = 1.0

    # Confidence
    confidence: float = 1.0
    signal_coverage: float = 1.0

    # Metadata
    assessed_at: datetime = field(default_factory=utcnow)
    assessment_method: str = "config_band_lookup"

    # Flags
    flags: List[str] = field(default_factory=list)
    referral_reasons: List[str] = field(default_factory=list)
