"""Energy Aggregators"""
from .aggregators import (
    # Network Authority
    EnergyPartnerQualityAggregator, ContractorQualityAggregator, EnergyBankingRelationshipAggregator,
    InsuranceHistoryAggregator, RegulatorRelationshipAggregator, OfftakeQualityAggregator,
    # Safety Performance
    OSHATRIRAggregator, OSHAViolationsAggregator, BSEEIncidentAggregator, ProcessSafetyAggregator,
    FatalityHistoryAggregator, MajorIncidentAggregator, NearMissReportingAggregator,
    # Environmental
    EPAViolationAggregator, SpillHistoryAggregator, EmissionsComplianceAggregator,
    FlaringIntensityAggregator, MethaneEmissionsAggregator, RemediationAggregator,
    # Operational
    ProductionConsistencyAggregator, FacilityActivityAggregator, WellIntegrityAggregator,
    MaintenancePatternAggregator, OperationalEfficiencyAggregator,
    # Financial
    LeverageAggregator, AROCoverageAggregator, CapexTrendAggregator, RestructuringAggregator,
    # Asset Portfolio
    AssetAgeAggregator, ConcentrationAggregator, TechnologyProfileAggregator,
    DecommissioningAggregator, PermitStatusAggregator,
    # Corporate Footprint
    SafetyCommunicationAggregator, EnergyESGReportingAggregator, TechnicalHiringAggregator,
    IndustryPresenceAggregator, DisclosureQualityAggregator, HSELeadershipAggregator,
    # Structured Data
    EnergyESGRatingAggregator, BenchmarkAggregator,
    # Categorical
    OperatorTypeAggregator, OperationSegmentAggregator, GeographicFocusAggregator,
)

# Phase 5: All new energy segment-specific aggregators
from .phase5_aggregators import (
    # Upstream Deepwater
    BOPTestingComplianceAggregator, WellControlEventsAggregator, RigContractorQualityAggregator,
    SubseaEquipmentAgeAggregator, WaterDepthProfileAggregator, MetoceanExposureAggregator,
    BSEEComplianceDetailAggregator, SpudToProductionAggregator,
    # Upstream Onshore
    ProducedWaterManagementAggregator, H2SExposureAggregator, ArtificialLiftReliabilityAggregator,
    StateRegulatoryComplianceAggregator, WellVintageProfileAggregator,
    # Upstream Unconventional
    FracFleetQualityAggregator, WaterRecyclingRateAggregator, InducedSeismicityScoreAggregator,
    WellSpacingOptimisationAggregator, CompletionEfficiencyAggregator, PadDrillingIntensityAggregator,
    # Midstream
    PHMSAComplianceAggregator, InlineInspectionAggregator, CathodicProtectionAggregator,
    RightOfWayAggregator, SCADAMaturityAggregator, PipelineVintageAggregator, ThroughputConsistencyAggregator,
    # Downstream
    TurnaroundComplianceAggregator, PSMAuditFindingsAggregator, MechanicalIntegrityAggregator,
    FeedstockComplexityAggregator, BIExposureRatioAggregator, ProcessUnitCountAggregator,
    # Shared Renewable
    TechnologyMaturityAggregator, EPCContractorQualityAggregator, WarrantyCoverageAggregator,
    CapacityFactorAggregator, NatCatExposureAggregator, GridInterconnectionAggregator,
    PPAQualityAggregator, DegradationRateAggregator, CommissioningDefectsAggregator,
    ConstructionPhaseAggregator, EPCTrackRecordAggregator, SupplyChainQualityAggregator,
    # Offshore Wind
    InstallationVesselQualityAggregator, FoundationTypeAggregator, TurbinePlatformGenerationAggregator,
    CableRouteRiskAggregator, MarineWeatherExposureAggregator, CrewTransferSafetyAggregator,
    OfftakeContractQualityAggregator,
    # Onshore Renewable
    HailExposureAggregator, PanelTechnologyVintageAggregator, InverterReliabilityAggregator,
    CurtailmentRateAggregator, PortfolioGeographicSpreadAggregator,
    # Storage
    BatteryChemistryAggregator, ThermalManagementSystemAggregator, FireSuppressionCapabilityAggregator,
    BMSSophisticationAggregator, HydrogenStoragePressureAggregator, SafetyStandardComplianceAggregator,
    CellFormatMaturityAggregator, ElectrolyserTechnologyAggregator,
)

__all__ = [
    "EnergyPartnerQualityAggregator", "ContractorQualityAggregator", "EnergyBankingRelationshipAggregator",
    "InsuranceHistoryAggregator", "RegulatorRelationshipAggregator", "OfftakeQualityAggregator",
    "OSHATRIRAggregator", "OSHAViolationsAggregator", "BSEEIncidentAggregator", "ProcessSafetyAggregator",
    "FatalityHistoryAggregator", "MajorIncidentAggregator", "NearMissReportingAggregator",
    "EPAViolationAggregator", "SpillHistoryAggregator", "EmissionsComplianceAggregator",
    "FlaringIntensityAggregator", "MethaneEmissionsAggregator", "RemediationAggregator",
    "ProductionConsistencyAggregator", "FacilityActivityAggregator", "WellIntegrityAggregator",
    "MaintenancePatternAggregator", "OperationalEfficiencyAggregator",
    "LeverageAggregator", "AROCoverageAggregator", "CapexTrendAggregator", "RestructuringAggregator",
    "AssetAgeAggregator", "ConcentrationAggregator", "TechnologyProfileAggregator",
    "DecommissioningAggregator", "PermitStatusAggregator",
    "SafetyCommunicationAggregator", "EnergyESGReportingAggregator", "TechnicalHiringAggregator",
    "IndustryPresenceAggregator", "DisclosureQualityAggregator", "HSELeadershipAggregator",
    "EnergyESGRatingAggregator", "BenchmarkAggregator",
    "OperatorTypeAggregator", "OperationSegmentAggregator", "GeographicFocusAggregator",
    # Phase 5
    "BOPTestingComplianceAggregator", "WellControlEventsAggregator", "RigContractorQualityAggregator",
    "SubseaEquipmentAgeAggregator", "WaterDepthProfileAggregator", "MetoceanExposureAggregator",
    "BSEEComplianceDetailAggregator", "SpudToProductionAggregator",
    "ProducedWaterManagementAggregator", "H2SExposureAggregator", "ArtificialLiftReliabilityAggregator",
    "StateRegulatoryComplianceAggregator", "WellVintageProfileAggregator",
    "FracFleetQualityAggregator", "WaterRecyclingRateAggregator", "InducedSeismicityScoreAggregator",
    "WellSpacingOptimisationAggregator", "CompletionEfficiencyAggregator", "PadDrillingIntensityAggregator",
    "PHMSAComplianceAggregator", "InlineInspectionAggregator", "CathodicProtectionAggregator",
    "RightOfWayAggregator", "SCADAMaturityAggregator", "PipelineVintageAggregator", "ThroughputConsistencyAggregator",
    "TurnaroundComplianceAggregator", "PSMAuditFindingsAggregator", "MechanicalIntegrityAggregator",
    "FeedstockComplexityAggregator", "BIExposureRatioAggregator", "ProcessUnitCountAggregator",
    "TechnologyMaturityAggregator", "EPCContractorQualityAggregator", "WarrantyCoverageAggregator",
    "CapacityFactorAggregator", "NatCatExposureAggregator", "GridInterconnectionAggregator",
    "PPAQualityAggregator", "DegradationRateAggregator", "CommissioningDefectsAggregator",
    "ConstructionPhaseAggregator", "EPCTrackRecordAggregator", "SupplyChainQualityAggregator",
    "InstallationVesselQualityAggregator", "FoundationTypeAggregator", "TurbinePlatformGenerationAggregator",
    "CableRouteRiskAggregator", "MarineWeatherExposureAggregator", "CrewTransferSafetyAggregator",
    "OfftakeContractQualityAggregator",
    "HailExposureAggregator", "PanelTechnologyVintageAggregator", "InverterReliabilityAggregator",
    "CurtailmentRateAggregator", "PortfolioGeographicSpreadAggregator",
    "BatteryChemistryAggregator", "ThermalManagementSystemAggregator", "FireSuppressionCapabilityAggregator",
    "BMSSophisticationAggregator", "HydrogenStoragePressureAggregator", "SafetyStandardComplianceAggregator",
    "CellFormatMaturityAggregator", "ElectrolyserTechnologyAggregator",
]
