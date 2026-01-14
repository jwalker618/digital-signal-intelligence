"""
DSI Aggregator Implementations by Coverage Domain

Structure:
    common.py           - Cross-coverage reusable aggregators
    aerospace/          - Aviation-specific aggregators
        network_authority.py
        safety_record.py
        regulatory_compliance.py
        operational_and_others.py

Common Aggregators (reusable across coverages):
    - CreditRatingAggregator
    - CorporateGovernanceAggregator
    - RegulatoryEnforcementAggregator
    - IndustryEngagementAggregator
    - PublicFinancialsAggregator
    - IncidentHistoryAggregator

All aggregators are PRODUCTION READY and handle real data.
"""

# =============================================================================
# COMMON AGGREGATORS
# =============================================================================
from .common import (
    CreditRatingAggregator,
    CorporateGovernanceAggregator,
    RegulatoryEnforcementAggregator,
    IndustryEngagementAggregator,
    PublicFinancialsAggregator,
    IncidentHistoryAggregator,
)

# =============================================================================
# AEROSPACE AGGREGATORS
# =============================================================================
from .aerospace import (
    # Network Authority
    AllianceMembershipAggregator,
    CodeshareQualityAggregator,
    LessorQualityAggregator,
    OEMRelationshipAggregator,
    MROQualityAggregator,
    # Safety Record
    AviationSafetyAggregator,
    AccidentHistoryAggregator,
    IncidentHistoryAggregator as AeroIncidentHistoryAggregator,
    AccidentRateAggregator,
    FatalityHistoryAggregator,
    InvestigationFindingsAggregator,
    # Regulatory Compliance
    CertificateStatusAggregator,
    IOSAAuditAggregator,
    RampInspectionAggregator,
    EUSafetyListAggregator,
    StateSafetyAggregator,
    # Operational Quality
    FlightOperationsAggregator,
    CrewTrainingAggregator,
    OperationalComplexityAggregator,
    # Fleet Quality
    FleetQualityAggregator,
    OrderBacklogAggregator,
    MaintenanceIndicatorsAggregator,
    # Route Risk
    RouteRiskAggregator,
    # Corporate Governance
    SafetyLeadershipAggregator,
    # Financial
    MarketPositionAggregator,
    GovernmentSupportAggregator,
)

__all__ = [
    # Common
    "CreditRatingAggregator",
    "CorporateGovernanceAggregator",
    "RegulatoryEnforcementAggregator",
    "IndustryEngagementAggregator",
    "PublicFinancialsAggregator",
    "IncidentHistoryAggregator",
    # Aerospace
    "AllianceMembershipAggregator",
    "CodeshareQualityAggregator",
    "LessorQualityAggregator",
    "OEMRelationshipAggregator",
    "MROQualityAggregator",
    "AviationSafetyAggregator",
    "AccidentHistoryAggregator",
    "AeroIncidentHistoryAggregator",
    "AccidentRateAggregator",
    "FatalityHistoryAggregator",
    "InvestigationFindingsAggregator",
    "CertificateStatusAggregator",
    "IOSAAuditAggregator",
    "RampInspectionAggregator",
    "EUSafetyListAggregator",
    "StateSafetyAggregator",
    "FlightOperationsAggregator",
    "CrewTrainingAggregator",
    "OperationalComplexityAggregator",
    "FleetQualityAggregator",
    "OrderBacklogAggregator",
    "MaintenanceIndicatorsAggregator",
    "RouteRiskAggregator",
    "SafetyLeadershipAggregator",
    "MarketPositionAggregator",
    "GovernmentSupportAggregator",
]
