"""
DSI Aerospace Stub Extractors

Network Authority, Safety Record, Regulatory Compliance, Fleet Management,
Operational Excellence, and Other aerospace-related extractors.
"""

# Network Authority and Safety Record (network_and_safety.py)
from .network_and_safety import (
    AirlineAllianceExtractor,
    CodesharePartnershipExtractor,
    AircraftLessorExtractor,
    OEMRelationshipExtractor,
    MROProviderExtractor,
    AviationSafetyDatabaseExtractor,
)

# Regulatory Compliance and Fleet Management (regulatory_and_fleet.py)
from .regulatory_and_fleet import (
    OperatingCertificateExtractor,
    IOSARegistryExtractor,
    RampInspectionExtractor,
    EUSafetyListExtractor,
    StateSafetyExtractor,
    FlightOperationsExtractor,
    FleetRegistryExtractor,
    OrderBacklogExtractor,
)

# Operational Excellence and Others (operational_and_others.py)
from .operational_and_others import (
    CrewTrainingExtractor,
    OperationalComplexityExtractor,
    RouteRiskExtractor,
    SafetyLeadershipExtractor,
    MarketPositionExtractor,
    GovernmentSupportExtractor,
    MaintenanceIndicatorsExtractor,
)

__all__ = [
    # Network Authority
    "AirlineAllianceExtractor",
    "CodesharePartnershipExtractor",
    "AircraftLessorExtractor",
    "OEMRelationshipExtractor",
    "MROProviderExtractor",
    # Safety Record
    "AviationSafetyDatabaseExtractor",
    # Regulatory Compliance
    "OperatingCertificateExtractor",
    "IOSARegistryExtractor",
    "RampInspectionExtractor",
    "EUSafetyListExtractor",
    "StateSafetyExtractor",
    # Flight Operations
    "FlightOperationsExtractor",
    # Fleet Management
    "FleetRegistryExtractor",
    "OrderBacklogExtractor",
    # Operational Excellence
    "CrewTrainingExtractor",
    "OperationalComplexityExtractor",
    "RouteRiskExtractor",
    # Safety Leadership
    "SafetyLeadershipExtractor",
    # Market Position
    "MarketPositionExtractor",
    "GovernmentSupportExtractor",
    # Maintenance
    "MaintenanceIndicatorsExtractor",
]
from . import phase_5_extractors
