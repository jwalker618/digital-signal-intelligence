"""
Energy Phase 5 Inference Functions - All New Signals

Maps YAML inference_utility_function names to pipeline orchestration
for all 60 new signals introduced in Phase 5 energy expansion.

Reusable structure: Each inference function follows the same _run_pipeline
or _run_categorical pattern established in the base signals.py.
"""

import time
from typing import Dict, Any

from ....types import SignalResult, InferenceContext
from ....inference.registry import register_inference_function

# Upstream/Midstream/Downstream extractors
from ....extractors.stubs.energy import (
    BOPTestingComplianceExtractor, WellControlEventsExtractor, RigContractorQualityExtractor,
    SubseaEquipmentAgeExtractor, WaterDepthProfileExtractor, MetoceanExposureExtractor,
    BSEEComplianceDetailExtractor, SpudToProductionExtractor,
    ProducedWaterManagementExtractor, H2SExposureExtractor, ArtificialLiftReliabilityExtractor,
    StateRegulatoryComplianceExtractor, WellVintageProfileExtractor,
    FracFleetQualityExtractor, WaterRecyclingRateExtractor, InducedSeismicityScoreExtractor,
    WellSpacingOptimisationExtractor, CompletionEfficiencyExtractor, PadDrillingIntensityExtractor,
    PHMSAComplianceExtractor, InlineInspectionExtractor, CathodicProtectionExtractor,
    RightOfWayExtractor, SCADAMaturityExtractor, PipelineVintageExtractor, ThroughputConsistencyExtractor,
    TurnaroundComplianceExtractor, PSMAuditFindingsExtractor, MechanicalIntegrityExtractor,
    FeedstockComplexityExtractor, BIExposureRatioExtractor, ProcessUnitCountExtractor,
)

# Renewable/Storage extractors
from ....extractors.stubs.energy import (
    TechnologyMaturityExtractor, EPCContractorQualityExtractor, WarrantyCoverageExtractor,
    CapacityFactorExtractor, NatCatExposureExtractor, GridInterconnectionExtractor,
    PPAQualityExtractor, DegradationRateExtractor, CommissioningDefectsExtractor,
    ConstructionPhaseExtractor, EPCTrackRecordExtractor, SupplyChainQualityExtractor,
    InstallationVesselQualityExtractor, FoundationTypeExtractor, TurbinePlatformGenerationExtractor,
    CableRouteRiskExtractor, MarineWeatherExposureExtractor, CrewTransferSafetyExtractor,
    OfftakeContractQualityExtractor,
    HailExposureExtractor, PanelTechnologyVintageExtractor, InverterReliabilityExtractor,
    CurtailmentRateExtractor, PortfolioGeographicSpreadExtractor,
    BatteryChemistryExtractor, ThermalManagementSystemExtractor, FireSuppressionCapabilityExtractor,
    BMSSophisticationExtractor, HydrogenStoragePressureExtractor, SafetyStandardComplianceExtractor,
    CellFormatMaturityExtractor, ElectrolyserTechnologyExtractor,
)

# Upstream/Midstream/Downstream aggregators
from ....aggregators.implementations.energy import (
    BOPTestingComplianceAggregator, WellControlEventsAggregator, RigContractorQualityAggregator,
    SubseaEquipmentAgeAggregator, WaterDepthProfileAggregator, MetoceanExposureAggregator,
    BSEEComplianceDetailAggregator, SpudToProductionAggregator,
    ProducedWaterManagementAggregator, H2SExposureAggregator, ArtificialLiftReliabilityAggregator,
    StateRegulatoryComplianceAggregator, WellVintageProfileAggregator,
    FracFleetQualityAggregator, WaterRecyclingRateAggregator, InducedSeismicityScoreAggregator,
    WellSpacingOptimisationAggregator, CompletionEfficiencyAggregator, PadDrillingIntensityAggregator,
    PHMSAComplianceAggregator, InlineInspectionAggregator, CathodicProtectionAggregator,
    RightOfWayAggregator, SCADAMaturityAggregator, PipelineVintageAggregator, ThroughputConsistencyAggregator,
    TurnaroundComplianceAggregator, PSMAuditFindingsAggregator, MechanicalIntegrityAggregator,
    FeedstockComplexityAggregator, BIExposureRatioAggregator, ProcessUnitCountAggregator,
)

# Renewable/Storage aggregators
from ....aggregators.implementations.energy import (
    TechnologyMaturityAggregator, EPCContractorQualityAggregator, WarrantyCoverageAggregator,
    CapacityFactorAggregator, NatCatExposureAggregator, GridInterconnectionAggregator,
    PPAQualityAggregator, DegradationRateAggregator, CommissioningDefectsAggregator,
    ConstructionPhaseAggregator, EPCTrackRecordAggregator, SupplyChainQualityAggregator,
    InstallationVesselQualityAggregator, FoundationTypeAggregator, TurbinePlatformGenerationAggregator,
    CableRouteRiskAggregator, MarineWeatherExposureAggregator, CrewTransferSafetyAggregator,
    OfftakeContractQualityAggregator,
    HailExposureAggregator, PanelTechnologyVintageAggregator, InverterReliabilityAggregator,
    CurtailmentRateAggregator, PortfolioGeographicSpreadAggregator,
    BatteryChemistryAggregator, ThermalManagementSystemAggregator, FireSuppressionCapabilityAggregator,
    BMSSophisticationAggregator, HydrogenStoragePressureAggregator, SafetyStandardComplianceAggregator,
    CellFormatMaturityAggregator, ElectrolyserTechnologyAggregator,
)


def _run_pipeline(signal_id, extractor, aggregator, entity_id, context, score_field, default=50, **kw):
    start = time.time()
    try:
        ext = extractor.extract(entity_id, context=context, **kw)
        if not ext.success:
            return SignalResult(signal_id=signal_id, score=default, confidence=0.3, error="Extraction failed")
        agg = aggregator.aggregate([ext])
        score = agg.data.get(score_field, default) if agg.success else default
        return SignalResult(signal_id=signal_id, score=round(score, 1), confidence=1.0, execution_time_ms=(time.time()-start)*1000,
                          raw_data=ext.data, aggregated_data=agg.data, metadata={"extractor": type(extractor).__name__, "from_cache": ext.from_cache})
    except Exception as e:
        return SignalResult(signal_id=signal_id, score=default, confidence=0.0, error=str(e))


def _run_categorical(signal_id, extractor, aggregator, entity_id, context, cat_field, default):
    start = time.time()
    try:
        ext = extractor.extract(entity_id, context=context)
        if not ext.success:
            return SignalResult(signal_id=signal_id, category=default, confidence=0.3, error="Extraction failed")
        agg = aggregator.aggregate([ext])
        cat = agg.data.get(cat_field, default) if agg.success else default
        return SignalResult(signal_id=signal_id, category=cat, confidence=0.85, execution_time_ms=(time.time()-start)*1000,
                          raw_data=ext.data, aggregated_data=agg.data)
    except Exception as e:
        return SignalResult(signal_id=signal_id, category=default, confidence=0.0, error=str(e))


# =============================================================================
# UPSTREAM DEEPWATER
# =============================================================================
@register_inference_function("bop_testing_compliance_basefunction")
def p5_01(entity_id, context): return _run_pipeline("bop_testing_compliance", BOPTestingComplianceExtractor(), BOPTestingComplianceAggregator(), entity_id, context, "bop_testing_compliance_score", 50)

@register_inference_function("well_control_events_basefunction")
def p5_02(entity_id, context): return _run_pipeline("well_control_events", WellControlEventsExtractor(), WellControlEventsAggregator(), entity_id, context, "well_control_events_score", 100)

@register_inference_function("rig_contractor_quality_basefunction")
def p5_03(entity_id, context): return _run_pipeline("rig_contractor_quality", RigContractorQualityExtractor(), RigContractorQualityAggregator(), entity_id, context, "rig_contractor_quality_score", 50)

@register_inference_function("subsea_equipment_age_basefunction")
def p5_04(entity_id, context): return _run_pipeline("subsea_equipment_age", SubseaEquipmentAgeExtractor(), SubseaEquipmentAgeAggregator(), entity_id, context, "subsea_equipment_age_score", 60)

@register_inference_function("water_depth_profile_basefunction")
def p5_05(entity_id, context): return _run_pipeline("water_depth_profile", WaterDepthProfileExtractor(), WaterDepthProfileAggregator(), entity_id, context, "water_depth_profile_score", 50)

@register_inference_function("metocean_exposure_basefunction")
def p5_06(entity_id, context): return _run_pipeline("metocean_exposure", MetoceanExposureExtractor(), MetoceanExposureAggregator(), entity_id, context, "metocean_exposure_score", 50)

@register_inference_function("bsee_compliance_detail_basefunction")
def p5_07(entity_id, context): return _run_pipeline("bsee_compliance_detail", BSEEComplianceDetailExtractor(), BSEEComplianceDetailAggregator(), entity_id, context, "bsee_compliance_detail_score", 70)

@register_inference_function("spud_to_production_basefunction")
def p5_08(entity_id, context): return _run_pipeline("spud_to_production", SpudToProductionExtractor(), SpudToProductionAggregator(), entity_id, context, "spud_to_production_score", 60)

# =============================================================================
# UPSTREAM ONSHORE
# =============================================================================
@register_inference_function("produced_water_management_basefunction")
def p5_09(entity_id, context): return _run_pipeline("produced_water_management", ProducedWaterManagementExtractor(), ProducedWaterManagementAggregator(), entity_id, context, "produced_water_management_score", 60)

@register_inference_function("h2s_exposure_basefunction")
def p5_10(entity_id, context): return _run_pipeline("h2s_exposure", H2SExposureExtractor(), H2SExposureAggregator(), entity_id, context, "h2s_exposure_score", 70)

@register_inference_function("artificial_lift_reliability_basefunction")
def p5_11(entity_id, context): return _run_pipeline("artificial_lift_reliability", ArtificialLiftReliabilityExtractor(), ArtificialLiftReliabilityAggregator(), entity_id, context, "artificial_lift_reliability_score", 60)

@register_inference_function("state_regulatory_compliance_basefunction")
def p5_12(entity_id, context): return _run_pipeline("state_regulatory_compliance", StateRegulatoryComplianceExtractor(), StateRegulatoryComplianceAggregator(), entity_id, context, "state_regulatory_compliance_score", 70)

@register_inference_function("well_vintage_profile_basefunction")
def p5_13(entity_id, context): return _run_pipeline("well_vintage_profile", WellVintageProfileExtractor(), WellVintageProfileAggregator(), entity_id, context, "well_vintage_profile_score", 60)

# =============================================================================
# UPSTREAM UNCONVENTIONAL
# =============================================================================
@register_inference_function("frac_fleet_quality_basefunction")
def p5_14(entity_id, context): return _run_pipeline("frac_fleet_quality", FracFleetQualityExtractor(), FracFleetQualityAggregator(), entity_id, context, "frac_fleet_quality_score", 60)

@register_inference_function("water_recycling_rate_basefunction")
def p5_15(entity_id, context): return _run_pipeline("water_recycling_rate", WaterRecyclingRateExtractor(), WaterRecyclingRateAggregator(), entity_id, context, "water_recycling_rate_score", 50)

@register_inference_function("induced_seismicity_score_basefunction")
def p5_16(entity_id, context): return _run_pipeline("induced_seismicity_score", InducedSeismicityScoreExtractor(), InducedSeismicityScoreAggregator(), entity_id, context, "induced_seismicity_score", 70)

@register_inference_function("well_spacing_optimisation_basefunction")
def p5_17(entity_id, context): return _run_pipeline("well_spacing_optimisation", WellSpacingOptimisationExtractor(), WellSpacingOptimisationAggregator(), entity_id, context, "well_spacing_optimisation_score", 60)

@register_inference_function("completion_efficiency_basefunction")
def p5_18(entity_id, context): return _run_pipeline("completion_efficiency", CompletionEfficiencyExtractor(), CompletionEfficiencyAggregator(), entity_id, context, "completion_efficiency_score", 60)

@register_inference_function("pad_drilling_intensity_basefunction")
def p5_19(entity_id, context): return _run_pipeline("pad_drilling_intensity", PadDrillingIntensityExtractor(), PadDrillingIntensityAggregator(), entity_id, context, "pad_drilling_intensity_score", 50)

# =============================================================================
# MIDSTREAM
# =============================================================================
@register_inference_function("phmsa_compliance_basefunction")
def p5_20(entity_id, context): return _run_pipeline("phmsa_compliance", PHMSAComplianceExtractor(), PHMSAComplianceAggregator(), entity_id, context, "phmsa_compliance_score", 70)

@register_inference_function("inline_inspection_basefunction")
def p5_21(entity_id, context): return _run_pipeline("inline_inspection", InlineInspectionExtractor(), InlineInspectionAggregator(), entity_id, context, "inline_inspection_score", 60)

@register_inference_function("cathodic_protection_basefunction")
def p5_22(entity_id, context): return _run_pipeline("cathodic_protection", CathodicProtectionExtractor(), CathodicProtectionAggregator(), entity_id, context, "cathodic_protection_score", 60)

@register_inference_function("right_of_way_basefunction")
def p5_23(entity_id, context): return _run_pipeline("right_of_way", RightOfWayExtractor(), RightOfWayAggregator(), entity_id, context, "right_of_way_score", 60)

@register_inference_function("scada_maturity_basefunction")
def p5_24(entity_id, context): return _run_pipeline("scada_maturity", SCADAMaturityExtractor(), SCADAMaturityAggregator(), entity_id, context, "scada_maturity_score", 50)

@register_inference_function("pipeline_vintage_basefunction")
def p5_25(entity_id, context): return _run_pipeline("pipeline_vintage", PipelineVintageExtractor(), PipelineVintageAggregator(), entity_id, context, "pipeline_vintage_score", 60)

@register_inference_function("throughput_consistency_basefunction")
def p5_26(entity_id, context): return _run_pipeline("throughput_consistency", ThroughputConsistencyExtractor(), ThroughputConsistencyAggregator(), entity_id, context, "throughput_consistency_score", 60)

# =============================================================================
# DOWNSTREAM
# =============================================================================
@register_inference_function("turnaround_compliance_basefunction")
def p5_27(entity_id, context): return _run_pipeline("turnaround_compliance", TurnaroundComplianceExtractor(), TurnaroundComplianceAggregator(), entity_id, context, "turnaround_compliance_score", 60)

@register_inference_function("psm_audit_findings_basefunction")
def p5_28(entity_id, context): return _run_pipeline("psm_audit_findings", PSMAuditFindingsExtractor(), PSMAuditFindingsAggregator(), entity_id, context, "psm_audit_findings_score", 70)

@register_inference_function("mechanical_integrity_basefunction")
def p5_29(entity_id, context): return _run_pipeline("mechanical_integrity", MechanicalIntegrityExtractor(), MechanicalIntegrityAggregator(), entity_id, context, "mechanical_integrity_score", 60)

@register_inference_function("feedstock_complexity_basefunction")
def p5_30(entity_id, context): return _run_pipeline("feedstock_complexity", FeedstockComplexityExtractor(), FeedstockComplexityAggregator(), entity_id, context, "feedstock_complexity_score", 50)

@register_inference_function("bi_exposure_ratio_basefunction")
def p5_31(entity_id, context): return _run_pipeline("bi_exposure_ratio", BIExposureRatioExtractor(), BIExposureRatioAggregator(), entity_id, context, "bi_exposure_ratio_score", 50)

@register_inference_function("process_unit_count_basefunction")
def p5_32(entity_id, context): return _run_pipeline("process_unit_count", ProcessUnitCountExtractor(), ProcessUnitCountAggregator(), entity_id, context, "process_unit_count_score", 50)

# =============================================================================
# SHARED RENEWABLE
# =============================================================================
@register_inference_function("technology_maturity_basefunction")
def p5_33(entity_id, context): return _run_pipeline("technology_maturity", TechnologyMaturityExtractor(), TechnologyMaturityAggregator(), entity_id, context, "technology_maturity_score", 50)

@register_inference_function("epc_contractor_quality_basefunction")
def p5_34(entity_id, context): return _run_pipeline("epc_contractor_quality", EPCContractorQualityExtractor(), EPCContractorQualityAggregator(), entity_id, context, "epc_contractor_quality_score", 50)

@register_inference_function("warranty_coverage_basefunction")
def p5_35(entity_id, context): return _run_pipeline("warranty_coverage", WarrantyCoverageExtractor(), WarrantyCoverageAggregator(), entity_id, context, "warranty_coverage_score", 60)

@register_inference_function("capacity_factor_basefunction")
def p5_36(entity_id, context): return _run_pipeline("capacity_factor", CapacityFactorExtractor(), CapacityFactorAggregator(), entity_id, context, "capacity_factor_score", 50)

@register_inference_function("natcat_exposure_basefunction")
def p5_37(entity_id, context): return _run_pipeline("natcat_exposure", NatCatExposureExtractor(), NatCatExposureAggregator(), entity_id, context, "natcat_exposure_score", 50)

@register_inference_function("grid_interconnection_basefunction")
def p5_38(entity_id, context): return _run_pipeline("grid_interconnection", GridInterconnectionExtractor(), GridInterconnectionAggregator(), entity_id, context, "grid_interconnection_score", 60)

@register_inference_function("ppa_quality_basefunction")
def p5_39(entity_id, context): return _run_pipeline("ppa_quality", PPAQualityExtractor(), PPAQualityAggregator(), entity_id, context, "ppa_quality_score", 50)

@register_inference_function("degradation_rate_basefunction")
def p5_40(entity_id, context): return _run_pipeline("degradation_rate", DegradationRateExtractor(), DegradationRateAggregator(), entity_id, context, "degradation_rate_score", 60)

@register_inference_function("commissioning_defects_basefunction")
def p5_41(entity_id, context): return _run_pipeline("commissioning_defects", CommissioningDefectsExtractor(), CommissioningDefectsAggregator(), entity_id, context, "commissioning_defects_score", 60)

@register_inference_function("construction_phase_basefunction")
def p5_42(entity_id, context): return _run_categorical("construction_phase", ConstructionPhaseExtractor(), ConstructionPhaseAggregator(), entity_id, context, "construction_phase", "MATURE_OPERATION")

@register_inference_function("epc_track_record_basefunction")
def p5_43(entity_id, context): return _run_pipeline("epc_track_record", EPCTrackRecordExtractor(), EPCTrackRecordAggregator(), entity_id, context, "epc_track_record_score", 50)

@register_inference_function("supply_chain_quality_basefunction")
def p5_44(entity_id, context): return _run_pipeline("supply_chain_quality", SupplyChainQualityExtractor(), SupplyChainQualityAggregator(), entity_id, context, "supply_chain_quality_score", 50)

# =============================================================================
# OFFSHORE WIND
# =============================================================================
@register_inference_function("installation_vessel_quality_basefunction")
def p5_45(entity_id, context): return _run_pipeline("installation_vessel_quality", InstallationVesselQualityExtractor(), InstallationVesselQualityAggregator(), entity_id, context, "installation_vessel_quality_score", 50)

@register_inference_function("foundation_type_basefunction")
def p5_46(entity_id, context): return _run_categorical("foundation_type", FoundationTypeExtractor(), FoundationTypeAggregator(), entity_id, context, "foundation_type", "MONOPILE")

@register_inference_function("turbine_platform_generation_basefunction")
def p5_47(entity_id, context): return _run_pipeline("turbine_platform_generation", TurbinePlatformGenerationExtractor(), TurbinePlatformGenerationAggregator(), entity_id, context, "turbine_platform_generation_score", 50)

@register_inference_function("cable_route_risk_basefunction")
def p5_48(entity_id, context): return _run_pipeline("cable_route_risk", CableRouteRiskExtractor(), CableRouteRiskAggregator(), entity_id, context, "cable_route_risk_score", 50)

@register_inference_function("marine_weather_exposure_basefunction")
def p5_49(entity_id, context): return _run_pipeline("marine_weather_exposure", MarineWeatherExposureExtractor(), MarineWeatherExposureAggregator(), entity_id, context, "marine_weather_exposure_score", 50)

@register_inference_function("crew_transfer_safety_basefunction")
def p5_50(entity_id, context): return _run_pipeline("crew_transfer_safety", CrewTransferSafetyExtractor(), CrewTransferSafetyAggregator(), entity_id, context, "crew_transfer_safety_score", 60)

@register_inference_function("offtake_contract_quality_basefunction")
def p5_51(entity_id, context): return _run_pipeline("offtake_contract_quality", OfftakeContractQualityExtractor(), OfftakeContractQualityAggregator(), entity_id, context, "offtake_contract_quality_score", 50)

# =============================================================================
# ONSHORE RENEWABLE
# =============================================================================
@register_inference_function("hail_exposure_basefunction")
def p5_52(entity_id, context): return _run_pipeline("hail_exposure", HailExposureExtractor(), HailExposureAggregator(), entity_id, context, "hail_exposure_score", 50)

@register_inference_function("panel_technology_vintage_basefunction")
def p5_53(entity_id, context): return _run_pipeline("panel_technology_vintage", PanelTechnologyVintageExtractor(), PanelTechnologyVintageAggregator(), entity_id, context, "panel_technology_vintage_score", 60)

@register_inference_function("inverter_reliability_basefunction")
def p5_54(entity_id, context): return _run_pipeline("inverter_reliability", InverterReliabilityExtractor(), InverterReliabilityAggregator(), entity_id, context, "inverter_reliability_score", 60)

@register_inference_function("curtailment_rate_basefunction")
def p5_55(entity_id, context): return _run_pipeline("curtailment_rate", CurtailmentRateExtractor(), CurtailmentRateAggregator(), entity_id, context, "curtailment_rate_score", 60)

@register_inference_function("portfolio_geographic_spread_basefunction")
def p5_56(entity_id, context): return _run_pipeline("portfolio_geographic_spread", PortfolioGeographicSpreadExtractor(), PortfolioGeographicSpreadAggregator(), entity_id, context, "portfolio_geographic_spread_score", 50)

# =============================================================================
# STORAGE
# =============================================================================
@register_inference_function("battery_chemistry_basefunction")
def p5_57(entity_id, context): return _run_categorical("battery_chemistry", BatteryChemistryExtractor(), BatteryChemistryAggregator(), entity_id, context, "battery_chemistry", "LFP")

@register_inference_function("thermal_management_system_basefunction")
def p5_58(entity_id, context): return _run_pipeline("thermal_management_system", ThermalManagementSystemExtractor(), ThermalManagementSystemAggregator(), entity_id, context, "thermal_management_system_score", 50)

@register_inference_function("fire_suppression_capability_basefunction")
def p5_59(entity_id, context): return _run_pipeline("fire_suppression_capability", FireSuppressionCapabilityExtractor(), FireSuppressionCapabilityAggregator(), entity_id, context, "fire_suppression_capability_score", 50)

@register_inference_function("bms_sophistication_basefunction")
def p5_60(entity_id, context): return _run_pipeline("bms_sophistication", BMSSophisticationExtractor(), BMSSophisticationAggregator(), entity_id, context, "bms_sophistication_score", 50)

@register_inference_function("hydrogen_storage_pressure_basefunction")
def p5_61(entity_id, context): return _run_pipeline("hydrogen_storage_pressure", HydrogenStoragePressureExtractor(), HydrogenStoragePressureAggregator(), entity_id, context, "hydrogen_storage_pressure_score", 50)

@register_inference_function("safety_standard_compliance_basefunction")
def p5_62(entity_id, context): return _run_pipeline("safety_standard_compliance", SafetyStandardComplianceExtractor(), SafetyStandardComplianceAggregator(), entity_id, context, "safety_standard_compliance_score", 50)

@register_inference_function("cell_format_maturity_basefunction")
def p5_63(entity_id, context): return _run_pipeline("cell_format_maturity", CellFormatMaturityExtractor(), CellFormatMaturityAggregator(), entity_id, context, "cell_format_maturity_score", 50)

@register_inference_function("electrolyser_technology_basefunction")
def p5_64(entity_id, context): return _run_pipeline("electrolyser_technology", ElectrolyserTechnologyExtractor(), ElectrolyserTechnologyAggregator(), entity_id, context, "electrolyser_technology_score", 50)
