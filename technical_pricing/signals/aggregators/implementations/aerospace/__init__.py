"""
Aerospace Aggregators

Production-ready aggregators for aerospace coverage signals.
Organized by signal group for clarity.
"""

from .network_authority import (
    AllianceMembershipAggregator,
    CodeshareQualityAggregator,
    LessorQualityAggregator,
    OEMRelationshipAggregator,
    MROQualityAggregator,
)

from .safety_record import (
    AviationSafetyAggregator,
    AccidentHistoryAggregator,
    IncidentHistoryAggregator,
    AccidentRateAggregator,
    FatalityHistoryAggregator,
    InvestigationFindingsAggregator,
)

from .regulatory_compliance import (
    CertificateStatusAggregator,
    IOSAAuditAggregator,
    RampInspectionAggregator,
    EUSafetyListAggregator,
    StateSafetyAggregator,
)

from .operational_and_others import (
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
    # Network Authority
    "AllianceMembershipAggregator",
    "CodeshareQualityAggregator",
    "LessorQualityAggregator",
    "OEMRelationshipAggregator",
    "MROQualityAggregator",
    # Safety Record
    "AviationSafetyAggregator",
    "AccidentHistoryAggregator",
    "IncidentHistoryAggregator",
    "AccidentRateAggregator",
    "FatalityHistoryAggregator",
    "InvestigationFindingsAggregator",
    # Regulatory Compliance
    "CertificateStatusAggregator",
    "IOSAAuditAggregator",
    "RampInspectionAggregator",
    "EUSafetyListAggregator",
    "StateSafetyAggregator",
    # Operational Quality
    "FlightOperationsAggregator",
    "CrewTrainingAggregator",
    "OperationalComplexityAggregator",
    # Fleet Quality
    "FleetQualityAggregator",
    "OrderBacklogAggregator",
    "MaintenanceIndicatorsAggregator",
    # Route Risk
    "RouteRiskAggregator",
    # Corporate Governance
    "SafetyLeadershipAggregator",
    # Financial
    "MarketPositionAggregator",
    "GovernmentSupportAggregator",
]
