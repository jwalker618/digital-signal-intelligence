"""
Marine Inference Functions - All Signal Groups

Maps YAML inference_utility_function names to pipeline orchestration.
43 signals + 5 categorical = 48 total functions
"""

import time
from ....types import SignalResult, InferenceContext
from ....inference.registry import register_inference_function

from ....extractors.stubs.marine import (
    # Network Authority
    ClassificationSocietyExtractor, PIClubExtractor, ChartererQualityExtractor,
    MarineBankingRelationshipExtractor, FlagStateExtractor, MarineIndustryAssociationExtractor,
    TechnicalManagerExtractor, PortRelationshipExtractor,
    # Operational Telemetry
    AISComplianceExtractor, DarkActivityExtractor, RouteRiskExtractor,
    PSCRegionExposureExtractor, OperationalEfficiencyExtractor, WeatherRoutingExtractor,
    # Safety Compliance
    PSCDetentionExtractor, PSCDeficiencyExtractor, ClassStatusExtractor,
    ISMComplianceExtractor, CasualtyHistoryExtractor, TotalLossHistoryExtractor,
    # Fleet Profile
    FleetAgeExtractor, FleetStabilityExtractor, VesselQualityExtractor,
    CrewCertificationExtractor, ManagementConsistencyExtractor,
    # Sanctions Compliance
    SanctionsStatusExtractor, OwnershipTransparencyExtractor, JurisdictionRiskExtractor,
    STSPatternExtractor, HistoricalSanctionsExtractor,
    # Environmental
    IMO2020ComplianceExtractor, BWMComplianceExtractor, CIIRatingExtractor, EnvironmentalIncidentExtractor,
    # Corporate Footprint
    MarineWebsiteQualityExtractor, FleetListDisclosureExtractor, MarineSustainabilityReportingExtractor,
    SafetyCultureExtractor, CrewWelfareExtractor, MarineIndustryPresenceExtractor,
    # Structured Data
    VettingExtractor, MarineESGRatingExtractor, MarineCreditRatingExtractor,
    # Categorical
    OperatorClassificationExtractor, VesselCategoryExtractor, TradingPatternExtractor,
    FlagStateQualityExtractor, MarineFleetAgeExtractor,
)

from ....aggregators.implementations.marine import (
    # Network Authority
    ClassificationSocietyAggregator, PIClubAggregator, ChartererQualityAggregator,
    MarineBankingAggregator, FlagStateAggregator, MarineIndustryAssociationAggregator,
    TechnicalManagerAggregator, PortRelationshipAggregator,
    # Operational Telemetry
    AISComplianceAggregator, DarkActivityAggregator, RouteRiskAggregator,
    PSCRegionAggregator, OperationalEfficiencyAggregator, WeatherRoutingAggregator,
    # Safety Compliance
    PSCDetentionAggregator, PSCDeficiencyAggregator, ClassStatusAggregator,
    ISMComplianceAggregator, CasualtyHistoryAggregator, TotalLossHistoryAggregator,
    # Fleet Profile
    FleetAgeAggregator, FleetStabilityAggregator, VesselQualityAggregator,
    CrewCertificationAggregator, ManagementConsistencyAggregator,
    # Sanctions Compliance
    SanctionsStatusAggregator, OwnershipTransparencyAggregator, JurisdictionRiskAggregator,
    STSPatternAggregator, HistoricalSanctionsAggregator,
    # Environmental
    IMO2020ComplianceAggregator, BWMComplianceAggregator, CIIRatingAggregator, EnvironmentalIncidentAggregator,
    # Corporate Footprint
    MarineWebsiteQualityAggregator, FleetListDisclosureAggregator, MarineSustainabilityAggregator,
    SafetyCultureAggregator, CrewWelfareAggregator, MarineIndustryPresenceAggregator,
    # Structured Data
    VettingAggregator, MarineESGRatingAggregator, MarineCreditRatingAggregator,
    # Categorical
    OperatorClassificationAggregator, VesselCategoryAggregator, TradingPatternAggregator,
    FlagStateQualityAggregator, FleetAgeBandAggregator,
)


def _run_pipeline(signal_id, extractor, aggregator, entity_id, context, score_field, default=50):
    start = time.time()
    try:
        ext = extractor.extract(entity_id, context=context)
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
# CATEGORICAL (5)
# =============================================================================

@register_inference_function("operator_classification_basefunction")
def f1(e, c): return _run_categorical("operator_type", OperatorClassificationExtractor(), OperatorClassificationAggregator(), e, c, "operator_type", "INDEPENDENT")

@register_inference_function("primaryvessel_category_basefunction")
def f2(e, c): return _run_categorical("vessel_category", VesselCategoryExtractor(), VesselCategoryAggregator(), e, c, "vessel_category", "GENERAL_CARGO")

@register_inference_function("trading_pattern_basefunction")
def f3(e, c): return _run_categorical("trading_pattern", TradingPatternExtractor(), TradingPatternAggregator(), e, c, "trading_pattern", "MIXED")

@register_inference_function("flagstate_quality_basefunction")
def f4(e, c): return _run_categorical("flag_state_quality", FlagStateQualityExtractor(), FlagStateQualityAggregator(), e, c, "flag_state_quality", "GREY_LIST")

@register_inference_function("marine_fleet_age_basefunction")
def f5(e, c): return _run_categorical("fleet_age_band", MarineFleetAgeExtractor(), FleetAgeBandAggregator(), e, c, "fleet_age_band", "AGE_10_15")


# =============================================================================
# NETWORK AUTHORITY (8)
# =============================================================================

@register_inference_function("classification_society_basefunction")
def f6(e, c): return _run_pipeline("classification_society", ClassificationSocietyExtractor(), ClassificationSocietyAggregator(), e, c, "classification_society_score", 70)

@register_inference_function("pi_club_basefunction")
def f7(e, c): return _run_pipeline("pi_club", PIClubExtractor(), PIClubAggregator(), e, c, "pi_club_score", 60)

@register_inference_function("chartere_quality_basefunction")
def f8(e, c): return _run_pipeline("charterer_quality", ChartererQualityExtractor(), ChartererQualityAggregator(), e, c, "charterer_quality_score", 60)

@register_inference_function("marine_banking_relationship_basefunction")
def f9(e, c): return _run_pipeline("banking_relationship", MarineBankingExtractor(), MarineBankingAggregator(), e, c, "banking_relationship_score", 50)

@register_inference_function("flag_state_basefunction")
def f10(e, c): return _run_pipeline("flag_state", FlagStateExtractor(), FlagStateAggregator(), e, c, "flag_state_score", 60)

@register_inference_function("marine_industry_association_basefunction")
def f11(e, c): return _run_pipeline("industry_association", MarineIndustryAssociationExtractor(), MarineIndustryAssociationAggregator(), e, c, "industry_association_score", 40)

@register_inference_function("technical_manager_basefunction")
def f12(e, c): return _run_pipeline("technical_manager", TechnicalManagerExtractor(), TechnicalManagerAggregator(), e, c, "technical_manager_score", 70)

@register_inference_function("port_relationship_basefunction")
def f13(e, c): return _run_pipeline("port_relationship", PortRelationshipExtractor(), PortRelationshipAggregator(), e, c, "port_relationship_score", 65)


# =============================================================================
# OPERATIONAL TELEMETRY (6)
# =============================================================================

@register_inference_function("ais_compliance_basefunction")
def f14(e, c): return _run_pipeline("ais_compliance", AISComplianceExtractor(), AISComplianceAggregator(), e, c, "ais_compliance_score", 90)

@register_inference_function("dark_activity_basefunction")
def f15(e, c): return _run_pipeline("dark_activity", DarkActivityExtractor(), DarkActivityAggregator(), e, c, "dark_activity_score", 90)

@register_inference_function("route_risk_basefunction")
def f16(e, c): return _run_pipeline("route_risk", RouteRiskExtractor(), RouteRiskAggregator(), e, c, "route_risk_score", 70)

@register_inference_function("psc_regions_basefunction")
def f17(e, c): return _run_pipeline("psc_region_exposure", PSCRegionExposureExtractor(), PSCRegionAggregator(), e, c, "psc_region_score", 65)

@register_inference_function("operational_efficiency_basefunction")
def f18(e, c): return _run_pipeline("operational_efficiency", OperationalEfficiencyExtractor(), OperationalEfficiencyAggregator(), e, c, "operational_efficiency_score", 70)

@register_inference_function("weather_routing_basefunction")
def f19(e, c): return _run_pipeline("weather_routing", WeatherRoutingExtractor(), WeatherRoutingAggregator(), e, c, "weather_routing_score", 70)


# =============================================================================
# SAFETY COMPLIANCE (6)
# =============================================================================

@register_inference_function("psc_detention_basefunction")
def f20(e, c): return _run_pipeline("psc_detention", PSCDetentionExtractor(), PSCDetentionAggregator(), e, c, "psc_detention_score", 85)

@register_inference_function("psc_deficiency_basefunction")
def f21(e, c): return _run_pipeline("psc_deficiency", PSCDeficiencyExtractor(), PSCDeficiencyAggregator(), e, c, "psc_deficiency_score", 75)

@register_inference_function("class_status_basefunction")
def f22(e, c): return _run_pipeline("class_status", ClassStatusExtractor(), ClassStatusAggregator(), e, c, "class_status_score", 90)

@register_inference_function("ism_compliance_basefunction")
def f23(e, c): return _run_pipeline("ism_compliance", ISMComplianceExtractor(), ISMComplianceAggregator(), e, c, "ism_compliance_score", 90)

@register_inference_function("casualty_history_basefunction")
def f24(e, c): return _run_pipeline("casualty_history", CasualtyHistoryExtractor(), CasualtyHistoryAggregator(), e, c, "casualty_history_score", 90)

@register_inference_function("totalloss_history_basefunction")
def f25(e, c): return _run_pipeline("total_loss", TotalLossHistoryExtractor(), TotalLossHistoryAggregator(), e, c, "total_loss_score", 100)


# =============================================================================
# FLEET PROFILE (5)
# =============================================================================

@register_inference_function("fleet_age_basefunction")
def f26(e, c): return _run_pipeline("fleet_age", FleetAgeExtractor(), FleetAgeAggregator(), e, c, "fleet_age_score", 70)

@register_inference_function("fleet_stability_basefunction")
def f27(e, c): return _run_pipeline("fleet_stability", FleetStabilityExtractor(), FleetStabilityAggregator(), e, c, "fleet_stability_score", 70)

@register_inference_function("vessel_quality_basefunction")
def f28(e, c): return _run_pipeline("vessel_quality", VesselQualityExtractor(), VesselQualityAggregator(), e, c, "vessel_quality_score", 65)

@register_inference_function("crew_certification_basefunction")
def f29(e, c): return _run_pipeline("crew_certification", CrewCertificationExtractor(), CrewCertificationAggregator(), e, c, "crew_certification_score", 80)

@register_inference_function("management_consistency_basefunction")
def f30(e, c): return _run_pipeline("management_consistency", ManagementConsistencyExtractor(), ManagementConsistencyAggregator(), e, c, "management_consistency_score", 75)


# =============================================================================
# SANCTIONS COMPLIANCE (5)
# =============================================================================

@register_inference_function("sanctions_status_basefunction")
def f31(e, c): return _run_pipeline("sanctions_status", SanctionsStatusExtractor(), SanctionsStatusAggregator(), e, c, "sanctions_status_score", 100)

@register_inference_function("ownership_transparency_basefunction")
def f32(e, c): return _run_pipeline("ownership_transparency", OwnershipTransparencyExtractor(), OwnershipTransparencyAggregator(), e, c, "ownership_transparency_score", 70)

@register_inference_function("jurisdiction_risk_basefunction")
def f33(e, c): return _run_pipeline("jurisdiction_risk", JurisdictionRiskExtractor(), JurisdictionRiskAggregator(), e, c, "jurisdiction_risk_score", 80)

@register_inference_function("sts_pattern_basefunction")
def f34(e, c): return _run_pipeline("sts_pattern", STSPatternExtractor(), STSPatternAggregator(), e, c, "sts_pattern_score", 90)

@register_inference_function("historiccal_sanctions_basefunction")
def f35(e, c): return _run_pipeline("historical_sanctions", HistoricalSanctionsExtractor(), HistoricalSanctionsAggregator(), e, c, "historical_sanctions_score", 100)


# =============================================================================
# ENVIRONMENTAL (4)
# =============================================================================

@register_inference_function("imo_compliance_basefunction")
def f36(e, c): return _run_pipeline("imo2020_compliance", IMO2020ComplianceExtractor(), IMO2020ComplianceAggregator(), e, c, "imo2020_compliance_score", 85)

@register_inference_function("bwm_compliance_basefunction")
def f37(e, c): return _run_pipeline("bwm_compliance", BWMComplianceExtractor(), BWMComplianceAggregator(), e, c, "bwm_compliance_score", 80)

@register_inference_function("cii_rating_basefunction")
def f38(e, c): return _run_pipeline("cii_rating", CIIRatingExtractor(), CIIRatingAggregator(), e, c, "cii_rating_score", 65)

@register_inference_function("enviromental_incident_basefunction")
def f39(e, c): return _run_pipeline("environmental_incident", EnvironmentalIncidentExtractor(), EnvironmentalIncidentAggregator(), e, c, "environmental_incident_score", 90)


# =============================================================================
# CORPORATE FOOTPRINT (6)
# =============================================================================

@register_inference_function("marine_website_quality_basefunction")
def f40(e, c): return _run_pipeline("website_quality", MarineWebsiteQualityExtractor(), MarineWebsiteQualityAggregator(), e, c, "website_quality_score", 50)

@register_inference_function("fleet_list_basefunction")
def f41(e, c): return _run_pipeline("fleet_disclosure", FleetListDisclosureExtractor(), FleetListDisclosureAggregator(), e, c, "fleet_list_score", 50)

@register_inference_function("marine_sustainability_reporting_basefunction")
def f42(e, c): return _run_pipeline("sustainability_reporting", MarineSustainabilityReportingExtractor(), MarineSustainabilityAggregator(), e, c, "sustainability_reporting_score", 40)

@register_inference_function("safety_culture_basefunction")
def f43(e, c): return _run_pipeline("safety_communication", SafetyCultureExtractor(), SafetyCultureAggregator(), e, c, "safety_culture_score", 50)

@register_inference_function("crew_welfare_basefunction")
def f44(e, c): return _run_pipeline("crew_welfare", CrewWelfareExtractor(), CrewWelfareAggregator(), e, c, "crew_welfare_score", 65)

@register_inference_function("marine_industry_presence_basefunction")
def f45(e, c): return _run_pipeline("industry_presence", MarineIndustryPresenceExtractor(), MarineIndustryPresenceAggregator(), e, c, "industry_presence_score", 50)


# =============================================================================
# STRUCTURED DATA (3)
# =============================================================================

@register_inference_function("vetting_basefunction")
def f46(e, c): return _run_pipeline("vetting", VettingExtractor(), VettingAggregator(), e, c, "vetting_score", 60)

@register_inference_function("marine_esg_rating_basefunction")
def f47(e, c): return _run_pipeline("esg_rating", MarineESGRatingExtractor(), MarineESGRatingAggregator(), e, c, "esg_rating_score", 50)

@register_inference_function("marine_credit_rating_basefunction")
def f48(e, c): return _run_pipeline("credit_rating", MarineCreditRatingExtractor(), MarineCreditRatingAggregator(), e, c, "credit_rating_score", 50)
