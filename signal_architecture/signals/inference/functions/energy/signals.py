"""
Energy Inference Functions - All Signal Groups

Maps YAML inference_utility_function names to pipeline orchestration.
"""

import time
from typing import Dict, Any

from ....types import SignalResult, InferenceContext
from ....inference.registry import register_inference_function



# V6/E10 neutral stand-ins — real extractor wiring lands via the
# D-series production extractors (Stage 6). Until then every call
# returns a neutral SignalResult(score=50, confidence=0.5).

async def _run_pipeline(signal_id, *args, default=50.0, **kwargs):
    """Neutral scoring stand-in. Accepts the legacy
    (signal_id, extractor, aggregator, entity_id, context, ...)
    signature but ignores the extractor + aggregator args."""
    return SignalResult(
        signal_id=signal_id,
        score=float(default),
        confidence=0.5,
        execution_time_ms=0.0,
    )


async def _run_categorical(signal_id, *args, default="OTHER", **kwargs):
    """Neutral categorical stand-in — see _run_pipeline."""
    return SignalResult(
        signal_id=signal_id,
        category=default,
        confidence=0.5,
        execution_time_ms=0.0,
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


# CATEGORICAL
@register_inference_function("energy_operator_type_basefunction")
def f1(entity_id, context): return _run_categorical("operator_type", OperatorTypeExtractor(), OperatorTypeAggregator(), entity_id, context, "operator_type", "UNKNOWN")

@register_inference_function("operation_segment_basefunction")
def f2(entity_id, context): return _run_categorical("operation_segment", OperationSegmentExtractor(), OperationSegmentAggregator(), entity_id, context, "primary_segment", "MIXED")

@register_inference_function("geographic_focus_basefunction")
def f3(entity_id, context): return _run_categorical("geographic_focus", GeographicFocusExtractor(), GeographicFocusAggregator(), entity_id, context, "primary_geography", "OTHER")

# NETWORK AUTHORITY
@register_inference_function("energy_partner_quality_basefunction")
def f4(entity_id, context): return _run_pipeline("partner_quality", EnergyPartnerQualityExtractor(), EnergyPartnerQualityAggregator(), entity_id, context, "partner_quality_score", 50)

@register_inference_function("contractor_quality_basefunction")
def f5(entity_id, context): return _run_pipeline("contractor_quality", ContractorQualityExtractor(), ContractorQualityAggregator(), entity_id, context, "contractor_quality_score", 50)

@register_inference_function("energy_banking_relationship_basefunction")
def f6(entity_id, context): return _run_pipeline("banking_relationship", EnergyBankingRelationshipExtractor(), EnergyBankingRelationshipAggregator(), entity_id, context, "banking_relationship_score", 50)

@register_inference_function("insurance_history_basefunction")
def f7(entity_id, context): return _run_pipeline("insurance_history", InsuranceHistoryExtractor(), InsuranceHistoryAggregator(), entity_id, context, "insurance_history_score", 70)

@register_inference_function("energy_industry_association_basefunction")
def f8(entity_id, context): return _run_pipeline("industry_association", IndustryAssociationExtractor(), IndustryEngagementAggregator(), entity_id, context, "engagement_score", 40, industry="ENERGY")

@register_inference_function("regulator_relationship_basefunction")
def f9(entity_id, context): return _run_pipeline("regulator_relationship", RegulatorRelationshipExtractor(), RegulatorRelationshipAggregator(), entity_id, context, "regulator_relationship_score", 60)

@register_inference_function("offtake_quality_basefunction")
def f10(entity_id, context): return _run_pipeline("customer_quality", OfftakeQualityExtractor(), OfftakeQualityAggregator(), entity_id, context, "offtake_quality_score", 60)

# SAFETY PERFORMANCE
@register_inference_function("osha_trir_basefunction")
def f11(entity_id, context): return _run_pipeline("osha_trir", OSHATRIRExtractor(), OSHATRIRAggregator(), entity_id, context, "osha_trir_score", 50)

@register_inference_function("osha_violations_basefunction")
def f12(entity_id, context): return _run_pipeline("osha_violations", OSHAViolationsExtractor(), OSHAViolationsAggregator(), entity_id, context, "osha_violations_score", 70)

@register_inference_function("bsee_incident_basefunction")
def f13(entity_id, context): return _run_pipeline("bsee_incident", BSEEIncidentExtractor(), BSEEIncidentAggregator(), entity_id, context, "bsee_incident_score", 100)

@register_inference_function("process_safety_basefunction")
def f14(entity_id, context): return _run_pipeline("process_safety", ProcessSafetyExtractor(), ProcessSafetyAggregator(), entity_id, context, "process_safety_score", 70)

@register_inference_function("fatality_history_basefunction")
def f15(entity_id, context): return _run_pipeline("fatality", FatalityHistoryExtractor(), FatalityHistoryAggregator(), entity_id, context, "fatality_score", 100)

@register_inference_function("major_incident_basefunction")
def f16(entity_id, context): return _run_pipeline("major_incident", MajorIncidentExtractor(), MajorIncidentAggregator(), entity_id, context, "major_incident_score", 100)

@register_inference_function("nearmiss_reporting_basefunction")
def f17(entity_id, context): return _run_pipeline("near_miss", NearMissReportingExtractor(), NearMissReportingAggregator(), entity_id, context, "near_miss_score", 50)

# ENVIRONMENTAL COMPLIANCE
@register_inference_function("epa_violation_basefunction")
def f18(entity_id, context): return _run_pipeline("epa_violation", EPAViolationExtractor(), EPAViolationAggregator(), entity_id, context, "epa_violation_score", 70)

@register_inference_function("spill_history_basefunction")
def f19(entity_id, context): return _run_pipeline("spill_history", SpillHistoryExtractor(), SpillHistoryAggregator(), entity_id, context, "spill_history_score", 80)

@register_inference_function("emissions_compliance_basefunction")
def f20(entity_id, context): return _run_pipeline("emissions_compliance", EmissionsComplianceExtractor(), EmissionsComplianceAggregator(), entity_id, context, "emissions_compliance_score", 70)

@register_inference_function("flaring_intensity_basefunction")
def f21(entity_id, context): return _run_pipeline("flaring", FlaringIntensityExtractor(), FlaringIntensityAggregator(), entity_id, context, "flaring_score", 60)

@register_inference_function("methane_emissions_basefunction")
def f22(entity_id, context): return _run_pipeline("methane", MethaneEmissionsExtractor(), MethaneEmissionsAggregator(), entity_id, context, "methane_score", 60)

@register_inference_function("remediation_basefunction")
def f23(entity_id, context): return _run_pipeline("remediation", RemediationExtractor(), RemediationAggregator(), entity_id, context, "remediation_score", 80)

# OPERATIONAL TELEMETRY
@register_inference_function("production_consistency_basefunction")
def f24(entity_id, context): return _run_pipeline("production_consistency", ProductionConsistencyExtractor(), ProductionConsistencyAggregator(), entity_id, context, "production_consistency_score", 70)

@register_inference_function("facility_activity_basefunction")
def f25(entity_id, context): return _run_pipeline("facility_activity", FacilityActivityExtractor(), FacilityActivityAggregator(), entity_id, context, "facility_activity_score", 70)

@register_inference_function("well_integrity_basefunction")
def f26(entity_id, context): return _run_pipeline("well_integrity", WellIntegrityExtractor(), WellIntegrityAggregator(), entity_id, context, "well_integrity_score", 70)

@register_inference_function("maintenance_patterm_basefunction")
def f27(entity_id, context): return _run_pipeline("maintenance_pattern", MaintenancePatternExtractor(), MaintenancePatternAggregator(), entity_id, context, "maintenance_pattern_score", 70)

@register_inference_function("operational_efficiency_basefunction")
def f28(entity_id, context): return _run_pipeline("operational_efficiency", OperationalEfficiencyExtractor(), OperationalEfficiencyAggregator(), entity_id, context, "operational_efficiency_score", 70)

# FINANCIAL STABILITY
@register_inference_function("energy_credit_rating_basefunction")
def f29(entity_id, context): return _run_pipeline("credit_rating", CreditRatingExtractor(), CreditRatingAggregator(), entity_id, context, "average_rating_score", 50)

@register_inference_function("leverage_basefunction")
def f30(entity_id, context): return _run_pipeline("leverage", LeverageExtractor(), LeverageAggregator(), entity_id, context, "leverage_score", 50)

@register_inference_function("aro_coverage_basefunction")
def f31(entity_id, context): return _run_pipeline("aro_coverage", AROCoverageExtractor(), AROCoverageAggregator(), entity_id, context, "aro_coverage_score", 70)

@register_inference_function("capex_trend_basefunction")
def f32(entity_id, context): return _run_pipeline("capex_trend", CapexTrendExtractor(), CapexTrendAggregator(), entity_id, context, "capex_trend_score", 70)

@register_inference_function("restructuring_basefunction")
def f33(entity_id, context): return _run_pipeline("restructuring", RestructuringExtractor(), RestructuringAggregator(), entity_id, context, "restructuring_score", 100)

# ASSET PORTFOLIO
@register_inference_function("asset_age_basefunction")
def f34(entity_id, context): return _run_pipeline("asset_age", AssetAgeExtractor(), AssetAgeAggregator(), entity_id, context, "asset_age_score", 60)

@register_inference_function("concentration_basefunction")
def f35(entity_id, context): return _run_pipeline("concentration", ConcentrationExtractor(), ConcentrationAggregator(), entity_id, context, "concentration_score", 60)

@register_inference_function("technology_profile_basefunction")
def f36(entity_id, context): return _run_pipeline("complexity", TechnologyProfileExtractor(), TechnologyProfileAggregator(), entity_id, context, "technology_profile_score", 70)

@register_inference_function("decomissioning_basefunction")
def f37(entity_id, context): return _run_pipeline("decommissioning", DecommissioningExtractor(), DecommissioningAggregator(), entity_id, context, "decommissioning_score", 70)

@register_inference_function("permit_status_basefunction")
def f38(entity_id, context): return _run_pipeline("permit_status", PermitStatusExtractor(), PermitStatusAggregator(), entity_id, context, "permit_status_score", 80)

# CORPORATE FOOTPRINT
@register_inference_function("safety_comms_basefunction")
def f39(entity_id, context): return _run_pipeline("safety_communication", SafetyCommunicationExtractor(), SafetyCommunicationAggregator(), entity_id, context, "safety_communication_score", 50)

@register_inference_function("energy_esg_reporting_basefunction")
def f40(entity_id, context): return _run_pipeline("esg_reporting", EnergyESGReportingExtractor(), EnergyESGReportingAggregator(), entity_id, context, "esg_reporting_score", 50)

@register_inference_function("technical_hiring_basefunction")
def f41(entity_id, context): return _run_pipeline("technical_hiring", TechnicalHiringExtractor(), TechnicalHiringAggregator(), entity_id, context, "technical_hiring_score", 50)

@register_inference_function("industry_presence_basefunction")
def f42(entity_id, context): return _run_pipeline("industry_presence", IndustryPresenceExtractor(), IndustryPresenceAggregator(), entity_id, context, "industry_presence_score", 50)

@register_inference_function("disclosure_quality_basefunction")
def f43(entity_id, context): return _run_pipeline("disclosure_quality", DisclosureQualityExtractor(), DisclosureQualityAggregator(), entity_id, context, "disclosure_quality_score", 60)

@register_inference_function("hse_leadership_basefunction")
def f44(entity_id, context): return _run_pipeline("hse_leadership", HSELeadershipExtractor(), HSELeadershipAggregator(), entity_id, context, "hse_leadership_score", 50)

# STRUCTURED DATA
@register_inference_function("energy_esg_rating_basefunction")
def f45(entity_id, context): return _run_pipeline("esg_rating", EnergyESGRatingExtractor(), EnergyESGRatingAggregator(), entity_id, context, "esg_rating_score", 50)

@register_inference_function("benchmark_basefunction")
def f46(entity_id, context): return _run_pipeline("benchmark", BenchmarkExtractor(), BenchmarkAggregator(), entity_id, context, "benchmark_score", 60)
