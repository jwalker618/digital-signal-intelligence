"""
Signal Categorization Framework

11 categorizer types:
1. ThresholdBucketCategorizer - Numeric values to categories
2. EnumerationCategorizer - Attribute mapping  
3. TierCategorizer - Score to tier mapping
4. ConditionEvaluator - Band-based threshold evaluation
5. ModifierCalculator - Composite modifier from features
6. MajorityCategorizer - Dominant category from distribution
7. RateBenchmarkCategorizer - Compare rates vs benchmarks
8. QualityTierCategorizer - Quality tier assignment
9. CompositeScoreCategorizer - Weighted composite scores
10. BooleanFlagCategorizer - Yes/no flags
11. ScoringLogicCategorizer - Discrete state to score mapping
"""

from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type, TypedDict

logger = logging.getLogger(__name__)

CATEGORIZER_REGISTRY: Dict[str, Type["DataCategorizer"]] = {}

def register_categorizer(cls: Type["DataCategorizer"]) -> Type["DataCategorizer"]:
    CATEGORIZER_REGISTRY[cls.__name__] = cls
    return cls

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

class ThresholdBucket(TypedDict):
    min_value: float
    max_value: float
    category: str
    score: float
    modifier: float

class SignalWeight(TypedDict):
    weight: float
    critical: bool
    critical_threshold: float

# =============================================================================
# CONFIGURATION PROFILES
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
            {"min_value": 0, "max_value": 3, "category": "MICRO", "score": 55, "modifier": 1.20},
            {"min_value": 4, "max_value": 10, "category": "SMALL", "score": 65, "modifier": 1.12},
            {"min_value": 11, "max_value": 25, "category": "MEDIUM", "score": 75, "modifier": 1.00},
            {"min_value": 26, "max_value": 75, "category": "LARGE", "score": 85, "modifier": 0.92},
            {"min_value": 76, "max_value": 200, "category": "MAJOR", "score": 90, "modifier": 0.88},
            {"min_value": 201, "max_value": float("inf"), "category": "MEGA", "score": 95, "modifier": 0.82},
        ],
        "default": [
            {"min_value": 0, "max_value": 10, "category": "SMALL", "score": 65, "modifier": 1.10},
            {"min_value": 11, "max_value": 50, "category": "MEDIUM", "score": 75, "modifier": 1.00},
            {"min_value": 51, "max_value": 200, "category": "LARGE", "score": 85, "modifier": 0.95},
            {"min_value": 201, "max_value": float("inf"), "category": "MAJOR", "score": 90, "modifier": 0.90},
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
        "default": [
            {"min_value": 0, "max_value": 10_000_000, "category": "SMALL", "score": 65, "modifier": 1.10},
            {"min_value": 10_000_001, "max_value": 100_000_000, "category": "MEDIUM", "score": 75, "modifier": 1.00},
            {"min_value": 100_000_001, "max_value": float("inf"), "category": "LARGE", "score": 85, "modifier": 0.95},
        ],
    },
    "employee_count": {
        "cyber": [
            {"min_value": 0, "max_value": 50, "category": "SMALL", "score": 70, "modifier": 1.08},
            {"min_value": 51, "max_value": 250, "category": "MEDIUM", "score": 75, "modifier": 1.00},
            {"min_value": 251, "max_value": 1000, "category": "LARGE", "score": 78, "modifier": 0.98},
            {"min_value": 1001, "max_value": 5000, "category": "ENTERPRISE", "score": 80, "modifier": 0.95},
            {"min_value": 5001, "max_value": float("inf"), "category": "MAJOR_ENTERPRISE", "score": 82, "modifier": 0.92},
        ],
        "professional_indemnity": [
            {"min_value": 1, "max_value": 5, "category": "SOLO", "score": 65, "modifier": 1.15},
            {"min_value": 6, "max_value": 20, "category": "SMALL_FIRM", "score": 72, "modifier": 1.08},
            {"min_value": 21, "max_value": 50, "category": "MID_FIRM", "score": 78, "modifier": 1.00},
            {"min_value": 51, "max_value": 200, "category": "LARGE_FIRM", "score": 82, "modifier": 0.95},
            {"min_value": 201, "max_value": float("inf"), "category": "MAJOR_FIRM", "score": 85, "modifier": 0.92},
        ],
        "default": [
            {"min_value": 0, "max_value": 50, "category": "SMALL", "score": 70, "modifier": 1.05},
            {"min_value": 51, "max_value": 500, "category": "MEDIUM", "score": 78, "modifier": 1.00},
            {"min_value": 501, "max_value": float("inf"), "category": "LARGE", "score": 82, "modifier": 0.95},
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
            {"min_value": 0, "max_value": 3, "category": "NEW", "score": 95, "modifier": 0.88},
            {"min_value": 3.01, "max_value": 8, "category": "MODERN", "score": 88, "modifier": 0.92},
            {"min_value": 8.01, "max_value": 15, "category": "MATURE", "score": 78, "modifier": 1.00},
            {"min_value": 15.01, "max_value": 20, "category": "AGING", "score": 65, "modifier": 1.12},
            {"min_value": 20.01, "max_value": float("inf"), "category": "OLD", "score": 50, "modifier": 1.25},
        ],
        "default": [
            {"min_value": 0, "max_value": 5, "category": "NEW", "score": 90, "modifier": 0.92},
            {"min_value": 5.01, "max_value": 15, "category": "MATURE", "score": 78, "modifier": 1.00},
            {"min_value": 15.01, "max_value": float("inf"), "category": "OLD", "score": 60, "modifier": 1.15},
        ],
    },
    "production_boed": {
        "energy": [
            {"min_value": 0, "max_value": 10000, "category": "SMALL_PRODUCER", "score": 65, "modifier": 1.12},
            {"min_value": 10001, "max_value": 50000, "category": "MID_PRODUCER", "score": 72, "modifier": 1.05},
            {"min_value": 50001, "max_value": 200000, "category": "LARGE_PRODUCER", "score": 78, "modifier": 1.00},
            {"min_value": 200001, "max_value": 500000, "category": "MAJOR_PRODUCER", "score": 83, "modifier": 0.95},
            {"min_value": 500001, "max_value": float("inf"), "category": "SUPER_MAJOR", "score": 88, "modifier": 0.90},
        ],
        "default": [
            {"min_value": 0, "max_value": 50000, "category": "SMALL", "score": 70, "modifier": 1.05},
            {"min_value": 50001, "max_value": float("inf"), "category": "LARGE", "score": 85, "modifier": 0.95},
        ],
    },
    "market_cap": {
        "d_and_o": [
            {"min_value": 0, "max_value": 300_000_000, "category": "MICRO_CAP", "score": 65, "modifier": 1.15},
            {"min_value": 300_000_001, "max_value": 2_000_000_000, "category": "SMALL_CAP", "score": 72, "modifier": 1.08},
            {"min_value": 2_000_000_001, "max_value": 10_000_000_000, "category": "MID_CAP", "score": 78, "modifier": 1.00},
            {"min_value": 10_000_000_001, "max_value": 200_000_000_000, "category": "LARGE_CAP", "score": 83, "modifier": 0.95},
            {"min_value": 200_000_000_001, "max_value": float("inf"), "category": "MEGA_CAP", "score": 88, "modifier": 0.90},
        ],
        "default": [
            {"min_value": 0, "max_value": 2_000_000_000, "category": "SMALL", "score": 70, "modifier": 1.08},
            {"min_value": 2_000_000_001, "max_value": float("inf"), "category": "LARGE", "score": 85, "modifier": 0.92},
        ],
    },
}

MODIFIER_PROFILES: Dict[str, Dict[str, Dict[str, float]]] = {
    "marine": {
        "operator_type": {"MAJOR_LINER": 0.85, "REGIONAL_LINER": 0.92, "MAJOR_TANKER": 0.88, "INDEPENDENT_TANKER": 0.95, "MAJOR_BULK": 0.90, "TRAMP_OPERATOR": 1.05, "UNCATEGORIZED": 1.00},
        "vessel_category": {"container": 0.92, "tanker": 0.95, "bulk": 0.98, "lng": 0.90, "lpg": 0.92, "ro_ro": 1.02, "passenger": 1.08, "offshore": 1.05},
        "fleet_size": {"MICRO": 1.15, "SMALL": 1.10, "MEDIUM": 1.00, "LARGE": 0.95, "MAJOR": 0.90, "MEGA": 0.85},
        "flag_state_quality": {"WHITE": 0.95, "GREY": 1.05, "BLACK": 1.25},
    },
    "aerospace": {
        "operator_type": {"MAJOR_SCHEDULED": 0.82, "REGIONAL_SCHEDULED": 0.90, "LOW_COST_CARRIER": 0.92, "CHARTER_PASSENGER": 1.00, "CARGO_MAJOR": 0.88, "CARGO_REGIONAL": 0.95, "BUSINESS_AVIATION": 1.05, "HELICOPTER_OPERATOR": 1.12, "UNCATEGORIZED": 1.00},
        "fleet_size": {"MICRO": 1.20, "SMALL": 1.12, "MEDIUM": 1.00, "LARGE": 0.92, "MAJOR": 0.88, "MEGA": 0.82},
        "regulatory_framework": {"FAA": 0.92, "EASA": 0.90, "TCCA": 0.92, "CASA": 0.93, "OTHER": 1.08},
        "iosa_status": {"REGISTERED": 0.90, "EXPIRED": 1.05, "NEVER_REGISTERED": 1.12, "NOT_APPLICABLE": 1.00},
    },
    "cyber": {
        "employee_count": {"SMALL": 1.08, "MEDIUM": 1.00, "LARGE": 0.98, "ENTERPRISE": 0.95, "MAJOR_ENTERPRISE": 0.92},
        "industry_classification": {"HEALTHCARE": 1.15, "FINANCIAL_SERVICES": 1.12, "RETAIL_ECOMMERCE": 1.08, "TECHNOLOGY": 0.95, "MANUFACTURING": 1.00, "PROFESSIONAL_SERVICES": 0.98, "EDUCATION": 1.05, "OTHER": 1.00},
    },
    "d_and_o": {
        "company_type": {"PRIVATE_VENTURE_BACKED": 1.12, "PRIVATE_PE_BACKED": 1.08, "PRIVATE_FAMILY": 0.95, "PUBLIC_NYSE": 1.00, "PUBLIC_NASDAQ": 1.02, "PUBLIC_OTC": 1.15, "NON_PROFIT": 0.92, "SPAC": 1.25},
        "industry_classification": {"TECHNOLOGY": 1.10, "HEALTHCARE_PHARMA": 1.15, "FINANCIAL_SERVICES": 1.12, "MANUFACTURING": 0.95, "RETAIL": 1.00, "ENERGY": 1.08, "OTHER": 1.00},
    },
    "financial_institutions": {
        "asset_size": {"COMMUNITY": 1.08, "REGIONAL": 1.00, "SUPER_REGIONAL": 0.95, "LARGE": 0.90, "GSIB": 0.85},
        "institution_type": {"COMMERCIAL_BANK": 0.95, "CREDIT_UNION": 0.92, "INVESTMENT_BANK": 1.08, "BROKER_DEALER": 1.12, "FINTECH": 1.15, "CRYPTO_EXCHANGE": 1.30, "PAYMENT_PROCESSOR": 1.08, "BHC": 0.98},
    },
    "energy": {
        "operator_type": {"SUPER_MAJOR": 0.82, "MAJOR_IOC": 0.88, "LARGE_INDEPENDENT": 0.92, "MID_INDEPENDENT": 1.00, "SMALL_INDEPENDENT": 1.08, "NOC": 0.90, "SERVICE_COMPANY": 1.02},
        "operation_segment": {"UPSTREAM_CONVENTIONAL": 1.00, "UPSTREAM_UNCONVENTIONAL": 1.08, "UPSTREAM_OFFSHORE_DEEP": 1.15, "MIDSTREAM_PIPELINE": 0.92, "DOWNSTREAM_REFINING": 1.00, "RENEWABLES": 0.88},
    },
    "professional_indemnity": {
        "profession_type": {"ACCOUNTANT_BIG4": 0.85, "ACCOUNTANT_NATIONAL": 0.92, "ACCOUNTANT_REGIONAL": 1.00, "LAWYER_AMLAW50": 0.88, "LAWYER_AMLAW100": 0.92, "LAWYER_REGIONAL": 1.00, "LAWYER_BOUTIQUE": 1.05, "ARCHITECT_LARGE": 0.95, "ARCHITECT_SMALL": 1.08, "ENGINEER_LARGE": 0.95, "ENGINEER_SMALL": 1.08},
        "employee_count": {"SOLO": 1.15, "SMALL_FIRM": 1.08, "MID_FIRM": 1.00, "LARGE_FIRM": 0.95, "MAJOR_FIRM": 0.92},
    },
}

TIER_PROFILES: Dict[str, Dict[str, Any]] = {
    "default": {
        "tiers": [
            {"min_score": 800, "max_score": 1000, "tier": "PREFERRED", "auto_approve": True, "auto_decline": False},
            {"min_score": 650, "max_score": 799, "tier": "STANDARD_PLUS", "auto_approve": True, "auto_decline": False},
            {"min_score": 500, "max_score": 649, "tier": "STANDARD", "auto_approve": False, "auto_decline": False},
            {"min_score": 350, "max_score": 499, "tier": "SUBSTANDARD", "auto_approve": False, "auto_decline": False},
            {"min_score": 0, "max_score": 349, "tier": "DECLINE", "auto_approve": False, "auto_decline": True},
        ],
    },
    "marine": {
        "tiers": [
            {"min_score": 850, "max_score": 1000, "tier": "PREFERRED", "auto_approve": True, "auto_decline": False},
            {"min_score": 700, "max_score": 849, "tier": "STANDARD_PLUS", "auto_approve": True, "auto_decline": False},
            {"min_score": 550, "max_score": 699, "tier": "STANDARD", "auto_approve": False, "auto_decline": False},
            {"min_score": 400, "max_score": 549, "tier": "SUBSTANDARD", "auto_approve": False, "auto_decline": False},
            {"min_score": 0, "max_score": 399, "tier": "DECLINE", "auto_approve": False, "auto_decline": True},
        ],
    },
}

QUALITY_TIER_PROFILES: Dict[str, List[Dict[str, Any]]] = {
    "auditor": [
        {"tier": "BIG_4", "score": 95, "entities": ["deloitte", "pwc", "pricewaterhousecoopers", "ey", "ernst & young", "kpmg"]},
        {"tier": "NATIONAL", "score": 85, "entities": ["bdo", "rsm", "grant thornton", "crowe", "cbiz", "moss adams"]},
        {"tier": "REGIONAL", "score": 75, "entities": []},
        {"tier": "LOCAL", "score": 65, "entities": []},
    ],
    "classification_society": [
        {"tier": "TOP_IACS", "score": 95, "entities": ["lloyd's register", "dnv", "bureau veritas", "abs", "american bureau of shipping"]},
        {"tier": "IACS_MEMBER", "score": 88, "entities": ["class nk", "rina", "ccs", "korean register", "indian register"]},
        {"tier": "RECOGNIZED", "score": 75, "entities": []},
        {"tier": "OTHER", "score": 60, "entities": []},
    ],
    "p_and_i_club": [
        {"tier": "IG_TOP", "score": 95, "entities": ["gard", "britannia", "uk club", "north", "standard club", "west of england", "skuld"]},
        {"tier": "IG_MEMBER", "score": 88, "entities": ["american club", "japan club", "london club", "swedish club"]},
        {"tier": "QUALITY_FIXED", "score": 78, "entities": []},
        {"tier": "STANDARD", "score": 68, "entities": []},
    ],
    "credit_rating": [
        {"tier": "INVESTMENT_GRADE_HIGH", "score": 95, "entities": ["aaa", "aa+", "aa", "aa-"]},
        {"tier": "INVESTMENT_GRADE_MID", "score": 88, "entities": ["a+", "a", "a-"]},
        {"tier": "INVESTMENT_GRADE_LOW", "score": 78, "entities": ["bbb+", "bbb", "bbb-"]},
        {"tier": "SPECULATIVE_HIGH", "score": 65, "entities": ["bb+", "bb", "bb-"]},
        {"tier": "SPECULATIVE_LOW", "score": 35, "entities": ["b+", "b", "b-", "ccc+", "ccc"]},
        {"tier": "DEFAULT", "score": 15, "entities": ["d", "rd", "sd"]},
    ],
    "security_vendors": [
        {"tier": "TIER_1", "score": 92, "entities": ["crowdstrike", "palo alto", "fortinet", "cisco", "microsoft", "sentinelone", "zscaler", "okta"]},
        {"tier": "TIER_2", "score": 80, "entities": ["sophos", "trend micro", "mcafee", "symantec", "checkpoint", "proofpoint"]},
        {"tier": "REGIONAL", "score": 68, "entities": []},
        {"tier": "UNKNOWN", "score": 55, "entities": []},
    ],
}

CONDITION_BANDS: Dict[str, List[Dict[str, Any]]] = {
    "safety_record_critical": [
        {"min_value": 0, "max_value": 20, "action": "DECLINE", "modifier": None, "message": "Unacceptable safety record"},
        {"min_value": 21, "max_value": 40, "action": "REFER", "modifier": None, "message": "Poor safety record requires review"},
        {"min_value": 41, "max_value": 60, "action": "FLAG", "modifier": 1.15, "message": "Below average safety record"},
        {"min_value": 61, "max_value": 100, "action": "INFO", "modifier": None, "message": "Safety record acceptable"},
    ],
    "regulatory_compliance_critical": [
        {"min_value": 0, "max_value": 25, "action": "DECLINE", "modifier": None, "message": "Severe regulatory issues"},
        {"min_value": 26, "max_value": 45, "action": "REFER", "modifier": None, "message": "Significant regulatory concerns"},
        {"min_value": 46, "max_value": 65, "action": "FLAG", "modifier": 1.12, "message": "Regulatory concerns noted"},
        {"min_value": 66, "max_value": 100, "action": "INFO", "modifier": None, "message": "Regulatory standing acceptable"},
    ],
    "sanctions_compliance_critical": [
        {"min_value": 0, "max_value": 10, "action": "DECLINE", "modifier": None, "message": "Active sanctions exposure"},
        {"min_value": 11, "max_value": 30, "action": "REFER", "modifier": None, "message": "Sanctions concerns identified"},
        {"min_value": 31, "max_value": 60, "action": "FLAG", "modifier": 1.15, "message": "Historical sanctions involvement"},
        {"min_value": 61, "max_value": 100, "action": "INFO", "modifier": None, "message": "Sanctions compliance acceptable"},
    ],
    "financial_condition_critical": [
        {"min_value": 0, "max_value": 25, "action": "DECLINE", "modifier": None, "message": "Severe financial distress"},
        {"min_value": 26, "max_value": 45, "action": "REFER", "modifier": None, "message": "Financial concerns require review"},
        {"min_value": 46, "max_value": 65, "action": "FLAG", "modifier": 1.10, "message": "Financial metrics below target"},
        {"min_value": 66, "max_value": 100, "action": "INFO", "modifier": None, "message": "Financial condition acceptable"},
    ],
    "breach_history_critical": [
        {"min_value": 0, "max_value": 30, "action": "DECLINE", "modifier": None, "message": "Recent significant breaches"},
        {"min_value": 31, "max_value": 50, "action": "REFER", "modifier": None, "message": "Breach history requires review"},
        {"min_value": 51, "max_value": 70, "action": "FLAG", "modifier": 1.08, "message": "Prior breach incidents noted"},
        {"min_value": 71, "max_value": 100, "action": "INFO", "modifier": None, "message": "Breach history acceptable"},
    ],
    "litigation_critical": [
        {"min_value": 0, "max_value": 20, "action": "DECLINE", "modifier": None, "message": "Severe litigation exposure"},
        {"min_value": 21, "max_value": 40, "action": "REFER", "modifier": None, "message": "Significant litigation pending"},
        {"min_value": 41, "max_value": 60, "action": "FLAG", "modifier": 1.12, "message": "Active litigation noted"},
        {"min_value": 61, "max_value": 100, "action": "INFO", "modifier": None, "message": "Litigation exposure acceptable"},
    ],
}

SIGNAL_WEIGHT_PROFILES: Dict[str, Dict[str, SignalWeight]] = {
    "marine": {
        "safety_compliance": {"weight": 0.25, "critical": True, "critical_threshold": 40},
        "operational_telemetry": {"weight": 0.20, "critical": True, "critical_threshold": 40},
        "sanctions_compliance": {"weight": 0.15, "critical": True, "critical_threshold": 40},
        "financial_stability": {"weight": 0.12, "critical": False, "critical_threshold": 30},
        "fleet_quality": {"weight": 0.10, "critical": False, "critical_threshold": 30},
        "classification_quality": {"weight": 0.08, "critical": False, "critical_threshold": 30},
        "p_and_i_quality": {"weight": 0.05, "critical": False, "critical_threshold": 30},
        "management_quality": {"weight": 0.05, "critical": False, "critical_threshold": 30},
    },
    "aerospace": {
        "safety_record": {"weight": 0.30, "critical": True, "critical_threshold": 40},
        "regulatory_compliance": {"weight": 0.20, "critical": True, "critical_threshold": 40},
        "operational_quality": {"weight": 0.15, "critical": False, "critical_threshold": 35},
        "fleet_quality": {"weight": 0.12, "critical": False, "critical_threshold": 30},
        "financial_stability": {"weight": 0.10, "critical": False, "critical_threshold": 30},
        "maintenance_quality": {"weight": 0.08, "critical": False, "critical_threshold": 30},
        "crew_quality": {"weight": 0.05, "critical": False, "critical_threshold": 25},
    },
    "cyber": {
        "technical_infrastructure": {"weight": 0.35, "critical": True, "critical_threshold": 40},
        "public_record": {"weight": 0.25, "critical": True, "critical_threshold": 40},
        "governance": {"weight": 0.18, "critical": False, "critical_threshold": 35},
        "vendor_management": {"weight": 0.12, "critical": False, "critical_threshold": 30},
        "incident_response": {"weight": 0.10, "critical": False, "critical_threshold": 30},
    },
    "d_and_o": {
        "governance": {"weight": 0.25, "critical": True, "critical_threshold": 40},
        "litigation": {"weight": 0.25, "critical": True, "critical_threshold": 40},
        "financial": {"weight": 0.20, "critical": True, "critical_threshold": 40},
        "regulatory": {"weight": 0.12, "critical": False, "critical_threshold": 35},
        "public_company_factors": {"weight": 0.10, "critical": False, "critical_threshold": 30},
        "industry_factors": {"weight": 0.08, "critical": False, "critical_threshold": 30},
    },
    "financial_institutions": {
        "regulatory_compliance": {"weight": 0.25, "critical": True, "critical_threshold": 40},
        "financial_condition": {"weight": 0.20, "critical": True, "critical_threshold": 40},
        "credit_quality": {"weight": 0.15, "critical": False, "critical_threshold": 35},
        "operational_risk": {"weight": 0.12, "critical": False, "critical_threshold": 30},
        "cybersecurity": {"weight": 0.10, "critical": False, "critical_threshold": 30},
        "governance": {"weight": 0.10, "critical": False, "critical_threshold": 30},
        "litigation": {"weight": 0.08, "critical": False, "critical_threshold": 30},
    },
    "energy": {
        "safety_performance": {"weight": 0.30, "critical": True, "critical_threshold": 40},
        "environmental_compliance": {"weight": 0.20, "critical": True, "critical_threshold": 40},
        "regulatory_standing": {"weight": 0.15, "critical": False, "critical_threshold": 35},
        "operational_quality": {"weight": 0.12, "critical": False, "critical_threshold": 30},
        "financial_stability": {"weight": 0.10, "critical": False, "critical_threshold": 30},
        "asset_quality": {"weight": 0.08, "critical": False, "critical_threshold": 30},
        "esg_factors": {"weight": 0.05, "critical": False, "critical_threshold": 25},
    },
    "professional_indemnity": {
        "regulatory_standing": {"weight": 0.25, "critical": True, "critical_threshold": 40},
        "claims_history": {"weight": 0.20, "critical": True, "critical_threshold": 40},
        "network_authority": {"weight": 0.15, "critical": False, "critical_threshold": 35},
        "peer_review": {"weight": 0.12, "critical": False, "critical_threshold": 30},
        "quality_management": {"weight": 0.10, "critical": False, "critical_threshold": 30},
        "client_quality": {"weight": 0.10, "critical": False, "critical_threshold": 30},
        "professional_development": {"weight": 0.08, "critical": False, "critical_threshold": 25},
    },
}

SCORING_LOGIC_PROFILES: Dict[str, Dict[str, float]] = {
    "accident_history_5yr": {"NONE": 100, "MINOR_1": 85, "MINOR_2_PLUS": 70, "MAJOR_1": 50, "MAJOR_2_PLUS": 25, "FATAL": 10},
    "enforcement_actions_3yr": {"NONE": 100, "MINOR_1": 85, "MINOR_2_PLUS": 70, "MAJOR_1": 45, "MAJOR_2_PLUS": 20, "CONSENT_ORDER": 15},
    "capital_ratio_status": {"WELL_CAPITALIZED": 100, "ADEQUATELY_CAPITALIZED": 80, "UNDERCAPITALIZED": 50, "CRITICALLY_UNDERCAPITALIZED": 10},
    "breach_history_3yr": {"NONE": 100, "MINOR_1": 85, "MINOR_2_PLUS": 70, "MAJOR_1": 50, "MAJOR_2_PLUS": 25, "REGULATORY_NOTIFICATION": 40},
    "psc_detention_status": {"NONE_3YR": 100, "DETAINED_1_3YR": 75, "DETAINED_2_3YR": 55, "DETAINED_3_PLUS_3YR": 30, "BANNED": 5},
    "dark_activity_status": {"NONE": 100, "BRIEF_COASTAL": 90, "EXTENDED_COASTAL": 75, "OPEN_WATER_MINOR": 55, "OPEN_WATER_MAJOR": 25, "STS_SUSPECTED": 15},
    "iosa_status": {"REGISTERED_CURRENT": 100, "REGISTERED_RENEWAL_PENDING": 90, "EXPIRED_LESS_6MO": 70, "EXPIRED_6MO_PLUS": 45, "NEVER_REGISTERED_APPLICABLE": 30, "NOT_APPLICABLE": 75},
    "class_status": {"IN_CLASS_NO_CONDITIONS": 100, "IN_CLASS_MINOR_CONDITIONS": 85, "IN_CLASS_MAJOR_CONDITIONS": 60, "SUSPENDED": 25, "WITHDRAWN": 10, "NO_CLASS": 5},
    "malpractice_claims_5yr": {"NONE": 100, "CLAIM_1_NO_PAYMENT": 90, "CLAIM_1_WITH_PAYMENT": 75, "CLAIMS_2_3": 55, "CLAIMS_4_PLUS": 30, "LICENSE_ACTION": 15},
}

ENUMERATION_PROFILES: Dict[str, Dict[str, Dict[str, Any]]] = {
    "operator_type": {
        "marine": {
            "MAJOR_LINER": {"criteria": ["vessel_majority == container", "fleet_size >= 50", "offers_liner_service == True"], "score": 90},
            "REGIONAL_LINER": {"criteria": ["vessel_majority == container", "fleet_size >= 10", "offers_liner_service == True"], "score": 82},
            "MAJOR_TANKER": {"criteria": ["vessel_majority == tanker", "fleet_size >= 30"], "score": 88},
            "INDEPENDENT_TANKER": {"criteria": ["vessel_majority == tanker", "fleet_size < 30"], "score": 75},
            "MAJOR_BULK": {"criteria": ["vessel_majority == bulk", "fleet_size >= 40"], "score": 85},
            "TRAMP_OPERATOR": {"criteria": ["offers_liner_service == False", "fleet_size < 10"], "score": 65},
        },
        "aerospace": {
            "MAJOR_SCHEDULED": {"criteria": ["operations_type == scheduled", "fleet_size >= 50"], "score": 92},
            "REGIONAL_SCHEDULED": {"criteria": ["operations_type == scheduled", "fleet_size >= 10"], "score": 85},
            "LOW_COST_CARRIER": {"criteria": ["operations_type == scheduled", "business_model == lcc"], "score": 82},
            "CARGO_MAJOR": {"criteria": ["aircraft_category == freighter", "fleet_size >= 20"], "score": 88},
            "HELICOPTER_OPERATOR": {"criteria": ["aircraft_category == helicopter"], "score": 70},
        },
    },
    "vessel_category": {
        "marine": {
            "container": {"score": 85}, "tanker": {"score": 82}, "bulk": {"score": 80}, "lng": {"score": 88},
            "lpg": {"score": 85}, "ro_ro": {"score": 75}, "passenger": {"score": 72}, "offshore": {"score": 70},
        },
    },
    "industry_classification": {
        "cyber": {
            "HEALTHCARE": {"score": 72, "data_sensitivity": "high"}, "FINANCIAL_SERVICES": {"score": 75, "data_sensitivity": "high"},
            "TECHNOLOGY": {"score": 85, "data_sensitivity": "medium"}, "MANUFACTURING": {"score": 80, "data_sensitivity": "low"},
        },
        "d_and_o": {
            "TECHNOLOGY": {"score": 72, "litigation_risk": "high"}, "HEALTHCARE_PHARMA": {"score": 70, "litigation_risk": "high"},
            "MANUFACTURING": {"score": 82, "litigation_risk": "low"}, "RETAIL": {"score": 78, "litigation_risk": "medium"},
        },
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
    """Categorizes numeric values into predefined buckets."""

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
class EnumerationCategorizer(DataCategorizer):
    """Maps attributes to predefined categories based on enumeration profiles."""

    def categorize(self, data: Dict[str, Any]) -> CategorizationResult:
        profile = self._get_profile(ENUMERATION_PROFILES, self.configuration)
        if not profile:
            return CategorizationResult(category="UNKNOWN", score=50, modifier=1.0, criteria=[f"No profile for {self.configuration}/{self.coverage}"], confidence=0.0)

        if "category" in data:
            direct_category = data["category"]
            if direct_category in profile:
                cat_data = profile[direct_category]
                return CategorizationResult(
                    category=direct_category, score=cat_data.get("score", 75),
                    modifier=MODIFIER_PROFILES.get(self.coverage, {}).get(self.configuration, {}).get(direct_category, 1.0),
                    criteria=[f"Direct mapping: {direct_category}"], confidence=1.0, metadata=cat_data
                )

        for category_name, category_def in profile.items():
            if "criteria" not in category_def:
                continue
            if self._evaluate_criteria(category_def["criteria"], data):
                return CategorizationResult(
                    category=category_name, score=category_def.get("score", 75),
                    modifier=MODIFIER_PROFILES.get(self.coverage, {}).get(self.configuration, {}).get(category_name, 1.0),
                    criteria=category_def["criteria"], confidence=0.9, metadata={"inferred": True}
                )
        return CategorizationResult(category="UNCATEGORIZED", score=70, modifier=1.0, criteria=["No matching category criteria"], confidence=0.5)

    def _evaluate_criteria(self, criteria: List[str], data: Dict[str, Any]) -> bool:
        for criterion in criteria:
            if not self._evaluate_single_criterion(criterion, data):
                return False
        return True

    def _evaluate_single_criterion(self, criterion: str, data: Dict[str, Any]) -> bool:
        if " in " in criterion:
            parts = criterion.split(" in ")
            field = parts[0].strip()
            values_str = parts[1].strip().strip("[]")
            allowed_values = [v.strip() for v in values_str.split(",")]
            return str(data.get(field, "")).lower() in [v.lower() for v in allowed_values]

        for op in [">=", "<=", "==", "!=", ">", "<"]:
            if op in criterion:
                parts = criterion.split(op)
                field, expected = parts[0].strip(), parts[1].strip()
                actual = data.get(field)
                if actual is None:
                    return False
                if expected.lower() in ["true", "false"]:
                    expected_bool = expected.lower() == "true"
                    return (bool(actual) == expected_bool) if op == "==" else (bool(actual) != expected_bool)
                try:
                    expected_num, actual_num = float(expected), float(actual)
                    if op == ">=": return actual_num >= expected_num
                    if op == "<=": return actual_num <= expected_num
                    if op == ">": return actual_num > expected_num
                    if op == "<": return actual_num < expected_num
                    if op == "==": return actual_num == expected_num
                    if op == "!=": return actual_num != expected_num
                except ValueError:
                    if op == "==": return str(actual).lower() == expected.lower()
                    if op == "!=": return str(actual).lower() != expected.lower()
                break
        return False


@register_categorizer
class TierCategorizer(DataCategorizer):
    """Maps composite scores to tier assignments."""

    def categorize(self, data: Dict[str, Any]) -> CategorizationResult:
        score = data.get("score")
        if score is None:
            return CategorizationResult(category="UNKNOWN", action="REFER", criteria=["No score provided"], confidence=0.0)

        profile = self._get_profile(TIER_PROFILES, self.coverage) or TIER_PROFILES["default"]
        tiers = profile.get("tiers", [])

        for tier_def in tiers:
            if tier_def["min_score"] <= score <= tier_def["max_score"]:
                action = "DECLINE" if tier_def.get("auto_decline") else ("APPROVE" if tier_def.get("auto_approve") else "REFER")
                return CategorizationResult(
                    category=tier_def["tier"], score=score, action=action,
                    criteria=[f"Score {score} in tier {tier_def['tier']}"], confidence=1.0,
                    metadata={"tier_def": tier_def}
                )
        return CategorizationResult(category="UNKNOWN", score=score, action="REFER", criteria=[f"Score {score} outside defined tiers"], confidence=0.5)


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
class ModifierCalculator(DataCategorizer):
    """Calculates composite modifier from multiple categorical features."""

    def categorize(self, data: Dict[str, Any]) -> CategorizationResult:
        coverage_modifiers = MODIFIER_PROFILES.get(self.coverage, {})
        if not coverage_modifiers:
            return CategorizationResult(modifier=1.0, criteria=[f"No modifier profile for {self.coverage}"], confidence=0.0)

        composite_modifier = 1.0
        applied_modifiers = []
        criteria = []

        for feature_name, feature_value in data.items():
            if feature_name in coverage_modifiers:
                feature_modifiers = coverage_modifiers[feature_name]
                if feature_value in feature_modifiers:
                    mod = feature_modifiers[feature_value]
                    composite_modifier *= mod
                    applied_modifiers.append({"feature": feature_name, "value": feature_value, "modifier": mod})
                    criteria.append(f"{feature_name}={feature_value} -> {mod}")

        return CategorizationResult(modifier=round(composite_modifier, 4), criteria=criteria, confidence=1.0 if applied_modifiers else 0.5, metadata={"applied_modifiers": applied_modifiers})


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
class QualityTierCategorizer(DataCategorizer):
    """Assigns quality tiers based on entity identification."""

    def categorize(self, data: Dict[str, Any]) -> CategorizationResult:
        entity = data.get("entity", "").lower().strip()
        if not entity:
            return CategorizationResult(category="UNKNOWN", score=50, criteria=["No entity provided"], confidence=0.0)

        profile = QUALITY_TIER_PROFILES.get(self.configuration)
        if not profile:
            return CategorizationResult(category="UNKNOWN", score=50, criteria=[f"No quality tier profile for {self.configuration}"], confidence=0.0)

        for tier_def in profile:
            for known_entity in tier_def["entities"]:
                if known_entity.lower() in entity or entity in known_entity.lower():
                    return CategorizationResult(
                        category=tier_def["tier"], score=tier_def["score"],
                        criteria=[f"Entity '{entity}' matched to {tier_def['tier']}"],
                        confidence=0.95, metadata={"matched_entity": known_entity}
                    )

        lowest_tier = profile[-1] if profile else None
        if lowest_tier:
            return CategorizationResult(category=lowest_tier["tier"], score=lowest_tier["score"], criteria=[f"Entity '{entity}' assigned default tier"], confidence=0.6)
        return CategorizationResult(category="UNKNOWN", score=50, criteria=[f"Unable to categorize entity '{entity}'"], confidence=0.0)


@register_categorizer
class CompositeScoreCategorizer(DataCategorizer):
    """Calculates weighted composite scores from signal groups with critical signal override."""

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

        for signal_name, signal_score in signals.items():
            if signal_name in weights:
                weight_def = weights[signal_name]
                weight = weight_def["weight"]
                contribution = signal_score * weight
                weighted_sum += contribution
                total_weight += weight
                signal_contributions.append({"signal": signal_name, "score": signal_score, "weight": weight, "contribution": contribution})

                if weight_def.get("critical", False):
                    threshold = weight_def.get("critical_threshold", 40)
                    if signal_score < threshold:
                        critical_failures.append({"signal": signal_name, "score": signal_score, "threshold": threshold})

        if total_weight == 0:
            return CategorizationResult(score=50, criteria=["No matching signals found in profile"], confidence=0.0)

        composite_score = weighted_sum / total_weight if total_weight > 0 else 50
        action = None
        criteria = [f"Weighted composite score: {composite_score:.1f}"]

        if critical_failures:
            composite_score = min(composite_score, 499)
            action = "REFER"
            for failure in critical_failures:
                criteria.append(f"CRITICAL: {failure['signal']} ({failure['score']}) below threshold ({failure['threshold']})")

        return CategorizationResult(
            score=round(composite_score, 2), action=action, criteria=criteria, confidence=1.0 if total_weight >= 0.8 else 0.7,
            metadata={"signal_contributions": signal_contributions, "critical_failures": critical_failures, "total_weight_applied": total_weight}
        )


@register_categorizer
class BooleanFlagCategorizer(DataCategorizer):
    """Evaluates boolean flags with associated consequences."""
    
    FLAG_DEFINITIONS: Dict[str, Dict[str, Dict[str, Any]]] = {
        "iosa_registered": {
            "true": {"score": 95, "modifier": 0.90, "message": "IOSA registered"},
            "false": {"score": 65, "modifier": 1.12, "message": "Not IOSA registered"},
        },
        "bug_bounty_program": {
            "true": {"score": 85, "modifier": 0.95, "message": "Bug bounty program active"},
            "false": {"score": 70, "modifier": 1.05, "message": "No bug bounty program"},
        },
        "offers_liner_service": {
            "true": {"score": 85, "modifier": 0.95, "message": "Offers liner service"},
            "false": {"score": 75, "modifier": 1.00, "message": "No liner service"},
        },
        "sanctioned_country_exposure": {
            "true": {"score": 20, "modifier": 1.50, "action": "REFER", "message": "Sanctioned country exposure"},
            "false": {"score": 90, "modifier": 1.00, "message": "No sanctioned exposure"},
        },
        "prior_bankruptcy": {
            "true": {"score": 45, "modifier": 1.25, "action": "REFER", "message": "Prior bankruptcy"},
            "false": {"score": 85, "modifier": 1.00, "message": "No bankruptcy history"},
        },
    }

    def categorize(self, data: Dict[str, Any]) -> CategorizationResult:
        flag_value = data.get("flag")
        if flag_value is None:
            return CategorizationResult(category="UNKNOWN", score=50, criteria=["No flag value provided"], confidence=0.0)

        flag_def = self.FLAG_DEFINITIONS.get(self.configuration)
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
class ScoringLogicCategorizer(DataCategorizer):
    """Maps discrete states to scores based on predefined logic profiles."""

    def categorize(self, data: Dict[str, Any]) -> CategorizationResult:
        state = data.get("state", "").upper()
        if not state:
            return CategorizationResult(category="UNKNOWN", score=50, criteria=["No state provided"], confidence=0.0)

        profile = SCORING_LOGIC_PROFILES.get(self.configuration)
        if not profile:
            return CategorizationResult(category="UNKNOWN", score=50, criteria=[f"No scoring logic profile for {self.configuration}"], confidence=0.0)

        score = profile.get(state)
        if score is not None:
            return CategorizationResult(category=state, score=score, criteria=[f"{self.configuration} state '{state}' -> score {score}"], confidence=1.0, metadata={"profile": self.configuration, "state": state})

        available_states = list(profile.keys())
        return CategorizationResult(category="UNKNOWN", score=50, criteria=[f"State '{state}' not found. Available: {available_states}"], confidence=0.0)


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def get_categorizer(categorizer_type: str, coverage: str, configuration: str, **kwargs: Any) -> DataCategorizer:
    """Factory function to instantiate categorizers."""
    type_mapping = {
        "threshold_bucket": ThresholdBucketCategorizer,
        "enumeration": EnumerationCategorizer,
        "tier": TierCategorizer,
        "condition": ConditionEvaluator,
        "modifier": ModifierCalculator,
        "majority": MajorityCategorizer,
        "rate_benchmark": RateBenchmarkCategorizer,
        "quality_tier": QualityTierCategorizer,
        "composite_score": CompositeScoreCategorizer,
        "boolean_flag": BooleanFlagCategorizer,
        "scoring_logic": ScoringLogicCategorizer,
    }

    categorizer_class = type_mapping.get(categorizer_type.lower())
    if not categorizer_class:
        raise ValueError(f"Unknown categorizer type '{categorizer_type}'. Available: {list(type_mapping.keys())}")

    return categorizer_class(coverage=coverage, configuration=configuration, **kwargs)


def list_available_profiles() -> Dict[str, List[str]]:
    """List all available configuration profiles."""
    return {
        "threshold_profiles": list(THRESHOLD_PROFILES.keys()),
        "modifier_profiles": list(MODIFIER_PROFILES.keys()),
        "tier_profiles": list(TIER_PROFILES.keys()),
        "quality_tier_profiles": list(QUALITY_TIER_PROFILES.keys()),
        "condition_bands": list(CONDITION_BANDS.keys()),
        "signal_weight_profiles": list(SIGNAL_WEIGHT_PROFILES.keys()),
        "scoring_logic_profiles": list(SCORING_LOGIC_PROFILES.keys()),
        "enumeration_profiles": list(ENUMERATION_PROFILES.keys()),
    }


# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("CATEGORISERS MODULE - DEMONSTRATION")
    print("=" * 60)

    ### DELETE - THIS IS A CATEGORISER
    # 1. ThresholdBucketCategorizer
    print("\n1. ThresholdBucketCategorizer (Marine Fleet Size)")
    cat = get_categorizer("threshold_bucket", "marine", "fleet_size")
    for size in [3, 25, 75, 150]:
        result = cat.categorize({"value": size})
        print(f"   Fleet size {size}: {result.category} (score={result.score}, modifier={result.modifier})")

    ### DELETE = THIS IS A CATEGORISER
    # 2. EnumerationCategorizer
    print("\n2. EnumerationCategorizer (Marine Operator Type)")
    cat = get_categorizer("enumeration", "marine", "operator_type")
    test_data = {"vessel_majority": "container", "fleet_size": 60, "offers_liner_service": True}
    result = cat.categorize(test_data)
    print(f"   Inferred: {result.category} (score={result.score})")

    ### KEEP - THIS NEEDS ADJUSTMENT TO TAKE IN VALUES FROM CONFIG, BUT IS REQUIRED
    # 3. TierCategorizer
    print("\n3. TierCategorizer (Score to Tier)")
    cat = get_categorizer("tier", "marine", "default")
    for score in [900, 750, 600, 450, 300]:
        result = cat.categorize({"score": score})
        print(f"   Score {score}: {result.category} (action={result.action})")

    ### KEEP - THIS NEEDS ADJUSTMENT TO TAKE IN VALUES FROM CONFIG, BUT IS REQUIRED
    # 4. ConditionEvaluator
    print("\n4. ConditionEvaluator (Safety Record)")
    cat = get_categorizer("condition", "marine", "safety_record_critical")
    for val in [15, 35, 55, 80]:
        result = cat.categorize({"value": val})
        print(f"   Safety score {val}: action={result.action}")

    ### KEEP - THIS NEEDS ADJUSTMENT TO TAKE IN VALUES FROM CONFIG, BUT IS REQUIRED
    # 5. ModifierCalculator
    print("\n5. ModifierCalculator (Composite Marine Modifier)")
    cat = get_categorizer("modifier", "marine", "composite")
    data = {"operator_type": "MAJOR_LINER", "fleet_size": "LARGE", "flag_state_quality": "WHITE"}
    result = cat.categorize(data)
    print(f"   Features: {data}")
    print(f"   Composite modifier: {result.modifier}")

    ### DELETE = THIS IS A AGGREGATOR
    # 6. MajorityCategorizer
    print("\n6. MajorityCategorizer (Vessel Category)")
    cat = get_categorizer("majority", "marine", "vessel_category")
    result = cat.categorize({"distribution": {"container": 45, "bulk": 15, "tanker": 10}})
    print(f"   Majority: {result.category} ({result.score:.1f}%)")

    #### I DONT KNOW ABOUT THIS ONE YET
    # 7. QualityTierCategorizer
    print("\n7. QualityTierCategorizer (Auditor)")
    cat = get_categorizer("quality_tier", "financial_institutions", "auditor")
    for entity in ["Deloitte", "BDO USA", "Smith CPA"]:
        result = cat.categorize({"entity": entity})
        print(f"   '{entity}': {result.category} (score={result.score})")

    ### KEEP - THIS NEEDS ADJUSTMENT TO TAKE IN VALUES FROM CONFIG, BUT IS REQUIRED
    # 8. CompositeScoreCategorizer
    print("\n8. CompositeScoreCategorizer (Marine Signals)")
    cat = get_categorizer("composite_score", "marine", "default")
    signals = {"safety_compliance": 85, "operational_telemetry": 78, "sanctions_compliance": 92, "financial_stability": 70}
    result = cat.categorize({"signals": signals})
    print(f"   Composite score: {result.score}")

    ### KEEP - THIS NEEDS ADJUSTMENT TO TAKE IN VALUES FROM CONFIG, BUT IS REQUIRED
    # 9. BooleanFlagCategorizer
    print("\n9. BooleanFlagCategorizer (IOSA Registered)")
    cat = get_categorizer("boolean_flag", "aerospace", "iosa_registered")
    for val in [True, False]:
        result = cat.categorize({"flag": val})
        print(f"   IOSA registered={val}: score={result.score}, modifier={result.modifier}")

    ### KEEP - THIS NEEDS ADJUSTMENT TO TAKE IN VALUES FROM CONFIG, BUT IS REQUIRED
    # 10. ScoringLogicCategorizer
    print("\n10. ScoringLogicCategorizer (PSC Detention)")
    cat = get_categorizer("scoring_logic", "marine", "psc_detention_status")
    for state in ["NONE_3YR", "DETAINED_1_3YR", "DETAINED_3_PLUS_3YR"]:
        result = cat.categorize({"state": state})
        print(f"    State '{state}': score={result.score}")
