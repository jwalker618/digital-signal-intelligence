"""Energy Stub Extractors"""

from .network_and_safety import (
    # Network Authority
    EnergyPartnerQualityExtractor,
    ContractorQualityExtractor,
    EnergyBankingRelationshipExtractor,
    InsuranceHistoryExtractor,
    RegulatorRelationshipExtractor,
    OfftakeQualityExtractor,
    # Safety Performance
    OSHATRIRExtractor,
    OSHAViolationsExtractor,
    BSEEIncidentExtractor,
    ProcessSafetyExtractor,
    FatalityHistoryExtractor,
    MajorIncidentExtractor,
    NearMissReportingExtractor,
)

from .enviromental_operational_financial import (
    # Environmental
    EPAViolationExtractor,
    SpillHistoryExtractor,
    EmissionsComplianceExtractor,
    FlaringIntensityExtractor,
    MethaneEmissionsExtractor,
    RemediationExtractor,
    # Operational
    ProductionConsistencyExtractor,
    FacilityActivityExtractor,
    WellIntegrityExtractor,
    MaintenancePatternExtractor,
    OperationalEfficiencyExtractor,
    # Financial
    LeverageExtractor,
    AROCoverageExtractor,
    CapexTrendExtractor,
    RestructuringExtractor,
)

from .asset_footprint_structured_categorical import (
    # Asset Portfolio
    AssetAgeExtractor,
    ConcentrationExtractor,
    TechnologyProfileExtractor,
    DecommissioningExtractor,
    PermitStatusExtractor,
    # Corporate Footprint
    SafetyCommunicationExtractor,
    EnergyESGReportingExtractor,
    TechnicalHiringExtractor,
    IndustryPresenceExtractor,
    DisclosureQualityExtractor,
    HSELeadershipExtractor,
    # Structured Data
    EnergyESGRatingExtractor,
    BenchmarkExtractor,
    # Categorical
    OperatorTypeExtractor,
    OperationSegmentExtractor,
    GeographicFocusExtractor,
)

# Phase 5: Upstream, Midstream & Downstream specialist signals
from .upstream_midstream_downstream import (
    # Upstream Deepwater
    BOPTestingComplianceExtractor,
    WellControlEventsExtractor,
    RigContractorQualityExtractor,
    SubseaEquipmentAgeExtractor,
    WaterDepthProfileExtractor,
    MetoceanExposureExtractor,
    BSEEComplianceDetailExtractor,
    SpudToProductionExtractor,
    # Upstream Onshore
    ProducedWaterManagementExtractor,
    H2SExposureExtractor,
    ArtificialLiftReliabilityExtractor,
    StateRegulatoryComplianceExtractor,
    WellVintageProfileExtractor,
    # Upstream Unconventional
    FracFleetQualityExtractor,
    WaterRecyclingRateExtractor,
    InducedSeismicityScoreExtractor,
    WellSpacingOptimisationExtractor,
    CompletionEfficiencyExtractor,
    PadDrillingIntensityExtractor,
    # Midstream
    PHMSAComplianceExtractor,
    InlineInspectionExtractor,
    CathodicProtectionExtractor,
    RightOfWayExtractor,
    SCADAMaturityExtractor,
    PipelineVintageExtractor,
    ThroughputConsistencyExtractor,
    # Downstream
    TurnaroundComplianceExtractor,
    PSMAuditFindingsExtractor,
    MechanicalIntegrityExtractor,
    FeedstockComplexityExtractor,
    BIExposureRatioExtractor,
    ProcessUnitCountExtractor,
)

# Phase 5: Renewable, Storage & Shared Renewable signals
from .renewable_storage import (
    # Shared Renewable
    TechnologyMaturityExtractor,
    EPCContractorQualityExtractor,
    WarrantyCoverageExtractor,
    CapacityFactorExtractor,
    NatCatExposureExtractor,
    GridInterconnectionExtractor,
    PPAQualityExtractor,
    DegradationRateExtractor,
    CommissioningDefectsExtractor,
    ConstructionPhaseExtractor,
    EPCTrackRecordExtractor,
    SupplyChainQualityExtractor,
    # Offshore Wind
    InstallationVesselQualityExtractor,
    FoundationTypeExtractor,
    TurbinePlatformGenerationExtractor,
    CableRouteRiskExtractor,
    MarineWeatherExposureExtractor,
    CrewTransferSafetyExtractor,
    OfftakeContractQualityExtractor,
    # Onshore Renewable
    HailExposureExtractor,
    PanelTechnologyVintageExtractor,
    InverterReliabilityExtractor,
    CurtailmentRateExtractor,
    PortfolioGeographicSpreadExtractor,
    # Storage
    BatteryChemistryExtractor,
    ThermalManagementSystemExtractor,
    FireSuppressionCapabilityExtractor,
    BMSSophisticationExtractor,
    HydrogenStoragePressureExtractor,
    SafetyStandardComplianceExtractor,
    CellFormatMaturityExtractor,
    ElectrolyserTechnologyExtractor,
)

__all__ = [
    # Network Authority
    "EnergyPartnerQualityExtractor", "ContractorQualityExtractor", "EnergyBankingRelationshipExtractor",
    "InsuranceHistoryExtractor", "RegulatorRelationshipExtractor", "OfftakeQualityExtractor",
    # Safety Performance
    "OSHATRIRExtractor", "OSHAViolationsExtractor", "BSEEIncidentExtractor", "ProcessSafetyExtractor",
    "FatalityHistoryExtractor", "MajorIncidentExtractor", "NearMissReportingExtractor",
    # Environmental
    "EPAViolationExtractor", "SpillHistoryExtractor", "EmissionsComplianceExtractor",
    "FlaringIntensityExtractor", "MethaneEmissionsExtractor", "RemediationExtractor",
    # Operational
    "ProductionConsistencyExtractor", "FacilityActivityExtractor", "WellIntegrityExtractor",
    "MaintenancePatternExtractor", "OperationalEfficiencyExtractor",
    # Financial
    "LeverageExtractor", "AROCoverageExtractor", "CapexTrendExtractor", "RestructuringExtractor",
    # Asset Portfolio
    "AssetAgeExtractor", "ConcentrationExtractor", "TechnologyProfileExtractor",
    "DecommissioningExtractor", "PermitStatusExtractor",
    # Corporate Footprint
    "SafetyCommunicationExtractor", "EnergyESGReportingExtractor", "TechnicalHiringExtractor",
    "IndustryPresenceExtractor", "DisclosureQualityExtractor", "HSELeadershipExtractor",
    # Structured Data
    "EnergyESGRatingExtractor", "BenchmarkExtractor",
    # Categorical
    "OperatorTypeExtractor", "OperationSegmentExtractor", "GeographicFocusExtractor",
    # Phase 5: Upstream Deepwater
    "BOPTestingComplianceExtractor", "WellControlEventsExtractor", "RigContractorQualityExtractor",
    "SubseaEquipmentAgeExtractor", "WaterDepthProfileExtractor", "MetoceanExposureExtractor",
    "BSEEComplianceDetailExtractor", "SpudToProductionExtractor",
    # Phase 5: Upstream Onshore
    "ProducedWaterManagementExtractor", "H2SExposureExtractor", "ArtificialLiftReliabilityExtractor",
    "StateRegulatoryComplianceExtractor", "WellVintageProfileExtractor",
    # Phase 5: Upstream Unconventional
    "FracFleetQualityExtractor", "WaterRecyclingRateExtractor", "InducedSeismicityScoreExtractor",
    "WellSpacingOptimisationExtractor", "CompletionEfficiencyExtractor", "PadDrillingIntensityExtractor",
    # Phase 5: Midstream
    "PHMSAComplianceExtractor", "InlineInspectionExtractor", "CathodicProtectionExtractor",
    "RightOfWayExtractor", "SCADAMaturityExtractor", "PipelineVintageExtractor", "ThroughputConsistencyExtractor",
    # Phase 5: Downstream
    "TurnaroundComplianceExtractor", "PSMAuditFindingsExtractor", "MechanicalIntegrityExtractor",
    "FeedstockComplexityExtractor", "BIExposureRatioExtractor", "ProcessUnitCountExtractor",
    # Phase 5: Shared Renewable
    "TechnologyMaturityExtractor", "EPCContractorQualityExtractor", "WarrantyCoverageExtractor",
    "CapacityFactorExtractor", "NatCatExposureExtractor", "GridInterconnectionExtractor",
    "PPAQualityExtractor", "DegradationRateExtractor", "CommissioningDefectsExtractor",
    "ConstructionPhaseExtractor", "EPCTrackRecordExtractor", "SupplyChainQualityExtractor",
    # Phase 5: Offshore Wind
    "InstallationVesselQualityExtractor", "FoundationTypeExtractor", "TurbinePlatformGenerationExtractor",
    "CableRouteRiskExtractor", "MarineWeatherExposureExtractor", "CrewTransferSafetyExtractor",
    "OfftakeContractQualityExtractor",
    # Phase 5: Onshore Renewable
    "HailExposureExtractor", "PanelTechnologyVintageExtractor", "InverterReliabilityExtractor",
    "CurtailmentRateExtractor", "PortfolioGeographicSpreadExtractor",
    # Phase 5: Storage
    "BatteryChemistryExtractor", "ThermalManagementSystemExtractor", "FireSuppressionCapabilityExtractor",
    "BMSSophisticationExtractor", "HydrogenStoragePressureExtractor", "SafetyStandardComplianceExtractor",
    "CellFormatMaturityExtractor", "ElectrolyserTechnologyExtractor",
]
