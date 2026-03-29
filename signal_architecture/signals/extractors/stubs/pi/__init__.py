"""
PI (Professional Indemnity) Stub Extractors

Professional services-specific data source simulations organized by signal group:
- network_and_regulatory.py: Network authority + regulatory standing signals
- stability_and_quality.py: Firm stability + practice quality signals
- infrastructure_footprint_litigation_categorical.py: Technical, footprint, litigation, categorical
"""

from .network_and_regulatory import (
    # Network Authority
    PeerRankingExtractor,
    ClientQualityExtractor,
    ReferralQualityExtractor,
    AssociationLeadershipExtractor,
    ThoughtLeadershipExtractor,
    PanelMembershipExtractor,
    # Regulatory Standing
    LicenseStatusExtractor,
    DisciplinaryHistoryExtractor,
    MalpracticeRecordExtractor,
    CEComplianceExtractor,
    SpecialtyCertificationExtractor,
    PeerReviewExtractor,
    PCAOBStandingExtractor,
)

from .stability_and_quality import (
    # Firm Stability
    YearsInPracticeExtractor,
    PartnerStabilityExtractor,
    StaffRetentionExtractor,
    OfficeStabilityExtractor,
    PIFinancialStabilityExtractor,
    SuccessionPlanningExtractor,
    # Practice Quality
    OutcomePatternsExtractor,
    ClientReviewsExtractor,
    WorkQualityExtractor,
    FeeDisputeExtractor,
    ComplaintHistoryExtractor,
)

from .infrastructure_footprint_litigation_categorical import (
    # Technical Infrastructure
    PITLSScoreExtractor,
    PIEmailAuthExtractor,
    PISecurityHeadersExtractor,
    PortalSecurityExtractor,
    PIBreachHistoryExtractor,
    # Corporate Footprint
    PIWebsiteQualityExtractor,
    BioCompletenessExtractor,
    PracticeClarityExtractor,
    PublicationsExtractor,
    CommunityInvolvementExtractor,
    DiversityExtractor,
    # Litigation History
    MalpracticeSuitsExtractor,
    FeeDisputesLitigationExtractor,
    RegulatoryEnforcementExtractor,
    CivilLitigationExtractor,
    BankruptcyExtractor,
    # Categorical
    ProfessionClassificationExtractor,
    FirmSizeExtractor,
    AnnualRevenueExtractor,
)

__all__ = [
    # Network Authority
    "PeerRankingExtractor",
    "ClientQualityExtractor",
    "ReferralQualityExtractor",
    "AssociationLeadershipExtractor",
    "ThoughtLeadershipExtractor",
    "PanelMembershipExtractor",
    # Regulatory Standing
    "LicenseStatusExtractor",
    "DisciplinaryHistoryExtractor",
    "MalpracticeRecordExtractor",
    "CEComplianceExtractor",
    "SpecialtyCertificationExtractor",
    "PeerReviewExtractor",
    "PCAOBStandingExtractor",
    # Firm Stability
    "YearsInPracticeExtractor",
    "PartnerStabilityExtractor",
    "StaffRetentionExtractor",
    "OfficeStabilityExtractor",
    "PIFinancialStabilityExtractor",
    "SuccessionPlanningExtractor",
    # Practice Quality
    "OutcomePatternsExtractor",
    "ClientReviewsExtractor",
    "WorkQualityExtractor",
    "FeeDisputeExtractor",
    "ComplaintHistoryExtractor",
    # Technical Infrastructure
    "PITLSScoreExtractor",
    "PIEmailAuthExtractor",
    "PISecurityHeadersExtractor",
    "PortalSecurityExtractor",
    "PIBreachHistoryExtractor",
    # Corporate Footprint
    "PIWebsiteQualityExtractor",
    "BioCompletenessExtractor",
    "PracticeClarityExtractor",
    "PublicationsExtractor",
    "CommunityInvolvementExtractor",
    "DiversityExtractor",
    # Litigation History
    "MalpracticeSuitsExtractor",
    "FeeDisputesLitigationExtractor",
    "RegulatoryEnforcementExtractor",
    "CivilLitigationExtractor",
    "BankruptcyExtractor",
    # Categorical
    "ProfessionClassificationExtractor",
    "FirmSizeExtractor",
    "AnnualRevenueExtractor",
]
from . import phase_6_extractors
