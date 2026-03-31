"""Marine Aggregators"""

from .aggregators import (
    # Network Authority
    ClassificationSocietyAggregator,
    PIClubAggregator,
    ChartererQualityAggregator,
    MarineBankingAggregator,
    FlagStateAggregator,
    MarineIndustryAssociationAggregator,
    TechnicalManagerAggregator,
    PortRelationshipAggregator,
    # Operational Telemetry
    AISComplianceAggregator,
    DarkActivityAggregator,
    RouteRiskAggregator,
    PSCRegionAggregator,
    OperationalEfficiencyAggregator,
    WeatherRoutingAggregator,
    # Safety Compliance
    PSCDetentionAggregator,
    PSCDeficiencyAggregator,
    ClassStatusAggregator,
    ISMComplianceAggregator,
    CasualtyHistoryAggregator,
    TotalLossHistoryAggregator,
    # Fleet Profile
    FleetAgeAggregator,
    FleetStabilityAggregator,
    VesselQualityAggregator,
    CrewCertificationAggregator,
    ManagementConsistencyAggregator,
    # Sanctions Compliance
    SanctionsStatusAggregator,
    OwnershipTransparencyAggregator,
    JurisdictionRiskAggregator,
    STSPatternAggregator,
    HistoricalSanctionsAggregator,
    # Environmental
    IMO2020ComplianceAggregator,
    BWMComplianceAggregator,
    CIIRatingAggregator,
    EnvironmentalIncidentAggregator,
    # Corporate Footprint
    MarineWebsiteQualityAggregator,
    FleetListDisclosureAggregator,
    MarineSustainabilityAggregator,
    SafetyCultureAggregator,
    CrewWelfareAggregator,
    MarineIndustryPresenceAggregator,
    # Structured Data
    VettingAggregator,
    MarineESGRatingAggregator,
    MarineCreditRatingAggregator,
    # Categorical
    OperatorClassificationAggregator,
    VesselCategoryAggregator,
    TradingPatternAggregator,
    FlagStateQualityAggregator,
    FleetAgeBandAggregator,
)

__all__ = [
    # Network Authority
    "ClassificationSocietyAggregator",
    "PIClubAggregator",
    "ChartererQualityAggregator",
    "MarineBankingAggregator",
    "FlagStateAggregator",
    "MarineIndustryAssociationAggregator",
    "TechnicalManagerAggregator",
    "PortRelationshipAggregator",
    # Operational Telemetry
    "AISComplianceAggregator",
    "DarkActivityAggregator",
    "RouteRiskAggregator",
    "PSCRegionAggregator",
    "OperationalEfficiencyAggregator",
    "WeatherRoutingAggregator",
    # Safety Compliance
    "PSCDetentionAggregator",
    "PSCDeficiencyAggregator",
    "ClassStatusAggregator",
    "ISMComplianceAggregator",
    "CasualtyHistoryAggregator",
    "TotalLossHistoryAggregator",
    # Fleet Profile
    "FleetAgeAggregator",
    "FleetStabilityAggregator",
    "VesselQualityAggregator",
    "CrewCertificationAggregator",
    "ManagementConsistencyAggregator",
    # Sanctions Compliance
    "SanctionsStatusAggregator",
    "OwnershipTransparencyAggregator",
    "JurisdictionRiskAggregator",
    "STSPatternAggregator",
    "HistoricalSanctionsAggregator",
    # Environmental
    "IMO2020ComplianceAggregator",
    "BWMComplianceAggregator",
    "CIIRatingAggregator",
    "EnvironmentalIncidentAggregator",
    # Corporate Footprint
    "MarineWebsiteQualityAggregator",
    "FleetListDisclosureAggregator",
    "MarineSustainabilityAggregator",
    "SafetyCultureAggregator",
    "CrewWelfareAggregator",
    "MarineIndustryPresenceAggregator",
    # Structured Data
    "VettingAggregator",
    "MarineESGRatingAggregator",
    "MarineCreditRatingAggregator",
    # Categorical
    "OperatorClassificationAggregator",
    "VesselCategoryAggregator",
    "TradingPatternAggregator",
    "FlagStateQualityAggregator",
    "FleetAgeBandAggregator",
]
from . import phase_3_aggregators
