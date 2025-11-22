"""
Digital Signal Intelligence (DSI) Pricing Model for Financial Institutions
===========================================================================

Comprehensive insurance pricing for banks, asset managers, insurance companies,
and other financial institutions based on digital footprint and regulatory signals.

Author: John Walker
Date: November 2025
Version: 1.0
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np


class FinancialInstitutionType(Enum):
    """Types of financial institutions"""

    COMMERCIAL_BANK = "commercial_bank"
    INVESTMENT_BANK = "investment_bank"
    ASSET_MANAGER = "asset_manager"
    INSURANCE_COMPANY = "insurance_company"
    BROKER_DEALER = "broker_dealer"
    HEDGE_FUND = "hedge_fund"
    PRIVATE_EQUITY = "private_equity"
    FINTECH = "fintech"
    CREDIT_UNION = "credit_union"
    PAYMENT_PROCESSOR = "payment_processor"


class FICoverageType(Enum):
    """Financial Institution coverage types"""

    DNO = "directors_and_officers"
    EPL = "employment_practices_liability"
    FIDUCIARY = "fiduciary_liability"
    CRIME = "financial_institution_bond"
    ERRORS_OMISSIONS = "professional_liability"
    CYBER = "cyber_liability"
    REGULATORY = "regulatory_defense"


class RegulatoryJurisdiction(Enum):
    """Primary regulatory jurisdictions"""

    US_FEDERAL = "us_federal"  # SEC, FDIC, OCC, Fed
    US_STATE = "us_state"
    UK_FCA = "uk_fca"
    EU_ESMA = "eu_esma"
    SINGAPORE_MAS = "singapore_mas"
    HONG_KONG_SFC = "hong_kong_sfc"
    SWITZERLAND_FINMA = "switzerland_finma"
    MULTIPLE = "multiple_jurisdictions"


@dataclass
class FinancialInstitutionSignals:
    """Enhanced digital signals specific to financial institutions"""

    # Regulatory & Compliance Signals (0-100)
    regulatory_disclosures: float = 0.0  # SEC filings, regulatory reports
    enforcement_history: float = 0.0  # Clean record = 100
    complaint_resolution: float = 0.0  # FINRA BrokerCheck, complaints handled
    licensing_status: float = 0.0  # Current, valid licenses
    audit_transparency: float = 0.0  # Financial audit availability
    regulatory_cooperation: float = 0.0  # Cooperation indicators

    # Governance & Leadership (0-100)
    board_composition: float = 0.0  # Independent directors, expertise
    management_experience: float = 0.0  # Leadership team credentials
    compensation_disclosure: float = 0.0  # Executive comp transparency
    succession_planning: float = 0.0  # Succession plan visibility
    risk_committee: float = 0.0  # Risk committee structure
    ethics_program: float = 0.0  # Code of conduct, ethics training

    # Financial Transparency (0-100)
    financial_reporting: float = 0.0  # Timely, complete financials
    auditor_quality: float = 0.0  # Big 4 vs other
    financial_stability: float = 0.0  # Capital ratios, liquidity
    revenue_transparency: float = 0.0  # Revenue source disclosure
    risk_disclosure: float = 0.0  # Risk factor documentation
    third_party_ratings: float = 0.0  # Credit ratings, analyst coverage

    # Operational Controls (0-100)
    compliance_program: float = 0.0  # AML, KYC program indicators
    internal_controls: float = 0.0  # SOX compliance, internal audit
    vendor_management: float = 0.0  # Third-party risk management
    business_continuity: float = 0.0  # BCP/DR plan visibility
    incident_reporting: float = 0.0  # Breach notification, incident disclosure
    insurance_coverage: float = 0.0  # Existing insurance program

    # Market & Reputation (0-100)
    media_sentiment: float = 0.0  # News sentiment analysis
    client_reviews: float = 0.0  # Online reviews, testimonials
    industry_recognition: float = 0.0  # Awards, rankings
    litigation_history: float = 0.0  # Clean = 100
    regulatory_citations: float = 0.0  # Quality of regulatory mentions
    social_responsibility: float = 0.0  # ESG initiatives, community involvement

    # Technology & Security (0-100)
    cybersecurity_posture: float = 0.0  # Security certifications, controls
    technology_investment: float = 0.0  # Digital transformation signals
    data_protection: float = 0.0  # Privacy policies, data handling
    system_resilience: float = 0.0  # Uptime, redundancy
    innovation_signals: float = 0.0  # Digital products, API offerings
    regulatory_technology: float = 0.0  # RegTech adoption

    def get_category_score(self, category: str) -> float:
        """Calculate average score for a signal category"""
        if category == "regulatory":
            signals = [
                self.regulatory_disclosures,
                self.enforcement_history,
                self.complaint_resolution,
                self.licensing_status,
                self.audit_transparency,
                self.regulatory_cooperation,
            ]
        elif category == "governance":
            signals = [
                self.board_composition,
                self.management_experience,
                self.compensation_disclosure,
                self.succession_planning,
                self.risk_committee,
                self.ethics_program,
            ]
        elif category == "financial":
            signals = [
                self.financial_reporting,
                self.auditor_quality,
                self.financial_stability,
                self.revenue_transparency,
                self.risk_disclosure,
                self.third_party_ratings,
            ]
        elif category == "operational":
            signals = [
                self.compliance_program,
                self.internal_controls,
                self.vendor_management,
                self.business_continuity,
                self.incident_reporting,
                self.insurance_coverage,
            ]
        elif category == "reputation":
            signals = [
                self.media_sentiment,
                self.client_reviews,
                self.industry_recognition,
                self.litigation_history,
                self.regulatory_citations,
                self.social_responsibility,
            ]
        elif category == "technology":
            signals = [
                self.cybersecurity_posture,
                self.technology_investment,
                self.data_protection,
                self.system_resilience,
                self.innovation_signals,
                self.regulatory_technology,
            ]
        else:
            return 0.0

        return np.mean([s for s in signals if s > 0])

    def get_composite_score(self) -> float:
        """Calculate composite financial institution score (0-1000 scale)"""
        # Weighted by importance for financial institutions
        weights = {
            "regulatory": 0.25,  # Most critical for FIs
            "governance": 0.20,  # D&O focus
            "financial": 0.20,  # Financial stability
            "operational": 0.15,  # Controls and compliance
            "reputation": 0.10,  # Market perception
            "technology": 0.10,  # Modern operations
        }

        categories = [
            "regulatory",
            "governance",
            "financial",
            "operational",
            "reputation",
            "technology",
        ]
        weighted_sum = sum(self.get_category_score(cat) * weights[cat] for cat in categories)

        return weighted_sum * 10  # Convert to 0-1000 scale


@dataclass
class FinancialInstitutionProfile:
    """Profile for financial institution"""

    institution_name: str
    institution_type: FinancialInstitutionType
    primary_jurisdiction: RegulatoryJurisdiction
    additional_jurisdictions: List[RegulatoryJurisdiction] = field(default_factory=list)

    # Size & Scale
    total_assets: float = 0.0  # USD
    revenue: float = 0.0  # USD
    aum: Optional[float] = None  # Assets under management
    employees: int = 0
    years_operating: int = 0

    # Ownership & Structure
    publicly_traded: bool = False
    parent_company: Optional[str] = None
    subsidiaries: int = 0

    # Business Characteristics
    client_count: Optional[int] = None
    retail_vs_institutional: str = "mixed"  # "retail", "institutional", "mixed"
    product_complexity: str = "moderate"  # "simple", "moderate", "complex"
    international_operations: bool = False

    # Risk History
    regulatory_actions_5yr: int = 0
    material_litigation_5yr: int = 0
    largest_settlement: float = 0.0
    data_breaches_5yr: int = 0
    customer_complaints_annual: int = 0

    # Financial Metrics
    capital_ratio: Optional[float] = None  # Tier 1 capital ratio for banks
    return_on_equity: Optional[float] = None
    loss_ratio: Optional[float] = None  # For insurance companies

    # Insurance Program
    current_limits: Dict[str, float] = field(default_factory=dict)
    claims_5yr: int = 0
    largest_claim: float = 0.0

    # Digital signals
    signals: FinancialInstitutionSignals = field(default_factory=FinancialInstitutionSignals)


@dataclass
class FIPricingResult:
    """Output of financial institution pricing"""

    institution_name: str
    institution_type: str
    coverage_type: str

    # Pricing components
    base_rate: float
    regulatory_modifier: float
    governance_modifier: float
    size_modifier: float
    complexity_modifier: float
    history_modifier: float
    jurisdiction_modifier: float

    # Policy structure
    recommended_limit: float
    deductible: float
    retention: float

    # Final pricing
    technical_rate: float
    annual_premium: float
    premium_per_million_revenue: float

    # Risk assessment
    composite_score: float
    regulatory_score: float
    governance_score: float
    risk_tier: str
    regulatory_action_probability: float
    confidence_level: float

    # Underwriting
    recommendation: str
    reasoning: str
    conditions: List[str] = field(default_factory=list)
    coverage_restrictions: List[str] = field(default_factory=list)


class FinancialInstitutionPricingModel:
    """
    Comprehensive pricing model for financial institutions
    """

    def __init__(self, coverage_type: FICoverageType):
        self.coverage_type = coverage_type
        self.base_rates = self._initialize_base_rates()
        self.institution_multipliers = self._initialize_institution_multipliers()
        self.jurisdiction_multipliers = self._initialize_jurisdiction_multipliers()

    def _initialize_base_rates(self) -> Dict[str, Dict[str, float]]:
        """
        Initialize base rates per $1M revenue by institution type and coverage
        Rates in USD per $1M revenue
        """
        return {
            "directors_and_officers": {
                "commercial_bank": 3200.0,
                "investment_bank": 4500.0,
                "asset_manager": 3800.0,
                "insurance_company": 3400.0,
                "broker_dealer": 4200.0,
                "hedge_fund": 5000.0,
                "private_equity": 4800.0,
                "fintech": 3600.0,
                "credit_union": 2400.0,
                "payment_processor": 3500.0,
            },
            "employment_practices_liability": {
                "commercial_bank": 1200.0,
                "investment_bank": 1800.0,
                "asset_manager": 1500.0,
                "insurance_company": 1300.0,
                "broker_dealer": 1600.0,
                "hedge_fund": 2000.0,
                "private_equity": 1900.0,
                "fintech": 1400.0,
                "credit_union": 950.0,
                "payment_processor": 1300.0,
            },
            "fiduciary_liability": {
                "commercial_bank": 2800.0,
                "investment_bank": 3500.0,
                "asset_manager": 4200.0,
                "insurance_company": 2600.0,
                "broker_dealer": 3800.0,
                "hedge_fund": 4500.0,
                "private_equity": 4000.0,
                "fintech": 2200.0,
                "credit_union": 1800.0,
                "payment_processor": 1500.0,
            },
            "financial_institution_bond": {
                "commercial_bank": 850.0,
                "investment_bank": 1200.0,
                "asset_manager": 950.0,
                "insurance_company": 800.0,
                "broker_dealer": 1100.0,
                "hedge_fund": 1300.0,
                "private_equity": 1150.0,
                "fintech": 1000.0,
                "credit_union": 650.0,
                "payment_processor": 1400.0,
            },
            "professional_liability": {
                "commercial_bank": 1800.0,
                "investment_bank": 2800.0,
                "asset_manager": 2400.0,
                "insurance_company": 2000.0,
                "broker_dealer": 2600.0,
                "hedge_fund": 3000.0,
                "private_equity": 2700.0,
                "fintech": 2200.0,
                "credit_union": 1400.0,
                "payment_processor": 2100.0,
            },
            "cyber_liability": {
                "commercial_bank": 2200.0,
                "investment_bank": 2600.0,
                "asset_manager": 2000.0,
                "insurance_company": 1900.0,
                "broker_dealer": 2400.0,
                "hedge_fund": 2100.0,
                "private_equity": 1800.0,
                "fintech": 2800.0,
                "credit_union": 1700.0,
                "payment_processor": 3200.0,
            },
            "regulatory_defense": {
                "commercial_bank": 1500.0,
                "investment_bank": 2200.0,
                "asset_manager": 1800.0,
                "insurance_company": 1600.0,
                "broker_dealer": 2000.0,
                "hedge_fund": 2400.0,
                "private_equity": 2100.0,
                "fintech": 1700.0,
                "credit_union": 1100.0,
                "payment_processor": 1600.0,
            },
        }

    def _initialize_institution_multipliers(self) -> Dict[FinancialInstitutionType, float]:
        """Risk multipliers by institution type"""
        return {
            FinancialInstitutionType.HEDGE_FUND: 1.45,
            FinancialInstitutionType.INVESTMENT_BANK: 1.40,
            FinancialInstitutionType.PRIVATE_EQUITY: 1.35,
            FinancialInstitutionType.BROKER_DEALER: 1.30,
            FinancialInstitutionType.ASSET_MANAGER: 1.20,
            FinancialInstitutionType.FINTECH: 1.15,
            FinancialInstitutionType.INSURANCE_COMPANY: 1.10,
            FinancialInstitutionType.COMMERCIAL_BANK: 1.05,
            FinancialInstitutionType.PAYMENT_PROCESSOR: 1.10,
            FinancialInstitutionType.CREDIT_UNION: 0.85,
        }

    def _initialize_jurisdiction_multipliers(self) -> Dict[RegulatoryJurisdiction, float]:
        """Regulatory jurisdiction risk multipliers"""
        return {
            RegulatoryJurisdiction.US_FEDERAL: 1.25,  # SEC, stringent enforcement
            RegulatoryJurisdiction.UK_FCA: 1.20,
            RegulatoryJurisdiction.EU_ESMA: 1.15,
            RegulatoryJurisdiction.MULTIPLE: 1.40,  # Cross-border complexity
            RegulatoryJurisdiction.SINGAPORE_MAS: 1.05,
            RegulatoryJurisdiction.HONG_KONG_SFC: 1.10,
            RegulatoryJurisdiction.SWITZERLAND_FINMA: 1.08,
            RegulatoryJurisdiction.US_STATE: 1.00,
        }

    def calculate_regulatory_modifier(
        self, signals: FinancialInstitutionSignals, institution: FinancialInstitutionProfile
    ) -> Tuple[float, float]:
        """
        Calculate modifier based on regulatory compliance and history
        CRITICAL for financial institutions
        """
        reg_score = signals.get_category_score("regulatory")

        # Base modifier from regulatory score
        if reg_score >= 90:
            base_mod = 0.70
        elif reg_score >= 80:
            base_mod = 0.80
        elif reg_score >= 70:
            base_mod = 0.95
        elif reg_score >= 60:
            base_mod = 1.15
        elif reg_score >= 50:
            base_mod = 1.40
        else:
            base_mod = 1.80  # Poor regulatory standing

        # Adjust for enforcement history
        if institution.regulatory_actions_5yr == 0:
            enforcement_mod = 0.95
        elif institution.regulatory_actions_5yr == 1:
            enforcement_mod = 1.20
        elif institution.regulatory_actions_5yr == 2:
            enforcement_mod = 1.50
        else:
            enforcement_mod = 2.00  # Multiple actions = major red flag

        # Material settlements
        if institution.largest_settlement > 50_000_000:
            settlement_mod = 1.50
        elif institution.largest_settlement > 10_000_000:
            settlement_mod = 1.25
        elif institution.largest_settlement > 1_000_000:
            settlement_mod = 1.10
        else:
            settlement_mod = 1.00

        final_mod = base_mod * enforcement_mod * settlement_mod

        return final_mod, reg_score

    def calculate_governance_modifier(
        self, signals: FinancialInstitutionSignals
    ) -> Tuple[float, float]:
        """Calculate modifier based on corporate governance"""
        gov_score = signals.get_category_score("governance")

        # Governance critical for D&O and fiduciary
        if self.coverage_type in [FICoverageType.DNO, FICoverageType.FIDUCIARY]:
            weight = 1.30
        else:
            weight = 1.15

        if gov_score >= 85:
            modifier = 0.75 * weight
        elif gov_score >= 75:
            modifier = 0.88 * weight
        elif gov_score >= 65:
            modifier = 1.00 * weight
        elif gov_score >= 55:
            modifier = 1.20 * weight
        else:
            modifier = 1.50 * weight

        return modifier, gov_score

    def calculate_size_modifier(self, institution: FinancialInstitutionProfile) -> float:
        """Calculate size-based modifier"""
        revenue_mm = institution.revenue / 1_000_000

        # Larger institutions get better rates (economies of scale in controls)
        if revenue_mm < 50:
            return 1.35
        elif revenue_mm < 250:
            return 1.20
        elif revenue_mm < 1000:
            return 1.05
        elif revenue_mm < 5000:
            return 0.95
        elif revenue_mm < 25000:
            return 0.88
        else:
            return 0.82  # Mega institutions

    def calculate_complexity_modifier(self, institution: FinancialInstitutionProfile) -> float:
        """Calculate modifier based on business complexity"""
        complexity_score = 1.0

        # Product complexity
        if institution.product_complexity == "complex":
            complexity_score *= 1.30
        elif institution.product_complexity == "moderate":
            complexity_score *= 1.10

        # International operations
        if institution.international_operations:
            complexity_score *= 1.20

        # Multiple jurisdictions
        if len(institution.additional_jurisdictions) >= 3:
            complexity_score *= 1.25
        elif len(institution.additional_jurisdictions) >= 1:
            complexity_score *= 1.12

        # Subsidiary complexity
        if institution.subsidiaries >= 20:
            complexity_score *= 1.18
        elif institution.subsidiaries >= 10:
            complexity_score *= 1.10
        elif institution.subsidiaries >= 5:
            complexity_score *= 1.05

        return complexity_score

    def calculate_history_modifier(self, institution: FinancialInstitutionProfile) -> float:
        """Calculate modifier based on loss and litigation history"""
        modifier = 1.0

        # Material litigation
        if institution.material_litigation_5yr == 0:
            modifier *= 0.92
        elif institution.material_litigation_5yr <= 2:
            modifier *= 1.15
        elif institution.material_litigation_5yr <= 5:
            modifier *= 1.40
        else:
            modifier *= 1.75

        # Insurance claims
        if institution.claims_5yr == 0:
            modifier *= 0.90
        elif institution.claims_5yr <= 2:
            modifier *= 1.20
        else:
            modifier *= 1.55

        # Customer complaints (for retail institutions)
        if institution.customer_complaints_annual > 0:
            if institution.client_count:
                complaint_rate = institution.customer_complaints_annual / institution.client_count
                if complaint_rate > 0.05:  # >5% complaint rate
                    modifier *= 1.35
                elif complaint_rate > 0.02:
                    modifier *= 1.18

        return modifier

    def calculate_financial_stability_modifier(
        self, signals: FinancialInstitutionSignals, institution: FinancialInstitutionProfile
    ) -> float:
        """Calculate modifier based on financial strength"""
        fin_score = signals.get_category_score("financial")

        base_mod = 1.0
        if fin_score >= 85:
            base_mod = 0.90
        elif fin_score >= 75:
            base_mod = 0.95
        elif fin_score >= 65:
            base_mod = 1.00
        elif fin_score >= 55:
            base_mod = 1.12
        else:
            base_mod = 1.30

        # Adjust for specific metrics if available
        if institution.capital_ratio is not None:
            if institution.capital_ratio >= 15.0:  # Well-capitalized
                base_mod *= 0.92
            elif institution.capital_ratio < 8.0:  # Undercapitalized
                base_mod *= 1.25

        if institution.return_on_equity is not None:
            if institution.return_on_equity < 0:  # Unprofitable
                base_mod *= 1.40

        return base_mod

    def estimate_regulatory_action_probability(
        self, composite_score: float, reg_score: float, prior_actions: int
    ) -> float:
        """Estimate probability of regulatory action in next 5 years"""
        # Base probability from scores
        if reg_score >= 85 and composite_score >= 750:
            base_prob = 0.05
        elif reg_score >= 75 and composite_score >= 700:
            base_prob = 0.12
        elif reg_score >= 65 and composite_score >= 650:
            base_prob = 0.25
        elif reg_score >= 55 and composite_score >= 600:
            base_prob = 0.40
        else:
            base_prob = 0.60

        # Prior actions are highly predictive
        if prior_actions > 0:
            base_prob *= 1 + prior_actions * 0.50

        return min(base_prob, 0.85)

    def recommend_policy_structure(
        self, institution: FinancialInstitutionProfile, coverage_type: FICoverageType
    ) -> Tuple[float, float, float]:
        """
        Recommend limit, deductible, and retention
        Returns: (limit, deductible, retention)
        """
        revenue_mm = institution.revenue / 1_000_000
        assets_mm = (
            institution.total_assets / 1_000_000
            if institution.total_assets > 0
            else revenue_mm * 10
        )

        # D&O limits typically 1-3% of revenue or market cap proxy
        if coverage_type == FICoverageType.DNO:
            base_limit = min(revenue_mm * 0.02 * 1_000_000, 250_000_000)
        elif coverage_type == FICoverageType.FIDUCIARY:
            base_limit = min(assets_mm * 0.01 * 1_000_000, 100_000_000)
        elif coverage_type == FICoverageType.CRIME:
            base_limit = min(assets_mm * 0.005 * 1_000_000, 50_000_000)
        else:
            base_limit = min(revenue_mm * 0.015 * 1_000_000, 100_000_000)

        # Round to standard limits
        standard_limits = [
            1_000_000,
            2_000_000,
            5_000_000,
            10_000_000,
            25_000_000,
            50_000_000,
            75_000_000,
            100_000_000,
            150_000_000,
            200_000_000,
            250_000_000,
            500_000_000,
        ]
        limit = min(standard_limits, key=lambda x: abs(x - base_limit))

        # Deductible: 1-2.5% of limit
        deductible = max(limit * 0.015, 25_000)

        # Retention for excess layers
        retention = max(limit * 0.10, 500_000)

        return limit, deductible, retention

    def determine_risk_tier(
        self, composite_score: float, reg_score: float, gov_score: float
    ) -> str:
        """Determine risk tier with emphasis on regulatory and governance"""
        # Regulatory score can override
        if reg_score < 50:
            return "Tier 5 - Critical Regulatory Risk"
        elif gov_score < 50 and self.coverage_type == FICoverageType.DNO:
            return "Tier 5 - Critical Governance Risk"
        elif composite_score >= 800 and reg_score >= 85 and gov_score >= 80:
            return "Tier 1 - Preferred"
        elif composite_score >= 700 and reg_score >= 75 and gov_score >= 70:
            return "Tier 2 - Standard"
        elif composite_score >= 650 and reg_score >= 65:
            return "Tier 3 - Elevated"
        elif composite_score >= 600 and reg_score >= 55:
            return "Tier 4 - High Risk"
        else:
            return "Tier 5 - Critical Risk"

    def calculate_confidence(self, signals: FinancialInstitutionSignals) -> float:
        """Calculate confidence in pricing"""
        all_signals = [
            signals.regulatory_disclosures,
            signals.enforcement_history,
            signals.complaint_resolution,
            signals.licensing_status,
            signals.audit_transparency,
            signals.regulatory_cooperation,
            signals.board_composition,
            signals.management_experience,
            signals.compensation_disclosure,
            signals.succession_planning,
            signals.risk_committee,
            signals.ethics_program,
            signals.financial_reporting,
            signals.auditor_quality,
            signals.financial_stability,
            signals.revenue_transparency,
            signals.risk_disclosure,
            signals.third_party_ratings,
            signals.compliance_program,
            signals.internal_controls,
            signals.vendor_management,
            signals.business_continuity,
            signals.incident_reporting,
            signals.insurance_coverage,
            signals.media_sentiment,
            signals.client_reviews,
            signals.industry_recognition,
            signals.litigation_history,
            signals.regulatory_citations,
            signals.social_responsibility,
            signals.cybersecurity_posture,
            signals.technology_investment,
            signals.data_protection,
            signals.system_resilience,
            signals.innovation_signals,
            signals.regulatory_technology,
        ]

        non_zero = sum(1 for s in all_signals if s > 0)
        coverage = non_zero / len(all_signals)

        # Financial institutions require high data coverage
        if coverage >= 0.80:
            return 0.95
        elif coverage >= 0.65:
            return 0.87
        elif coverage >= 0.50:
            return 0.75
        elif coverage >= 0.35:
            return 0.60
        else:
            return 0.45

    def generate_recommendation(
        self,
        composite_score: float,
        reg_score: float,
        gov_score: float,
        confidence: float,
        institution: FinancialInstitutionProfile,
    ) -> Tuple[str, str, List[str], List[str]]:
        """
        Generate recommendation, reasoning, conditions, and restrictions
        """
        conditions = []
        restrictions = []

        # Critical regulatory issues = decline
        if reg_score < 50 or institution.regulatory_actions_5yr >= 3:
            rec = "Decline - Critical Regulatory Risk"
            reason = f"Severe regulatory issues (score: {reg_score:.0f}, {institution.regulatory_actions_5yr} actions in 5 years). Pattern indicates systemic compliance failures. Requires 24+ months clean record."
            return rec, reason, conditions, restrictions

        # Multiple material settlements
        if institution.largest_settlement > 100_000_000:
            restrictions.append("Prior acts exclusion for settlements >$100M")
            restrictions.append("Aggregate limit reduced by 30%")

        # Strong profile
        if composite_score >= 800 and reg_score >= 85 and gov_score >= 80 and confidence >= 0.85:
            rec = "Auto-Approve - Preferred Pricing"
            reason = f"Exceptional regulatory compliance (score: {reg_score:.0f}) and governance (score: {gov_score:.0f}). Clean enforcement history. Best-in-class controls."
            conditions = [
                "Annual D&O questionnaire",
                "Maintain current insurance limits",
                "30-day notice of material changes",
            ]

        elif composite_score >= 700 and reg_score >= 75 and gov_score >= 70 and confidence >= 0.80:
            rec = "Auto-Approve - Standard Pricing"
            reason = f"Good regulatory standing (score: {reg_score:.0f}) and governance (score: {gov_score:.0f}). Acceptable risk profile with adequate controls."
            conditions = [
                "Annual D&O questionnaire",
                "Quarterly regulatory action disclosure",
                "Material litigation notice within 10 days",
                "Independent director ratio maintained at current level",
            ]

        elif composite_score >= 650 and reg_score >= 65 and confidence >= 0.70:
            rec = "Manual Review - Elevated Risk"
            reason = f"Moderate regulatory profile (score: {reg_score:.0f}). Some concerns requiring underwriter assessment. Regulatory action probability: elevated."
            conditions = [
                "Detailed D&O application required",
                "Recent regulatory examination reports",
                "Board meeting minutes (past 12 months)",
                "Compliance program documentation",
                "Prior litigation history (5 years)",
                "Higher deductible required",
            ]
            if institution.regulatory_actions_5yr > 0:
                restrictions.append(
                    f"Prior acts exclusion for matters related to {institution.regulatory_actions_5yr} prior regulatory action(s)"
                )

        elif confidence < 0.65:
            rec = "Manual Review - Insufficient Data"
            reason = f"Limited transparency (confidence: {confidence:.0%}). Insufficient public information for automated decisioning. Requires full traditional underwriting."
            conditions = [
                "Complete financial institution application",
                "Audited financials (3 years)",
                "Regulatory reports and examinations",
                "Complete litigation and claim history",
                "Management biographies and credentials",
                "Description of compliance and risk management programs",
            ]

        else:
            rec = "Manual Review - High Risk"
            reason = f"Elevated risk profile (composite: {composite_score:.0f}, regulatory: {reg_score:.0f}). Significant concerns requiring senior underwriter review and potential coverage modifications."
            conditions = [
                "Senior underwriter approval required",
                "Detailed regulatory history and current status",
                "Remediation plan for identified deficiencies",
                "Enhanced monitoring with quarterly updates",
                "Higher retention and co-insurance",
                "Independent compliance assessment within 6 months",
            ]
            restrictions.extend(
                [
                    "Sub-limits on regulatory defense costs",
                    "Conduct exclusion for known matters",
                    "Reduced limits for subsidiary operations",
                    "Prior acts limitation to 3 years",
                ]
            )

        return rec, reason, conditions, restrictions

    def price(
        self, institution: FinancialInstitutionProfile, requested_limit: Optional[float] = None
    ) -> FIPricingResult:
        """
        Generate complete financial institution pricing
        """
        # Calculate all modifiers
        reg_mod, reg_score = self.calculate_regulatory_modifier(institution.signals, institution)
        gov_mod, gov_score = self.calculate_governance_modifier(institution.signals)
        size_mod = self.calculate_size_modifier(institution)
        complexity_mod = self.calculate_complexity_modifier(institution)
        history_mod = self.calculate_history_modifier(institution)
        fin_stability_mod = self.calculate_financial_stability_modifier(
            institution.signals, institution
        )

        # Jurisdiction multiplier
        jurisdiction_mod = self.jurisdiction_multipliers[institution.primary_jurisdiction]
        if len(institution.additional_jurisdictions) > 0:
            jurisdiction_mod *= 1.15  # Complexity of multiple jurisdictions

        # Get base rate
        base_rate = self.base_rates[self.coverage_type.value][institution.institution_type.value]

        # Calculate technical rate
        tech_rate = (
            base_rate
            * reg_mod
            * gov_mod
            * size_mod
            * complexity_mod
            * history_mod
            * fin_stability_mod
            * jurisdiction_mod
        )

        # Calculate exposure base
        exposure_mm = institution.revenue / 1_000_000

        # Base premium
        base_premium = tech_rate * exposure_mm

        # Risk assessment
        composite = institution.signals.get_composite_score()
        confidence = self.calculate_confidence(institution.signals)
        risk_tier = self.determine_risk_tier(composite, reg_score, gov_score)
        reg_action_prob = self.estimate_regulatory_action_probability(
            composite, reg_score, institution.regulatory_actions_5yr
        )

        # Policy structure
        limit, deductible, retention = self.recommend_policy_structure(
            institution, self.coverage_type
        )

        # Use requested limit if provided
        if requested_limit:
            limit = requested_limit

        # Premium per million revenue for comparison
        premium_per_mm = base_premium / exposure_mm if exposure_mm > 0 else 0

        # Generate recommendation
        rec, reason, conditions, restrictions = self.generate_recommendation(
            composite, reg_score, gov_score, confidence, institution
        )

        return FIPricingResult(
            institution_name=institution.institution_name,
            institution_type=institution.institution_type.value,
            coverage_type=self.coverage_type.value,
            base_rate=base_rate,
            regulatory_modifier=reg_mod,
            governance_modifier=gov_mod,
            size_modifier=size_mod,
            complexity_modifier=complexity_mod,
            history_modifier=history_mod,
            jurisdiction_modifier=jurisdiction_mod,
            recommended_limit=limit,
            deductible=deductible,
            retention=retention,
            technical_rate=tech_rate,
            annual_premium=base_premium,
            premium_per_million_revenue=premium_per_mm,
            composite_score=composite,
            regulatory_score=reg_score,
            governance_score=gov_score,
            risk_tier=risk_tier,
            regulatory_action_probability=reg_action_prob,
            confidence_level=confidence,
            recommendation=rec,
            reasoning=reason,
            conditions=conditions,
            coverage_restrictions=restrictions,
        )


# Example usage
if __name__ == "__main__":
    # Example 1: Well-managed regional bank with strong compliance
    strong_bank_signals = FinancialInstitutionSignals(
        regulatory_disclosures=92,
        enforcement_history=100,
        complaint_resolution=88,
        licensing_status=95,
        audit_transparency=90,
        regulatory_cooperation=87,
        board_composition=85,
        management_experience=88,
        compensation_disclosure=82,
        succession_planning=80,
        risk_committee=87,
        ethics_program=85,
        financial_reporting=90,
        auditor_quality=95,
        financial_stability=88,
        revenue_transparency=85,
        risk_disclosure=87,
        third_party_ratings=82,
        compliance_program=90,
        internal_controls=88,
        vendor_management=85,
        business_continuity=87,
        incident_reporting=83,
        insurance_coverage=90,
        media_sentiment=78,
        client_reviews=80,
        industry_recognition=75,
        litigation_history=92,
        regulatory_citations=85,
        social_responsibility=80,
        cybersecurity_posture=87,
        technology_investment=82,
        data_protection=88,
        system_resilience=85,
        innovation_signals=75,
        regulatory_technology=80,
    )

    regional_bank = FinancialInstitutionProfile(
        institution_name="First Regional Bank",
        institution_type=FinancialInstitutionType.COMMERCIAL_BANK,
        primary_jurisdiction=RegulatoryJurisdiction.US_FEDERAL,
        total_assets=15_000_000_000,
        revenue=450_000_000,
        employees=2500,
        years_operating=75,
        publicly_traded=True,
        client_count=500_000,
        retail_vs_institutional="mixed",
        product_complexity="moderate",
        international_operations=False,
        regulatory_actions_5yr=0,
        material_litigation_5yr=1,
        largest_settlement=2_500_000,
        data_breaches_5yr=0,
        customer_complaints_annual=150,
        capital_ratio=12.5,
        return_on_equity=11.2,
        claims_5yr=0,
        signals=strong_bank_signals,
    )

    # Example 2: Hedge fund with regulatory issues
    problematic_hf_signals = FinancialInstitutionSignals(
        regulatory_disclosures=58,
        enforcement_history=45,
        complaint_resolution=52,
        licensing_status=70,
        audit_transparency=55,
        regulatory_cooperation=48,
        board_composition=60,
        management_experience=65,
        compensation_disclosure=50,
        succession_planning=45,
        risk_committee=55,
        ethics_program=52,
        financial_reporting=68,
        auditor_quality=75,
        financial_stability=62,
        revenue_transparency=58,
        risk_disclosure=55,
        third_party_ratings=60,
        compliance_program=58,
        internal_controls=62,
        vendor_management=55,
        business_continuity=60,
        incident_reporting=50,
        insurance_coverage=65,
        media_sentiment=42,
        client_reviews=48,
        industry_recognition=55,
        litigation_history=38,
        regulatory_citations=45,
        social_responsibility=50,
        cybersecurity_posture=68,
        technology_investment=70,
        data_protection=65,
        system_resilience=62,
        innovation_signals=72,
        regulatory_technology=60,
    )

    hedge_fund = FinancialInstitutionProfile(
        institution_name="Apex Capital Management",
        institution_type=FinancialInstitutionType.HEDGE_FUND,
        primary_jurisdiction=RegulatoryJurisdiction.US_FEDERAL,
        additional_jurisdictions=[RegulatoryJurisdiction.UK_FCA],
        total_assets=8_000_000_000,
        revenue=200_000_000,
        aum=8_000_000_000,
        employees=150,
        years_operating=12,
        publicly_traded=False,
        client_count=250,
        retail_vs_institutional="institutional",
        product_complexity="complex",
        international_operations=True,
        regulatory_actions_5yr=2,
        material_litigation_5yr=3,
        largest_settlement=15_000_000,
        data_breaches_5yr=0,
        customer_complaints_annual=8,
        return_on_equity=18.5,
        claims_5yr=1,
        largest_claim=5_000_000,
        signals=problematic_hf_signals,
    )

    # Example 3: Fintech startup with limited history
    fintech_signals = FinancialInstitutionSignals(
        regulatory_disclosures=72,
        enforcement_history=95,
        complaint_resolution=78,
        licensing_status=85,
        audit_transparency=70,
        regulatory_cooperation=75,
        board_composition=68,
        management_experience=72,
        compensation_disclosure=65,
        succession_planning=55,
        risk_committee=65,
        ethics_program=70,
        financial_reporting=75,
        auditor_quality=70,
        financial_stability=65,
        revenue_transparency=72,
        risk_disclosure=68,
        third_party_ratings=60,
        compliance_program=75,
        internal_controls=70,
        vendor_management=72,
        business_continuity=68,
        incident_reporting=70,
        insurance_coverage=60,
        media_sentiment=80,
        client_reviews=85,
        industry_recognition=72,
        litigation_history=100,
        regulatory_citations=75,
        social_responsibility=78,
        cybersecurity_posture=88,
        technology_investment=92,
        data_protection=85,
        system_resilience=82,
        innovation_signals=95,
        regulatory_technology=88,
    )

    fintech = FinancialInstitutionProfile(
        institution_name="PayFlow Technologies",
        institution_type=FinancialInstitutionType.FINTECH,
        primary_jurisdiction=RegulatoryJurisdiction.US_STATE,
        total_assets=500_000_000,
        revenue=75_000_000,
        employees=300,
        years_operating=6,
        publicly_traded=False,
        client_count=2_000_000,
        retail_vs_institutional="retail",
        product_complexity="moderate",
        international_operations=False,
        regulatory_actions_5yr=0,
        material_litigation_5yr=0,
        largest_settlement=0,
        data_breaches_5yr=0,
        customer_complaints_annual=450,
        return_on_equity=-5.2,
        claims_5yr=0,
        signals=fintech_signals,
    )

    # Price D&O coverage for all three
    model = FinancialInstitutionPricingModel(FICoverageType.DNO)

    institutions = [
        ("Strong Compliance (Regional Bank)", regional_bank),
        ("Regulatory Issues (Hedge Fund)", hedge_fund),
        ("Emerging (Fintech)", fintech),
    ]

    print("=" * 120)
    print("FINANCIAL INSTITUTIONS D&O INSURANCE PRICING ANALYSIS")
    print("=" * 120)

    for label, institution in institutions:
        result = model.price(institution)

        print(f"\n{label}: {result.institution_name}")
        print("-" * 120)
        print(f"Type: {result.institution_type.upper().replace('_', ' ')}")
        print(f"Revenue: ${institution.revenue:,.0f} | Assets: ${institution.total_assets:,.0f}")
        print(
            f"Employees: {institution.employees:,} | Operating: {institution.years_operating} years"
        )
        print(
            f"Regulatory Actions (5yr): {institution.regulatory_actions_5yr} | Material Litigation (5yr): {institution.material_litigation_5yr}"
        )

        print(f"\nRISK ASSESSMENT:")
        print(f"  Composite Score: {result.composite_score:.0f}/1000")
        print(f"  Regulatory Score: {result.regulatory_score:.0f}/100")
        print(f"  Governance Score: {result.governance_score:.0f}/100")
        print(f"  Risk Tier: {result.risk_tier}")
        print(f"  Regulatory Action Probability (5yr): {result.regulatory_action_probability:.1%}")
        print(f"  Confidence Level: {result.confidence_level:.0%}")

        print(f"\nPRICING COMPONENTS:")
        print(f"  Base Rate: ${result.base_rate:,.2f} per $1M revenue")
        print(f"  Regulatory Modifier: {result.regulatory_modifier:.3f}x")
        print(f"  Governance Modifier: {result.governance_modifier:.3f}x")
        print(f"  Size Modifier: {result.size_modifier:.3f}x")
        print(f"  Complexity Modifier: {result.complexity_modifier:.3f}x")
        print(f"  History Modifier: {result.history_modifier:.3f}x")
        print(f"  Jurisdiction Modifier: {result.jurisdiction_modifier:.3f}x")
        print(f"  Technical Rate: ${result.technical_rate:,.2f} per $1M revenue")

        print(f"\nPOLICY STRUCTURE:")
        print(f"  Recommended Limit: ${result.recommended_limit:,.0f}")
        print(f"  Deductible: ${result.deductible:,.0f}")
        print(f"  Retention (excess): ${result.retention:,.0f}")
        print(f"  Annual Premium: ${result.annual_premium:,.0f}")
        print(f"  Premium per $1M Revenue: ${result.premium_per_million_revenue:,.0f}")

        print(f"\nUNDERWRITING DECISION:")
        print(f"  Recommendation: {result.recommendation}")
        print(f"  Reasoning: {result.reasoning}")

        if result.conditions:
            print(f"  Conditions:")
            for condition in result.conditions:
                print(f"    • {condition}")

        if result.coverage_restrictions:
            print(f"  Coverage Restrictions:")
            for restriction in result.coverage_restrictions:
                print(f"    • {restriction}")

        print("\n" + "=" * 120)

    # Demonstrate sensitivity to regulatory improvements
    print("\n\nREGULATORY IMPROVEMENT SENSITIVITY ANALYSIS")
    print("=" * 120)
    print("Impact of improving regulatory compliance for Hedge Fund:\n")

    scenarios = [
        (45, "Current - Multiple regulatory actions, poor standing"),
        (65, "Improved - Actions resolved, remediation in progress"),
        (85, "Excellent - Clean record, proactive compliance"),
    ]

    for reg_score, description in scenarios:
        test_signals = FinancialInstitutionSignals(**problematic_hf_signals.__dict__)
        test_signals.enforcement_history = reg_score
        test_signals.regulatory_disclosures = reg_score
        test_signals.regulatory_cooperation = reg_score
        test_signals.complaint_resolution = reg_score

        test_institution = FinancialInstitutionProfile(**hedge_fund.__dict__)
        test_institution.signals = test_signals
        if reg_score >= 85:
            test_institution.regulatory_actions_5yr = 0
        elif reg_score >= 65:
            test_institution.regulatory_actions_5yr = 1

        result = model.price(test_institution)

        print(f"Regulatory Score: {reg_score}/100 - {description}")
        print(f"  Premium: ${result.annual_premium:,.0f}")
        print(f"  Regulatory Action Probability: {result.regulatory_action_probability:.1%}")
        print(f"  Recommendation: {result.recommendation}")
        print()
