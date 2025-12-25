"""
Aerospace Aggregators - Remaining Signal Groups

Covers:
- operational_quality: OTP, dispatch, crew, training, complexity, growth
- fleet_quality: age, homogeneity, generation, orders, maintenance
- route_risk: conflict zones, airports, destinations, weather, terrain
- corporate_governance: management, safety leadership, reporting, structure, engagement
- financial_stability: credit, financials, market position, government support
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from ...base import ProductionAggregator
from ....types import AggregatorResult, ExtractorResult


# =============================================================================
# OPERATIONAL QUALITY
# =============================================================================

class FlightOperationsAggregator(ProductionAggregator):
    """
    Transforms flight operations data into performance metrics.
    
    Expected input (from FlightOperationsExtractor):
        {
            "data": {
                "otp_15min_pct": float,
                "otp_vs_industry": float,
                "dispatch_reliability_pct": float,
                "dispatch_vs_industry": float,
                "cancellation_rate_pct": float,
                ...
            }
        }
    
    Output:
        OTP score and dispatch reliability score.
    """
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        
        if not raw:
            return self._create_error_result("No operations data available")
        
        otp = self._normalize_float(raw.get("otp_15min_pct"), 0.75)
        otp_vs_industry = self._normalize_float(raw.get("otp_vs_industry"), 0)
        dispatch = self._normalize_float(raw.get("dispatch_reliability_pct"), 0.98)
        dispatch_vs_industry = self._normalize_float(raw.get("dispatch_vs_industry"), 0)
        cancellation = self._normalize_float(raw.get("cancellation_rate_pct"), 0.02)
        
        # OTP score (scaled 0-100)
        # 92%+ = 100, 65% = 0
        otp_score = max(0, min(100, (otp - 0.65) / 0.27 * 100))
        
        # Dispatch score
        # 99.9%+ = 100, 95% = 0
        dispatch_score = max(0, min(100, (dispatch - 0.95) / 0.049 * 100))
        
        return self._create_success_result({
            "otp_pct": round(otp * 100, 1),
            "otp_vs_industry": round(otp_vs_industry, 1),
            "dispatch_pct": round(dispatch * 100, 2),
            "dispatch_vs_industry": round(dispatch_vs_industry, 2),
            "cancellation_rate": round(cancellation * 100, 2),
            "otp_score": round(otp_score, 1),
            "dispatch_score": round(dispatch_score, 1),
        }, extractor_results, warnings)


class CrewTrainingAggregator(ProductionAggregator):
    """
    Transforms crew/training data into experience and investment metrics.
    
    Output:
        crew_experience_score and training_indicators_score.
    """
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        
        if not raw:
            return self._create_error_result("No crew data available")
        
        captain_hours = self._normalize_int(raw.get("average_captain_flight_hours"), 10000)
        captain_tenure = self._normalize_float(raw.get("average_captain_tenure_years"), 5)
        turnover = self._normalize_float(raw.get("crew_turnover_rate"), 0.1)
        experience_vs_industry = self._normalize_float(raw.get("experience_vs_industry"), 0)
        
        training_programs = self._normalize_int(raw.get("advanced_programs_count"), 0)
        exceeds_regulatory = self._normalize_int(raw.get("exceeds_regulatory_count"), 0)
        has_sim_center = self._normalize_bool(raw.get("has_own_simulator_center"))
        training_tier = self._normalize_int(raw.get("training_partner_tier"), 2)
        
        # Experience score
        # Based on hours, tenure, and turnover
        hours_score = min(captain_hours / 15000, 1) * 40
        tenure_score = min(captain_tenure / 10, 1) * 30
        turnover_penalty = min(turnover / 0.20, 1) * 20
        
        experience_score = hours_score + tenure_score + 30 - turnover_penalty
        
        # Training score
        training_score = 40  # Base
        training_score += min(training_programs * 5, 25)
        training_score += exceeds_regulatory * 5
        if has_sim_center:
            training_score += 15
        if training_tier == 1:
            training_score += 10
        elif training_tier == 3:
            training_score -= 10
        
        return self._create_success_result({
            "captain_hours": captain_hours,
            "captain_tenure": round(captain_tenure, 1),
            "turnover_rate": round(turnover * 100, 1),
            "training_programs": training_programs,
            "has_sim_center": has_sim_center,
            "crew_experience_score": round(max(0, min(100, experience_score)), 1),
            "training_indicators_score": round(max(0, min(100, training_score)), 1),
        }, extractor_results, warnings)


class OperationalComplexityAggregator(ProductionAggregator):
    """
    Transforms operational complexity data into risk metrics.
    
    Output:
        operational_complexity_score and growth_rate_score.
    """
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        
        if not raw:
            return self._create_error_result("No complexity data available")
        
        destinations = self._normalize_int(raw.get("destination_count"), 50)
        aircraft_types = self._normalize_int(raw.get("aircraft_type_count"), 2)
        operation_types = self._normalize_int(raw.get("operation_type_count"), 1)
        complexity_score_raw = self._normalize_float(raw.get("complexity_score"), 50)
        
        fleet_growth = self._normalize_float(raw.get("fleet_growth_yoy"), 0)
        capacity_growth = self._normalize_float(raw.get("capacity_growth_yoy"), 0)
        is_rapid = self._normalize_bool(raw.get("is_rapid_growth"))
        
        # Complexity score (lower complexity = higher score for insurance)
        # Invert the raw complexity score
        complexity_score = 100 - complexity_score_raw
        
        # Growth rate score
        # Moderate growth is good, rapid growth is risky, contraction is concerning
        if is_rapid:
            growth_score = 50  # Rapid growth is risky
            warnings.append("Rapid growth detected - increased operational risk")
        elif fleet_growth < -0.05:
            growth_score = 60  # Contraction may indicate issues
        elif fleet_growth < 0:
            growth_score = 75
        elif fleet_growth <= 0.10:
            growth_score = 90  # Healthy moderate growth
        else:
            growth_score = 70  # Fast but not rapid
        
        return self._create_success_result({
            "destinations": destinations,
            "aircraft_types": aircraft_types,
            "operation_types": operation_types,
            "fleet_growth_pct": round(fleet_growth * 100, 1),
            "capacity_growth_pct": round(capacity_growth * 100, 1),
            "is_rapid_growth": is_rapid,
            "operational_complexity_score": round(max(0, min(100, complexity_score)), 1),
            "growth_rate_score": round(growth_score, 1),
        }, extractor_results, warnings)


# =============================================================================
# FLEET QUALITY
# =============================================================================

class FleetQualityAggregator(ProductionAggregator):
    """
    Transforms fleet registry data into quality metrics.
    
    Output:
        fleet_age_score, fleet_homogeneity_score, aircraft_generation_score.
    """
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        
        if not raw:
            return self._create_error_result("No fleet data available")
        
        fleet_size = self._normalize_int(raw.get("fleet_size"), 1)
        avg_age = self._normalize_float(raw.get("average_fleet_age"), 12)
        age_vs_industry = self._normalize_float(raw.get("age_vs_industry"), 0)
        homogeneity = self._normalize_float(raw.get("homogeneity_score"), 50)
        new_gen_pct = self._normalize_float(raw.get("new_generation_percentage"), 30)
        type_count = self._normalize_int(raw.get("type_count"), 2)
        
        # Fleet age score (younger = better)
        # 0-5 years = 100, 20+ years = 20
        if avg_age <= 5:
            age_score = 100
        elif avg_age <= 10:
            age_score = 85
        elif avg_age <= 15:
            age_score = 65
        elif avg_age <= 20:
            age_score = 45
        else:
            age_score = 25
        
        # Homogeneity score (already 0-100 where higher = more homogeneous)
        homogeneity_score = homogeneity
        
        # Generation score (more new gen = better)
        generation_score = new_gen_pct  # Already 0-100
        
        return self._create_success_result({
            "fleet_size": fleet_size,
            "average_age": round(avg_age, 1),
            "age_vs_industry": round(age_vs_industry, 1),
            "type_count": type_count,
            "homogeneity_pct": round(homogeneity, 1),
            "new_generation_pct": round(new_gen_pct, 1),
            "fleet_age_score": round(age_score, 1),
            "fleet_homogeneity_score": round(homogeneity_score, 1),
            "aircraft_generation_score": round(generation_score, 1),
        }, extractor_results, warnings)


class OrderBacklogAggregator(ProductionAggregator):
    """
    Transforms order backlog data into investment metrics.
    
    Output:
        order_backlog_score.
    """
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        
        if not raw:
            return self._create_error_result("No order data available")
        
        has_orders = self._normalize_bool(raw.get("has_order_backlog"))
        firm_orders = self._normalize_int(raw.get("total_firm_orders"), 0)
        years_backlog = self._normalize_float(raw.get("years_of_backlog"), 0)
        signal = raw.get("investment_signal", "LOW")
        
        # Score based on investment signal
        if signal == "STRONG":
            score = 90
        elif signal == "MODERATE":
            score = 70
        elif has_orders:
            score = 55
        else:
            score = 40  # No orders isn't terrible but shows less investment
        
        return self._create_success_result({
            "has_orders": has_orders,
            "firm_orders": firm_orders,
            "years_of_backlog": round(years_backlog, 1),
            "investment_signal": signal,
            "order_backlog_score": score,
        }, extractor_results, warnings)


class MaintenanceIndicatorsAggregator(ProductionAggregator):
    """
    Transforms maintenance data into quality metrics.
    
    Output:
        maintenance_indicators_score.
    """
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        
        if not raw:
            return self._create_error_result("No maintenance data available")
        
        ad_compliance = self._normalize_float(raw.get("ad_compliance_rate"), 0.99)
        tech_dispatch = self._normalize_float(raw.get("technical_dispatch_reliability"), 0.98)
        overdue_ads = self._normalize_int(raw.get("overdue_airworthiness_directives"), 0)
        aog_events = self._normalize_int(raw.get("aog_events_per_month"), 2)
        predictive = self._normalize_bool(raw.get("predictive_maintenance_program"))
        
        # Start with base score
        score = 60
        
        # AD compliance (critical)
        if ad_compliance >= 0.999:
            score += 20
        elif ad_compliance >= 0.99:
            score += 15
        elif ad_compliance >= 0.98:
            score += 10
        else:
            score -= 10
        
        if overdue_ads > 0:
            score -= overdue_ads * 10
            warnings.append(f"{overdue_ads} overdue Airworthiness Directive(s)")
        
        # Tech dispatch
        if tech_dispatch >= 0.99:
            score += 15
        elif tech_dispatch >= 0.98:
            score += 10
        
        # Predictive maintenance bonus
        if predictive:
            score += 10
        
        # AOG penalty
        if aog_events > 3:
            score -= 5
        
        return self._create_success_result({
            "ad_compliance_pct": round(ad_compliance * 100, 2),
            "tech_dispatch_pct": round(tech_dispatch * 100, 2),
            "overdue_ads": overdue_ads,
            "aog_events_monthly": aog_events,
            "has_predictive_maintenance": predictive,
            "maintenance_indicators_score": round(max(0, min(100, score)), 1),
        }, extractor_results, warnings)


# =============================================================================
# ROUTE RISK
# =============================================================================

class RouteRiskAggregator(ProductionAggregator):
    """
    Transforms route risk data into exposure metrics.
    
    Output:
        Scores for all 5 route risk signals.
    """
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        
        if not raw:
            return self._create_error_result("No route risk data available")
        
        # Conflict zone
        has_conflict = self._normalize_bool(raw.get("has_conflict_zone_exposure"))
        conflict_pct = self._normalize_float(raw.get("conflict_zone_routes_pct"), 0)
        
        # Challenging airports
        challenging_pct = self._normalize_float(raw.get("challenging_airport_pct"), 0)
        special_qual = self._normalize_bool(raw.get("requires_special_qualification"))
        
        # High risk destinations
        high_risk_pct = self._normalize_float(raw.get("high_risk_route_pct"), 0)
        
        # Weather
        weather_data = raw.get("weather_exposure", {})
        severe_weather_pct = self._normalize_float(raw.get("severe_weather_route_pct"), 0)
        
        # Terrain
        terrain_data = raw.get("terrain_exposure", {})
        mountain_pct = self._normalize_float(terrain_data.get("mountainous_approach_pct"), 0) if terrain_data else 0
        
        # Calculate scores (100 = low risk, 0 = high risk)
        
        # Conflict zone score
        if has_conflict:
            conflict_score = max(0, 100 - conflict_pct * 5)
            warnings.append("Operates through/near conflict zones")
        else:
            conflict_score = 100
        
        # Challenging airports score
        challenging_score = max(0, 100 - challenging_pct * 100 * 3)
        
        # High risk destinations score
        high_risk_score = max(0, 100 - high_risk_pct * 4)
        
        # Weather exposure score
        weather_score = max(0, 100 - severe_weather_pct * 100 * 2)
        
        # Terrain exposure score
        terrain_score = max(0, 100 - mountain_pct * 100 * 3)
        
        return self._create_success_result({
            "has_conflict_exposure": has_conflict,
            "conflict_zone_pct": round(conflict_pct, 2),
            "challenging_airport_pct": round(challenging_pct * 100, 1),
            "high_risk_destination_pct": round(high_risk_pct, 1),
            "severe_weather_pct": round(severe_weather_pct * 100, 1),
            "mountainous_approach_pct": round(mountain_pct * 100, 1),
            "conflict_zone_score": round(conflict_score, 1),
            "challenging_airports_score": round(challenging_score, 1),
            "high_risk_destinations_score": round(high_risk_score, 1),
            "weather_exposure_score": round(weather_score, 1),
            "terrain_exposure_score": round(terrain_score, 1),
        }, extractor_results, warnings)


# =============================================================================
# CORPORATE GOVERNANCE
# =============================================================================

class SafetyLeadershipAggregator(ProductionAggregator):
    """
    Transforms safety leadership data into governance metrics.
    
    Output:
        safety_leadership_score and safety_reporting_score.
    """
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        
        if not raw:
            return self._create_error_result("No safety leadership data available")
        
        leadership = raw.get("safety_leadership", {})
        sms = raw.get("sms", {})
        reporting = raw.get("safety_reporting", {})
        
        has_cso = self._normalize_bool(leadership.get("has_chief_safety_officer"))
        has_board_committee = self._normalize_bool(leadership.get("has_safety_board_committee"))
        has_sms = self._normalize_bool(sms.get("sms_implemented"))
        sms_maturity = self._normalize_int(sms.get("sms_maturity_level"), 0)
        
        publishes_report = self._normalize_bool(reporting.get("publishes_annual_safety_report"))
        just_culture = self._normalize_bool(reporting.get("just_culture_policy"))
        foqa = self._normalize_bool(reporting.get("foqa_program"))
        kpis_published = self._normalize_bool(reporting.get("safety_kpis_published"))
        
        # Safety culture score (from raw data or calculate)
        culture_score = self._normalize_float(raw.get("safety_culture_score"), None)
        if culture_score is None:
            culture_score = 0
            if has_cso:
                culture_score += 25
            if has_board_committee:
                culture_score += 20
            if has_sms:
                culture_score += 25 + sms_maturity * 5
            if just_culture:
                culture_score += 15
            if foqa:
                culture_score += 15
        
        # Transparency score
        transparency_score = self._normalize_float(raw.get("safety_transparency_score"), None)
        if transparency_score is None:
            transparency_score = 0
            if publishes_report:
                transparency_score += 50
            if kpis_published:
                transparency_score += 30
            if foqa:
                transparency_score += 20
        
        return self._create_success_result({
            "has_cso": has_cso,
            "has_board_committee": has_board_committee,
            "has_sms": has_sms,
            "sms_maturity": sms_maturity,
            "publishes_report": publishes_report,
            "just_culture": just_culture,
            "has_foqa": foqa,
            "safety_leadership_score": round(min(100, culture_score), 1),
            "safety_reporting_score": round(min(100, transparency_score), 1),
        }, extractor_results, warnings)


# =============================================================================
# FINANCIAL STABILITY
# =============================================================================

class MarketPositionAggregator(ProductionAggregator):
    """
    Transforms market position data into competitive metrics.
    
    Output:
        market_position_score.
    """
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        
        if not raw:
            return self._create_error_result("No market position data available")
        
        is_flag = self._normalize_bool(raw.get("is_flag_carrier"))
        is_leader = self._normalize_bool(raw.get("is_market_leader"))
        domestic_share = self._normalize_float(raw.get("domestic_market_share_pct"), 5)
        domestic_rank = self._normalize_int(raw.get("market_rank_domestic"), 10)
        skytrax = raw.get("skytrax_rating")
        network_strength = raw.get("route_network_strength", "MODERATE")
        
        # Calculate score
        score = 40  # Base
        
        if is_flag:
            score += 15
        if is_leader:
            score += 15
        
        # Market share bonus
        if domestic_share >= 30:
            score += 15
        elif domestic_share >= 20:
            score += 10
        elif domestic_share >= 10:
            score += 5
        
        # Ranking bonus
        if domestic_rank <= 3:
            score += 10
        elif domestic_rank <= 5:
            score += 5
        
        # Skytrax bonus
        if skytrax == 5:
            score += 10
        elif skytrax == 4:
            score += 5
        
        return self._create_success_result({
            "is_flag_carrier": is_flag,
            "is_market_leader": is_leader,
            "domestic_share_pct": round(domestic_share, 1),
            "domestic_rank": domestic_rank,
            "skytrax_rating": skytrax,
            "network_strength": network_strength,
            "market_position_score": round(min(100, score), 1),
        }, extractor_results, warnings)


class GovernmentSupportAggregator(ProductionAggregator):
    """
    Transforms government support data into stability metrics.
    
    Output:
        government_support_score.
    """
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        
        if not raw:
            return self._create_error_result("No government support data available")
        
        is_state_owned = self._normalize_bool(raw.get("is_state_owned"))
        has_stake = self._normalize_bool(raw.get("has_government_stake"))
        implicit_guarantee = self._normalize_bool(raw.get("implicit_guarantee"))
        is_flag = self._normalize_bool(raw.get("is_flag_carrier"))
        received_support = self._normalize_bool(raw.get("has_received_government_support"))
        
        ownership = raw.get("government_ownership", {})
        ownership_pct = self._normalize_float(ownership.get("ownership_percentage"), 0) if ownership else 0
        
        # Score reflects stability from government backing
        # Note: This is a stability indicator, not a judgment
        score = 50  # Neutral base
        
        if is_state_owned:
            score += 35  # Strong implicit support
        elif has_stake and ownership_pct > 25:
            score += 25
        elif has_stake:
            score += 15
        
        if is_flag:
            score += 10
        
        if implicit_guarantee:
            score += 10
        
        if received_support:
            score += 5  # Demonstrated willingness to support
        
        # Cap at 100
        score = min(100, score)
        
        return self._create_success_result({
            "is_state_owned": is_state_owned,
            "has_government_stake": has_stake,
            "ownership_pct": round(ownership_pct, 1),
            "is_flag_carrier": is_flag,
            "implicit_guarantee": implicit_guarantee,
            "received_support": received_support,
            "government_support_score": round(score, 1),
        }, extractor_results, warnings)
