"""
Digital Signal Intelligence (DSI) - Cyber Insurance Pricing Model
==================================================================

DSI-compliant cyber insurance pricing based entirely on externally
observable signals, network authority analysis, and minimal optional
direct inquiry.

This model conforms to Foundational Principles

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

class IndustryClassification(Enum):
    """Industry classification derived from public records (SIC/NAICS)"""
    TECHNOLOGY = "technology"
    FINANCIAL_SERVICES = "financial_services"
    HEALTHCARE = "healthcare"
    RETAIL = "retail"
    MANUFACTURING = "manufacturing"
    PROFESSIONAL_SERVICES = "professional_services"
    EDUCATION = "education"
    GOVERNMENT = "government"
    ENERGY = "energy"
    OTHER = "other"


class SizeBand(Enum):
    """
    Size classification inferred from observable signals.
    
    Inference sources:
    - LinkedIn employee count
    - Job posting volume
    - Office locations
    - Public filings (if available)
    - Website complexity/scale indicators
    """
    SMALL = "small"          # Estimated <500 employees
    MEDIUM = "medium"        # Estimated 500-5,000 employees
    LARGE = "large"          # Estimated 5,000-25,000 employees
    ENTERPRISE = "enterprise" # Estimated >25,000 employees


# =============================================================================
# SIGNAL DATA STRUCTURES
# =============================================================================

@dataclass
class NetworkAuthoritySignals:
    """
    Type 1: Network Authority Signals
    
    PageRank-style signals derived from relationship analysis.
    All signals scored 0-100.
    """
    
    # Customer quality (inferred from case studies, logos, testimonials)
    customer_quality_score: float = 0.0
    customer_quality_evidence: str = ""
    
    # Partner network quality (technology partners, alliances)
    partner_quality_score: float = 0.0
    partner_quality_evidence: str = ""
    
    # Security vendor relationships (CrowdStrike, Palo Alto, etc.)
    security_vendor_score: float = 0.0
    security_vendor_evidence: str = ""
    
    # Industry body membership (FS-ISAC, sector ISACs, trade associations)
    industry_body_score: float = 0.0
    industry_body_evidence: str = ""
    
    # Certification authority (who certifies them - ISO, SOC 2 auditors)
    certification_authority_score: float = 0.0
    certification_authority_evidence: str = ""
    
    # Banking/financial relationship quality
    financial_relationship_score: float = 0.0
    financial_relationship_evidence: str = ""
    
    # Peer network centrality (position in industry graph)
    network_centrality_score: float = 0.0
    network_centrality_evidence: str = ""
    
    # Second-degree relationship quality
    second_degree_score: float = 0.0
    second_degree_evidence: str = ""


@dataclass
class TechnicalInfrastructureSignals:
    """
    Type 2: Technical Infrastructure Signals
    
    Observable technical implementation signals.
    All signals scored 0-100.
    """
    
    # TLS/SSL configuration (SSL Labs methodology)
    tls_score: float = 0.0
    tls_evidence: str = ""
    
    # Security headers (HSTS, CSP, X-Frame-Options, etc.)
    security_headers_score: float = 0.0
    security_headers_evidence: str = ""
    
    # Email authentication (SPF, DMARC, DKIM)
    email_auth_score: float = 0.0
    email_auth_evidence: str = ""
    
    # DNSSEC implementation
    dnssec_score: float = 0.0
    dnssec_evidence: str = ""
    
    # Network exposure (open ports, exposed services via Shodan/Censys)
    exposure_score: float = 0.0
    exposure_evidence: str = ""
    
    # Software currency (version fingerprinting)
    software_currency_score: float = 0.0
    software_currency_evidence: str = ""
    
    # Known vulnerabilities (CVEs for detected software versions)
    cve_exposure_score: float = 0.0
    cve_exposure_evidence: str = ""
    
    # Cloud infrastructure quality (major providers vs unknown)
    cloud_infrastructure_score: float = 0.0
    cloud_infrastructure_evidence: str = ""


@dataclass
class CorporateFootprintSignals:
    """
    Type 5: Corporate Digital Footprint Signals
    
    Signals derived from the company's own digital presence.
    All signals scored 0-100.
    """
    
    # Security page presence and quality
    security_page_score: float = 0.0
    security_page_evidence: str = ""
    
    # Privacy policy quality (NLP analysis)
    privacy_policy_score: float = 0.0
    privacy_policy_evidence: str = ""
    
    # Security.txt presence and completeness
    security_txt_score: float = 0.0
    security_txt_evidence: str = ""
    
    # Bug bounty program presence (HackerOne, Bugcrowd)
    bug_bounty_score: float = 0.0
    bug_bounty_evidence: str = ""
    
    # Security-related job postings (CISO, security engineers)
    security_hiring_score: float = 0.0
    security_hiring_evidence: str = ""
    
    # Technical blog/content quality
    technical_content_score: float = 0.0
    technical_content_evidence: str = ""
    
    # Developer/API documentation presence
    developer_resources_score: float = 0.0
    developer_resources_evidence: str = ""
    
    # Leadership visibility (security leadership profiles)
    security_leadership_score: float = 0.0
    security_leadership_evidence: str = ""


@dataclass
class PublicRecordSignals:
    """
    Type 6: Public Record Signals
    
    Signals from regulatory filings and public databases.
    All signals scored 0-100.
    """
    
    # Breach history (HHS, state AG, public disclosures)
    breach_history_score: float = 0.0
    breach_history_evidence: str = ""
    
    # Regulatory actions (FTC, state AG enforcement)
    regulatory_action_score: float = 0.0
    regulatory_action_evidence: str = ""
    
    # Litigation history (data breach lawsuits)
    litigation_score: float = 0.0
    litigation_evidence: str = ""
    
    # Credential exposure (HaveIBeenPwned corporate domain)
    credential_exposure_score: float = 0.0
    credential_exposure_evidence: str = ""
    
    # Dark web exposure (leaked data, credentials for sale)
    dark_web_score: float = 0.0
    dark_web_evidence: str = ""


@dataclass
class StructuredDataSignals:
    """
    Type 4: Structured Data Feed Signals
    
    Third-party ratings and scores used as authority signals.
    All signals scored 0-100.
    """
    
    # Security rating (BitSight, SecurityScorecard if available)
    security_rating_score: float = 0.0
    security_rating_evidence: str = ""
    
    # ESG cyber/privacy component (MSCI, Sustainalytics)
    esg_cyber_score: float = 0.0
    esg_cyber_evidence: str = ""
    
    # Credit rating (as proxy for organizational quality)
    credit_rating_score: float = 0.0
    credit_rating_evidence: str = ""


@dataclass
class DirectInquirySignals:
    """
    Type 7: Direct Inquiry Signals (Optional)
    
    Minimal, critical questions - maximum 8 for cyber.
    These are OPTIONAL - model functions without them.
    """
    
    # All fields are Optional - None means not provided
    
    mfa_enabled: Optional[bool] = None
    # "Is multi-factor authentication enabled for all remote access?"
    
    security_training: Optional[bool] = None
    # "Do all employees complete annual cyber security training?"
    
    phi_handler: Optional[bool] = None
    # "Do you process Protected Health Information (PHI)?"
    
    pci_scope: Optional[bool] = None
    # "Do you store payment card data (PCI scope)?"
    
    incident_response_plan: Optional[bool] = None
    # "Do you have a documented incident response plan?"
    
    edr_deployed: Optional[bool] = None
    # "Is endpoint detection and response (EDR) deployed on all endpoints?"
    
    immutable_backups: Optional[bool] = None
    # "Are backups maintained offline or immutable?"
    
    recent_incident: Optional[bool] = None
    # "Have you experienced a material cyber incident in the past 3 years?"


# =============================================================================
# COMPANY PROFILE (Observable Data Only)
# =============================================================================

@dataclass
class CyberCompanyProfile:
    """
    Company profile constructed entirely from observable data.
    
    No self-reported operational data, no questionnaire fields.
    """
    
    # Identifiers
    company_name: str
    primary_domain: str
    
    # Observable from public records/registries
    industry: IndustryClassification
    country: str
    is_publicly_traded: bool = False
    
    # Inferred from observable signals
    size_band: SizeBand = SizeBand.MEDIUM
    size_inference_confidence: float = 0.5
    
    # Regulatory context (inferred from industry + observable indicators)
    likely_hipaa_scope: bool = False  # Healthcare industry
    likely_pci_scope: bool = False    # E-commerce indicators
    likely_financial_regulation: bool = False  # Financial services
    
    # All signal categories
    network_authority: NetworkAuthoritySignals = field(default_factory=NetworkAuthoritySignals)
    technical_infrastructure: TechnicalInfrastructureSignals = field(default_factory=TechnicalInfrastructureSignals)
    corporate_footprint: CorporateFootprintSignals = field(default_factory=CorporateFootprintSignals)
    public_records: PublicRecordSignals = field(default_factory=PublicRecordSignals)
    structured_data: StructuredDataSignals = field(default_factory=StructuredDataSignals)
    direct_inquiry: DirectInquirySignals = field(default_factory=DirectInquirySignals)


# =============================================================================
# SCORING ENGINE
# =============================================================================

class CyberDSIScorer:
    """
    Calculates composite scores from individual signals.
    
    Follows DSI Principle 9: Signal → Score → Tier → Price
    """
    
    # Category weights for cyber insurance
    # Technical infrastructure and public records are critical for cyber
    CATEGORY_WEIGHTS = {
        "network_authority": 0.15,
        "technical_infrastructure": 0.35,  # Critical for cyber
        "corporate_footprint": 0.15,
        "public_records": 0.25,            # Breach history critical
        "structured_data": 0.10,
    }
    
    # Signal weights within each category
    SIGNAL_WEIGHTS = {
        "network_authority": {
            "customer_quality": 0.15,
            "partner_quality": 0.10,
            "security_vendor": 0.20,        # Important for cyber
            "industry_body": 0.15,
            "certification_authority": 0.15,
            "financial_relationship": 0.05,
            "network_centrality": 0.10,
            "second_degree": 0.10,
        },
        "technical_infrastructure": {
            "tls": 0.15,
            "security_headers": 0.12,
            "email_auth": 0.12,
            "dnssec": 0.06,
            "exposure": 0.20,               # Critical - attack surface
            "software_currency": 0.12,
            "cve_exposure": 0.18,           # Critical - known vulns
            "cloud_infrastructure": 0.05,
        },
        "corporate_footprint": {
            "security_page": 0.15,
            "privacy_policy": 0.10,
            "security_txt": 0.10,
            "bug_bounty": 0.20,             # Strong security signal
            "security_hiring": 0.15,
            "technical_content": 0.10,
            "developer_resources": 0.05,
            "security_leadership": 0.15,
        },
        "public_records": {
            "breach_history": 0.35,         # Critical predictor
            "regulatory_action": 0.20,
            "litigation": 0.15,
            "credential_exposure": 0.20,
            "dark_web": 0.10,
        },
        "structured_data": {
            "security_rating": 0.50,
            "esg_cyber": 0.25,
            "credit_rating": 0.25,
        },
    }
    
    def calculate_category_score(
        self, 
        signals: object, 
        category: str
    ) -> Tuple[float, int, int]:
        """
        Calculate weighted average score for a signal category.
        
        Returns: (score, signals_available, signals_total)
        """
        weights = self.SIGNAL_WEIGHTS.get(category, {})
        
        weighted_sum = 0.0
        weight_sum = 0.0
        signals_available = 0
        signals_total = len(weights)
        
        for signal_name, weight in weights.items():
            # Get the score attribute
            score_attr = f"{signal_name}_score"
            if hasattr(signals, score_attr):
                score = getattr(signals, score_attr)
                if score > 0:  # Signal is available
                    weighted_sum += score * weight
                    weight_sum += weight
                    signals_available += 1
        
        if weight_sum > 0:
            category_score = weighted_sum / weight_sum
        else:
            category_score = 0.0
        
        return category_score, signals_available, signals_total
    
    def calculate_composite_score(
        self, 
        company: CyberCompanyProfile
    ) -> Tuple[float, float, Dict[str, float]]:
        """
        Calculate overall composite score.
        
        Returns: (composite_score 0-1000, confidence 0-1, category_scores)
        """
        category_signals = {
            "network_authority": company.network_authority,
            "technical_infrastructure": company.technical_infrastructure,
            "corporate_footprint": company.corporate_footprint,
            "public_records": company.public_records,
            "structured_data": company.structured_data,
        }
        
        category_scores = {}
        total_signals_available = 0
        total_signals_possible = 0
        weighted_composite = 0.0
        weight_sum = 0.0
        
        for category, signals in category_signals.items():
            score, available, total = self.calculate_category_score(signals, category)
            category_scores[category] = score
            total_signals_available += available
            total_signals_possible += total
            
            if available > 0:  # Only include categories with data
                weight = self.CATEGORY_WEIGHTS[category]
                weighted_composite += score * weight
                weight_sum += weight
        
        # Calculate composite (0-100 scale from signals, convert to 0-1000)
        if weight_sum > 0:
            composite_100 = weighted_composite / weight_sum
            composite_1000 = composite_100 * 10
        else:
            composite_1000 = 0.0
        
        # Calculate confidence based on signal coverage
        if total_signals_possible > 0:
            coverage = total_signals_available / total_signals_possible
            if coverage >= 0.85:
                confidence = 0.95
            elif coverage >= 0.70:
                confidence = 0.75 + (coverage - 0.70) * (0.20 / 0.15)
            elif coverage >= 0.55:
                confidence = 0.60 + (coverage - 0.55) * (0.15 / 0.15)
            else:
                confidence = coverage / 0.55 * 0.60
        else:
            confidence = 0.0
        
        return composite_1000, confidence, category_scores
    
    def apply_direct_inquiry_adjustment(
        self,
        composite_score: float,
        inquiry: DirectInquirySignals
    ) -> Tuple[float, List[str]]:
        """
        Apply adjustments from optional direct inquiry responses.
        
        These are additive/subtractive adjustments, not multipliers.
        Returns: (adjusted_score, adjustment_notes)
        """
        adjustment = 0.0
        notes = []
        
        # Positive signals
        if inquiry.mfa_enabled is True:
            adjustment += 30
            notes.append("MFA enabled: +30")
        elif inquiry.mfa_enabled is False:
            adjustment -= 50
            notes.append("MFA not enabled: -50")
        
        if inquiry.security_training is True:
            adjustment += 20
            notes.append("Security training: +20")
        
        if inquiry.incident_response_plan is True:
            adjustment += 25
            notes.append("IR plan documented: +25")
        
        if inquiry.edr_deployed is True:
            adjustment += 30
            notes.append("EDR deployed: +30")
        
        if inquiry.immutable_backups is True:
            adjustment += 35
            notes.append("Immutable backups: +35")
        
        # Negative/risk signals
        if inquiry.recent_incident is True:
            adjustment -= 100
            notes.append("Recent incident disclosed: -100")
        
        # Regulatory exposure (adjusts risk, not score directly)
        # These are noted but handled in pricing
        if inquiry.phi_handler is True:
            notes.append("PHI handler: regulatory exposure noted")
        
        if inquiry.pci_scope is True:
            notes.append("PCI scope: regulatory exposure noted")
        
        adjusted_score = max(0, min(1000, composite_score + adjustment))
        
        return adjusted_score, notes


# =============================================================================
# TIER ASSIGNMENT
# =============================================================================

class CyberTierAssignment:
    """
    Assigns risk tier based on composite score.
    
    Standard DSI five-tier structure.
    """
    
    TIER_THRESHOLDS = {
        1: 800,   # 800-1000: Preferred
        2: 650,   # 650-799: Standard
        3: 500,   # 500-649: Elevated
        4: 350,   # 350-499: High Risk
        5: 0,     # 0-349: Critical
    }
    
    TIER_LABELS = {
        1: "Preferred",
        2: "Standard", 
        3: "Elevated",
        4: "High Risk",
        5: "Critical",
    }
    
    TIER_ACTIONS = {
        1: "Auto-approve at preferred pricing",
        2: "Auto-approve at standard pricing",
        3: "Auto-approve with conditions",
        4: "Manual review required",
        5: "Decline or senior review required",
    }
    
    @classmethod
    def assign_tier(cls, composite_score: float) -> Tuple[int, str, str]:
        """
        Assign tier based on score.
        
        Returns: (tier_number, tier_label, tier_action)
        """
        for tier in range(1, 6):
            if composite_score >= cls.TIER_THRESHOLDS[tier]:
                return tier, cls.TIER_LABELS[tier], cls.TIER_ACTIONS[tier]
        
        return 5, cls.TIER_LABELS[5], cls.TIER_ACTIONS[5]
    
    @classmethod
    def check_critical_overrides(
        cls,
        company: CyberCompanyProfile,
        tier: int
    ) -> Tuple[int, Optional[str]]:
        """
        Check for critical signals that override tier assignment.
        
        Returns: (adjusted_tier, override_reason)
        """
        # Critical vulnerability exposure forces Tier 4+
        tech = company.technical_infrastructure
        if tech.cve_exposure_score > 0 and tech.cve_exposure_score < 30:
            if tier < 4:
                return 4, "Critical CVE exposure detected"
        
        if tech.exposure_score > 0 and tech.exposure_score < 30:
            if tier < 4:
                return 4, "Critical network exposure detected"
        
        # Recent breach forces Tier 4+
        records = company.public_records
        if records.breach_history_score > 0 and records.breach_history_score < 40:
            if tier < 4:
                return 4, "Recent breach history"
        
        # Dark web exposure forces Tier 4+
        if records.dark_web_score > 0 and records.dark_web_score < 30:
            if tier < 4:
                return 4, "Active dark web exposure"
        
        # Disclosed recent incident (from direct inquiry) forces Tier 4+
        if company.direct_inquiry.recent_incident is True:
            if tier < 4:
                return 4, "Recent incident disclosed"
        
        return tier, None


# =============================================================================
# PRICING ENGINE
# =============================================================================

class CyberPricingEngine:
    """
    Calculates premium based on tier, industry, and size.
    
    Follows DSI Principle 9: Simple tier-based pricing.
    """
    
    # Base annual premium by tier (for $1M limit, medium-sized company)
    TIER_BASE_PREMIUM = {
        1: 8000,    # Preferred
        2: 12000,   # Standard
        3: 18000,   # Elevated
        4: 30000,   # High Risk
        5: 50000,   # Critical (if bound at all)
    }
    
    # Industry multipliers
    INDUSTRY_MULTIPLIERS = {
        IndustryClassification.HEALTHCARE: 1.50,
        IndustryClassification.FINANCIAL_SERVICES: 1.40,
        IndustryClassification.RETAIL: 1.25,
        IndustryClassification.TECHNOLOGY: 1.15,
        IndustryClassification.ENERGY: 1.20,
        IndustryClassification.PROFESSIONAL_SERVICES: 1.10,
        IndustryClassification.EDUCATION: 1.05,
        IndustryClassification.MANUFACTURING: 0.95,
        IndustryClassification.GOVERNMENT: 0.90,
        IndustryClassification.OTHER: 1.00,
    }
    
    # Size multipliers
    SIZE_MULTIPLIERS = {
        SizeBand.SMALL: 0.60,
        SizeBand.MEDIUM: 1.00,
        SizeBand.LARGE: 2.50,
        SizeBand.ENTERPRISE: 5.00,
    }
    
    # Limit factors (premium scales sub-linearly with limit)
    LIMIT_FACTORS = {
        1_000_000: 1.00,
        2_000_000: 1.70,
        5_000_000: 3.20,
        10_000_000: 5.00,
        25_000_000: 9.00,
        50_000_000: 14.00,
        100_000_000: 22.00,
    }
    
    @classmethod
    def calculate_premium(
        cls,
        tier: int,
        industry: IndustryClassification,
        size: SizeBand,
        limit: float,
        phi_handler: bool = False,
        pci_scope: bool = False,
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate annual premium.
        
        Returns: (premium, pricing_components)
        """
        # Base premium for tier
        base = cls.TIER_BASE_PREMIUM[tier]
        
        # Industry adjustment
        industry_mult = cls.INDUSTRY_MULTIPLIERS.get(industry, 1.0)
        
        # Size adjustment
        size_mult = cls.SIZE_MULTIPLIERS.get(size, 1.0)
        
        # Limit factor
        limit_factor = 1.0
        for threshold, factor in sorted(cls.LIMIT_FACTORS.items()):
            if limit >= threshold:
                limit_factor = factor
        
        # Regulatory exposure adjustments (from direct inquiry if provided)
        regulatory_mult = 1.0
        if phi_handler:
            regulatory_mult *= 1.30
        if pci_scope:
            regulatory_mult *= 1.20
        
        # Calculate premium
        premium = base * industry_mult * size_mult * limit_factor * regulatory_mult
        
        # Minimum premium
        minimum = 5000
        premium = max(premium, minimum)
        
        components = {
            "base_premium": base,
            "industry_multiplier": industry_mult,
            "size_multiplier": size_mult,
            "limit_factor": limit_factor,
            "regulatory_multiplier": regulatory_mult,
            "final_premium": premium,
        }
        
        return premium, components
    
    @classmethod
    def recommend_limit(
        cls,
        size: SizeBand,
        industry: IndustryClassification,
    ) -> float:
        """
        Recommend appropriate limit based on observable characteristics.
        """
        base_limits = {
            SizeBand.SMALL: 1_000_000,
            SizeBand.MEDIUM: 5_000_000,
            SizeBand.LARGE: 25_000_000,
            SizeBand.ENTERPRISE: 100_000_000,
        }
        
        base = base_limits.get(size, 5_000_000)
        
        # Adjust for high-risk industries
        if industry in [IndustryClassification.HEALTHCARE, 
                        IndustryClassification.FINANCIAL_SERVICES,
                        IndustryClassification.RETAIL]:
            base = base * 1.5
        
        # Round to standard limit
        standard_limits = [1_000_000, 2_000_000, 5_000_000, 10_000_000, 
                          25_000_000, 50_000_000, 100_000_000]
        
        return min(standard_limits, key=lambda x: abs(x - base))
    
    @classmethod
    def recommend_retention(cls, limit: float, tier: int) -> float:
        """
        Recommend appropriate retention/deductible.
        """
        # Base retention as percentage of limit
        base_pct = {
            1: 0.01,   # 1% for preferred
            2: 0.02,   # 2% for standard
            3: 0.03,   # 3% for elevated
            4: 0.05,   # 5% for high risk
            5: 0.10,   # 10% for critical
        }
        
        retention = limit * base_pct.get(tier, 0.02)
        
        # Minimum $10k, maximum $500k
        retention = max(10_000, min(500_000, retention))
        
        # Round to standard amounts
        if retention <= 25_000:
            return 25_000
        elif retention <= 50_000:
            return 50_000
        elif retention <= 100_000:
            return 100_000
        elif retention <= 250_000:
            return 250_000
        else:
            return 500_000


# =============================================================================
# DECISION ENGINE
# =============================================================================

@dataclass
class CyberUnderwritingDecision:
    """Complete underwriting decision output"""
    
    # Company identification
    company_name: str
    domain: str
    
    # Classification
    industry: str
    size_band: str
    
    # Scoring
    composite_score: float
    confidence: float
    category_scores: Dict[str, float]
    
    # Tier assignment
    tier: int
    tier_label: str
    tier_action: str
    tier_override_reason: Optional[str]
    
    # Pricing
    recommended_limit: float
    recommended_retention: float
    annual_premium: float
    pricing_components: Dict[str, float]
    
    # Decision
    decision: str  # APPROVE, APPROVE_WITH_CONDITIONS, REFER, DECLINE
    conditions: List[str]
    reasoning: str
    
    # Direct inquiry impact
    direct_inquiry_applied: bool
    direct_inquiry_adjustments: List[str]
    
    # Metadata
    signals_available: int
    signals_total: int
    assessment_timestamp: str


class CyberDecisionEngine:
    """
    Generates final underwriting decision.
    """
    
    @classmethod
    def generate_conditions(cls, tier: int, company: CyberCompanyProfile) -> List[str]:
        """Generate conditions based on tier and signals."""
        conditions = []
        
        if tier >= 3:
            conditions.append("Annual security assessment required")
        
        if tier >= 3:
            conditions.append("Incident response plan must be documented")
        
        # Check for specific weak signals
        tech = company.technical_infrastructure
        if tech.email_auth_score > 0 and tech.email_auth_score < 60:
            conditions.append("Implement DMARC enforcement within 90 days")
        
        if tech.cve_exposure_score > 0 and tech.cve_exposure_score < 60:
            conditions.append("Remediate critical/high CVEs within 30 days")
        
        if company.direct_inquiry.mfa_enabled is False:
            conditions.append("MFA required for all remote access within 60 days")
        
        if company.direct_inquiry.edr_deployed is False and tier >= 3:
            conditions.append("EDR deployment required within 90 days")
        
        if tier >= 4:
            conditions.append("Quarterly security reviews required")
            conditions.append("30-day breach notification mandatory")
        
        # Always require notification
        conditions.append("Notify insurer of any security incidents within 72 hours")
        
        return conditions
    
    @classmethod
    def generate_decision(
        cls,
        tier: int,
        confidence: float,
        composite_score: float,
        company: CyberCompanyProfile,
    ) -> Tuple[str, str]:
        """
        Generate decision and reasoning.
        
        Returns: (decision, reasoning)
        """
        # Low confidence forces referral regardless of score
        if confidence < 0.60:
            return (
                "REFER",
                f"Insufficient signal coverage (confidence: {confidence:.0%}). "
                f"Manual underwriting required to supplement DSI assessment."
            )
        
        # Tier-based decisions
        if tier == 1:
            return (
                "APPROVE",
                f"Excellent security posture (score: {composite_score:.0f}/1000). "
                f"Strong network authority, minimal vulnerabilities, no adverse history. "
                f"Qualifies for preferred pricing with auto-approval."
            )
        
        elif tier == 2:
            return (
                "APPROVE",
                f"Good security posture (score: {composite_score:.0f}/1000). "
                f"Adequate controls and acceptable risk profile. "
                f"Qualifies for standard pricing with auto-approval."
            )
        
        elif tier == 3:
            return (
                "APPROVE_WITH_CONDITIONS",
                f"Moderate security posture (score: {composite_score:.0f}/1000). "
                f"Some gaps identified requiring conditions. "
                f"Approved with binding conditions."
            )
        
        elif tier == 4:
            # Check specific reasons for Tier 4
            reasons = []
            if company.public_records.breach_history_score > 0 and \
               company.public_records.breach_history_score < 50:
                reasons.append("adverse breach history")
            if company.technical_infrastructure.cve_exposure_score > 0 and \
               company.technical_infrastructure.cve_exposure_score < 50:
                reasons.append("significant vulnerability exposure")
            if company.direct_inquiry.recent_incident is True:
                reasons.append("recent security incident")
            
            reason_str = ", ".join(reasons) if reasons else "elevated risk indicators"
            
            return (
                "REFER",
                f"High risk profile (score: {composite_score:.0f}/1000). "
                f"Concerns include: {reason_str}. "
                f"Manual underwriter review required before binding."
            )
        
        else:  # Tier 5
            return (
                "DECLINE",
                f"Critical risk profile (score: {composite_score:.0f}/1000). "
                f"Risk exceeds appetite. Senior review required for any exception."
            )


# =============================================================================
# MAIN PRICING MODEL
# =============================================================================

class CyberDSIPricingModel:
    """
    Complete DSI Cyber Insurance Pricing Model.
    
    Conforms to DSI Principles v1.0.
    """
    
    def __init__(self):
        self.scorer = CyberDSIScorer()
    
    def assess(
        self,
        company: CyberCompanyProfile,
        requested_limit: Optional[float] = None,
    ) -> CyberUnderwritingDecision:
        """
        Perform complete DSI assessment and pricing.
        
        Args:
            company: Company profile with all observable signals
            requested_limit: Specific limit requested (optional)
        
        Returns:
            Complete underwriting decision
        """
        # Step 1: Calculate composite score
        composite, confidence, category_scores = self.scorer.calculate_composite_score(company)
        
        # Step 2: Apply direct inquiry adjustments (if provided)
        adjusted_composite, inquiry_notes = self.scorer.apply_direct_inquiry_adjustment(
            composite, company.direct_inquiry
        )
        direct_inquiry_applied = len(inquiry_notes) > 0
        
        # Step 3: Assign tier
        tier, tier_label, tier_action = CyberTierAssignment.assign_tier(adjusted_composite)
        
        # Step 4: Check for critical overrides
        tier, override_reason = CyberTierAssignment.check_critical_overrides(company, tier)
        if override_reason:
            tier_label = CyberTierAssignment.TIER_LABELS[tier]
            tier_action = CyberTierAssignment.TIER_ACTIONS[tier]
        
        # Step 5: Determine limit and retention
        if requested_limit:
            limit = requested_limit
        else:
            limit = CyberPricingEngine.recommend_limit(company.size_band, company.industry)
        
        retention = CyberPricingEngine.recommend_retention(limit, tier)
        
        # Step 6: Calculate premium
        phi_handler = company.direct_inquiry.phi_handler or company.likely_hipaa_scope
        pci_scope = company.direct_inquiry.pci_scope or company.likely_pci_scope
        
        premium, pricing_components = CyberPricingEngine.calculate_premium(
            tier=tier,
            industry=company.industry,
            size=company.size_band,
            limit=limit,
            phi_handler=phi_handler,
            pci_scope=pci_scope,
        )
        
        # Step 7: Generate decision and conditions
        decision, reasoning = CyberDecisionEngine.generate_decision(
            tier, confidence, adjusted_composite, company
        )
        
        conditions = CyberDecisionEngine.generate_conditions(tier, company)
        
        # Step 8: Calculate signal coverage
        total_signals = 27  # Total defined signals across categories
        signals_available = sum(
            1 for cat in [company.network_authority, company.technical_infrastructure,
                         company.corporate_footprint, company.public_records,
                         company.structured_data]
            for attr in dir(cat)
            if attr.endswith('_score') and getattr(cat, attr, 0) > 0
        )
        
        return CyberUnderwritingDecision(
            company_name=company.company_name,
            domain=company.primary_domain,
            industry=company.industry.value,
            size_band=company.size_band.value,
            composite_score=adjusted_composite,
            confidence=confidence,
            category_scores=category_scores,
            tier=tier,
            tier_label=tier_label,
            tier_action=tier_action,
            tier_override_reason=override_reason,
            recommended_limit=limit,
            recommended_retention=retention,
            annual_premium=premium,
            pricing_components=pricing_components,
            decision=decision,
            conditions=conditions,
            reasoning=reasoning,
            direct_inquiry_applied=direct_inquiry_applied,
            direct_inquiry_adjustments=inquiry_notes,
            signals_available=signals_available,
            signals_total=total_signals,
            assessment_timestamp=datetime.now().isoformat(),
        )


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    
    print("=" * 80)
    print("DSI CYBER INSURANCE PRICING MODEL v2.0")
    print("Conforming to DSI Principles v1.0")
    print("=" * 80)
    
    # Example 1: Strong security posture (observable signals only)
    print("\n" + "-" * 80)
    print("EXAMPLE 1: Technology Company - Strong Security Posture")
    print("-" * 80)
    
    strong_company = CyberCompanyProfile(
        company_name="SecureTech Corp",
        primary_domain="securetech.com",
        industry=IndustryClassification.TECHNOLOGY,
        country="US",
        is_publicly_traded=True,
        size_band=SizeBand.LARGE,
        size_inference_confidence=0.85,
        
        network_authority=NetworkAuthoritySignals(
            customer_quality_score=88,
            customer_quality_evidence="Fortune 500 customers visible in case studies",
            partner_quality_score=85,
            partner_quality_evidence="AWS, Microsoft, Google partnerships",
            security_vendor_score=92,
            security_vendor_evidence="CrowdStrike, Palo Alto partnerships visible",
            industry_body_score=90,
            industry_body_evidence="FS-ISAC member, Cloud Security Alliance",
            certification_authority_score=95,
            certification_authority_evidence="SOC 2 Type II, ISO 27001 visible",
            financial_relationship_score=80,
            financial_relationship_evidence="Major bank credit facility announced",
            network_centrality_score=85,
            network_centrality_evidence="Central node in tech security network",
            second_degree_score=82,
            second_degree_evidence="Partners' partners are high-quality",
        ),
        
        technical_infrastructure=TechnicalInfrastructureSignals(
            tls_score=98,
            tls_evidence="A+ SSL Labs rating",
            security_headers_score=92,
            security_headers_evidence="HSTS, CSP, all major headers present",
            email_auth_score=95,
            email_auth_evidence="SPF, DKIM, DMARC with p=reject",
            dnssec_score=85,
            dnssec_evidence="DNSSEC fully implemented",
            exposure_score=90,
            exposure_evidence="Minimal exposed services, no admin panels",
            software_currency_score=88,
            software_currency_evidence="Current versions detected",
            cve_exposure_score=92,
            cve_exposure_evidence="No critical/high CVEs detected",
            cloud_infrastructure_score=95,
            cloud_infrastructure_evidence="AWS/Azure enterprise deployment",
        ),
        
        corporate_footprint=CorporateFootprintSignals(
            security_page_score=95,
            security_page_evidence="Comprehensive security page with certifications",
            privacy_policy_score=90,
            privacy_policy_evidence="GDPR-compliant, detailed policy",
            security_txt_score=100,
            security_txt_evidence="security.txt present with all fields",
            bug_bounty_score=95,
            bug_bounty_evidence="Active HackerOne program, responsive",
            security_hiring_score=85,
            security_hiring_evidence="CISO, security engineers actively hiring",
            technical_content_score=80,
            technical_content_evidence="Active security blog",
            developer_resources_score=85,
            developer_resources_evidence="Comprehensive API documentation",
            security_leadership_score=90,
            security_leadership_evidence="CISO profile visible, conference speaker",
        ),
        
        public_records=PublicRecordSignals(
            breach_history_score=100,
            breach_history_evidence="No breaches found in public records",
            regulatory_action_score=100,
            regulatory_action_evidence="No enforcement actions",
            litigation_score=95,
            litigation_evidence="No data breach litigation",
            credential_exposure_score=85,
            credential_exposure_evidence="Minor historical exposure, resolved",
            dark_web_score=90,
            dark_web_evidence="No active exposure detected",
        ),
        
        structured_data=StructuredDataSignals(
            security_rating_score=88,
            security_rating_evidence="BitSight 750+",
            esg_cyber_score=82,
            esg_cyber_evidence="Strong MSCI cyber/privacy score",
            credit_rating_score=85,
            credit_rating_evidence="Investment grade rating",
        ),
        
        # Optional direct inquiry - all positive
        direct_inquiry=DirectInquirySignals(
            mfa_enabled=True,
            security_training=True,
            phi_handler=False,
            pci_scope=False,
            incident_response_plan=True,
            edr_deployed=True,
            immutable_backups=True,
            recent_incident=False,
        ),
    )
    
    model = CyberDSIPricingModel()
    decision = model.assess(strong_company)
    
    print(f"\nCompany: {decision.company_name}")
    print(f"Domain: {decision.domain}")
    print(f"Industry: {decision.industry.upper()}")
    print(f"Size: {decision.size_band.upper()}")
    
    print(f"\n--- SCORING ---")
    print(f"Composite Score: {decision.composite_score:.0f}/1000")
    print(f"Confidence: {decision.confidence:.0%}")
    print(f"Signals: {decision.signals_available}/{decision.signals_total} available")
    
    print(f"\nCategory Scores:")
    for cat, score in decision.category_scores.items():
        print(f"  {cat}: {score:.0f}/100")
    
    print(f"\n--- TIER ASSIGNMENT ---")
    print(f"Tier: {decision.tier} ({decision.tier_label})")
    print(f"Action: {decision.tier_action}")
    if decision.tier_override_reason:
        print(f"Override: {decision.tier_override_reason}")
    
    print(f"\n--- PRICING ---")
    print(f"Recommended Limit: ${decision.recommended_limit:,.0f}")
    print(f"Recommended Retention: ${decision.recommended_retention:,.0f}")
    print(f"Annual Premium: ${decision.annual_premium:,.0f}")
    print(f"Rate: {decision.annual_premium / decision.recommended_limit * 100:.2f}% of limit")
    
    print(f"\n--- DECISION ---")
    print(f"Decision: {decision.decision}")
    print(f"Reasoning: {decision.reasoning}")
    
    if decision.direct_inquiry_applied:
        print(f"\nDirect Inquiry Adjustments:")
        for adj in decision.direct_inquiry_adjustments:
            print(f"  • {adj}")
    
    print(f"\nConditions:")
    for cond in decision.conditions:
        print(f"  • {cond}")
    
    # Example 2: Weak security posture
    print("\n" + "-" * 80)
    print("EXAMPLE 2: Retail Company - Weak Security Posture")
    print("-" * 80)
    
    weak_company = CyberCompanyProfile(
        company_name="QuickMart Retail",
        primary_domain="quickmart.com",
        industry=IndustryClassification.RETAIL,
        country="US",
        is_publicly_traded=False,
        size_band=SizeBand.MEDIUM,
        likely_pci_scope=True,
        
        network_authority=NetworkAuthoritySignals(
            customer_quality_score=45,
            customer_quality_evidence="No enterprise customers visible",
            partner_quality_score=40,
            partner_quality_evidence="Unknown payment processor",
            security_vendor_score=0,  # No security vendor relationships visible
            industry_body_score=0,    # No industry body membership
            certification_authority_score=30,
            certification_authority_evidence="PCI DSS mentioned but not verified",
        ),
        
        technical_infrastructure=TechnicalInfrastructureSignals(
            tls_score=65,
            tls_evidence="TLS 1.2, some issues detected",
            security_headers_score=35,
            security_headers_evidence="Missing CSP, X-Frame-Options",
            email_auth_score=40,
            email_auth_evidence="SPF only, no DMARC",
            dnssec_score=0,  # Not implemented
            exposure_score=45,
            exposure_evidence="Admin panels exposed, unnecessary ports",
            software_currency_score=38,
            software_currency_evidence="Outdated CMS detected",
            cve_exposure_score=35,
            cve_exposure_evidence="Multiple high-severity CVEs",
            cloud_infrastructure_score=50,
            cloud_infrastructure_evidence="Mixed hosting environment",
        ),
        
        corporate_footprint=CorporateFootprintSignals(
            security_page_score=0,    # No security page
            privacy_policy_score=45,
            privacy_policy_evidence="Basic policy, missing GDPR elements",
            security_txt_score=0,     # No security.txt
            bug_bounty_score=0,       # No bug bounty
            security_hiring_score=20,
            security_hiring_evidence="No security roles advertised",
            technical_content_score=0,
            developer_resources_score=0,
            security_leadership_score=0,  # No visible security leadership
        ),
        
        public_records=PublicRecordSignals(
            breach_history_score=40,
            breach_history_evidence="Payment card breach 2 years ago",
            regulatory_action_score=60,
            regulatory_action_evidence="PCI compliance issues noted",
            litigation_score=50,
            litigation_evidence="Class action from breach, settled",
            credential_exposure_score=35,
            credential_exposure_evidence="Employee credentials in multiple breaches",
            dark_web_score=40,
            dark_web_evidence="Customer data found on dark web",
        ),
        
        structured_data=StructuredDataSignals(
            security_rating_score=42,
            security_rating_evidence="BitSight below 600",
        ),
        
        # Direct inquiry - concerning responses
        direct_inquiry=DirectInquirySignals(
            mfa_enabled=False,
            security_training=False,
            pci_scope=True,
            incident_response_plan=False,
            edr_deployed=False,
            immutable_backups=False,
            recent_incident=True,  # Had an incident
        ),
    )
    
    decision2 = model.assess(weak_company)
    
    print(f"\nCompany: {decision2.company_name}")
    print(f"Industry: {decision2.industry.upper()}")
    
    print(f"\n--- SCORING ---")
    print(f"Composite Score: {decision2.composite_score:.0f}/1000")
    print(f"Confidence: {decision2.confidence:.0%}")
    
    print(f"\nCategory Scores:")
    for cat, score in decision2.category_scores.items():
        print(f"  {cat}: {score:.0f}/100")
    
    print(f"\n--- TIER ASSIGNMENT ---")
    print(f"Tier: {decision2.tier} ({decision2.tier_label})")
    if decision2.tier_override_reason:
        print(f"Override: {decision2.tier_override_reason}")
    
    print(f"\n--- PRICING ---")
    print(f"Recommended Limit: ${decision2.recommended_limit:,.0f}")
    print(f"Annual Premium: ${decision2.annual_premium:,.0f}")
    
    print(f"\n--- DECISION ---")
    print(f"Decision: {decision2.decision}")
    print(f"Reasoning: {decision2.reasoning}")
    
    if decision2.direct_inquiry_applied:
        print(f"\nDirect Inquiry Adjustments:")
        for adj in decision2.direct_inquiry_adjustments:
            print(f"  • {adj}")
    
    print("\n" + "=" * 80)
    print("Assessment complete.")
