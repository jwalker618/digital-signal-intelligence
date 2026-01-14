"""
Aerospace Stub Extractors - Part 3

Signal Groups Covered:
- operational_quality (continued): crew_experience, training_indicators, 
                                   operational_complexity, growth_rate
- route_risk: conflict zones, challenging airports, weather exposure
- corporate_governance: management, safety leadership, reporting
- financial_stability: market position, government support
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from signals.extractors.base import StubExtractor, utcnow
from signals.types import ExtractorResult


# =============================================================================
# CREW AND TRAINING EXTRACTOR
# Signals: crew_experience, training_indicators
# =============================================================================

class CrewTrainingExtractor(StubExtractor):
    """
    STUB: Simulates crew experience and training data.
    
    Real implementation would query:
    - LinkedIn/professional networks for crew profiles
    - Training provider databases
    - Simulator utilization records
    - Job posting analysis
    
    Used for: crew_experience, training_indicators signals
    """
    SOURCE_NAME = "crew_training_database"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        # Crew experience metrics
        avg_captain_hours = self._random_int(5000, 20000)
        avg_fo_hours = self._random_int(1500, 8000)
        avg_captain_tenure = self._random_float(3, 20, 1)
        
        # Training investment signals
        has_sim_center = self._random_bool(0.3)
        training_partner_tier = self._random_choice([1, 2, 3], weights=[0.3, 0.5, 0.2])
        
        training_programs = []
        programs = ["LOFT", "CRM", "UPRT", "EBT", "THREAT_ERROR", "FATIGUE_MANAGEMENT"]
        for prog in programs:
            if self._random_bool(0.7):
                training_programs.append({
                    "program": prog,
                    "implemented": True,
                    "exceeds_regulatory": self._random_bool(0.4),
                    "last_update": self._random_date_iso(years_back=2),
                })
        
        # Hiring signals (indicates experience level being recruited)
        min_hiring_hours = self._random_int(500, 3000)
        hiring_rate = self._random_choice(["STABLE", "EXPANDING", "CONTRACTING", "RAPID_EXPANSION"])
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                # Crew experience
                "average_captain_flight_hours": avg_captain_hours,
                "average_fo_flight_hours": avg_fo_hours,
                "average_captain_tenure_years": avg_captain_tenure,
                "average_fo_tenure_years": self._random_float(1, 10, 1),
                "crew_turnover_rate": self._random_float(0.05, 0.25, 2),
                "industry_avg_captain_hours": 12000,
                "experience_vs_industry": round((avg_captain_hours - 12000) / 12000 * 100, 1),
                
                # Training infrastructure
                "has_own_simulator_center": has_sim_center,
                "simulator_count": self._random_int(1, 10) if has_sim_center else 0,
                "training_partner_tier": training_partner_tier,
                "training_partner": self._random_choice([
                    "CAE", "L3Harris", "FlightSafety", "Lufthansa Aviation Training", "Regional Provider"
                ]),
                
                # Training programs
                "training_programs": training_programs,
                "advanced_programs_count": len(training_programs),
                "exceeds_regulatory_count": sum(1 for p in training_programs if p.get("exceeds_regulatory")),
                
                # Hiring indicators
                "minimum_hiring_hours_requirement": min_hiring_hours,
                "hiring_trend": hiring_rate,
                "cadet_program": self._random_bool(0.3),
                
                # Certifications
                "atqp_approved": self._random_bool(0.4),  # Alternative Training and Qualification Programme
                "ebt_implemented": any(p["program"] == "EBT" for p in training_programs),
            }
        }
        
        return self._create_success_result(data)


# =============================================================================
# OPERATIONAL COMPLEXITY EXTRACTOR
# Signals: operational_complexity, growth_rate
# =============================================================================

class OperationalComplexityExtractor(StubExtractor):
    """
    STUB: Simulates operational complexity metrics.
    
    Real implementation would query:
    - OAG schedule data
    - Fleet diversity metrics
    - Route network analysis
    
    Used for: operational_complexity, growth_rate signals
    """
    SOURCE_NAME = "operational_complexity_analysis"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        # Network complexity
        destinations = self._random_int(5, 300)
        countries = self._random_int(1, 80)
        hubs = self._random_int(1, 10)
        
        # Fleet diversity
        aircraft_types = self._random_int(1, 15)
        engine_types = self._random_int(1, 8)
        
        # Operational variety
        operation_types = []
        if self._random_bool(0.8):
            operation_types.append("PASSENGER_SCHEDULED")
        if self._random_bool(0.4):
            operation_types.append("CARGO")
        if self._random_bool(0.3):
            operation_types.append("CHARTER")
        if self._random_bool(0.1):
            operation_types.append("WET_LEASE")
        
        # Growth metrics
        fleet_growth_yoy = self._random_float(-0.1, 0.3, 3)
        capacity_growth_yoy = self._random_float(-0.15, 0.35, 3)
        
        # Complexity score calculation (higher = more complex = higher risk)
        complexity_score = (
            min(destinations / 300 * 30, 30) +  # Max 30 points
            min(aircraft_types / 15 * 25, 25) +  # Max 25 points
            min(countries / 80 * 20, 20) +  # Max 20 points
            min(len(operation_types) / 4 * 15, 15) +  # Max 15 points
            (10 if fleet_growth_yoy > 0.15 else 0)  # Rapid growth penalty
        )
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                # Network complexity
                "destination_count": destinations,
                "country_count": countries,
                "hub_count": hubs,
                "is_hub_and_spoke": hubs > 0 and self._random_bool(0.6),
                "is_point_to_point": self._random_bool(0.4),
                
                # Fleet diversity
                "aircraft_type_count": aircraft_types,
                "engine_type_count": engine_types,
                "cockpit_commonality_pct": self._random_float(0.3, 1.0, 2),
                
                # Operational variety
                "operation_types": operation_types,
                "operation_type_count": len(operation_types),
                
                # Growth metrics
                "fleet_growth_yoy": fleet_growth_yoy,
                "capacity_growth_yoy": capacity_growth_yoy,
                "is_rapid_growth": fleet_growth_yoy > 0.15 or capacity_growth_yoy > 0.20,
                "is_contracting": fleet_growth_yoy < -0.05,
                
                # Risk score
                "complexity_score": round(complexity_score, 1),
                "complexity_tier": "HIGH" if complexity_score > 60 else ("MEDIUM" if complexity_score > 35 else "LOW"),
                
                # Industry context
                "daily_departures": self._random_int(10, 2000),
                "annual_passengers": self._random_int(100000, 100000000),
            }
        }
        
        return self._create_success_result(data)


# =============================================================================
# ROUTE RISK EXTRACTOR
# Signals: conflict_zone_exposure, challenging_airports, high_risk_destinations,
#          weather_exposure, terrain_exposure
# =============================================================================

class RouteRiskExtractor(StubExtractor):
    """
    STUB: Simulates route network risk analysis.
    
    Real implementation would query:
    - NOTAM databases
    - EUROCONTROL conflict zone data
    - Airport categorization databases
    - Weather hazard analysis
    
    Used for: conflict_zone_exposure, challenging_airports, 
              high_risk_destinations, weather_exposure, terrain_exposure signals
    """
    SOURCE_NAME = "route_risk_analysis"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    CONFLICT_ZONES = ["UKRAINE", "YEMEN", "SYRIA", "LIBYA", "SOMALIA", "IRAN_AIRSPACE"]
    CHALLENGING_AIRPORTS = ["LUKLA", "PARO", "INNSBRUCK", "MADEIRA", "TEGUCIGALPA", "ST_BARTS"]
    HIGH_RISK_COUNTRIES = ["AFGHANISTAN", "IRAQ", "VENEZUELA", "NORTH_KOREA", "ERITREA"]
    
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        total_routes = self._random_int(10, 500)
        
        # Conflict zone analysis
        conflict_exposure = self._random_bool(0.1)
        conflict_details = []
        if conflict_exposure:
            num_zones = self._random_int(1, 3)
            for _ in range(num_zones):
                conflict_details.append({
                    "zone": self._random_choice(self.CONFLICT_ZONES),
                    "exposure_type": self._random_choice(["OVERFLY", "DESTINATION", "PROXIMITY"]),
                    "routes_affected": self._random_int(1, 10),
                    "alternative_available": self._random_bool(0.7),
                })
        
        # Challenging airports
        challenging_pct = self._random_float(0, 0.15, 3)
        challenging_airports = []
        if challenging_pct > 0:
            num_challenging = max(1, int(total_routes * challenging_pct))
            for _ in range(min(num_challenging, 5)):
                challenging_airports.append({
                    "airport_code": self._random_choice(self.CHALLENGING_AIRPORTS + [self._random_string(3)]),
                    "challenge_type": self._random_choice([
                        "TERRAIN", "SHORT_RUNWAY", "WEATHER", "APPROACH_COMPLEXITY", "ALTITUDE"
                    ]),
                    "special_qualification_required": self._random_bool(0.8),
                    "frequency": self._random_choice(["DAILY", "WEEKLY", "SEASONAL"]),
                })
        
        # High-risk destination analysis
        high_risk_routes = self._random_int(0, int(total_routes * 0.1))
        high_risk_details = []
        if high_risk_routes > 0:
            for _ in range(min(high_risk_routes, 5)):
                high_risk_details.append({
                    "destination": self._random_choice(self.HIGH_RISK_COUNTRIES + [self._random_country_code()]),
                    "risk_factors": self._random_choice([
                        ["POLITICAL_INSTABILITY"],
                        ["TERRORISM_RISK"],
                        ["INFRASTRUCTURE_CONCERNS"],
                        ["POLITICAL_INSTABILITY", "TERRORISM_RISK"],
                    ]),
                    "advisory_level": self._random_choice(["CAUTION", "RECONSIDER", "DO_NOT_TRAVEL"]),
                })
        
        # Weather exposure
        severe_weather_routes = self._random_float(0, 0.30, 3)
        weather_exposure = {
            "tropical_cyclone_exposure": self._random_bool(0.2),
            "monsoon_exposure": self._random_bool(0.25),
            "winter_operations_pct": self._random_float(0, 0.5, 2),
            "severe_turbulence_routes_pct": severe_weather_routes,
            "volcanic_ash_exposure_regions": self._random_int(0, 3),
        }
        
        # Terrain exposure
        terrain_exposure = {
            "mountainous_approach_pct": self._random_float(0, 0.2, 3),
            "high_altitude_airports_count": self._random_int(0, 10),
            "overwater_operations_pct": self._random_float(0, 0.3, 2),
            "etops_operations": self._random_bool(0.3),
            "etops_minutes": self._random_choice([60, 120, 180, 240, None]),
        }
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "total_routes_analyzed": total_routes,
                
                # Conflict zones
                "has_conflict_zone_exposure": conflict_exposure,
                "conflict_zones": conflict_details,
                "conflict_zone_routes_pct": len(conflict_details) / total_routes * 100 if conflict_details else 0,
                
                # Challenging airports
                "challenging_airport_pct": round(challenging_pct * 100, 1),
                "challenging_airports": challenging_airports,
                "requires_special_qualification": any(a["special_qualification_required"] for a in challenging_airports),
                
                # High-risk destinations
                "high_risk_destination_count": high_risk_routes,
                "high_risk_destinations": high_risk_details,
                "high_risk_route_pct": round(high_risk_routes / total_routes * 100, 1) if total_routes > 0 else 0,
                
                # Weather
                "weather_exposure": weather_exposure,
                "severe_weather_route_pct": round(severe_weather_routes * 100, 1),
                
                # Terrain
                "terrain_exposure": terrain_exposure,
                "complex_terrain_operations": terrain_exposure["mountainous_approach_pct"] > 0.1,
            }
        }
        
        return self._create_success_result(data)


# =============================================================================
# SAFETY LEADERSHIP EXTRACTOR
# Signals: safety_leadership, safety_reporting
# =============================================================================

class SafetyLeadershipExtractor(StubExtractor):
    """
    STUB: Simulates safety leadership and culture indicators.
    
    Real implementation would query:
    - Company website/about pages
    - LinkedIn for safety leadership roles
    - Public safety reports
    - Press releases
    
    Used for: safety_leadership, safety_reporting signals
    """
    SOURCE_NAME = "safety_leadership_analysis"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        # Safety leadership structure
        has_cso = self._random_bool(0.6)  # Chief Safety Officer
        has_safety_board_rep = self._random_bool(0.3)
        has_sms = self._random_bool(0.85)  # Safety Management System
        
        safety_leadership = {
            "has_chief_safety_officer": has_cso,
            "cso_reports_to": self._random_choice(["CEO", "COO", "BOARD"]) if has_cso else None,
            "cso_tenure_years": self._random_int(1, 15) if has_cso else None,
            "has_safety_board_committee": has_safety_board_rep,
            "safety_committee_meetings_per_year": self._random_int(4, 12) if has_safety_board_rep else None,
            "dedicated_safety_staff_count": self._random_int(2, 50),
            "safety_staff_per_aircraft": self._random_float(0.1, 0.5, 2),
        }
        
        # Safety Management System
        sms_details = {
            "sms_implemented": has_sms,
            "sms_maturity_level": self._random_int(1, 4) if has_sms else 0,
            "sms_certification": self._random_choice(["ICAO_ANNEX19", "FAA_AC", "EASA_PART_ORG", None]) if has_sms else None,
            "last_sms_audit_date": self._random_date_iso(years_back=2) if has_sms else None,
            "sms_audit_findings": self._random_int(0, 10) if has_sms else None,
        }
        
        # Safety reporting and transparency
        publishes_safety_report = self._random_bool(0.4)
        safety_reporting = {
            "publishes_annual_safety_report": publishes_safety_report,
            "safety_report_url": f"https://example.com/{entity_id}/safety" if publishes_safety_report else None,
            "voluntary_reporting_system": self._random_bool(0.7),
            "just_culture_policy": self._random_bool(0.6),
            "safety_kpis_published": self._random_bool(0.3),
            "participates_in_asias": self._random_bool(0.4),  # Aviation Safety Information Analysis and Sharing
            "flight_data_monitoring_program": self._random_bool(0.75),
            "foqa_program": self._random_bool(0.6),  # Flight Operational Quality Assurance
        }
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "safety_leadership": safety_leadership,
                "sms": sms_details,
                "safety_reporting": safety_reporting,
                
                # Summary metrics
                "safety_culture_score": self._calculate_safety_culture_score(
                    safety_leadership, sms_details, safety_reporting
                ),
                "safety_transparency_score": self._calculate_transparency_score(safety_reporting),
            }
        }
        
        return self._create_success_result(data)
    
    def _calculate_safety_culture_score(self, leadership, sms, reporting) -> int:
        """Calculate a safety culture score 0-100."""
        score = 0
        if leadership["has_chief_safety_officer"]:
            score += 20
        if leadership["has_safety_board_committee"]:
            score += 15
        if sms["sms_implemented"]:
            score += 20 + (sms["sms_maturity_level"] or 0) * 5
        if reporting["voluntary_reporting_system"]:
            score += 10
        if reporting["just_culture_policy"]:
            score += 10
        if reporting["flight_data_monitoring_program"]:
            score += 10
        return min(100, score)
    
    def _calculate_transparency_score(self, reporting) -> int:
        """Calculate a transparency score 0-100."""
        score = 0
        if reporting["publishes_annual_safety_report"]:
            score += 40
        if reporting["safety_kpis_published"]:
            score += 30
        if reporting["participates_in_asias"]:
            score += 30
        return min(100, score)


# =============================================================================
# MARKET POSITION EXTRACTOR
# Signal: market_position
# =============================================================================

class MarketPositionExtractor(StubExtractor):
    """
    STUB: Simulates market position and competitive analysis.
    
    Real implementation would query:
    - IATA statistics
    - OAG market share data
    - Industry reports
    
    Used for: market_position signal
    """
    SOURCE_NAME = "market_position_analysis"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        # Market position metrics
        is_flag_carrier = self._random_bool(0.2)
        is_market_leader = self._random_bool(0.15)
        
        market_share_domestic = self._random_float(0.01, 0.50, 3)
        market_share_international = self._random_float(0.001, 0.20, 4)
        
        # Competitive position
        competitors_count = self._random_int(2, 20)
        market_concentration = self._random_choice(["CONCENTRATED", "MODERATE", "FRAGMENTED"])
        
        # Brand and reputation
        brand_value_rank = self._random_int(1, 100) if self._random_bool(0.3) else None
        skytrax_rating = self._random_choice([3, 4, 5, None], weights=[0.3, 0.3, 0.2, 0.2])
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "is_flag_carrier": is_flag_carrier,
                "is_market_leader": is_market_leader,
                "domestic_market_share_pct": round(market_share_domestic * 100, 1),
                "international_market_share_pct": round(market_share_international * 100, 1),
                "market_rank_domestic": self._random_int(1, 10) if market_share_domestic > 0.05 else self._random_int(5, 30),
                "market_rank_international": self._random_int(1, 50),
                "competitors_count": competitors_count,
                "market_concentration": market_concentration,
                "brand_value_rank_global": brand_value_rank,
                "skytrax_rating": skytrax_rating,
                "route_network_strength": self._random_choice(["STRONG", "MODERATE", "LIMITED"]),
                "hub_strength": self._random_choice(["DOMINANT", "SIGNIFICANT", "MINOR", "NONE"]),
            }
        }
        
        return self._create_success_result(data)


# =============================================================================
# GOVERNMENT SUPPORT EXTRACTOR
# Signal: government_support
# =============================================================================

class GovernmentSupportExtractor(StubExtractor):
    """
    STUB: Simulates government ownership and support data.
    
    Real implementation would query:
    - Public ownership records
    - Government subsidy databases
    - State aid announcements
    
    Used for: government_support signal
    """
    SOURCE_NAME = "government_support_database"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        is_state_owned = self._random_bool(0.15)
        has_government_stake = self._random_bool(0.25) if not is_state_owned else True
        
        government_ownership = None
        if has_government_stake:
            if is_state_owned:
                ownership_pct = self._random_float(0.51, 1.0, 2)
            else:
                ownership_pct = self._random_float(0.05, 0.50, 2)
            
            government_ownership = {
                "ownership_percentage": round(ownership_pct * 100, 1),
                "is_majority_owned": ownership_pct > 0.5,
                "sovereign_wealth_fund": self._random_bool(0.3),
                "direct_government": self._random_bool(0.7),
                "owning_entity": self._random_choice([
                    "Ministry of Transport",
                    "National Investment Fund",
                    "Sovereign Wealth Fund",
                    "State Holding Company",
                ]),
            }
        
        # Support mechanisms
        has_received_support = self._random_bool(0.3)
        support_history = []
        if has_received_support:
            num_supports = self._random_int(1, 3)
            for _ in range(num_supports):
                support_history.append({
                    "support_type": self._random_choice([
                        "DIRECT_SUBSIDY", "LOAN_GUARANTEE", "TAX_RELIEF",
                        "ROUTE_SUBSIDY", "COVID_RELIEF", "EQUITY_INJECTION"
                    ]),
                    "amount_usd": self._random_float(1e6, 5e9, 0),
                    "year": self._random_int(2018, 2024),
                    "ongoing": self._random_bool(0.3),
                })
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "is_state_owned": is_state_owned,
                "has_government_stake": has_government_stake,
                "government_ownership": government_ownership,
                "is_flag_carrier": is_state_owned or (has_government_stake and self._random_bool(0.5)),
                "has_received_government_support": has_received_support,
                "support_history": support_history,
                "total_support_received_usd": sum(s["amount_usd"] for s in support_history),
                "ongoing_support": any(s["ongoing"] for s in support_history),
                "implicit_guarantee": is_state_owned or (has_government_stake and government_ownership and government_ownership["ownership_percentage"] > 30),
            }
        }
        
        return self._create_success_result(data)


# =============================================================================
# MAINTENANCE INDICATORS EXTRACTOR
# Signal: maintenance_indicators
# =============================================================================

class MaintenanceIndicatorsExtractor(StubExtractor):
    """
    STUB: Simulates maintenance quality indicators.
    
    Real implementation would query:
    - AD compliance databases
    - Service bulletin compliance
    - Maintenance event tracking
    
    Used for: maintenance_indicators signal
    """
    SOURCE_NAME = "maintenance_indicators"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        # Airworthiness directive compliance
        ad_compliance_rate = self._random_float(0.95, 1.0, 4)
        overdue_ads = self._random_int(0, 3) if ad_compliance_rate < 0.99 else 0
        
        # Service bulletin compliance
        sb_compliance_rate = self._random_float(0.80, 0.98, 3)
        
        # Maintenance events
        tech_dispatch_rate = self._random_float(0.97, 0.999, 4)
        
        # AOG events (Aircraft on Ground)
        aog_events_monthly = self._random_int(0, 5)
        avg_aog_duration_hours = self._random_float(4, 48, 1)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                # Compliance
                "ad_compliance_rate": ad_compliance_rate,
                "overdue_airworthiness_directives": overdue_ads,
                "sb_compliance_rate": sb_compliance_rate,
                "critical_sb_compliance_rate": self._random_float(0.98, 1.0, 3),
                
                # Reliability
                "technical_dispatch_reliability": tech_dispatch_rate,
                "pilot_reported_defects_per_100_hours": self._random_float(1, 10, 1),
                "repeat_defect_rate": self._random_float(0.02, 0.15, 3),
                
                # AOG metrics
                "aog_events_per_month": aog_events_monthly,
                "average_aog_duration_hours": avg_aog_duration_hours,
                
                # Investment indicators
                "maintenance_cost_per_flight_hour": self._random_float(200, 800, 0),
                "maintenance_reserve_funded": self._random_bool(0.7),
                "predictive_maintenance_program": self._random_bool(0.4),
                
                # Quality indicators
                "maintenance_error_rate": self._random_float(0.001, 0.01, 4),
                "ground_damage_events_annual": self._random_int(0, 10),
            }
        }
        
        return self._create_success_result(data)
