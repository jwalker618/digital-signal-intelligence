"""
Energy Phase 5 Aggregators - All New Signal Groups

Production-ready aggregators for Phase 5 energy coverage expansion signals.
Covers upstream deepwater/onshore/unconventional, midstream, downstream,
offshore wind, onshore renewable, storage, and shared renewable signals.
"""

from typing import List
from ...base import ProductionAggregator
from ....types import AggregatorResult, ExtractorResult


def _simple_agg(cls_name, score_key, default=50):
    """Factory for simple score-passthrough aggregators."""
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result(f"No {score_key} data")
        return self._create_success_result(
            {score_key: round(self._normalize_float(raw.get(score_key), default), 1)},
            extractor_results
        )
    return type(cls_name, (ProductionAggregator,), {"aggregate": aggregate})


def _categorical_agg(cls_name, cat_key, default):
    """Factory for categorical aggregators."""
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result(f"No {cat_key} data")
        return self._create_success_result(
            {cat_key: raw.get(cat_key, default)},
            extractor_results
        )
    return type(cls_name, (ProductionAggregator,), {"aggregate": aggregate})


# =============================================================================
# UPSTREAM DEEPWATER AGGREGATORS
# =============================================================================
BOPTestingComplianceAggregator = _simple_agg("BOPTestingComplianceAggregator", "bop_testing_compliance_score", 50)
WellControlEventsAggregator = _simple_agg("WellControlEventsAggregator", "well_control_events_score", 100)
RigContractorQualityAggregator = _simple_agg("RigContractorQualityAggregator", "rig_contractor_quality_score", 50)
SubseaEquipmentAgeAggregator = _simple_agg("SubseaEquipmentAgeAggregator", "subsea_equipment_age_score", 60)
WaterDepthProfileAggregator = _simple_agg("WaterDepthProfileAggregator", "water_depth_profile_score", 50)
MetoceanExposureAggregator = _simple_agg("MetoceanExposureAggregator", "metocean_exposure_score", 50)
BSEEComplianceDetailAggregator = _simple_agg("BSEEComplianceDetailAggregator", "bsee_compliance_detail_score", 70)
SpudToProductionAggregator = _simple_agg("SpudToProductionAggregator", "spud_to_production_score", 60)

# =============================================================================
# UPSTREAM ONSHORE AGGREGATORS
# =============================================================================
ProducedWaterManagementAggregator = _simple_agg("ProducedWaterManagementAggregator", "produced_water_management_score", 60)
H2SExposureAggregator = _simple_agg("H2SExposureAggregator", "h2s_exposure_score", 70)
ArtificialLiftReliabilityAggregator = _simple_agg("ArtificialLiftReliabilityAggregator", "artificial_lift_reliability_score", 60)
StateRegulatoryComplianceAggregator = _simple_agg("StateRegulatoryComplianceAggregator", "state_regulatory_compliance_score", 70)
WellVintageProfileAggregator = _simple_agg("WellVintageProfileAggregator", "well_vintage_profile_score", 60)

# =============================================================================
# UPSTREAM UNCONVENTIONAL AGGREGATORS
# =============================================================================
FracFleetQualityAggregator = _simple_agg("FracFleetQualityAggregator", "frac_fleet_quality_score", 60)
WaterRecyclingRateAggregator = _simple_agg("WaterRecyclingRateAggregator", "water_recycling_rate_score", 50)
InducedSeismicityScoreAggregator = _simple_agg("InducedSeismicityScoreAggregator", "induced_seismicity_score", 70)
WellSpacingOptimisationAggregator = _simple_agg("WellSpacingOptimisationAggregator", "well_spacing_optimisation_score", 60)
CompletionEfficiencyAggregator = _simple_agg("CompletionEfficiencyAggregator", "completion_efficiency_score", 60)
PadDrillingIntensityAggregator = _simple_agg("PadDrillingIntensityAggregator", "pad_drilling_intensity_score", 50)

# =============================================================================
# MIDSTREAM AGGREGATORS
# =============================================================================
PHMSAComplianceAggregator = _simple_agg("PHMSAComplianceAggregator", "phmsa_compliance_score", 70)
InlineInspectionAggregator = _simple_agg("InlineInspectionAggregator", "inline_inspection_score", 60)
CathodicProtectionAggregator = _simple_agg("CathodicProtectionAggregator", "cathodic_protection_score", 60)
RightOfWayAggregator = _simple_agg("RightOfWayAggregator", "right_of_way_score", 60)
SCADAMaturityAggregator = _simple_agg("SCADAMaturityAggregator", "scada_maturity_score", 50)
PipelineVintageAggregator = _simple_agg("PipelineVintageAggregator", "pipeline_vintage_score", 60)
ThroughputConsistencyAggregator = _simple_agg("ThroughputConsistencyAggregator", "throughput_consistency_score", 60)

# =============================================================================
# DOWNSTREAM AGGREGATORS
# =============================================================================
TurnaroundComplianceAggregator = _simple_agg("TurnaroundComplianceAggregator", "turnaround_compliance_score", 60)
PSMAuditFindingsAggregator = _simple_agg("PSMAuditFindingsAggregator", "psm_audit_findings_score", 70)
MechanicalIntegrityAggregator = _simple_agg("MechanicalIntegrityAggregator", "mechanical_integrity_score", 60)
FeedstockComplexityAggregator = _simple_agg("FeedstockComplexityAggregator", "feedstock_complexity_score", 50)
BIExposureRatioAggregator = _simple_agg("BIExposureRatioAggregator", "bi_exposure_ratio_score", 50)
ProcessUnitCountAggregator = _simple_agg("ProcessUnitCountAggregator", "process_unit_count_score", 50)

# =============================================================================
# SHARED RENEWABLE AGGREGATORS
# =============================================================================
TechnologyMaturityAggregator = _simple_agg("TechnologyMaturityAggregator", "technology_maturity_score", 50)
EPCContractorQualityAggregator = _simple_agg("EPCContractorQualityAggregator", "epc_contractor_quality_score", 50)
WarrantyCoverageAggregator = _simple_agg("WarrantyCoverageAggregator", "warranty_coverage_score", 60)
CapacityFactorAggregator = _simple_agg("CapacityFactorAggregator", "capacity_factor_score", 50)
NatCatExposureAggregator = _simple_agg("NatCatExposureAggregator", "natcat_exposure_score", 50)
GridInterconnectionAggregator = _simple_agg("GridInterconnectionAggregator", "grid_interconnection_score", 60)
PPAQualityAggregator = _simple_agg("PPAQualityAggregator", "ppa_quality_score", 50)
DegradationRateAggregator = _simple_agg("DegradationRateAggregator", "degradation_rate_score", 60)
CommissioningDefectsAggregator = _simple_agg("CommissioningDefectsAggregator", "commissioning_defects_score", 60)
ConstructionPhaseAggregator = _categorical_agg("ConstructionPhaseAggregator", "construction_phase", "MATURE_OPERATION")
EPCTrackRecordAggregator = _simple_agg("EPCTrackRecordAggregator", "epc_track_record_score", 50)
SupplyChainQualityAggregator = _simple_agg("SupplyChainQualityAggregator", "supply_chain_quality_score", 50)

# =============================================================================
# OFFSHORE WIND AGGREGATORS
# =============================================================================
InstallationVesselQualityAggregator = _simple_agg("InstallationVesselQualityAggregator", "installation_vessel_quality_score", 50)
FoundationTypeAggregator = _categorical_agg("FoundationTypeAggregator", "foundation_type", "MONOPILE")
TurbinePlatformGenerationAggregator = _simple_agg("TurbinePlatformGenerationAggregator", "turbine_platform_generation_score", 50)
CableRouteRiskAggregator = _simple_agg("CableRouteRiskAggregator", "cable_route_risk_score", 50)
MarineWeatherExposureAggregator = _simple_agg("MarineWeatherExposureAggregator", "marine_weather_exposure_score", 50)
CrewTransferSafetyAggregator = _simple_agg("CrewTransferSafetyAggregator", "crew_transfer_safety_score", 60)
OfftakeContractQualityAggregator = _simple_agg("OfftakeContractQualityAggregator", "offtake_contract_quality_score", 50)

# =============================================================================
# ONSHORE RENEWABLE AGGREGATORS
# =============================================================================
HailExposureAggregator = _simple_agg("HailExposureAggregator", "hail_exposure_score", 50)
PanelTechnologyVintageAggregator = _simple_agg("PanelTechnologyVintageAggregator", "panel_technology_vintage_score", 60)
InverterReliabilityAggregator = _simple_agg("InverterReliabilityAggregator", "inverter_reliability_score", 60)
CurtailmentRateAggregator = _simple_agg("CurtailmentRateAggregator", "curtailment_rate_score", 60)
PortfolioGeographicSpreadAggregator = _simple_agg("PortfolioGeographicSpreadAggregator", "portfolio_geographic_spread_score", 50)

# =============================================================================
# STORAGE AGGREGATORS
# =============================================================================
BatteryChemistryAggregator = _categorical_agg("BatteryChemistryAggregator", "battery_chemistry", "LFP")
ThermalManagementSystemAggregator = _simple_agg("ThermalManagementSystemAggregator", "thermal_management_system_score", 50)
FireSuppressionCapabilityAggregator = _simple_agg("FireSuppressionCapabilityAggregator", "fire_suppression_capability_score", 50)
BMSSophisticationAggregator = _simple_agg("BMSSophisticationAggregator", "bms_sophistication_score", 50)
HydrogenStoragePressureAggregator = _simple_agg("HydrogenStoragePressureAggregator", "hydrogen_storage_pressure_score", 50)
SafetyStandardComplianceAggregator = _simple_agg("SafetyStandardComplianceAggregator", "safety_standard_compliance_score", 50)
CellFormatMaturityAggregator = _simple_agg("CellFormatMaturityAggregator", "cell_format_maturity_score", 50)
ElectrolyserTechnologyAggregator = _simple_agg("ElectrolyserTechnologyAggregator", "electrolyser_technology_score", 50)
