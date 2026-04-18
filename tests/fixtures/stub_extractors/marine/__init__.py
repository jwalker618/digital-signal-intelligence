"""
Marine Stub Extractors

Marine-specific data source simulations organized by signal group:
- network_and_operational.py: Network authority + operational telemetry signals
- safety_fleet_sanctions.py: Safety compliance + fleet profile + sanctions signals
- environmental_footprint_structured_categorical.py: Environmental, footprint, structured, categorical
"""

from .network_and_operational import (
    # Network Authority
    ClassificationSocietyExtractor,
    PIClubExtractor,
    ChartererQualityExtractor,
    MarineBankingRelationshipExtractor,
    FlagStateExtractor,
    MarineIndustryAssociationExtractor,
    TechnicalManagerExtractor,
    PortRelationshipExtractor,
    # Operational Telemetry
    AISComplianceExtractor,
    DarkActivityExtractor,
    RouteRiskExtractor,
    PSCRegionExposureExtractor,
    OperationalEfficiencyExtractor,
    WeatherRoutingExtractor,
)

from .safety_fleet_sanctions import (
    # Safety Compliance
    PSCDetentionExtractor,
    PSCDeficiencyExtractor,
    ClassStatusExtractor,
    ISMComplianceExtractor,
    CasualtyHistoryExtractor,
    TotalLossHistoryExtractor,
    # Fleet Profile
    FleetAgeExtractor,
    FleetStabilityExtractor,
    VesselQualityExtractor,
    CrewCertificationExtractor,
    ManagementConsistencyExtractor,
    # Sanctions Compliance
    SanctionsStatusExtractor,
    OwnershipTransparencyExtractor,
    JurisdictionRiskExtractor,
    STSPatternExtractor,
    HistoricalSanctionsExtractor,
)

from .environmental_footprint_structured_categorical import (
    # Environmental
    IMO2020ComplianceExtractor,
    BWMComplianceExtractor,
    CIIRatingExtractor,
    EnvironmentalIncidentExtractor,
    # Corporate Footprint
    MarineWebsiteQualityExtractor,
    FleetListDisclosureExtractor,
    MarineSustainabilityReportingExtractor,
    SafetyCultureExtractor,
    CrewWelfareExtractor,
    MarineIndustryPresenceExtractor,
    # Structured Data
    VettingExtractor,
    MarineESGRatingExtractor,
    MarineCreditRatingExtractor,
    # Categorical
    OperatorClassificationExtractor,
    VesselCategoryExtractor,
    TradingPatternExtractor,
    FlagStateQualityExtractor,
    MarineFleetAgeExtractor,
)

__all__ = [
    # Network Authority
    "ClassificationSocietyExtractor",
    "PIClubExtractor",
    "ChartererQualityExtractor",
    "MarineBankingRelationshipExtractor",
    "FlagStateExtractor",
    "MarineIndustryAssociationExtractor",
    "TechnicalManagerExtractor",
    "PortRelationshipExtractor",
    # Operational Telemetry
    "AISComplianceExtractor",
    "DarkActivityExtractor",
    "RouteRiskExtractor",
    "PSCRegionExposureExtractor",
    "OperationalEfficiencyExtractor",
    "WeatherRoutingExtractor",
    # Safety Compliance
    "PSCDetentionExtractor",
    "PSCDeficiencyExtractor",
    "ClassStatusExtractor",
    "ISMComplianceExtractor",
    "CasualtyHistoryExtractor",
    "TotalLossHistoryExtractor",
    # Fleet Profile
    "FleetAgeExtractor",
    "FleetStabilityExtractor",
    "VesselQualityExtractor",
    "CrewCertificationExtractor",
    "ManagementConsistencyExtractor",
    # Sanctions Compliance
    "SanctionsStatusExtractor",
    "OwnershipTransparencyExtractor",
    "JurisdictionRiskExtractor",
    "STSPatternExtractor",
    "HistoricalSanctionsExtractor",
    # Environmental
    "IMO2020ComplianceExtractor",
    "BWMComplianceExtractor",
    "CIIRatingExtractor",
    "EnvironmentalIncidentExtractor",
    # Corporate Footprint
    "MarineWebsiteQualityExtractor",
    "FleetListDisclosureExtractor",
    "MarineSustainabilityReportingExtractor",
    "SafetyCultureExtractor",
    "CrewWelfareExtractor",
    "MarineIndustryPresenceExtractor",
    # Structured Data
    "VettingExtractor",
    "MarineESGRatingExtractor",
    "MarineCreditRatingExtractor",
    # Categorical
    "OperatorClassificationExtractor",
    "VesselCategoryExtractor",
    "TradingPatternExtractor",
    "FlagStateQualityExtractor",
    "MarineFleetAgeExtractor",
]
from . import phase_3_extractors
