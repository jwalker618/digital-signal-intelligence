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

from .environmental_operational_financial import (
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
]
