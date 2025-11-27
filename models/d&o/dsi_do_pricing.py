"""
Digital Signal Intelligence (DSI) - Directors & Officers Insurance Pricing Model
=================================================================================

DSI-compliant D&O insurance pricing based entirely on externally observable
signals, network authority analysis, and minimal optional direct inquiry.

This model conforms to Foundational Principles.

D&O insurance is uniquely suited to DSI because corporate governance generates
extensive public footprints through SEC filings, proxy statements, court records,
and regulatory databases - all structured, authoritative, and machine-readable.

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

class CompanyType(Enum):
    """Company type classification from observable signals."""
    PUBLIC_LARGE_CAP = "public_large_cap"
    PUBLIC_MID_CAP = "public_mid_cap"
    PUBLIC_SMALL_CAP = "public_small_cap"
    PUBLIC_MICRO_CAP = "public_micro_cap"
    PRE_IPO = "pre_ipo"
    SPAC = "spac"
    PRIVATE_BACKED = "private_backed"
    PRIVATE_OTHER = "private_other"
    NONPROFIT = "nonprofit"


class IndustryClassification(Enum):
    """Industry classification from SIC/NAICS codes."""
    FINANCIAL_SERVICES = "financial_services"
    HEALTHCARE_PHARMA = "healthcare_pharma"
    TECHNOLOGY = "technology"
    ENERGY = "energy"
    RETAIL_CONSUMER = "retail_consumer"
    MANUFACTURING = "manufacturing"
    REAL_ESTATE = "real_estate"
    CRYPTO_DIGITAL = "crypto_digital"
    CANNABIS = "cannabis"
    OTHER = "other"


# =============================================================================
# SIGNAL DATA STRUCTURES
# =============================================================================

@dataclass
class NetworkAuthoritySignals:
    """Type 1: Network Authority Signals - PageRank-style relationship analysis."""
    auditor_quality_score: float = 0.0
    auditor_quality_evidence: str = ""
    legal_counsel_score: float = 0.0
    legal_counsel_evidence: str = ""
    banking_relationship_score: float = 0.0
    banking_relationship_evidence: str = ""
    investor_quality_score: float = 0.0
    investor_quality_evidence: str = ""
    board_network_score: float = 0.0
    board_network_evidence: str = ""
    index_inclusion_score: float = 0.0
    index_inclusion_evidence: str = ""
    analyst_coverage_score: float = 0.0
    analyst_coverage_evidence: str = ""
    industry_association_score: float = 0.0
    industry_association_evidence: str = ""


@dataclass
class GovernanceSignals:
    """Type 6: Public Record Signals - from SEC proxy statements."""
    board_independence_score: float = 0.0
    board_independence_evidence: str = ""
    board_diversity_score: float = 0.0
    board_diversity_evidence: str = ""
    ceo_chair_separation_score: float = 0.0
    ceo_chair_separation_evidence: str = ""
    committee_structure_score: float = 0.0
    committee_structure_evidence: str = ""
    board_refreshment_score: float = 0.0
    board_refreshment_evidence: str = ""
    related_party_score: float = 0.0
    related_party_evidence: str = ""
    compensation_structure_score: float = 0.0
    compensation_structure_evidence: str = ""
    shareholder_rights_score: float = 0.0
    shareholder_rights_evidence: str = ""


@dataclass
class FinancialSignals:
    """Type 6: Public Record Signals - from SEC filings and market data."""
    audit_opinion_score: float = 0.0
    audit_opinion_evidence: str = ""
    internal_controls_score: float = 0.0
    internal_controls_evidence: str = ""
    restatement_score: float = 0.0
    restatement_evidence: str = ""
    filing_timeliness_score: float = 0.0
    filing_timeliness_evidence: str = ""
    revenue_recognition_score: float = 0.0
    revenue_recognition_evidence: str = ""
    debt_covenant_score: float = 0.0
    debt_covenant_evidence: str = ""
    stock_volatility_score: float = 0.0
    stock_volatility_evidence: str = ""
    short_interest_score: float = 0.0
    short_interest_evidence: str = ""


@dataclass
class LitigationSignals:
    """Type 6: Public Record Signals - from PACER, SEC, SCAC."""
    securities_litigation_score: float = 0.0
    securities_litigation_evidence: str = ""
    derivative_litigation_score: float = 0.0
    derivative_litigation_evidence: str = ""
    sec_enforcement_score: float = 0.0
    sec_enforcement_evidence: str = ""
    regulatory_action_score: float = 0.0
    regulatory_action_evidence: str = ""
    pending_litigation_score: float = 0.0
    pending_litigation_evidence: str = ""
    whistleblower_score: float = 0.0
    whistleblower_evidence: str = ""


@dataclass
class ExecutiveSignals:
    """Type 5/6: Executive-related signals from filings and observable sources."""
    executive_stability_score: float = 0.0
    executive_stability_evidence: str = ""
    cfo_quality_score: float = 0.0
    cfo_quality_evidence: str = ""
    insider_trading_score: float = 0.0
    insider_trading_evidence: str = ""
    executive_background_score: float = 0.0
    executive_background_evidence: str = ""
    trading_plan_score: float = 0.0
    trading_plan_evidence: str = ""


@dataclass
class CorporateFootprintSignals:
    """Type 5: Corporate Digital Footprint Signals."""
    investor_relations_score: float = 0.0
    investor_relations_evidence: str = ""
    governance_page_score: float = 0.0
    governance_page_evidence: str = ""
    esg_reporting_score: float = 0.0
    esg_reporting_evidence: str = ""
    press_release_score: float = 0.0
    press_release_evidence: str = ""
    leadership_visibility_score: float = 0.0
    leadership_visibility_evidence: str = ""
    hiring_signals_score: float = 0.0
    hiring_signals_evidence: str = ""


@dataclass
class StructuredDataSignals:
    """Type 4: Structured Data Feed Signals - third-party ratings."""
    credit_rating_score: float = 0.0
    credit_rating_evidence: str = ""
    esg_rating_score: float = 0.0
    esg_rating_evidence: str = ""
    governance_rating_score: float = 0.0
    governance_rating_evidence: str = ""
    iss_governance_score: float = 0.0
    iss_governance_evidence: str = ""


@dataclass
class DirectInquirySignals:
    """Type 7: Direct Inquiry Signals (Optional) - maximum 5 questions."""
    pending_claims: Optional[bool] = None
    regulatory_investigation: Optional[bool] = None
    planned_transaction: Optional[bool] = None
    covenant_compliance: Optional[bool] = None
    executive_dispute: Optional[bool] = None


# =============================================================================
# COMPANY PROFILE
# =============================================================================

@dataclass
class DOCompanyProfile:
    """Company profile from observable data only."""
    company_name: str
    ticker: Optional[str]
    cik: Optional[str]
    primary_domain: str
    company_type: CompanyType
    industry: IndustryClassification
    country: str
    stock_exchange: Optional[str] = None
    market_cap: Optional[float] = None
    is_index_member: bool = False
    
    network_authority: NetworkAuthoritySignals = field(default_factory=NetworkAuthoritySignals)
    governance: GovernanceSignals = field(default_factory=GovernanceSignals)
    financial: FinancialSignals = field(default_factory=FinancialSignals)
    litigation: LitigationSignals = field(default_factory=LitigationSignals)
    executive: ExecutiveSignals = field(default_factory=ExecutiveSignals)
    corporate_footprint: CorporateFootprintSignals = field(default_factory=CorporateFootprintSignals)
    structured_data: StructuredDataSignals = field(default_factory=StructuredDataSignals)
    direct_inquiry: DirectInquirySignals = field(default_factory=DirectInquirySignals)


# =============================================================================
# SCORING ENGINE
# =============================================================================

class DODSIScorer:
    """Calculates composite scores from individual signals."""
    
    CATEGORY_WEIGHTS = {
        "network_authority": 0.10,
        "governance": 0.25,
        "financial": 0.20,
        "litigation": 0.25,
        "executive": 0.10,
        "corporate_footprint": 0.05,
        "structured_data": 0.05,
    }
    
    SIGNAL_WEIGHTS = {
        "network_authority": {
            "auditor_quality": 0.20, "legal_counsel": 0.15, "banking_relationship": 0.15,
            "investor_quality": 0.15, "board_network": 0.15, "index_inclusion": 0.05,
            "analyst_coverage": 0.10, "industry_association": 0.05,
        },
        "governance": {
            "board_independence": 0.20, "board_diversity": 0.10, "ceo_chair_separation": 0.15,
            "committee_structure": 0.15, "board_refreshment": 0.10, "related_party": 0.10,
            "compensation_structure": 0.10, "shareholder_rights": 0.10,
        },
        "financial": {
            "audit_opinion": 0.20, "internal_controls": 0.20, "restatement": 0.20,
            "filing_timeliness": 0.10, "revenue_recognition": 0.10, "debt_covenant": 0.05,
            "stock_volatility": 0.10, "short_interest": 0.05,
        },
        "litigation": {
            "securities_litigation": 0.35, "derivative_litigation": 0.15, "sec_enforcement": 0.20,
            "regulatory_action": 0.15, "pending_litigation": 0.10, "whistleblower": 0.05,
        },
        "executive": {
            "executive_stability": 0.25, "cfo_quality": 0.20, "insider_trading": 0.25,
            "executive_background": 0.15, "trading_plan": 0.15,
        },
        "corporate_footprint": {
            "investor_relations": 0.25, "governance_page": 0.20, "esg_reporting": 0.15,
            "press_release": 0.15, "leadership_visibility": 0.15, "hiring_signals": 0.10,
        },
        "structured_data": {
            "credit_rating": 0.30, "esg_rating": 0.20, "governance_rating": 0.30, "iss_governance": 0.20,
        },
    }
    
    def calculate_category_score(self, signals: object, category: str) -> Tuple[float, int, int]:
        weights = self.SIGNAL_WEIGHTS.get(category, {})
        weighted_sum, weight_sum, signals_available = 0.0, 0.0, 0
        
        for signal_name, weight in weights.items():
            score = getattr(signals, f"{signal_name}_score", 0)
            if score > 0:
                weighted_sum += score * weight
                weight_sum += weight
                signals_available += 1
        
        return (weighted_sum / weight_sum if weight_sum > 0 else 0.0, signals_available, len(weights))
    
    def calculate_composite_score(self, company: DOCompanyProfile) -> Tuple[float, float, Dict[str, float]]:
        category_signals = {
            "network_authority": company.network_authority, "governance": company.governance,
            "financial": company.financial, "litigation": company.litigation,
            "executive": company.executive, "corporate_footprint": company.corporate_footprint,
            "structured_data": company.structured_data,
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
        
        if inquiry.pending_claims is True: adjustment -= 200; notes.append("Pending securities claims: -200")
        if inquiry.regulatory_investigation is True: adjustment -= 100; notes.append("Regulatory investigation: -100")
        if inquiry.executive_dispute is True: adjustment -= 75; notes.append("Executive dispute: -75")
        if inquiry.planned_transaction is True: adjustment -= 50; notes.append("Planned transaction: -50")
        if inquiry.covenant_compliance is False: adjustment -= 100; notes.append("Covenant non-compliance: -100")
        if inquiry.pending_claims is False: adjustment += 25; notes.append("No pending claims confirmed: +25")
        
        return max(0, min(1000, score + adjustment)), notes


# =============================================================================
# TIER ASSIGNMENT
# =============================================================================

class DOTierAssignment:
    TIER_THRESHOLDS = {1: 800, 2: 650, 3: 500, 4: 350, 5: 0}
    TIER_LABELS = {1: "Preferred", 2: "Standard", 3: "Elevated", 4: "High Risk", 5: "Critical"}
    TIER_ACTIONS = {
        1: "Auto-approve at preferred pricing", 2: "Auto-approve at standard pricing",
        3: "Auto-approve with conditions", 4: "Manual review required", 5: "Decline or senior review required",
    }
    
    @classmethod
    def assign_tier(cls, score: float) -> Tuple[int, str, str]:
        for tier in range(1, 6):
            if score >= cls.TIER_THRESHOLDS[tier]:
                return tier, cls.TIER_LABELS[tier], cls.TIER_ACTIONS[tier]
        return 5, cls.TIER_LABELS[5], cls.TIER_ACTIONS[5]
    
    @classmethod
    def check_critical_overrides(cls, company: DOCompanyProfile, tier: int) -> Tuple[int, Optional[str]]:
        lit, fin = company.litigation, company.financial
        
        if lit.securities_litigation_score > 0 and lit.securities_litigation_score < 40 and tier < 4:
            return 4, "Active or recent securities litigation"
        if lit.sec_enforcement_score > 0 and lit.sec_enforcement_score < 40 and tier < 4:
            return 4, "SEC enforcement history"
        if fin.internal_controls_score > 0 and fin.internal_controls_score < 40 and tier < 3:
            return 3, "Material weakness in internal controls"
        if fin.restatement_score > 0 and fin.restatement_score < 50 and tier < 3:
            return 3, "Financial restatement history"
        if fin.audit_opinion_score > 0 and fin.audit_opinion_score < 30 and tier < 4:
            return 4, "Qualified audit opinion or going concern"
        if company.direct_inquiry.pending_claims is True and tier < 4:
            return 4, "Pending securities claims disclosed"
        if company.direct_inquiry.regulatory_investigation is True and tier < 3:
            return 3, "Regulatory investigation disclosed"
        
        return tier, None


# =============================================================================
# PRICING ENGINE
# =============================================================================

class DOPricingEngine:
    TIER_BASE_PREMIUM = {1: 4000, 2: 6000, 3: 9000, 4: 15000, 5: 25000}
    
    COMPANY_TYPE_MULTIPLIERS = {
        CompanyType.PUBLIC_LARGE_CAP: 2.50, CompanyType.PUBLIC_MID_CAP: 1.50,
        CompanyType.PUBLIC_SMALL_CAP: 1.00, CompanyType.PUBLIC_MICRO_CAP: 1.25,
        CompanyType.PRE_IPO: 2.00, CompanyType.SPAC: 3.50,
        CompanyType.PRIVATE_BACKED: 0.60, CompanyType.PRIVATE_OTHER: 0.50, CompanyType.NONPROFIT: 0.40,
    }
    
    INDUSTRY_MULTIPLIERS = {
        IndustryClassification.CRYPTO_DIGITAL: 2.50, IndustryClassification.CANNABIS: 2.00,
        IndustryClassification.HEALTHCARE_PHARMA: 1.60, IndustryClassification.FINANCIAL_SERVICES: 1.40,
        IndustryClassification.TECHNOLOGY: 1.25, IndustryClassification.ENERGY: 1.15,
        IndustryClassification.REAL_ESTATE: 1.10, IndustryClassification.RETAIL_CONSUMER: 1.00,
        IndustryClassification.MANUFACTURING: 0.90, IndustryClassification.OTHER: 1.00,
    }
    
    LIMIT_FACTORS = {
        1_000_000: 1.00, 2_000_000: 1.65, 5_000_000: 2.80, 10_000_000: 4.20,
        25_000_000: 7.50, 50_000_000: 11.00, 100_000_000: 16.00,
    }
    
    @classmethod
    def calculate_premium(cls, tier: int, company_type: CompanyType, industry: IndustryClassification, limit: float) -> Tuple[float, Dict]:
        base = cls.TIER_BASE_PREMIUM[tier]
        type_mult = cls.COMPANY_TYPE_MULTIPLIERS.get(company_type, 1.0)
        industry_mult = cls.INDUSTRY_MULTIPLIERS.get(industry, 1.0)
        limit_factor = max([f for t, f in cls.LIMIT_FACTORS.items() if limit >= t], default=1.0)
        
        premium = max(base * type_mult * industry_mult * limit_factor, 10000)
        return premium, {"base": base, "type_mult": type_mult, "industry_mult": industry_mult, "limit_factor": limit_factor}
    
    @classmethod
    def recommend_limit(cls, company_type: CompanyType, market_cap: Optional[float]) -> float:
        base_limits = {
            CompanyType.PUBLIC_LARGE_CAP: 100_000_000, CompanyType.PUBLIC_MID_CAP: 50_000_000,
            CompanyType.PUBLIC_SMALL_CAP: 25_000_000, CompanyType.PUBLIC_MICRO_CAP: 10_000_000,
            CompanyType.PRE_IPO: 25_000_000, CompanyType.SPAC: 25_000_000,
            CompanyType.PRIVATE_BACKED: 10_000_000, CompanyType.PRIVATE_OTHER: 5_000_000, CompanyType.NONPROFIT: 2_000_000,
        }
        base = base_limits.get(company_type, 10_000_000)
        if market_cap: base = min(base, market_cap * 0.015)
        
        standard = [1_000_000, 2_000_000, 5_000_000, 10_000_000, 25_000_000, 50_000_000, 100_000_000]
        return min(standard, key=lambda x: abs(x - base))
    
    @classmethod
    def recommend_retention(cls, limit: float, tier: int) -> float:
        pcts = {1: 0.01, 2: 0.015, 3: 0.02, 4: 0.03, 5: 0.05}
        retention = max(100_000, min(2_500_000, limit * pcts.get(tier, 0.02)))
        standard = [100_000, 250_000, 500_000, 1_000_000, 1_500_000, 2_500_000]
        return min(standard, key=lambda x: abs(x - retention))


# =============================================================================
# DECISION ENGINE
# =============================================================================

@dataclass
class DOUnderwritingDecision:
    company_name: str
    ticker: Optional[str]
    company_type: str
    industry: str
    composite_score: float
    confidence: float
    category_scores: Dict[str, float]
    tier: int
    tier_label: str
    tier_action: str
    tier_override_reason: Optional[str]
    recommended_limit: float
    recommended_retention: float
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


class DODecisionEngine:
    @classmethod
    def generate_conditions(cls, tier: int, company: DOCompanyProfile) -> List[str]:
        conditions = []
        if tier >= 2: conditions.append("Annual D&O questionnaire required at renewal")
        if tier >= 3: conditions.append("Quarterly financial monitoring required")
        if company.governance.board_independence_score > 0 and company.governance.board_independence_score < 60:
            conditions.append("Board independence improvement expected within 12 months")
        if company.financial.internal_controls_score > 0 and company.financial.internal_controls_score < 60:
            conditions.append("Remediation plan for internal control issues required")
        if company.direct_inquiry.planned_transaction is True:
            conditions.extend(["Transaction-specific coverage review required", "Run-off coverage to be quoted separately"])
        if tier >= 4: conditions.extend(["Senior underwriter approval required", "Claims cooperation clause enhanced"])
        conditions.append("Prompt notice of claims or circumstances required")
        return conditions
    
    @classmethod
    def generate_decision(cls, tier: int, confidence: float, score: float, company: DOCompanyProfile) -> Tuple[str, str]:
        if confidence < 0.60:
            return "REFER", f"Insufficient signal coverage (confidence: {confidence:.0%}). Manual underwriting required."
        
        if tier == 1:
            return "APPROVE", f"Excellent governance profile (score: {score:.0f}/1000). Qualifies for preferred pricing."
        elif tier == 2:
            return "APPROVE", f"Good governance profile (score: {score:.0f}/1000). Standard pricing applies."
        elif tier == 3:
            return "APPROVE_WITH_CONDITIONS", f"Moderate risk profile (score: {score:.0f}/1000). Approved with conditions."
        elif tier == 4:
            return "REFER", f"High risk profile (score: {score:.0f}/1000). Manual underwriter review required."
        else:
            return "DECLINE", f"Critical risk profile (score: {score:.0f}/1000). Risk exceeds appetite."


# =============================================================================
# MAIN PRICING MODEL
# =============================================================================

class DODSIPricingModel:
    def __init__(self):
        self.scorer = DODSIScorer()
    
    def assess(self, company: DOCompanyProfile, requested_limit: Optional[float] = None) -> DOUnderwritingDecision:
        composite, confidence, category_scores = self.scorer.calculate_composite_score(company)
        adjusted, inquiry_notes = self.scorer.apply_direct_inquiry_adjustment(composite, company.direct_inquiry)
        tier, tier_label, tier_action = DOTierAssignment.assign_tier(adjusted)
        tier, override = DOTierAssignment.check_critical_overrides(company, tier)
        if override: tier_label, tier_action = DOTierAssignment.TIER_LABELS[tier], DOTierAssignment.TIER_ACTIONS[tier]
        
        limit = requested_limit or DOPricingEngine.recommend_limit(company.company_type, company.market_cap)
        retention = DOPricingEngine.recommend_retention(limit, tier)
        premium, pricing = DOPricingEngine.calculate_premium(tier, company.company_type, company.industry, limit)
        decision, reasoning = DODecisionEngine.generate_decision(tier, confidence, adjusted, company)
        conditions = DODecisionEngine.generate_conditions(tier, company)
        
        signals_available = sum(1 for cat in [company.network_authority, company.governance, company.financial,
                                               company.litigation, company.executive, company.corporate_footprint,
                                               company.structured_data]
                                for attr in dir(cat) if attr.endswith('_score') and getattr(cat, attr, 0) > 0)
        
        return DOUnderwritingDecision(
            company_name=company.company_name, ticker=company.ticker, company_type=company.company_type.value,
            industry=company.industry.value, composite_score=adjusted, confidence=confidence,
            category_scores=category_scores, tier=tier, tier_label=tier_label, tier_action=tier_action,
            tier_override_reason=override, recommended_limit=limit, recommended_retention=retention,
            annual_premium=premium, pricing_components=pricing, decision=decision, conditions=conditions,
            reasoning=reasoning, direct_inquiry_applied=len(inquiry_notes) > 0,
            direct_inquiry_adjustments=inquiry_notes, signals_available=signals_available, signals_total=42,
            assessment_timestamp=datetime.now().isoformat(),
        )


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("DSI D&O INSURANCE PRICING MODEL v2.0")
    print("=" * 80)
    
    # Example: Well-governed large-cap
    company = DOCompanyProfile(
        company_name="TechGiant Corp", ticker="TGNT", cik="0001234567", primary_domain="techgiant.com",
        company_type=CompanyType.PUBLIC_LARGE_CAP, industry=IndustryClassification.TECHNOLOGY,
        country="US", stock_exchange="NASDAQ", market_cap=85_000_000_000, is_index_member=True,
        
        network_authority=NetworkAuthoritySignals(
            auditor_quality_score=95, legal_counsel_score=90, banking_relationship_score=92,
            investor_quality_score=88, board_network_score=85, index_inclusion_score=100,
            analyst_coverage_score=90, industry_association_score=80,
        ),
        governance=GovernanceSignals(
            board_independence_score=92, board_diversity_score=85, ceo_chair_separation_score=100,
            committee_structure_score=95, board_refreshment_score=80, related_party_score=90,
            compensation_structure_score=85, shareholder_rights_score=82,
        ),
        financial=FinancialSignals(
            audit_opinion_score=100, internal_controls_score=95, restatement_score=100,
            filing_timeliness_score=100, revenue_recognition_score=85, debt_covenant_score=95,
            stock_volatility_score=75, short_interest_score=90,
        ),
        litigation=LitigationSignals(
            securities_litigation_score=95, derivative_litigation_score=100, sec_enforcement_score=100,
            regulatory_action_score=90, pending_litigation_score=85, whistleblower_score=95,
        ),
        executive=ExecutiveSignals(
            executive_stability_score=88, cfo_quality_score=90, insider_trading_score=85,
            executive_background_score=95, trading_plan_score=90,
        ),
        corporate_footprint=CorporateFootprintSignals(
            investor_relations_score=95, governance_page_score=90, esg_reporting_score=85,
            press_release_score=80, leadership_visibility_score=88, hiring_signals_score=85,
        ),
        structured_data=StructuredDataSignals(
            credit_rating_score=90, esg_rating_score=82, governance_rating_score=88, iss_governance_score=85,
        ),
        direct_inquiry=DirectInquirySignals(pending_claims=False, regulatory_investigation=False),
    )
    
    model = DODSIPricingModel()
    decision = model.assess(company)
    
    print(f"\nCompany: {decision.company_name} ({decision.ticker})")
    print(f"Composite Score: {decision.composite_score:.0f}/1000 | Confidence: {decision.confidence:.0%}")
    print(f"Tier: {decision.tier} ({decision.tier_label})")
    print(f"Limit: ${decision.recommended_limit:,.0f} | Premium: ${decision.annual_premium:,.0f}")
    print(f"Decision: {decision.decision}")
    print(f"Reasoning: {decision.reasoning}")
