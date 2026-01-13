"""
DSI Stub Extractors by Coverage Domain

This package contains stub extractor implementations organized by coverage domain.
All stubs return randomized but structurally realistic data.

Structure:
    common.py       - Cross-coverage reusable extractors
    aerospace.py    - Aviation-specific extractors (Part 1: Network Authority, Safety)
    aerospace_part3.py - Aviation-specific extractors (Part 2: Regulatory, Fleet, Route, Governance)
    cyber.py        - Cybersecurity extractors (TODO)
    do.py           - Directors & Officers extractors (TODO)
    energy.py       - Energy sector extractors (TODO)
    fi.py           - Financial Institutions extractors (TODO)
    marine.py       - Marine/shipping extractors (TODO)
    pi.py           - Professional Indemnity extractors (TODO)

Common Extractors (reusable across coverages):
    - CreditRatingExtractor: Credit ratings from major agencies
    - CorporateRegistryExtractor: Company structure, leadership, incorporation
    - RegulatoryEnforcementExtractor: Enforcement actions (parameterized by regulator)
    - IndustryAssociationExtractor: Industry body memberships
    - PublicFinancialsExtractor: Financial filings and metrics
    - IncidentHistoryExtractor: Generic incident/event history

Aerospace Extractors:
    Network Authority:
        - AirlineAllianceExtractor: Alliance membership (Star, oneworld, SkyTeam)
        - CodesharePartnershipExtractor: Codeshare and interline partnerships
        - AircraftLessorExtractor: Lessor relationships and quality
        - OEMRelationshipExtractor: Boeing/Airbus/Embraer relationships
        - MROProviderExtractor: Maintenance provider data
    
    Safety Record:
        - AviationSafetyDatabaseExtractor: Accident/incident history
    
    Regulatory Compliance:
        - OperatingCertificateExtractor: AOC status, regulator info
        - IOSARegistryExtractor: IOSA registration and audit data
        - RampInspectionExtractor: SAFA/SACA results
        - EUSafetyListExtractor: EU banned carrier list
        - StateSafetyExtractor: ICAO USOAP scores
    
    Operational Quality:
        - FlightOperationsExtractor: OTP, dispatch reliability
        - CrewTrainingExtractor: Crew experience, training programs
        - OperationalComplexityExtractor: Network complexity, growth
    
    Fleet Quality:
        - FleetRegistryExtractor: Fleet composition, age, types
        - OrderBacklogExtractor: Aircraft orders
        - MaintenanceIndicatorsExtractor: Maintenance quality metrics
    
    Route Risk:
        - RouteRiskExtractor: Conflict zones, challenging airports
    
    Corporate Governance:
        - SafetyLeadershipExtractor: CSO, SMS, safety culture
    
    Financial:
        - MarketPositionExtractor: Market share, competitive position
        - GovernmentSupportExtractor: State ownership, subsidies
"""

# =============================================================================
# COMMON EXTRACTORS
# =============================================================================
from .stubs.common import (
    CreditRatingExtractor,
    CorporateRegistryExtractor,
    RegulatoryEnforcementExtractor,
    IndustryAssociationExtractor,
    PublicFinancialsExtractor,
    IncidentHistoryExtractor,
)

# =============================================================================
# AEROSPACE EXTRACTORS
# =============================================================================
from .stubs.aerospace import (
    # Network Authority
    AirlineAllianceExtractor,
    CodesharePartnershipExtractor,
    AircraftLessorExtractor,
    OEMRelationshipExtractor,
    MROProviderExtractor,
    # Safety Record
    AviationSafetyDatabaseExtractor,
)

from .stubs.aerospace_part2 import (
    # Regulatory Compliance
    OperatingCertificateExtractor,
    IOSARegistryExtractor,
    RampInspectionExtractor,
    EUSafetyListExtractor,
    StateSafetyExtractor,
    # Operational Quality
    FlightOperationsExtractor,
    # Fleet Quality
    FleetRegistryExtractor,
    OrderBacklogExtractor,
)

from .stubs.aerospace_part3 import (
    # Operational Quality (continued)
    CrewTrainingExtractor,
    OperationalComplexityExtractor,
    # Fleet Quality (continued)
    MaintenanceIndicatorsExtractor,
    # Route Risk
    RouteRiskExtractor,
    # Corporate Governance
    SafetyLeadershipExtractor,
    # Financial
    MarketPositionExtractor,
    GovernmentSupportExtractor,
)

__all__ = [
    # Common
    "CreditRatingExtractor",
    "CorporateRegistryExtractor",
    "RegulatoryEnforcementExtractor",
    "IndustryAssociationExtractor",
    "PublicFinancialsExtractor",
    "IncidentHistoryExtractor",
    # Aerospace - Network Authority
    "AirlineAllianceExtractor",
    "CodesharePartnershipExtractor",
    "AircraftLessorExtractor",
    "OEMRelationshipExtractor",
    "MROProviderExtractor",
    # Aerospace - Safety Record
    "AviationSafetyDatabaseExtractor",
    # Aerospace - Regulatory Compliance
    "OperatingCertificateExtractor",
    "IOSARegistryExtractor",
    "RampInspectionExtractor",
    "EUSafetyListExtractor",
    "StateSafetyExtractor",
    # Aerospace - Operational Quality
    "FlightOperationsExtractor",
    "CrewTrainingExtractor",
    "OperationalComplexityExtractor",
    # Aerospace - Fleet Quality
    "FleetRegistryExtractor",
    "OrderBacklogExtractor",
    "MaintenanceIndicatorsExtractor",
    # Aerospace - Route Risk
    "RouteRiskExtractor",
    # Aerospace - Corporate Governance
    "SafetyLeadershipExtractor",
    # Aerospace - Financial
    "MarketPositionExtractor",
    "GovernmentSupportExtractor",
]
