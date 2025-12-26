"""Aerospace Aggregators"""

from .aggregators import (
    # Network Authority
    AllianceMembershipAggregator,
    CodeshareQualityAggregator,
    LessorQualityAggregator,
    OEMRelationshipAggregator,
    MROQualityAggregator,
    # Safety Record
    AviationSafetyAggregator,
    AccidentHistoryAggregator,
    IncidentHistoryAggregator,
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
    "AllianceMembershipAggregator", "CodeshareQualityAggregator", "LessorQualityAggregator",
    "OEMRelationshipAggregator", "MROQualityAggregator", "AviationSafetyAggregator",
    "AccidentHistoryAggregator", "IncidentHistoryAggregator", "AccidentRateAggregator",
    "FatalityHistoryAggregator", "InvestigationFindingsAggregator", "CertificateStatusAggregator",
    "IOSAAuditAggregator", "RampInspectionAggregator", "EUSafetyListAggregator",
    "StateSafetyAggregator", "FlightOperationsAggregator", "CrewTrainingAggregator",
    "OperationalComplexityAggregator", "FleetQualityAggregator", "OrderBacklogAggregator",
    "MaintenanceIndicatorsAggregator", "RouteRiskAggregator", "SafetyLeadershipAggregator",
    "MarketPositionAggregator", "GovernmentSupportAggregator",
]

