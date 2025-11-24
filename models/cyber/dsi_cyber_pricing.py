"""
Digital Signal Intelligence (DSI) Pricing Model for Cyber Insurance
====================================================================

Comprehensive cyber insurance pricing based on digital footprint analysis,
security posture signals, and network intelligence.

Author: John Walker
Date: November 2025
Version: 1.0
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum


class IndustryVertical(Enum):
    """Industry verticals with different cyber risk profiles"""
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


class CyberCoverageType(Enum):
    """Cyber insurance coverage types"""
    FIRST_PARTY = "first_party"  # Data breach response, business interruption
    THIRD_PARTY = "third_party"  # Liability, regulatory defense
    COMPREHENSIVE = "comprehensive"  # Both first and third party


class CompanySize(Enum):
    """Company size categories"""
    SMALL = "small"  # <$50M revenue, <500 employees
    MEDIUM = "medium"  # $50M-$1B revenue, 500-5000 employees
    LARGE = "large"  # $1B-$10B revenue, 5000-50000 employees
    ENTERPRISE = "enterprise"  # >$10B revenue, >50000 employees


@dataclass
class CyberSecuritySignals:
    """Enhanced digital signals specific to cyber risk assessment"""
    
    # Infrastructure Security (0-100)
    ssl_certificate: float = 0.0  # Current, valid, strong encryption
    tls_version: float = 0.0  # TLS 1.3 = 100, TLS 1.2 = 80, older = lower
    security_headers: float = 0.0  # HSTS, CSP, X-Frame-Options, etc.
    dnssec_implementation: float = 0.0  # DNS Security Extensions
    spf_dmarc_dkim: float = 0.0  # Email authentication protocols
    web_application_firewall: float = 0.0  # WAF presence indicators
    
    # Vulnerability Indicators (0-100, inverse scoring)
    open_ports_score: float = 0.0  # Fewer open ports = higher score
    outdated_software: float = 0.0  # Current software = higher score
    known_vulnerabilities: float = 0.0  # Fewer CVEs = higher score
    exposed_databases: float = 0.0  # No exposure = 100
    leaked_credentials: float = 0.0  # No leaks = 100
    breached_history: float = 0.0  # No history = 100
    
    # Organizational Maturity (0-100)
    security_certifications: float = 0.0  # ISO 27001, SOC 2, etc.
    privacy_policy_quality: float = 0.0  # Comprehensive, GDPR-compliant
    incident_response_plan: float = 0.0  # Public or inferred presence
    bug_bounty_program: float = 0.0  # HackerOne, Bugcrowd presence
    security_team_visibility: float = 0.0  # CISO, security roles on LinkedIn
    security_blog_activity: float = 0.0  # Security awareness content
    
    # Third-Party Risk (0-100)
    vendor_security_standards: float = 0.0  # Vendor requirements visible
    supply_chain_transparency: float = 0.0  # Disclosed partners/vendors
    cloud_provider_quality: float = 0.0  # AWS/Azure/GCP vs unknown
    third_party_integrations: float = 0.0  # Managed integration complexity
    data_processor_agreements: float = 0.0  # DPA visibility
    
    # Behavioral Security (0-100)
    patch_discipline: float = 0.0  # Update frequency tracking
    security_investment: float = 0.0  # Security budget signals
    employee_training: float = 0.0  # Security awareness programs
    mfa_adoption: float = 0.0  # Multi-factor auth signals
    backup_procedures: float = 0.0  # Disaster recovery visibility
    monitoring_capabilities: float = 0.0  # SOC/SIEM indicators
    
    def get_category_score(self, category: str) -> float:
        """Calculate average score for a signal category"""
        if category == "infrastructure":
            signals = [self.ssl_certificate, self.tls_version, self.security_headers,
                      self.dnssec_implementation, self.spf_dmarc_dkim, 
                      self.web_application_firewall]
        elif category == "vulnerability":
            signals = [self.open_ports_score, self.outdated_software, 
                      self.known_vulnerabilities, self.exposed_databases,
                      self.leaked_credentials, self.breached_history]
        elif category == "organizational":
            signals = [self.security_certifications, self.privacy_policy_quality,
                      self.incident_response_plan, self.bug_bounty_program,
                      self.security_team_visibility, self.security_blog_activity]
        elif category == "third_party":
            signals = [self.vendor_security_standards, self.supply_chain_transparency,
                      self.cloud_provider_quality, self.third_party_integrations,
                      self.data_processor_agreements]
        elif category == "behavioral":
            signals = [self.patch_discipline, self.security_investment,
                      self.employee_training, self.mfa_adoption,
                      self.backup_procedures, self.monitoring_capabilities]
        else:
            return 0.0
        
        return np.mean([s for s in signals if s > 0])
    
    def get_composite_score(self) -> float:
        """Calculate composite cyber security score (0-1000 scale)"""
        # Weighted by importance to cyber risk
        weights = {
            "infrastructure": 0.20,
            "vulnerability": 0.30,  # Most critical for cyber
            "organizational": 0.20,
            "third_party": 0.15,
            "behavioral": 0.15
        }
        
        categories = ["infrastructure", "vulnerability", "organizational", 
                     "third_party", "behavioral"]
        weighted_sum = sum(
            self.get_category_score(cat) * weights[cat] 
            for cat in categories
        )
        
        # Convert from 0-100 to 0-1000 scale
        return weighted_sum * 10


@dataclass
class CyberCompanyProfile:
    """Company profile for cyber insurance pricing"""
    company_name: str
    industry: IndustryVertical
    country: str
    annual_revenue: float  # USD
    employees: int
    size_category: CompanySize
    
    # Data characteristics
    records_stored: Optional[int] = None  # Customer/patient records
    pii_volume: str = "medium"  # "low", "medium", "high", "critical"
    phi_handler: bool = False  # Protected Health Information
    pci_scope: bool = False  # Payment Card Industry data
    
    # IT environment
    cloud_percentage: float = 50.0  # % of infrastructure in cloud
    legacy_systems: bool = False
    bring_your_own_device: bool = False
    remote_workforce_pct: float = 30.0  # % remote employees
    
    # Traditional risk factors
    prior_incidents: int = 0
    largest_breach_records: Optional[int] = None
    regulatory_actions: int = 0
    cyber_insurance_history: int = 0  # Years of prior coverage
    
    # Financial
    revenue_per_employee: float = 0.0
    it_budget_pct: float = 0.0  # % of revenue spent on IT
    
    # Cyber security signals
    signals: CyberSecuritySignals = field(default_factory=CyberSecuritySignals)
    
    def __post_init__(self):
        """Calculate derived fields"""
        if self.revenue_per_employee == 0.0 and self.employees > 0:
            self.revenue_per_employee = self.annual_revenue / self.employees


@dataclass
class CyberPricingResult:
    """Output of cyber insurance pricing calculation"""
    company_name: str
    industry: str
    coverage_type: str
    
    # Pricing components
    base_rate: float
    cyber_maturity_modifier: float
    vulnerability_modifier: float
    industry_modifier: float
    size_modifier: float
    data_sensitivity_modifier: float
    
    # Limits and deductibles
    policy_limit: float
    deductible: float
    
    # Final pricing
    technical_rate: float
    annual_premium: float
    
    # Risk assessment
    composite_score: float
    vulnerability_score: float
    risk_tier: str
    breach_probability: float  # Estimated annual probability
    expected_loss: float
    confidence_level: float
    
    # Coverage and underwriting recommendations
    recommended_limit: float
    recommended_deductible: float
    recommendation: str
    reasoning: str
    conditions: List[str] = field(default_factory=list)
    sublimits: Dict[str, float] = field(default_factory=dict)
    
    
class CyberInsurancePricingModel:
    """
    Comprehensive cyber insurance pricing model using Digital Signal Intelligence
    """
    
    def __init__(self, coverage_type: CyberCoverageType):
        self.coverage_type = coverage_type
        self.base_rates = self._initialize_base_rates()
        self.industry_multipliers = self._initialize_industry_multipliers()
        
    def _initialize_base_rates(self) -> Dict[str, Dict[str, float]]:
        """
        Initialize base rates per $1M of revenue by company size and coverage type
        Base rates in USD per $1M revenue
        """
        return {
            "first_party": {
                "small": 2800.0,
                "medium": 2200.0,
                "large": 1800.0,
                "enterprise": 1500.0
            },
            "third_party": {
                "small": 3200.0,
                "medium": 2600.0,
                "large": 2100.0,
                "enterprise": 1750.0
            },
            "comprehensive": {
                "small": 5500.0,
                "medium": 4400.0,
                "large": 3600.0,
                "enterprise": 3000.0
            }
        }
    
    def _initialize_industry_multipliers(self) -> Dict[str, float]:
        """Initialize industry risk multipliers"""
        return {
            "technology": 1.15,  # High-value target
            "financial_services": 1.40,  # Heavily regulated, high-value data
            "healthcare": 1.50,  # PHI, regulatory risk
            "retail": 1.25,  # PCI compliance, customer data
            "manufacturing": 0.95,  # Lower data exposure
            "professional_services": 1.10,  # Client data risk
            "education": 1.05,  # Student data, lower security maturity
            "government": 0.90,  # Security focus, but catastrophic if breached
            "energy": 1.20,  # Critical infrastructure
            "other": 1.00
        }
    
    def calculate_cyber_maturity_modifier(self, signals: CyberSecuritySignals) -> Tuple[float, float]:
        """
        Calculate modifier based on overall cyber security maturity
        Returns: (modifier, composite_score)
        """
        composite_score = signals.get_composite_score()
        
        # Score-based modifiers - cyber is more sensitive to low scores
        if composite_score >= 800:
            modifier = 0.60  # Exceptional security
        elif composite_score >= 700:
            modifier = 0.70 + (800 - composite_score) / 100 * 0.10  # 0.70-0.80
        elif composite_score >= 600:
            modifier = 0.80 + (700 - composite_score) / 100 * 0.15  # 0.80-0.95
        elif composite_score >= 500:
            modifier = 0.95 + (600 - composite_score) / 100 * 0.25  # 0.95-1.20
        elif composite_score >= 400:
            modifier = 1.20 + (500 - composite_score) / 100 * 0.40  # 1.20-1.60
        else:
            modifier = 1.60 + (400 - composite_score) / 400 * 0.90  # 1.60-2.50
        
        return modifier, composite_score
    
    def calculate_vulnerability_modifier(self, signals: CyberSecuritySignals) -> Tuple[float, float]:
        """
        Calculate modifier based on vulnerability indicators
        This is critical for cyber - direct exposure measurement
        Returns: (modifier, vulnerability_score)
        """
        vuln_score = signals.get_category_score("vulnerability")
        
        # Vulnerability is inverse - more critical than other factors
        if vuln_score >= 90:
            modifier = 0.70  # Very few vulnerabilities
        elif vuln_score >= 80:
            modifier = 0.80
        elif vuln_score >= 70:
            modifier = 0.95
        elif vuln_score >= 60:
            modifier = 1.10
        elif vuln_score >= 50:
            modifier = 1.30
        elif vuln_score >= 40:
            modifier = 1.60
        else:
            modifier = 2.00  # Critical vulnerability exposure
        
        return modifier, vuln_score
    
    def calculate_data_sensitivity_modifier(self, company: CyberCompanyProfile) -> float:
        """Calculate modifier based on data sensitivity"""
        base_modifier = 1.0
        
        # PII volume
        pii_multipliers = {"low": 0.90, "medium": 1.00, "high": 1.25, "critical": 1.50}
        base_modifier *= pii_multipliers.get(company.pii_volume, 1.0)
        
        # PHI (healthcare data)
        if company.phi_handler:
            base_modifier *= 1.40
        
        # PCI (payment card data)
        if company.pci_scope:
            base_modifier *= 1.30
        
        # Number of records
        if company.records_stored:
            if company.records_stored > 100_000_000:
                base_modifier *= 1.35
            elif company.records_stored > 10_000_000:
                base_modifier *= 1.25
            elif company.records_stored > 1_000_000:
                base_modifier *= 1.15
            elif company.records_stored > 100_000:
                base_modifier *= 1.05
        
        return base_modifier
    
    def calculate_it_environment_modifier(self, company: CyberCompanyProfile) -> float:
        """Calculate modifier based on IT environment characteristics"""
        modifier = 1.0
        
        # Cloud vs on-premise (cloud generally more secure if using major providers)
        if company.cloud_percentage >= 80:
            modifier *= 0.92
        elif company.cloud_percentage <= 20:
            modifier *= 1.15
        
        # Legacy systems
        if company.legacy_systems:
            modifier *= 1.25
        
        # BYOD policy
        if company.bring_your_own_device:
            modifier *= 1.15
        
        # Remote workforce
        if company.remote_workforce_pct >= 70:
            modifier *= 1.20
        elif company.remote_workforce_pct >= 50:
            modifier *= 1.10
        
        return modifier
    
    def calculate_prior_incidents_modifier(self, company: CyberCompanyProfile) -> float:
        """Calculate modifier based on prior cyber incidents"""
        if company.prior_incidents == 0:
            return 0.95
        elif company.prior_incidents == 1:
            return 1.30
        elif company.prior_incidents == 2:
            return 1.65
        else:
            return 2.00  # Multiple incidents = major red flag
    
    def estimate_breach_probability(self, composite_score: float, 
                                   industry: IndustryVertical,
                                   prior_incidents: int) -> float:
        """Estimate annual probability of a material breach"""
        # Base probability by score
        if composite_score >= 800:
            base_prob = 0.02  # 2% annual probability
        elif composite_score >= 700:
            base_prob = 0.05
        elif composite_score >= 600:
            base_prob = 0.10
        elif composite_score >= 500:
            base_prob = 0.18
        elif composite_score >= 400:
            base_prob = 0.30
        else:
            base_prob = 0.45
        
        # Adjust for industry
        industry_adjustments = {
            IndustryVertical.HEALTHCARE: 1.30,
            IndustryVertical.FINANCIAL_SERVICES: 1.25,
            IndustryVertical.RETAIL: 1.20,
            IndustryVertical.TECHNOLOGY: 1.15,
            IndustryVertical.MANUFACTURING: 0.85,
            IndustryVertical.GOVERNMENT: 0.90
        }
        
        multiplier = industry_adjustments.get(industry, 1.0)
        adjusted_prob = base_prob * multiplier
        
        # Prior incidents dramatically increase probability
        if prior_incidents > 0:
            adjusted_prob *= (1 + prior_incidents * 0.40)
        
        return min(adjusted_prob, 0.70)  # Cap at 70%
    
    def estimate_expected_loss(self, company: CyberCompanyProfile,
                              breach_probability: float) -> float:
        """Estimate expected annual loss from cyber incidents"""
        # Base loss varies by company size and data sensitivity
        revenue_mm = company.annual_revenue / 1_000_000
        
        # Average breach cost per record: $150-200
        if company.records_stored:
            per_record_cost = 175
            # Assume 10% of records exposed in typical breach
            exposure = company.records_stored * 0.10 * per_record_cost
        else:
            # Estimate based on revenue
            exposure = revenue_mm * 5000  # $5k per $1M revenue
        
        # Business interruption component
        daily_revenue = company.annual_revenue / 365
        interruption_days = 15  # Average downtime
        bi_exposure = daily_revenue * interruption_days
        
        # Third-party liability
        if self.coverage_type in [CyberCoverageType.THIRD_PARTY, CyberCoverageType.COMPREHENSIVE]:
            liability_exposure = exposure * 2.5  # Regulatory fines, lawsuits
        else:
            liability_exposure = 0
        
        total_exposure = exposure + bi_exposure + liability_exposure
        expected_loss = total_exposure * breach_probability
        
        return expected_loss
    
    def recommend_policy_structure(self, company: CyberCompanyProfile,
                                   expected_loss: float) -> Tuple[float, float, Dict[str, float]]:
        """
        Recommend policy limit, deductible, and sublimits
        Returns: (limit, deductible, sublimits_dict)
        """
        revenue_mm = company.annual_revenue / 1_000_000
        
        # Policy limit: 2-3x expected loss, capped by revenue percentage
        recommended_limit = min(
            expected_loss * 2.5,
            revenue_mm * 0.15 * 1_000_000  # 15% of revenue max
        )
        
        # Round to standard limits
        standard_limits = [1_000_000, 2_000_000, 5_000_000, 10_000_000,
                          25_000_000, 50_000_000, 100_000_000]
        recommended_limit = min(standard_limits, 
                               key=lambda x: abs(x - recommended_limit))
        
        # Deductible: typically 1-5% of limit or $10k minimum
        deductible = max(recommended_limit * 0.02, 10_000)
        
        # Sublimits for specific coverages
        sublimits = {
            "breach_response": recommended_limit * 0.25,
            "business_interruption": recommended_limit * 0.50,
            "cyber_extortion": recommended_limit * 0.15,
            "regulatory_defense": recommended_limit * 0.40,
            "media_liability": recommended_limit * 0.30
        }
        
        return recommended_limit, deductible, sublimits
    
    def determine_risk_tier(self, composite_score: float, 
                           vulnerability_score: float) -> str:
        """Determine risk tier with emphasis on vulnerabilities"""
        # Vulnerability score can override composite
        if vulnerability_score < 50:
            return "Tier 5 - Critical Risk (Uninsurable)"
        elif composite_score >= 800 and vulnerability_score >= 85:
            return "Tier 1 - Preferred"
        elif composite_score >= 700 and vulnerability_score >= 75:
            return "Tier 2 - Standard"
        elif composite_score >= 600 and vulnerability_score >= 65:
            return "Tier 3 - Elevated"
        elif composite_score >= 500 and vulnerability_score >= 55:
            return "Tier 4 - High Risk"
        else:
            return "Tier 5 - Critical Risk"
    
    def calculate_confidence(self, signals: CyberSecuritySignals) -> float:
        """Calculate confidence level in the pricing"""
        all_signals = [
            signals.ssl_certificate, signals.tls_version, signals.security_headers,
            signals.dnssec_implementation, signals.spf_dmarc_dkim,
            signals.web_application_firewall, signals.open_ports_score,
            signals.outdated_software, signals.known_vulnerabilities,
            signals.exposed_databases, signals.leaked_credentials,
            signals.breached_history, signals.security_certifications,
            signals.privacy_policy_quality, signals.incident_response_plan,
            signals.bug_bounty_program, signals.security_team_visibility,
            signals.security_blog_activity, signals.vendor_security_standards,
            signals.supply_chain_transparency, signals.cloud_provider_quality,
            signals.third_party_integrations, signals.data_processor_agreements,
            signals.patch_discipline, signals.security_investment,
            signals.employee_training, signals.mfa_adoption,
            signals.backup_procedures, signals.monitoring_capabilities
        ]
        
        non_zero = sum(1 for s in all_signals if s > 0)
        signal_coverage = non_zero / len(all_signals)
        
        # Cyber requires higher signal coverage for confidence
        if signal_coverage >= 0.85:
            return 0.95
        elif signal_coverage >= 0.70:
            return 0.88
        elif signal_coverage >= 0.55:
            return 0.75
        elif signal_coverage >= 0.40:
            return 0.65
        else:
            return 0.50  # Below 50% confidence requires manual review
    
    def generate_recommendation(self, composite_score: float,
                               vulnerability_score: float,
                               confidence: float,
                               breach_probability: float,
                               prior_incidents: int) -> Tuple[str, str, List[str]]:
        """
        Generate underwriting recommendation, reasoning, and conditions
        """
        conditions = []
        
        # Critical vulnerabilities = decline
        if vulnerability_score < 50:
            rec = "Decline - Critical Vulnerabilities"
            reason = f"Critical vulnerability exposure (score: {vulnerability_score:.0f}). Unacceptable risk of imminent breach. Must remediate: open databases, leaked credentials, or known CVEs before coverage possible."
            return rec, reason, conditions
        
        # Multiple prior incidents with low scores = decline
        if prior_incidents >= 2 and composite_score < 600:
            rec = "Decline - Repeat Breach Pattern"
            reason = f"Multiple prior incidents ({prior_incidents}) combined with low security maturity (score: {composite_score:.0f}). Pattern indicates systemic security failures. Requires 12+ months incident-free with demonstrated improvements."
            return rec, reason, conditions
        
        # Strong security posture
        if composite_score >= 800 and vulnerability_score >= 85 and confidence >= 0.85:
            rec = "Auto-Approve - Preferred Pricing"
            reason = f"Exceptional cyber security maturity (score: {composite_score:.0f}). Strong controls, minimal vulnerabilities, low breach probability ({breach_probability:.1%}). Best-in-class risk."
            conditions = ["Annual security assessment required", "30-day breach notification"]
            
        elif composite_score >= 700 and vulnerability_score >= 75 and confidence >= 0.80:
            rec = "Auto-Approve - Standard Pricing"
            reason = f"Good cyber security posture (score: {composite_score:.0f}). Adequate controls with acceptable vulnerability profile. Breach probability: {breach_probability:.1%}."
            conditions = ["Annual security questionnaire", "Incident response plan on file", "30-day breach notification"]
            
        elif composite_score >= 600 and vulnerability_score >= 65 and confidence >= 0.70:
            rec = "Manual Review - Elevated Risk"
            reason = f"Moderate security maturity (score: {composite_score:.0f}). Some vulnerabilities present. Breach probability: {breach_probability:.1%}. Underwriter review required."
            conditions = ["Detailed security questionnaire", "Penetration test results within 12 months", 
                         "Incident response plan required", "MFA implementation required within 90 days"]
            
        elif confidence < 0.65:
            rec = "Manual Review - Insufficient Data"
            reason = f"Low signal coverage (confidence: {confidence:.0%}). Unable to assess security posture adequately. Requires traditional underwriting process."
            conditions = ["Complete cyber security questionnaire", "IT environment documentation",
                         "Security audit or penetration test results"]
            
        else:
            rec = "Manual Review - High Risk"
            reason = f"Below-standard security maturity (score: {composite_score:.0f}). Significant vulnerabilities (score: {vulnerability_score:.0f}). Breach probability: {breach_probability:.1%}. May require coverage restrictions or decline."
            conditions = ["Comprehensive security assessment required", "Penetration test mandatory",
                         "Remediation plan for identified vulnerabilities", "Higher deductible/sublimits",
                         "Quarterly security reviews", "MFA mandatory", "EDR/XDR solution required"]
        
        return rec, reason, conditions
    
    def price(self, company: CyberCompanyProfile,
             requested_limit: Optional[float] = None) -> CyberPricingResult:
        """
        Generate complete cyber insurance pricing
        """
        # Calculate all modifiers
        maturity_mod, composite = self.calculate_cyber_maturity_modifier(company.signals)
        vuln_mod, vuln_score = self.calculate_vulnerability_modifier(company.signals)
        industry_mod = self.industry_multipliers[company.industry]
        data_mod = self.calculate_data_sensitivity_modifier(company)
        it_env_mod = self.calculate_it_environment_modifier(company)
        incidents_mod = self.calculate_prior_incidents_modifier(company)
        
        # Size modifier based on revenue efficiency
        if company.size_category == CompanySize.ENTERPRISE:
            size_mod = 0.85
        elif company.size_category == CompanySize.LARGE:
            size_mod = 0.92
        elif company.size_category == CompanySize.MEDIUM:
            size_mod = 1.00
        else:
            size_mod = 1.15
        
        # Get base rate
        base_rate = self.base_rates[self.coverage_type.value][company.size_category.value]
        
        # Calculate technical rate
        tech_rate = (base_rate * maturity_mod * vuln_mod * industry_mod * 
                    size_mod * data_mod * it_env_mod * incidents_mod)
        
        # Calculate exposure base (revenue in millions)
        exposure_mm = company.annual_revenue / 1_000_000
        
        # Calculate premium
        base_premium = tech_rate * exposure_mm
        
        # Risk assessment
        breach_prob = self.estimate_breach_probability(
            composite, company.industry, company.prior_incidents
        )
        expected_loss = self.estimate_expected_loss(company, breach_prob)
        confidence = self.calculate_confidence(company.signals)
        risk_tier = self.determine_risk_tier(composite, vuln_score)
        
        # Policy structure
        limit, deductible, sublimits = self.recommend_policy_structure(
            company, expected_loss
        )
        
        # Use requested limit if provided
        if requested_limit:
            limit = requested_limit
            # Adjust premium proportionally
            base_premium *= (limit / sublimits["business_interruption"]) ** 0.7
        
        # Generate recommendation
        recommendation, reasoning, conditions = self.generate_recommendation(
            composite, vuln_score, confidence, breach_prob, company.prior_incidents
        )
        
        return CyberPricingResult(
            company_name=company.company_name,
            industry=company.industry.value,
            coverage_type=self.coverage_type.value,
            base_rate=base_rate,
            cyber_maturity_modifier=maturity_mod,
            vulnerability_modifier=vuln_mod,
            industry_modifier=industry_mod,
            size_modifier=size_mod,
            data_sensitivity_modifier=data_mod,
            policy_limit=limit,
            deductible=deductible,
            technical_rate=tech_rate,
            annual_premium=base_premium,
            composite_score=composite,
            vulnerability_score=vuln_score,
            risk_tier=risk_tier,
            breach_probability=breach_prob,
            expected_loss=expected_loss,
            confidence_level=confidence,
            recommended_limit=limit,
            recommended_deductible=deductible,
            sublimits=sublimits,
            recommendation=recommendation,
            reasoning=reasoning,
            conditions=conditions
        )


# Example usage
if __name__ == "__main__":
    # Example 1: Technology company with strong security (like Petrobras but tech sector)
    strong_tech_signals = CyberSecuritySignals(
        ssl_certificate=95, tls_version=100, security_headers=90,
        dnssec_implementation=85, spf_dmarc_dkim=92, web_application_firewall=88,
        open_ports_score=90, outdated_software=88, known_vulnerabilities=92,
        exposed_databases=100, leaked_credentials=95, breached_history=100,
        security_certifications=90, privacy_policy_quality=88, incident_response_plan=85,
        bug_bounty_program=92, security_team_visibility=87, security_blog_activity=80,
        vendor_security_standards=85, supply_chain_transparency=82, cloud_provider_quality=95,
        third_party_integrations=88, data_processor_agreements=85,
        patch_discipline=90, security_investment=88, employee_training=85,
        mfa_adoption=95, backup_procedures=90, monitoring_capabilities=92
    )
    
    tech_company = CyberCompanyProfile(
        company_name="TechCorp Global",
        industry=IndustryVertical.TECHNOLOGY,
        country="United States",
        annual_revenue=5_000_000_000,
        employees=15000,
        size_category=CompanySize.LARGE,
        records_stored=25_000_000,
        pii_volume="high",
        phi_handler=False,
        pci_scope=True,
        cloud_percentage=80,
        legacy_systems=False,
        bring_your_own_device=True,
        remote_workforce_pct=60,
        prior_incidents=0,
        largest_breach_records=None,
        regulatory_actions=0,
        cyber_insurance_history=3,
        it_budget_pct=12.0,
        signals=strong_tech_signals
    )
    
    # Example 2: Healthcare company with moderate security (concerning vulnerabilities)
    moderate_healthcare_signals = CyberSecuritySignals(
        ssl_certificate=85, tls_version=80, security_headers=70,
        dnssec_implementation=60, spf_dmarc_dkim=75, web_application_firewall=65,
        open_ports_score=65, outdated_software=58, known_vulnerabilities=62,
        exposed_databases=70, leaked_credentials=65, breached_history=60,
        security_certifications=72, privacy_policy_quality=80, incident_response_plan=68,
        bug_bounty_program=0, security_team_visibility=70, security_blog_activity=45,
        vendor_security_standards=68, supply_chain_transparency=60, cloud_provider_quality=75,
        third_party_integrations=65, data_processor_agreements=78,
        patch_discipline=58, security_investment=65, employee_training=70,
        mfa_adoption=72, backup_procedures=75, monitoring_capabilities=68
    )
    
    healthcare_company = CyberCompanyProfile(
        company_name="Regional Health System",
        industry=IndustryVertical.HEALTHCARE,
        country="United States",
        annual_revenue=800_000_000,
        employees=5000,
        size_category=CompanySize.MEDIUM,
        records_stored=2_000_000,
        pii_volume="critical",
        phi_handler=True,
        pci_scope=True,
        cloud_percentage=40,
        legacy_systems=True,
        bring_your_own_device=False,
        remote_workforce_pct=25,
        prior_incidents=1,
        largest_breach_records=50_000,
        regulatory_actions=0,
        cyber_insurance_history=5,
        it_budget_pct=6.5,
        signals=moderate_healthcare_signals
    )
    
    # Example 3: Retail company with poor security (like PEMEX equivalent)
    poor_retail_signals = CyberSecuritySignals(
        ssl_certificate=75, tls_version=60, security_headers=45,
        dnssec_implementation=30, spf_dmarc_dkim=55, web_application_firewall=40,
        open_ports_score=45, outdated_software=38, known_vulnerabilities=42,
        exposed_databases=50, leaked_credentials=40, breached_history=35,
        security_certifications=40, privacy_policy_quality=50, incident_response_plan=35,
        bug_bounty_program=0, security_team_visibility=45, security_blog_activity=20,
        vendor_security_standards=42, supply_chain_transparency=38, cloud_provider_quality=60,
        third_party_integrations=45, data_processor_agreements=40,
        patch_discipline=35, security_investment=40, employee_training=38,
        mfa_adoption=45, backup_procedures=50, monitoring_capabilities=42
    )
    
    retail_company = CyberCompanyProfile(
        company_name="National Retail Chain",
        industry=IndustryVertical.RETAIL,
        country="United States",
        annual_revenue=2_000_000_000,
        employees=25000,
        size_category=CompanySize.LARGE,
        records_stored=50_000_000,
        pii_volume="high",
        phi_handler=False,
        pci_scope=True,
        cloud_percentage=30,
        legacy_systems=True,
        bring_your_own_device=True,
        remote_workforce_pct=15,
        prior_incidents=2,
        largest_breach_records=5_000_000,
        regulatory_actions=1,
        cyber_insurance_history=2,
        it_budget_pct=3.5,
        signals=poor_retail_signals
    )
    
    # Price all three companies with comprehensive coverage
    model = CyberInsurancePricingModel(CyberCoverageType.COMPREHENSIVE)
    
    companies = [
        ("Strong Security (Tech)", tech_company),
        ("Moderate Security (Healthcare)", healthcare_company),
        ("Poor Security (Retail)", retail_company)
    ]
    
    print("=" * 100)
    print("CYBER INSURANCE PRICING ANALYSIS")
    print("Coverage Type: Comprehensive (First-Party + Third-Party)")
    print("=" * 100)
    
    for label, company in companies:
        result = model.price(company)
        
        print(f"\n{label}: {result.company_name}")
        print("-" * 100)
        print(f"Industry: {result.industry.upper()} | Size: {company.size_category.value.upper()}")
        print(f"Revenue: ${company.annual_revenue:,.0f} | Employees: {company.employees:,}")
        print(f"Records Stored: {company.records_stored:,} | PII Volume: {company.pii_volume.upper()}")
        print(f"Prior Incidents: {company.prior_incidents}")
        
        print(f"\nSECURITY ASSESSMENT:")
        print(f"  Composite Score: {result.composite_score:.0f}/1000")
        print(f"  Vulnerability Score: {result.vulnerability_score:.0f}/100")
        print(f"  Risk Tier: {result.risk_tier}")
        print(f"  Breach Probability: {result.breach_probability:.1%} annually")
        print(f"  Expected Annual Loss: ${result.expected_loss:,.0f}")
        print(f"  Confidence Level: {result.confidence_level:.0%}")
        
        print(f"\nPRICING COMPONENTS:")
        print(f"  Base Rate: ${result.base_rate:,.2f} per $1M revenue")
        print(f"  Cyber Maturity Modifier: {result.cyber_maturity_modifier:.3f}x")
        print(f"  Vulnerability Modifier: {result.vulnerability_modifier:.3f}x")
        print(f"  Industry Modifier: {result.industry_modifier:.3f}x")
        print(f"  Size Modifier: {result.size_modifier:.3f}x")
        print(f"  Data Sensitivity Modifier: {result.data_sensitivity_modifier:.3f}x")
        print(f"  Technical Rate: ${result.technical_rate:,.2f} per $1M revenue")
        
        print(f"\nPOLICY STRUCTURE:")
        print(f"  Recommended Limit: ${result.recommended_limit:,.0f}")
        print(f"  Recommended Deductible: ${result.deductible:,.0f}")
        print(f"  Annual Premium: ${result.annual_premium:,.0f}")
        print(f"  Premium as % of Limit: {(result.annual_premium / result.recommended_limit * 100):.2f}%")
        
        print(f"\nSUBLIMITS:")
        for coverage, amount in result.sublimits.items():
            print(f"    {coverage.replace('_', ' ').title()}: ${amount:,.0f}")
        
        print(f"\nUNDERWRITING DECISION:")
        print(f"  Recommendation: {result.recommendation}")
        print(f"  Reasoning: {result.reasoning}")
        
        if result.conditions:
            print(f"  Conditions:")
            for condition in result.conditions:
                print(f"    • {condition}")
        
        print("\n" + "=" * 100)
    
    # Demonstrate sensitivity to vulnerability changes
    print("\n\nVULNERABILITY SENSITIVITY ANALYSIS")
    print("=" * 100)
    print("Impact of vulnerability remediation on pricing for Healthcare company:\n")
    
    vulnerability_scenarios = [
        (40, "Critical - Multiple exposed databases, leaked credentials"),
        (60, "High - Some known CVEs, minimal exposure"),
        (80, "Moderate - Few vulnerabilities, good patch management"),
        (95, "Low - Minimal attack surface, excellent security hygiene")
    ]
    
    for vuln_score, description in vulnerability_scenarios:
        test_signals = CyberSecuritySignals(**moderate_healthcare_signals.__dict__)
        # Adjust all vulnerability signals proportionally
        test_signals.open_ports_score = vuln_score
        test_signals.outdated_software = vuln_score
        test_signals.known_vulnerabilities = vuln_score
        test_signals.exposed_databases = vuln_score
        test_signals.leaked_credentials = vuln_score
        
        test_company = CyberCompanyProfile(**healthcare_company.__dict__)
        test_company.signals = test_signals
        
        result = model.price(test_company)
        
        print(f"Vulnerability Score: {vuln_score}/100 - {description}")
        print(f"  Premium: ${result.annual_premium:,.0f}")
        print(f"  Breach Probability: {result.breach_probability:.1%}")
        print(f"  Recommendation: {result.recommendation}")
        print()
