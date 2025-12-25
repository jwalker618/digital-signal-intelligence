"""
Aerospace Inference Functions - Remaining Signal Groups

Signal Groups:
- operational_quality: OTP, dispatch, crew, training, complexity, growth
- fleet_quality: age, homogeneity, generation, orders, maintenance
- route_risk: conflict zones, airports, destinations, weather, terrain
- corporate_governance: management, safety leadership, reporting, structure, engagement
- financial_stability: credit, financials, market position, government support
"""

import time
from typing import Dict, Any, Optional

from ...types import SignalResult, InferenceContext
from ...inference.registry import register_inference_function

# Extractors
from ...extractors.stubs.aerospace import (
    FlightOperationsExtractor,
    CrewTrainingExtractor,
    OperationalComplexityExtractor,
    FleetRegistryExtractor,
    OrderBacklogExtractor,
    MaintenanceIndicatorsExtractor,
    RouteRiskExtractor,
    SafetyLeadershipExtractor,
    MarketPositionExtractor,
    GovernmentSupportExtractor,
)
from ...extractors.stubs.common import (
    CreditRatingExtractor,
    PublicFinancialsExtractor,
    CorporateRegistryExtractor,
    IndustryAssociationExtractor,
)

# Aggregators
from ...aggregators.implementations.aerospace import (
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
from ...aggregators.implementations.common import (
    CreditRatingAggregator,
    PublicFinancialsAggregator,
    CorporateGovernanceAggregator,
    IndustryEngagementAggregator,
)


def _create_signal_result(
    signal_id: str,
    score: float,
    confidence: float,
    execution_time: float,
    extract_result,
    agg_result,
    extractor_name: str,
    aggregator_name: str,
) -> SignalResult:
    """Helper to create consistent SignalResult objects."""
    return SignalResult(
        signal_id=signal_id,
        score=score,
        confidence=confidence,
        execution_time_ms=execution_time,
        raw_data=extract_result.data if extract_result else None,
        aggregated_data=agg_result.data if agg_result else None,
        metadata={
            "extractor": extractor_name,
            "aggregator": aggregator_name,
            "from_cache": extract_result.from_cache if extract_result else False,
        }
    )


# =============================================================================
# OPERATIONAL QUALITY
# =============================================================================

@register_inference_function("otp_score_basefunction")
def otp_score_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for otp_score signal (On-Time Performance)."""
    start_time = time.time()
    
    try:
        extractor = FlightOperationsExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="otp_score", score=70, confidence=0.3, error="Extraction failed")
        
        aggregator = FlightOperationsAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("otp_score", 70) if agg_result.success else 70
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("otp_score", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "FlightOperationsExtractor", "FlightOperationsAggregator")
    except Exception as e:
        return SignalResult(signal_id="otp_score", score=70, confidence=0.0, error=str(e))


@register_inference_function("dispatch_reliability_basefunction")
def dispatch_reliability_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for dispatch_reliability signal."""
    start_time = time.time()
    
    try:
        extractor = FlightOperationsExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="dispatch_reliability", score=70, confidence=0.3, error="Extraction failed")
        
        aggregator = FlightOperationsAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("dispatch_score", 70) if agg_result.success else 70
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("dispatch_reliability", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "FlightOperationsExtractor", "FlightOperationsAggregator")
    except Exception as e:
        return SignalResult(signal_id="dispatch_reliability", score=70, confidence=0.0, error=str(e))


@register_inference_function("crew_experience_basefunction")
def crew_experience_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for crew_experience signal."""
    start_time = time.time()
    
    try:
        extractor = CrewTrainingExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="crew_experience", score=60, confidence=0.3, error="Extraction failed")
        
        aggregator = CrewTrainingAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("crew_experience_score", 60) if agg_result.success else 60
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("crew_experience", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "CrewTrainingExtractor", "CrewTrainingAggregator")
    except Exception as e:
        return SignalResult(signal_id="crew_experience", score=60, confidence=0.0, error=str(e))


@register_inference_function("training_indicators_basefunction")
def training_indicators_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for training_indicators signal."""
    start_time = time.time()
    
    try:
        extractor = CrewTrainingExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="training_indicators", score=60, confidence=0.3, error="Extraction failed")
        
        aggregator = CrewTrainingAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("training_indicators_score", 60) if agg_result.success else 60
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("training_indicators", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "CrewTrainingExtractor", "CrewTrainingAggregator")
    except Exception as e:
        return SignalResult(signal_id="training_indicators", score=60, confidence=0.0, error=str(e))


@register_inference_function("operational_complexity_basefunction")
def operational_complexity_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for operational_complexity signal."""
    start_time = time.time()
    
    try:
        extractor = OperationalComplexityExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="operational_complexity", score=60, confidence=0.3, error="Extraction failed")
        
        aggregator = OperationalComplexityAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("operational_complexity_score", 60) if agg_result.success else 60
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("operational_complexity", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "OperationalComplexityExtractor", "OperationalComplexityAggregator")
    except Exception as e:
        return SignalResult(signal_id="operational_complexity", score=60, confidence=0.0, error=str(e))


@register_inference_function("growth_rate_basefunction")
def growth_rate_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for growth_rate signal."""
    start_time = time.time()
    
    try:
        extractor = OperationalComplexityExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="growth_rate", score=70, confidence=0.3, error="Extraction failed")
        
        aggregator = OperationalComplexityAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("growth_rate_score", 70) if agg_result.success else 70
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("growth_rate", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "OperationalComplexityExtractor", "OperationalComplexityAggregator")
    except Exception as e:
        return SignalResult(signal_id="growth_rate", score=70, confidence=0.0, error=str(e))


# =============================================================================
# FLEET QUALITY
# =============================================================================

@register_inference_function("fleet_age_basefunction")
def fleet_age_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for fleet_age signal."""
    start_time = time.time()
    
    try:
        extractor = FleetRegistryExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="fleet_age", score=60, confidence=0.3, error="Extraction failed")
        
        aggregator = FleetQualityAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("fleet_age_score", 60) if agg_result.success else 60
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("fleet_age", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "FleetRegistryExtractor", "FleetQualityAggregator")
    except Exception as e:
        return SignalResult(signal_id="fleet_age", score=60, confidence=0.0, error=str(e))


@register_inference_function("fleet_homgenity_basefunction")  # Note: typo matches YAML
def fleet_homogeneity_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for fleet_homogeneity signal."""
    start_time = time.time()
    
    try:
        extractor = FleetRegistryExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="fleet_homogeneity", score=60, confidence=0.3, error="Extraction failed")
        
        aggregator = FleetQualityAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("fleet_homogeneity_score", 60) if agg_result.success else 60
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("fleet_homogeneity", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "FleetRegistryExtractor", "FleetQualityAggregator")
    except Exception as e:
        return SignalResult(signal_id="fleet_homogeneity", score=60, confidence=0.0, error=str(e))


@register_inference_function("aircraft_generation_basefunction")
def aircraft_generation_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for aircraft_generation signal."""
    start_time = time.time()
    
    try:
        extractor = FleetRegistryExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="aircraft_generation", score=50, confidence=0.3, error="Extraction failed")
        
        aggregator = FleetQualityAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("aircraft_generation_score", 50) if agg_result.success else 50
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("aircraft_generation", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "FleetRegistryExtractor", "FleetQualityAggregator")
    except Exception as e:
        return SignalResult(signal_id="aircraft_generation", score=50, confidence=0.0, error=str(e))


@register_inference_function("order_backlog_basefunction")
def order_backlog_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for order_backlog signal."""
    start_time = time.time()
    
    try:
        extractor = OrderBacklogExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="order_backlog", score=50, confidence=0.3, error="Extraction failed")
        
        aggregator = OrderBacklogAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("order_backlog_score", 50) if agg_result.success else 50
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("order_backlog", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "OrderBacklogExtractor", "OrderBacklogAggregator")
    except Exception as e:
        return SignalResult(signal_id="order_backlog", score=50, confidence=0.0, error=str(e))


@register_inference_function("maintenece_indicators_basefunction")  # Note: typo matches YAML
def maintenance_indicators_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for maintenance_indicators signal."""
    start_time = time.time()
    
    try:
        extractor = MaintenanceIndicatorsExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="maintenance_indicators", score=70, confidence=0.3, error="Extraction failed")
        
        aggregator = MaintenanceIndicatorsAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("maintenance_indicators_score", 70) if agg_result.success else 70
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("maintenance_indicators", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "MaintenanceIndicatorsExtractor", "MaintenanceIndicatorsAggregator")
    except Exception as e:
        return SignalResult(signal_id="maintenance_indicators", score=70, confidence=0.0, error=str(e))


# =============================================================================
# ROUTE RISK
# =============================================================================

@register_inference_function("conflict_zone_basefunction")
def conflict_zone_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for conflict_zone_exposure signal."""
    start_time = time.time()
    
    try:
        extractor = RouteRiskExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="conflict_zone_exposure", score=90, confidence=0.3, error="Extraction failed")
        
        aggregator = RouteRiskAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("conflict_zone_score", 90) if agg_result.success else 90
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("conflict_zone_exposure", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "RouteRiskExtractor", "RouteRiskAggregator")
    except Exception as e:
        return SignalResult(signal_id="conflict_zone_exposure", score=90, confidence=0.0, error=str(e))


@register_inference_function("challenging_aiports_basefunction")  # Note: typo matches YAML
def challenging_airports_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for challenging_airports signal."""
    start_time = time.time()
    
    try:
        extractor = RouteRiskExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="challenging_airports", score=80, confidence=0.3, error="Extraction failed")
        
        aggregator = RouteRiskAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("challenging_airports_score", 80) if agg_result.success else 80
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("challenging_airports", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "RouteRiskExtractor", "RouteRiskAggregator")
    except Exception as e:
        return SignalResult(signal_id="challenging_airports", score=80, confidence=0.0, error=str(e))


@register_inference_function("highrisk_exposure_basefunction")
def highrisk_exposure_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for high_risk_destinations signal."""
    start_time = time.time()
    
    try:
        extractor = RouteRiskExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="high_risk_destinations", score=85, confidence=0.3, error="Extraction failed")
        
        aggregator = RouteRiskAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("high_risk_destinations_score", 85) if agg_result.success else 85
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("high_risk_destinations", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "RouteRiskExtractor", "RouteRiskAggregator")
    except Exception as e:
        return SignalResult(signal_id="high_risk_destinations", score=85, confidence=0.0, error=str(e))


@register_inference_function("weather_exposure_basefunction")
def weather_exposure_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for weather_exposure signal."""
    start_time = time.time()
    
    try:
        extractor = RouteRiskExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="weather_exposure", score=75, confidence=0.3, error="Extraction failed")
        
        aggregator = RouteRiskAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("weather_exposure_score", 75) if agg_result.success else 75
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("weather_exposure", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "RouteRiskExtractor", "RouteRiskAggregator")
    except Exception as e:
        return SignalResult(signal_id="weather_exposure", score=75, confidence=0.0, error=str(e))


@register_inference_function("terrain_exposure_basefunction")
def terrain_exposure_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for terrain_exposure signal."""
    start_time = time.time()
    
    try:
        extractor = RouteRiskExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="terrain_exposure", score=80, confidence=0.3, error="Extraction failed")
        
        aggregator = RouteRiskAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("terrain_exposure_score", 80) if agg_result.success else 80
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("terrain_exposure", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "RouteRiskExtractor", "RouteRiskAggregator")
    except Exception as e:
        return SignalResult(signal_id="terrain_exposure", score=80, confidence=0.0, error=str(e))


# =============================================================================
# CORPORATE GOVERNANCE
# =============================================================================

@register_inference_function("management_stability_basefunction")
def management_stability_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for management_stability signal."""
    start_time = time.time()
    
    try:
        extractor = CorporateRegistryExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="management_stability", score=60, confidence=0.3, error="Extraction failed")
        
        aggregator = CorporateGovernanceAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("management_stability_score", 60) if agg_result.success else 60
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("management_stability", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "CorporateRegistryExtractor", "CorporateGovernanceAggregator")
    except Exception as e:
        return SignalResult(signal_id="management_stability", score=60, confidence=0.0, error=str(e))


@register_inference_function("safety_leadership_basefunction")
def safety_leadership_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for safety_leadership signal."""
    start_time = time.time()
    
    try:
        extractor = SafetyLeadershipExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="safety_leadership", score=50, confidence=0.3, error="Extraction failed")
        
        aggregator = SafetyLeadershipAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("safety_leadership_score", 50) if agg_result.success else 50
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("safety_leadership", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "SafetyLeadershipExtractor", "SafetyLeadershipAggregator")
    except Exception as e:
        return SignalResult(signal_id="safety_leadership", score=50, confidence=0.0, error=str(e))


@register_inference_function("saefty_reporting_basefunction")  # Note: typo matches YAML
def safety_reporting_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for safety_reporting signal."""
    start_time = time.time()
    
    try:
        extractor = SafetyLeadershipExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="safety_reporting", score=50, confidence=0.3, error="Extraction failed")
        
        aggregator = SafetyLeadershipAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("safety_reporting_score", 50) if agg_result.success else 50
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("safety_reporting", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "SafetyLeadershipExtractor", "SafetyLeadershipAggregator")
    except Exception as e:
        return SignalResult(signal_id="safety_reporting", score=50, confidence=0.0, error=str(e))


@register_inference_function("corporate_structure_basefunction")
def corporate_structure_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for corporate_structure signal."""
    start_time = time.time()
    
    try:
        extractor = CorporateRegistryExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="corporate_structure", score=60, confidence=0.3, error="Extraction failed")
        
        aggregator = CorporateGovernanceAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        # Corporate structure score based on transparency and independence
        score = agg_result.data.get("board_independence_score", 60) if agg_result.success else 60
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("corporate_structure", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "CorporateRegistryExtractor", "CorporateGovernanceAggregator")
    except Exception as e:
        return SignalResult(signal_id="corporate_structure", score=60, confidence=0.0, error=str(e))


@register_inference_function("industry_enngagement_basefunction")  # Note: typo matches YAML
def industry_engagement_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for industry_engagement signal."""
    start_time = time.time()
    
    try:
        extractor = IndustryAssociationExtractor()
        extract_result = extractor.extract(entity_id, industry="AVIATION", context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="industry_engagement", score=40, confidence=0.3, error="Extraction failed")
        
        aggregator = IndustryEngagementAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("engagement_score", 40) if agg_result.success else 40
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("industry_engagement", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "IndustryAssociationExtractor", "IndustryEngagementAggregator")
    except Exception as e:
        return SignalResult(signal_id="industry_engagement", score=40, confidence=0.0, error=str(e))


# =============================================================================
# FINANCIAL STABILITY
# =============================================================================

@register_inference_function("credit_rating_basefunction")
def credit_rating_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for credit_rating signal."""
    start_time = time.time()
    
    try:
        extractor = CreditRatingExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="credit_rating", score=50, confidence=0.3, error="Extraction failed")
        
        aggregator = CreditRatingAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        # Use average rating score, default to 50 if no rating
        if agg_result.success and agg_result.data.get("has_rating"):
            score = agg_result.data.get("average_rating_score", 50)
        else:
            score = 50  # Neutral for no rating
        
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("credit_rating", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "CreditRatingExtractor", "CreditRatingAggregator")
    except Exception as e:
        return SignalResult(signal_id="credit_rating", score=50, confidence=0.0, error=str(e))


@register_inference_function("public_financials_basefunction")
def public_financials_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for public_financials signal."""
    start_time = time.time()
    
    try:
        extractor = PublicFinancialsExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="public_financials", score=50, confidence=0.3, error="Extraction failed")
        
        aggregator = PublicFinancialsAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("financial_health_score", 50) if agg_result.success else 50
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("public_financials", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "PublicFinancialsExtractor", "PublicFinancialsAggregator")
    except Exception as e:
        return SignalResult(signal_id="public_financials", score=50, confidence=0.0, error=str(e))


@register_inference_function("market_position_basefunction")
def market_position_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for market_position signal."""
    start_time = time.time()
    
    try:
        extractor = MarketPositionExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="market_position", score=50, confidence=0.3, error="Extraction failed")
        
        aggregator = MarketPositionAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("market_position_score", 50) if agg_result.success else 50
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("market_position", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "MarketPositionExtractor", "MarketPositionAggregator")
    except Exception as e:
        return SignalResult(signal_id="market_position", score=50, confidence=0.0, error=str(e))


@register_inference_function("goverment_support_basefunction")  # Note: typo matches YAML
def government_support_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for government_support signal."""
    start_time = time.time()
    
    try:
        extractor = GovernmentSupportExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="government_support", score=50, confidence=0.3, error="Extraction failed")
        
        aggregator = GovernmentSupportAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("government_support_score", 50) if agg_result.success else 50
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("government_support", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "GovernmentSupportExtractor", "GovernmentSupportAggregator")
    except Exception as e:
        return SignalResult(signal_id="government_support", score=50, confidence=0.0, error=str(e))
