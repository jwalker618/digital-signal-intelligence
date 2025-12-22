"""
extractors/#coverage#.py - Coverage Inference Functions
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from .base import (
    TTLCategory,
    TTLConfig,
    DataSource,
    SignalResult,
    ExtractionResult,
    MissingSignalStrategy,
    SignalWeightConfig,
    DataExtractor,

    EXTRACTOR_REGISTRY,

    register_extractor
)

logger = logging.getLogger(__name__)

# =============================================================================
# AEROSPACE EXTRACTORS
# =============================================================================

@register_extractor
class AircraftFleetExtractor(DataExtractor):
    """
    Aircraft Fleet Data - Fleet composition, age, ownership.
    
    Signals: fleet_size, fleet_age, fleet_homogeneity, aircraft_generation, order_backlog
    
    Alternative Sources:
    - Cirium: fleets/aircraft
    - ch-aviation: fleets/list
    - Planespotters: operators/fleet
    - FAA Registry: aircraft/by_owner
    """
    source_name = "aircraft_fleet"
    coverage = "aerospace"
    signals = ["fleet_size", "fleet_age", "fleet_homogeneity", "aircraft_generation", "order_backlog"]
    ttl_config = TTLConfig.semi_static("Fleet composition changes weekly")
    
    alternative_sources = [
        DataSource("api", "cirium", "fleets/aircraft", priority=1),
        DataSource("api", "ch_aviation", "fleets/list", priority=2),
        DataSource("api", "planespotters", "operators/fleet", priority=3),
        DataSource("registry", "faa_registry", "aircraft/by_owner", priority=4),
    ]

    def extract(self) -> ExtractionResult:
        fleet_size = self._weighted_choice([
            (self._rng.randint(1, 10), 0.30), (self._rng.randint(11, 50), 0.35),
            (self._rng.randint(51, 200), 0.25), (self._rng.randint(201, 800), 0.10)
        ])
        
        aircraft_types = ["B737", "A320", "B777", "A350", "B787", "A330", "E190", "CRJ", "ATR"]
        primary_type = self._rng.choice(aircraft_types[:4])
        
        aircraft = []
        type_counts = {}
        total_age = 0
        
        for i in range(fleet_size):
            if i < fleet_size * 0.6:
                ac_type = primary_type
            else:
                ac_type = self._rng.choice(aircraft_types)
            
            type_counts[ac_type] = type_counts.get(ac_type, 0) + 1
            age = self._rng.randint(0, 25)
            total_age += age
            
            aircraft.append({
                "registration": self._random_id("N", 5) if self._rng.random() > 0.50 else self._random_id("G-", 4),
                "type": ac_type,
                "age_years": age,
                "build_year": 2024 - age,
                "ownership": self._weighted_choice([("Owned", 0.35), ("Finance Lease", 0.30), ("Operating Lease", 0.35)]),
                "lessor": self._rng.choice(["AerCap", "SMBC", "Avolon", "BOC Aviation", "GECAS", None]) if self._rng.random() > 0.35 else None,
            })
        
        avg_age = total_age / fleet_size if fleet_size > 0 else 0
        homogeneity = max(type_counts.values()) / fleet_size if fleet_size > 0 else 0
        
        raw_data = {
            "operator_id": self.kwargs.get("operator_id", self._random_id("OP", 6)),
            "fleet_summary": {
                "total_aircraft": fleet_size,
                "average_age_years": round(avg_age, 1),
                "newest_aircraft_age": min(a["age_years"] for a in aircraft) if aircraft else 0,
                "oldest_aircraft_age": max(a["age_years"] for a in aircraft) if aircraft else 0,
                "type_count": len(type_counts),
                "primary_type": primary_type,
                "homogeneity_score": round(homogeneity, 2),
            },
            "type_distribution": type_counts,
            "ownership_breakdown": {
                "owned": sum(1 for a in aircraft if a["ownership"] == "Owned"),
                "finance_lease": sum(1 for a in aircraft if a["ownership"] == "Finance Lease"),
                "operating_lease": sum(1 for a in aircraft if a["ownership"] == "Operating Lease"),
            },
            "order_backlog": {
                "total_orders": self._rng.randint(0, 100),
                "deliveries_next_12mo": self._rng.randint(0, 20),
                "types_ordered": self._rng.sample(["B737 MAX", "A320neo", "A350", "B787"], self._rng.randint(0, 3)),
            },
            "aircraft": aircraft[:50],
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "fleet_size": fleet_size,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class OperationalPerformanceExtractor(DataExtractor):
    """
    Operational Performance - OTP, dispatch reliability, completion factor.
    
    Signals: otp_score, dispatch_reliability, operational_complexity, growth_rate
    
    Alternative Sources:
    - OAG: performance/otp
    - Cirium: performance/punctuality
    """
    source_name = "operational_performance"
    coverage = "aerospace"
    signals = ["otp_score", "dispatch_reliability", "operational_complexity", "growth_rate"]
    ttl_config = TTLConfig.dynamic("Performance metrics updated daily")
    
    alternative_sources = [
        DataSource("api", "oag", "performance/otp", priority=1),
        DataSource("api", "cirium", "performance/punctuality", priority=2),
        DataSource("api", "cirium", "performance/dispatch", priority=3),
    ]

    def extract(self) -> ExtractionResult:
        otp = round(self._rng.uniform(65, 92), 1)
        dispatch = round(self._rng.uniform(97, 99.9), 2)
        completion = round(self._rng.uniform(96, 99.5), 2)
        
        raw_data = {
            "operator_id": self.kwargs.get("operator_id", self._random_id("OP", 6)),
            "performance_metrics": {
                "on_time_performance_pct": otp,
                "dispatch_reliability_pct": dispatch,
                "completion_factor_pct": completion,
                "average_delay_minutes": self._rng.randint(5, 45),
                "cancellation_rate_pct": round(100 - completion, 2),
            },
            "benchmark_comparison": {
                "otp_vs_industry": round(otp - 78, 1),
                "dispatch_vs_industry": round(dispatch - 98.5, 2),
                "ranking_percentile": self._rng.randint(10, 95),
            },
            "operational_complexity": {
                "fleet_types": self._rng.randint(1, 8),
                "destinations": self._rng.randint(20, 300),
                "daily_departures": self._rng.randint(50, 2000),
                "hub_count": self._rng.randint(1, 10),
                "complexity_score": self._weighted_choice([("Low", 0.20), ("Medium", 0.50), ("High", 0.30)]),
            },
            "growth_metrics": {
                "asm_growth_yoy_pct": round(self._rng.uniform(-10, 25), 1),
                "passenger_growth_yoy_pct": round(self._rng.uniform(-5, 20), 1),
                "route_additions_12mo": self._rng.randint(0, 30),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "otp": otp,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class MROProviderExtractor(DataExtractor):
    """
    MRO Provider Data - Maintenance quality, approvals, capabilities.
    
    Signals: mro_quality, maintenance_indicators
    
    Alternative Sources:
    - FAA: repair_stations/145
    - EASA: part_145_approvals
    """
    source_name = "mro_provider"
    coverage = "aerospace"
    signals = ["mro_quality", "maintenance_indicators"]
    ttl_config = TTLConfig.semi_static("MRO relationships change infrequently")
    
    alternative_sources = [
        DataSource("registry", "faa", "repair_stations/145", priority=1),
        DataSource("registry", "easa", "part_145_approvals", priority=2),
    ]

    def extract(self) -> ExtractionResult:
        mro_tier = self._weighted_choice([
            ("OEM Affiliated", 0.20), ("Major Independent", 0.30),
            ("Regional", 0.30), ("In-House", 0.20)
        ])
        
        capabilities = ["Airframe", "Engine", "Component", "Line Maintenance", "Base Maintenance"]
        
        raw_data = {
            "operator_id": self.kwargs.get("operator_id", self._random_id("OP", 6)),
            "primary_mro": {
                "provider_name": self._random_company_name("Aviation Services"),
                "tier": mro_tier,
                "faa_145_certified": True,
                "easa_145_certified": self._rng.random() > 0.20,
                "capabilities": self._rng.sample(capabilities, self._rng.randint(2, 5)),
            },
            "maintenance_quality": {
                "audit_findings_12mo": self._rng.randint(0, 15),
                "repeat_findings": self._rng.randint(0, 5),
                "ad_compliance_rate_pct": round(self._rng.uniform(98, 100), 1),
                "unscheduled_maintenance_rate": round(self._rng.uniform(0.5, 5), 2),
            },
            "mro_relationship": {
                "years_with_provider": self._rng.randint(1, 20),
                "contract_type": self._weighted_choice([("Flight Hour", 0.40), ("Fixed Price", 0.35), ("Time & Materials", 0.25)]),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "mro_tier": mro_tier,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class CrewTrainingExtractor(DataExtractor):
    """
    Crew Training Data - Training programs, experience levels.
    
    Signals: crew_experience, training_indicators
    
    Alternative Sources:
    - CAE: training/customers
    - FlightSafety: clients
    - LinkedIn: people/search
    """
    source_name = "crew_training"
    coverage = "aerospace"
    signals = ["crew_experience", "training_indicators"]
    ttl_config = TTLConfig.semi_static("Training data updated weekly")
    
    alternative_sources = [
        DataSource("api", "cae", "training/customers", priority=1),
        DataSource("api", "flightsafety", "clients", priority=2),
        DataSource("api", "linkedin", "people/search", {"title": ["Captain", "First Officer"]}, priority=3),
    ]

    def extract(self) -> ExtractionResult:
        avg_captain_hours = self._rng.randint(5000, 20000)
        avg_fo_hours = self._rng.randint(2000, 8000)
        
        raw_data = {
            "operator_id": self.kwargs.get("operator_id", self._random_id("OP", 6)),
            "crew_experience": {
                "average_captain_hours": avg_captain_hours,
                "average_fo_hours": avg_fo_hours,
                "min_hiring_hours": self._rng.choice([500, 1000, 1500, 2500]),
                "captain_upgrade_hours": self._rng.choice([3000, 4000, 5000]),
            },
            "training_program": {
                "simulator_provider": self._weighted_choice([("CAE", 0.35), ("FlightSafety", 0.30), ("In-House", 0.25), ("Other", 0.10)]),
                "recurrent_frequency_months": 6,
                "advanced_training": {
                    "upset_recovery": self._rng.random() > 0.20,
                    "aqa_program": self._rng.random() > 0.30,
                    "losa_program": self._rng.random() > 0.40,
                },
                "training_hours_per_pilot_annual": self._rng.randint(40, 120),
            },
            "crew_metrics": {
                "total_pilots": self._rng.randint(50, 5000),
                "turnover_rate_pct": round(self._rng.uniform(3, 20), 1),
                "check_airman_ratio": round(self._rng.uniform(0.05, 0.15), 3),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "avg_captain_hours": avg_captain_hours,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class AviationFinancialExtractor(DataExtractor):
    """
    Aviation Financial Data - Revenue, EBITDAR, leverage.
    
    Signals: credit_rating, public_financials, market_position
    
    Alternative Sources:
    - SEC Edgar: 10-K, 10-Q, 20-F
    - Bloomberg: financials
    """
    source_name = "aviation_financial"
    coverage = "aerospace"
    signals = ["credit_rating", "public_financials", "market_position", "government_support"]
    ttl_config = TTLConfig.semi_static("Financial data updated weekly")
    
    alternative_sources = [
        DataSource("filing", "sec_edgar", "10-K", priority=1),
        DataSource("api", "bloomberg", "financials", priority=2),
        DataSource("api", "sp_global", "ratings", priority=3),
    ]

    def extract(self) -> ExtractionResult:
        revenue = self._weighted_choice([
            (self._rng.randint(100, 500) * 1_000_000, 0.30),
            (self._rng.randint(500, 2000) * 1_000_000, 0.35),
            (self._rng.randint(2000, 10000) * 1_000_000, 0.25),
            (self._rng.randint(10000, 50000) * 1_000_000, 0.10),
        ])
        
        ebitdar_margin = self._rng.uniform(0.10, 0.30)
        ebitdar = revenue * ebitdar_margin
        
        debt_to_ebitdar = self._weighted_choice([
            (self._rng.uniform(1.0, 3.0), 0.30),
            (self._rng.uniform(3.0, 5.0), 0.40),
            (self._rng.uniform(5.0, 8.0), 0.25),
            (self._rng.uniform(8.0, 15.0), 0.05),
        ])
        
        ratings = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC"]
        rating_idx = self._weighted_choice([
            (2, 0.10), (3, 0.25), (4, 0.35), (5, 0.20), (6, 0.10)
        ])
        
        raw_data = {
            "operator_id": self.kwargs.get("operator_id", self._random_id("OP", 6)),
            "financials": {
                "revenue_usd": revenue,
                "ebitdar_usd": ebitdar,
                "ebitdar_margin_pct": round(ebitdar_margin * 100, 1),
                "net_income_usd": ebitdar * self._rng.uniform(-0.2, 0.5),
                "total_assets_usd": revenue * self._rng.uniform(1.5, 4),
                "is_public": self._rng.random() > 0.40,
            },
            "leverage": {
                "total_debt_usd": ebitdar * debt_to_ebitdar,
                "debt_to_ebitdar": round(debt_to_ebitdar, 2),
                "lease_adjusted_debt_usd": ebitdar * debt_to_ebitdar * 1.3,
                "cash_usd": revenue * self._rng.uniform(0.05, 0.25),
            },
            "credit_rating": {
                "has_rating": self._rng.random() > 0.30,
                "rating": ratings[rating_idx] if self._rng.random() > 0.30 else None,
                "outlook": self._weighted_choice([("Stable", 0.50), ("Positive", 0.20), ("Negative", 0.30)]),
            },
            "market_position": {
                "domestic_market_share_pct": round(self._rng.uniform(1, 40), 1),
                "primary_hub_slot_share_pct": round(self._rng.uniform(5, 60), 1),
            },
            "government_support": {
                "state_owned_pct": self._rng.randint(0, 100) if self._rng.random() < 0.20 else 0,
                "received_bailout": self._rng.random() < 0.15,
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "revenue": revenue,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class RouteRiskExtractor(DataExtractor):
    """
    Route Risk Analysis - Conflict zones, challenging airports, weather exposure.
    
    Signals: conflict_zone_exposure, challenging_airports, high_risk_destinations, weather_exposure
    
    Alternative Sources:
    - OAG: schedules/routes
    - Osprey Flight Solutions: risk_zones
    - Eurocontrol: notams/conflict
    """
    source_name = "route_risk"
    coverage = "aerospace"
    signals = ["conflict_zone_exposure", "challenging_airports", "high_risk_destinations", "weather_exposure"]
    ttl_config = TTLConfig.real_time("Conflict zone data requires hourly updates")
    
    alternative_sources = [
        DataSource("api", "oag", "schedules/routes", priority=1),
        DataSource("api", "osprey_flight_solutions", "risk_zones", priority=2),
        DataSource("api", "eurocontrol", "notams/conflict", priority=3),
        DataSource("api", "jeppesen", "airport/special_procedures", priority=4),
    ]

    def extract(self) -> ExtractionResult:
        conflict_zones = ["Ukraine/Russia", "Middle East", "Horn of Africa", "Myanmar", "Sahel"]
        high_risk_airports = ["Kathmandu", "Tegucigalpa", "Paro", "Funchal", "Gibraltar"]
        
        exposed_conflicts = self._rng.sample(conflict_zones, self._rng.randint(0, 2))
        challenging_destinations = self._rng.sample(high_risk_airports, self._rng.randint(0, 3))
        
        raw_data = {
            "operator_id": self.kwargs.get("operator_id", self._random_id("OP", 6)),
            "conflict_exposure": {
                "active_conflict_zones": exposed_conflicts,
                "overfly_restrictions": len(exposed_conflicts) > 0,
                "rerouting_cost_impact_pct": len(exposed_conflicts) * self._rng.uniform(0.5, 2),
            },
            "airport_risk": {
                "challenging_airports_served": challenging_destinations,
                "special_qualification_required": len(challenging_destinations) > 0,
                "terrain_exposure_score": self._weighted_choice([("Low", 0.50), ("Medium", 0.35), ("High", 0.15)]),
            },
            "destination_risk": {
                "high_risk_countries": self._rng.sample(
                    ["Iran", "Iraq", "Afghanistan", "Yemen", "Libya", "Syria"],
                    self._rng.randint(0, 3)
                ),
                "cat_2_3_countries": self._rng.randint(0, 5),
            },
            "weather_exposure": {
                "hurricane_exposed_routes_pct": round(self._rng.uniform(0, 30), 1),
                "monsoon_exposed_routes_pct": round(self._rng.uniform(0, 40), 1),
                "winter_weather_hub": self._rng.random() > 0.60,
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "conflict_zones": len(exposed_conflicts),
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


