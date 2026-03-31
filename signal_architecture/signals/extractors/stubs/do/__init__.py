"""
D&O Stub Extractors

Directors & Officers coverage data source simulations:
- network_and_governance.py: Auditor, counsel, investors, board
- financial_litigation_executive.py: Audit, controls, litigation, executive
- footprint_structured_categorical.py: IR, ESG, governance ratings, company type
"""

from .network_and_governance import (
    # Network Authority
    AuditorQualityExtractor,
    LegalCounselExtractor,
    BankingRelationshipExtractor,
    InvestorQualityExtractor,
    BoardNetworkExtractor,
    IndexInclusionExtractor,
    AnalystCoverageExtractor,
    # Governance
    BoardIndependenceExtractor,
    BoardDiversityExtractor,
    CEOChairSeparationExtractor,
    CommitteeStructureExtractor,
    BoardRefreshmentExtractor,
    RelatedPartyExtractor,
    CompensationStructureExtractor,
    ShareholderRightsExtractor,
)

from .financial_litigation_executive import (
    # Financial
    AuditOpinionExtractor,
    InternalControlsExtractor,
    RestatementExtractor,
    FilingTimelinessExtractor,
    RevenueRecognitionExtractor,
    DebtCovenantExtractor,
    StockVolatilityExtractor,
    ShortInterestExtractor,
    # Litigation
    SecuritiesLitigationExtractor,
    DerivativeLitigationExtractor,
    SECEnforcementExtractor,
    RegulatoryActionExtractor,
    PendingLitigationExtractor,
    WhistleblowerExtractor,
    # Executive
    ExecutiveStabilityExtractor,
    CFOQualityExtractor,
    InsiderTradingExtractor,
    ExecutiveBackgroundExtractor,
    TradingPlanExtractor,
)

from .footprint_structured_categorical import (
    # Corporate Footprint
    InvestorRelationsExtractor,
    GovernancePageExtractor,
    ESGReportingExtractor,
    PressReleaseExtractor,
    LeadershipVisibilityExtractor,
    HiringSignalsExtractor,
    # Structured Data
    ESGRatingExtractor,
    GovernanceRatingExtractor,
    ISSGovernanceExtractor,
    # Categorical
    CompanyTypeExtractor,
    DOIndustryExtractor,
    StockExchangeExtractor,
)

__all__ = [
    # Network Authority
    "AuditorQualityExtractor",
    "LegalCounselExtractor",
    "BankingRelationshipExtractor",
    "InvestorQualityExtractor",
    "BoardNetworkExtractor",
    "IndexInclusionExtractor",
    "AnalystCoverageExtractor",
    # Governance
    "BoardIndependenceExtractor",
    "BoardDiversityExtractor",
    "CEOChairSeparationExtractor",
    "CommitteeStructureExtractor",
    "BoardRefreshmentExtractor",
    "RelatedPartyExtractor",
    "CompensationStructureExtractor",
    "ShareholderRightsExtractor",
    # Financial
    "AuditOpinionExtractor",
    "InternalControlsExtractor",
    "RestatementExtractor",
    "FilingTimelinessExtractor",
    "RevenueRecognitionExtractor",
    "DebtCovenantExtractor",
    "StockVolatilityExtractor",
    "ShortInterestExtractor",
    # Litigation
    "SecuritiesLitigationExtractor",
    "DerivativeLitigationExtractor",
    "SECEnforcementExtractor",
    "RegulatoryActionExtractor",
    "PendingLitigationExtractor",
    "WhistleblowerExtractor",
    # Executive
    "ExecutiveStabilityExtractor",
    "CFOQualityExtractor",
    "InsiderTradingExtractor",
    "ExecutiveBackgroundExtractor",
    "TradingPlanExtractor",
    # Corporate Footprint
    "InvestorRelationsExtractor",
    "GovernancePageExtractor",
    "ESGReportingExtractor",
    "PressReleaseExtractor",
    "LeadershipVisibilityExtractor",
    "HiringSignalsExtractor",
    # Structured Data
    "ESGRatingExtractor",
    "GovernanceRatingExtractor",
    "ISSGovernanceExtractor",
    # Categorical
    "CompanyTypeExtractor",
    "DOIndustryExtractor",
    "StockExchangeExtractor",
]
from . import phase_6_extractors
