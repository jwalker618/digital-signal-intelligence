"""
Digital Signal Intelligence (DSI) - Aerospace Insurance Pricing Model
======================================================================

DSI-compliant aerospace insurance pricing based entirely on externally observable
signals, network authority analysis, and minimal optional direct inquiry.

This model conforms to Foundational Principles.

Coverage Types Addressed:
- Aviation Hull & Liability (Airlines)
- Aviation Hull & Liability (General Aviation)
- Aircraft Products Liability
- Airport Liability

Author: John Walker
Version: 2.0
Date: November 2025
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class OperatorType(Enum):
    MAJOR_AIRLINE = "major_airline"
    REGIONAL_AIRLINE = "regional_airline"
    LOW_COST_CARRIER = "low_cost_carrier"
    CARGO_AIRLINE = "cargo_airline"
    CHARTER_OPERATOR = "charter_operator"
    CORPORATE_FLIGHT = "corporate_flight"
    HELICOPTER_OPERATOR = "helicopter_operator"
    FLIGHT_SCHOOL = "flight_school"
    PRIVATE_OWNER = "private_owner"


class FleetCategory(Enum):
    WIDEBODY = "widebody"
    NARROWBODY = "narrowbody"
    REGIONAL_JET = "regional_jet"
    TURBOPROP = "turboprop"
    BUSINESS_JET = "business_jet"
    HELICOPTER = "helicopter"
    PISTON = "piston"


class RegulatoryFramework(Enum):
    FAA = "faa"
    EASA = "easa"
    CAA_UK = "caa_uk"
    OTHER_ICAO = "other_icao"
    NON_ICAO = "non_icao"


class FleetSize(Enum):
    SINGLE = "single"
    MICRO = "micro"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    MAJOR = "major"


class RiskTier(Enum):
    TIER_1 = 1
    TIER_2 = 2
    TIER_3 = 3
    TIER_4 = 4
    TIER_5 = 5


class IOSAStatus(Enum):
    REGISTERED = "registered"
    EXPIRED = "expired"
    NEVER_REGISTERED = "never"
    NOT_APPLICABLE = "na"


@dataclass
class NetworkAuthoritySignals:
    alliance_membership_score: float = 0.0
    codeshare_quality_score: float = 0.0
    lessor_quality_score: float = 0.0
    oem_relationship_score: float = 0.0
    mro_quality_score: float = 0.0


@dataclass
class SafetyRecordSignals:
    accident_history_score: float = 0.0
    incident_history_score: float = 0.0
    accident_rate_score: float = 0.0
    fatality_history_score: float = 0.0
    investigation_findings_score: float = 0.0


@dataclass
class RegulatoryComplianceSignals:
    certificate_status_score: float = 0.0
    enforcement_actions_score: float = 0.0
    ad_compliance_score: float = 0.0
    iosa_status_score: float = 0.0
    ramp_inspection_score: float = 0.0
    eu_safety_list_score: float = 0.0


@dataclass
class OperationalQualitySignals:
    otp_score: float = 0.0
    dispatch_reliability_score: float = 0.0
    training_program_score: float = 0.0
    sms_maturity_score: float = 0.0
    crew_experience_score: float = 0.0


@dataclass
class FleetQualitySignals:
    fleet_age_score: float = 0.0
    fleet_homogeneity_score: float = 0.0
    aircraft_generation_score: float = 0.0
    maintenance_program_score: float = 0.0
    heavy_check_currency_score: float = 0.0


@dataclass
class FinancialStabilitySignals:
    credit_rating_score: float = 0.0
    liquidity_score: float = 0.0
    profitability_score: float = 0.0
    load_factor_score: float = 0.0
    fleet_renewal_score: float = 0.0


@dataclass
class RouteRiskSignals:
    high_risk_destination_score: float = 0.0
    challenging_airport_score: float = 0.0
    overwater_exposure_score: float = 0.0
    weather_exposure_score: float = 0.0
    conflict_zone_score: float = 0.0


@dataclass
class CorporateGovernanceSignals:
    management_stability_score: float = 0.0
    safety_culture_score: float = 0.0
    disclosure_quality_score: float = 0.0
    crisis_response_score: float = 0.0


@dataclass
class DirectInquirySignals:
    pending_claims: Optional[bool] = None
    regulatory_action: Optional[bool] = None
    coverage_declined: Optional[bool] = None
    fleet_change: Optional[bool] = None
    route_expansion: Optional[bool] = None
    ownership_change: Optional[bool] = None


OPERATOR_WEIGHTS = {
    OperatorType.MAJOR_AIRLINE: {
        'network_authority': 0.15, 'safety_record': 0.25, 'regulatory_compliance': 0.20,
        'operational_quality': 0.15, 'fleet_quality': 0.10, 'financial_stability': 0.05,
        'route_risk': 0.05, 'corporate_governance': 0.05,
    },
    OperatorType.REGIONAL_AIRLINE: {
        'network_authority': 0.10, 'safety_record': 0.25, 'regulatory_compliance': 0.20,
        'operational_quality': 0.15, 'fleet_quality': 0.15, 'financial_stability': 0.05,
        'route_risk': 0.05, 'corporate_governance': 0.05,
    },
    OperatorType.HELICOPTER_OPERATOR: {
        'network_authority': 0.05, 'safety_record': 0.30, 'regulatory_compliance': 0.25,
        'operational_quality': 0.15, 'fleet_quality': 0.10, 'financial_stability': 0.05,
        'route_risk': 0.05, 'corporate_governance': 0.05,
    },
}

DEFAULT_WEIGHTS = {
    'network_authority': 0.10, 'safety_record': 0.25, 'regulatory_compliance': 0.20,
    'operational_quality': 0.15, 'fleet_quality': 0.15, 'financial_stability': 0.05,
    'route_risk': 0.05, 'corporate_governance': 0.05,
}

REGULATORY_MODIFIERS = {
    RegulatoryFramework.FAA: 1.00, RegulatoryFramework.EASA: 1.00,
    RegulatoryFramework.CAA_UK: 1.00, RegulatoryFramework.OTHER_ICAO: 1.15,
    RegulatoryFramework.NON_ICAO: 1.40,
}

FLEET_CATEGORY_MODIFIERS = {
    FleetCategory.WIDEBODY: 1.10, FleetCategory.NARROWBODY: 1.00,
    FleetCategory.REGIONAL_JET: 1.05, FleetCategory.TURBOPROP: 0.95,
    FleetCategory.BUSINESS_JET: 1.15, FleetCategory.HELICOPTER: 1.30,
    FleetCategory.PISTON: 1.20,
}

FLEET_SIZE_MODIFIERS = {
    FleetSize.SINGLE: 1.30, FleetSize.MICRO: 1.20, FleetSize.SMALL: 1.10,
    FleetSize.MEDIUM: 1.00, FleetSize.LARGE: 0.95, FleetSize.MAJOR: 0.90,
}

IOSA_MODIFIERS = {
    IOSAStatus.REGISTERED: 0.90, IOSAStatus.EXPIRED: 1.15,
    IOSAStatus.NEVER_REGISTERED: 1.25, IOSAStatus.NOT_APPLICABLE: 1.00,
}

TIER_MODIFIERS = {
    RiskTier.TIER_1: 0.75, RiskTier.TIER_2: 1.00, RiskTier.TIER_3: 1.35,
    RiskTier.TIER_4: 1.85, RiskTier.TIER_5: 2.75,
}


@dataclass
class CategoryScore:
    category_name: str
    category_score: float
    category_weight: float
    weighted_contribution: float


@dataclass
class DSIAssessment:
    entity_name: str
    operator_type: OperatorType
    fleet_category: FleetCategory
    fleet_size: FleetSize
    regulatory_framework: RegulatoryFramework
    iosa_status: IOSAStatus
    category_scores: List[CategoryScore]
    composite_score: float
    tier: RiskTier
    confidence: float
    red_flags: List[str]
    green_flags: List[str]
    decision: str
    decision_rationale: str
    base_premium: float
    risk_adjusted_premium: float
    premium_modifier: float
    hull_value: float
    liability_limit: float
    assessment_date: datetime
    signal_coverage: float


class DSIAerospaceEngine:
    def __init__(self):
        self.operator_weights = OPERATOR_WEIGHTS
        self.default_weights = DEFAULT_WEIGHTS

    def get_weights(self, operator_type: OperatorType) -> Dict[str, float]:
        return self.operator_weights.get(operator_type, self.default_weights)

    def calculate_category_score(self, signals: List[Tuple[str, float, float]], category_name: str) -> CategoryScore:
        if not signals:
            return CategoryScore(category_name, 0.0, 0.0, 0.0)
        
        weighted_sum = sum(score * conf for _, score, conf in signals)
        total_conf = sum(conf for _, _, conf in signals)
        category_score = (weighted_sum / total_conf) if total_conf > 0 else 0.0
        
        return CategoryScore(category_name, min(100, category_score), 0.0, 0.0)

    def calculate_composite_score(self, category_scores: List[CategoryScore], weights: Dict[str, float]) -> float:
        weight_map = {
            'Network Authority': weights.get('network_authority', 0.10),
            'Safety Record': weights.get('safety_record', 0.25),
            'Regulatory Compliance': weights.get('regulatory_compliance', 0.20),
            'Operational Quality': weights.get('operational_quality', 0.15),
            'Fleet Quality': weights.get('fleet_quality', 0.15),
            'Financial Stability': weights.get('financial_stability', 0.05),
            'Route Risk': weights.get('route_risk', 0.05),
            'Corporate Governance': weights.get('corporate_governance', 0.05),
        }
        
        total_weighted = 0.0
        total_weight = 0.0
        for cat in category_scores:
            weight = weight_map.get(cat.category_name, 0.05)
            cat.category_weight = weight
            cat.weighted_contribution = cat.category_score * weight
            total_weighted += cat.weighted_contribution
            total_weight += weight
        
        return (total_weighted / total_weight) * 10 if total_weight > 0 else 0.0

    def assign_tier(self, score: float) -> RiskTier:
        if score >= 800: return RiskTier.TIER_1
        elif score >= 650: return RiskTier.TIER_2
        elif score >= 500: return RiskTier.TIER_3
        elif score >= 350: return RiskTier.TIER_4
        else: return RiskTier.TIER_5

    def identify_red_flags(self, safety: SafetyRecordSignals, regulatory: RegulatoryComplianceSignals,
                          operational: OperationalQualitySignals, financial: FinancialStabilitySignals,
                          direct: DirectInquirySignals) -> List[str]:
        flags = []
        if safety.accident_history_score > 0 and safety.accident_history_score < 50:
            flags.append("Significant accident history")
        if safety.fatality_history_score > 0 and safety.fatality_history_score < 50:
            flags.append("Fatal accident history")
        if regulatory.certificate_status_score > 0 and regulatory.certificate_status_score < 50:
            flags.append("Operating certificate concerns")
        if regulatory.eu_safety_list_score > 0 and regulatory.eu_safety_list_score < 30:
            flags.append("EU Air Safety List restrictions")
        if regulatory.iosa_status_score > 0 and regulatory.iosa_status_score < 40:
            flags.append("IOSA registration lapsed or never obtained")
        if direct.pending_claims:
            flags.append("Pending aviation liability claims")
        if direct.regulatory_action:
            flags.append("Pending regulatory enforcement action")
        if direct.coverage_declined:
            flags.append("Prior coverage declined or non-renewed")
        return flags

    def identify_green_flags(self, network: NetworkAuthoritySignals, safety: SafetyRecordSignals,
                            regulatory: RegulatoryComplianceSignals, operational: OperationalQualitySignals,
                            fleet: FleetQualitySignals) -> List[str]:
        flags = []
        if network.alliance_membership_score >= 80:
            flags.append("Major airline alliance member")
        if network.lessor_quality_score >= 85:
            flags.append("Tier 1 lessor relationships")
        if safety.accident_history_score >= 95:
            flags.append("Clean accident history")
        if regulatory.iosa_status_score >= 90:
            flags.append("Current IOSA registration")
        if regulatory.enforcement_actions_score >= 95:
            flags.append("No regulatory enforcement history")
        if operational.sms_maturity_score >= 85:
            flags.append("Mature Safety Management System")
        if fleet.fleet_age_score >= 85:
            flags.append("Young, modern fleet")
        return flags

    def determine_decision(self, tier: RiskTier, red_flags: List[str], regulatory: RegulatoryComplianceSignals) -> Tuple[str, str]:
        critical = ["EU Air Safety List", "Operating certificate", "Fatal accident", "Pending regulatory", "Prior coverage declined"]
        has_critical = any(any(c in f for c in critical) for f in red_flags)
        
        if regulatory.eu_safety_list_score > 0 and regulatory.eu_safety_list_score < 30:
            return "DECLINE", "Operator on EU Air Safety List"
        if has_critical:
            return "DECLINE", f"Critical red flag(s): {'; '.join(red_flags[:2])}"
        
        if tier == RiskTier.TIER_1:
            return "APPROVE", "Tier 1 risk - auto-approve with preferred pricing"
        elif tier == RiskTier.TIER_2:
            return "APPROVE" if len(red_flags) <= 1 else "REVIEW", "Tier 2 risk"
        elif tier == RiskTier.TIER_3:
            return "REVIEW", "Tier 3 elevated risk - requires underwriter review"
        elif tier == RiskTier.TIER_4:
            return "REVIEW", "Tier 4 high risk - requires senior review"
        else:
            return "DECLINE", "Tier 5 critical risk"

    def calculate_premium(self, operator_type: OperatorType, fleet_category: FleetCategory,
                         fleet_size: FleetSize, regulatory_framework: RegulatoryFramework,
                         iosa_status: IOSAStatus, tier: RiskTier,
                         hull_value: float, liability_limit: float) -> Tuple[float, float, float]:
        
        HULL_RATES = {
            OperatorType.MAJOR_AIRLINE: 800, OperatorType.REGIONAL_AIRLINE: 1200,
            OperatorType.LOW_COST_CARRIER: 1000, OperatorType.CARGO_AIRLINE: 1500,
            OperatorType.CHARTER_OPERATOR: 1800, OperatorType.CORPORATE_FLIGHT: 2000,
            OperatorType.HELICOPTER_OPERATOR: 4000, OperatorType.FLIGHT_SCHOOL: 3000,
            OperatorType.PRIVATE_OWNER: 2500,
        }
        LIABILITY_RATES = {
            OperatorType.MAJOR_AIRLINE: 500, OperatorType.REGIONAL_AIRLINE: 700,
            OperatorType.LOW_COST_CARRIER: 600, OperatorType.CARGO_AIRLINE: 400,
            OperatorType.CHARTER_OPERATOR: 900, OperatorType.CORPORATE_FLIGHT: 800,
            OperatorType.HELICOPTER_OPERATOR: 2000, OperatorType.FLIGHT_SCHOOL: 1500,
            OperatorType.PRIVATE_OWNER: 1000,
        }
        
        hull_rate = HULL_RATES.get(operator_type, 2000)
        liability_rate = LIABILITY_RATES.get(operator_type, 1000)
        
        hull_factor = hull_value / 1_000_000
        liability_factor = liability_limit / 1_000_000
        liability_ilf = 1.0 + (liability_factor - 1) * 0.12
        
        base_premium = (hull_rate * hull_factor) + (liability_rate * liability_ilf)
        
        fleet_mod = FLEET_CATEGORY_MODIFIERS.get(fleet_category, 1.0)
        size_mod = FLEET_SIZE_MODIFIERS.get(fleet_size, 1.0)
        reg_mod = REGULATORY_MODIFIERS.get(regulatory_framework, 1.0)
        iosa_mod = IOSA_MODIFIERS.get(iosa_status, 1.0)
        tier_mod = TIER_MODIFIERS.get(tier, 1.0)
        
        total_modifier = fleet_mod * size_mod * reg_mod * iosa_mod * tier_mod
        return base_premium, base_premium * total_modifier, total_modifier

    def assess(self, entity_name: str, operator_type: OperatorType, fleet_category: FleetCategory,
               fleet_size: FleetSize, regulatory_framework: RegulatoryFramework, iosa_status: IOSAStatus,
               network: NetworkAuthoritySignals, safety: SafetyRecordSignals,
               regulatory: RegulatoryComplianceSignals, operational: OperationalQualitySignals,
               fleet: FleetQualitySignals, financial: FinancialStabilitySignals,
               route: RouteRiskSignals, governance: CorporateGovernanceSignals,
               direct: DirectInquirySignals, hull_value: float = 50_000_000,
               liability_limit: float = 500_000_000) -> DSIAssessment:
        
        weights = self.get_weights(operator_type)
        category_scores = []
        
        # Build category scores
        net_sigs = [(n, s, 0.9) for n, s in [
            ("Alliance", network.alliance_membership_score), ("Codeshare", network.codeshare_quality_score),
            ("Lessor", network.lessor_quality_score), ("MRO", network.mro_quality_score)
        ] if s > 0]
        category_scores.append(self.calculate_category_score(net_sigs, "Network Authority"))
        
        safety_sigs = [(n, s, 1.0) for n, s in [
            ("Accidents", safety.accident_history_score), ("Incidents", safety.incident_history_score),
            ("Rate", safety.accident_rate_score), ("Fatalities", safety.fatality_history_score)
        ] if s > 0]
        category_scores.append(self.calculate_category_score(safety_sigs, "Safety Record"))
        
        reg_sigs = [(n, s, 1.0) for n, s in [
            ("Certificate", regulatory.certificate_status_score), ("Enforcement", regulatory.enforcement_actions_score),
            ("IOSA", regulatory.iosa_status_score), ("Ramp", regulatory.ramp_inspection_score),
            ("EU List", regulatory.eu_safety_list_score)
        ] if s > 0]
        category_scores.append(self.calculate_category_score(reg_sigs, "Regulatory Compliance"))
        
        ops_sigs = [(n, s, 0.9) for n, s in [
            ("OTP", operational.otp_score), ("Dispatch", operational.dispatch_reliability_score),
            ("Training", operational.training_program_score), ("SMS", operational.sms_maturity_score)
        ] if s > 0]
        category_scores.append(self.calculate_category_score(ops_sigs, "Operational Quality"))
        
        fleet_sigs = [(n, s, 0.9) for n, s in [
            ("Age", fleet.fleet_age_score), ("Homogeneity", fleet.fleet_homogeneity_score),
            ("Maintenance", fleet.maintenance_program_score)
        ] if s > 0]
        category_scores.append(self.calculate_category_score(fleet_sigs, "Fleet Quality"))
        
        fin_sigs = [(n, s, 0.8) for n, s in [
            ("Credit", financial.credit_rating_score), ("Liquidity", financial.liquidity_score),
            ("Profitability", financial.profitability_score)
        ] if s > 0]
        category_scores.append(self.calculate_category_score(fin_sigs, "Financial Stability"))
        
        route_sigs = [(n, s, 0.9) for n, s in [
            ("High Risk", route.high_risk_destination_score), ("Airports", route.challenging_airport_score),
            ("Conflict", route.conflict_zone_score)
        ] if s > 0]
        category_scores.append(self.calculate_category_score(route_sigs, "Route Risk"))
        
        gov_sigs = [(n, s, 0.8) for n, s in [
            ("Management", governance.management_stability_score), ("Safety Culture", governance.safety_culture_score)
        ] if s > 0]
        category_scores.append(self.calculate_category_score(gov_sigs, "Corporate Governance"))
        
        composite_score = self.calculate_composite_score(category_scores, weights)
        
        # Critical overrides
        if regulatory.eu_safety_list_score > 0 and regulatory.eu_safety_list_score < 30:
            composite_score = min(composite_score, 200)
        if safety.fatality_history_score > 0 and safety.fatality_history_score < 50:
            composite_score = min(composite_score, 450)
        
        tier = self.assign_tier(composite_score)
        red_flags = self.identify_red_flags(safety, regulatory, operational, financial, direct)
        green_flags = self.identify_green_flags(network, safety, regulatory, operational, fleet)
        decision, rationale = self.determine_decision(tier, red_flags, regulatory)
        
        base_premium, risk_adjusted, modifier = self.calculate_premium(
            operator_type, fleet_category, fleet_size, regulatory_framework,
            iosa_status, tier, hull_value, liability_limit
        )
        
        all_sigs = [network.alliance_membership_score, safety.accident_history_score,
                    regulatory.certificate_status_score, operational.training_program_score,
                    fleet.fleet_age_score, financial.credit_rating_score]
        signal_coverage = len([s for s in all_sigs if s > 0]) / len(all_sigs)
        
        return DSIAssessment(
            entity_name=entity_name, operator_type=operator_type, fleet_category=fleet_category,
            fleet_size=fleet_size, regulatory_framework=regulatory_framework, iosa_status=iosa_status,
            category_scores=category_scores, composite_score=composite_score, tier=tier,
            confidence=min(0.95, signal_coverage * 0.9 + 0.1), red_flags=red_flags, green_flags=green_flags,
            decision=decision, decision_rationale=rationale, base_premium=base_premium,
            risk_adjusted_premium=risk_adjusted, premium_modifier=modifier,
            hull_value=hull_value, liability_limit=liability_limit,
            assessment_date=datetime.now(), signal_coverage=signal_coverage
        )


def print_assessment(a: DSIAssessment):
    print("=" * 70)
    print("DSI AEROSPACE INSURANCE ASSESSMENT")
    print("=" * 70)
    print(f"\nEntity: {a.entity_name}")
    print(f"Operator: {a.operator_type.value} | Fleet: {a.fleet_category.value} | Size: {a.fleet_size.value}")
    print(f"Regulatory: {a.regulatory_framework.value} | IOSA: {a.iosa_status.value}")
    print(f"\n{'─' * 70}")
    print(f"COMPOSITE SCORE: {a.composite_score:.0f}/1000 | TIER: {a.tier.name} | CONFIDENCE: {a.confidence:.0%}")
    print(f"{'─' * 70}")
    print("\nCATEGORY SCORES:")
    for cat in a.category_scores:
        bar = "█" * int(cat.category_score / 5) + "░" * (20 - int(cat.category_score / 5))
        print(f"  {cat.category_name:25} {cat.category_score:5.1f}/100 {bar}")
    if a.green_flags:
        print("\n  ✓ GREEN FLAGS:", ", ".join(a.green_flags[:3]))
    if a.red_flags:
        print("  ⚠ RED FLAGS:", ", ".join(a.red_flags[:3]))
    print(f"\n{'─' * 70}")
    print(f"DECISION: {a.decision} - {a.decision_rationale}")
    print(f"\nCOVERAGE: Hull ${a.hull_value:,.0f} | Liability ${a.liability_limit:,.0f}")
    print(f"PRICING: Base ${a.base_premium:,.0f} | Modifier {a.premium_modifier:.2f}x | Final ${a.risk_adjusted_premium:,.0f}")
    print("=" * 70)


if __name__ == "__main__":
    engine = DSIAerospaceEngine()
    
    assessment = engine.assess(
        entity_name="Horizon Regional Airlines",
        operator_type=OperatorType.REGIONAL_AIRLINE,
        fleet_category=FleetCategory.REGIONAL_JET,
        fleet_size=FleetSize.MEDIUM,
        regulatory_framework=RegulatoryFramework.FAA,
        iosa_status=IOSAStatus.REGISTERED,
        network=NetworkAuthoritySignals(alliance_membership_score=0, codeshare_quality_score=75,
                                        lessor_quality_score=85, oem_relationship_score=80, mro_quality_score=78),
        safety=SafetyRecordSignals(accident_history_score=90, incident_history_score=85,
                                   accident_rate_score=88, fatality_history_score=100, investigation_findings_score=85),
        regulatory=RegulatoryComplianceSignals(certificate_status_score=95, enforcement_actions_score=90,
                                               ad_compliance_score=95, iosa_status_score=90,
                                               ramp_inspection_score=88, eu_safety_list_score=100),
        operational=OperationalQualitySignals(otp_score=82, dispatch_reliability_score=90,
                                              training_program_score=88, sms_maturity_score=85, crew_experience_score=80),
        fleet=FleetQualitySignals(fleet_age_score=82, fleet_homogeneity_score=90,
                                  aircraft_generation_score=85, maintenance_program_score=88, heavy_check_currency_score=92),
        financial=FinancialStabilitySignals(credit_rating_score=70, liquidity_score=75,
                                            profitability_score=72, load_factor_score=80, fleet_renewal_score=85),
        route=RouteRiskSignals(high_risk_destination_score=90, challenging_airport_score=85,
                               overwater_exposure_score=95, weather_exposure_score=80, conflict_zone_score=100),
        governance=CorporateGovernanceSignals(management_stability_score=85, safety_culture_score=88,
                                              disclosure_quality_score=75, crisis_response_score=80),
        direct=DirectInquirySignals(pending_claims=False, regulatory_action=False, coverage_declined=False,
                                    fleet_change=True, route_expansion=False, ownership_change=False),
        hull_value=750_000_000,
        liability_limit=1_000_000_000
    )
    
    print_assessment(assessment)
