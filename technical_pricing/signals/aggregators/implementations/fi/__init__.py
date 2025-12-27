"""FI (Financial Institutions) Aggregators"""

from .aggregators import (
    # Network Authority
    CorrespondentQualityAggregator,
    FHLBMembershipAggregator,
    ClearingRelationshipAggregator,
    FIAuditorQualityAggregator,
    LegalCounselAggregator,
    FIIndustryAssociationAggregator,
    FICreditRatingAggregator,
    # Regulatory Compliance
    ExaminationRatingAggregator,
    EnforcementActionAggregator,
    InformalActionAggregator,
    CRARatingAggregator,
    BSAAMLAggregator,
    FairLendingAggregator,
    ConsumerComplianceAggregator,
    # Financial Condition
    CapitalRatioAggregator,
    AssetQualityAggregator,
    LiquidityAggregator,
    EarningsAggregator,
    ConcentrationAggregator,
    InterestRateRiskAggregator,
    GrowthRateAggregator,
    # Governance
    FIBoardIndependenceAggregator,
    BoardExpertiseAggregator,
    FIExecutiveStabilityAggregator,
    RiskCommitteeAggregator,
    AuditCommitteeAggregator,
    RelatedPartyAggregator,
    # Operational Risk
    CFPBComplaintAggregator,
    BBBComplaintAggregator,
    FILitigationAggregator,
    FIBreachHistoryAggregator,
    OperationalIncidentAggregator,
    # Cyber Security
    FITLSConfigAggregator,
    FIEmailAuthAggregator,
    FISecurityHeadersAggregator,
    FINetworkExposureAggregator,
    FICVEExposureAggregator,
    FISecurityRatingAggregator,
    # Corporate Footprint
    InvestorRelationsAggregator,
    FIDisclosureQualityAggregator,
    FISecurityPageAggregator,
    FIHiringSignalsAggregator,
    FIESGReportingAggregator,
    CommunityPresenceAggregator,
    # Structured Data
    FIESGRatingAggregator,
    PeerBenchmarkAggregator,
    # Categorical
    InstitutionTypeAggregator,
    RegulatoryAuthorityAggregator,
    AssetSizeAggregator,
    PubliclyTradedAggregator,
)

__all__ = [
    # Network Authority
    "CorrespondentQualityAggregator",
    "FHLBMembershipAggregator",
    "ClearingRelationshipAggregator",
    "FIAuditorQualityAggregator",
    "LegalCounselAggregator",
    "FIIndustryAssociationAggregator",
    "FICreditRatingAggregator",
    # Regulatory Compliance
    "ExaminationRatingAggregator",
    "EnforcementActionAggregator",
    "InformalActionAggregator",
    "CRARatingAggregator",
    "BSAAMLAggregator",
    "FairLendingAggregator",
    "ConsumerComplianceAggregator",
    # Financial Condition
    "CapitalRatioAggregator",
    "AssetQualityAggregator",
    "LiquidityAggregator",
    "EarningsAggregator",
    "ConcentrationAggregator",
    "InterestRateRiskAggregator",
    "GrowthRateAggregator",
    # Governance
    "FIBoardIndependenceAggregator",
    "BoardExpertiseAggregator",
    "FIExecutiveStabilityAggregator",
    "RiskCommitteeAggregator",
    "AuditCommitteeAggregator",
    "RelatedPartyAggregator",
    # Operational Risk
    "CFPBComplaintAggregator",
    "BBBComplaintAggregator",
    "FILitigationAggregator",
    "FIBreachHistoryAggregator",
    "OperationalIncidentAggregator",
    # Cyber Security
    "FITLSConfigAggregator",
    "FIEmailAuthAggregator",
    "FISecurityHeadersAggregator",
    "FINetworkExposureAggregator",
    "FICVEExposureAggregator",
    "FISecurityRatingAggregator",
    # Corporate Footprint
    "InvestorRelationsAggregator",
    "FIDisclosureQualityAggregator",
    "FISecurityPageAggregator",
    "FIHiringSignalsAggregator",
    "FIESGReportingAggregator",
    "CommunityPresenceAggregator",
    # Structured Data
    "FIESGRatingAggregator",
    "PeerBenchmarkAggregator",
    # Categorical
    "InstitutionTypeAggregator",
    "RegulatoryAuthorityAggregator",
    "AssetSizeAggregator",
    "PubliclyTradedAggregator",
]
