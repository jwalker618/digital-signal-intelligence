"""PI (Professional Indemnity) Aggregators"""

from .aggregators import (
    # Network Authority
    PeerRankingAggregator,
    ClientQualityAggregator,
    ReferralQualityAggregator,
    AssociationLeadershipAggregator,
    ThoughtLeadershipAggregator,
    PanelMembershipAggregator,
    # Regulatory Standing
    LicenseStatusAggregator,
    DisciplinaryHistoryAggregator,
    MalpracticeRecordAggregator,
    CEComplianceAggregator,
    SpecialtyCertificationAggregator,
    PeerReviewAggregator,
    PCAOBStandingAggregator,
    # Firm Stability
    YearsInPracticeAggregator,
    PartnerStabilityAggregator,
    StaffRetentionAggregator,
    OfficeStabilityAggregator,
    PIFinancialStabilityAggregator,
    SuccessionPlanningAggregator,
    # Practice Quality
    OutcomePatternsAggregator,
    ClientReviewsAggregator,
    WorkQualityAggregator,
    FeeDisputeAggregator,
    ComplaintHistoryAggregator,
    # Technical Infrastructure
    PITLSScoreAggregator,
    PIEmailAuthAggregator,
    PISecurityHeadersAggregator,
    PortalSecurityAggregator,
    PIBreachHistoryAggregator,
    # Corporate Footprint
    PIWebsiteQualityAggregator,
    BioCompletenessAggregator,
    PracticeClarityAggregator,
    PublicationsAggregator,
    CommunityInvolvementAggregator,
    DiversityAggregator,
    # Litigation History
    MalpracticeSuitsAggregator,
    FeeDisputesLitigationAggregator,
    PIRegulatoryEnforcementAggregator,
    CivilLitigationAggregator,
    BankruptcyAggregator,
    # Categorical
    ProfessionClassificationAggregator,
    FirmSizeAggregator,
    AnnualRevenueAggregator,
)

__all__ = [
    # Network Authority
    "PeerRankingAggregator",
    "ClientQualityAggregator",
    "ReferralQualityAggregator",
    "AssociationLeadershipAggregator",
    "ThoughtLeadershipAggregator",
    "PanelMembershipAggregator",
    # Regulatory Standing
    "LicenseStatusAggregator",
    "DisciplinaryHistoryAggregator",
    "MalpracticeRecordAggregator",
    "CEComplianceAggregator",
    "SpecialtyCertificationAggregator",
    "PeerReviewAggregator",
    "PCAOBStandingAggregator",
    # Firm Stability
    "YearsInPracticeAggregator",
    "PartnerStabilityAggregator",
    "StaffRetentionAggregator",
    "OfficeStabilityAggregator",
    "PIFinancialStabilityAggregator",
    "SuccessionPlanningAggregator",
    # Practice Quality
    "OutcomePatternsAggregator",
    "ClientReviewsAggregator",
    "WorkQualityAggregator",
    "FeeDisputeAggregator",
    "ComplaintHistoryAggregator",
    # Technical Infrastructure
    "PITLSScoreAggregator",
    "PIEmailAuthAggregator",
    "PISecurityHeadersAggregator",
    "PortalSecurityAggregator",
    "PIBreachHistoryAggregator",
    # Corporate Footprint
    "PIWebsiteQualityAggregator",
    "BioCompletenessAggregator",
    "PracticeClarityAggregator",
    "PublicationsAggregator",
    "CommunityInvolvementAggregator",
    "DiversityAggregator",
    # Litigation History
    "MalpracticeSuitsAggregator",
    "FeeDisputesLitigationAggregator",
    "PIRegulatoryEnforcementAggregator",
    "CivilLitigationAggregator",
    "BankruptcyAggregator",
    # Categorical
    "ProfessionClassificationAggregator",
    "FirmSizeAggregator",
    "AnnualRevenueAggregator",
]
