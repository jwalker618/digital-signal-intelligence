"""
Digital Signal Intelligence (DSI) - Marine Insurance Pricing Model
===================================================================

DSI-compliant marine insurance pricing based entirely on externally observable
signals, network authority analysis, and minimal optional direct inquiry.

This model conforms to Foundational Principles.

Marine insurance is uniquely suited to DSI because vessel operations generate
extensive digital footprints through AIS tracking, classification society
databases, port state control records, and regulatory filings - all publicly
accessible and machine-readable.

Key DSI Principle: We assess OPERATOR behavior patterns, not individual vessel
pricing. A well-managed operator's fleet behavior indicates individual vessel quality.

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
    MAJOR_LINER = "major_liner"              # Top 20 container lines
    MAJOR_TANKER = "major_tanker"            # Major tanker operators
    MAJOR_BULK = "major_bulk"                # Major dry bulk operators
    REGIONAL_OPERATOR = "regional_operator"  # Regional fleet operators
    INDEPENDENT = "independent"              # Single/few vessel operators
    STATE_OWNED = "state_owned"              # Government-owned fleets
    UNKNOWN = "unknown"


class VesselCategory(Enum):
    """Primary vessel category for fleet."""
    CONTAINER = "container"
    TANKER = "tanker"
    DRY_BULK = "dry_bulk"
    LNG_LPG = "lng_lpg"
    OFFSHORE = "offshore"
    PASSENGER = "passenger"
    GENERAL_CARGO = "general_cargo"
    MIXED = "mixed"


class TradingPattern(Enum):
    """Trading pattern classification from AIS analysis."""
    LINER_REGULAR = "liner_regular"          # Fixed routes, schedules
    SPOT_TRAMP = "spot_tramp"                # Voyage charter, variable routes
    INDUSTRIAL = "industrial"                 # Dedicated cargo flows
    MIXED = "mixed"


# =============================================================================
# SIGNAL DATA STRUCTURES
# =============================================================================

@dataclass
class NetworkAuthoritySignals:
    """
    Type 1: Network Authority Signals
    
    PageRank-style signals from maritime industry relationships.
    Who trusts this operator? Who do they work with?
    """
    
    # Classification society quality (IACS vs non-IACS)
    classification_society_score: float = 0.0
    classification_society_evidence: str = ""
    
    # P&I Club membership (IG clubs vs fixed premium)
    pi_club_score: float = 0.0
    pi_club_evidence: str = ""
    
    # Major charterer relationships (oil majors, commodity traders)
    charterer_quality_score: float = 0.0
    charterer_quality_evidence: str = ""
    
    # Banking/finance relationships (ship finance banks)
    banking_relationship_score: float = 0.0
    banking_relationship_evidence: str = ""
    
    # Flag state quality (Paris MoU white/grey/black list)
    flag_state_score: float = 0.0
    flag_state_evidence: str = ""
    
    # Industry association membership (BIMCO, Intertanko, etc.)
    industry_association_score: float = 0.0
    industry_association_evidence: str = ""
    
    # Technical manager quality (if third-party managed)
    technical_manager_score: float = 0.0
    technical_manager_evidence: str = ""
    
    # Port relationships (preferred ports, terminal agreements)
    port_relationship_score: float = 0.0
    port_relationship_evidence: str = ""


@dataclass
class OperationalTelemetrySignals:
    """
    Type 3: Asset Telemetry Signals
    
    From AIS tracking data - behavioral patterns at fleet level.
    We assess HOW the operator runs their fleet, not individual vessels.
    """
    
    # AIS compliance (transmission consistency across fleet)
    ais_compliance_score: float = 0.0
    ais_compliance_evidence: str = ""
    
    # Dark activity patterns (AIS gaps in suspicious locations)
    dark_activity_score: float = 0.0
    dark_activity_evidence: str = ""
    
    # Trading route risk profile (high-risk area exposure)
    route_risk_score: float = 0.0
    route_risk_evidence: str = ""
    
    # Port state control region exposure
    psc_region_exposure_score: float = 0.0
    psc_region_exposure_evidence: str = ""
    
    # Speed/fuel efficiency patterns (operational discipline)
    operational_efficiency_score: float = 0.0
    operational_efficiency_evidence: str = ""
    
    # Seasonal/weather routing (risk management behavior)
    weather_routing_score: float = 0.0
    weather_routing_evidence: str = ""


@dataclass
class SafetyComplianceSignals:
    """
    Type 6: Public Record Signals - Safety Component
    
    From port state control databases, classification societies,
    and regulatory records.
    """
    
    # Port state control performance (detention ratio)
    psc_detention_score: float = 0.0
    psc_detention_evidence: str = ""
    
    # PSC deficiency rate
    psc_deficiency_score: float = 0.0
    psc_deficiency_evidence: str = ""
    
    # Classification society status (class, conditions, recommendations)
    class_status_score: float = 0.0
    class_status_evidence: str = ""
    
    # ISM/ISPS compliance (Document of Compliance status)
    ism_compliance_score: float = 0.0
    ism_compliance_evidence: str = ""
    
    # Casualty/incident history
    casualty_history_score: float = 0.0
    casualty_history_evidence: str = ""
    
    # Total loss history
    total_loss_score: float = 0.0
    total_loss_evidence: str = ""


@dataclass
class FleetProfileSignals:
    """
    Type 6: Public Record Signals - Fleet Component
    
    From Equasis, classification society registries, and maritime databases.
    """
    
    # Fleet age profile
    fleet_age_score: float = 0.0
    fleet_age_evidence: str = ""
    
    # Fleet size and stability
    fleet_stability_score: float = 0.0
    fleet_stability_evidence: str = ""
    
    # Vessel quality indicators (class notation, equipment)
    vessel_quality_score: float = 0.0
    vessel_quality_evidence: str = ""
    
    # Crew nationality/certification patterns
    crew_certification_score: float = 0.0
    crew_certification_evidence: str = ""
    
    # Technical management consistency
    management_consistency_score: float = 0.0
    management_consistency_evidence: str = ""


@dataclass
class SanctionsComplianceSignals:
    """
    Type 6: Public Record Signals - Sanctions Component
    
    Critical for marine - sanctions violations can void coverage.
    """
    
    # Direct sanctions status
    sanctions_status_score: float = 0.0
    sanctions_status_evidence: str = ""
    
    # Beneficial ownership transparency
    ownership_transparency_score: float = 0.0
    ownership_transparency_evidence: str = ""
    
    # High-risk jurisdiction exposure
    jurisdiction_risk_score: float = 0.0
    jurisdiction_risk_evidence: str = ""
    
    # STS (ship-to-ship) transfer patterns
    sts_pattern_score: float = 0.0
    sts_pattern_evidence: str = ""
    
    # Historical sanctions connections
    historical_sanctions_score: float = 0.0
    historical_sanctions_evidence: str = ""


@dataclass
class EnvironmentalSignals:
    """
    Type 6: Public Record Signals - Environmental Component
    
    From IMO databases, classification societies, and regulatory records.
    """
    
    # IMO 2020 compliance (sulphur regulations)
    imo2020_compliance_score: float = 0.0
    imo2020_compliance_evidence: str = ""
    
    # Ballast water management compliance
    bwm_compliance_score: float = 0.0
    bwm_compliance_evidence: str = ""
    
    # CII rating (Carbon Intensity Indicator)
    cii_rating_score: float = 0.0
    cii_rating_evidence: str = ""
    
    # Environmental incidents/fines
    environmental_incident_score: float = 0.0
    environmental_incident_evidence: str = ""


@dataclass
class CorporateFootprintSignals:
    """
    Type 5: Corporate Digital Footprint Signals
    
    Observable from operator's digital presence.
    """
    
    # Website quality and transparency
    website_quality_score: float = 0.0
    website_quality_evidence: str = ""
    
    # Fleet disclosure (published fleet list)
    fleet_disclosure_score: float = 0.0
    fleet_disclosure_evidence: str = ""
    
    # Sustainability/ESG reporting
    sustainability_reporting_score: float = 0.0
    sustainability_reporting_evidence: str = ""
    
    # Safety culture communication
    safety_communication_score: float = 0.0
    safety_communication_evidence: str = ""
    
    # Crew welfare visibility
    crew_welfare_score: float = 0.0
    crew_welfare_evidence: str = ""
    
    # Industry presence (conferences, publications)
    industry_presence_score: float = 0.0
    industry_presence_evidence: str = ""


@dataclass
class StructuredDataSignals:
    """
    Type 4: Structured Data Feed Signals
    
    Third-party ratings and indices.
    """
    
    # RightShip or similar vetting scores
    vetting_score: float = 0.0
    vetting_evidence: str = ""
    
    # ESG maritime ratings
    esg_rating_score: float = 0.0
    esg_rating_evidence: str = ""
    
    # Credit rating (if rated)
    credit_rating_score: float = 0.0
    credit_rating_evidence: str = ""


@dataclass
class DirectInquirySignals:
    """
    Type 7: Direct Inquiry Signals (Optional)
    
    Maximum 5 questions for Marine.
    """
    
    fleet_size: Optional[int] = None
    # "Total number of vessels in owned/operated fleet?"
    
    psc_detentions: Optional[bool] = None
    # "Any vessels detained by port state control in past 36 months?"
    
    total_losses: Optional[bool] = None
    # "Any total losses or major casualties in past 5 years?"
    
    third_party_manager: Optional[bool] = None
    # "Is the fleet managed by a third-party technical manager?"
    
    sanctioned_trade: Optional[bool] = None
    # "Any vessels currently trading to sanctioned regions?"


# =============================================================================
# OPERATOR PROFILE
# =============================================================================

@dataclass
class MarineOperatorProfile:
    """
    Operator profile from observable data only.
    
    DSI Principle: We assess operators, not individual vessels.
    Operator behavior indicates fleet-wide risk quality.
    """
    
    # Identifiers
    operator_name: str
    imo_company_number: Optional[str]  # IMO unique company ID
    primary_domain: str
    
    # Classification (from observable signals)
    operator_type: OperatorType
    vessel_category: VesselCategory
    trading_pattern: TradingPattern
    headquarters_country: str
    
    # Observable fleet metrics
    fleet_size_observed: int = 0           # From Equasis/class records
    average_vessel_age: float = 0.0        # Calculated from registry
    primary_flag_states: List[str] = field(default_factory=list)
    
    # All signal categories
    network_authority: NetworkAuthoritySignals = field(default_factory=NetworkAuthoritySignals)
    operational_telemetry: OperationalTelemetrySignals = field(default_factory=OperationalTelemetrySignals)
    safety_compliance: SafetyComplianceSignals = field(default_factory=SafetyComplianceSignals)
    fleet_profile: FleetProfileSignals = field(default_factory=FleetProfileSignals)
    sanctions_compliance: SanctionsComplianceSignals = field(default_factory=SanctionsComplianceSignals)
    environmental: EnvironmentalSignals = field(default_factory=EnvironmentalSignals)
    corporate_footprint: CorporateFootprintSignals = field(default_factory=CorporateFootprintSignals)
    structured_data: StructuredDataSignals = field(default_factory=StructuredDataSignals)
    direct_inquiry: DirectInquirySignals = field(default_factory=DirectInquirySignals)


# =============================================================================
# SCORING ENGINE
# =============================================================================

class MarineDSIScorer:
    """
    Calculates composite scores from individual signals.
    
    Marine weight emphasizes safety compliance and operational telemetry
    as these directly predict claims.
    """
    
    CATEGORY_WEIGHTS = {
        "network_authority": 0.15,
        "operational_telemetry": 0.20,    # AIS behavior patterns
        "safety_compliance": 0.25,         # PSC, class status - critical
        "fleet_profile": 0.10,
        "sanctions_compliance": 0.15,      # Critical - can void coverage
        "environmental": 0.05,
        "corporate_footprint": 0.05,
        "structured_data": 0.05,
    }
    
    SIGNAL_WEIGHTS = {
        "network_authority": {
            "classification_society": 0.20, "pi_club": 0.15, "charterer_quality": 0.15,
            "banking_relationship": 0.10, "flag_state": 0.15, "industry_association": 0.10,
            "technical_manager": 0.10, "port_relationship": 0.05,
        },
        "operational_telemetry": {
            "ais_compliance": 0.25, "dark_activity": 0.25, "route_risk": 0.20,
            "psc_region_exposure": 0.10, "operational_efficiency": 0.10, "weather_routing": 0.10,
        },
        "safety_compliance": {
            "psc_detention": 0.25, "psc_deficiency": 0.20, "class_status": 0.20,
            "ism_compliance": 0.15, "casualty_history": 0.10, "total_loss": 0.10,
        },
        "fleet_profile": {
            "fleet_age": 0.30, "fleet_stability": 0.20, "vessel_quality": 0.20,
            "crew_certification": 0.15, "management_consistency": 0.15,
        },
        "sanctions_compliance": {
            "sanctions_status": 0.30, "ownership_transparency": 0.20, "jurisdiction_risk": 0.20,
            "sts_pattern": 0.15, "historical_sanctions": 0.15,
        },
        "environmental": {
            "imo2020_compliance": 0.30, "bwm_compliance": 0.25, "cii_rating": 0.25,
            "environmental_incident": 0.20,
        },
        "corporate_footprint": {
            "website_quality": 0.15, "fleet_disclosure": 0.20, "sustainability_reporting": 0.20,
            "safety_communication": 0.20, "crew_welfare": 0.10, "industry_presence": 0.15,
        },
        "structured_data": {
            "vetting": 0.50, "esg_rating": 0.30, "credit_rating": 0.20,
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
    
    def calculate_composite_score(self, operator: MarineOperatorProfile) -> Tuple[float, float, Dict[str, float]]:
        category_signals = {
            "network_authority": operator.network_authority,
            "operational_telemetry": operator.operational_telemetry,
            "safety_compliance": operator.safety_compliance,
            "fleet_profile": operator.fleet_profile,
            "sanctions_compliance": operator.sanctions_compliance,
            "environmental": operator.environmental,
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
        
        # Fleet size affects confidence but not score directly
        if inquiry.fleet_size is not None:
            if inquiry.fleet_size >= 20:
                notes.append(f"Large fleet ({inquiry.fleet_size} vessels): high data confidence")
            elif inquiry.fleet_size < 5:
                notes.append(f"Small fleet ({inquiry.fleet_size} vessels): limited pattern data")
        
        # Negative signals
        if inquiry.psc_detentions is True:
            adjustment -= 75
            notes.append("PSC detentions in past 36 months: -75")
        
        if inquiry.total_losses is True:
            adjustment -= 150
            notes.append("Total losses in past 5 years: -150")
        
        if inquiry.sanctioned_trade is True:
            adjustment -= 300  # Critical - may decline
            notes.append("Trading to sanctioned regions: -300")
        
        # Positive confirmation
        if inquiry.psc_detentions is False:
            adjustment += 25
            notes.append("No PSC detentions confirmed: +25")
        
        if inquiry.total_losses is False:
            adjustment += 50
            notes.append("No total losses confirmed: +50")
        
        return max(0, min(1000, score + adjustment)), notes


# =============================================================================
# TIER ASSIGNMENT
# =============================================================================

class MarineTierAssignment:
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
    def check_critical_overrides(cls, operator: MarineOperatorProfile, tier: int) -> Tuple[int, Optional[str]]:
        # Sanctions issues - critical, may force decline
        sanc = operator.sanctions_compliance
        if sanc.sanctions_status_score > 0 and sanc.sanctions_status_score < 30:
            return 5, "Sanctions exposure detected"
        
        if sanc.sts_pattern_score > 0 and sanc.sts_pattern_score < 30:
            if tier < 4:
                return 4, "Suspicious STS transfer patterns"
        
        # Dark activity - major red flag
        telem = operator.operational_telemetry
        if telem.dark_activity_score > 0 and telem.dark_activity_score < 30:
            if tier < 4:
                return 4, "Significant dark AIS activity"
        
        # PSC detention issues
        safety = operator.safety_compliance
        if safety.psc_detention_score > 0 and safety.psc_detention_score < 40:
            if tier < 3:
                return 3, "Elevated PSC detention rate"
        
        # Total loss history
        if safety.total_loss_score > 0 and safety.total_loss_score < 50:
            if tier < 4:
                return 4, "Total loss history"
        
        # Class status issues
        if safety.class_status_score > 0 and safety.class_status_score < 40:
            if tier < 4:
                return 4, "Class status concerns"
        
        # Direct inquiry overrides
        if operator.direct_inquiry.sanctioned_trade is True:
            return 5, "Trading to sanctioned regions"
        
        if operator.direct_inquiry.total_losses is True:
            if tier < 4:
                return 4, "Total losses disclosed"
        
        return tier, None


# =============================================================================
# PRICING ENGINE
# =============================================================================

class MarinePricingEngine:
    """
    Calculates premium based on tier, operator type, and vessel category.
    
    Base rates per $1M of insured value for fleet coverage.
    """
    
    TIER_BASE_RATE = {  # Per $1M insured value
        1: 0.0015,   # 0.15%
        2: 0.0022,   # 0.22%
        3: 0.0032,   # 0.32%
        4: 0.0050,   # 0.50%
        5: 0.0080,   # 0.80%
    }
    
    OPERATOR_TYPE_MULTIPLIERS = {
        OperatorType.MAJOR_LINER: 0.80,        # Lowest risk, best practices
        OperatorType.MAJOR_TANKER: 0.90,
        OperatorType.MAJOR_BULK: 0.95,
        OperatorType.REGIONAL_OPERATOR: 1.00,
        OperatorType.INDEPENDENT: 1.25,         # Less data, higher uncertainty
        OperatorType.STATE_OWNED: 1.10,
        OperatorType.UNKNOWN: 1.50,
    }
    
    VESSEL_CATEGORY_MULTIPLIERS = {
        VesselCategory.CONTAINER: 0.90,
        VesselCategory.TANKER: 1.10,           # Pollution risk
        VesselCategory.DRY_BULK: 1.00,
        VesselCategory.LNG_LPG: 0.85,          # High standards
        VesselCategory.OFFSHORE: 1.30,         # Complex operations
        VesselCategory.PASSENGER: 1.25,        # Life safety
        VesselCategory.GENERAL_CARGO: 1.10,
        VesselCategory.MIXED: 1.05,
    }
    
    TRADING_PATTERN_MULTIPLIERS = {
        TradingPattern.LINER_REGULAR: 0.85,    # Predictable, well-maintained
        TradingPattern.SPOT_TRAMP: 1.15,       # Variable, opportunistic
        TradingPattern.INDUSTRIAL: 0.90,       # Dedicated, known routes
        TradingPattern.MIXED: 1.00,
    }
    
    AGE_MULTIPLIERS = {
        (0, 5): 0.85,
        (5, 10): 0.95,
        (10, 15): 1.05,
        (15, 20): 1.20,
        (20, 25): 1.40,
        (25, 100): 1.60,
    }
    
    @classmethod
    def get_age_multiplier(cls, avg_age: float) -> float:
        for (low, high), mult in cls.AGE_MULTIPLIERS.items():
            if low <= avg_age < high:
                return mult
        return 1.60
    
    @classmethod
    def calculate_premium(
        cls,
        tier: int,
        operator_type: OperatorType,
        vessel_category: VesselCategory,
        trading_pattern: TradingPattern,
        avg_vessel_age: float,
        total_insured_value: float,
    ) -> Tuple[float, Dict]:
        
        base_rate = cls.TIER_BASE_RATE[tier]
        operator_mult = cls.OPERATOR_TYPE_MULTIPLIERS.get(operator_type, 1.0)
        category_mult = cls.VESSEL_CATEGORY_MULTIPLIERS.get(vessel_category, 1.0)
        trading_mult = cls.TRADING_PATTERN_MULTIPLIERS.get(trading_pattern, 1.0)
        age_mult = cls.get_age_multiplier(avg_vessel_age)
        
        adjusted_rate = base_rate * operator_mult * category_mult * trading_mult * age_mult
        premium = total_insured_value * adjusted_rate
        
        # Minimum premium
        minimum = 50000
        premium = max(premium, minimum)
        
        components = {
            "base_rate": base_rate,
            "operator_multiplier": operator_mult,
            "category_multiplier": category_mult,
            "trading_multiplier": trading_mult,
            "age_multiplier": age_mult,
            "adjusted_rate": adjusted_rate,
            "total_insured_value": total_insured_value,
        }
        
        return premium, components
    
    @classmethod
    def recommend_deductible(cls, tier: int, total_insured_value: float) -> float:
        """Recommend deductible as percentage of TIV."""
        deductible_pcts = {1: 0.005, 2: 0.0075, 3: 0.01, 4: 0.015, 5: 0.02}
        deductible = total_insured_value * deductible_pcts.get(tier, 0.01)
        
        # Round to standard amounts
        standard = [50_000, 100_000, 150_000, 250_000, 500_000, 1_000_000]
        return min(standard, key=lambda x: abs(x - deductible))


# =============================================================================
# DECISION ENGINE
# =============================================================================

@dataclass
class MarineUnderwritingDecision:
    """Complete underwriting decision output."""
    operator_name: str
    operator_type: str
    vessel_category: str
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


class MarineDecisionEngine:
    @classmethod
    def generate_conditions(cls, tier: int, operator: MarineOperatorProfile) -> List[str]:
        conditions = []
        
        if tier >= 2:
            conditions.append("Annual fleet list update required")
        
        if tier >= 3:
            conditions.append("PSC inspection results to be reported within 30 days")
            conditions.append("Any detention to be notified immediately")
        
        # Specific signal-driven conditions
        if operator.safety_compliance.psc_deficiency_score > 0 and operator.safety_compliance.psc_deficiency_score < 60:
            conditions.append("Quarterly PSC performance reporting required")
        
        if operator.operational_telemetry.dark_activity_score > 0 and operator.operational_telemetry.dark_activity_score < 70:
            conditions.append("Enhanced AIS monitoring required")
        
        if operator.fleet_profile.fleet_age_score > 0 and operator.fleet_profile.fleet_age_score < 50:
            conditions.append("Vessels over 20 years require individual survey")
        
        if operator.sanctions_compliance.ownership_transparency_score > 0 and operator.sanctions_compliance.ownership_transparency_score < 60:
            conditions.append("Beneficial ownership disclosure required")
        
        if tier >= 4:
            conditions.append("Senior underwriter approval required")
            conditions.append("Named vessel schedule with individual values required")
            conditions.append("Survey of any vessel over 15 years")
        
        # Always
        conditions.append("Trading warranties apply (excluding war risk areas)")
        conditions.append("Prompt notice of incidents required")
        
        return conditions
    
    @classmethod
    def generate_decision(cls, tier: int, confidence: float, score: float, operator: MarineOperatorProfile) -> Tuple[str, str]:
        if confidence < 0.60:
            return "REFER", f"Insufficient signal coverage (confidence: {confidence:.0%}). Manual underwriting required."
        
        # Check for sanctions - always decline
        if operator.direct_inquiry.sanctioned_trade is True:
            return "DECLINE", "Trading to sanctioned regions. Coverage not available."
        
        if operator.sanctions_compliance.sanctions_status_score > 0 and operator.sanctions_compliance.sanctions_status_score < 20:
            return "DECLINE", "Sanctions exposure identified. Coverage not available."
        
        if tier == 1:
            return "APPROVE", f"Excellent operator profile (score: {score:.0f}/1000). Strong safety record, clean PSC history, transparent operations. Preferred pricing."
        elif tier == 2:
            return "APPROVE", f"Good operator profile (score: {score:.0f}/1000). Acceptable safety and compliance record. Standard pricing."
        elif tier == 3:
            return "APPROVE_WITH_CONDITIONS", f"Moderate risk profile (score: {score:.0f}/1000). Some concerns require conditions."
        elif tier == 4:
            return "REFER", f"High risk profile (score: {score:.0f}/1000). Manual review required."
        else:
            return "DECLINE", f"Critical risk profile (score: {score:.0f}/1000). Risk exceeds appetite."


# =============================================================================
# MAIN PRICING MODEL
# =============================================================================

class MarineDSIPricingModel:
    """Complete DSI Marine Insurance Pricing Model."""
    
    def __init__(self):
        self.scorer = MarineDSIScorer()
    
    def assess(
        self,
        operator: MarineOperatorProfile,
        total_insured_value: float,
    ) -> MarineUnderwritingDecision:
        
        # Step 1: Calculate composite score
        composite, confidence, category_scores = self.scorer.calculate_composite_score(operator)
        
        # Step 2: Apply direct inquiry adjustments
        adjusted, inquiry_notes = self.scorer.apply_direct_inquiry_adjustment(composite, operator.direct_inquiry)
        
        # Step 3: Assign tier
        tier, tier_label, tier_action = MarineTierAssignment.assign_tier(adjusted)
        
        # Step 4: Check critical overrides
        tier, override = MarineTierAssignment.check_critical_overrides(operator, tier)
        if override:
            tier_label = MarineTierAssignment.TIER_LABELS[tier]
            tier_action = MarineTierAssignment.TIER_ACTIONS[tier]
        
        # Step 5: Calculate premium
        premium, pricing = MarinePricingEngine.calculate_premium(
            tier=tier,
            operator_type=operator.operator_type,
            vessel_category=operator.vessel_category,
            trading_pattern=operator.trading_pattern,
            avg_vessel_age=operator.average_vessel_age,
            total_insured_value=total_insured_value,
        )
        
        deductible = MarinePricingEngine.recommend_deductible(tier, total_insured_value)
        
        # Step 6: Generate decision
        decision, reasoning = MarineDecisionEngine.generate_decision(tier, confidence, adjusted, operator)
        conditions = MarineDecisionEngine.generate_conditions(tier, operator)
        
        # Signal count
        signals_available = sum(
            1 for cat in [operator.network_authority, operator.operational_telemetry,
                         operator.safety_compliance, operator.fleet_profile,
                         operator.sanctions_compliance, operator.environmental,
                         operator.corporate_footprint, operator.structured_data]
            for attr in dir(cat) if attr.endswith('_score') and getattr(cat, attr, 0) > 0
        )
        
        return MarineUnderwritingDecision(
            operator_name=operator.operator_name,
            operator_type=operator.operator_type.value,
            vessel_category=operator.vessel_category.value,
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
            signals_total=39,
            assessment_timestamp=datetime.now().isoformat(),
        )


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("DSI MARINE INSURANCE PRICING MODEL v2.0")
    print("=" * 80)
    
    # Example: Major container line with strong profile
    operator = MarineOperatorProfile(
        operator_name="Global Container Lines",
        imo_company_number="1234567",
        primary_domain="globalcontainer.com",
        operator_type=OperatorType.MAJOR_LINER,
        vessel_category=VesselCategory.CONTAINER,
        trading_pattern=TradingPattern.LINER_REGULAR,
        headquarters_country="Denmark",
        fleet_size_observed=85,
        average_vessel_age=8.5,
        primary_flag_states=["DK", "SG", "HK"],
        
        network_authority=NetworkAuthoritySignals(
            classification_society_score=95,
            pi_club_score=92,
            charterer_quality_score=88,
            banking_relationship_score=90,
            flag_state_score=95,
            industry_association_score=85,
            technical_manager_score=90,
            port_relationship_score=85,
        ),
        operational_telemetry=OperationalTelemetrySignals(
            ais_compliance_score=98,
            dark_activity_score=95,
            route_risk_score=85,
            psc_region_exposure_score=80,
            operational_efficiency_score=88,
            weather_routing_score=85,
        ),
        safety_compliance=SafetyComplianceSignals(
            psc_detention_score=95,
            psc_deficiency_score=88,
            class_status_score=98,
            ism_compliance_score=95,
            casualty_history_score=90,
            total_loss_score=100,
        ),
        fleet_profile=FleetProfileSignals(
            fleet_age_score=85,
            fleet_stability_score=90,
            vessel_quality_score=92,
            crew_certification_score=88,
            management_consistency_score=95,
        ),
        sanctions_compliance=SanctionsComplianceSignals(
            sanctions_status_score=100,
            ownership_transparency_score=95,
            jurisdiction_risk_score=90,
            sts_pattern_score=100,
            historical_sanctions_score=100,
        ),
        environmental=EnvironmentalSignals(
            imo2020_compliance_score=95,
            bwm_compliance_score=92,
            cii_rating_score=85,
            environmental_incident_score=95,
        ),
        corporate_footprint=CorporateFootprintSignals(
            website_quality_score=90,
            fleet_disclosure_score=95,
            sustainability_reporting_score=88,
            safety_communication_score=85,
            crew_welfare_score=82,
            industry_presence_score=90,
        ),
        structured_data=StructuredDataSignals(
            vetting_score=92,
            esg_rating_score=85,
            credit_rating_score=88,
        ),
        direct_inquiry=DirectInquirySignals(
            fleet_size=85,
            psc_detentions=False,
            total_losses=False,
            sanctioned_trade=False,
        ),
    )
    
    model = MarineDSIPricingModel()
    decision = model.assess(operator, total_insured_value=2_500_000_000)
    
    print(f"\nOperator: {decision.operator_name}")
    print(f"Type: {decision.operator_type} | Category: {decision.vessel_category}")
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
