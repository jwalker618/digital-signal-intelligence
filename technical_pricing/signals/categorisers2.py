"""
Signal Data Extraction Framework

Architecture:
- 11 categorizer types for different signal patterns
- Coverage-specific signal configurations
- Comprehensive threshold, scoring logic, and quality tier profiles
- Support for composite scoring with critical signal handling

Categorizer Types:
1. ThresholdBucketCategorizer - Numeric values to categories
2. ScoringLogicCategorizer - Discrete state to score mapping
3. QualityTierCategorizer - Entity-based quality tiers
4. EnumerationCategorizer - Attribute mapping
5. BooleanFlagCategorizer - Yes/no flags
6. RateBenchmarkCategorizer - Compare rates vs benchmarks
7. CompositeScoreCategorizer - Weighted composite scores
8. TierCategorizer - Score to risk tier mapping
9. ConditionEvaluator - Band-based threshold evaluation
10. ModifierCalculator - Composite modifier from features
11. MajorityCategorizer - Dominant category from distribution
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Type, TypedDict, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


# =============================================================================
# REGISTRY & TYPE DEFINITIONS
# =============================================================================

CATEGORIZER_REGISTRY: Dict[str, Type["DataCategorizer"]] = {}


def register_categorizer(cls: Type["DataCategorizer"]) -> Type["DataCategorizer"]:
    """Decorator to register categorizer classes."""
    CATEGORIZER_REGISTRY[cls.__name__] = cls
    return cls


class MissingSignalStrategy(Enum):
    """Strategy for handling missing signals in composite scoring."""
    EXCLUDE = "exclude"
    USE_DEFAULT = "use_default"
    PENALIZE = "penalize"
    REQUIRE = "require"


class ThresholdBucket(TypedDict):
    """Definition for a single threshold bucket."""
    min_value: float
    max_value: float
    category: str
    score: float
    modifier: float


class SignalWeight(TypedDict):
    """Weight configuration for a signal in composite scoring."""
    weight: float
    critical: bool
    critical_threshold: float
    missing_strategy: str
    default_value: float


class QualityTier(TypedDict):
    """Definition for a quality tier."""
    tier: str
    score: float
    modifier: float
    entities: List[str]


@dataclass
class CategorizationResult:
    """Standardized result from any categorizer."""
    category: Optional[str] = None
    score: Optional[float] = None
    modifier: Optional[float] = None
    criteria: List[str] = field(default_factory=list)
    action: Optional[str] = None
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category, "score": self.score, "modifier": self.modifier,
            "criteria": self.criteria, "action": self.action, "confidence": self.confidence,
            "metadata": self.metadata,
        }


# =============================================================================
# THRESHOLD BUCKET PROFILES
# =============================================================================

THRESHOLD_PROFILES: Dict[str, Dict[str, List[ThresholdBucket]]] = {
    "fleet_size": {
        "marine": [
            {"min_value": 0, "max_value": 5, "category": "MICRO", "score": 60, "modifier": 1.15},
            {"min_value": 6, "max_value": 20, "category": "SMALL", "score": 70, "modifier": 1.10},
            {"min_value": 21, "max_value": 50, "category": "MEDIUM", "score": 80, "modifier": 1.00},
            {"min_value": 51, "max_value": 100, "category": "LARGE", "score": 85, "modifier": 0.95},
            {"min_value": 101, "max_value": 250, "category": "MAJOR", "score": 90, "modifier": 0.90},
            {"min_value": 251, "max_value": float("inf"), "category": "MEGA", "score": 95, "modifier": 0.85},
        ],
        "aerospace": [
            {"min_value": 0, "max_value": 5, "category": "MICRO", "score": 55, "modifier": 1.20},
            {"min_value": 6, "max_value": 15, "category": "SMALL", "score": 65, "modifier": 1.12},
            {"min_value": 16, "max_value": 40, "category": "MEDIUM", "score": 75, "modifier": 1.00},
            {"min_value": 41, "max_value": 100, "category": "LARGE", "score": 85, "modifier": 0.92},
            {"min_value": 101, "max_value": 250, "category": "MAJOR", "score": 90, "modifier": 0.88},
            {"min_value": 251, "max_value": float("inf"), "category": "MEGA", "score": 95, "modifier": 0.82},
        ],
        "default": [
            {"min_value": 0, "max_value": 10, "category": "SMALL", "score": 65, "modifier": 1.10},
            {"min_value": 11, "max_value": 50, "category": "MEDIUM", "score": 75, "modifier": 1.00},
            {"min_value": 51, "max_value": 200, "category": "LARGE", "score": 85, "modifier": 0.95},
            {"min_value": 201, "max_value": float("inf"), "category": "MAJOR", "score": 90, "modifier": 0.90},
        ],
    },
    "fleet_age": {
        "marine": [
            {"min_value": 0, "max_value": 5, "category": "NEW", "score": 95, "modifier": 0.90},
            {"min_value": 5.01, "max_value": 10, "category": "MODERN", "score": 88, "modifier": 0.95},
            {"min_value": 10.01, "max_value": 15, "category": "MATURE", "score": 78, "modifier": 1.00},
            {"min_value": 15.01, "max_value": 20, "category": "AGING", "score": 65, "modifier": 1.10},
            {"min_value": 20.01, "max_value": 25, "category": "OLD", "score": 50, "modifier": 1.25},
            {"min_value": 25.01, "max_value": float("inf"), "category": "VERY_OLD", "score": 35, "modifier": 1.40},
        ],
        "aerospace": [
            {"min_value": 0, "max_value": 5, "category": "NEW_GEN", "score": 95, "modifier": 0.88},
            {"min_value": 5.01, "max_value": 10, "category": "CURRENT_GEN", "score": 88, "modifier": 0.92},
            {"min_value": 10.01, "max_value": 18, "category": "MATURE", "score": 78, "modifier": 1.00},
            {"min_value": 18.01, "max_value": 25, "category": "AGING", "score": 62, "modifier": 1.15},
            {"min_value": 25.01, "max_value": float("inf"), "category": "LEGACY", "score": 45, "modifier": 1.30},
        ],
        "default": [
            {"min_value": 0, "max_value": 5, "category": "NEW", "score": 90, "modifier": 0.92},
            {"min_value": 5.01, "max_value": 15, "category": "MATURE", "score": 78, "modifier": 1.00},
            {"min_value": 15.01, "max_value": float("inf"), "category": "OLD", "score": 60, "modifier": 1.15},
        ],
    },
    "psc_deficiency_rate": {
        "marine": [
            {"min_value": 0, "max_value": 0.5, "category": "EXCELLENT", "score": 95, "modifier": 0.90},
            {"min_value": 0.51, "max_value": 1.5, "category": "GOOD", "score": 85, "modifier": 0.95},
            {"min_value": 1.51, "max_value": 3.0, "category": "AVERAGE", "score": 75, "modifier": 1.00},
            {"min_value": 3.01, "max_value": 5.0, "category": "ELEVATED", "score": 60, "modifier": 1.10},
            {"min_value": 5.01, "max_value": 8.0, "category": "HIGH", "score": 45, "modifier": 1.25},
            {"min_value": 8.01, "max_value": float("inf"), "category": "CRITICAL", "score": 25, "modifier": 1.50},
        ],
    },
    "accident_rate": {
        "aerospace": [
            {"min_value": 0, "max_value": 0.5, "category": "EXCELLENT", "score": 98, "modifier": 0.85},
            {"min_value": 0.51, "max_value": 1.0, "category": "GOOD", "score": 90, "modifier": 0.92},
            {"min_value": 1.01, "max_value": 2.0, "category": "AVERAGE", "score": 78, "modifier": 1.00},
            {"min_value": 2.01, "max_value": 4.0, "category": "ELEVATED", "score": 60, "modifier": 1.15},
            {"min_value": 4.01, "max_value": float("inf"), "category": "HIGH_RISK", "score": 35, "modifier": 1.40},
        ],
    },
    "otp_score": {
        "aerospace": [
            {"min_value": 90, "max_value": 100, "category": "EXCELLENT", "score": 95, "modifier": 0.90},
            {"min_value": 80, "max_value": 89.99, "category": "GOOD", "score": 85, "modifier": 0.95},
            {"min_value": 70, "max_value": 79.99, "category": "AVERAGE", "score": 72, "modifier": 1.00},
            {"min_value": 60, "max_value": 69.99, "category": "BELOW_AVERAGE", "score": 55, "modifier": 1.10},
            {"min_value": 0, "max_value": 59.99, "category": "POOR", "score": 40, "modifier": 1.25},
        ],
    },
    "security_rating": {
        "cyber": [
            {"min_value": 850, "max_value": 1000, "category": "EXCELLENT", "score": 98, "modifier": 0.85},
            {"min_value": 750, "max_value": 849, "category": "GOOD", "score": 88, "modifier": 0.92},
            {"min_value": 650, "max_value": 749, "category": "AVERAGE", "score": 75, "modifier": 1.00},
            {"min_value": 550, "max_value": 649, "category": "BELOW_AVERAGE", "score": 58, "modifier": 1.12},
            {"min_value": 400, "max_value": 549, "category": "POOR", "score": 40, "modifier": 1.30},
            {"min_value": 0, "max_value": 399, "category": "CRITICAL", "score": 20, "modifier": 1.50},
        ],
        "financial_institutions": [
            {"min_value": 800, "max_value": 1000, "category": "EXCELLENT", "score": 95, "modifier": 0.88},
            {"min_value": 700, "max_value": 799, "category": "GOOD", "score": 85, "modifier": 0.95},
            {"min_value": 600, "max_value": 699, "category": "ACCEPTABLE", "score": 72, "modifier": 1.00},
            {"min_value": 500, "max_value": 599, "category": "NEEDS_IMPROVEMENT", "score": 55, "modifier": 1.15},
            {"min_value": 0, "max_value": 499, "category": "UNACCEPTABLE", "score": 30, "modifier": 1.40},
        ],
        "default": [
            {"min_value": 80, "max_value": 100, "category": "EXCELLENT", "score": 95, "modifier": 0.90},
            {"min_value": 65, "max_value": 79, "category": "GOOD", "score": 82, "modifier": 0.95},
            {"min_value": 50, "max_value": 64, "category": "AVERAGE", "score": 70, "modifier": 1.00},
            {"min_value": 35, "max_value": 49, "category": "BELOW_AVERAGE", "score": 55, "modifier": 1.10},
            {"min_value": 0, "max_value": 34, "category": "POOR", "score": 35, "modifier": 1.30},
        ],
    },
    "tls_score": {
        "default": [
            {"min_value": 90, "max_value": 100, "category": "A_PLUS", "score": 98, "modifier": 0.92},
            {"min_value": 80, "max_value": 89, "category": "A", "score": 92, "modifier": 0.95},
            {"min_value": 70, "max_value": 79, "category": "B", "score": 82, "modifier": 1.00},
            {"min_value": 60, "max_value": 69, "category": "C", "score": 65, "modifier": 1.08},
            {"min_value": 50, "max_value": 59, "category": "D", "score": 45, "modifier": 1.18},
            {"min_value": 0, "max_value": 49, "category": "F", "score": 25, "modifier": 1.35},
        ],
    },
    "breach_count": {
        "cyber": [
            {"min_value": 0, "max_value": 0, "category": "NONE", "score": 95, "modifier": 0.90},
            {"min_value": 1, "max_value": 1, "category": "SINGLE", "score": 70, "modifier": 1.05},
            {"min_value": 2, "max_value": 3, "category": "MULTIPLE", "score": 50, "modifier": 1.20},
            {"min_value": 4, "max_value": float("inf"), "category": "SERIAL", "score": 25, "modifier": 1.50},
        ],
    },
    "board_independence_pct": {
        "d_and_o": [
            {"min_value": 80, "max_value": 100, "category": "HIGHLY_INDEPENDENT", "score": 95, "modifier": 0.90},
            {"min_value": 67, "max_value": 79.99, "category": "INDEPENDENT", "score": 85, "modifier": 0.95},
            {"min_value": 50, "max_value": 66.99, "category": "MAJORITY_INDEPENDENT", "score": 70, "modifier": 1.00},
            {"min_value": 33, "max_value": 49.99, "category": "MINORITY_INDEPENDENT", "score": 50, "modifier": 1.15},
            {"min_value": 0, "max_value": 32.99, "category": "CONTROLLED", "score": 35, "modifier": 1.30},
        ],
    },
    "short_interest_pct": {
        "d_and_o": [
            {"min_value": 0, "max_value": 3, "category": "LOW", "score": 90, "modifier": 0.95},
            {"min_value": 3.01, "max_value": 8, "category": "MODERATE", "score": 78, "modifier": 1.00},
            {"min_value": 8.01, "max_value": 15, "category": "ELEVATED", "score": 60, "modifier": 1.10},
            {"min_value": 15.01, "max_value": 25, "category": "HIGH", "score": 42, "modifier": 1.25},
            {"min_value": 25.01, "max_value": float("inf"), "category": "EXTREME", "score": 25, "modifier": 1.45},
        ],
    },
    "stock_volatility": {
        "d_and_o": [
            {"min_value": 0, "max_value": 0.20, "category": "LOW", "score": 92, "modifier": 0.92},
            {"min_value": 0.201, "max_value": 0.35, "category": "MODERATE", "score": 80, "modifier": 1.00},
            {"min_value": 0.351, "max_value": 0.50, "category": "ELEVATED", "score": 65, "modifier": 1.10},
            {"min_value": 0.501, "max_value": 0.75, "category": "HIGH", "score": 48, "modifier": 1.22},
            {"min_value": 0.751, "max_value": float("inf"), "category": "EXTREME", "score": 30, "modifier": 1.40},
        ],
    },
    "asset_size": {
        "financial_institutions": [
            {"min_value": 0, "max_value": 500_000_000, "category": "COMMUNITY", "score": 70, "modifier": 1.08},
            {"min_value": 500_000_001, "max_value": 5_000_000_000, "category": "REGIONAL", "score": 78, "modifier": 1.00},
            {"min_value": 5_000_000_001, "max_value": 50_000_000_000, "category": "SUPER_REGIONAL", "score": 85, "modifier": 0.95},
            {"min_value": 50_000_000_001, "max_value": 250_000_000_000, "category": "LARGE", "score": 88, "modifier": 0.90},
            {"min_value": 250_000_000_001, "max_value": float("inf"), "category": "GSIB", "score": 92, "modifier": 0.85},
        ],
    },
    "capital_ratio": {
        "financial_institutions": [
            {"min_value": 15, "max_value": 100, "category": "WELL_CAPITALIZED_PLUS", "score": 98, "modifier": 0.88},
            {"min_value": 10, "max_value": 14.99, "category": "WELL_CAPITALIZED", "score": 92, "modifier": 0.92},
            {"min_value": 8, "max_value": 9.99, "category": "ADEQUATELY_CAPITALIZED", "score": 78, "modifier": 1.00},
            {"min_value": 6, "max_value": 7.99, "category": "UNDERCAPITALIZED", "score": 50, "modifier": 1.25},
            {"min_value": 0, "max_value": 5.99, "category": "SIGNIFICANTLY_UNDERCAPITALIZED", "score": 25, "modifier": 1.50},
        ],
    },
    "npl_ratio": {
        "financial_institutions": [
            {"min_value": 0, "max_value": 0.5, "category": "EXCELLENT", "score": 95, "modifier": 0.90},
            {"min_value": 0.51, "max_value": 1.5, "category": "GOOD", "score": 85, "modifier": 0.95},
            {"min_value": 1.51, "max_value": 3.0, "category": "AVERAGE", "score": 72, "modifier": 1.00},
            {"min_value": 3.01, "max_value": 5.0, "category": "ELEVATED", "score": 55, "modifier": 1.12},
            {"min_value": 5.01, "max_value": 8.0, "category": "HIGH", "score": 38, "modifier": 1.28},
            {"min_value": 8.01, "max_value": float("inf"), "category": "CRITICAL", "score": 20, "modifier": 1.50},
        ],
    },
    "cre_concentration": {
        "financial_institutions": [
            {"min_value": 0, "max_value": 100, "category": "LOW", "score": 92, "modifier": 0.92},
            {"min_value": 101, "max_value": 200, "category": "MODERATE", "score": 80, "modifier": 1.00},
            {"min_value": 201, "max_value": 300, "category": "ELEVATED", "score": 65, "modifier": 1.10},
            {"min_value": 301, "max_value": 400, "category": "HIGH", "score": 48, "modifier": 1.22},
            {"min_value": 401, "max_value": float("inf"), "category": "EXCESSIVE", "score": 30, "modifier": 1.40},
        ],
    },
    "osha_trir": {
        "energy": [
            {"min_value": 0, "max_value": 0.5, "category": "EXCELLENT", "score": 98, "modifier": 0.85},
            {"min_value": 0.51, "max_value": 1.0, "category": "GOOD", "score": 90, "modifier": 0.92},
            {"min_value": 1.01, "max_value": 2.0, "category": "AVERAGE", "score": 78, "modifier": 1.00},
            {"min_value": 2.01, "max_value": 4.0, "category": "ELEVATED", "score": 60, "modifier": 1.15},
            {"min_value": 4.01, "max_value": 6.0, "category": "HIGH", "score": 42, "modifier": 1.30},
            {"min_value": 6.01, "max_value": float("inf"), "category": "CRITICAL", "score": 22, "modifier": 1.50},
        ],
    },
    "production_boed": {
        "energy": [
            {"min_value": 0, "max_value": 10_000, "category": "SMALL_PRODUCER", "score": 65, "modifier": 1.12},
            {"min_value": 10_001, "max_value": 50_000, "category": "MID_PRODUCER", "score": 72, "modifier": 1.05},
            {"min_value": 50_001, "max_value": 200_000, "category": "LARGE_PRODUCER", "score": 78, "modifier": 1.00},
            {"min_value": 200_001, "max_value": 500_000, "category": "MAJOR_PRODUCER", "score": 83, "modifier": 0.95},
            {"min_value": 500_001, "max_value": float("inf"), "category": "SUPER_MAJOR", "score": 88, "modifier": 0.90},
        ],
    },
    "reserve_life_years": {
        "energy": [
            {"min_value": 15, "max_value": float("inf"), "category": "LONG", "score": 92, "modifier": 0.90},
            {"min_value": 10, "max_value": 14.99, "category": "ADEQUATE", "score": 82, "modifier": 0.95},
            {"min_value": 7, "max_value": 9.99, "category": "MODERATE", "score": 70, "modifier": 1.00},
            {"min_value": 4, "max_value": 6.99, "category": "SHORT", "score": 55, "modifier": 1.12},
            {"min_value": 0, "max_value": 3.99, "category": "VERY_SHORT", "score": 38, "modifier": 1.28},
        ],
    },
    "employee_count": {
        "professional_indemnity": [
            {"min_value": 1, "max_value": 5, "category": "SOLO", "score": 65, "modifier": 1.15},
            {"min_value": 6, "max_value": 20, "category": "SMALL_FIRM", "score": 72, "modifier": 1.08},
            {"min_value": 21, "max_value": 50, "category": "MID_FIRM", "score": 78, "modifier": 1.00},
            {"min_value": 51, "max_value": 200, "category": "LARGE_FIRM", "score": 82, "modifier": 0.95},
            {"min_value": 201, "max_value": float("inf"), "category": "MAJOR_FIRM", "score": 85, "modifier": 0.92},
        ],
        "cyber": [
            {"min_value": 0, "max_value": 50, "category": "SMALL", "score": 70, "modifier": 1.08},
            {"min_value": 51, "max_value": 250, "category": "MEDIUM", "score": 75, "modifier": 1.00},
            {"min_value": 251, "max_value": 1000, "category": "LARGE", "score": 78, "modifier": 0.98},
            {"min_value": 1001, "max_value": 5000, "category": "ENTERPRISE", "score": 80, "modifier": 0.95},
            {"min_value": 5001, "max_value": float("inf"), "category": "MAJOR_ENTERPRISE", "score": 82, "modifier": 0.92},
        ],
        "default": [
            {"min_value": 0, "max_value": 50, "category": "SMALL", "score": 70, "modifier": 1.05},
            {"min_value": 51, "max_value": 500, "category": "MEDIUM", "score": 78, "modifier": 1.00},
            {"min_value": 501, "max_value": float("inf"), "category": "LARGE", "score": 82, "modifier": 0.95},
        ],
    },
    "malpractice_frequency": {
        "professional_indemnity": [
            {"min_value": 0, "max_value": 0, "category": "NONE", "score": 95, "modifier": 0.88},
            {"min_value": 0.01, "max_value": 0.02, "category": "LOW", "score": 85, "modifier": 0.95},
            {"min_value": 0.021, "max_value": 0.05, "category": "MODERATE", "score": 70, "modifier": 1.00},
            {"min_value": 0.051, "max_value": 0.10, "category": "ELEVATED", "score": 55, "modifier": 1.15},
            {"min_value": 0.101, "max_value": float("inf"), "category": "HIGH", "score": 35, "modifier": 1.35},
        ],
    },
    "partner_turnover_rate": {
        "professional_indemnity": [
            {"min_value": 0, "max_value": 5, "category": "STABLE", "score": 92, "modifier": 0.92},
            {"min_value": 5.01, "max_value": 10, "category": "NORMAL", "score": 82, "modifier": 1.00},
            {"min_value": 10.01, "max_value": 20, "category": "ELEVATED", "score": 65, "modifier": 1.10},
            {"min_value": 20.01, "max_value": float("inf"), "category": "HIGH", "score": 45, "modifier": 1.28},
        ],
    },
}


# =============================================================================
# QUALITY TIER PROFILES (Entity Recognition)
# =============================================================================

QUALITY_TIER_PROFILES: Dict[str, List[Dict[str, Any]]] = {
    # MARINE
    "classification_society": [
        {"tier": "IACS_PREMIER", "score": 98, "modifier": 0.88, "entities": ["DNV", "Lloyd's Register", "Bureau Veritas", "ABS", "ClassNK"]},
        {"tier": "IACS_MEMBER", "score": 92, "modifier": 0.92, "entities": ["RINA", "Korean Register", "CCS", "IRS", "PRS", "CRS"]},
        {"tier": "RECOGNIZED", "score": 75, "modifier": 1.00, "entities": ["Türk Loydu", "RMRS", "BKI", "VR"]},
        {"tier": "OTHER", "score": 55, "modifier": 1.15, "entities": []},
    ],
    "pi_club": [
        {"tier": "IG_PREMIER", "score": 98, "modifier": 0.85, "entities": ["Gard", "Britannia", "UK P&I Club", "Standard Club", "Steamship Mutual", "West of England"]},
        {"tier": "IG_MEMBER", "score": 92, "modifier": 0.90, "entities": ["North P&I", "Skuld", "Swedish Club", "Japan P&I", "London P&I", "American Club"]},
        {"tier": "FIXED_PREMIUM", "score": 70, "modifier": 1.05, "entities": ["Lodestar", "Hanseatic", "Raets", "Osprey"]},
        {"tier": "OTHER", "score": 50, "modifier": 1.20, "entities": []},
    ],
    "flag_state": [
        {"tier": "PREMIUM", "score": 95, "modifier": 0.88, "entities": ["Singapore", "Hong Kong", "Denmark", "Norway", "United Kingdom", "Japan", "Netherlands"]},
        {"tier": "STANDARD", "score": 85, "modifier": 0.95, "entities": ["Marshall Islands", "Liberia", "Bahamas", "Malta", "Cyprus", "Isle of Man", "Bermuda"]},
        {"tier": "ELEVATED_RISK", "score": 65, "modifier": 1.08, "entities": ["Panama", "Antigua", "Vanuatu", "St Kitts", "Belize"]},
        {"tier": "HIGH_RISK", "score": 45, "modifier": 1.25, "entities": ["Mongolia", "Bolivia", "Cameroon", "Sierra Leone", "Togo", "Moldova"]},
    ],
    # AEROSPACE
    "lessor_quality": [
        {"tier": "TIER_1", "score": 95, "modifier": 0.90, "entities": ["AerCap", "GECAS", "Avolon", "SMBC Aviation Capital", "BOC Aviation", "Air Lease"]},
        {"tier": "TIER_2", "score": 85, "modifier": 0.95, "entities": ["BBAM", "Nordic Aviation Capital", "Aviation Capital Group", "ICBC Leasing", "CDB Aviation"]},
        {"tier": "TIER_3", "score": 72, "modifier": 1.00, "entities": ["Jackson Square", "Aircastle", "Macquarie AirFinance", "Castlelake"]},
        {"tier": "OTHER", "score": 58, "modifier": 1.12, "entities": []},
    ],
    "mro_provider": [
        {"tier": "OEM_NETWORK", "score": 95, "modifier": 0.88, "entities": ["Lufthansa Technik", "AFI KLM E&M", "ST Aerospace", "HAECO", "SIA Engineering"]},
        {"tier": "MAJOR_INDEPENDENT", "score": 88, "modifier": 0.92, "entities": ["AAR", "MTU Aero Engines", "StandardAero", "Turkish Technic", "Ameco Beijing"]},
        {"tier": "REGIONAL", "score": 75, "modifier": 1.00, "entities": ["FL Technics", "Magnetic MRO", "MRO Holdings", "Joramco"]},
        {"tier": "BASIC", "score": 60, "modifier": 1.10, "entities": []},
    ],
    # D&O / FI
    "auditor_quality": [
        {"tier": "BIG_FOUR", "score": 95, "modifier": 0.90, "entities": ["Deloitte", "PwC", "PricewaterhouseCoopers", "EY", "Ernst & Young", "KPMG"]},
        {"tier": "NATIONAL", "score": 85, "modifier": 0.95, "entities": ["BDO", "Grant Thornton", "RSM", "Crowe", "Baker Tilly", "CliftonLarsonAllen"]},
        {"tier": "REGIONAL", "score": 72, "modifier": 1.00, "entities": ["Moss Adams", "Plante Moran", "Wipfli", "Cherry Bekaert", "Armanino"]},
        {"tier": "LOCAL", "score": 58, "modifier": 1.12, "entities": []},
    ],
    "legal_counsel": [
        {"tier": "ELITE", "score": 95, "modifier": 0.88, "entities": ["Wachtell", "Cravath", "Sullivan & Cromwell", "Skadden", "Davis Polk", "Simpson Thacher"]},
        {"tier": "AM_LAW_50", "score": 88, "modifier": 0.92, "entities": ["Kirkland", "Latham", "Gibson Dunn", "Cleary", "Sidley", "Morgan Lewis", "Jones Day"]},
        {"tier": "AM_LAW_100", "score": 78, "modifier": 1.00, "entities": ["King & Spalding", "Ropes & Gray", "Cooley", "WilmerHale", "Goodwin"]},
        {"tier": "REGIONAL", "score": 65, "modifier": 1.08, "entities": []},
    ],
    "correspondent_bank": [
        {"tier": "GSIB", "score": 95, "modifier": 0.88, "entities": ["JPMorgan", "Bank of America", "Citibank", "Wells Fargo", "HSBC", "Deutsche Bank"]},
        {"tier": "LARGE_REGIONAL", "score": 85, "modifier": 0.95, "entities": ["PNC", "US Bancorp", "Truist", "TD Bank", "Fifth Third", "KeyBank"]},
        {"tier": "COMMUNITY", "score": 72, "modifier": 1.00, "entities": []},
    ],
    # PROFESSIONAL INDEMNITY
    "firm_ranking": [
        {"tier": "AM_LAW_100", "score": 95, "modifier": 0.88, "entities": ["Kirkland & Ellis", "Latham & Watkins", "DLA Piper", "Baker McKenzie", "Skadden"]},
        {"tier": "AM_LAW_200", "score": 85, "modifier": 0.92, "entities": ["Foley & Lardner", "Duane Morris", "Greenberg Traurig", "Reed Smith"]},
        {"tier": "REGIONAL_LEADER", "score": 78, "modifier": 1.00, "entities": []},
        {"tier": "BOUTIQUE", "score": 72, "modifier": 1.05, "entities": []},
        {"tier": "SMALL_FIRM", "score": 62, "modifier": 1.12, "entities": []},
    ],
    "accounting_firm": [
        {"tier": "BIG_FOUR", "score": 95, "modifier": 0.88, "entities": ["Deloitte", "PwC", "EY", "KPMG"]},
        {"tier": "TOP_25", "score": 85, "modifier": 0.95, "entities": ["BDO", "Grant Thornton", "RSM", "Crowe", "Baker Tilly", "CLA"]},
        {"tier": "REGIONAL", "score": 72, "modifier": 1.00, "entities": ["Moss Adams", "Plante Moran", "Wipfli", "Armanino", "Marcum"]},
        {"tier": "LOCAL", "score": 58, "modifier": 1.12, "entities": []},
    ],
}


# =============================================================================
# BOOLEAN FLAG DEFINITIONS
# =============================================================================

BOOLEAN_FLAG_PROFILES: Dict[str, Dict[str, Dict[str, Any]]] = {
    # Marine
    "iosa_registered": {"true": {"score": 95, "modifier": 0.90, "message": "IOSA registered"}, "false": {"score": 65, "modifier": 1.12, "message": "Not IOSA registered"}},
    "offers_liner_service": {"true": {"score": 85, "modifier": 0.95, "message": "Offers liner service"}, "false": {"score": 75, "modifier": 1.00, "message": "No liner service"}},
    "sanctioned_country_exposure": {"true": {"score": 20, "modifier": 1.50, "action": "REFER", "message": "Sanctioned country exposure"}, "false": {"score": 90, "modifier": 1.00, "message": "No sanctioned exposure"}},
    "sts_activity": {"true": {"score": 55, "modifier": 1.18, "action": "FLAG", "message": "STS activity detected"}, "false": {"score": 88, "modifier": 1.00, "message": "No STS activity"}},
    "dark_vessel_pattern": {"true": {"score": 30, "modifier": 1.35, "action": "REFER", "message": "Dark vessel pattern detected"}, "false": {"score": 92, "modifier": 1.00, "message": "Normal AIS transmission"}},
    
    # Cyber
    "bug_bounty_program": {"true": {"score": 88, "modifier": 0.92, "message": "Bug bounty program active"}, "false": {"score": 70, "modifier": 1.00, "message": "No bug bounty program"}},
    "security_txt": {"true": {"score": 85, "modifier": 0.95, "message": "security.txt present"}, "false": {"score": 72, "modifier": 1.00, "message": "No security.txt"}},
    "mfa_enforced": {"true": {"score": 92, "modifier": 0.90, "message": "MFA enforced"}, "false": {"score": 55, "modifier": 1.15, "message": "MFA not enforced"}},
    "soc2_certified": {"true": {"score": 92, "modifier": 0.88, "message": "SOC2 certified"}, "false": {"score": 65, "modifier": 1.05, "message": "No SOC2 certification"}},
    
    # D&O
    "ceo_chair_combined": {"true": {"score": 65, "modifier": 1.08, "message": "CEO/Chair roles combined"}, "false": {"score": 88, "modifier": 0.95, "message": "Separated CEO/Chair"}},
    "prior_restatement": {"true": {"score": 50, "modifier": 1.20, "action": "FLAG", "message": "Prior financial restatement"}, "false": {"score": 92, "modifier": 1.00, "message": "No restatements"}},
    "going_concern": {"true": {"score": 25, "modifier": 1.45, "action": "REFER", "message": "Going concern issue"}, "false": {"score": 95, "modifier": 1.00, "message": "No going concern"}},
    "material_weakness": {"true": {"score": 40, "modifier": 1.25, "action": "FLAG", "message": "Material weakness in controls"}, "false": {"score": 92, "modifier": 1.00, "message": "No material weaknesses"}},
    "poison_pill": {"true": {"score": 60, "modifier": 1.10, "message": "Poison pill in place"}, "false": {"score": 82, "modifier": 1.00, "message": "No poison pill"}},
    
    # Financial Institutions
    "well_capitalized": {"true": {"score": 92, "modifier": 0.92, "message": "Well capitalized"}, "false": {"score": 45, "modifier": 1.30, "action": "REFER", "message": "Not well capitalized"}},
    "mou_active": {"true": {"score": 50, "modifier": 1.22, "action": "FLAG", "message": "Active MOU with regulator"}, "false": {"score": 88, "modifier": 1.00, "message": "No active MOU"}},
    "bsa_consent_order": {"true": {"score": 25, "modifier": 1.45, "action": "REFER", "message": "BSA consent order"}, "false": {"score": 92, "modifier": 1.00, "message": "No BSA issues"}},
    
    # Energy
    "vpp_participant": {"true": {"score": 92, "modifier": 0.88, "message": "VPP participant"}, "false": {"score": 72, "modifier": 1.00, "message": "Not VPP participant"}},
    "iso_45001_certified": {"true": {"score": 90, "modifier": 0.90, "message": "ISO 45001 certified"}, "false": {"score": 70, "modifier": 1.00, "message": "No ISO 45001"}},
    "net_zero_commitment": {"true": {"score": 85, "modifier": 0.95, "message": "Net zero commitment"}, "false": {"score": 70, "modifier": 1.00, "message": "No net zero commitment"}},
    "superfund_exposure": {"true": {"score": 35, "modifier": 1.35, "action": "REFER", "message": "Superfund site exposure"}, "false": {"score": 90, "modifier": 1.00, "message": "No Superfund exposure"}},
    
    # Professional Indemnity
    "claims_made_coverage": {"true": {"score": 85, "modifier": 0.95, "message": "Claims-made coverage history"}, "false": {"score": 65, "modifier": 1.10, "message": "No prior claims-made"}},
    "peer_review_enrolled": {"true": {"score": 88, "modifier": 0.92, "message": "Enrolled in peer review"}, "false": {"score": 62, "modifier": 1.10, "message": "Not enrolled in peer review"}},
    "cpe_compliant": {"true": {"score": 90, "modifier": 0.95, "message": "CPE compliant"}, "false": {"score": 55, "modifier": 1.15, "message": "CPE non-compliant"}},
    "prior_bankruptcy": {"true": {"score": 45, "modifier": 1.25, "action": "REFER", "message": "Prior bankruptcy"}, "false": {"score": 85, "modifier": 1.00, "message": "No bankruptcy history"}},
}


# =============================================================================
# SCORING LOGIC PROFILES (State -> Score Mapping)
# =============================================================================

SCORING_LOGIC_PROFILES: Dict[str, Dict[str, float]] = {
    # MARINE
    "psc_detention_status": {"NONE_3YR": 100, "DETAINED_1_3YR": 72, "DETAINED_2_3YR": 52, "DETAINED_3_PLUS_3YR": 30, "BANNED": 5},
    "class_status": {"IN_CLASS": 95, "IN_CLASS_COC": 78, "SUSPENDED": 35, "WITHDRAWN": 15, "NEVER_CLASSED": 25},
    "ism_compliance": {"VALID_DOC_SMC": 95, "VALID_DOC_ONLY": 82, "EXPIRED_DOC": 45, "WITHDRAWN": 20, "NEVER_CERTIFIED": 30},
    "sanctions_status": {"CLEAR": 100, "WATCHLIST": 55, "SECONDARY_SANCTIONS": 35, "SDN_LISTED": 5, "BLOCKED": 0},
    "flag_state_quality": {"WHITE_LIST": 95, "GREY_LIST": 65, "BLACK_LIST": 25, "FOC_HIGH_RISK": 40, "UNLISTED": 50},
    "ais_compliance": {"FULL_COMPLIANCE": 95, "MINOR_GAPS": 82, "SIGNIFICANT_GAPS": 58, "FREQUENT_DARK": 35, "SYSTEMATIC_EVASION": 10},
    "cii_rating": {"A": 98, "B": 88, "C": 75, "D": 55, "E": 30},
    "ownership_transparency": {"FULLY_DISCLOSED": 95, "MOSTLY_DISCLOSED": 82, "PARTIAL": 62, "OPAQUE": 38, "UNKNOWN": 25},
    "jurisdiction_risk": {"LOW_RISK": 95, "MODERATE_RISK": 75, "ELEVATED_RISK": 55, "HIGH_RISK": 35, "PROHIBITED": 5},
    "fleet_stability": {"STABLE": 92, "NORMAL_TURNOVER": 80, "MODERATE_CHANGES": 65, "HIGH_TURNOVER": 45, "UNSTABLE": 28},
    "vessel_condition": {"EXCELLENT": 95, "GOOD": 85, "FAIR": 70, "POOR": 50, "SUBSTANDARD": 30},
    "crew_certification": {"ALL_CERTIFIED": 95, "MOSTLY_CERTIFIED": 82, "SOME_GAPS": 65, "SIGNIFICANT_GAPS": 42, "MAJOR_ISSUES": 20},
    "management_tenure": {"LONG_TERM": 92, "ESTABLISHED": 82, "MODERATE": 70, "SHORT_TERM": 55, "NEW": 42},
    "route_risk_level": {"LOW": 92, "MODERATE": 78, "ELEVATED": 60, "HIGH": 42, "EXTREME": 22},
    "psc_region_risk": {"PARIS_MOU": 88, "TOKYO_MOU": 85, "USCG": 85, "INDIAN_OCEAN_MOU": 72, "ABUJA_MOU": 65, "OTHER": 60},
    
    # AEROSPACE
    "certificate_status": {"ACTIVE": 95, "ACTIVE_RESTRICTIONS": 70, "SUSPENDED": 30, "REVOKED": 5, "PENDING": 60},
    "iosa_status": {"CURRENT": 95, "EXPIRED_RECENT": 72, "EXPIRED_OLD": 55, "NEVER_REGISTERED": 50, "WITHDRAWN": 40},
    "eu_safety_list": {"NOT_LISTED": 95, "PARTIAL_BAN": 35, "FULL_BAN": 5},
    "alliance_membership": {"STAR_ALLIANCE": 92, "ONEWORLD": 90, "SKYTEAM": 88, "VALUE_ALLIANCE": 75, "NONE": 65},
    "ramp_inspection_status": {"ALL_PASSED": 95, "MINOR_FINDINGS": 82, "MODERATE_FINDINGS": 65, "MAJOR_FINDINGS": 40, "GROUNDED": 15},
    "state_safety_rating": {"CAT_1": 95, "CAT_2": 50, "NOT_ASSESSED": 70},
    "training_program_status": {"ADVANCED": 95, "STANDARD": 82, "BASIC": 65, "DEFICIENT": 40},
    "operational_complexity": {"LOW": 88, "MODERATE": 78, "HIGH": 65, "VERY_HIGH": 52},
    "aircraft_generation": {"LATEST_GEN": 95, "CURRENT_GEN": 88, "PREVIOUS_GEN": 75, "LEGACY": 55, "CLASSIC": 40},
    "order_backlog_status": {"STRONG": 90, "MODERATE": 78, "LIMITED": 65, "NONE": 55, "CANCELLED": 40},
    "maintenance_status": {"EXCELLENT": 95, "GOOD": 85, "AVERAGE": 72, "BELOW_AVERAGE": 55, "POOR": 35},
    "weather_exposure": {"LOW": 90, "MODERATE": 78, "HIGH": 62, "EXTREME": 45},
    "terrain_exposure": {"STANDARD": 90, "CHALLENGING": 72, "MOUNTAINOUS": 58, "EXTREME": 42},
    "financial_disclosure": {"COMPREHENSIVE": 92, "STANDARD": 80, "LIMITED": 62, "MINIMAL": 45, "NONE": 28},
    "market_position": {"LEADER": 92, "MAJOR": 85, "ESTABLISHED": 75, "EMERGING": 62, "MARGINAL": 48},
    "safety_reporting_culture": {"STRONG": 95, "GOOD": 85, "AVERAGE": 72, "WEAK": 52, "ABSENT": 30},
    "corporate_structure": {"TRANSPARENT": 92, "STANDARD": 80, "COMPLEX": 62, "OPAQUE": 42},
    "investigation_status": {"NO_OPEN": 95, "MINOR_OPEN": 78, "MAJOR_OPEN": 55, "CRITICAL_OPEN": 30},
    
    # CYBER
    "email_auth": {"SPF_DKIM_DMARC_STRICT": 98, "SPF_DKIM_DMARC": 92, "SPF_DKIM": 78, "SPF_ONLY": 60, "NONE": 30},
    "dnssec_status": {"ENABLED_VERIFIED": 95, "ENABLED": 88, "PARTIAL": 65, "DISABLED": 45},
    "breach_severity": {"NONE": 95, "MINOR": 78, "MODERATE": 58, "MAJOR": 35, "CRITICAL": 15},
    "waf_status": {"ENTERPRISE_WAF": 95, "CLOUD_WAF": 88, "BASIC_WAF": 75, "NONE_DETECTED": 50},
    "security_headers_status": {"ALL_PRESENT": 95, "MOST_PRESENT": 82, "SOME_PRESENT": 65, "FEW_PRESENT": 45, "NONE": 25},
    "software_currency": {"CURRENT": 95, "RECENT": 85, "OUTDATED": 60, "EOL": 35, "ABANDONED": 15},
    "cloud_security_posture": {"EXCELLENT": 95, "GOOD": 85, "AVERAGE": 72, "BELOW_AVERAGE": 55, "POOR": 35},
    "privacy_policy_quality": {"COMPREHENSIVE": 92, "STANDARD": 80, "BASIC": 65, "MINIMAL": 45, "ABSENT": 20},
    "technical_blog_quality": {"ACTIVE_SECURITY": 92, "ACTIVE_GENERAL": 78, "OCCASIONAL": 65, "STALE": 50, "NONE": 35},
    "dark_web_exposure": {"NONE_DETECTED": 95, "MINIMAL": 78, "MODERATE": 58, "SIGNIFICANT": 38, "CRITICAL": 18},
    "compliance_certifications": {"SOC2_ISO27001": 98, "SOC2": 92, "ISO27001": 88, "OTHER": 72, "NONE": 50},
    "certification_status": {"MULTIPLE_CERTS": 95, "PRIMARY_CERT": 85, "PARTIAL": 68, "EXPIRED": 45, "NONE": 35},
    "network_centrality": {"HIGH": 92, "MODERATE": 78, "LOW": 62, "ISOLATED": 45},
    "second_degree_quality": {"STRONG": 88, "MODERATE": 75, "WEAK": 58, "NONE": 42},
    
    # D&O
    "audit_opinion": {"UNQUALIFIED": 95, "UNQUALIFIED_EMPHASIS": 88, "QUALIFIED": 60, "ADVERSE": 25, "DISCLAIMER": 15, "GOING_CONCERN": 40},
    "internal_controls": {"EFFECTIVE": 95, "EFFECTIVE_WITH_DEFICIENCY": 75, "MATERIAL_WEAKNESS": 45, "MULTIPLE_WEAKNESSES": 25},
    "sox_compliance": {"FULLY_COMPLIANT": 95, "MINOR_ISSUES": 82, "SIGNIFICANT_DEFICIENCY": 60, "MATERIAL_WEAKNESS": 35, "NON_COMPLIANT": 15},
    "litigation_status": {"NONE_PENDING": 95, "MINOR_CLAIMS": 82, "SIGNIFICANT_CLAIMS": 60, "CLASS_ACTION": 40, "MULTIPLE_CLASS_ACTIONS": 22, "SEC_INVESTIGATION": 30},
    "committee_structure": {"FULL_INDEPENDENCE": 95, "MAJORITY_INDEPENDENT": 82, "MIXED": 65, "INSIDER_DOMINATED": 42},
    "compensation_alignment": {"STRONG_ALIGNMENT": 92, "MODERATE_ALIGNMENT": 78, "WEAK_ALIGNMENT": 58, "MISALIGNED": 38},
    "shareholder_rights": {"STRONG": 92, "MODERATE": 78, "LIMITED": 58, "WEAK": 40},
    "filing_timeliness": {"ALWAYS_TIMELY": 95, "MOSTLY_TIMELY": 82, "OCCASIONAL_LATE": 65, "FREQUENTLY_LATE": 45, "DELINQUENT": 20},
    "revenue_recognition_risk": {"LOW": 92, "MODERATE": 75, "ELEVATED": 55, "HIGH": 35},
    "debt_covenant_status": {"COMPLIANT": 92, "COMPLIANT_TIGHT": 75, "WAIVER_OBTAINED": 55, "VIOLATION": 30},
    "pending_litigation_status": {"NONE": 95, "MINOR": 80, "MODERATE": 62, "SIGNIFICANT": 42, "SEVERE": 22},
    "cfo_experience": {"HIGHLY_EXPERIENCED": 92, "EXPERIENCED": 82, "MODERATE": 68, "LIMITED": 52, "INEXPERIENCED": 35},
    "insider_trading_pattern": {"NORMAL": 92, "ELEVATED_BUYING": 85, "ELEVATED_SELLING": 60, "UNUSUAL_PATTERN": 42, "SUSPICIOUS": 22},
    "executive_background_check": {"CLEAN": 95, "MINOR_ISSUES": 78, "MODERATE_ISSUES": 55, "SIGNIFICANT_ISSUES": 32},
    "board_network_quality": {"EXCELLENT": 92, "GOOD": 82, "AVERAGE": 70, "LIMITED": 55, "WEAK": 40},
    "index_inclusion": {"SP500": 95, "RUSSELL_1000": 88, "RUSSELL_2000": 78, "OTHER_INDEX": 68, "NONE": 55},
    "ir_quality": {"EXCELLENT": 92, "GOOD": 82, "AVERAGE": 70, "BASIC": 55, "POOR": 38},
    "press_release_quality": {"TRANSPARENT": 92, "STANDARD": 80, "MINIMAL": 62, "UNCLEAR": 45},
    "leadership_visibility": {"HIGH": 88, "MODERATE": 75, "LOW": 58, "ABSENT": 42},
    "hiring_signals": {"STRONG_GROWTH": 88, "MODERATE_GROWTH": 78, "STABLE": 70, "CONTRACTING": 55, "LAYOFFS": 40},
    "governance_rating": {"EXCELLENT": 95, "GOOD": 85, "AVERAGE": 72, "BELOW_AVERAGE": 55, "POOR": 35},
    "iss_governance_score": {"1": 98, "2": 90, "3": 78, "4": 62, "5": 45, "6": 35, "7": 28, "8": 22, "9": 15, "10": 8},
    
    # FINANCIAL INSTITUTIONS
    "camels_rating": {"1": 98, "2": 88, "3": 68, "4": 42, "5": 18},
    "cra_rating": {"OUTSTANDING": 95, "SATISFACTORY": 82, "NEEDS_IMPROVEMENT": 55, "SUBSTANTIAL_NONCOMPLIANCE": 25},
    "bsa_aml_status": {"SATISFACTORY": 92, "NEEDS_IMPROVEMENT": 62, "DEFICIENT": 30, "CONSENT_ORDER": 15},
    "enforcement_action_status": {"NONE": 95, "MOU": 72, "BOARD_RESOLUTION": 65, "CONSENT_ORDER": 42, "CEASE_AND_DESIST": 25, "CMP": 35},
    "fair_lending_status": {"COMPLIANT": 92, "MINOR_ISSUES": 78, "MODERATE_ISSUES": 58, "SIGNIFICANT_ISSUES": 35, "DOJ_REFERRAL": 15},
    "consumer_compliance_status": {"SATISFACTORY": 92, "NEEDS_IMPROVEMENT": 65, "DEFICIENT": 35},
    "interest_rate_risk": {"LOW": 92, "MODERATE": 78, "ELEVATED": 60, "HIGH": 42, "CRITICAL": 22},
    "board_expertise": {"HIGHLY_QUALIFIED": 92, "QUALIFIED": 82, "ADEQUATE": 68, "LIMITED": 52, "DEFICIENT": 35},
    "audit_committee_quality": {"STRONG": 92, "ADEQUATE": 78, "WEAK": 55, "DEFICIENT": 35},
    "disclosure_quality": {"COMPREHENSIVE": 92, "STANDARD": 80, "LIMITED": 62, "MINIMAL": 45},
    "community_presence": {"STRONG": 88, "MODERATE": 75, "LIMITED": 60, "MINIMAL": 45},
    
    # ENERGY
    "permit_status": {"ALL_CURRENT": 95, "MINOR_PENDING": 85, "SIGNIFICANT_PENDING": 65, "DENIED_RECENT": 40, "MULTIPLE_DENIALS": 25},
    "regulatory_standing": {"GOOD_STANDING": 95, "MINOR_VIOLATIONS": 78, "NOV_OUTSTANDING": 58, "ENFORCEMENT_ACTION": 35, "CONSENT_DECREE": 25},
    "esg_rating": {"AAA": 98, "AA": 92, "A": 85, "BBB": 75, "BB": 62, "B": 48, "CCC": 32, "UNRATED": 50},
    "process_safety_status": {"EXCELLENT": 95, "GOOD": 85, "AVERAGE": 72, "BELOW_AVERAGE": 52, "POOR": 32},
    "emissions_status": {"COMPLIANT": 92, "MINOR_EXCEEDANCE": 78, "MODERATE_EXCEEDANCE": 58, "SIGNIFICANT_EXCEEDANCE": 35, "MAJOR_VIOLATION": 18},
    "remediation_status": {"NONE_REQUIRED": 95, "ACTIVE_ON_SCHEDULE": 82, "ACTIVE_DELAYED": 62, "STALLED": 42, "NON_COMPLIANT": 22},
    "facility_status": {"OPERATING": 90, "REDUCED": 75, "IDLE": 55, "SHUTIN": 40, "ABANDONED": 25},
    "well_integrity_status": {"EXCELLENT": 95, "GOOD": 85, "FAIR": 70, "CONCERNING": 50, "CRITICAL": 28},
    "capex_trend": {"INCREASING": 88, "STABLE": 78, "DECLINING": 62, "SEVERELY_CUT": 42},
    "decommissioning_status": {"FULLY_FUNDED": 92, "ADEQUATELY_FUNDED": 80, "UNDERFUNDED": 55, "SIGNIFICANTLY_UNDERFUNDED": 35},
    "insurance_history": {"EXCELLENT": 92, "GOOD": 82, "AVERAGE": 70, "ELEVATED_CLAIMS": 52, "HIGH_CLAIMS": 35},
    "regulator_relationship": {"EXCELLENT": 92, "GOOD": 82, "NEUTRAL": 70, "STRAINED": 52, "ADVERSARIAL": 35},
    
    # PROFESSIONAL INDEMNITY
    "license_status": {"ALL_ACTIVE": 95, "MOSTLY_ACTIVE": 85, "SOME_INACTIVE": 70, "SUSPENDED": 35, "DISBARRED": 5},
    "peer_review_rating": {"PASS": 95, "PASS_WITH_DEFICIENCY": 72, "FAIL": 35, "NOT_ENROLLED": 55},
    "disciplinary_history": {"NONE": 95, "PRIVATE_REPRIMAND": 82, "PUBLIC_REPRIMAND": 65, "SUSPENSION": 40, "DISBARMENT": 10},
    "pcaob_status": {"REGISTERED_CLEAN": 95, "REGISTERED_DEFICIENCIES": 72, "NOT_REGISTERED": 60, "SANCTIONED": 25},
    "referral_network_quality": {"STRONG": 92, "MODERATE": 78, "LIMITED": 62, "WEAK": 45},
    "thought_leadership": {"RECOGNIZED_EXPERT": 92, "ACTIVE_CONTRIBUTOR": 80, "OCCASIONAL": 65, "MINIMAL": 50, "NONE": 38},
    "office_stability": {"STABLE": 92, "NORMAL": 80, "SOME_CHANGES": 65, "FREQUENT_MOVES": 48, "UNSTABLE": 32},
    "firm_financial_status": {"STRONG": 92, "STABLE": 82, "ADEQUATE": 70, "STRAINED": 52, "DISTRESSED": 32},
    "outcome_quality": {"EXCELLENT": 92, "GOOD": 82, "AVERAGE": 70, "BELOW_AVERAGE": 55, "POOR": 38},
    "work_quality_indicators": {"EXCELLENT": 92, "GOOD": 82, "AVERAGE": 70, "INCONSISTENT": 52, "PROBLEMATIC": 32},
    "client_portal_security": {"ENTERPRISE": 92, "STANDARD": 78, "BASIC": 60, "NONE": 40},
    "practice_area_clarity": {"VERY_CLEAR": 92, "CLEAR": 82, "ADEQUATE": 70, "VAGUE": 52, "UNCLEAR": 35},
    
    # COMMON / CROSS-COVERAGE
    "credit_rating": {"AAA": 98, "AA_PLUS": 95, "AA": 92, "AA_MINUS": 90, "A_PLUS": 88, "A": 85, "A_MINUS": 82,
                      "BBB_PLUS": 78, "BBB": 75, "BBB_MINUS": 72, "BB_PLUS": 65, "BB": 60, "BB_MINUS": 55,
                      "B_PLUS": 48, "B": 42, "B_MINUS": 38, "CCC": 28, "CC": 18, "C": 12, "D": 5, "NR": 50},
    "website_quality": {"EXCELLENT": 92, "GOOD": 82, "AVERAGE": 70, "BASIC": 55, "POOR": 35, "NONE": 20},
    "industry_presence": {"LEADER": 95, "ESTABLISHED": 85, "GROWING": 72, "EMERGING": 60, "UNKNOWN": 45},
    "safety_communication": {"COMPREHENSIVE": 92, "GOOD": 82, "AVERAGE": 70, "BASIC": 55, "MINIMAL": 38},
    "crew_welfare_rating": {"EXCELLENT": 92, "GOOD": 82, "AVERAGE": 70, "BELOW_AVERAGE": 55, "POOR": 38},
    "port_relationship": {"PREFERRED": 92, "STANDARD": 78, "RESTRICTED": 55, "BANNED": 20},
}


# =============================================================================
# QUALITY TIER PROFILES (Entity Recognition)
# =============================================================================

QUALITY_TIER_PROFILES: Dict[str, List[QualityTier]] = {
    "classification_society": [
        {"tier": "IACS_PREMIER", "score": 98, "modifier": 0.88, "entities": ["DNV", "Lloyd's Register", "Bureau Veritas", "ABS", "ClassNK"]},
        {"tier": "IACS_MEMBER", "score": 92, "modifier": 0.92, "entities": ["RINA", "Korean Register", "CCS", "IRS", "PRS", "CRS"]},
        {"tier": "RECOGNIZED", "score": 75, "modifier": 1.00, "entities": ["Türk Loydu", "RMRS", "BKI", "VR"]},
        {"tier": "OTHER", "score": 55, "modifier": 1.15, "entities": []},
    ],
    "pi_club": [
        {"tier": "IG_PREMIER", "score": 98, "modifier": 0.85, "entities": ["Gard", "Britannia", "UK P&I Club", "Standard Club", "Steamship Mutual", "West of England"]},
        {"tier": "IG_MEMBER", "score": 92, "modifier": 0.90, "entities": ["North P&I", "Skuld", "Swedish Club", "Japan P&I", "London P&I", "American Club"]},
        {"tier": "FIXED_PREMIUM", "score": 70, "modifier": 1.05, "entities": ["Lodestar", "Hanseatic", "Raets", "Osprey"]},
        {"tier": "OTHER", "score": 50, "modifier": 1.20, "entities": []},
    ],
    "flag_state": [
        {"tier": "PREMIUM", "score": 95, "modifier": 0.88, "entities": ["Singapore", "Hong Kong", "Denmark", "Norway", "United Kingdom", "Japan", "Netherlands"]},
        {"tier": "STANDARD", "score": 85, "modifier": 0.95, "entities": ["Marshall Islands", "Liberia", "Bahamas", "Malta", "Cyprus", "Isle of Man", "Bermuda"]},
        {"tier": "ELEVATED_RISK", "score": 65, "modifier": 1.08, "entities": ["Panama", "Antigua", "Vanuatu", "St Kitts", "Belize"]},
        {"tier": "HIGH_RISK", "score": 45, "modifier": 1.25, "entities": ["Mongolia", "Bolivia", "Cameroon", "Sierra Leone", "Togo", "Moldova"]},
    ],
    "lessor_quality": [
        {"tier": "TIER_1", "score": 95, "modifier": 0.90, "entities": ["AerCap", "GECAS", "Avolon", "SMBC Aviation Capital", "BOC Aviation", "Air Lease"]},
        {"tier": "TIER_2", "score": 85, "modifier": 0.95, "entities": ["BBAM", "Nordic Aviation Capital", "Aviation Capital Group", "ICBC Leasing", "CDB Aviation"]},
        {"tier": "TIER_3", "score": 72, "modifier": 1.00, "entities": ["Jackson Square", "Aircastle", "Macquarie AirFinance", "Castlelake"]},
        {"tier": "OTHER", "score": 58, "modifier": 1.12, "entities": []},
    ],
    "mro_provider": [
        {"tier": "OEM_NETWORK", "score": 95, "modifier": 0.88, "entities": ["Lufthansa Technik", "AFI KLM E&M", "ST Aerospace", "HAECO", "SIA Engineering"]},
        {"tier": "MAJOR_INDEPENDENT", "score": 88, "modifier": 0.92, "entities": ["AAR", "MTU Aero Engines", "StandardAero", "Turkish Technic", "Ameco Beijing"]},
        {"tier": "REGIONAL", "score": 75, "modifier": 1.00, "entities": ["FL Technics", "Magnetic MRO", "MRO Holdings", "Joramco"]},
        {"tier": "BASIC", "score": 60, "modifier": 1.10, "entities": []},
    ],
    "auditor_quality": [
        {"tier": "BIG_FOUR", "score": 95, "modifier": 0.90, "entities": ["Deloitte", "PwC", "PricewaterhouseCoopers", "EY", "Ernst & Young", "KPMG"]},
        {"tier": "NATIONAL", "score": 85, "modifier": 0.95, "entities": ["BDO", "Grant Thornton", "RSM", "Crowe", "Baker Tilly", "CliftonLarsonAllen"]},
        {"tier": "REGIONAL", "score": 72, "modifier": 1.00, "entities": ["Moss Adams", "Plante Moran", "Wipfli", "Cherry Bekaert", "Armanino"]},
        {"tier": "LOCAL", "score": 58, "modifier": 1.12, "entities": []},
    ],
    "legal_counsel": [
        {"tier": "ELITE", "score": 95, "modifier": 0.88, "entities": ["Wachtell", "Cravath", "Sullivan & Cromwell", "Skadden", "Davis Polk", "Simpson Thacher"]},
        {"tier": "AM_LAW_50", "score": 88, "modifier": 0.92, "entities": ["Kirkland", "Latham", "Gibson Dunn", "Cleary", "Sidley", "Morgan Lewis", "Jones Day"]},
        {"tier": "AM_LAW_100", "score": 78, "modifier": 1.00, "entities": ["King & Spalding", "Ropes & Gray", "Cooley", "WilmerHale", "Goodwin"]},
        {"tier": "REGIONAL", "score": 65, "modifier": 1.08, "entities": []},
    ],
    "correspondent_bank": [
        {"tier": "GSIB", "score": 95, "modifier": 0.88, "entities": ["JPMorgan", "Bank of America", "Citibank", "Wells Fargo", "HSBC", "Deutsche Bank"]},
        {"tier": "LARGE_REGIONAL", "score": 85, "modifier": 0.95, "entities": ["PNC", "US Bancorp", "Truist", "TD Bank", "Fifth Third", "KeyBank"]},
        {"tier": "COMMUNITY", "score": 72, "modifier": 1.00, "entities": []},
    ],
    "firm_ranking": [
        {"tier": "AM_LAW_100", "score": 95, "modifier": 0.88, "entities": ["Kirkland & Ellis", "Latham & Watkins", "DLA Piper", "Baker McKenzie", "Skadden"]},
        {"tier": "AM_LAW_200", "score": 85, "modifier": 0.92, "entities": ["Foley & Lardner", "Duane Morris", "Greenberg Traurig", "Reed Smith"]},
        {"tier": "REGIONAL_LEADER", "score": 78, "modifier": 1.00, "entities": []},
        {"tier": "BOUTIQUE", "score": 72, "modifier": 1.05, "entities": []},
        {"tier": "SMALL_FIRM", "score": 62, "modifier": 1.12, "entities": []},
    ],
    "customer_tier": [
        {"tier": "ENTERPRISE", "score": 95, "modifier": 0.88, "entities": ["Fortune 500", "Global 2000"]},
        {"tier": "MID_MARKET", "score": 82, "modifier": 0.95, "entities": []},
        {"tier": "SMB", "score": 70, "modifier": 1.00, "entities": []},
        {"tier": "STARTUP", "score": 58, "modifier": 1.08, "entities": []},
    ],
    "partner_tier": [
        {"tier": "STRATEGIC", "score": 92, "modifier": 0.90, "entities": ["Microsoft", "Google", "AWS", "Salesforce"]},
        {"tier": "PREMIER", "score": 85, "modifier": 0.95, "entities": []},
        {"tier": "STANDARD", "score": 75, "modifier": 1.00, "entities": []},
        {"tier": "BASIC", "score": 62, "modifier": 1.08, "entities": []},
    ],
    "security_vendor_tier": [
        {"tier": "LEADER", "score": 95, "modifier": 0.88, "entities": ["CrowdStrike", "Palo Alto", "Microsoft", "Zscaler", "Okta"]},
        {"tier": "ESTABLISHED", "score": 85, "modifier": 0.95, "entities": ["Fortinet", "SentinelOne", "Rapid7", "Tenable"]},
        {"tier": "EMERGING", "score": 72, "modifier": 1.00, "entities": []},
        {"tier": "UNKNOWN", "score": 55, "modifier": 1.12, "entities": []},
    ],
    "investor_tier": [
        {"tier": "TIER_1", "score": 95, "modifier": 0.88, "entities": ["Blackrock", "Vanguard", "Fidelity", "State Street", "Capital Group"]},
        {"tier": "TIER_2", "score": 85, "modifier": 0.95, "entities": ["Wellington", "T. Rowe Price", "Invesco", "Franklin Templeton"]},
        {"tier": "TIER_3", "score": 75, "modifier": 1.00, "entities": []},
        {"tier": "OTHER", "score": 62, "modifier": 1.08, "entities": []},
    ],
    "jv_partner_tier": [
        {"tier": "SUPERMAJOR", "score": 95, "modifier": 0.85, "entities": ["ExxonMobil", "Shell", "Chevron", "BP", "TotalEnergies"]},
        {"tier": "MAJOR", "score": 88, "modifier": 0.92, "entities": ["ConocoPhillips", "Equinor", "Eni", "Occidental"]},
        {"tier": "LARGE_INDEPENDENT", "score": 78, "modifier": 1.00, "entities": ["Devon", "Pioneer", "EOG", "Marathon Oil"]},
        {"tier": "OTHER", "score": 65, "modifier": 1.10, "entities": []},
    ],
    "contractor_tier": [
        {"tier": "TIER_1", "score": 92, "modifier": 0.90, "entities": ["Schlumberger", "Halliburton", "Baker Hughes", "Transocean"]},
        {"tier": "TIER_2", "score": 82, "modifier": 0.95, "entities": ["Patterson-UTI", "Nabors", "Helmerich & Payne"]},
        {"tier": "TIER_3", "score": 70, "modifier": 1.00, "entities": []},
        {"tier": "LOCAL", "score": 58, "modifier": 1.12, "entities": []},
    ],
    "client_tier": [
        {"tier": "BLUE_CHIP", "score": 95, "modifier": 0.88, "entities": ["Fortune 100", "Government"]},
        {"tier": "ESTABLISHED", "score": 85, "modifier": 0.95, "entities": []},
        {"tier": "MID_MARKET", "score": 75, "modifier": 1.00, "entities": []},
        {"tier": "EMERGING", "score": 62, "modifier": 1.08, "entities": []},
    ],
}


# =============================================================================
# BOOLEAN FLAG DEFINITIONS (Part 2)
# =============================================================================

BOOLEAN_FLAG_PROFILES_EXTENDED: Dict[str, Dict[str, Dict[str, Any]]] = {
    # Energy
    "vpp_participant": {"true": {"score": 92, "modifier": 0.88, "message": "VPP participant"}, "false": {"score": 72, "modifier": 1.00, "message": "Not VPP participant"}},
    "iso_45001_certified": {"true": {"score": 90, "modifier": 0.90, "message": "ISO 45001 certified"}, "false": {"score": 70, "modifier": 1.00, "message": "No ISO 45001"}},
    "net_zero_commitment": {"true": {"score": 85, "modifier": 0.95, "message": "Net zero commitment"}, "false": {"score": 70, "modifier": 1.00, "message": "No net zero commitment"}},
    "superfund_exposure": {"true": {"score": 35, "modifier": 1.35, "action": "REFER", "message": "Superfund exposure"}, "false": {"score": 90, "modifier": 1.00, "message": "No Superfund exposure"}},
    "restructuring_history": {"true": {"score": 55, "modifier": 1.15, "action": "FLAG", "message": "Restructuring history"}, "false": {"score": 85, "modifier": 1.00, "message": "No restructuring"}},
    "technical_hiring_active": {"true": {"score": 82, "modifier": 0.95, "message": "Technical hiring active"}, "false": {"score": 70, "modifier": 1.00, "message": "No technical hiring"}},
    "dedicated_hse_officer": {"true": {"score": 90, "modifier": 0.92, "message": "Dedicated HSE officer"}, "false": {"score": 65, "modifier": 1.05, "message": "No dedicated HSE officer"}},
    
    # Professional Indemnity
    "claims_made_coverage": {"true": {"score": 85, "modifier": 0.95, "message": "Claims-made history"}, "false": {"score": 65, "modifier": 1.10, "message": "No prior claims-made"}},
    "peer_review_enrolled": {"true": {"score": 88, "modifier": 0.92, "message": "Peer review enrolled"}, "false": {"score": 62, "modifier": 1.10, "message": "Not peer review enrolled"}},
    "cpe_compliant": {"true": {"score": 90, "modifier": 0.95, "message": "CPE compliant"}, "false": {"score": 55, "modifier": 1.15, "message": "CPE non-compliant"}},
    "specialty_certified": {"true": {"score": 88, "modifier": 0.92, "message": "Specialty certified"}, "false": {"score": 72, "modifier": 1.00, "message": "No specialty certification"}},
    "association_leader": {"true": {"score": 90, "modifier": 0.90, "message": "Association leader"}, "false": {"score": 72, "modifier": 1.00, "message": "Not association leader"}},
    "insurance_panel_member": {"true": {"score": 85, "modifier": 0.95, "message": "Insurance panel member"}, "false": {"score": 70, "modifier": 1.00, "message": "Not panel member"}},
    "succession_plan": {"true": {"score": 88, "modifier": 0.95, "message": "Succession plan exists"}, "false": {"score": 62, "modifier": 1.08, "message": "No succession plan"}},
    "pro_bono_program": {"true": {"score": 82, "modifier": 0.95, "message": "Pro bono program"}, "false": {"score": 72, "modifier": 1.00, "message": "No pro bono program"}},
    "prior_bankruptcy": {"true": {"score": 35, "modifier": 1.35, "action": "REFER", "message": "Prior bankruptcy"}, "false": {"score": 92, "modifier": 1.00, "message": "No bankruptcy history"}},
}


# =============================================================================
# CONDITION BANDS (Value -> Action)
# =============================================================================

CONDITION_BANDS: Dict[str, List[Dict[str, Any]]] = {
    "detention_count": [
        {"min_value": 0, "max_value": 0, "action": "APPROVE", "message": "No detentions", "modifier": 0.90},
        {"min_value": 1, "max_value": 1, "action": "FLAG", "message": "Single detention", "modifier": 1.05},
        {"min_value": 2, "max_value": 2, "action": "REFER", "message": "Multiple detentions", "modifier": 1.20},
        {"min_value": 3, "max_value": float("inf"), "action": "DECLINE", "message": "Excessive detentions", "modifier": 1.50},
    ],
    "class_action_count": [
        {"min_value": 0, "max_value": 0, "action": "APPROVE", "message": "No class actions", "modifier": 1.00},
        {"min_value": 1, "max_value": 1, "action": "REFER", "message": "Active class action", "modifier": 1.25},
        {"min_value": 2, "max_value": float("inf"), "action": "DECLINE", "message": "Multiple class actions", "modifier": 1.50},
    ],
    "breach_records_count": [
        {"min_value": 0, "max_value": 0, "action": "APPROVE", "message": "No breach history", "modifier": 0.92},
        {"min_value": 1, "max_value": 1, "action": "FLAG", "message": "Single breach", "modifier": 1.08},
        {"min_value": 2, "max_value": 3, "action": "REFER", "message": "Multiple breaches", "modifier": 1.25},
        {"min_value": 4, "max_value": float("inf"), "action": "DECLINE", "message": "Serial breacher", "modifier": 1.50},
    ],
    "fatality_count": [
        {"min_value": 0, "max_value": 0, "action": "APPROVE", "message": "No fatalities", "modifier": 1.00},
        {"min_value": 1, "max_value": float("inf"), "action": "REFER", "message": "Fatality history", "modifier": 1.35},
    ],
    "enforcement_action_count": [
        {"min_value": 0, "max_value": 0, "action": "APPROVE", "message": "No enforcement actions", "modifier": 0.95},
        {"min_value": 1, "max_value": 2, "action": "FLAG", "message": "Minor enforcement history", "modifier": 1.10},
        {"min_value": 3, "max_value": float("inf"), "action": "REFER", "message": "Significant enforcement history", "modifier": 1.30},
    ],
    "accident_count": [
        {"min_value": 0, "max_value": 0, "action": "APPROVE", "message": "No accidents", "modifier": 0.90},
        {"min_value": 1, "max_value": 1, "action": "FLAG", "message": "Single accident", "modifier": 1.12},
        {"min_value": 2, "max_value": float("inf"), "action": "REFER", "message": "Multiple accidents", "modifier": 1.35},
    ],
    "incident_count": [
        {"min_value": 0, "max_value": 2, "action": "APPROVE", "message": "Normal incident level", "modifier": 1.00},
        {"min_value": 3, "max_value": 5, "action": "FLAG", "message": "Elevated incidents", "modifier": 1.08},
        {"min_value": 6, "max_value": float("inf"), "action": "REFER", "message": "High incident count", "modifier": 1.22},
    ],
    "regulatory_action_count": [
        {"min_value": 0, "max_value": 0, "action": "APPROVE", "message": "No regulatory actions", "modifier": 0.95},
        {"min_value": 1, "max_value": 1, "action": "FLAG", "message": "Single regulatory action", "modifier": 1.08},
        {"min_value": 2, "max_value": float("inf"), "action": "REFER", "message": "Multiple regulatory actions", "modifier": 1.25},
    ],
    "sec_enforcement_count": [
        {"min_value": 0, "max_value": 0, "action": "APPROVE", "message": "No SEC enforcement", "modifier": 0.95},
        {"min_value": 1, "max_value": float("inf"), "action": "REFER", "message": "SEC enforcement history", "modifier": 1.35},
    ],
    "derivative_suit_count": [
        {"min_value": 0, "max_value": 0, "action": "APPROVE", "message": "No derivative suits", "modifier": 1.00},
        {"min_value": 1, "max_value": float("inf"), "action": "FLAG", "message": "Derivative suit history", "modifier": 1.15},
    ],
    "related_party_transaction_count": [
        {"min_value": 0, "max_value": 2, "action": "APPROVE", "message": "Minimal related party transactions", "modifier": 1.00},
        {"min_value": 3, "max_value": 5, "action": "FLAG", "message": "Multiple related party transactions", "modifier": 1.08},
        {"min_value": 6, "max_value": float("inf"), "action": "REFER", "message": "Excessive related party transactions", "modifier": 1.20},
    ],
    "fi_litigation_count": [
        {"min_value": 0, "max_value": 0, "action": "APPROVE", "message": "No litigation", "modifier": 0.95},
        {"min_value": 1, "max_value": 2, "action": "FLAG", "message": "Minor litigation", "modifier": 1.05},
        {"min_value": 3, "max_value": float("inf"), "action": "REFER", "message": "Significant litigation", "modifier": 1.22},
    ],
    "operational_incident_count": [
        {"min_value": 0, "max_value": 1, "action": "APPROVE", "message": "Minimal incidents", "modifier": 1.00},
        {"min_value": 2, "max_value": 3, "action": "FLAG", "message": "Multiple incidents", "modifier": 1.10},
        {"min_value": 4, "max_value": float("inf"), "action": "REFER", "message": "Frequent incidents", "modifier": 1.25},
    ],
    "osha_violation_count": [
        {"min_value": 0, "max_value": 0, "action": "APPROVE", "message": "No OSHA violations", "modifier": 0.92},
        {"min_value": 1, "max_value": 2, "action": "FLAG", "message": "Minor OSHA violations", "modifier": 1.05},
        {"min_value": 3, "max_value": 5, "action": "REFER", "message": "Multiple OSHA violations", "modifier": 1.20},
        {"min_value": 6, "max_value": float("inf"), "action": "DECLINE", "message": "Excessive OSHA violations", "modifier": 1.45},
    ],
    "bsee_incident_count": [
        {"min_value": 0, "max_value": 0, "action": "APPROVE", "message": "No BSEE incidents", "modifier": 0.95},
        {"min_value": 1, "max_value": 2, "action": "FLAG", "message": "Minor BSEE incidents", "modifier": 1.08},
        {"min_value": 3, "max_value": float("inf"), "action": "REFER", "message": "Multiple BSEE incidents", "modifier": 1.28},
    ],
    "major_incident_count": [
        {"min_value": 0, "max_value": 0, "action": "APPROVE", "message": "No major incidents", "modifier": 0.90},
        {"min_value": 1, "max_value": float("inf"), "action": "REFER", "message": "Major incident history", "modifier": 1.40},
    ],
    "epa_violation_count": [
        {"min_value": 0, "max_value": 0, "action": "APPROVE", "message": "No EPA violations", "modifier": 0.92},
        {"min_value": 1, "max_value": 2, "action": "FLAG", "message": "Minor EPA violations", "modifier": 1.08},
        {"min_value": 3, "max_value": float("inf"), "action": "REFER", "message": "Multiple EPA violations", "modifier": 1.30},
    ],
    "spill_count": [
        {"min_value": 0, "max_value": 0, "action": "APPROVE", "message": "No spills", "modifier": 0.92},
        {"min_value": 1, "max_value": 2, "action": "FLAG", "message": "Minor spills", "modifier": 1.08},
        {"min_value": 3, "max_value": float("inf"), "action": "REFER", "message": "Multiple spills", "modifier": 1.28},
    ],
    "malpractice_suit_count": [
        {"min_value": 0, "max_value": 0, "action": "APPROVE", "message": "No malpractice suits", "modifier": 0.90},
        {"min_value": 1, "max_value": 1, "action": "FLAG", "message": "Single malpractice suit", "modifier": 1.12},
        {"min_value": 2, "max_value": 3, "action": "REFER", "message": "Multiple malpractice suits", "modifier": 1.30},
        {"min_value": 4, "max_value": float("inf"), "action": "DECLINE", "message": "Excessive malpractice suits", "modifier": 1.50},
    ],
    "fee_dispute_count": [
        {"min_value": 0, "max_value": 1, "action": "APPROVE", "message": "Minimal fee disputes", "modifier": 1.00},
        {"min_value": 2, "max_value": 3, "action": "FLAG", "message": "Multiple fee disputes", "modifier": 1.08},
        {"min_value": 4, "max_value": float("inf"), "action": "REFER", "message": "Frequent fee disputes", "modifier": 1.20},
    ],
    "client_complaint_count": [
        {"min_value": 0, "max_value": 1, "action": "APPROVE", "message": "Minimal complaints", "modifier": 1.00},
        {"min_value": 2, "max_value": 4, "action": "FLAG", "message": "Multiple complaints", "modifier": 1.08},
        {"min_value": 5, "max_value": float("inf"), "action": "REFER", "message": "Frequent complaints", "modifier": 1.22},
    ],
    "fee_litigation_count": [
        {"min_value": 0, "max_value": 0, "action": "APPROVE", "message": "No fee litigation", "modifier": 1.00},
        {"min_value": 1, "max_value": 2, "action": "FLAG", "message": "Minor fee litigation", "modifier": 1.08},
        {"min_value": 3, "max_value": float("inf"), "action": "REFER", "message": "Frequent fee litigation", "modifier": 1.22},
    ],
    "regulatory_enforcement_count": [
        {"min_value": 0, "max_value": 0, "action": "APPROVE", "message": "No regulatory enforcement", "modifier": 0.95},
        {"min_value": 1, "max_value": float("inf"), "action": "REFER", "message": "Regulatory enforcement history", "modifier": 1.30},
    ],
    "civil_litigation_count": [
        {"min_value": 0, "max_value": 1, "action": "APPROVE", "message": "Minimal civil litigation", "modifier": 1.00},
        {"min_value": 2, "max_value": 3, "action": "FLAG", "message": "Multiple civil matters", "modifier": 1.08},
        {"min_value": 4, "max_value": float("inf"), "action": "REFER", "message": "Frequent civil litigation", "modifier": 1.20},
    ],
    "cyber_litigation_count": [
        {"min_value": 0, "max_value": 0, "action": "APPROVE", "message": "No cyber litigation", "modifier": 0.95},
        {"min_value": 1, "max_value": float("inf"), "action": "FLAG", "message": "Cyber litigation history", "modifier": 1.18},
    ],
    "historical_sanctions_count": [
        {"min_value": 0, "max_value": 0, "action": "APPROVE", "message": "No sanctions history", "modifier": 0.95},
        {"min_value": 1, "max_value": float("inf"), "action": "REFER", "message": "Historical sanctions", "modifier": 1.35},
    ],
    "environmental_incident_count": [
        {"min_value": 0, "max_value": 0, "action": "APPROVE", "message": "No environmental incidents", "modifier": 0.92},
        {"min_value": 1, "max_value": 2, "action": "FLAG", "message": "Minor environmental incidents", "modifier": 1.08},
        {"min_value": 3, "max_value": float("inf"), "action": "REFER", "message": "Multiple environmental incidents", "modifier": 1.25},
    ],
}


# =============================================================================
# SIGNAL WEIGHT PROFILES (For Composite Scoring)
# =============================================================================

SIGNAL_WEIGHT_PROFILES: Dict[str, Dict[str, SignalWeight]] = {
    "marine": {
        "psc_detention": {"weight": 0.12, "critical": True, "critical_threshold": 40, "missing_strategy": "penalize", "default_value": 50},
        "class_status": {"weight": 0.10, "critical": True, "critical_threshold": 35, "missing_strategy": "penalize", "default_value": 50},
        "ism_compliance": {"weight": 0.08, "critical": True, "critical_threshold": 40, "missing_strategy": "penalize", "default_value": 50},
        "casualty_history": {"weight": 0.08, "critical": True, "critical_threshold": 30, "missing_strategy": "penalize", "default_value": 50},
        "sanctions_status": {"weight": 0.12, "critical": True, "critical_threshold": 50, "missing_strategy": "require", "default_value": 0},
        "ownership_transparency": {"weight": 0.06, "critical": False, "critical_threshold": 0, "missing_strategy": "penalize", "default_value": 50},
        "fleet_age": {"weight": 0.06, "critical": False, "critical_threshold": 0, "missing_strategy": "use_default", "default_value": 65},
        "fleet_stability": {"weight": 0.04, "critical": False, "critical_threshold": 0, "missing_strategy": "exclude", "default_value": 70},
        "classification_society": {"weight": 0.06, "critical": False, "critical_threshold": 0, "missing_strategy": "use_default", "default_value": 70},
        "pi_club": {"weight": 0.05, "critical": False, "critical_threshold": 0, "missing_strategy": "use_default", "default_value": 70},
        "flag_state": {"weight": 0.05, "critical": False, "critical_threshold": 0, "missing_strategy": "use_default", "default_value": 70},
        "ais_compliance": {"weight": 0.06, "critical": False, "critical_threshold": 30, "missing_strategy": "use_default", "default_value": 70},
        "dark_activity": {"weight": 0.05, "critical": False, "critical_threshold": 30, "missing_strategy": "exclude", "default_value": 75},
        "cii_rating": {"weight": 0.04, "critical": False, "critical_threshold": 0, "missing_strategy": "exclude", "default_value": 70},
        "environmental_incident": {"weight": 0.03, "critical": False, "critical_threshold": 25, "missing_strategy": "exclude", "default_value": 80},
    },
    "aerospace": {
        "accident_history": {"weight": 0.15, "critical": True, "critical_threshold": 35, "missing_strategy": "penalize", "default_value": 50},
        "accident_rate": {"weight": 0.12, "critical": True, "critical_threshold": 40, "missing_strategy": "penalize", "default_value": 50},
        "fatality_history": {"weight": 0.10, "critical": True, "critical_threshold": 30, "missing_strategy": "penalize", "default_value": 50},
        "certificate_status": {"weight": 0.10, "critical": True, "critical_threshold": 50, "missing_strategy": "require", "default_value": 0},
        "iosa_audit_status": {"weight": 0.08, "critical": False, "critical_threshold": 0, "missing_strategy": "penalize", "default_value": 55},
        "enforcement_actions": {"weight": 0.06, "critical": False, "critical_threshold": 30, "missing_strategy": "use_default", "default_value": 65},
        "fleet_age": {"weight": 0.06, "critical": False, "critical_threshold": 0, "missing_strategy": "use_default", "default_value": 65},
        "fleet_homogeneity": {"weight": 0.04, "critical": False, "critical_threshold": 0, "missing_strategy": "exclude", "default_value": 70},
        "otp_score": {"weight": 0.05, "critical": False, "critical_threshold": 0, "missing_strategy": "exclude", "default_value": 70},
        "dispatch_reliability": {"weight": 0.04, "critical": False, "critical_threshold": 0, "missing_strategy": "exclude", "default_value": 75},
        "conflict_zone_exposure": {"weight": 0.06, "critical": False, "critical_threshold": 25, "missing_strategy": "use_default", "default_value": 80},
        "challenging_airports": {"weight": 0.04, "critical": False, "critical_threshold": 0, "missing_strategy": "exclude", "default_value": 75},
        "credit_rating": {"weight": 0.05, "critical": False, "critical_threshold": 0, "missing_strategy": "use_default", "default_value": 65},
        "market_position": {"weight": 0.05, "critical": False, "critical_threshold": 0, "missing_strategy": "exclude", "default_value": 70},
    },
    "cyber": {
        "security_rating": {"weight": 0.15, "critical": True, "critical_threshold": 40, "missing_strategy": "penalize", "default_value": 50},
        "tls_score": {"weight": 0.08, "critical": False, "critical_threshold": 30, "missing_strategy": "use_default", "default_value": 60},
        "email_auth": {"weight": 0.08, "critical": False, "critical_threshold": 30, "missing_strategy": "use_default", "default_value": 55},
        "cve_exposure": {"weight": 0.08, "critical": False, "critical_threshold": 25, "missing_strategy": "use_default", "default_value": 60},
        "breach_history": {"weight": 0.12, "critical": True, "critical_threshold": 35, "missing_strategy": "penalize", "default_value": 50},
        "regulatory_action": {"weight": 0.06, "critical": False, "critical_threshold": 30, "missing_strategy": "exclude", "default_value": 75},
        "credential_exposure": {"weight": 0.06, "critical": False, "critical_threshold": 25, "missing_strategy": "use_default", "default_value": 65},
        "security_page": {"weight": 0.04, "critical": False, "critical_threshold": 0, "missing_strategy": "exclude", "default_value": 65},
        "bug_bounty": {"weight": 0.05, "critical": False, "critical_threshold": 0, "missing_strategy": "exclude", "default_value": 60},
        "customer_quality": {"weight": 0.06, "critical": False, "critical_threshold": 0, "missing_strategy": "exclude", "default_value": 70},
        "security_vendor": {"weight": 0.06, "critical": False, "critical_threshold": 0, "missing_strategy": "exclude", "default_value": 65},
        "certification_authority": {"weight": 0.08, "critical": False, "critical_threshold": 0, "missing_strategy": "use_default", "default_value": 60},
        "credit_rating": {"weight": 0.05, "critical": False, "critical_threshold": 0, "missing_strategy": "exclude", "default_value": 65},
        "esg_cyber": {"weight": 0.03, "critical": False, "critical_threshold": 0, "missing_strategy": "exclude", "default_value": 70},
    },
    "d_and_o": {
        "board_independence": {"weight": 0.08, "critical": False, "critical_threshold": 0, "missing_strategy": "use_default", "default_value": 65},
        "ceo_chair_separation": {"weight": 0.05, "critical": False, "critical_threshold": 0, "missing_strategy": "exclude", "default_value": 70},
        "committee_structure": {"weight": 0.05, "critical": False, "critical_threshold": 0, "missing_strategy": "exclude", "default_value": 70},
        "audit_opinion": {"weight": 0.12, "critical": True, "critical_threshold": 50, "missing_strategy": "penalize", "default_value": 50},
        "internal_controls": {"weight": 0.10, "critical": True, "critical_threshold": 45, "missing_strategy": "penalize", "default_value": 50},
        "restatement": {"weight": 0.08, "critical": False, "critical_threshold": 35, "missing_strategy": "use_default", "default_value": 75},
        "securities_litigation": {"weight": 0.12, "critical": True, "critical_threshold": 40, "missing_strategy": "penalize", "default_value": 50},
        "sec_enforcement": {"weight": 0.10, "critical": True, "critical_threshold": 35, "missing_strategy": "penalize", "default_value": 50},
        "derivative_litigation": {"weight": 0.06, "critical": False, "critical_threshold": 30, "missing_strategy": "use_default", "default_value": 70},
        "executive_stability": {"weight": 0.05, "critical": False, "critical_threshold": 0, "missing_strategy": "exclude", "default_value": 70},
        "insider_trading": {"weight": 0.06, "critical": False, "critical_threshold": 30, "missing_strategy": "use_default", "default_value": 75},
        "stock_volatility": {"weight": 0.05, "critical": False, "critical_threshold": 0, "missing_strategy": "exclude", "default_value": 65},
        "short_interest": {"weight": 0.05, "critical": False, "critical_threshold": 30, "missing_strategy": "exclude", "default_value": 70},
        "credit_rating": {"weight": 0.03, "critical": False, "critical_threshold": 0, "missing_strategy": "exclude", "default_value": 65},
    },
    "financial_institutions": {
        "examination_rating": {"weight": 0.15, "critical": True, "critical_threshold": 50, "missing_strategy": "penalize", "default_value": 50},
        "enforcement_action": {"weight": 0.10, "critical": True, "critical_threshold": 40, "missing_strategy": "penalize", "default_value": 50},
        "bsa_aml": {"weight": 0.08, "critical": True, "critical_threshold": 40, "missing_strategy": "penalize", "default_value": 50},
        "cra_rating": {"weight": 0.05, "critical": False, "critical_threshold": 0, "missing_strategy": "use_default", "default_value": 70},
        "capital_ratio": {"weight": 0.12, "critical": True, "critical_threshold": 45, "missing_strategy": "penalize", "default_value": 50},
        "asset_quality": {"weight": 0.10, "critical": True, "critical_threshold": 40, "missing_strategy": "penalize", "default_value": 50},
        "liquidity": {"weight": 0.06, "critical": False, "critical_threshold": 30, "missing_strategy": "use_default", "default_value": 65},
        "earnings": {"weight": 0.05, "critical": False, "critical_threshold": 0, "missing_strategy": "use_default", "default_value": 65},
        "concentration": {"weight": 0.05, "critical": False, "critical_threshold": 25, "missing_strategy": "use_default", "default_value": 70},
        "board_independence": {"weight": 0.04, "critical": False, "critical_threshold": 0, "missing_strategy": "exclude", "default_value": 70},
        "risk_committee": {"weight": 0.04, "critical": False, "critical_threshold": 0, "missing_strategy": "exclude", "default_value": 70},
        "cfpb_complaint": {"weight": 0.04, "critical": False, "critical_threshold": 25, "missing_strategy": "exclude", "default_value": 75},
        "breach_history": {"weight": 0.04, "critical": False, "critical_threshold": 30, "missing_strategy": "exclude", "default_value": 75},
        "security_rating": {"weight": 0.05, "critical": False, "critical_threshold": 35, "missing_strategy": "use_default", "default_value": 60},
        "credit_rating": {"weight": 0.03, "critical": False, "critical_threshold": 0, "missing_strategy": "exclude", "default_value": 65},
    },
    "energy": {
        "osha_trir": {"weight": 0.12, "critical": True, "critical_threshold": 40, "missing_strategy": "penalize", "default_value": 50},
        "osha_violations": {"weight": 0.08, "critical": True, "critical_threshold": 35, "missing_strategy": "penalize", "default_value": 50},
        "fatality": {"weight": 0.10, "critical": True, "critical_threshold": 30, "missing_strategy": "penalize", "default_value": 50},
        "process_safety": {"weight": 0.08, "critical": True, "critical_threshold": 35, "missing_strategy": "penalize", "default_value": 50},
        "epa_violation": {"weight": 0.08, "critical": True, "critical_threshold": 35, "missing_strategy": "penalize", "default_value": 50},
        "spill_history": {"weight": 0.06, "critical": False, "critical_threshold": 30, "missing_strategy": "use_default", "default_value": 70},
        "emissions_compliance": {"weight": 0.05, "critical": False, "critical_threshold": 0, "missing_strategy": "use_default", "default_value": 70},
        "production_consistency": {"weight": 0.05, "critical": False, "critical_threshold": 0, "missing_strategy": "exclude", "default_value": 70},
        "well_integrity": {"weight": 0.05, "critical": False, "critical_threshold": 30, "missing_strategy": "use_default", "default_value": 70},
        "credit_rating": {"weight": 0.06, "critical": False, "critical_threshold": 0, "missing_strategy": "use_default", "default_value": 65},
        "leverage": {"weight": 0.05, "critical": False, "critical_threshold": 25, "missing_strategy": "use_default", "default_value": 65},
        "aro_coverage": {"weight": 0.04, "critical": False, "critical_threshold": 0, "missing_strategy": "exclude", "default_value": 70},
        "decommissioning": {"weight": 0.04, "critical": False, "critical_threshold": 0, "missing_strategy": "exclude", "default_value": 70},
        "permit_status": {"weight": 0.05, "critical": False, "critical_threshold": 30, "missing_strategy": "use_default", "default_value": 75},
        "esg_rating": {"weight": 0.05, "critical": False, "critical_threshold": 0, "missing_strategy": "exclude", "default_value": 65},
        "ghg_intensity": {"weight": 0.04, "critical": False, "critical_threshold": 0, "missing_strategy": "exclude", "default_value": 65},
    },
    "professional_indemnity": {
        "license_status": {"weight": 0.12, "critical": True, "critical_threshold": 50, "missing_strategy": "require", "default_value": 0},
        "disciplinary_history": {"weight": 0.10, "critical": True, "critical_threshold": 40, "missing_strategy": "penalize", "default_value": 50},
        "malpractice_record": {"weight": 0.12, "critical": True, "critical_threshold": 40, "missing_strategy": "penalize", "default_value": 50},
        "peer_review": {"weight": 0.06, "critical": False, "critical_threshold": 0, "missing_strategy": "use_default", "default_value": 65},
        "ce_compliance": {"weight": 0.05, "critical": False, "critical_threshold": 35, "missing_strategy": "use_default", "default_value": 70},
        "specialty_certification": {"weight": 0.04, "critical": False, "critical_threshold": 0, "missing_strategy": "exclude", "default_value": 70},
        "peer_ranking": {"weight": 0.06, "critical": False, "critical_threshold": 0, "missing_strategy": "exclude", "default_value": 65},
        "client_quality": {"weight": 0.05, "critical": False, "critical_threshold": 0, "missing_strategy": "exclude", "default_value": 70},
        "panel_membership": {"weight": 0.04, "critical": False, "critical_threshold": 0, "missing_strategy": "exclude", "default_value": 70},
        "tenure": {"weight": 0.05, "critical": False, "critical_threshold": 0, "missing_strategy": "use_default", "default_value": 65},
        "partner_stability": {"weight": 0.05, "critical": False, "critical_threshold": 0, "missing_strategy": "use_default", "default_value": 70},
        "staff_retention": {"weight": 0.04, "critical": False, "critical_threshold": 0, "missing_strategy": "exclude", "default_value": 70},
        "financial_stability": {"weight": 0.06, "critical": False, "critical_threshold": 30, "missing_strategy": "use_default", "default_value": 65},
        "malpractice_suits": {"weight": 0.08, "critical": True, "critical_threshold": 40, "missing_strategy": "penalize", "default_value": 50},
        "fee_disputes_litigation": {"weight": 0.04, "critical": False, "critical_threshold": 0, "missing_strategy": "exclude", "default_value": 75},
        "breach_history": {"weight": 0.04, "critical": False, "critical_threshold": 30, "missing_strategy": "exclude", "default_value": 80},
    },
}


# =============================================================================
# TIER PROFILES (Score -> Risk Tier Mapping)
# =============================================================================

TIER_PROFILES: Dict[str, Dict[str, Any]] = {
    "default": {
        "tiers": [
            {"tier": "TIER_1_PREFERRED", "min_score": 90, "max_score": 100, "auto_approve": True, "auto_decline": False, "referral_level": None},
            {"tier": "TIER_2_STANDARD", "min_score": 75, "max_score": 89.99, "auto_approve": False, "auto_decline": False, "referral_level": "UNDERWRITER"},
            {"tier": "TIER_3_SUBSTANDARD", "min_score": 55, "max_score": 74.99, "auto_approve": False, "auto_decline": False, "referral_level": "SENIOR_UNDERWRITER"},
            {"tier": "TIER_4_HIGH_RISK", "min_score": 35, "max_score": 54.99, "auto_approve": False, "auto_decline": False, "referral_level": "CHIEF_UNDERWRITER"},
            {"tier": "TIER_5_DECLINE", "min_score": 0, "max_score": 34.99, "auto_approve": False, "auto_decline": True, "referral_level": None},
        ]
    },
    "marine": {
        "tiers": [
            {"tier": "MARINE_PREMIER", "min_score": 88, "max_score": 100, "auto_approve": True, "auto_decline": False, "referral_level": None},
            {"tier": "MARINE_STANDARD", "min_score": 72, "max_score": 87.99, "auto_approve": False, "auto_decline": False, "referral_level": "UNDERWRITER"},
            {"tier": "MARINE_ELEVATED", "min_score": 55, "max_score": 71.99, "auto_approve": False, "auto_decline": False, "referral_level": "SENIOR_UNDERWRITER"},
            {"tier": "MARINE_HIGH_RISK", "min_score": 40, "max_score": 54.99, "auto_approve": False, "auto_decline": False, "referral_level": "MARINE_LEADER"},
            {"tier": "MARINE_DECLINE", "min_score": 0, "max_score": 39.99, "auto_approve": False, "auto_decline": True, "referral_level": None},
        ]
    },
    "aerospace": {
        "tiers": [
            {"tier": "AEROSPACE_PREMIER", "min_score": 90, "max_score": 100, "auto_approve": True, "auto_decline": False, "referral_level": None},
            {"tier": "AEROSPACE_STANDARD", "min_score": 75, "max_score": 89.99, "auto_approve": False, "auto_decline": False, "referral_level": "UNDERWRITER"},
            {"tier": "AEROSPACE_ELEVATED", "min_score": 58, "max_score": 74.99, "auto_approve": False, "auto_decline": False, "referral_level": "AVIATION_SPECIALIST"},
            {"tier": "AEROSPACE_HIGH_RISK", "min_score": 40, "max_score": 57.99, "auto_approve": False, "auto_decline": False, "referral_level": "AEROSPACE_LEADER"},
            {"tier": "AEROSPACE_DECLINE", "min_score": 0, "max_score": 39.99, "auto_approve": False, "auto_decline": True, "referral_level": None},
        ]
    },
    "cyber": {
        "tiers": [
            {"tier": "CYBER_PREMIER", "min_score": 85, "max_score": 100, "auto_approve": True, "auto_decline": False, "referral_level": None},
            {"tier": "CYBER_STANDARD", "min_score": 70, "max_score": 84.99, "auto_approve": False, "auto_decline": False, "referral_level": "UNDERWRITER"},
            {"tier": "CYBER_ELEVATED", "min_score": 50, "max_score": 69.99, "auto_approve": False, "auto_decline": False, "referral_level": "CYBER_SPECIALIST"},
            {"tier": "CYBER_HIGH_RISK", "min_score": 35, "max_score": 49.99, "auto_approve": False, "auto_decline": False, "referral_level": "CYBER_LEADER"},
            {"tier": "CYBER_DECLINE", "min_score": 0, "max_score": 34.99, "auto_approve": False, "auto_decline": True, "referral_level": None},
        ]
    },
    "d_and_o": {
        "tiers": [
            {"tier": "DO_PREMIER", "min_score": 88, "max_score": 100, "auto_approve": True, "auto_decline": False, "referral_level": None},
            {"tier": "DO_STANDARD", "min_score": 72, "max_score": 87.99, "auto_approve": False, "auto_decline": False, "referral_level": "UNDERWRITER"},
            {"tier": "DO_ELEVATED", "min_score": 52, "max_score": 71.99, "auto_approve": False, "auto_decline": False, "referral_level": "DO_SPECIALIST"},
            {"tier": "DO_HIGH_RISK", "min_score": 35, "max_score": 51.99, "auto_approve": False, "auto_decline": False, "referral_level": "DO_LEADER"},
            {"tier": "DO_DECLINE", "min_score": 0, "max_score": 34.99, "auto_approve": False, "auto_decline": True, "referral_level": None},
        ]
    },
    "financial_institutions": {
        "tiers": [
            {"tier": "FI_PREMIER", "min_score": 88, "max_score": 100, "auto_approve": True, "auto_decline": False, "referral_level": None},
            {"tier": "FI_STANDARD", "min_score": 72, "max_score": 87.99, "auto_approve": False, "auto_decline": False, "referral_level": "UNDERWRITER"},
            {"tier": "FI_ELEVATED", "min_score": 55, "max_score": 71.99, "auto_approve": False, "auto_decline": False, "referral_level": "FI_SPECIALIST"},
            {"tier": "FI_HIGH_RISK", "min_score": 38, "max_score": 54.99, "auto_approve": False, "auto_decline": False, "referral_level": "FI_LEADER"},
            {"tier": "FI_DECLINE", "min_score": 0, "max_score": 37.99, "auto_approve": False, "auto_decline": True, "referral_level": None},
        ]
    },
    "energy": {
        "tiers": [
            {"tier": "ENERGY_PREMIER", "min_score": 88, "max_score": 100, "auto_approve": True, "auto_decline": False, "referral_level": None},
            {"tier": "ENERGY_STANDARD", "min_score": 70, "max_score": 87.99, "auto_approve": False, "auto_decline": False, "referral_level": "UNDERWRITER"},
            {"tier": "ENERGY_ELEVATED", "min_score": 52, "max_score": 69.99, "auto_approve": False, "auto_decline": False, "referral_level": "ENERGY_SPECIALIST"},
            {"tier": "ENERGY_HIGH_RISK", "min_score": 35, "max_score": 51.99, "auto_approve": False, "auto_decline": False, "referral_level": "ENERGY_LEADER"},
            {"tier": "ENERGY_DECLINE", "min_score": 0, "max_score": 34.99, "auto_approve": False, "auto_decline": True, "referral_level": None},
        ]
    },
    "professional_indemnity": {
        "tiers": [
            {"tier": "PI_PREMIER", "min_score": 88, "max_score": 100, "auto_approve": True, "auto_decline": False, "referral_level": None},
            {"tier": "PI_STANDARD", "min_score": 72, "max_score": 87.99, "auto_approve": False, "auto_decline": False, "referral_level": "UNDERWRITER"},
            {"tier": "PI_ELEVATED", "min_score": 55, "max_score": 71.99, "auto_approve": False, "auto_decline": False, "referral_level": "PI_SPECIALIST"},
            {"tier": "PI_HIGH_RISK", "min_score": 38, "max_score": 54.99, "auto_approve": False, "auto_decline": False, "referral_level": "PI_LEADER"},
            {"tier": "PI_DECLINE", "min_score": 0, "max_score": 37.99, "auto_approve": False, "auto_decline": True, "referral_level": None},
        ]
    },
}


# =============================================================================
# BASE CATEGORIZER CLASS
# =============================================================================

class DataCategorizer(ABC):
    """Abstract base class for all categorizers."""

    def __init__(self, coverage: str, configuration: str, **kwargs: Any):
        self.coverage = coverage
        self.configuration = configuration
        self.kwargs = kwargs

    @abstractmethod
    def categorize(self, data: Dict[str, Any]) -> CategorizationResult:
        raise NotImplementedError

    def _get_profile(self, profiles: Dict[str, Any], config_key: str, coverage_key: Optional[str] = None) -> Any:
        cov = coverage_key or self.coverage
        config_data = profiles.get(config_key, {})
        if isinstance(config_data, dict):
            return config_data.get(cov) or config_data.get("default")
        return config_data


# =============================================================================
# CATEGORIZER IMPLEMENTATIONS
# =============================================================================

@register_categorizer
class ThresholdBucketCategorizer(DataCategorizer):
    """Categorizes numeric values into predefined buckets with scores and modifiers."""

    def categorize(self, data: Dict[str, Any]) -> CategorizationResult:
        value = data.get("value")
        if value is None:
            return CategorizationResult(category="UNKNOWN", score=50, modifier=1.0, criteria=["No value provided"], confidence=0.0)

        buckets = self._get_profile(THRESHOLD_PROFILES, self.configuration)
        if not buckets:
            return CategorizationResult(category="UNKNOWN", score=50, modifier=1.0, criteria=[f"No profile for {self.configuration}/{self.coverage}"], confidence=0.0)

        for bucket in buckets:
            if bucket["min_value"] <= value <= bucket["max_value"]:
                return CategorizationResult(
                    category=bucket["category"], score=bucket["score"], modifier=bucket["modifier"],
                    criteria=[f"{self.configuration}={value} in [{bucket['min_value']}, {bucket['max_value']}]"],
                    confidence=1.0, metadata={"bucket": bucket, "value": value}
                )
        return CategorizationResult(category="OUT_OF_RANGE", score=50, modifier=1.0, criteria=[f"Value {value} outside defined buckets"], confidence=0.5)


@register_categorizer
class ScoringLogicCategorizer(DataCategorizer):
    """Maps discrete states to scores based on predefined logic profiles."""

    def categorize(self, data: Dict[str, Any]) -> CategorizationResult:
        state = data.get("state", "").upper().replace(" ", "_")
        if not state:
            return CategorizationResult(category="UNKNOWN", score=50, criteria=["No state provided"], confidence=0.0)

        profile = SCORING_LOGIC_PROFILES.get(self.configuration)
        if not profile:
            return CategorizationResult(category="UNKNOWN", score=50, criteria=[f"No scoring logic profile for {self.configuration}"], confidence=0.0)

        score = profile.get(state)
        if score is not None:
            return CategorizationResult(category=state, score=score, criteria=[f"{self.configuration}: '{state}' -> {score}"], confidence=1.0, metadata={"profile": self.configuration, "state": state})

        available_states = list(profile.keys())
        return CategorizationResult(category="UNKNOWN", score=50, criteria=[f"State '{state}' not found. Available: {available_states}"], confidence=0.0)


@register_categorizer
class QualityTierCategorizer(DataCategorizer):
    """Assigns quality tiers based on entity identification."""

    def categorize(self, data: Dict[str, Any]) -> CategorizationResult:
        entity = data.get("entity", "").strip()
        if not entity:
            return CategorizationResult(category="UNKNOWN", score=50, criteria=["No entity provided"], confidence=0.0)

        profile = QUALITY_TIER_PROFILES.get(self.configuration)
        if not profile:
            return CategorizationResult(category="UNKNOWN", score=50, criteria=[f"No quality tier profile for {self.configuration}"], confidence=0.0)

        entity_lower = entity.lower()
        for tier_def in profile:
            for known_entity in tier_def["entities"]:
                if known_entity.lower() in entity_lower or entity_lower in known_entity.lower():
                    return CategorizationResult(
                        category=tier_def["tier"], score=tier_def["score"], modifier=tier_def["modifier"],
                        criteria=[f"Entity '{entity}' matched to {tier_def['tier']}"],
                        confidence=0.95, metadata={"matched_entity": known_entity}
                    )

        lowest_tier = profile[-1] if profile else None
        if lowest_tier:
            return CategorizationResult(category=lowest_tier["tier"], score=lowest_tier["score"], modifier=lowest_tier["modifier"], criteria=[f"Entity '{entity}' assigned default tier"], confidence=0.6)
        return CategorizationResult(category="UNKNOWN", score=50, criteria=[f"Unable to categorize entity '{entity}'"], confidence=0.0)


@register_categorizer
class BooleanFlagCategorizer(DataCategorizer):
    """Evaluates boolean flags with associated consequences."""

    def categorize(self, data: Dict[str, Any]) -> CategorizationResult:
        flag_value = data.get("flag")
        if flag_value is None:
            return CategorizationResult(category="UNKNOWN", score=50, criteria=["No flag value provided"], confidence=0.0)

        flag_def = BOOLEAN_FLAG_PROFILES.get(self.configuration)
        if not flag_def:
            bool_val = bool(flag_value)
            return CategorizationResult(category="TRUE" if bool_val else "FALSE", score=75, modifier=1.0, criteria=[f"{self.configuration} = {bool_val}"], confidence=0.7)

        key = "true" if flag_value else "false"
        consequence = flag_def.get(key, {})

        return CategorizationResult(
            category=key.upper(), score=consequence.get("score", 75), modifier=consequence.get("modifier", 1.0),
            action=consequence.get("action"), criteria=[consequence.get("message", f"{self.configuration} = {flag_value}")],
            confidence=1.0, metadata={"flag_definition": consequence}
        )


@register_categorizer
class ConditionEvaluator(DataCategorizer):
    """Evaluates values against condition bands to determine actions."""

    def categorize(self, data: Dict[str, Any]) -> CategorizationResult:
        value = data.get("value")
        if value is None:
            return CategorizationResult(action="REFER", criteria=["No value provided"], confidence=0.0)

        bands = CONDITION_BANDS.get(self.configuration)
        if not bands:
            return CategorizationResult(action="INFO", criteria=[f"No condition bands for {self.configuration}"], confidence=0.0)

        for band in bands:
            if band["min_value"] <= value <= band["max_value"]:
                return CategorizationResult(
                    action=band["action"], modifier=band.get("modifier"), criteria=[band["message"]], confidence=1.0,
                    metadata={"band": band, "value": value, "condition": self.configuration}
                )
        return CategorizationResult(action="INFO", criteria=[f"Value {value} outside defined bands"], confidence=0.5)


@register_categorizer
class RateBenchmarkCategorizer(DataCategorizer):
    """Compares rates against industry benchmarks."""
    
    BENCHMARK_BANDS = [
        {"max_pct": 50, "score": 100, "label": "EXCELLENT"},
        {"max_pct": 75, "score": 85, "label": "GOOD"},
        {"max_pct": 100, "score": 70, "label": "AVERAGE"},
        {"max_pct": 150, "score": 50, "label": "BELOW_AVERAGE"},
        {"max_pct": 200, "score": 30, "label": "POOR"},
        {"max_pct": float("inf"), "score": 15, "label": "CRITICAL"},
    ]

    def categorize(self, data: Dict[str, Any]) -> CategorizationResult:
        actual = data.get("actual_rate")
        benchmark = data.get("benchmark_rate")

        if actual is None or benchmark is None:
            return CategorizationResult(category="UNKNOWN", score=50, criteria=["Missing actual_rate or benchmark_rate"], confidence=0.0)

        if benchmark == 0:
            return CategorizationResult(category="UNKNOWN", score=50, criteria=["Benchmark rate is zero"], confidence=0.0)

        pct_of_benchmark = (actual / benchmark) * 100

        for band in self.BENCHMARK_BANDS:
            if pct_of_benchmark <= band["max_pct"]:
                return CategorizationResult(
                    category=band["label"], score=band["score"],
                    criteria=[f"Rate is {pct_of_benchmark:.1f}% of benchmark ({band['label']})"],
                    confidence=1.0, metadata={"actual_rate": actual, "benchmark_rate": benchmark, "pct_of_benchmark": pct_of_benchmark}
                )
        return CategorizationResult(category="UNKNOWN", score=50, criteria=["Unable to categorize rate"], confidence=0.0)


@register_categorizer
class TierCategorizer(DataCategorizer):
    """Maps composite scores to tier assignments with referral levels."""

    def categorize(self, data: Dict[str, Any]) -> CategorizationResult:
        score = data.get("score")
        if score is None:
            return CategorizationResult(category="UNKNOWN", action="REFER", criteria=["No score provided"], confidence=0.0)

        profile = TIER_PROFILES.get(self.coverage) or TIER_PROFILES.get("default")
        tiers = profile.get("tiers", [])

        for tier_def in tiers:
            if tier_def["min_score"] <= score <= tier_def["max_score"]:
                action = "DECLINE" if tier_def.get("auto_decline") else ("APPROVE" if tier_def.get("auto_approve") else "REFER")
                return CategorizationResult(
                    category=tier_def["tier"], score=score, action=action,
                    criteria=[f"Score {score} -> {tier_def['tier']}"], confidence=1.0,
                    metadata={"tier_def": tier_def, "referral_level": tier_def.get("referral_level")}
                )
        return CategorizationResult(category="UNKNOWN", score=score, action="REFER", criteria=[f"Score {score} outside defined tiers"], confidence=0.5)


@register_categorizer
class MajorityCategorizer(DataCategorizer):
    """Determines the dominant category from a distribution."""

    def categorize(self, data: Dict[str, Any]) -> CategorizationResult:
        distribution = data.get("distribution", {})
        if not distribution:
            return CategorizationResult(category="UNKNOWN", criteria=["No distribution provided"], confidence=0.0)

        total = sum(distribution.values())
        if total == 0:
            return CategorizationResult(category="EMPTY", criteria=["Distribution sums to zero"], confidence=0.0)

        max_count = max(distribution.values())
        max_categories = [cat for cat, count in distribution.items() if count == max_count]

        if len(max_categories) == 1:
            majority_category = max_categories[0]
            majority_pct = (max_count / total) * 100
            return CategorizationResult(
                category=majority_category, score=majority_pct,
                criteria=[f"{majority_category} is majority with {majority_pct:.1f}%"],
                confidence=1.0 if majority_pct > 50 else 0.8,
                metadata={"distribution": distribution, "total": total, "majority_pct": majority_pct}
            )
        else:
            return CategorizationResult(category="MIXED", criteria=[f"Tie between: {', '.join(max_categories)}"], confidence=0.7, metadata={"tied_categories": max_categories})


@register_categorizer
class ModifierCalculator(DataCategorizer):
    """Calculates composite modifier from multiple categorical features."""

    def categorize(self, data: Dict[str, Any]) -> CategorizationResult:
        composite_modifier = 1.0
        applied_modifiers = []
        criteria = []

        for feature_name, feature_value in data.items():
            # Check boolean flags
            if feature_name in BOOLEAN_FLAG_PROFILES:
                flag_def = BOOLEAN_FLAG_PROFILES[feature_name]
                key = "true" if feature_value else "false"
                if key in flag_def and "modifier" in flag_def[key]:
                    mod = flag_def[key]["modifier"]
                    composite_modifier *= mod
                    applied_modifiers.append({"feature": feature_name, "value": feature_value, "modifier": mod})
                    criteria.append(f"{feature_name}={feature_value} -> {mod}")

        if not applied_modifiers:
            return CategorizationResult(modifier=1.0, criteria=["No applicable modifiers found"], confidence=0.5)
            
        return CategorizationResult(modifier=round(composite_modifier, 4), criteria=criteria, confidence=1.0, metadata={"applied_modifiers": applied_modifiers})


@register_categorizer
class CompositeScoreCategorizer(DataCategorizer):
    """Calculates weighted composite scores from signal groups with critical signal handling."""

    def categorize(self, data: Dict[str, Any]) -> CategorizationResult:
        signals = data.get("signals", {})
        if not signals:
            return CategorizationResult(score=50, criteria=["No signals provided"], confidence=0.0)

        weights = SIGNAL_WEIGHT_PROFILES.get(self.coverage, {})
        if not weights:
            return CategorizationResult(score=50, criteria=[f"No signal weight profile for {self.coverage}"], confidence=0.0)

        weighted_sum = 0.0
        total_weight = 0.0
        signal_contributions = []
        critical_failures = []
        missing_signals = []

        for signal_name, weight_def in weights.items():
            signal_score = signals.get(signal_name)
            weight = weight_def["weight"]
            
            if signal_score is None:
                strategy = weight_def.get("missing_strategy", "exclude")
                if strategy == "require":
                    return CategorizationResult(
                        score=0, action="REFER", 
                        criteria=[f"Required signal '{signal_name}' is missing"],
                        confidence=0.0, metadata={"missing_required": signal_name}
                    )
                elif strategy == "penalize":
                    signal_score = weight_def.get("default_value", 50) * 0.8
                    missing_signals.append({"signal": signal_name, "strategy": "penalize", "applied_score": signal_score})
                elif strategy == "use_default":
                    signal_score = weight_def.get("default_value", 50)
                    missing_signals.append({"signal": signal_name, "strategy": "use_default", "applied_score": signal_score})
                else:  # exclude
                    missing_signals.append({"signal": signal_name, "strategy": "exclude"})
                    continue
            
            contribution = signal_score * weight
            weighted_sum += contribution
            total_weight += weight
            signal_contributions.append({
                "signal": signal_name, "score": signal_score, "weight": weight, 
                "contribution": contribution, "is_critical": weight_def.get("critical", False)
            })

            if weight_def.get("critical", False):
                threshold = weight_def.get("critical_threshold", 40)
                if signal_score < threshold:
                    critical_failures.append({"signal": signal_name, "score": signal_score, "threshold": threshold})

        if total_weight == 0:
            return CategorizationResult(score=50, criteria=["No matching signals found in profile"], confidence=0.0)

        composite_score = weighted_sum / total_weight
        action = None
        criteria = [f"Weighted composite score: {composite_score:.1f}"]

        if critical_failures:
            composite_score = min(composite_score, 49.9)
            action = "REFER"
            for failure in critical_failures:
                criteria.append(f"CRITICAL: {failure['signal']} ({failure['score']}) below threshold ({failure['threshold']})")

        return CategorizationResult(
            score=round(composite_score, 2), action=action, criteria=criteria, 
            confidence=1.0 if total_weight >= 0.8 else 0.7,
            metadata={
                "signal_contributions": signal_contributions, 
                "critical_failures": critical_failures,
                "missing_signals": missing_signals,
                "total_weight_applied": round(total_weight, 4)
            }
        )


@register_categorizer
class EnumerationCategorizer(DataCategorizer):
    """Maps attributes to predefined categories based on enumeration profiles."""

    ENUMERATION_PROFILES: Dict[str, Dict[str, Dict[str, Any]]] = {
        "vessel_type": {
            "marine": {
                "CONTAINER": {"score": 85, "liner_potential": True},
                "TANKER": {"score": 80, "liner_potential": False},
                "BULK": {"score": 78, "liner_potential": False},
                "LNG": {"score": 88, "liner_potential": False},
                "LPG": {"score": 85, "liner_potential": False},
                "RORO": {"score": 82, "liner_potential": True},
                "CRUISE": {"score": 90, "liner_potential": True},
                "OFFSHORE": {"score": 75, "liner_potential": False},
                "GENERAL_CARGO": {"score": 72, "liner_potential": False},
            }
        },
        "industry_sector": {
            "cyber": {
                "HEALTHCARE": {"score": 72, "data_sensitivity": "high"},
                "FINANCIAL_SERVICES": {"score": 75, "data_sensitivity": "high"},
                "TECHNOLOGY": {"score": 85, "data_sensitivity": "medium"},
                "MANUFACTURING": {"score": 80, "data_sensitivity": "low"},
                "RETAIL": {"score": 78, "data_sensitivity": "medium"},
                "EDUCATION": {"score": 72, "data_sensitivity": "medium"},
                "GOVERNMENT": {"score": 70, "data_sensitivity": "high"},
            },
            "d_and_o": {
                "TECHNOLOGY": {"score": 72, "litigation_risk": "high"},
                "HEALTHCARE_PHARMA": {"score": 70, "litigation_risk": "high"},
                "MANUFACTURING": {"score": 82, "litigation_risk": "low"},
                "RETAIL": {"score": 78, "litigation_risk": "medium"},
                "FINANCIAL_SERVICES": {"score": 75, "litigation_risk": "high"},
                "ENERGY": {"score": 72, "litigation_risk": "medium"},
            },
        },
        "aircraft_type": {
            "aerospace": {
                "NARROW_BODY": {"score": 88, "complexity": "standard"},
                "WIDE_BODY": {"score": 85, "complexity": "high"},
                "REGIONAL_JET": {"score": 82, "complexity": "standard"},
                "TURBOPROP": {"score": 78, "complexity": "standard"},
                "FREIGHTER": {"score": 80, "complexity": "high"},
                "BUSINESS_JET": {"score": 85, "complexity": "low"},
            }
        },
        "professional_type": {
            "professional_indemnity": {
                "LAW_FIRM": {"score": 80, "regulation": "high"},
                "ACCOUNTING_FIRM": {"score": 82, "regulation": "high"},
                "ENGINEERING_FIRM": {"score": 78, "regulation": "medium"},
                "ARCHITECTURE_FIRM": {"score": 78, "regulation": "medium"},
                "CONSULTING_FIRM": {"score": 75, "regulation": "low"},
                "MEDICAL_PRACTICE": {"score": 72, "regulation": "high"},
            }
        },
    }

    def categorize(self, data: Dict[str, Any]) -> CategorizationResult:
        enum_profiles = self.ENUMERATION_PROFILES.get(self.configuration, {})
        profile = enum_profiles.get(self.coverage)
        
        if not profile:
            return CategorizationResult(category="UNKNOWN", score=50, criteria=[f"No enumeration profile for {self.configuration}/{self.coverage}"], confidence=0.0)

        category = data.get("category", "").upper().replace(" ", "_")
        if not category:
            return CategorizationResult(category="UNKNOWN", score=50, criteria=["No category provided"], confidence=0.0)

        if category in profile:
            cat_data = profile[category]
            return CategorizationResult(
                category=category, score=cat_data.get("score", 75),
                criteria=[f"Direct mapping: {category}"], confidence=1.0, metadata=cat_data
            )

        return CategorizationResult(category="UNCATEGORIZED", score=70, criteria=[f"Category '{category}' not in profile"], confidence=0.5)


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def get_categorizer(categorizer_type: str, coverage: str, configuration: str, **kwargs: Any) -> DataCategorizer:
    """Factory function to instantiate categorizers by type."""
    type_mapping = {
        "threshold_bucket": ThresholdBucketCategorizer,
        "scoring_logic": ScoringLogicCategorizer,
        "quality_tier": QualityTierCategorizer,
        "boolean_flag": BooleanFlagCategorizer,
        "condition": ConditionEvaluator,
        "rate_benchmark": RateBenchmarkCategorizer,
        "tier": TierCategorizer,
        "majority": MajorityCategorizer,
        "modifier": ModifierCalculator,
        "composite_score": CompositeScoreCategorizer,
        "enumeration": EnumerationCategorizer,
    }

    categorizer_class = type_mapping.get(categorizer_type.lower())
    if not categorizer_class:
        raise ValueError(f"Unknown categorizer type '{categorizer_type}'. Available: {list(type_mapping.keys())}")

    return categorizer_class(coverage=coverage, configuration=configuration, **kwargs)


def list_available_profiles() -> Dict[str, List[str]]:
    """List all available configuration profiles."""
    return {
        "threshold_profiles": list(THRESHOLD_PROFILES.keys()),
        "scoring_logic_profiles": list(SCORING_LOGIC_PROFILES.keys()),
        "quality_tier_profiles": list(QUALITY_TIER_PROFILES.keys()),
        "boolean_flag_profiles": list(BOOLEAN_FLAG_PROFILES.keys()),
        "condition_bands": list(CONDITION_BANDS.keys()),
        "signal_weight_profiles": list(SIGNAL_WEIGHT_PROFILES.keys()),
        "tier_profiles": list(TIER_PROFILES.keys()),
    }


def get_coverage_signals(coverage: str) -> Dict[str, SignalWeight]:
    """Get all signal weights for a coverage line."""
    return SIGNAL_WEIGHT_PROFILES.get(coverage, {})


# =============================================================================
# SIGNAL TO CATEGORIZER MAPPING
# =============================================================================

SIGNAL_CATEGORIZER_MAP: Dict[str, Dict[str, Tuple[str, str]]] = {
    "marine": {
        "classification_society": ("quality_tier", "classification_society"),
        "pi_club": ("quality_tier", "pi_club"),
        "flag_state": ("quality_tier", "flag_state"),
        "psc_detention": ("scoring_logic", "psc_detention_status"),
        "psc_deficiency": ("threshold_bucket", "psc_deficiency_rate"),
        "class_status": ("scoring_logic", "class_status"),
        "ism_compliance": ("scoring_logic", "ism_compliance"),
        "sanctions_status": ("scoring_logic", "sanctions_status"),
        "ais_compliance": ("scoring_logic", "ais_compliance"),
        "cii_rating": ("scoring_logic", "cii_rating"),
        "fleet_age": ("threshold_bucket", "fleet_age"),
        "fleet_size": ("threshold_bucket", "fleet_size"),
        "dark_activity": ("boolean_flag", "dark_vessel_pattern"),
        "sts_pattern": ("boolean_flag", "sts_activity"),
        "casualty_history": ("condition", "fatality_count"),
        "total_loss": ("boolean_flag", "total_loss_history"),
        "environmental_incident": ("condition", "environmental_incident_count"),
        "fleet_stability": ("scoring_logic", "fleet_stability"),
        "ownership_transparency": ("scoring_logic", "ownership_transparency"),
    },
    "aerospace": {
        "certificate_status": ("scoring_logic", "certificate_status"),
        "iosa_audit_status": ("scoring_logic", "iosa_status"),
        "eu_safety_list": ("scoring_logic", "eu_safety_list"),
        "alliance_membership": ("scoring_logic", "alliance_membership"),
        "accident_history": ("condition", "accident_count"),
        "accident_rate": ("threshold_bucket", "accident_rate"),
        "fatality_history": ("condition", "fatality_count"),
        "otp_score": ("threshold_bucket", "otp_score"),
        "fleet_age": ("threshold_bucket", "fleet_age"),
        "lessor_quality": ("quality_tier", "lessor_quality"),
        "mro_quality": ("quality_tier", "mro_provider"),
        "conflict_zone_exposure": ("boolean_flag", "conflict_zone_exposure"),
        "challenging_airports": ("scoring_logic", "operational_complexity"),
        "credit_rating": ("scoring_logic", "credit_rating"),
        "dispatch_reliability": ("scoring_logic", "maintenance_status"),
        "enforcement_actions": ("condition", "enforcement_action_count"),
        "fleet_homogeneity": ("scoring_logic", "aircraft_generation"),
        "market_position": ("scoring_logic", "market_position"),
    },
    "cyber": {
        "security_rating": ("threshold_bucket", "security_rating"),
        "tls_score": ("threshold_bucket", "tls_score"),
        "email_auth": ("scoring_logic", "email_auth"),
        "dnssec": ("scoring_logic", "dnssec_status"),
        "breach_history": ("condition", "breach_records_count"),
        "waf_presence": ("scoring_logic", "waf_status"),
        "bug_bounty": ("boolean_flag", "bug_bounty_program"),
        "security_txt": ("boolean_flag", "security_txt"),
        "ciso_present": ("boolean_flag", "ciso_present"),
        "soc2_certified": ("boolean_flag", "soc2_certified"),
        "customer_quality": ("quality_tier", "customer_tier"),
        "security_vendor": ("quality_tier", "security_vendor_tier"),
        "certification_authority": ("scoring_logic", "certification_status"),
        "credential_exposure": ("threshold_bucket", "breach_count"),
        "credit_rating": ("scoring_logic", "credit_rating"),
        "cve_exposure": ("scoring_logic", "software_currency"),
        "esg_cyber": ("scoring_logic", "esg_rating"),
        "regulatory_action": ("condition", "regulatory_action_count"),
        "security_page": ("boolean_flag", "security_page_exists"),
    },
    "d_and_o": {
        "audit_opinion": ("scoring_logic", "audit_opinion"),
        "internal_controls": ("scoring_logic", "internal_controls"),
        "board_independence": ("threshold_bucket", "board_independence_pct"),
        "short_interest": ("threshold_bucket", "short_interest_pct"),
        "stock_volatility": ("threshold_bucket", "stock_volatility"),
        "securities_litigation": ("condition", "class_action_count"),
        "sec_enforcement": ("condition", "sec_enforcement_count"),
        "ceo_chair_separation": ("boolean_flag", "ceo_chair_combined"),
        "prior_restatement": ("boolean_flag", "prior_restatement"),
        "going_concern": ("boolean_flag", "going_concern"),
        "auditor_quality": ("quality_tier", "auditor_quality"),
        "legal_counsel": ("quality_tier", "legal_counsel"),
        "committee_structure": ("scoring_logic", "committee_structure"),
        "credit_rating": ("scoring_logic", "credit_rating"),
        "derivative_litigation": ("condition", "derivative_suit_count"),
        "executive_stability": ("scoring_logic", "cfo_experience"),
        "insider_trading": ("scoring_logic", "insider_trading_pattern"),
        "restatement": ("boolean_flag", "prior_restatement"),
    },
    "financial_institutions": {
        "examination_rating": ("scoring_logic", "camels_rating"),
        "enforcement_action": ("scoring_logic", "enforcement_action_status"),
        "cra_rating": ("scoring_logic", "cra_rating"),
        "bsa_aml": ("scoring_logic", "bsa_aml_status"),
        "capital_ratio": ("threshold_bucket", "capital_ratio"),
        "asset_quality": ("threshold_bucket", "npl_ratio"),
        "concentration": ("threshold_bucket", "cre_concentration"),
        "asset_size": ("threshold_bucket", "asset_size"),
        "well_capitalized": ("boolean_flag", "well_capitalized"),
        "mou_active": ("boolean_flag", "mou_active"),
        "correspondent_quality": ("quality_tier", "correspondent_bank"),
        "board_independence": ("threshold_bucket", "board_independence_pct"),
        "breach_history": ("condition", "breach_records_count"),
        "cfpb_complaint": ("scoring_logic", "consumer_compliance_status"),
        "credit_rating": ("scoring_logic", "credit_rating"),
        "earnings": ("scoring_logic", "financial_disclosure"),
        "liquidity": ("scoring_logic", "interest_rate_risk"),
        "risk_committee": ("boolean_flag", "risk_committee_exists"),
        "security_rating": ("threshold_bucket", "security_rating"),
    },
    "energy": {
        "osha_trir": ("threshold_bucket", "osha_trir"),
        "osha_violations": ("condition", "osha_violation_count"),
        "fatality": ("condition", "fatality_count"),
        "epa_violation": ("condition", "epa_violation_count"),
        "spill_history": ("condition", "spill_count"),
        "permit_status": ("scoring_logic", "permit_status"),
        "esg_rating": ("scoring_logic", "esg_rating"),
        "production_boed": ("threshold_bucket", "production_boed"),
        "reserve_life_years": ("threshold_bucket", "reserve_life_years"),
        "superfund_exposure": ("boolean_flag", "superfund_exposure"),
        "net_zero_commitment": ("boolean_flag", "net_zero_commitment"),
        "partner_quality": ("quality_tier", "jv_partner_tier"),
        "contractor_quality": ("quality_tier", "contractor_tier"),
        "aro_coverage": ("scoring_logic", "decommissioning_status"),
        "credit_rating": ("scoring_logic", "credit_rating"),
        "decommissioning": ("scoring_logic", "decommissioning_status"),
        "emissions_compliance": ("scoring_logic", "emissions_status"),
        "ghg_intensity": ("scoring_logic", "regulatory_standing"),
        "leverage": ("scoring_logic", "capex_trend"),
        "process_safety": ("scoring_logic", "process_safety_status"),
        "production_consistency": ("scoring_logic", "facility_status"),
        "well_integrity": ("scoring_logic", "well_integrity_status"),
    },
    "professional_indemnity": {
        "license_status": ("scoring_logic", "license_status"),
        "disciplinary_history": ("scoring_logic", "disciplinary_history"),
        "peer_review": ("scoring_logic", "peer_review_rating"),
        "malpractice_frequency": ("threshold_bucket", "malpractice_frequency"),
        "partner_turnover_rate": ("threshold_bucket", "partner_turnover_rate"),
        "employee_count": ("threshold_bucket", "employee_count"),
        "malpractice_suits": ("condition", "malpractice_suit_count"),
        "fee_disputes": ("condition", "fee_dispute_count"),
        "cpe_compliant": ("boolean_flag", "cpe_compliant"),
        "peer_review_enrolled": ("boolean_flag", "peer_review_enrolled"),
        "prior_bankruptcy": ("boolean_flag", "prior_bankruptcy"),
        "firm_ranking": ("quality_tier", "firm_ranking"),
        "auditor_quality": ("quality_tier", "accounting_firm"),
        "breach_history": ("condition", "breach_records_count"),
        "ce_compliance": ("boolean_flag", "cpe_compliant"),
        "client_quality": ("quality_tier", "client_tier"),
        "fee_disputes_litigation": ("condition", "fee_litigation_count"),
        "financial_stability": ("scoring_logic", "firm_financial_status"),
        "malpractice_record": ("threshold_bucket", "malpractice_frequency"),
        "panel_membership": ("boolean_flag", "insurance_panel_member"),
        "partner_stability": ("threshold_bucket", "partner_turnover_rate"),
        "peer_ranking": ("quality_tier", "firm_ranking"),
        "specialty_certification": ("boolean_flag", "specialty_certified"),
        "staff_retention": ("scoring_logic", "office_stability"),
        "tenure": ("scoring_logic", "management_tenure"),
    },
}


def categorize_signal(signal_name: str, coverage: str, data: Dict[str, Any]) -> CategorizationResult:
    """Convenience function to categorize a single signal."""
    signal_map = SIGNAL_CATEGORIZER_MAP.get(coverage, {})
    if signal_name not in signal_map:
        return CategorizationResult(category="UNKNOWN", score=50, criteria=[f"Signal '{signal_name}' not mapped for {coverage}"], confidence=0.0)
    
    categorizer_type, configuration = signal_map[signal_name]
    categorizer = get_categorizer(categorizer_type, coverage, configuration)
    return categorizer.categorize(data)
