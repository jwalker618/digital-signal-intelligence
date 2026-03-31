"""D&O Aggregators"""

from .aggregators import (
    # Network Authority
    AuditorQualityAggregator,
    LegalCounselAggregator,
    DOBankingRelationshipAggregator,
    InvestorQualityAggregator,
    BoardNetworkAggregator,
    IndexInclusionAggregator,
    AnalystCoverageAggregator,
    # Governance
    BoardIndependenceAggregator,
    BoardDiversityAggregator,
    CEOChairSeparationAggregator,
    CommitteeStructureAggregator,
    BoardRefreshmentAggregator,
    RelatedPartyAggregator,
    CompensationStructureAggregator,
    ShareholderRightsAggregator,
    # Financial
    AuditOpinionAggregator,
    InternalControlsAggregator,
    RestatementAggregator,
    FilingTimelinessAggregator,
    RevenueRecognitionAggregator,
    DebtCovenantAggregator,
    StockVolatilityAggregator,
    ShortInterestAggregator,
    # Litigation
    SecuritiesLitigationAggregator,
    DerivativeLitigationAggregator,
    SECEnforcementAggregator,
    DORegulatoryActionAggregator,
    PendingLitigationAggregator,
    WhistleblowerAggregator,
    # Executive
    ExecutiveStabilityAggregator,
    CFOQualityAggregator,
    InsiderTradingAggregator,
    ExecutiveBackgroundAggregator,
    TradingPlanAggregator,
    # Corporate Footprint
    InvestorRelationsAggregator,
    GovernancePageAggregator,
    ESGReportingAggregator,
    PressReleaseAggregator,
    LeadershipVisibilityAggregator,
    HiringSignalsAggregator,
    # Structured Data
    ESGRatingAggregator,
    GovernanceRatingAggregator,
    ISSGovernanceAggregator,
    # Categorical
    CompanyTypeAggregator,
    DOIndustryAggregator,
    StockExchangeAggregator,
)

__all__ = [
    "AuditorQualityAggregator", "LegalCounselAggregator", "DOBankingRelationshipAggregator",
    "InvestorQualityAggregator", "BoardNetworkAggregator", "IndexInclusionAggregator",
    "AnalystCoverageAggregator", "BoardIndependenceAggregator", "BoardDiversityAggregator",
    "CEOChairSeparationAggregator", "CommitteeStructureAggregator", "BoardRefreshmentAggregator",
    "RelatedPartyAggregator", "CompensationStructureAggregator", "ShareholderRightsAggregator",
    "AuditOpinionAggregator", "InternalControlsAggregator", "RestatementAggregator",
    "FilingTimelinessAggregator", "RevenueRecognitionAggregator", "DebtCovenantAggregator",
    "StockVolatilityAggregator", "ShortInterestAggregator", "SecuritiesLitigationAggregator",
    "DerivativeLitigationAggregator", "SECEnforcementAggregator", "DORegulatoryActionAggregator",
    "PendingLitigationAggregator", "WhistleblowerAggregator", "ExecutiveStabilityAggregator",
    "CFOQualityAggregator", "InsiderTradingAggregator", "ExecutiveBackgroundAggregator",
    "TradingPlanAggregator", "InvestorRelationsAggregator", "GovernancePageAggregator",
    "ESGReportingAggregator", "PressReleaseAggregator", "LeadershipVisibilityAggregator",
    "HiringSignalsAggregator", "ESGRatingAggregator", "GovernanceRatingAggregator",
    "ISSGovernanceAggregator", "CompanyTypeAggregator", "DOIndustryAggregator",
    "StockExchangeAggregator",
]
from . import phase_6_aggregators
