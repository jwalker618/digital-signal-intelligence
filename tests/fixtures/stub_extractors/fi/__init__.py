"""
FI (Financial Institutions) Stub Extractors

Financial institution-specific data source simulations organized by signal group:
- network_and_regulatory.py: Network authority + regulatory compliance signals
- financial_and_governance.py: Financial condition + governance signals
- operational_cyber_footprint_categorical.py: Operational risk, cyber, footprint, structured, categorical
"""

from .network_and_regulatory import (
    # Network Authority
    CorrespondentQualityExtractor,
    FHLBMembershipExtractor,
    ClearingRelationshipExtractor,
    FIAuditorQualityExtractor,
    LegalCounselExtractor,
    FIIndustryAssociationExtractor,
    FICreditRatingExtractor,
    # Regulatory Compliance
    ExaminationRatingExtractor,
    EnforcementActionExtractor,
    InformalActionExtractor,
    CRARatingExtractor,
    BSAAMLExtractor,
    FairLendingExtractor,
    ConsumerComplianceExtractor,
)

from .financial_and_governance import (
    # Financial Condition
    CapitalRatioExtractor,
    AssetQualityExtractor,
    LiquidityExtractor,
    EarningsExtractor,
    ConcentrationExtractor,
    InterestRateRiskExtractor,
    GrowthRateExtractor,
    # Governance
    FIBoardIndependenceExtractor,
    BoardExpertiseExtractor,
    FIExecutiveStabilityExtractor,
    RiskCommitteeExtractor,
    AuditCommitteeExtractor,
    RelatedPartyExtractor,
)

from .operational_cyber_footprint_categorical import (
    # Operational Risk
    CFPBComplaintExtractor,
    BBBComplaintExtractor,
    FILitigationExtractor,
    FIBreachHistoryExtractor,
    OperationalIncidentExtractor,
    # Cyber Security
    FITLSConfigExtractor,
    FIEmailAuthExtractor,
    FISecurityHeadersExtractor,
    FINetworkExposureExtractor,
    FICVEExposureExtractor,
    FISecurityRatingExtractor,
    # Corporate Footprint
    InvestorRelationsExtractor,
    FIDisclosureQualityExtractor,
    FISecurityPageExtractor,
    FIHiringSignalsExtractor,
    FIESGReportingExtractor,
    CommunityPresenceExtractor,
    # Structured Data
    FIESGRatingExtractor,
    PeerBenchmarkExtractor,
    # Categorical
    InstitutionTypeExtractor,
    RegulatoryAuthorityExtractor,
    AssetSizeExtractor,
    PubliclyTradedExtractor,
)

__all__ = [
    # Network Authority
    "CorrespondentQualityExtractor",
    "FHLBMembershipExtractor",
    "ClearingRelationshipExtractor",
    "FIAuditorQualityExtractor",
    "LegalCounselExtractor",
    "FIIndustryAssociationExtractor",
    "FICreditRatingExtractor",
    # Regulatory Compliance
    "ExaminationRatingExtractor",
    "EnforcementActionExtractor",
    "InformalActionExtractor",
    "CRARatingExtractor",
    "BSAAMLExtractor",
    "FairLendingExtractor",
    "ConsumerComplianceExtractor",
    # Financial Condition
    "CapitalRatioExtractor",
    "AssetQualityExtractor",
    "LiquidityExtractor",
    "EarningsExtractor",
    "ConcentrationExtractor",
    "InterestRateRiskExtractor",
    "GrowthRateExtractor",
    # Governance
    "FIBoardIndependenceExtractor",
    "BoardExpertiseExtractor",
    "FIExecutiveStabilityExtractor",
    "RiskCommitteeExtractor",
    "AuditCommitteeExtractor",
    "RelatedPartyExtractor",
    # Operational Risk
    "CFPBComplaintExtractor",
    "BBBComplaintExtractor",
    "FILitigationExtractor",
    "FIBreachHistoryExtractor",
    "OperationalIncidentExtractor",
    # Cyber Security
    "FITLSConfigExtractor",
    "FIEmailAuthExtractor",
    "FISecurityHeadersExtractor",
    "FINetworkExposureExtractor",
    "FICVEExposureExtractor",
    "FISecurityRatingExtractor",
    # Corporate Footprint
    "InvestorRelationsExtractor",
    "FIDisclosureQualityExtractor",
    "FISecurityPageExtractor",
    "FIHiringSignalsExtractor",
    "FIESGReportingExtractor",
    "CommunityPresenceExtractor",
    # Structured Data
    "FIESGRatingExtractor",
    "PeerBenchmarkExtractor",
    # Categorical
    "InstitutionTypeExtractor",
    "RegulatoryAuthorityExtractor",
    "AssetSizeExtractor",
    "PubliclyTradedExtractor",
]
from . import phase_7_extractors
