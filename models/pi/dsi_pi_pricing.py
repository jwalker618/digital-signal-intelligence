"""
Digital Signal Intelligence (DSI) - Professional Indemnity Insurance Pricing Model
===================================================================================

DSI-compliant professional indemnity insurance pricing based entirely on externally
observable signals, network authority analysis, and minimal optional direct inquiry.

This model conforms to Foundational Principles.

Professional Indemnity insurance is exceptionally suited to DSI because:
- Regulatory/licensing bodies maintain public disciplinary records
- Professional certifications and peer ratings are verifiable
- Client relationships and case outcomes are often observable
- Litigation history is public record
- Firm stability signals (partner turnover, office changes) are discoverable

Key DSI Principle: We assess PROFESSIONAL COMPETENCE and OPERATIONAL DISCIPLINE
through regulatory standing, peer recognition, and observable practice patterns - 
not through self-reported descriptions of internal procedures.

Professional Classes Addressed:
- Law Firms (all sizes and practice areas)
- Accounting Firms (audit, tax, advisory)
- Architects & Engineers
- Consultants (management, IT, HR, etc.)
- Healthcare Professionals (non-medical malpractice)
- Real Estate Professionals (agents, brokers, appraisers)
- Insurance Agents & Brokers
- Financial Planners & Advisers (non-SEC registered)

Author: John Walker
Version: 2.0
Date: November 2025
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime
import math


# =============================================================================
# ENUMERATIONS
# =============================================================================

class ProfessionType(Enum):
    """Primary professional classification."""
    LAW_FIRM = "law_firm"
    ACCOUNTING_FIRM = "accounting_firm"
    ARCHITECTURE = "architecture"
    ENGINEERING = "engineering"
    MANAGEMENT_CONSULTING = "management_consulting"
    IT_CONSULTING = "it_consulting"
    HR_CONSULTING = "hr_consulting"
    REAL_ESTATE = "real_estate"
    INSURANCE_BROKER = "insurance_broker"
    FINANCIAL_PLANNING = "financial_planning"
    HEALTHCARE_ADMIN = "healthcare_admin"
    APPRAISAL_VALUATION = "appraisal_valuation"
    ENVIRONMENTAL_CONSULTING = "environmental_consulting"
    OTHER = "other"


class FirmSize(Enum):
    """Firm size classification by headcount."""
    SOLO = "solo"                    # 1 professional
    MICRO = "micro"                  # 2-5 professionals
    SMALL = "small"                  # 6-20 professionals
    MEDIUM = "medium"                # 21-100 professionals
    LARGE = "large"                  # 101-500 professionals
    MAJOR = "major"                  # 500+ professionals


class RevenueSize(Enum):
    """Annual revenue classification."""
    UNDER_500K = "under_500k"
    R_500K_1M = "500k_1m"
    R_1M_5M = "1m_5m"
    R_5M_25M = "5m_25m"
    R_25M_100M = "25m_100m"
    R_100M_500M = "100m_500m"
    OVER_500M = "over_500m"


class RiskTier(Enum):
    """DSI risk tier assignment."""
    TIER_1 = 1  # Preferred: Score 800-1000
    TIER_2 = 2  # Standard: Score 650-799
    TIER_3 = 3  # Elevated: Score 500-649
    TIER_4 = 4  # High Risk: Score 350-499
    TIER_5 = 5  # Critical: Score 0-349


class LegalPracticeArea(Enum):
    """Law firm practice area classification."""
    CORPORATE_MA = "corporate_ma"
    SECURITIES = "securities"
    REAL_ESTATE = "real_estate_law"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    EMPLOYMENT = "employment"
    LITIGATION_GENERAL = "litigation_general"
    LITIGATION_PLAINTIFF = "litigation_plaintiff"
    TAX = "tax"
    TRUSTS_ESTATES = "trusts_estates"
    FAMILY = "family"
    CRIMINAL = "criminal"
    PERSONAL_INJURY_DEFENSE = "pi_defense"
    PERSONAL_INJURY_PLAINTIFF = "pi_plaintiff"
    BANKRUPTCY = "bankruptcy"
    ENVIRONMENTAL = "environmental"
    HEALTHCARE = "healthcare_law"
    INSURANCE_COVERAGE = "insurance_coverage"
    GENERAL_PRACTICE = "general_practice"


class AccountingServiceType(Enum):
    """Accounting firm service classification."""
    AUDIT_PUBLIC = "audit_public"
    AUDIT_PRIVATE = "audit_private"
    TAX_INDIVIDUAL = "tax_individual"
    TAX_CORPORATE = "tax_corporate"
    TAX_ESTATE = "tax_estate"
    ADVISORY_MA = "advisory_ma"
    ADVISORY_VALUATION = "advisory_valuation"
    FORENSIC = "forensic"
    BOOKKEEPING = "bookkeeping"
    GENERAL_PRACTICE = "general_practice"


# =============================================================================
# SIGNAL DATA STRUCTURES
# =============================================================================

@dataclass
class NetworkAuthoritySignals:
    """
    Type 1: Network Authority Signals
    
    Who trusts this firm? Quality of professional relationships and recognition.
    """
    
    # Peer recognition and rankings
    peer_ranking_score: float = 0.0  # Chambers, Legal 500, Best Lawyers, etc.
    peer_ranking_evidence: str = ""
    
    # Client quality (public clients, notable matters)
    client_quality_score: float = 0.0
    client_quality_evidence: str = ""
    
    # Referral network quality
    referral_network_score: float = 0.0
    referral_network_evidence: str = ""
    
    # Professional association leadership
    association_leadership_score: float = 0.0
    association_leadership_evidence: str = ""
    
    # Academic/thought leadership
    thought_leadership_score: float = 0.0
    thought_leadership_evidence: str = ""
    
    # Insurance carrier panel membership
    panel_membership_score: float = 0.0
    panel_membership_evidence: str = ""
    
    # Bank/lender relationships (for real estate, etc.)
    lender_relationships_score: float = 0.0
    lender_relationships_evidence: str = ""


@dataclass
class RegulatoryStandingSignals:
    """
    Type 6: Public Record Signals - Regulatory/Licensing Component
    
    From bar associations, state licensing boards, professional bodies.
    """
    
    # License status (all principals/professionals)
    license_status_score: float = 0.0
    license_status_evidence: str = ""
    
    # Disciplinary history (sanctions, suspensions, censures)
    disciplinary_history_score: float = 0.0
    disciplinary_history_evidence: str = ""
    
    # Malpractice judgments/settlements (public records)
    malpractice_record_score: float = 0.0
    malpractice_record_evidence: str = ""
    
    # Continuing education compliance
    ce_compliance_score: float = 0.0
    ce_compliance_evidence: str = ""
    
    # Specialty certifications
    specialty_certification_score: float = 0.0
    specialty_certification_evidence: str = ""
    
    # Peer review rating (for accounting firms)
    peer_review_score: float = 0.0
    peer_review_evidence: str = ""
    
    # SEC/PCAOB standing (for applicable accounting firms)
    regulatory_standing_score: float = 0.0
    regulatory_standing_evidence: str = ""


@dataclass
class FirmStabilitySignals:
    """
    Type 5 & 6: Corporate Footprint and Public Record Signals
    
    Observable indicators of firm health and stability.
    """
    
    # Years in practice
    tenure_score: float = 0.0
    tenure_evidence: str = ""
    
    # Partner/principal stability
    partner_stability_score: float = 0.0
    partner_stability_evidence: str = ""
    
    # Staff retention signals (job postings, reviews)
    staff_retention_score: float = 0.0
    staff_retention_evidence: str = ""
    
    # Office presence/stability
    office_stability_score: float = 0.0
    office_stability_evidence: str = ""
    
    # Financial stability indicators
    financial_stability_score: float = 0.0
    financial_stability_evidence: str = ""
    
    # Growth trajectory (controlled vs chaotic)
    growth_pattern_score: float = 0.0
    growth_pattern_evidence: str = ""
    
    # Succession planning signals
    succession_score: float = 0.0
    succession_evidence: str = ""


@dataclass
class PracticeQualitySignals:
    """
    Type 5 & 6: Observable practice quality indicators.
    """
    
    # Matter/case outcome patterns (for litigators)
    outcome_patterns_score: float = 0.0
    outcome_patterns_evidence: str = ""
    
    # Transaction completion record (for transactional practices)
    transaction_record_score: float = 0.0
    transaction_record_evidence: str = ""
    
    # Client review/rating platforms
    client_review_score: float = 0.0
    client_review_evidence: str = ""
    
    # Published work quality (briefs, opinions, reports)
    work_quality_score: float = 0.0
    work_quality_evidence: str = ""
    
    # Fee dispute history
    fee_dispute_score: float = 0.0
    fee_dispute_evidence: str = ""
    
    # Complaints to professional bodies
    complaint_history_score: float = 0.0
    complaint_history_evidence: str = ""


@dataclass
class TechnicalInfrastructureSignals:
    """
    Type 2: Technical Infrastructure Signals
    
    Digital security posture - critical for client confidentiality.
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
    
    # Client portal security (if applicable)
    portal_security_score: float = 0.0
    portal_security_evidence: str = ""
    
    # Data breach history
    breach_history_score: float = 0.0
    breach_history_evidence: str = ""
    
    # Third-party security rating
    security_rating_score: float = 0.0
    security_rating_evidence: str = ""


@dataclass
class CorporateFootprintSignals:
    """
    Type 5: Corporate Digital Footprint Signals
    """
    
    # Website professionalism and completeness
    website_quality_score: float = 0.0
    website_quality_evidence: str = ""
    
    # Attorney/professional bio completeness
    bio_completeness_score: float = 0.0
    bio_completeness_evidence: str = ""
    
    # Practice area clarity
    practice_clarity_score: float = 0.0
    practice_clarity_evidence: str = ""
    
    # Thought leadership/publications
    publications_score: float = 0.0
    publications_evidence: str = ""
    
    # Community involvement
    community_involvement_score: float = 0.0
    community_involvement_evidence: str = ""
    
    # Diversity/inclusion signals
    diversity_score: float = 0.0
    diversity_evidence: str = ""
    
    # Pro bono commitment
    pro_bono_score: float = 0.0
    pro_bono_evidence: str = ""


@dataclass
class LitigationHistorySignals:
    """
    Type 6: Public Record Signals - Litigation Component
    
    From PACER, state court records, disciplinary databases.
    """
    
    # Malpractice suits filed
    malpractice_suits_score: float = 0.0
    malpractice_suits_evidence: str = ""
    
    # Fee disputes/arbitration
    fee_disputes_score: float = 0.0
    fee_disputes_evidence: str = ""
    
    # Regulatory enforcement
    regulatory_enforcement_score: float = 0.0
    regulatory_enforcement_evidence: str = ""
    
    # Other civil litigation (as defendant)
    civil_litigation_score: float = 0.0
    civil_litigation_evidence: str = ""
    
    # Bankruptcy involvement (firm or principals)
    bankruptcy_score: float = 0.0
    bankruptcy_evidence: str = ""


@dataclass
class DirectInquirySignals:
    """
    Type 7: Direct Inquiry Signals (Optional)
    
    Maximum 6 questions for Professional Indemnity.
    These supplement but cannot override external signals.
    """
    
    pending_claims: Optional[bool] = None
    # "Any pending or threatened malpractice claims?"
    
    disciplinary_pending: Optional[bool] = None
    # "Any pending disciplinary proceedings against any professional?"
    
    coverage_declined: Optional[bool] = None
    # "Has any PI coverage been declined or non-renewed in past 3 years?"
    
    practice_area_change: Optional[bool] = None
    # "Any significant change in practice areas in past 2 years?"
    
    merger_activity: Optional[bool] = None
    # "Any merger, acquisition, or spin-off in past 2 years?"
    
    major_client_loss: Optional[bool] = None
    # "Loss of client representing >25% of revenue in past year?"


# =============================================================================
# PROFESSION-SPECIFIC CONFIGURATIONS
# =============================================================================

@dataclass
class LawFirmProfile:
    """Law firm specific profile data."""
    practice_areas: List[LegalPracticeArea] = field(default_factory=list)
    primary_practice: Optional[LegalPracticeArea] = None
    jurisdictions: List[str] = field(default_factory=list)  # Bar admissions
    am_law_ranking: Optional[int] = None  # Am Law 100/200 ranking
    chambers_ranking: Optional[str] = None  # Band 1-6 or Not Ranked
    martindale_rating: Optional[str] = None  # AV, BV, etc.
    partner_count: int = 0
    associate_count: int = 0
    contingency_percentage: float = 0.0  # % of matters on contingency


@dataclass
class AccountingFirmProfile:
    """Accounting firm specific profile data."""
    service_types: List[AccountingServiceType] = field(default_factory=list)
    primary_service: Optional[AccountingServiceType] = None
    peer_review_rating: Optional[str] = None  # Pass, Pass w/ Deficiency, Fail
    pcaob_registered: bool = False
    sec_audit_clients: int = 0
    cpa_count: int = 0
    aicpa_membership: bool = False


@dataclass
class ArchEngProfile:
    """Architecture/Engineering firm specific profile data."""
    disciplines: List[str] = field(default_factory=list)
    primary_discipline: Optional[str] = None
    pe_licenses: int = 0  # Professional Engineer licenses
    aia_membership: bool = False  # American Institute of Architects
    project_types: List[str] = field(default_factory=list)
    typical_project_value: Optional[float] = None
    structural_work: bool = False  # Higher risk indicator


# =============================================================================
# SIGNAL CATEGORY WEIGHTS BY PROFESSION
# =============================================================================

PROFESSION_WEIGHTS: Dict[ProfessionType, Dict[str, float]] = {
    ProfessionType.LAW_FIRM: {
        'network_authority': 0.20,
        'regulatory_standing': 0.25,
        'firm_stability': 0.15,
        'practice_quality': 0.15,
        'technical_infrastructure': 0.05,
        'corporate_footprint': 0.10,
        'litigation_history': 0.10,
    },
    ProfessionType.ACCOUNTING_FIRM: {
        'network_authority': 0.15,
        'regulatory_standing': 0.30,  # Higher - peer review critical
        'firm_stability': 0.15,
        'practice_quality': 0.15,
        'technical_infrastructure': 0.05,
        'corporate_footprint': 0.10,
        'litigation_history': 0.10,
    },
    ProfessionType.ARCHITECTURE: {
        'network_authority': 0.15,
        'regulatory_standing': 0.20,
        'firm_stability': 0.15,
        'practice_quality': 0.20,  # Project outcomes critical
        'technical_infrastructure': 0.05,
        'corporate_footprint': 0.10,
        'litigation_history': 0.15,  # Construction defects common
    },
    ProfessionType.ENGINEERING: {
        'network_authority': 0.15,
        'regulatory_standing': 0.25,  # PE license critical
        'firm_stability': 0.15,
        'practice_quality': 0.20,
        'technical_infrastructure': 0.05,
        'corporate_footprint': 0.05,
        'litigation_history': 0.15,
    },
    ProfessionType.MANAGEMENT_CONSULTING: {
        'network_authority': 0.25,  # Reputation-driven
        'regulatory_standing': 0.10,  # Less regulated
        'firm_stability': 0.15,
        'practice_quality': 0.20,
        'technical_infrastructure': 0.10,
        'corporate_footprint': 0.15,
        'litigation_history': 0.05,
    },
    ProfessionType.IT_CONSULTING: {
        'network_authority': 0.15,
        'regulatory_standing': 0.10,
        'firm_stability': 0.15,
        'practice_quality': 0.20,
        'technical_infrastructure': 0.20,  # Their core competency
        'corporate_footprint': 0.10,
        'litigation_history': 0.10,
    },
    ProfessionType.REAL_ESTATE: {
        'network_authority': 0.15,
        'regulatory_standing': 0.25,  # License critical
        'firm_stability': 0.15,
        'practice_quality': 0.15,
        'technical_infrastructure': 0.05,
        'corporate_footprint': 0.10,
        'litigation_history': 0.15,
    },
    ProfessionType.INSURANCE_BROKER: {
        'network_authority': 0.20,
        'regulatory_standing': 0.25,
        'firm_stability': 0.15,
        'practice_quality': 0.15,
        'technical_infrastructure': 0.10,
        'corporate_footprint': 0.05,
        'litigation_history': 0.10,
    },
    ProfessionType.FINANCIAL_PLANNING: {
        'network_authority': 0.15,
        'regulatory_standing': 0.30,  # Regulatory critical
        'firm_stability': 0.15,
        'practice_quality': 0.15,
        'technical_infrastructure': 0.10,
        'corporate_footprint': 0.05,
        'litigation_history': 0.10,
    },
}

# Default weights for professions not explicitly configured
DEFAULT_WEIGHTS = {
    'network_authority': 0.15,
    'regulatory_standing': 0.25,
    'firm_stability': 0.15,
    'practice_quality': 0.15,
    'technical_infrastructure': 0.10,
    'corporate_footprint': 0.10,
    'litigation_history': 0.10,
}


# =============================================================================
# PRACTICE AREA RISK MODIFIERS (LAW FIRMS)
# =============================================================================

LEGAL_PRACTICE_RISK_MODIFIERS: Dict[LegalPracticeArea, float] = {
    LegalPracticeArea.SECURITIES: 1.40,  # High regulatory exposure
    LegalPracticeArea.CORPORATE_MA: 1.25,  # Large transaction exposure
    LegalPracticeArea.INTELLECTUAL_PROPERTY: 1.15,  # Patent valuations
    LegalPracticeArea.REAL_ESTATE: 1.10,  # Title issues
    LegalPracticeArea.PERSONAL_INJURY_PLAINTIFF: 1.30,  # Deadline sensitivity
    LegalPracticeArea.PERSONAL_INJURY_DEFENSE: 0.95,
    LegalPracticeArea.EMPLOYMENT: 1.10,
    LegalPracticeArea.TRUSTS_ESTATES: 1.20,  # Fiduciary exposure
    LegalPracticeArea.TAX: 1.15,  # IRS exposure
    LegalPracticeArea.BANKRUPTCY: 1.15,  # Fiduciary duties
    LegalPracticeArea.ENVIRONMENTAL: 1.20,  # Long-tail exposure
    LegalPracticeArea.HEALTHCARE: 1.15,  # Regulatory complexity
    LegalPracticeArea.INSURANCE_COVERAGE: 1.05,
    LegalPracticeArea.LITIGATION_GENERAL: 1.00,
    LegalPracticeArea.LITIGATION_PLAINTIFF: 1.15,  # Deadline sensitivity
    LegalPracticeArea.FAMILY: 0.90,  # Lower severity
    LegalPracticeArea.CRIMINAL: 0.85,  # Lower severity typically
    LegalPracticeArea.GENERAL_PRACTICE: 1.05,
}


# =============================================================================
# ACCOUNTING SERVICE RISK MODIFIERS
# =============================================================================

ACCOUNTING_SERVICE_RISK_MODIFIERS: Dict[AccountingServiceType, float] = {
    AccountingServiceType.AUDIT_PUBLIC: 1.50,  # Highest exposure
    AccountingServiceType.AUDIT_PRIVATE: 1.25,
    AccountingServiceType.ADVISORY_MA: 1.30,  # Transaction advisory
    AccountingServiceType.ADVISORY_VALUATION: 1.35,  # Valuation disputes
    AccountingServiceType.TAX_CORPORATE: 1.10,
    AccountingServiceType.TAX_ESTATE: 1.20,  # Estate planning complexity
    AccountingServiceType.TAX_INDIVIDUAL: 0.90,
    AccountingServiceType.FORENSIC: 1.25,  # Expert testimony exposure
    AccountingServiceType.BOOKKEEPING: 0.80,  # Lower exposure
    AccountingServiceType.GENERAL_PRACTICE: 1.00,
}


# =============================================================================
# FIRM SIZE RISK MODIFIERS
# =============================================================================

FIRM_SIZE_MODIFIERS: Dict[FirmSize, float] = {
    FirmSize.SOLO: 1.20,  # Higher individual concentration risk
    FirmSize.MICRO: 1.10,
    FirmSize.SMALL: 1.00,  # Baseline
    FirmSize.MEDIUM: 0.95,  # Some diversification benefit
    FirmSize.LARGE: 0.90,  # Better systems/oversight
    FirmSize.MAJOR: 0.85,  # But higher aggregate exposure
}


# =============================================================================
# REVENUE SIZE RISK MODIFIERS
# =============================================================================

REVENUE_SIZE_MODIFIERS: Dict[RevenueSize, float] = {
    RevenueSize.UNDER_500K: 0.85,
    RevenueSize.R_500K_1M: 0.90,
    RevenueSize.R_1M_5M: 1.00,
    RevenueSize.R_5M_25M: 1.10,
    RevenueSize.R_25M_100M: 1.25,
    RevenueSize.R_100M_500M: 1.40,
    RevenueSize.OVER_500M: 1.60,
}


# =============================================================================
# SCORING ENGINE
# =============================================================================

@dataclass
class SignalScore:
    """Individual signal score with metadata."""
    signal_name: str
    raw_score: float  # 0-100
    weight: float
    weighted_score: float
    evidence: str
    confidence: float  # 0-1, how reliable is this signal
    source: str


@dataclass
class CategoryScore:
    """Category-level aggregated score."""
    category_name: str
    signals: List[SignalScore]
    category_score: float  # 0-100
    category_weight: float
    weighted_contribution: float


@dataclass
class DSIAssessment:
    """Complete DSI assessment result."""
    entity_name: str
    profession_type: ProfessionType
    firm_size: FirmSize
    revenue_size: RevenueSize
    
    # Scoring
    category_scores: List[CategoryScore]
    composite_score: float  # 0-1000
    tier: RiskTier
    confidence: float  # Overall assessment confidence
    
    # Flags
    red_flags: List[str]
    green_flags: List[str]
    
    # Decision
    decision: str  # APPROVE, REVIEW, DECLINE
    decision_rationale: str
    
    # Pricing
    base_premium: float
    risk_adjusted_premium: float
    premium_modifier: float
    
    # Metadata
    assessment_date: datetime
    signal_coverage: float  # % of signals populated
    data_quality_score: float


class DSIProfessionalIndemnityEngine:
    """
    Main DSI engine for Professional Indemnity pricing.
    
    Implements DSI Principles v1.0 for PI insurance.
    """
    
    def __init__(self):
        self.profession_weights = PROFESSION_WEIGHTS
        self.default_weights = DEFAULT_WEIGHTS
        
    def get_weights(self, profession: ProfessionType) -> Dict[str, float]:
        """Get signal category weights for profession type."""
        return self.profession_weights.get(profession, self.default_weights)
    
    def calculate_category_score(
        self,
        signals: List[Tuple[str, float, str, float]],  # (name, score, evidence, confidence)
        category_name: str
    ) -> CategoryScore:
        """Calculate aggregated category score from individual signals."""
        if not signals:
            return CategoryScore(
                category_name=category_name,
                signals=[],
                category_score=0.0,
                category_weight=0.0,
                weighted_contribution=0.0
            )
        
        signal_scores = []
        total_weight = 0.0
        weighted_sum = 0.0
        
        # Equal weight within category for simplicity
        signal_weight = 1.0 / len(signals)
        
        for name, score, evidence, confidence in signals:
            # Score is 0-100, weight by confidence
            weighted = score * signal_weight * confidence
            signal_scores.append(SignalScore(
                signal_name=name,
                raw_score=score,
                weight=signal_weight,
                weighted_score=weighted,
                evidence=evidence,
                confidence=confidence,
                source="DSI Collection"
            ))
            weighted_sum += weighted
            total_weight += signal_weight * confidence
        
        # Calculate weighted average score (0-100)
        category_score = (weighted_sum / total_weight) if total_weight > 0 else 0.0
        
        return CategoryScore(
            category_name=category_name,
            signals=signal_scores,
            category_score=min(100, category_score),
            category_weight=0.0,  # Set later
            weighted_contribution=0.0  # Set later
        )
    
    def calculate_composite_score(
        self,
        category_scores: List[CategoryScore],
        weights: Dict[str, float]
    ) -> float:
        """Calculate composite DSI score (0-1000)."""
        total_weighted = 0.0
        total_weight = 0.0
        
        weight_map = {
            'Network Authority': weights.get('network_authority', 0.15),
            'Regulatory Standing': weights.get('regulatory_standing', 0.25),
            'Firm Stability': weights.get('firm_stability', 0.15),
            'Practice Quality': weights.get('practice_quality', 0.15),
            'Technical Infrastructure': weights.get('technical_infrastructure', 0.10),
            'Corporate Footprint': weights.get('corporate_footprint', 0.10),
            'Litigation History': weights.get('litigation_history', 0.10),
        }
        
        for cat in category_scores:
            weight = weight_map.get(cat.category_name, 0.1)
            cat.category_weight = weight
            cat.weighted_contribution = cat.category_score * weight
            total_weighted += cat.weighted_contribution
            total_weight += weight
        
        # Scale to 0-1000
        if total_weight > 0:
            return (total_weighted / total_weight) * 10
        return 0.0
    
    def assign_tier(self, composite_score: float) -> RiskTier:
        """Assign risk tier based on composite score."""
        if composite_score >= 800:
            return RiskTier.TIER_1
        elif composite_score >= 650:
            return RiskTier.TIER_2
        elif composite_score >= 500:
            return RiskTier.TIER_3
        elif composite_score >= 350:
            return RiskTier.TIER_4
        else:
            return RiskTier.TIER_5
    
    def identify_red_flags(
        self,
        regulatory: RegulatoryStandingSignals,
        litigation: LitigationHistorySignals,
        stability: FirmStabilitySignals,
        direct: DirectInquirySignals,
        profession: ProfessionType = None
    ) -> List[str]:
        """Identify critical red flags requiring attention."""
        flags = []
        
        # Regulatory red flags
        if regulatory.disciplinary_history_score > 0 and regulatory.disciplinary_history_score < 40:
            flags.append("Significant disciplinary history identified")
        if regulatory.license_status_score > 0 and regulatory.license_status_score < 50:
            flags.append("License status concerns (inactive, suspended, or restrictions)")
        if regulatory.malpractice_record_score > 0 and regulatory.malpractice_record_score < 40:
            flags.append("Material malpractice judgments or settlements on record")
        
        # Peer review only applies to accounting firms
        if profession == ProfessionType.ACCOUNTING_FIRM:
            if regulatory.peer_review_score > 0 and regulatory.peer_review_score < 40:
                flags.append("Failed or deficient peer review")
        
        # Litigation red flags
        if litigation.malpractice_suits_score > 0 and litigation.malpractice_suits_score < 40:
            flags.append("Multiple malpractice suits in recent history")
        if litigation.regulatory_enforcement_score > 0 and litigation.regulatory_enforcement_score < 40:
            flags.append("Regulatory enforcement action history")
        if litigation.bankruptcy_score > 0 and litigation.bankruptcy_score < 50:
            flags.append("Bankruptcy history (firm or principals)")
        
        # Stability red flags
        if stability.partner_stability_score > 0 and stability.partner_stability_score < 40:
            flags.append("High partner/principal turnover detected")
        if stability.financial_stability_score > 0 and stability.financial_stability_score < 40:
            flags.append("Financial instability indicators")
        
        # Direct inquiry red flags
        if direct.pending_claims:
            flags.append("Pending or threatened malpractice claims disclosed")
        if direct.disciplinary_pending:
            flags.append("Pending disciplinary proceedings disclosed")
        if direct.coverage_declined:
            flags.append("Prior PI coverage declined or non-renewed")
        
        return flags
    
    def identify_green_flags(
        self,
        network: NetworkAuthoritySignals,
        regulatory: RegulatoryStandingSignals,
        stability: FirmStabilitySignals,
        practice: PracticeQualitySignals
    ) -> List[str]:
        """Identify positive indicators."""
        flags = []
        
        # Network green flags
        if network.peer_ranking_score >= 80:
            flags.append("Top-tier peer recognition (Chambers, Legal 500, etc.)")
        if network.client_quality_score >= 80:
            flags.append("High-quality client base")
        if network.association_leadership_score >= 75:
            flags.append("Professional association leadership")
        
        # Regulatory green flags
        if regulatory.disciplinary_history_score >= 95:
            flags.append("Clean disciplinary record")
        if regulatory.specialty_certification_score >= 80:
            flags.append("Advanced specialty certifications")
        if regulatory.peer_review_score >= 90:
            flags.append("Pass with no deficiencies on peer review")
        
        # Stability green flags
        if stability.tenure_score >= 80:
            flags.append("Long-established practice (20+ years)")
        if stability.partner_stability_score >= 85:
            flags.append("Excellent partner retention")
        if stability.succession_score >= 80:
            flags.append("Clear succession planning in place")
        
        # Practice quality green flags
        if practice.client_review_score >= 85:
            flags.append("Excellent client reviews/ratings")
        if practice.complaint_history_score >= 95:
            flags.append("No complaints to professional bodies")
        
        return flags
    
    def determine_decision(
        self,
        tier: RiskTier,
        red_flags: List[str],
        confidence: float
    ) -> Tuple[str, str]:
        """Determine underwriting decision and rationale."""
        
        # Critical red flags force review regardless of tier
        critical_flags = [
            "Pending or threatened malpractice claims disclosed",
            "Pending disciplinary proceedings disclosed",
            "Prior PI coverage declined or non-renewed",
            "License status concerns",
            "Failed or deficient peer review",
        ]
        
        has_critical = any(
            any(cf in flag for cf in critical_flags) 
            for flag in red_flags
        )
        
        if has_critical:
            return "DECLINE", f"Critical red flag(s) identified: {'; '.join(red_flags[:3])}"
        
        if tier == RiskTier.TIER_1:
            if len(red_flags) == 0:
                return "APPROVE", "Tier 1 risk with no red flags - auto-approve with preferred pricing"
            else:
                return "APPROVE", f"Tier 1 risk with minor concerns - approve at standard pricing"
        
        elif tier == RiskTier.TIER_2:
            if len(red_flags) <= 1:
                return "APPROVE", "Tier 2 risk within acceptable parameters - auto-approve"
            else:
                return "REVIEW", f"Tier 2 risk with multiple flags - manual review recommended"
        
        elif tier == RiskTier.TIER_3:
            return "REVIEW", f"Tier 3 elevated risk - requires manual underwriter review"
        
        elif tier == RiskTier.TIER_4:
            return "REVIEW", f"Tier 4 high risk - requires senior underwriter review with loading"
        
        else:  # TIER_5
            return "DECLINE", f"Tier 5 critical risk - recommend decline"
    
    def calculate_premium(
        self,
        profession: ProfessionType,
        firm_size: FirmSize,
        revenue_size: RevenueSize,
        tier: RiskTier,
        limit: float,
        retention: float,
        practice_modifier: float = 1.0
    ) -> Tuple[float, float, float]:
        """
        Calculate premium based on DSI assessment.
        
        Returns: (base_premium, risk_adjusted_premium, modifier)
        """
        
        # Base rate per $1M limit by profession
        BASE_RATES: Dict[ProfessionType, float] = {
            ProfessionType.LAW_FIRM: 8500,
            ProfessionType.ACCOUNTING_FIRM: 9000,
            ProfessionType.ARCHITECTURE: 7500,
            ProfessionType.ENGINEERING: 8000,
            ProfessionType.MANAGEMENT_CONSULTING: 6000,
            ProfessionType.IT_CONSULTING: 7000,
            ProfessionType.REAL_ESTATE: 5500,
            ProfessionType.INSURANCE_BROKER: 6500,
            ProfessionType.FINANCIAL_PLANNING: 7500,
        }
        
        # Tier modifiers
        TIER_MODIFIERS = {
            RiskTier.TIER_1: 0.75,
            RiskTier.TIER_2: 1.00,
            RiskTier.TIER_3: 1.30,
            RiskTier.TIER_4: 1.75,
            RiskTier.TIER_5: 2.50,
        }
        
        # Get base rate
        base_rate = BASE_RATES.get(profession, 7000)
        
        # Apply modifiers
        firm_mod = FIRM_SIZE_MODIFIERS.get(firm_size, 1.0)
        revenue_mod = REVENUE_SIZE_MODIFIERS.get(revenue_size, 1.0)
        tier_mod = TIER_MODIFIERS.get(tier, 1.0)
        
        # Calculate
        limit_factor = limit / 1_000_000  # Per million
        
        # ILF curve (simplified)
        if limit_factor <= 1:
            ilf = 1.0
        elif limit_factor <= 2:
            ilf = 1.0 + (limit_factor - 1) * 0.6
        elif limit_factor <= 5:
            ilf = 1.6 + (limit_factor - 2) * 0.4
        else:
            ilf = 2.8 + (limit_factor - 5) * 0.3
        
        # Retention credit
        retention_factor = retention / 50_000  # Baseline $50K retention
        retention_credit = max(0.80, 1.0 - (retention_factor - 1) * 0.05)
        
        base_premium = base_rate * ilf * retention_credit
        
        # Apply all modifiers
        total_modifier = firm_mod * revenue_mod * tier_mod * practice_modifier
        risk_adjusted = base_premium * total_modifier
        
        return base_premium, risk_adjusted, total_modifier
    
    def assess(
        self,
        entity_name: str,
        profession: ProfessionType,
        firm_size: FirmSize,
        revenue_size: RevenueSize,
        network: NetworkAuthoritySignals,
        regulatory: RegulatoryStandingSignals,
        stability: FirmStabilitySignals,
        practice: PracticeQualitySignals,
        technical: TechnicalInfrastructureSignals,
        footprint: CorporateFootprintSignals,
        litigation: LitigationHistorySignals,
        direct: DirectInquirySignals,
        limit: float = 1_000_000,
        retention: float = 50_000,
        practice_modifier: float = 1.0
    ) -> DSIAssessment:
        """
        Perform complete DSI assessment for Professional Indemnity.
        """
        
        # Get weights for this profession
        weights = self.get_weights(profession)
        
        # Calculate category scores
        category_scores = []
        
        # Network Authority
        network_signals = [
            ("Peer Ranking", network.peer_ranking_score, network.peer_ranking_evidence, 0.9),
            ("Client Quality", network.client_quality_score, network.client_quality_evidence, 0.8),
            ("Referral Network", network.referral_network_score, network.referral_network_evidence, 0.7),
            ("Association Leadership", network.association_leadership_score, network.association_leadership_evidence, 0.9),
            ("Thought Leadership", network.thought_leadership_score, network.thought_leadership_evidence, 0.8),
        ]
        category_scores.append(self.calculate_category_score(
            [(n, s, e, c) for n, s, e, c in network_signals if s > 0],
            "Network Authority"
        ))
        
        # Regulatory Standing
        regulatory_signals = [
            ("License Status", regulatory.license_status_score, regulatory.license_status_evidence, 1.0),
            ("Disciplinary History", regulatory.disciplinary_history_score, regulatory.disciplinary_history_evidence, 1.0),
            ("Malpractice Record", regulatory.malpractice_record_score, regulatory.malpractice_record_evidence, 0.95),
            ("CE Compliance", regulatory.ce_compliance_score, regulatory.ce_compliance_evidence, 0.8),
            ("Specialty Certification", regulatory.specialty_certification_score, regulatory.specialty_certification_evidence, 0.85),
            ("Peer Review", regulatory.peer_review_score, regulatory.peer_review_evidence, 0.95),
        ]
        category_scores.append(self.calculate_category_score(
            [(n, s, e, c) for n, s, e, c in regulatory_signals if s > 0],
            "Regulatory Standing"
        ))
        
        # Firm Stability
        stability_signals = [
            ("Tenure", stability.tenure_score, stability.tenure_evidence, 0.9),
            ("Partner Stability", stability.partner_stability_score, stability.partner_stability_evidence, 0.85),
            ("Staff Retention", stability.staff_retention_score, stability.staff_retention_evidence, 0.7),
            ("Office Stability", stability.office_stability_score, stability.office_stability_evidence, 0.75),
            ("Financial Stability", stability.financial_stability_score, stability.financial_stability_evidence, 0.8),
            ("Succession Planning", stability.succession_score, stability.succession_evidence, 0.7),
        ]
        category_scores.append(self.calculate_category_score(
            [(n, s, e, c) for n, s, e, c in stability_signals if s > 0],
            "Firm Stability"
        ))
        
        # Practice Quality
        practice_signals = [
            ("Outcome Patterns", practice.outcome_patterns_score, practice.outcome_patterns_evidence, 0.8),
            ("Client Reviews", practice.client_review_score, practice.client_review_evidence, 0.85),
            ("Work Quality", practice.work_quality_score, practice.work_quality_evidence, 0.75),
            ("Fee Disputes", practice.fee_dispute_score, practice.fee_dispute_evidence, 0.9),
            ("Complaint History", practice.complaint_history_score, practice.complaint_history_evidence, 0.95),
        ]
        category_scores.append(self.calculate_category_score(
            [(n, s, e, c) for n, s, e, c in practice_signals if s > 0],
            "Practice Quality"
        ))
        
        # Technical Infrastructure
        tech_signals = [
            ("TLS Configuration", technical.tls_score, technical.tls_evidence, 0.95),
            ("Email Authentication", technical.email_auth_score, technical.email_auth_evidence, 0.9),
            ("Security Headers", technical.security_headers_score, technical.security_headers_evidence, 0.85),
            ("Breach History", technical.breach_history_score, technical.breach_history_evidence, 1.0),
        ]
        category_scores.append(self.calculate_category_score(
            [(n, s, e, c) for n, s, e, c in tech_signals if s > 0],
            "Technical Infrastructure"
        ))
        
        # Corporate Footprint
        footprint_signals = [
            ("Website Quality", footprint.website_quality_score, footprint.website_quality_evidence, 0.7),
            ("Bio Completeness", footprint.bio_completeness_score, footprint.bio_completeness_evidence, 0.75),
            ("Practice Clarity", footprint.practice_clarity_score, footprint.practice_clarity_evidence, 0.7),
            ("Publications", footprint.publications_score, footprint.publications_evidence, 0.6),
            ("Pro Bono", footprint.pro_bono_score, footprint.pro_bono_evidence, 0.5),
        ]
        category_scores.append(self.calculate_category_score(
            [(n, s, e, c) for n, s, e, c in footprint_signals if s > 0],
            "Corporate Footprint"
        ))
        
        # Litigation History
        litigation_signals = [
            ("Malpractice Suits", litigation.malpractice_suits_score, litigation.malpractice_suits_evidence, 1.0),
            ("Fee Disputes", litigation.fee_disputes_score, litigation.fee_disputes_evidence, 0.9),
            ("Regulatory Enforcement", litigation.regulatory_enforcement_score, litigation.regulatory_enforcement_evidence, 1.0),
            ("Civil Litigation", litigation.civil_litigation_score, litigation.civil_litigation_evidence, 0.85),
            ("Bankruptcy", litigation.bankruptcy_score, litigation.bankruptcy_evidence, 0.95),
        ]
        category_scores.append(self.calculate_category_score(
            [(n, s, e, c) for n, s, e, c in litigation_signals if s > 0],
            "Litigation History"
        ))
        
        # Calculate composite score
        composite_score = self.calculate_composite_score(category_scores, weights)
        
        # Apply critical overrides
        # License issues force minimum Tier 4
        if regulatory.license_status_score < 50:
            composite_score = min(composite_score, 450)
        
        # Active disciplinary issues force minimum Tier 4
        if regulatory.disciplinary_history_score < 40:
            composite_score = min(composite_score, 450)
        
        # Recent malpractice suits force minimum Tier 3
        if litigation.malpractice_suits_score < 40:
            composite_score = min(composite_score, 600)
        
        # Assign tier
        tier = self.assign_tier(composite_score)
        
        # Identify flags
        red_flags = self.identify_red_flags(regulatory, litigation, stability, direct, profession)
        green_flags = self.identify_green_flags(network, regulatory, stability, practice)
        
        # Calculate signal coverage
        all_signals = [
            network.peer_ranking_score, network.client_quality_score,
            regulatory.license_status_score, regulatory.disciplinary_history_score,
            stability.tenure_score, stability.partner_stability_score,
            practice.client_review_score, practice.complaint_history_score,
            technical.tls_score, technical.email_auth_score,
            footprint.website_quality_score,
            litigation.malpractice_suits_score,
        ]
        signal_coverage = len([s for s in all_signals if s > 0]) / len(all_signals)
        
        # Calculate confidence
        confidence = min(0.95, signal_coverage * 0.9 + 0.1)
        
        # Determine decision
        decision, rationale = self.determine_decision(tier, red_flags, confidence)
        
        # Calculate premium
        base_premium, risk_adjusted, modifier = self.calculate_premium(
            profession, firm_size, revenue_size, tier,
            limit, retention, practice_modifier
        )
        
        return DSIAssessment(
            entity_name=entity_name,
            profession_type=profession,
            firm_size=firm_size,
            revenue_size=revenue_size,
            category_scores=category_scores,
            composite_score=composite_score,
            tier=tier,
            confidence=confidence,
            red_flags=red_flags,
            green_flags=green_flags,
            decision=decision,
            decision_rationale=rationale,
            base_premium=base_premium,
            risk_adjusted_premium=risk_adjusted,
            premium_modifier=modifier,
            assessment_date=datetime.now(),
            signal_coverage=signal_coverage,
            data_quality_score=confidence
        )


# =============================================================================
# SIGNAL COLLECTION GUIDANCE
# =============================================================================

SIGNAL_SOURCES = """
DSI Professional Indemnity - Signal Collection Sources
========================================================

TYPE 1: NETWORK AUTHORITY
-------------------------
- Chambers & Partners rankings: chambers.com
- Legal 500: legal500.com
- Best Lawyers: bestlawyers.com
- Martindale-Hubbell: martindale.com
- Super Lawyers: superlawyers.com
- LinkedIn connections to quality clients
- Court filings showing client representations
- Published case studies on firm website
- Insurance defense panel directories
- Bank approved attorney lists

TYPE 2: TECHNICAL INFRASTRUCTURE
--------------------------------
- SSL Labs: ssllabs.com/ssltest
- SecurityHeaders: securityheaders.com
- DNS lookups for SPF/DMARC/DKIM
- Shodan/Censys for exposed services
- Have I Been Pwned for breach history
- BitSight/SecurityScorecard if available

TYPE 5: CORPORATE FOOTPRINT
---------------------------
- Firm website analysis
- Attorney/professional bio pages
- Practice area descriptions
- News/publications sections
- LinkedIn company page
- Glassdoor reviews (staff retention)
- Indeed job postings (growth/churn)

TYPE 6: PUBLIC RECORDS
----------------------
Law Firms:
- State bar disciplinary records (each jurisdiction)
- PACER federal court records
- State court records (varies by state)
- Westlaw/Lexis attorney profiles

Accounting Firms:
- AICPA peer review directory: peerreview.aicpa.org
- PCAOB registration: pcaobus.org
- SEC EDGAR for audit client issues
- State board disciplinary records

Architecture/Engineering:
- NCARB certificate status (architects)
- State PE board records (engineers)
- AIA membership directory
- NSPE directory

Real Estate:
- State RE commission lookup
- ARELLO database
- Realtor.com agent profiles
- Zillow agent reviews

TYPE 7: DIRECT INQUIRY (6 MAX)
------------------------------
1. Pending/threatened malpractice claims?
2. Pending disciplinary proceedings?
3. PI coverage declined/non-renewed (3 years)?
4. Significant practice area changes (2 years)?
5. Merger/acquisition/spin-off (2 years)?
6. Major client loss (>25% revenue)?
"""


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

def create_sample_assessment():
    """Create a sample DSI assessment for demonstration."""
    
    engine = DSIProfessionalIndemnityEngine()
    
    # Sample law firm signals
    network = NetworkAuthoritySignals(
        peer_ranking_score=75,
        peer_ranking_evidence="Chambers Band 3 in Corporate M&A",
        client_quality_score=80,
        client_quality_evidence="Represents Fortune 500 companies",
        referral_network_score=70,
        referral_network_evidence="Active referral relationships with Big 4",
        association_leadership_score=65,
        association_leadership_evidence="Partner serves on ABA committee",
        thought_leadership_score=70,
        thought_leadership_evidence="Regular CLE presentations, law review articles"
    )
    
    regulatory = RegulatoryStandingSignals(
        license_status_score=95,
        license_status_evidence="All attorneys in good standing",
        disciplinary_history_score=90,
        disciplinary_history_evidence="One private admonition 8 years ago",
        malpractice_record_score=85,
        malpractice_record_evidence="No malpractice judgments on record",
        ce_compliance_score=100,
        ce_compliance_evidence="All CLE requirements current",
        specialty_certification_score=70,
        specialty_certification_evidence="Two partners board certified"
    )
    
    stability = FirmStabilitySignals(
        tenure_score=85,
        tenure_evidence="Founded 1998, 27 years in practice",
        partner_stability_score=80,
        partner_stability_evidence="Average partner tenure 12 years",
        staff_retention_score=75,
        staff_retention_evidence="Glassdoor: 4.1/5.0 rating",
        office_stability_score=90,
        office_stability_evidence="Same primary location since 2005",
        financial_stability_score=80,
        financial_stability_evidence="Steady growth, no financial distress signals"
    )
    
    practice = PracticeQualitySignals(
        outcome_patterns_score=75,
        outcome_patterns_evidence="Above-average case outcomes",
        client_review_score=80,
        client_review_evidence="4.5/5.0 average on legal platforms",
        work_quality_score=75,
        work_quality_evidence="Well-regarded brief writing",
        fee_dispute_score=90,
        fee_dispute_evidence="One fee arbitration 5 years ago",
        complaint_history_score=95,
        complaint_history_evidence="No bar complaints in 10 years"
    )
    
    technical = TechnicalInfrastructureSignals(
        tls_score=85,
        tls_evidence="TLS 1.3, Grade A-",
        email_auth_score=80,
        email_auth_evidence="SPF, DKIM configured; DMARC at p=quarantine",
        security_headers_score=70,
        security_headers_evidence="Most headers present, missing CSP",
        breach_history_score=100,
        breach_history_evidence="No breaches identified"
    )
    
    footprint = CorporateFootprintSignals(
        website_quality_score=80,
        website_quality_evidence="Professional, modern website",
        bio_completeness_score=85,
        bio_completeness_evidence="Detailed attorney bios with experience",
        practice_clarity_score=80,
        practice_clarity_evidence="Clear practice area descriptions",
        publications_score=70,
        publications_evidence="Regular blog posts, some articles"
    )
    
    litigation = LitigationHistorySignals(
        malpractice_suits_score=85,
        malpractice_suits_evidence="One suit 6 years ago, dismissed",
        fee_disputes_score=90,
        fee_disputes_evidence="Minimal fee dispute history",
        regulatory_enforcement_score=95,
        regulatory_enforcement_evidence="No regulatory actions",
        civil_litigation_score=90,
        civil_litigation_evidence="No civil suits as defendant",
        bankruptcy_score=100,
        bankruptcy_evidence="No bankruptcy history"
    )
    
    direct = DirectInquirySignals(
        pending_claims=False,
        disciplinary_pending=False,
        coverage_declined=False,
        practice_area_change=False,
        merger_activity=False,
        major_client_loss=False
    )
    
    # Run assessment
    assessment = engine.assess(
        entity_name="Smith & Associates LLP",
        profession=ProfessionType.LAW_FIRM,
        firm_size=FirmSize.MEDIUM,
        revenue_size=RevenueSize.R_5M_25M,
        network=network,
        regulatory=regulatory,
        stability=stability,
        practice=practice,
        technical=technical,
        footprint=footprint,
        litigation=litigation,
        direct=direct,
        limit=2_000_000,
        retention=100_000,
        practice_modifier=LEGAL_PRACTICE_RISK_MODIFIERS[LegalPracticeArea.CORPORATE_MA]
    )
    
    return assessment


def print_assessment(assessment: DSIAssessment):
    """Print formatted assessment output."""
    
    print("=" * 70)
    print(f"DSI PROFESSIONAL INDEMNITY ASSESSMENT")
    print("=" * 70)
    print(f"\nEntity: {assessment.entity_name}")
    print(f"Profession: {assessment.profession_type.value}")
    print(f"Size: {assessment.firm_size.value} | Revenue: {assessment.revenue_size.value}")
    print(f"\n{'─' * 70}")
    print(f"COMPOSITE SCORE: {assessment.composite_score:.0f}/1000")
    print(f"TIER: {assessment.tier.name} ({assessment.tier.value})")
    print(f"CONFIDENCE: {assessment.confidence:.0%}")
    print(f"{'─' * 70}")
    
    print("\nCATEGORY SCORES:")
    for cat in assessment.category_scores:
        bar = "█" * int(cat.category_score / 5) + "░" * (20 - int(cat.category_score / 5))
        print(f"  {cat.category_name:25} {cat.category_score:5.1f}/100 {bar}")
    
    print(f"\n{'─' * 70}")
    print("FLAGS:")
    
    if assessment.green_flags:
        print("\n  ✓ GREEN FLAGS:")
        for flag in assessment.green_flags[:5]:
            print(f"    • {flag}")
    
    if assessment.red_flags:
        print("\n  ⚠ RED FLAGS:")
        for flag in assessment.red_flags[:5]:
            print(f"    • {flag}")
    
    print(f"\n{'─' * 70}")
    print("DECISION:")
    print(f"  Action: {assessment.decision}")
    print(f"  Rationale: {assessment.decision_rationale}")
    
    print(f"\n{'─' * 70}")
    print("PRICING:")
    print(f"  Base Premium:     ${assessment.base_premium:,.0f}")
    print(f"  Risk Modifier:    {assessment.premium_modifier:.2f}x")
    print(f"  Adjusted Premium: ${assessment.risk_adjusted_premium:,.0f}")
    
    print(f"\n{'─' * 70}")
    print(f"Assessment Date: {assessment.assessment_date.strftime('%Y-%m-%d %H:%M')}")
    print(f"Signal Coverage: {assessment.signal_coverage:.0%}")
    print("=" * 70)


if __name__ == "__main__":
    assessment = create_sample_assessment()
    print_assessment(assessment)
