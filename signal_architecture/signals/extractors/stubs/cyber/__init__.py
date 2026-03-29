"""
Cyber Stub Extractors

Cybersecurity coverage data source simulations organized by signal group:
- network_authority.py: Business relationships and partner quality
- technical_infrastructure.py: Observable security implementation
- corporate_footprint.py: Digital presence and security posture
- public_record_and_structured.py: Breach history, credentials, ratings
"""

from .network_authority import (
    CustomerQualityExtractor,
    PartnerNetworkExtractor,
    SecurityVendorExtractor,
    CertificationAuthorityExtractor,
    FinancialRelationshipExtractor,
    NetworkCentralityExtractor,
    SecondDegreeExtractor,
)

from .technical_infrastructure import (
    TLSConfigExtractor,
    SecurityHeadersExtractor,
    EmailAuthExtractor,
    DNSSECExtractor,
    NetworkExposureExtractor,
    SoftwareCurrencyExtractor,
    CVEExposureExtractor,
    CloudInfraExtractor,
    WAFPresenceExtractor,
    CDNUsageExtractor,
)

from .corporate_footprint import (
    SecurityPageExtractor,
    PrivacyPolicyExtractor,
    SecurityTxtExtractor,
    BugBountyExtractor,
    SecurityHiringExtractor,
    TechnicalContentExtractor,
    DeveloperResourcesExtractor,
    SecurityLeadershipExtractor,
    ComplianceBadgesExtractor,
)

from .public_record_and_structured import (
    BreachHistoryExtractor,
    LitigationHistoryExtractor,
    CredentialExposureExtractor,
    DarkWebExtractor,
    SecurityRatingExtractor,
    ESGCyberExtractor,
    IndustryClassificationExtractor,
    CompanySizeExtractor,
    OperationalBaseExtractor,
)

__all__ = [
    # Network Authority
    "CustomerQualityExtractor",
    "PartnerNetworkExtractor",
    "SecurityVendorExtractor",
    "CertificationAuthorityExtractor",
    "FinancialRelationshipExtractor",
    "NetworkCentralityExtractor",
    "SecondDegreeExtractor",
    # Technical Infrastructure
    "TLSConfigExtractor",
    "SecurityHeadersExtractor",
    "EmailAuthExtractor",
    "DNSSECExtractor",
    "NetworkExposureExtractor",
    "SoftwareCurrencyExtractor",
    "CVEExposureExtractor",
    "CloudInfraExtractor",
    "WAFPresenceExtractor",
    "CDNUsageExtractor",
    # Corporate Footprint
    "SecurityPageExtractor",
    "PrivacyPolicyExtractor",
    "SecurityTxtExtractor",
    "BugBountyExtractor",
    "SecurityHiringExtractor",
    "TechnicalContentExtractor",
    "DeveloperResourcesExtractor",
    "SecurityLeadershipExtractor",
    "ComplianceBadgesExtractor",
    # Public Record
    "BreachHistoryExtractor",
    "LitigationHistoryExtractor",
    "CredentialExposureExtractor",
    "DarkWebExtractor",
    # Structured Data
    "SecurityRatingExtractor",
    "ESGCyberExtractor",
    # Categorical
    "IndustryClassificationExtractor",
    "CompanySizeExtractor",
    "OperationalBaseExtractor",
]
from . import phase_7_extractors
