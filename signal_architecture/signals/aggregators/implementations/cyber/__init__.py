"""
Cyber Aggregators

Production-ready aggregators for cyber coverage signals.
"""

from .aggregators import (
    # Network Authority
    CustomerQualityAggregator,
    PartnerQualityAggregator,
    SecurityVendorAggregator,
    CertificationAuthorityAggregator,
    FinancialRelationshipAggregator,
    NetworkCentralityAggregator,
    SecondDegreeAggregator,
    # Technical Infrastructure
    TLSConfigAggregator,
    SecurityHeadersAggregator,
    EmailAuthAggregator,
    DNSSECAggregator,
    NetworkExposureAggregator,
    SoftwareCurrencyAggregator,
    CVEExposureAggregator,
    CloudInfraAggregator,
    WAFPresenceAggregator,
    CDNUsageAggregator,
    # Corporate Footprint
    SecurityPageAggregator,
    PrivacyPolicyAggregator,
    SecurityTxtAggregator,
    BugBountyAggregator,
    SecurityHiringAggregator,
    TechnicalContentAggregator,
    DeveloperResourcesAggregator,
    SecurityLeadershipAggregator,
    ComplianceBadgesAggregator,
    # Public Record
    BreachHistoryAggregator,
    LitigationHistoryAggregator,
    CredentialExposureAggregator,
    DarkWebAggregator,
    # Structured Data
    SecurityRatingAggregator,
    ESGCyberAggregator,
    # Categorical
    IndustryClassificationAggregator,
    CompanySizeAggregator,
    GeographyAggregator,
)

__all__ = [
    # Network Authority
    "CustomerQualityAggregator",
    "PartnerQualityAggregator",
    "SecurityVendorAggregator",
    "CertificationAuthorityAggregator",
    "FinancialRelationshipAggregator",
    "NetworkCentralityAggregator",
    "SecondDegreeAggregator",
    # Technical Infrastructure
    "TLSConfigAggregator",
    "SecurityHeadersAggregator",
    "EmailAuthAggregator",
    "DNSSECAggregator",
    "NetworkExposureAggregator",
    "SoftwareCurrencyAggregator",
    "CVEExposureAggregator",
    "CloudInfraAggregator",
    "WAFPresenceAggregator",
    "CDNUsageAggregator",
    # Corporate Footprint
    "SecurityPageAggregator",
    "PrivacyPolicyAggregator",
    "SecurityTxtAggregator",
    "BugBountyAggregator",
    "SecurityHiringAggregator",
    "TechnicalContentAggregator",
    "DeveloperResourcesAggregator",
    "SecurityLeadershipAggregator",
    "ComplianceBadgesAggregator",
    # Public Record
    "BreachHistoryAggregator",
    "LitigationHistoryAggregator",
    "CredentialExposureAggregator",
    "DarkWebAggregator",
    # Structured Data
    "SecurityRatingAggregator",
    "ESGCyberAggregator",
    # Categorical
    "IndustryClassificationAggregator",
    "CompanySizeAggregator",
    "GeographyAggregator",
]
