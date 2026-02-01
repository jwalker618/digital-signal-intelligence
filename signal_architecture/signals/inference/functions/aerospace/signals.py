"""
Aerospace Inference Functions - All Signal Groups

Maps YAML inference_utility_function names to pipeline orchestration.
"""

import time
from ....types import SignalResult, InferenceContext
from ....inference.registry import register_inference_function

# Import extractors (using actual names from aerospace __init__.py)
from ....extractors.stubs.aerospace import (
    AirlineAllianceExtractor,
    CodesharePartnershipExtractor,
    AircraftLessorExtractor,
    OEMRelationshipExtractor,
    MROProviderExtractor,
    AviationSafetyDatabaseExtractor,
    OperatingCertificateExtractor,
    IOSARegistryExtractor,
    RampInspectionExtractor,
    EUSafetyListExtractor,
    StateSafetyExtractor,
    FlightOperationsExtractor,
    FleetRegistryExtractor,
    OrderBacklogExtractor,
    CrewTrainingExtractor,
    OperationalComplexityExtractor,
    MaintenanceIndicatorsExtractor,
    RouteRiskExtractor,
    SafetyLeadershipExtractor,
    MarketPositionExtractor,
    GovernmentSupportExtractor,
)
from ....extractors.stubs.common import IndustryAssociationExtractor, CreditRatingExtractor

# Import aggregators (using actual names from aerospace __init__.py)
from ....aggregators.implementations.aerospace import (
    AllianceMembershipAggregator,
    CodeshareQualityAggregator,
    LessorQualityAggregator,
    OEMRelationshipAggregator,
    MROQualityAggregator,
    AviationSafetyAggregator,
    AccidentHistoryAggregator,
    IncidentHistoryAggregator,
    AccidentRateAggregator,
    FatalityHistoryAggregator,
    InvestigationFindingsAggregator,
    CertificateStatusAggregator,
    IOSAAuditAggregator,
    RampInspectionAggregator,
    EUSafetyListAggregator,
    StateSafetyAggregator,
    FlightOperationsAggregator,
    CrewTrainingAggregator,
    OperationalComplexityAggregator,
    FleetQualityAggregator,
    OrderBacklogAggregator,
    MaintenanceIndicatorsAggregator,
    RouteRiskAggregator,
    SafetyLeadershipAggregator,
    MarketPositionAggregator,
    GovernmentSupportAggregator,
)
from ....aggregators.implementations.common import IndustryEngagementAggregator, CreditRatingAggregator


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
@register_inference_function("aerospace_operator_type_basefunction")
def f1(e, c): return _run_categorical("operator_type", MarketPositionExtractor(), MarketPositionAggregator(), e, c, "operator_type", "UNKNOWN")

@register_inference_function("aerospace_fleet_size_basefunction")
def f2(e, c): return _run_categorical("fleet_size", FleetRegistryExtractor(), FleetQualityAggregator(), e, c, "fleet_size_category", "SMALL")

@register_inference_function("aerospace_operating_region_basefunction")
def f3(e, c): return _run_categorical("operating_region", RouteRiskExtractor(), RouteRiskAggregator(), e, c, "primary_region", "DOMESTIC")

# NETWORK AUTHORITY
@register_inference_function("alliance_membership_basefunction")
def f4(e, c): return _run_pipeline("alliance_membership", AirlineAllianceExtractor(), AllianceMembershipAggregator(), e, c, "alliance_score", 40)

@register_inference_function("codeshare_partner_basefunction")
def f5(e, c): return _run_pipeline("codeshare_quality", CodesharePartnershipExtractor(), CodeshareQualityAggregator(), e, c, "codeshare_score", 50)

@register_inference_function("mro_provider_basefunction")
def f6(e, c): return _run_pipeline("mro_quality", MROProviderExtractor(), MROQualityAggregator(), e, c, "mro_score", 50)

@register_inference_function("aircraft_lessor_basefunction")
def f7(e, c): return _run_pipeline("lessor_quality", AircraftLessorExtractor(), LessorQualityAggregator(), e, c, "lessor_score", 50)

@register_inference_function("aerospace_industry_engagement_basefunction")
def f8(e, c): return _run_pipeline("industry_engagement", IndustryAssociationExtractor(), IndustryEngagementAggregator(), e, c, "engagement_score", 40, industry="AEROSPACE")

@register_inference_function("aerospace_credit_rating_basefunction")
def f9(e, c): return _run_pipeline("credit_rating", CreditRatingExtractor(), CreditRatingAggregator(), e, c, "average_rating_score", 50)

@register_inference_function("oem_relationship_basefunction")
def f10(e, c): return _run_pipeline("oem_relationship", OEMRelationshipExtractor(), OEMRelationshipAggregator(), e, c, "oem_score", 50)

# SAFETY RECORD
@register_inference_function("safety_record_basefunction")
def f11(e, c): return _run_pipeline("safety_record", AviationSafetyDatabaseExtractor(), AviationSafetyAggregator(), e, c, "safety_score", 50)

@register_inference_function("accident_history_basefunction")
def f12(e, c): return _run_pipeline("accident_history", AviationSafetyDatabaseExtractor(), AccidentHistoryAggregator(), e, c, "accident_score", 80)

@register_inference_function("incident_history_basefunction")
def f13(e, c): return _run_pipeline("incident_history", AviationSafetyDatabaseExtractor(), IncidentHistoryAggregator(), e, c, "incident_score", 70)

@register_inference_function("accident_rate_basefunction")
def f14(e, c): return _run_pipeline("accident_rate", AviationSafetyDatabaseExtractor(), AccidentRateAggregator(), e, c, "rate_score", 70)

@register_inference_function("safety_rating_basefunction")
def f15(e, c): return _run_pipeline("safety_rating", AviationSafetyDatabaseExtractor(), FatalityHistoryAggregator(), e, c, "fatality_score", 80)

@register_inference_function("safety_reporting_basefunction")
def f16(e, c): return _run_pipeline("safety_reporting", AviationSafetyDatabaseExtractor(), InvestigationFindingsAggregator(), e, c, "reporting_score", 70)

# REGULATORY COMPLIANCE
@register_inference_function("certifcate_status_basefunction")
def f17(e, c): return _run_pipeline("certificate_status", OperatingCertificateExtractor(), CertificateStatusAggregator(), e, c, "certificate_score", 80)

@register_inference_function("enforcement_actions_basefunction")
def f18(e, c): return _run_pipeline("enforcement_actions", RampInspectionExtractor(), RampInspectionAggregator(), e, c, "ramp_score", 70)

@register_inference_function("audit_history_basefunction")
def f19(e, c): return _run_pipeline("audit_history", IOSARegistryExtractor(), IOSAAuditAggregator(), e, c, "iosa_score", 50)

@register_inference_function("sms_compliance_basefunction")
def f20(e, c): return _run_pipeline("sms_compliance", StateSafetyExtractor(), StateSafetyAggregator(), e, c, "sms_score", 70)

@register_inference_function("iosa_certification_basefunction")
def f21(e, c): return _run_pipeline("iosa_certification", IOSARegistryExtractor(), IOSAAuditAggregator(), e, c, "iosa_score", 50)

@register_inference_function("regulatory_responsiveness_basefunction")
def f22(e, c): return _run_pipeline("regulatory_responsiveness", EUSafetyListExtractor(), EUSafetyListAggregator(), e, c, "eu_score", 100)

# OPERATIONAL
@register_inference_function("otp_basefunction")
def f23(e, c): return _run_pipeline("on_time_performance", FlightOperationsExtractor(), FlightOperationsAggregator(), e, c, "otp_score", 70)

@register_inference_function("cancellation_rate_basefunction")
def f24(e, c): return _run_pipeline("cancellation_rate", FlightOperationsExtractor(), FlightOperationsAggregator(), e, c, "cancellation_score", 80)

@register_inference_function("operational_complexity_basefunction")
def f25(e, c): return _run_pipeline("operational_complexity", OperationalComplexityExtractor(), OperationalComplexityAggregator(), e, c, "complexity_score", 50)

@register_inference_function("crew_training_basefunction")
def f26(e, c): return _run_pipeline("crew_training", CrewTrainingExtractor(), CrewTrainingAggregator(), e, c, "training_score", 70)

# FLEET
@register_inference_function("fleet_age_basefunction")
def f27(e, c): return _run_pipeline("fleet_age", FleetRegistryExtractor(), FleetQualityAggregator(), e, c, "age_score", 50)

@register_inference_function("fleet_homogeneity_basefunction")
def f28(e, c): return _run_pipeline("fleet_homogeneity", FleetRegistryExtractor(), FleetQualityAggregator(), e, c, "homogeneity_score", 60)

@register_inference_function("aircraft_generation_basefunction")
def f29(e, c): return _run_pipeline("aircraft_generation", FleetRegistryExtractor(), FleetQualityAggregator(), e, c, "generation_score", 60)

@register_inference_function("maintenance_program_basefunction")
def f30(e, c): return _run_pipeline("maintenance_program", MaintenanceIndicatorsExtractor(), MaintenanceIndicatorsAggregator(), e, c, "maintenance_score", 70)

@register_inference_function("order_backlog_basefunction")
def f31(e, c): return _run_pipeline("order_backlog", OrderBacklogExtractor(), OrderBacklogAggregator(), e, c, "backlog_score", 50)

# ROUTE
@register_inference_function("route_risk_basefunction")
def f32(e, c): return _run_pipeline("route_risk", RouteRiskExtractor(), RouteRiskAggregator(), e, c, "route_score", 50)

@register_inference_function("challenging_aiports_basefunction")
def f33(e, c): return _run_pipeline("challenging_airports", RouteRiskExtractor(), RouteRiskAggregator(), e, c, "airports_score", 70)

@register_inference_function("weather_exposure_basefunction")
def f34(e, c): return _run_pipeline("weather_exposure", RouteRiskExtractor(), RouteRiskAggregator(), e, c, "weather_score", 60)

# CORPORATE FOOTPRINT & FINANCIAL
@register_inference_function("aerospace_website_quality_basefunction")
def f35(e, c): return _run_pipeline("website_quality", SafetyLeadershipExtractor(), SafetyLeadershipAggregator(), e, c, "website_score", 50)

@register_inference_function("aerospace_safety_page_basefunction")
def f36(e, c): return _run_pipeline("safety_page", SafetyLeadershipExtractor(), SafetyLeadershipAggregator(), e, c, "safety_page_score", 40)

@register_inference_function("aerospace_hiring_signals_basefunction")
def f37(e, c): return _run_pipeline("hiring_signals", MarketPositionExtractor(), MarketPositionAggregator(), e, c, "hiring_score", 50)

@register_inference_function("aerospace_news_basefunction")
def f38(e, c): return _run_pipeline("news_sentiment", MarketPositionExtractor(), MarketPositionAggregator(), e, c, "sentiment_score", 50)

@register_inference_function("financial_stability_basefunction")
def f39(e, c): return _run_pipeline("financial_stability", CreditRatingExtractor(), CreditRatingAggregator(), e, c, "average_rating_score", 50)

@register_inference_function("management_stability_basefunction")
def f40(e, c): return _run_pipeline("management_stability", SafetyLeadershipExtractor(), SafetyLeadershipAggregator(), e, c, "management_score", 50)

@register_inference_function("government_support_basefunction")
def f41(e, c): return _run_pipeline("government_support", GovernmentSupportExtractor(), GovernmentSupportAggregator(), e, c, "support_score", 50)


# =============================================================================
# SIGNAL ENHANCEMENTS - Priority 1 & 2 Stubs
# TODO: These stubs need production data sources (extractors/aggregators)
# =============================================================================

import random

@register_inference_function("certification_transparency_basefunction")
def f42(entity_id, context):
    """Infers FAA/EASA certification status transparency.

    Returns a score 0-100 where higher = more transparent certification status.
    Uses metadata: certificate_type, status, airworthiness_directives_count.

    TODO: Connect to production FAA/EASA certification databases.
    """
    start = time.time()
    certificate_type = random.choice(["Part_121", "Part_135", "EASA_AOC", "Part_145"])
    status = random.choice(["current", "conditional", "suspended", "revoked"])
    ad_count = random.randint(0, 25)
    status_scores = {"current": 90, "conditional": 60, "suspended": 25, "revoked": 5}
    base = status_scores.get(status, 50)
    score = max(0, min(100, base - (ad_count * 1.5) + random.randint(-5, 5)))
    return SignalResult(
        signal_id="certification_transparency",
        score=round(score, 1),
        confidence=0.6,
        execution_time_ms=(time.time() - start) * 1000,
        raw_data={
            "certificate_type": certificate_type,
            "status": status,
            "airworthiness_directives_count": ad_count,
        },
        aggregated_data={"certification_transparency_score": score},
        metadata={"stub": True, "enhancement": "priority_1"},
    )


@register_inference_function("supply_chain_quality_basefunction")
def f43(entity_id, context):
    """Infers supplier audit and quality signal for aerospace supply chain.

    Returns a score 0-100 where higher = better supply chain quality.
    Uses metadata: supplier_count, audit_pass_rate, critical_supplier_concentration.

    TODO: Connect to production supplier audit and quality management systems.
    """
    start = time.time()
    supplier_count = random.randint(5, 200)
    audit_pass_rate = round(random.uniform(0.6, 1.0), 2)
    critical_supplier_concentration = round(random.uniform(0.1, 0.8), 2)
    # Higher pass rate and lower concentration = better score
    score = max(0, min(100,
        (audit_pass_rate * 60) + ((1 - critical_supplier_concentration) * 30) + random.randint(-5, 5)
    ))
    return SignalResult(
        signal_id="supply_chain_quality",
        score=round(score, 1),
        confidence=0.55,
        execution_time_ms=(time.time() - start) * 1000,
        raw_data={
            "supplier_count": supplier_count,
            "audit_pass_rate": audit_pass_rate,
            "critical_supplier_concentration": critical_supplier_concentration,
        },
        aggregated_data={"supply_chain_quality_score": score},
        metadata={"stub": True, "enhancement": "priority_2"},
    )
