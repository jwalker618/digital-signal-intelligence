"""
Digital Signal Intelligence (DSI) - Financial Institutions Insurance Pricing Model
==================================================================================

DSI-compliant financial institutions insurance pricing based entirely on externally
observable signals, network authority analysis, and minimal optional direct inquiry.

This model conforms to Foundational Principles.

Financial Institutions insurance is exceptionally suited to DSI because:
- Regulatory filings (Call Reports, 10-K, FFIEC) are comprehensive and structured
- Examination results and enforcement actions are public
- Credit ratings provide third-party assessment
- Digital security posture is externally testable
- Consumer complaint data is publicly available

Key DSI Principle: We assess INSTITUTIONAL behavior patterns through regulatory
compliance, examination results, and observable operational practices - not through
self-reported questionnaires about internal controls.

Coverage Types Addressed:
- Financial Institution Bond (Fidelity)
- Professional Liability (E&O)
- Directors & Officers
- Cyber Liability
- Employment Practices Liability

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

class InstitutionType(Enum):
    """Institution type from charter/registration."""
    MONEY_CENTER_BANK = "money_center_bank"
    REGIONAL_BANK = "regional_bank"
    COMMUNITY_BANK = "community_bank"
    CREDIT_UNION = "credit_union"
    SAVINGS_INSTITUTION = "savings_institution"
    BROKER_DEALER = "broker_dealer"
    INVESTMENT_ADVISER = "investment_adviser"
    INSURANCE_COMPANY = "insurance_company"
    ASSET_MANAGER = "asset_manager"
    FINTECH = "fintech"
    MORTGAGE_COMPANY = "mortgage_company"
    PAYMENT_PROCESSOR = "payment_processor"
    OTHER = "other"


class RegulatoryFramework(Enum):
    """Primary regulatory framework."""
    OCC = "occ"                    # National banks
    FDIC = "fdic"                  # State non-member banks
    FED = "fed"                    # State member banks, BHCs
    NCUA = "ncua"                  # Credit unions
    SEC = "sec"                    # Broker-dealers, advisers
    STATE = "state"               # State-regulated
    MULTI = "multi"               # Multiple regulators


class AssetSizeBand(Enum):
    """Asset size classification."""
    MEGA = "mega"                  # >$250B
    LARGE = "large"               # $50B-$250B
    MID = "mid"                   # $10B-$50B
    SMALL = "small"               # $1B-$10B
    COMMUNITY = "community"       # <$1B


# =============================================================================
# SIGNAL DATA STRUCTURES
# =============================================================================

@dataclass
class NetworkAuthoritySignals:
    """
    Type 1: Network Authority Signals
    
    Who trusts this institution? Quality of relationships.
    """
    
    # Correspondent banking relationships
    correspondent_quality_score: float = 0.0
    correspondent_quality_evidence: str = ""
    
    # Federal Home Loan Bank membership
    fhlb_membership_score: float = 0.0
    fhlb_membership_evidence: str = ""
    
    # Clearing/settlement relationships
    clearing_relationship_score: float = 0.0
    clearing_relationship_evidence: str = ""
    
    # Auditor quality (Big 4, national, regional)
    auditor_quality_score: float = 0.0
    auditor_quality_evidence: str = ""
    
    # Legal counsel quality
    legal_counsel_score: float = 0.0
    legal_counsel_evidence: str = ""
    
    # Industry association membership
    industry_association_score: float = 0.0
    industry_association_evidence: str = ""
    
    # Credit rating (if rated)
    credit_rating_score: float = 0.0
    credit_rating_evidence: str = ""


@dataclass
class RegulatoryComplianceSignals:
    """
    Type 6: Public Record Signals - Regulatory Component
    
    From FFIEC, OCC, FDIC, Fed, SEC databases.
    """
    
    # Examination ratings (CAMELS components, if discoverable)
    examination_rating_score: float = 0.0
    examination_rating_evidence: str = ""
    
    # Enforcement actions (C&D, CMPs, formal agreements)
    enforcement_action_score: float = 0.0
    enforcement_action_evidence: str = ""
    
    # MOU/informal actions (if disclosed)
    informal_action_score: float = 0.0
    informal_action_evidence: str = ""
    
    # CRA rating (Community Reinvestment Act)
    cra_rating_score: float = 0.0
    cra_rating_evidence: str = ""
    
    # BSA/AML compliance (enforcement history)
    bsa_aml_score: float = 0.0
    bsa_aml_evidence: str = ""
    
    # Fair lending compliance
    fair_lending_score: float = 0.0
    fair_lending_evidence: str = ""
    
    # Consumer compliance (UDAP/UDAAP)
    consumer_compliance_score: float = 0.0
    consumer_compliance_evidence: str = ""


@dataclass
class FinancialConditionSignals:
    """
    Type 6: Public Record Signals - Financial Component
    
    From Call Reports, 10-K, regulatory filings.
    """
    
    # Capital ratios (CET1, Tier 1, Total)
    capital_ratio_score: float = 0.0
    capital_ratio_evidence: str = ""
    
    # Asset quality (NPL ratio, charge-offs)
    asset_quality_score: float = 0.0
    asset_quality_evidence: str = ""
    
    # Liquidity position
    liquidity_score: float = 0.0
    liquidity_evidence: str = ""
    
    # Earnings stability
    earnings_score: float = 0.0
    earnings_evidence: str = ""
    
    # Loan concentration risk
    concentration_score: float = 0.0
    concentration_evidence: str = ""
    
    # Interest rate risk exposure
    interest_rate_risk_score: float = 0.0
    interest_rate_risk_evidence: str = ""
    
    # Growth rate (rapid growth = higher risk)
    growth_rate_score: float = 0.0
    growth_rate_evidence: str = ""


@dataclass
class GovernanceSignals:
    """
    Type 6: Public Record Signals - Governance Component
    
    From proxy statements, regulatory filings.
    """
    
    # Board independence
    board_independence_score: float = 0.0
    board_independence_evidence: str = ""
    
    # Board expertise (banking, risk, audit experience)
    board_expertise_score: float = 0.0
    board_expertise_evidence: str = ""
    
    # Executive stability
    executive_stability_score: float = 0.0
    executive_stability_evidence: str = ""
    
    # Risk committee presence/quality
    risk_committee_score: float = 0.0
    risk_committee_evidence: str = ""
    
    # Audit committee quality
    audit_committee_score: float = 0.0
    audit_committee_evidence: str = ""
    
    # Related party transactions
    related_party_score: float = 0.0
    related_party_evidence: str = ""


@dataclass
class OperationalRiskSignals:
    """
    Type 6: Public Record Signals - Operational Component
    Type 2: Technical Infrastructure Signals
    """
    
    # CFPB complaint volume (vs peer benchmark)
    cfpb_complaint_score: float = 0.0
    cfpb_complaint_evidence: str = ""
    
    # BBB complaint patterns
    bbb_complaint_score: float = 0.0
    bbb_complaint_evidence: str = ""
    
    # Litigation history (class actions, regulatory)
    litigation_score: float = 0.0
    litigation_evidence: str = ""
    
    # Data breach history
    breach_history_score: float = 0.0
    breach_history_evidence: str = ""
    
    # Operational incidents disclosed
    operational_incident_score: float = 0.0
    operational_incident_evidence: str = ""


@dataclass
class CyberSecuritySignals:
    """
    Type 2: Technical Infrastructure Signals
    
    Externally observable security posture.
    """
    
    # TLS/SSL configuration
    tls_score: float = 0.0
    tls_evidence: str = ""
    
    # Email authentication (SPF, DMARC, DKIM)
    email_auth_score: float = 0.0
    email_auth_evidence: str = ""
    
    # Security headers
    security_headers_score: float = 0.0
    security_headers_evidence: str = ""
    
    # Network exposure
    network_exposure_score: float = 0.0
    network_exposure_evidence: str = ""
    
    # Known vulnerabilities (CVE exposure)
    vulnerability_score: float = 0.0
    vulnerability_evidence: str = ""
    
    # Third-party security rating (if available)
    security_rating_score: float = 0.0
    security_rating_evidence: str = ""


@dataclass
class CorporateFootprintSignals:
    """
    Type 5: Corporate Digital Footprint Signals
    """
    
    # Investor relations quality
    investor_relations_score: float = 0.0
    investor_relations_evidence: str = ""
    
    # Transparency/disclosure quality
    disclosure_quality_score: float = 0.0
    disclosure_quality_evidence: str = ""
    
    # Security page presence
    security_page_score: float = 0.0
    security_page_evidence: str = ""
    
    # Career page / hiring signals
    hiring_signals_score: float = 0.0
    hiring_signals_evidence: str = ""
    
    # ESG/sustainability reporting
    esg_reporting_score: float = 0.0
    esg_reporting_evidence: str = ""
    
    # Community presence
    community_presence_score: float = 0.0
    community_presence_evidence: str = ""


@dataclass
class StructuredDataSignals:
    """
    Type 4: Structured Data Feed Signals
    """
    
    # Credit rating (Moody's, S&P, Fitch)
    credit_rating_score: float = 0.0
    credit_rating_evidence: str = ""
    
    # ESG rating
    esg_rating_score: float = 0.0
    esg_rating_evidence: str = ""
    
    # Peer benchmarking data
    peer_benchmark_score: float = 0.0
    peer_benchmark_evidence: str = ""


@dataclass
class DirectInquirySignals:
    """
    Type 7: Direct Inquiry Signals (Optional)
    
    Maximum 6 questions for Financial Institutions.
    """
    
    regulatory_action: Optional[bool] = None
    # "Any pending or recent (3 years) regulatory enforcement actions?"
    
    examination_issues: Optional[bool] = None
    # "Any MRAs/MRIAs outstanding from most recent examination?"
    
    litigation_pending: Optional[bool] = None
    # "Any material litigation pending (class action, regulatory)?"
    
    cyber_incident: Optional[bool] = None
    # "Any reportable cyber incidents in past 24 months?"
    
    significant_growth: Optional[bool] = None
    # "Asset growth >20% in past 12 months?"
    
    new_product_line: Optional[bool] = None
    # "Any significant new product lines launched in past 12 months?"


# =============================================================================
# INSTITUTION PROFILE
# =============================================================================

@dataclass
class FIProfile:
    """
    Institution profile from observable data.
    
    All fields derivable from regulatory filings and public sources.
    """
    
    # Identifiers
    institution_name: str
    charter_number: Optional[str]
    rssd_id: Optional[str]           # Fed RSSD ID
    ticker: Optional[str]
    primary_domain: str
    
    # Classification
    institution_type: InstitutionType
    regulatory_framework: RegulatoryFramework
    asset_size_band: AssetSizeBand
    headquarters_state: str
    is_publicly_traded: bool = False
    
    # Observable metrics
    total_assets: float = 0.0
    total_deposits: float = 0.0
    employee_count: int = 0
    branch_count: int = 0
    
    # All signal categories
    network_authority: NetworkAuthoritySignals = field(default_factory=NetworkAuthoritySignals)
    regulatory_compliance: RegulatoryComplianceSignals = field(default_factory=RegulatoryComplianceSignals)
    financial_condition: FinancialConditionSignals = field(default_factory=FinancialConditionSignals)
    governance: GovernanceSignals = field(default_factory=GovernanceSignals)
    operational_risk: OperationalRiskSignals = field(default_factory=OperationalRiskSignals)
    cyber_security: CyberSecuritySignals = field(default_factory=CyberSecuritySignals)
    corporate_footprint: CorporateFootprintSignals = field(default_factory=CorporateFootprintSignals)
    structured_data: StructuredDataSignals = field(default_factory=StructuredDataSignals)
    direct_inquiry: DirectInquirySignals = field(default_factory=DirectInquirySignals)


# =============================================================================
# SCORING ENGINE
# =============================================================================

class FIDSIScorer:
    """
    Calculates composite scores from individual signals.
    
    FI weight emphasizes regulatory compliance and financial condition
    as these directly predict bond losses and liability claims.
    """
    
    CATEGORY_WEIGHTS = {
        "network_authority": 0.10,
        "regulatory_compliance": 0.25,    # Critical - exam results, enforcement
        "financial_condition": 0.20,      # Critical - CAMELS proxies
        "governance": 0.15,
        "operational_risk": 0.10,
        "cyber_security": 0.10,
        "corporate_footprint": 0.05,
        "structured_data": 0.05,
    }
    
    SIGNAL_WEIGHTS = {
        "network_authority": {
            "correspondent_quality": 0.20, "fhlb_membership": 0.10, "clearing_relationship": 0.15,
            "auditor_quality": 0.20, "legal_counsel": 0.10, "industry_association": 0.10,
            "credit_rating": 0.15,
        },
        "regulatory_compliance": {
            "examination_rating": 0.20, "enforcement_action": 0.25, "informal_action": 0.10,
            "cra_rating": 0.10, "bsa_aml": 0.15, "fair_lending": 0.10, "consumer_compliance": 0.10,
        },
        "financial_condition": {
            "capital_ratio": 0.20, "asset_quality": 0.20, "liquidity": 0.15,
            "earnings": 0.15, "concentration": 0.10, "interest_rate_risk": 0.10, "growth_rate": 0.10,
        },
        "governance": {
            "board_independence": 0.20, "board_expertise": 0.20, "executive_stability": 0.15,
            "risk_committee": 0.20, "audit_committee": 0.15, "related_party": 0.10,
        },
        "operational_risk": {
            "cfpb_complaint": 0.25, "bbb_complaint": 0.10, "litigation": 0.25,
            "breach_history": 0.25, "operational_incident": 0.15,
        },
        "cyber_security": {
            "tls": 0.20, "email_auth": 0.20, "security_headers": 0.15,
            "network_exposure": 0.20, "vulnerability": 0.15, "security_rating": 0.10,
        },
        "corporate_footprint": {
            "investor_relations": 0.20, "disclosure_quality": 0.20, "security_page": 0.15,
            "hiring_signals": 0.15, "esg_reporting": 0.15, "community_presence": 0.15,
        },
        "structured_data": {
            "credit_rating": 0.40, "esg_rating": 0.30, "peer_benchmark": 0.30,
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
    
    def calculate_composite_score(self, institution: FIProfile) -> Tuple[float, float, Dict[str, float]]:
        category_signals = {
            "network_authority": institution.network_authority,
            "regulatory_compliance": institution.regulatory_compliance,
            "financial_condition": institution.financial_condition,
            "governance": institution.governance,
            "operational_risk": institution.operational_risk,
            "cyber_security": institution.cyber_security,
            "corporate_footprint": institution.corporate_footprint,
            "structured_data": institution.structured_data,
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
        if inquiry.regulatory_action is True:
            adjustment -= 150
            notes.append("Regulatory enforcement action: -150")
        
        if inquiry.examination_issues is True:
            adjustment -= 75
            notes.append("Outstanding MRAs/MRIAs: -75")
        
        if inquiry.litigation_pending is True:
            adjustment -= 100
            notes.append("Material litigation pending: -100")
        
        if inquiry.cyber_incident is True:
            adjustment -= 75
            notes.append("Recent cyber incident: -75")
        
        # Risk indicators
        if inquiry.significant_growth is True:
            adjustment -= 25
            notes.append("Rapid growth (>20%): -25")
        
        if inquiry.new_product_line is True:
            adjustment -= 15
            notes.append("New product line risk: -15")
        
        # Positive confirmations
        if inquiry.regulatory_action is False:
            adjustment += 25
            notes.append("No regulatory actions confirmed: +25")
        
        if inquiry.cyber_incident is False:
            adjustment += 20
            notes.append("No cyber incidents confirmed: +20")
        
        return max(0, min(1000, score + adjustment)), notes


# =============================================================================
# TIER ASSIGNMENT
# =============================================================================

class FITierAssignment:
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
    def check_critical_overrides(cls, institution: FIProfile, tier: int) -> Tuple[int, Optional[str]]:
        # Enforcement actions - critical
        reg = institution.regulatory_compliance
        if reg.enforcement_action_score > 0 and reg.enforcement_action_score < 40:
            if tier < 4:
                return 4, "Regulatory enforcement action"
        
        # BSA/AML issues - critical for FI
        if reg.bsa_aml_score > 0 and reg.bsa_aml_score < 40:
            if tier < 4:
                return 4, "BSA/AML compliance issues"
        
        # Capital adequacy issues
        fin = institution.financial_condition
        if fin.capital_ratio_score > 0 and fin.capital_ratio_score < 40:
            if tier < 4:
                return 4, "Capital adequacy concerns"
        
        # Asset quality issues
        if fin.asset_quality_score > 0 and fin.asset_quality_score < 40:
            if tier < 3:
                return 3, "Asset quality concerns"
        
        # Data breach history
        ops = institution.operational_risk
        if ops.breach_history_score > 0 and ops.breach_history_score < 40:
            if tier < 3:
                return 3, "Data breach history"
        
        # Significant litigation
        if ops.litigation_score > 0 and ops.litigation_score < 40:
            if tier < 4:
                return 4, "Significant litigation history"
        
        # Direct inquiry overrides
        if institution.direct_inquiry.regulatory_action is True:
            if tier < 4:
                return 4, "Regulatory action disclosed"
        
        if institution.direct_inquiry.examination_issues is True:
            if tier < 3:
                return 3, "Examination issues disclosed"
        
        return tier, None


# =============================================================================
# PRICING ENGINE
# =============================================================================

class FIPricingEngine:
    """
    Calculates premium for FI package coverage.
    
    Base premium per $1M of combined limits.
    """
    
    TIER_BASE_PREMIUM = {  # Per $1M combined limit
        1: 1500,
        2: 2200,
        3: 3200,
        4: 5000,
        5: 8000,
    }
    
    INSTITUTION_TYPE_MULTIPLIERS = {
        InstitutionType.MONEY_CENTER_BANK: 1.50,
        InstitutionType.REGIONAL_BANK: 1.20,
        InstitutionType.COMMUNITY_BANK: 1.00,
        InstitutionType.CREDIT_UNION: 0.85,
        InstitutionType.SAVINGS_INSTITUTION: 0.90,
        InstitutionType.BROKER_DEALER: 1.40,
        InstitutionType.INVESTMENT_ADVISER: 1.25,
        InstitutionType.INSURANCE_COMPANY: 1.10,
        InstitutionType.ASSET_MANAGER: 1.30,
        InstitutionType.FINTECH: 1.50,
        InstitutionType.MORTGAGE_COMPANY: 1.35,
        InstitutionType.PAYMENT_PROCESSOR: 1.40,
        InstitutionType.OTHER: 1.20,
    }
    
    ASSET_SIZE_MULTIPLIERS = {
        AssetSizeBand.MEGA: 2.50,
        AssetSizeBand.LARGE: 1.80,
        AssetSizeBand.MID: 1.30,
        AssetSizeBand.SMALL: 1.00,
        AssetSizeBand.COMMUNITY: 0.80,
    }
    
    LIMIT_FACTORS = {
        1_000_000: 1.00,
        2_000_000: 1.70,
        5_000_000: 3.00,
        10_000_000: 4.50,
        25_000_000: 8.00,
        50_000_000: 12.00,
        100_000_000: 18.00,
    }
    
    @classmethod
    def calculate_premium(
        cls,
        tier: int,
        institution_type: InstitutionType,
        asset_size: AssetSizeBand,
        combined_limit: float,
    ) -> Tuple[float, Dict]:
        
        base = cls.TIER_BASE_PREMIUM[tier]
        type_mult = cls.INSTITUTION_TYPE_MULTIPLIERS.get(institution_type, 1.0)
        size_mult = cls.ASSET_SIZE_MULTIPLIERS.get(asset_size, 1.0)
        
        # Limit factor
        limit_factor = 1.0
        for threshold, factor in sorted(cls.LIMIT_FACTORS.items()):
            if combined_limit >= threshold:
                limit_factor = factor
        
        premium = base * type_mult * size_mult * limit_factor
        
        # Minimum premium
        minimum = 25000
        premium = max(premium, minimum)
        
        components = {
            "base_premium": base,
            "type_multiplier": type_mult,
            "size_multiplier": size_mult,
            "limit_factor": limit_factor,
            "combined_limit": combined_limit,
        }
        
        return premium, components
    
    @classmethod
    def recommend_limit(cls, asset_size: AssetSizeBand, total_assets: float) -> float:
        """Recommend combined limit based on asset size."""
        # Rough guideline: limit as percentage of assets
        base_limits = {
            AssetSizeBand.MEGA: 100_000_000,
            AssetSizeBand.LARGE: 50_000_000,
            AssetSizeBand.MID: 25_000_000,
            AssetSizeBand.SMALL: 10_000_000,
            AssetSizeBand.COMMUNITY: 5_000_000,
        }
        
        base = base_limits.get(asset_size, 10_000_000)
        
        # Cap at reasonable percentage of assets
        if total_assets > 0:
            asset_based = total_assets * 0.002  # 0.2% of assets
            base = min(base, asset_based)
        
        # Round to standard
        standard = [1_000_000, 2_000_000, 5_000_000, 10_000_000, 25_000_000, 50_000_000, 100_000_000]
        return min(standard, key=lambda x: abs(x - base))
    
    @classmethod
    def recommend_deductible(cls, tier: int, combined_limit: float) -> float:
        """Recommend deductible based on limit and tier."""
        deductible_pcts = {1: 0.01, 2: 0.015, 3: 0.02, 4: 0.025, 5: 0.03}
        deductible = combined_limit * deductible_pcts.get(tier, 0.02)
        
        # Bounds
        deductible = max(25_000, min(500_000, deductible))
        
        # Round
        standard = [25_000, 50_000, 100_000, 150_000, 250_000, 500_000]
        return min(standard, key=lambda x: abs(x - deductible))


# =============================================================================
# DECISION ENGINE
# =============================================================================

@dataclass
class FIUnderwritingDecision:
    """Complete underwriting decision output."""
    institution_name: str
    institution_type: str
    asset_size_band: str
    total_assets: float
    composite_score: float
    confidence: float
    category_scores: Dict[str, float]
    tier: int
    tier_label: str
    tier_action: str
    tier_override_reason: Optional[str]
    combined_limit: float
    recommended_deductible: float
    annual_premium: float
    pricing_components: Dict[str, float]
    decision: str
    conditions: List[str]
    reasoning: str
    direct_inquiry_applied: bool
    direct_inquiry_adjustments: List[str]
    signals_available: int
    signals_total: int
    assessment_timestamp: str


class FIDecisionEngine:
    @classmethod
    def generate_conditions(cls, tier: int, institution: FIProfile) -> List[str]:
        conditions = []
        
        if tier >= 2:
            conditions.append("Annual Call Report/financial statement review required")
        
        if tier >= 3:
            conditions.append("Regulatory examination results to be provided")
            conditions.append("Quarterly CFPB complaint monitoring")
        
        # Signal-driven conditions
        reg = institution.regulatory_compliance
        if reg.bsa_aml_score > 0 and reg.bsa_aml_score < 60:
            conditions.append("BSA/AML program documentation required")
        
        if reg.consumer_compliance_score > 0 and reg.consumer_compliance_score < 60:
            conditions.append("Consumer compliance program review required")
        
        fin = institution.financial_condition
        if fin.capital_ratio_score > 0 and fin.capital_ratio_score < 60:
            conditions.append("Capital plan to be provided")
        
        if fin.asset_quality_score > 0 and fin.asset_quality_score < 60:
            conditions.append("Loan portfolio review required")
        
        cyber = institution.cyber_security
        if cyber.vulnerability_score > 0 and cyber.vulnerability_score < 60:
            conditions.append("Vulnerability remediation plan required")
        
        if tier >= 4:
            conditions.append("Senior underwriter approval required")
            conditions.append("Independent IT security assessment required")
            conditions.append("Management interview required")
        
        # Always
        conditions.append("Prompt notice of regulatory actions required")
        conditions.append("Cyber incident notification within 72 hours")
        
        return conditions
    
    @classmethod
    def generate_decision(cls, tier: int, confidence: float, score: float, institution: FIProfile) -> Tuple[str, str]:
        if confidence < 0.60:
            return "REFER", f"Insufficient signal coverage (confidence: {confidence:.0%}). Manual underwriting required."
        
        if tier == 1:
            return "APPROVE", f"Excellent institution profile (score: {score:.0f}/1000). Strong regulatory standing, solid financials, robust controls. Preferred pricing."
        elif tier == 2:
            return "APPROVE", f"Good institution profile (score: {score:.0f}/1000). Acceptable regulatory and financial condition. Standard pricing."
        elif tier == 3:
            concerns = []
            if institution.regulatory_compliance.enforcement_action_score < 70:
                concerns.append("regulatory history")
            if institution.financial_condition.asset_quality_score < 60:
                concerns.append("asset quality")
            if institution.operational_risk.cfpb_complaint_score < 60:
                concerns.append("complaint volume")
            concern_str = ", ".join(concerns) if concerns else "elevated risk indicators"
            return "APPROVE_WITH_CONDITIONS", f"Moderate risk profile (score: {score:.0f}/1000). Concerns: {concern_str}."
        elif tier == 4:
            return "REFER", f"High risk profile (score: {score:.0f}/1000). Manual review required."
        else:
            return "DECLINE", f"Critical risk profile (score: {score:.0f}/1000). Risk exceeds appetite."


# =============================================================================
# MAIN PRICING MODEL
# =============================================================================

class FIDSIPricingModel:
    """Complete DSI Financial Institutions Insurance Pricing Model."""
    
    def __init__(self):
        self.scorer = FIDSIScorer()
    
    def assess(
        self,
        institution: FIProfile,
        requested_limit: Optional[float] = None,
    ) -> FIUnderwritingDecision:
        
        # Step 1: Calculate composite score
        composite, confidence, category_scores = self.scorer.calculate_composite_score(institution)
        
        # Step 2: Apply direct inquiry adjustments
        adjusted, inquiry_notes = self.scorer.apply_direct_inquiry_adjustment(composite, institution.direct_inquiry)
        
        # Step 3: Assign tier
        tier, tier_label, tier_action = FITierAssignment.assign_tier(adjusted)
        
        # Step 4: Check critical overrides
        tier, override = FITierAssignment.check_critical_overrides(institution, tier)
        if override:
            tier_label = FITierAssignment.TIER_LABELS[tier]
            tier_action = FITierAssignment.TIER_ACTIONS[tier]
        
        # Step 5: Determine limit
        if requested_limit:
            limit = requested_limit
        else:
            limit = FIPricingEngine.recommend_limit(institution.asset_size_band, institution.total_assets)
        
        deductible = FIPricingEngine.recommend_deductible(tier, limit)
        
        # Step 6: Calculate premium
        premium, pricing = FIPricingEngine.calculate_premium(
            tier=tier,
            institution_type=institution.institution_type,
            asset_size=institution.asset_size_band,
            combined_limit=limit,
        )
        
        # Step 7: Generate decision
        decision, reasoning = FIDecisionEngine.generate_decision(tier, confidence, adjusted, institution)
        conditions = FIDecisionEngine.generate_conditions(tier, institution)
        
        # Signal count
        signals_available = sum(
            1 for cat in [institution.network_authority, institution.regulatory_compliance,
                         institution.financial_condition, institution.governance,
                         institution.operational_risk, institution.cyber_security,
                         institution.corporate_footprint, institution.structured_data]
            for attr in dir(cat) if attr.endswith('_score') and getattr(cat, attr, 0) > 0
        )
        
        return FIUnderwritingDecision(
            institution_name=institution.institution_name,
            institution_type=institution.institution_type.value,
            asset_size_band=institution.asset_size_band.value,
            total_assets=institution.total_assets,
            composite_score=adjusted,
            confidence=confidence,
            category_scores=category_scores,
            tier=tier,
            tier_label=tier_label,
            tier_action=tier_action,
            tier_override_reason=override,
            combined_limit=limit,
            recommended_deductible=deductible,
            annual_premium=premium,
            pricing_components=pricing,
            decision=decision,
            conditions=conditions,
            reasoning=reasoning,
            direct_inquiry_applied=len(inquiry_notes) > 0,
            direct_inquiry_adjustments=inquiry_notes,
            signals_available=signals_available,
            signals_total=48,
            assessment_timestamp=datetime.now().isoformat(),
        )


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("DSI FINANCIAL INSTITUTIONS INSURANCE PRICING MODEL v2.0")
    print("=" * 80)
    
    # Example: Regional bank with strong profile
    institution = FIProfile(
        institution_name="Midwest Regional Bank",
        charter_number="12345",
        rssd_id="1234567",
        ticker="MWRB",
        primary_domain="midwestregional.com",
        institution_type=InstitutionType.REGIONAL_BANK,
        regulatory_framework=RegulatoryFramework.OCC,
        asset_size_band=AssetSizeBand.MID,
        headquarters_state="OH",
        is_publicly_traded=True,
        total_assets=25_000_000_000,
        total_deposits=20_000_000_000,
        employee_count=3500,
        branch_count=180,
        
        network_authority=NetworkAuthoritySignals(
            correspondent_quality_score=88,
            fhlb_membership_score=100,
            clearing_relationship_score=85,
            auditor_quality_score=92,
            legal_counsel_score=85,
            industry_association_score=80,
            credit_rating_score=82,
        ),
        regulatory_compliance=RegulatoryComplianceSignals(
            examination_rating_score=85,
            enforcement_action_score=100,
            informal_action_score=95,
            cra_rating_score=90,
            bsa_aml_score=88,
            fair_lending_score=90,
            consumer_compliance_score=85,
        ),
        financial_condition=FinancialConditionSignals(
            capital_ratio_score=90,
            asset_quality_score=85,
            liquidity_score=88,
            earnings_score=82,
            concentration_score=78,
            interest_rate_risk_score=80,
            growth_rate_score=85,
        ),
        governance=GovernanceSignals(
            board_independence_score=88,
            board_expertise_score=85,
            executive_stability_score=90,
            risk_committee_score=85,
            audit_committee_score=90,
            related_party_score=95,
        ),
        operational_risk=OperationalRiskSignals(
            cfpb_complaint_score=82,
            bbb_complaint_score=85,
            litigation_score=90,
            breach_history_score=95,
            operational_incident_score=88,
        ),
        cyber_security=CyberSecuritySignals(
            tls_score=92,
            email_auth_score=88,
            security_headers_score=85,
            network_exposure_score=90,
            vulnerability_score=85,
            security_rating_score=82,
        ),
        corporate_footprint=CorporateFootprintSignals(
            investor_relations_score=88,
            disclosure_quality_score=85,
            security_page_score=80,
            hiring_signals_score=82,
            esg_reporting_score=78,
            community_presence_score=90,
        ),
        structured_data=StructuredDataSignals(
            credit_rating_score=82,
            esg_rating_score=78,
            peer_benchmark_score=85,
        ),
        direct_inquiry=DirectInquirySignals(
            regulatory_action=False,
            examination_issues=False,
            litigation_pending=False,
            cyber_incident=False,
        ),
    )
    
    model = FIDSIPricingModel()
    decision = model.assess(institution)
    
    print(f"\nInstitution: {decision.institution_name}")
    print(f"Type: {decision.institution_type} | Size: {decision.asset_size_band}")
    print(f"Total Assets: ${decision.total_assets:,.0f}")
    print(f"\nComposite Score: {decision.composite_score:.0f}/1000 | Confidence: {decision.confidence:.0%}")
    print(f"Tier: {decision.tier} ({decision.tier_label})")
    print(f"\nCombined Limit: ${decision.combined_limit:,.0f}")
    print(f"Annual Premium: ${decision.annual_premium:,.0f}")
    print(f"Deductible: ${decision.recommended_deductible:,.0f}")
    print(f"\nDecision: {decision.decision}")
    print(f"Reasoning: {decision.reasoning}")
    
    print(f"\nCategory Scores:")
    for cat, score in decision.category_scores.items():
        print(f"  {cat}: {score:.0f}/100")
