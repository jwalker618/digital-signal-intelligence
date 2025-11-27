"""
Digital Signal Intelligence (DSI) - Energy Insurance Pricing Model
==================================================================

DSI-compliant energy insurance pricing based entirely on externally observable
signals, network authority analysis, and minimal optional direct inquiry.

This model conforms to Foundational Principles.

Energy insurance is well-suited to DSI because:
- Regulatory filings (EPA, OSHA, state agencies) are public
- Satellite imagery reveals operational patterns
- Industry databases track safety performance
- Corporate ESG disclosures are increasingly detailed
- Operator behavior patterns predict asset-level risk

Key DSI Principle: We assess OPERATOR safety culture and operational patterns,
not individual asset characteristics. Good operators maintain all assets well;
poor operators have systemic issues across their portfolio.

Author: John Walker
Version: 2.0
Date: November 2025
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple
from datetime import datetime


# =============================================================================
# ENUMERATIONS
# =============================================================================

class OperatorType(Enum):
    """Operator classification from observable signals."""
    SUPERMAJOR = "supermajor"              # ExxonMobil, Shell, BP, etc.
    MAJOR_INTEGRATED = "major_integrated"   # Large integrated operators
    LARGE_INDEPENDENT = "large_independent" # Large E&P independents
    MID_INDEPENDENT = "mid_independent"     # Mid-size independents
    SMALL_INDEPENDENT = "small_independent" # Small independents
    NATIONAL_OIL = "national_oil"          # NOCs
    MIDSTREAM_MAJOR = "midstream_major"     # Major pipeline/processing
    DOWNSTREAM_MAJOR = "downstream_major"   # Major refining
    PRIVATE_EQUITY = "private_equity"       # PE-backed operators
    UNKNOWN = "unknown"


class OperationSegment(Enum):
    """Primary operation segment."""
    UPSTREAM_CONVENTIONAL = "upstream_conventional"
    UPSTREAM_UNCONVENTIONAL = "upstream_unconventional"  # Shale, tight oil
    UPSTREAM_OFFSHORE = "upstream_offshore"
    UPSTREAM_DEEPWATER = "upstream_deepwater"
    MIDSTREAM_PIPELINE = "midstream_pipeline"
    MIDSTREAM_PROCESSING = "midstream_processing"
    MIDSTREAM_STORAGE = "midstream_storage"
    DOWNSTREAM_REFINING = "downstream_refining"
    DOWNSTREAM_PETROCHEMICAL = "downstream_petrochemical"
    POWER_GENERATION = "power_generation"
    RENEWABLE = "renewable"
    MIXED = "mixed"


class GeographicFocus(Enum):
    """Primary geographic focus."""
    US_ONSHORE = "us_onshore"
    US_GULF_SHELF = "us_gulf_shelf"
    US_GULF_DEEPWATER = "us_gulf_deepwater"
    NORTH_SEA = "north_sea"
    WEST_AFRICA = "west_africa"
    MIDDLE_EAST = "middle_east"
    ASIA_PACIFIC = "asia_pacific"
    LATIN_AMERICA = "latin_america"
    GLOBAL_DIVERSIFIED = "global_diversified"
    OTHER = "other"


# =============================================================================
# SIGNAL DATA STRUCTURES
# =============================================================================

@dataclass
class NetworkAuthoritySignals:
    """
    Type 1: Network Authority Signals
    
    Who trusts this operator? What relationships indicate quality?
    """
    
    # JV partner quality (majors, NOCs, quality independents)
    partner_quality_score: float = 0.0
    partner_quality_evidence: str = ""
    
    # Contractor relationships (tier-1 service companies)
    contractor_quality_score: float = 0.0
    contractor_quality_evidence: str = ""
    
    # Banking/financing relationships
    banking_relationship_score: float = 0.0
    banking_relationship_evidence: str = ""
    
    # Insurance market reputation (historical placement)
    insurance_history_score: float = 0.0
    insurance_history_evidence: str = ""
    
    # Industry association membership (API, IOGP, etc.)
    industry_association_score: float = 0.0
    industry_association_evidence: str = ""
    
    # Regulator relationship quality
    regulator_relationship_score: float = 0.0
    regulator_relationship_evidence: str = ""
    
    # Offtake/customer quality
    customer_quality_score: float = 0.0
    customer_quality_evidence: str = ""


@dataclass
class SafetyPerformanceSignals:
    """
    Type 6: Public Record Signals - Safety Component
    
    From OSHA, BSEE, EPA, state agencies, and industry databases.
    """
    
    # OSHA recordable incident rate (vs industry benchmark)
    osha_trir_score: float = 0.0
    osha_trir_evidence: str = ""
    
    # OSHA serious violations
    osha_violations_score: float = 0.0
    osha_violations_evidence: str = ""
    
    # BSEE incidents (offshore)
    bsee_incident_score: float = 0.0
    bsee_incident_evidence: str = ""
    
    # Process safety events (Tier 1, Tier 2)
    process_safety_score: float = 0.0
    process_safety_evidence: str = ""
    
    # Fatality history
    fatality_score: float = 0.0
    fatality_evidence: str = ""
    
    # Major incident history (explosions, blowouts, major spills)
    major_incident_score: float = 0.0
    major_incident_evidence: str = ""
    
    # Near-miss reporting (if disclosed)
    near_miss_score: float = 0.0
    near_miss_evidence: str = ""


@dataclass
class EnvironmentalComplianceSignals:
    """
    Type 6: Public Record Signals - Environmental Component
    
    From EPA, state agencies, and public disclosures.
    """
    
    # EPA violations (CAA, CWA, RCRA)
    epa_violation_score: float = 0.0
    epa_violation_evidence: str = ""
    
    # Spill history (NRC reports, state records)
    spill_history_score: float = 0.0
    spill_history_evidence: str = ""
    
    # Air emissions compliance
    emissions_compliance_score: float = 0.0
    emissions_compliance_evidence: str = ""
    
    # Flaring intensity (satellite-derived)
    flaring_score: float = 0.0
    flaring_evidence: str = ""
    
    # Methane emissions (satellite-derived)
    methane_score: float = 0.0
    methane_evidence: str = ""
    
    # Remediation obligations
    remediation_score: float = 0.0
    remediation_evidence: str = ""


@dataclass
class OperationalTelemetrySignals:
    """
    Type 3: Asset Telemetry Signals
    
    From satellite imagery, production data, and observable patterns.
    """
    
    # Production consistency (volatility in reported production)
    production_consistency_score: float = 0.0
    production_consistency_evidence: str = ""
    
    # Facility activity patterns (satellite-derived)
    facility_activity_score: float = 0.0
    facility_activity_evidence: str = ""
    
    # Well integrity indicators (shut-in patterns)
    well_integrity_score: float = 0.0
    well_integrity_evidence: str = ""
    
    # Maintenance patterns (observable turnarounds, shutdowns)
    maintenance_pattern_score: float = 0.0
    maintenance_pattern_evidence: str = ""
    
    # Operational efficiency (production per well, utilization)
    operational_efficiency_score: float = 0.0
    operational_efficiency_evidence: str = ""


@dataclass
class FinancialStabilitySignals:
    """
    Type 6: Public Record Signals - Financial Component
    Type 4: Structured Data Signals
    
    Financial health affects maintenance, safety investment, and claims risk.
    """
    
    # Credit rating
    credit_rating_score: float = 0.0
    credit_rating_evidence: str = ""
    
    # Debt/equity ratio relative to peers
    leverage_score: float = 0.0
    leverage_evidence: str = ""
    
    # Asset retirement obligation coverage
    aro_coverage_score: float = 0.0
    aro_coverage_evidence: str = ""
    
    # Capex trends (maintenance vs growth)
    capex_trend_score: float = 0.0
    capex_trend_evidence: str = ""
    
    # Bankruptcy/restructuring history
    restructuring_score: float = 0.0
    restructuring_evidence: str = ""


@dataclass
class AssetPortfolioSignals:
    """
    Type 6: Public Record Signals - Asset Component
    
    From regulatory filings, permit databases, and public disclosures.
    """
    
    # Asset age profile
    asset_age_score: float = 0.0
    asset_age_evidence: str = ""
    
    # Geographic concentration risk
    concentration_score: float = 0.0
    concentration_evidence: str = ""
    
    # Technology/complexity profile
    complexity_score: float = 0.0
    complexity_evidence: str = ""
    
    # Decommissioning obligations
    decommissioning_score: float = 0.0
    decommissioning_evidence: str = ""
    
    # Permit status (active, expired, pending)
    permit_status_score: float = 0.0
    permit_status_evidence: str = ""


@dataclass
class CorporateFootprintSignals:
    """
    Type 5: Corporate Digital Footprint Signals
    """
    
    # Safety culture communication
    safety_communication_score: float = 0.0
    safety_communication_evidence: str = ""
    
    # ESG/sustainability reporting quality
    esg_reporting_score: float = 0.0
    esg_reporting_evidence: str = ""
    
    # Technical hiring (HSE roles, engineers)
    technical_hiring_score: float = 0.0
    technical_hiring_evidence: str = ""
    
    # Industry conference presence
    industry_presence_score: float = 0.0
    industry_presence_evidence: str = ""
    
    # Transparency/disclosure quality
    disclosure_quality_score: float = 0.0
    disclosure_quality_evidence: str = ""
    
    # Leadership visibility (HSE leadership profiles)
    hse_leadership_score: float = 0.0
    hse_leadership_evidence: str = ""


@dataclass
class StructuredDataSignals:
    """
    Type 4: Structured Data Feed Signals
    """
    
    # ESG ratings (MSCI, Sustainalytics)
    esg_rating_score: float = 0.0
    esg_rating_evidence: str = ""
    
    # Industry benchmarking data
    benchmark_score: float = 0.0
    benchmark_evidence: str = ""
    
    # Credit rating
    credit_score: float = 0.0
    credit_evidence: str = ""


@dataclass
class DirectInquirySignals:
    """
    Type 7: Direct Inquiry Signals (Optional)
    
    Maximum 6 questions for Energy.
    """
    
    major_incidents: Optional[bool] = None
    # "Any major incidents (explosion, blowout, major spill) in past 5 years?"
    
    fatalities: Optional[bool] = None
    # "Any work-related fatalities in past 3 years?"
    
    regulatory_enforcement: Optional[bool] = None
    # "Any significant regulatory enforcement actions pending?"
    
    decommissioning_obligations: Optional[bool] = None
    # "Any significant unfunded decommissioning obligations?"
    
    joint_venture_operator: Optional[bool] = None
    # "Are you the designated operator for JV assets?"
    
    third_party_contractor: Optional[bool] = None
    # "Do you use third-party contractors for drilling/completions?"


# =============================================================================
# OPERATOR PROFILE
# =============================================================================

@dataclass
class EnergyOperatorProfile:
    """
    Operator profile from observable data.
    
    DSI Principle: We assess operators, not individual assets.
    Operator safety culture indicates portfolio-wide risk quality.
    """
    
    # Identifiers
    operator_name: str
    ticker: Optional[str]
    primary_domain: str
    
    # Classification
    operator_type: OperatorType
    operation_segment: OperationSegment
    geographic_focus: GeographicFocus
    headquarters_country: str
    is_publicly_traded: bool = False
    
    # Observable portfolio metrics
    estimated_production_boed: float = 0.0  # From public data
    estimated_asset_count: int = 0
    primary_basins: List[str] = field(default_factory=list)
    
    # All signal categories
    network_authority: NetworkAuthoritySignals = field(default_factory=NetworkAuthoritySignals)
    safety_performance: SafetyPerformanceSignals = field(default_factory=SafetyPerformanceSignals)
    environmental_compliance: EnvironmentalComplianceSignals = field(default_factory=EnvironmentalComplianceSignals)
    operational_telemetry: OperationalTelemetrySignals = field(default_factory=OperationalTelemetrySignals)
    financial_stability: FinancialStabilitySignals = field(default_factory=FinancialStabilitySignals)
    asset_portfolio: AssetPortfolioSignals = field(default_factory=AssetPortfolioSignals)
    corporate_footprint: CorporateFootprintSignals = field(default_factory=CorporateFootprintSignals)
    structured_data: StructuredDataSignals = field(default_factory=StructuredDataSignals)
    direct_inquiry: DirectInquirySignals = field(default_factory=DirectInquirySignals)


# =============================================================================
# SCORING ENGINE
# =============================================================================

class EnergyDSIScorer:
    """
    Calculates composite scores from individual signals.
    
    Energy weight emphasizes safety performance and environmental compliance
    as these directly predict property damage and liability claims.
    """
    
    CATEGORY_WEIGHTS = {
        "network_authority": 0.10,
        "safety_performance": 0.30,        # Critical - predicts claims
        "environmental_compliance": 0.20,  # Critical - liability exposure
        "operational_telemetry": 0.10,
        "financial_stability": 0.10,
        "asset_portfolio": 0.10,
        "corporate_footprint": 0.05,
        "structured_data": 0.05,
    }
    
    SIGNAL_WEIGHTS = {
        "network_authority": {
            "partner_quality": 0.20, "contractor_quality": 0.15, "banking_relationship": 0.15,
            "insurance_history": 0.15, "industry_association": 0.10, "regulator_relationship": 0.15,
            "customer_quality": 0.10,
        },
        "safety_performance": {
            "osha_trir": 0.20, "osha_violations": 0.15, "bsee_incident": 0.10,
            "process_safety": 0.20, "fatality": 0.15, "major_incident": 0.15, "near_miss": 0.05,
        },
        "environmental_compliance": {
            "epa_violation": 0.20, "spill_history": 0.25, "emissions_compliance": 0.15,
            "flaring": 0.15, "methane": 0.15, "remediation": 0.10,
        },
        "operational_telemetry": {
            "production_consistency": 0.20, "facility_activity": 0.20, "well_integrity": 0.20,
            "maintenance_pattern": 0.20, "operational_efficiency": 0.20,
        },
        "financial_stability": {
            "credit_rating": 0.25, "leverage": 0.20, "aro_coverage": 0.20,
            "capex_trend": 0.20, "restructuring": 0.15,
        },
        "asset_portfolio": {
            "asset_age": 0.25, "concentration": 0.20, "complexity": 0.20,
            "decommissioning": 0.20, "permit_status": 0.15,
        },
        "corporate_footprint": {
            "safety_communication": 0.20, "esg_reporting": 0.20, "technical_hiring": 0.15,
            "industry_presence": 0.15, "disclosure_quality": 0.15, "hse_leadership": 0.15,
        },
        "structured_data": {
            "esg_rating": 0.40, "benchmark": 0.35, "credit": 0.25,
        },
    }
    
    def calculate_category_score(self, signals: object, category: str) -> Tuple[float, int, int]:
        weights = self.SIGNAL_WEIGHTS.get(category, {})
        weighted_sum, weight_sum, available = 0.0, 0.0, 0
        
        for signal_name, weight in weights.items():
            score = getattr(signals, f"{signal_name}_score", 0)
            if score > 0:
                weighted_sum += score * weight
                weight_sum += weight
                available += 1
        
        return (weighted_sum / weight_sum if weight_sum > 0 else 0.0, available, len(weights))
    
    def calculate_composite_score(self, operator: EnergyOperatorProfile) -> Tuple[float, float, Dict[str, float]]:
        category_signals = {
            "network_authority": operator.network_authority,
            "safety_performance": operator.safety_performance,
            "environmental_compliance": operator.environmental_compliance,
            "operational_telemetry": operator.operational_telemetry,
            "financial_stability": operator.financial_stability,
            "asset_portfolio": operator.asset_portfolio,
            "corporate_footprint": operator.corporate_footprint,
            "structured_data": operator.structured_data,
        }
        
        category_scores, total_available, total_possible = {}, 0, 0
        weighted_composite, weight_sum = 0.0, 0.0
        
        for category, signals in category_signals.items():
            score, available, total = self.calculate_category_score(signals, category)
            category_scores[category] = score
            total_available += available
            total_possible += total
            if available > 0:
                weighted_composite += score * self.CATEGORY_WEIGHTS[category]
                weight_sum += self.CATEGORY_WEIGHTS[category]
        
        composite = (weighted_composite / weight_sum * 10) if weight_sum > 0 else 0.0
        coverage = total_available / total_possible if total_possible > 0 else 0
        
        if coverage >= 0.85: confidence = 0.95
        elif coverage >= 0.70: confidence = 0.75 + (coverage - 0.70) * (0.20 / 0.15)
        elif coverage >= 0.55: confidence = 0.60 + (coverage - 0.55) * (0.15 / 0.15)
        else: confidence = coverage / 0.55 * 0.60
        
        return composite, confidence, category_scores
    
    def apply_direct_inquiry_adjustment(self, score: float, inquiry: DirectInquirySignals) -> Tuple[float, List[str]]:
        adjustment, notes = 0.0, []
        
        # Critical negative signals
        if inquiry.major_incidents is True:
            adjustment -= 150
            notes.append("Major incidents in past 5 years: -150")
        
        if inquiry.fatalities is True:
            adjustment -= 100
            notes.append("Fatalities in past 3 years: -100")
        
        if inquiry.regulatory_enforcement is True:
            adjustment -= 75
            notes.append("Pending regulatory enforcement: -75")
        
        if inquiry.decommissioning_obligations is True:
            adjustment -= 50
            notes.append("Unfunded decommissioning obligations: -50")
        
        # Positive confirmations
        if inquiry.major_incidents is False:
            adjustment += 50
            notes.append("No major incidents confirmed: +50")
        
        if inquiry.fatalities is False:
            adjustment += 30
            notes.append("No fatalities confirmed: +30")
        
        # Informational
        if inquiry.joint_venture_operator is True:
            notes.append("JV operator status noted")
        
        return max(0, min(1000, score + adjustment)), notes


# =============================================================================
# TIER ASSIGNMENT
# =============================================================================

class EnergyTierAssignment:
    TIER_THRESHOLDS = {1: 800, 2: 650, 3: 500, 4: 350, 5: 0}
    TIER_LABELS = {1: "Preferred", 2: "Standard", 3: "Elevated", 4: "High Risk", 5: "Critical"}
    TIER_ACTIONS = {
        1: "Auto-approve at preferred pricing",
        2: "Auto-approve at standard pricing",
        3: "Auto-approve with conditions",
        4: "Manual review required",
        5: "Decline or senior review required",
    }
    
    @classmethod
    def assign_tier(cls, score: float) -> Tuple[int, str, str]:
        for tier in range(1, 6):
            if score >= cls.TIER_THRESHOLDS[tier]:
                return tier, cls.TIER_LABELS[tier], cls.TIER_ACTIONS[tier]
        return 5, cls.TIER_LABELS[5], cls.TIER_ACTIONS[5]
    
    @classmethod
    def check_critical_overrides(cls, operator: EnergyOperatorProfile, tier: int) -> Tuple[int, Optional[str]]:
        # Major incident history - critical
        safety = operator.safety_performance
        if safety.major_incident_score > 0 and safety.major_incident_score < 40:
            if tier < 4:
                return 4, "Major incident history"
        
        # Fatality history
        if safety.fatality_score > 0 and safety.fatality_score < 50:
            if tier < 3:
                return 3, "Fatality history"
        
        # Serious OSHA violations
        if safety.osha_violations_score > 0 and safety.osha_violations_score < 40:
            if tier < 3:
                return 3, "Serious OSHA violation history"
        
        # EPA violations
        env = operator.environmental_compliance
        if env.epa_violation_score > 0 and env.epa_violation_score < 40:
            if tier < 3:
                return 3, "Significant EPA violations"
        
        # Major spill history
        if env.spill_history_score > 0 and env.spill_history_score < 40:
            if tier < 4:
                return 4, "Major spill history"
        
        # Financial distress
        fin = operator.financial_stability
        if fin.restructuring_score > 0 and fin.restructuring_score < 40:
            if tier < 4:
                return 4, "Bankruptcy/restructuring history"
        
        # Direct inquiry overrides
        if operator.direct_inquiry.major_incidents is True:
            if tier < 4:
                return 4, "Major incidents disclosed"
        
        if operator.direct_inquiry.fatalities is True:
            if tier < 3:
                return 3, "Fatalities disclosed"
        
        return tier, None


# =============================================================================
# PRICING ENGINE
# =============================================================================

class EnergyPricingEngine:
    """
    Calculates premium based on tier, operator type, and segment.
    
    Energy uses rate per $1M of Total Insured Value (TIV).
    """
    
    TIER_BASE_RATE = {  # Per $1M TIV
        1: 0.0008,   # 0.08%
        2: 0.0012,   # 0.12%
        3: 0.0018,   # 0.18%
        4: 0.0028,   # 0.28%
        5: 0.0045,   # 0.45%
    }
    
    OPERATOR_TYPE_MULTIPLIERS = {
        OperatorType.SUPERMAJOR: 0.75,
        OperatorType.MAJOR_INTEGRATED: 0.85,
        OperatorType.LARGE_INDEPENDENT: 0.95,
        OperatorType.MID_INDEPENDENT: 1.00,
        OperatorType.SMALL_INDEPENDENT: 1.20,
        OperatorType.NATIONAL_OIL: 0.90,
        OperatorType.MIDSTREAM_MAJOR: 0.85,
        OperatorType.DOWNSTREAM_MAJOR: 0.90,
        OperatorType.PRIVATE_EQUITY: 1.15,
        OperatorType.UNKNOWN: 1.40,
    }
    
    SEGMENT_MULTIPLIERS = {
        OperationSegment.UPSTREAM_CONVENTIONAL: 1.00,
        OperationSegment.UPSTREAM_UNCONVENTIONAL: 0.95,  # Lower severity
        OperationSegment.UPSTREAM_OFFSHORE: 1.20,
        OperationSegment.UPSTREAM_DEEPWATER: 1.50,       # Highest risk
        OperationSegment.MIDSTREAM_PIPELINE: 0.80,
        OperationSegment.MIDSTREAM_PROCESSING: 1.00,
        OperationSegment.MIDSTREAM_STORAGE: 0.85,
        OperationSegment.DOWNSTREAM_REFINING: 1.30,      # Complex, high values
        OperationSegment.DOWNSTREAM_PETROCHEMICAL: 1.25,
        OperationSegment.POWER_GENERATION: 0.90,
        OperationSegment.RENEWABLE: 0.70,                # Lower hazard
        OperationSegment.MIXED: 1.05,
    }
    
    GEOGRAPHY_MULTIPLIERS = {
        GeographicFocus.US_ONSHORE: 1.00,
        GeographicFocus.US_GULF_SHELF: 1.10,
        GeographicFocus.US_GULF_DEEPWATER: 1.40,
        GeographicFocus.NORTH_SEA: 1.15,
        GeographicFocus.WEST_AFRICA: 1.25,
        GeographicFocus.MIDDLE_EAST: 1.20,
        GeographicFocus.ASIA_PACIFIC: 1.10,
        GeographicFocus.LATIN_AMERICA: 1.20,
        GeographicFocus.GLOBAL_DIVERSIFIED: 1.05,
        GeographicFocus.OTHER: 1.15,
    }
    
    @classmethod
    def calculate_premium(
        cls,
        tier: int,
        operator_type: OperatorType,
        segment: OperationSegment,
        geography: GeographicFocus,
        total_insured_value: float,
    ) -> Tuple[float, Dict]:
        
        base_rate = cls.TIER_BASE_RATE[tier]
        operator_mult = cls.OPERATOR_TYPE_MULTIPLIERS.get(operator_type, 1.0)
        segment_mult = cls.SEGMENT_MULTIPLIERS.get(segment, 1.0)
        geo_mult = cls.GEOGRAPHY_MULTIPLIERS.get(geography, 1.0)
        
        adjusted_rate = base_rate * operator_mult * segment_mult * geo_mult
        premium = total_insured_value * adjusted_rate
        
        # Minimum premium
        minimum = 100000
        premium = max(premium, minimum)
        
        components = {
            "base_rate": base_rate,
            "operator_multiplier": operator_mult,
            "segment_multiplier": segment_mult,
            "geography_multiplier": geo_mult,
            "adjusted_rate": adjusted_rate,
            "total_insured_value": total_insured_value,
        }
        
        return premium, components
    
    @classmethod
    def recommend_deductible(cls, tier: int, total_insured_value: float) -> float:
        """Recommend deductible based on TIV and tier."""
        deductible_pcts = {1: 0.005, 2: 0.0075, 3: 0.01, 4: 0.015, 5: 0.02}
        deductible = total_insured_value * deductible_pcts.get(tier, 0.01)
        
        # Bounds
        deductible = max(250_000, min(10_000_000, deductible))
        
        # Round to standard
        standard = [250_000, 500_000, 1_000_000, 2_500_000, 5_000_000, 10_000_000]
        return min(standard, key=lambda x: abs(x - deductible))


# =============================================================================
# DECISION ENGINE
# =============================================================================

@dataclass
class EnergyUnderwritingDecision:
    """Complete underwriting decision output."""
    operator_name: str
    operator_type: str
    operation_segment: str
    geographic_focus: str
    composite_score: float
    confidence: float
    category_scores: Dict[str, float]
    tier: int
    tier_label: str
    tier_action: str
    tier_override_reason: Optional[str]
    total_insured_value: float
    recommended_deductible: float
    annual_premium: float
    premium_rate: float
    pricing_components: Dict[str, float]
    decision: str
    conditions: List[str]
    reasoning: str
    direct_inquiry_applied: bool
    direct_inquiry_adjustments: List[str]
    signals_available: int
    signals_total: int
    assessment_timestamp: str


class EnergyDecisionEngine:
    @classmethod
    def generate_conditions(cls, tier: int, operator: EnergyOperatorProfile) -> List[str]:
        conditions = []
        
        if tier >= 2:
            conditions.append("Annual OSHA/safety metrics reporting required")
        
        if tier >= 3:
            conditions.append("Quarterly incident reporting required")
            conditions.append("HSE audit within 12 months required")
        
        # Signal-driven conditions
        safety = operator.safety_performance
        if safety.process_safety_score > 0 and safety.process_safety_score < 60:
            conditions.append("Process safety management review required")
        
        env = operator.environmental_compliance
        if env.spill_history_score > 0 and env.spill_history_score < 60:
            conditions.append("Spill prevention plan to be verified")
        
        if env.flaring_score > 0 and env.flaring_score < 60:
            conditions.append("Flaring reduction plan required")
        
        fin = operator.financial_stability
        if fin.aro_coverage_score > 0 and fin.aro_coverage_score < 60:
            conditions.append("ARO funding status to be verified")
        
        if tier >= 4:
            conditions.append("Senior underwriter approval required")
            conditions.append("Loss control survey required before binding")
            conditions.append("Named asset schedule with individual values required")
        
        # Always
        conditions.append("Prompt notice of incidents required")
        conditions.append("Compliance with all regulatory requirements warranted")
        
        return conditions
    
    @classmethod
    def generate_decision(cls, tier: int, confidence: float, score: float, operator: EnergyOperatorProfile) -> Tuple[str, str]:
        if confidence < 0.60:
            return "REFER", f"Insufficient signal coverage (confidence: {confidence:.0%}). Manual underwriting required."
        
        if tier == 1:
            return "APPROVE", f"Excellent operator profile (score: {score:.0f}/1000). Strong safety record, minimal environmental issues, robust financials. Preferred pricing."
        elif tier == 2:
            return "APPROVE", f"Good operator profile (score: {score:.0f}/1000). Acceptable safety and environmental record. Standard pricing."
        elif tier == 3:
            concerns = []
            if operator.safety_performance.osha_trir_score < 60:
                concerns.append("elevated incident rate")
            if operator.environmental_compliance.spill_history_score < 60:
                concerns.append("spill history")
            if operator.financial_stability.leverage_score < 60:
                concerns.append("financial leverage")
            concern_str = ", ".join(concerns) if concerns else "elevated risk indicators"
            return "APPROVE_WITH_CONDITIONS", f"Moderate risk profile (score: {score:.0f}/1000). Concerns: {concern_str}."
        elif tier == 4:
            return "REFER", f"High risk profile (score: {score:.0f}/1000). Manual review required."
        else:
            return "DECLINE", f"Critical risk profile (score: {score:.0f}/1000). Risk exceeds appetite."


# =============================================================================
# MAIN PRICING MODEL
# =============================================================================

class EnergyDSIPricingModel:
    """Complete DSI Energy Insurance Pricing Model."""
    
    def __init__(self):
        self.scorer = EnergyDSIScorer()
    
    def assess(
        self,
        operator: EnergyOperatorProfile,
        total_insured_value: float,
    ) -> EnergyUnderwritingDecision:
        
        # Step 1: Calculate composite score
        composite, confidence, category_scores = self.scorer.calculate_composite_score(operator)
        
        # Step 2: Apply direct inquiry adjustments
        adjusted, inquiry_notes = self.scorer.apply_direct_inquiry_adjustment(composite, operator.direct_inquiry)
        
        # Step 3: Assign tier
        tier, tier_label, tier_action = EnergyTierAssignment.assign_tier(adjusted)
        
        # Step 4: Check critical overrides
        tier, override = EnergyTierAssignment.check_critical_overrides(operator, tier)
        if override:
            tier_label = EnergyTierAssignment.TIER_LABELS[tier]
            tier_action = EnergyTierAssignment.TIER_ACTIONS[tier]
        
        # Step 5: Calculate premium
        premium, pricing = EnergyPricingEngine.calculate_premium(
            tier=tier,
            operator_type=operator.operator_type,
            segment=operator.operation_segment,
            geography=operator.geographic_focus,
            total_insured_value=total_insured_value,
        )
        
        deductible = EnergyPricingEngine.recommend_deductible(tier, total_insured_value)
        
        # Step 6: Generate decision
        decision, reasoning = EnergyDecisionEngine.generate_decision(tier, confidence, adjusted, operator)
        conditions = EnergyDecisionEngine.generate_conditions(tier, operator)
        
        # Signal count
        signals_available = sum(
            1 for cat in [operator.network_authority, operator.safety_performance,
                         operator.environmental_compliance, operator.operational_telemetry,
                         operator.financial_stability, operator.asset_portfolio,
                         operator.corporate_footprint, operator.structured_data]
            for attr in dir(cat) if attr.endswith('_score') and getattr(cat, attr, 0) > 0
        )
        
        return EnergyUnderwritingDecision(
            operator_name=operator.operator_name,
            operator_type=operator.operator_type.value,
            operation_segment=operator.operation_segment.value,
            geographic_focus=operator.geographic_focus.value,
            composite_score=adjusted,
            confidence=confidence,
            category_scores=category_scores,
            tier=tier,
            tier_label=tier_label,
            tier_action=tier_action,
            tier_override_reason=override,
            total_insured_value=total_insured_value,
            recommended_deductible=deductible,
            annual_premium=premium,
            premium_rate=pricing["adjusted_rate"],
            pricing_components=pricing,
            decision=decision,
            conditions=conditions,
            reasoning=reasoning,
            direct_inquiry_applied=len(inquiry_notes) > 0,
            direct_inquiry_adjustments=inquiry_notes,
            signals_available=signals_available,
            signals_total=43,
            assessment_timestamp=datetime.now().isoformat(),
        )


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("DSI ENERGY INSURANCE PRICING MODEL v2.0")
    print("=" * 80)
    
    # Example: Major integrated operator with strong profile
    operator = EnergyOperatorProfile(
        operator_name="PetroCorp International",
        ticker="PCOR",
        primary_domain="petrocorp.com",
        operator_type=OperatorType.MAJOR_INTEGRATED,
        operation_segment=OperationSegment.MIXED,
        geographic_focus=GeographicFocus.GLOBAL_DIVERSIFIED,
        headquarters_country="US",
        is_publicly_traded=True,
        estimated_production_boed=450000,
        estimated_asset_count=150,
        primary_basins=["Permian", "Eagle Ford", "Gulf of Mexico", "North Sea"],
        
        network_authority=NetworkAuthoritySignals(
            partner_quality_score=90,
            contractor_quality_score=88,
            banking_relationship_score=92,
            insurance_history_score=85,
            industry_association_score=90,
            regulator_relationship_score=85,
            customer_quality_score=88,
        ),
        safety_performance=SafetyPerformanceSignals(
            osha_trir_score=88,
            osha_violations_score=92,
            bsee_incident_score=85,
            process_safety_score=90,
            fatality_score=95,
            major_incident_score=92,
            near_miss_score=80,
        ),
        environmental_compliance=EnvironmentalComplianceSignals(
            epa_violation_score=88,
            spill_history_score=85,
            emissions_compliance_score=82,
            flaring_score=78,
            methane_score=80,
            remediation_score=85,
        ),
        operational_telemetry=OperationalTelemetrySignals(
            production_consistency_score=88,
            facility_activity_score=85,
            well_integrity_score=90,
            maintenance_pattern_score=85,
            operational_efficiency_score=82,
        ),
        financial_stability=FinancialStabilitySignals(
            credit_rating_score=88,
            leverage_score=82,
            aro_coverage_score=90,
            capex_trend_score=85,
            restructuring_score=100,
        ),
        asset_portfolio=AssetPortfolioSignals(
            asset_age_score=80,
            concentration_score=85,
            complexity_score=75,
            decommissioning_score=82,
            permit_status_score=95,
        ),
        corporate_footprint=CorporateFootprintSignals(
            safety_communication_score=88,
            esg_reporting_score=85,
            technical_hiring_score=82,
            industry_presence_score=90,
            disclosure_quality_score=85,
            hse_leadership_score=88,
        ),
        structured_data=StructuredDataSignals(
            esg_rating_score=82,
            benchmark_score=85,
            credit_score=88,
        ),
        direct_inquiry=DirectInquirySignals(
            major_incidents=False,
            fatalities=False,
            regulatory_enforcement=False,
            joint_venture_operator=True,
        ),
    )
    
    model = EnergyDSIPricingModel()
    decision = model.assess(operator, total_insured_value=5_000_000_000)
    
    print(f"\nOperator: {decision.operator_name}")
    print(f"Type: {decision.operator_type} | Segment: {decision.operation_segment}")
    print(f"Geography: {decision.geographic_focus}")
    print(f"\nComposite Score: {decision.composite_score:.0f}/1000 | Confidence: {decision.confidence:.0%}")
    print(f"Tier: {decision.tier} ({decision.tier_label})")
    print(f"\nTotal Insured Value: ${decision.total_insured_value:,.0f}")
    print(f"Annual Premium: ${decision.annual_premium:,.0f}")
    print(f"Rate: {decision.premium_rate:.4%}")
    print(f"Deductible: ${decision.recommended_deductible:,.0f}")
    print(f"\nDecision: {decision.decision}")
    print(f"Reasoning: {decision.reasoning}")
    
    print(f"\nCategory Scores:")
    for cat, score in decision.category_scores.items():
        print(f"  {cat}: {score:.0f}/100")
