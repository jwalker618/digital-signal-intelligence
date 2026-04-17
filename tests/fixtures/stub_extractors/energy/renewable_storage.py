"""
Energy Stub Extractors - Renewable, Storage & Shared Renewable Signals

Phase 5: New domain-specific signals for renewable/transition energy configurations.

SHARED RENEWABLE signals (used across offshore wind, onshore renewable, storage):
- technology_maturity: Technology platform maturity assessment
- epc_contractor_quality: EPC contractor track record and tier
- warranty_coverage: OEM warranty coverage assessment
- capacity_factor: Actual vs nameplate capacity ratio
- natcat_exposure: NatCat zone exposure (hail, wind, wildfire)
- grid_interconnection: Grid interconnection quality and reliability
- ppa_quality: PPA/CFD contract quality and counterparty
- degradation_rate: Performance degradation vs manufacturer curve
- commissioning_defects: Defect density during commissioning
- construction_phase: Project lifecycle phase (categorical)
- epc_track_record: EPC contractor historical delivery
- supply_chain_quality: Component supply chain tier quality

OFFSHORE WIND signals:
- installation_vessel_quality: WTI vessel quality and track record
- foundation_type: Foundation type (categorical)
- turbine_platform_generation: Turbine platform maturity
- cable_route_risk: Export cable route complexity
- marine_weather_exposure: Weather window analysis
- crew_transfer_safety: CTV/SOV safety record
- offtake_contract_quality: CFD/PPA/OREC contract quality

ONSHORE RENEWABLE signals:
- hail_exposure: Hail map overlay for solar installations
- panel_technology_vintage: Panel/turbine model vintage and defect history
- inverter_reliability: Inverter manufacturer reliability data
- curtailment_rate: Historical grid curtailment rate
- portfolio_geographic_spread: Geographic diversification across NatCat zones

STORAGE signals:
- battery_chemistry: Battery chemistry type (categorical)
- thermal_management_system: Active/passive cooling, thermal monitoring
- fire_suppression_capability: Suppression system type and effectiveness
- bms_sophistication: BMS capability and monitoring granularity
- hydrogen_storage_pressure: Storage pressure class
- safety_standard_compliance: NFPA 855, UL 9540A, IEC 62619 compliance
- cell_format_maturity: Cell format and manufacturer track record
- electrolyser_technology: PEM vs alkaline vs SOEC
"""

from typing import Any, Dict
from ...base import StubExtractor, utcnow


# =============================================================================
# SHARED RENEWABLE EXTRACTORS
# =============================================================================

class TechnologyMaturityExtractor(StubExtractor):
    """STUB: Technology platform maturity assessment."""
    SOURCE_NAME = "technology_maturity"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY

    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "technology_generation": self._random_choice(["MATURE", "PROVEN", "ESTABLISHED", "EMERGING", "FIRST_OF_KIND"]),
                "years_in_production": self._random_int(0, 30),
                "global_installed_base_gw": self._random_float(0, 500),
                "known_serial_defects": self._random_int(0, 3),
                "technology_maturity_score": self._random_float(15, 95),
            }
        }
        return self._create_success_result(data)


class EPCContractorQualityExtractor(StubExtractor):
    """STUB: EPC contractor track record and tier classification."""
    SOURCE_NAME = "epc_contractor"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY

    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "epc_contractor_name": self._random_choice(["Bechtel", "Fluor", "Siemens Gamesa", "Vestas", "JinkoSolar", "Unknown"]),
                "contractor_tier": self._random_choice([1, 2, 3]),
                "projects_completed": self._random_int(0, 200),
                "on_time_delivery_pct": self._random_float(60, 100),
                "defect_rate": self._random_float(0.5, 10),
                "epc_contractor_quality_score": self._random_float(20, 95),
            }
        }
        return self._create_success_result(data)


class WarrantyCoverageExtractor(StubExtractor):
    """STUB: OEM warranty coverage assessment."""
    SOURCE_NAME = "warranty_coverage"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_MONTHLY

    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "warranty_years_remaining": self._random_int(0, 25),
                "oem_financial_strength": self._random_choice(["STRONG", "ADEQUATE", "WEAK", "UNKNOWN"]),
                "warranty_scope": self._random_choice(["FULL", "LIMITED", "PARTS_ONLY", "NONE"]),
                "active_warranty_claims": self._random_int(0, 10),
                "warranty_coverage_score": self._random_float(25, 95),
            }
        }
        return self._create_success_result(data)


class CapacityFactorExtractor(StubExtractor):
    """STUB: Actual vs nameplate capacity ratio."""
    SOURCE_NAME = "capacity_factor"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY

    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        cf = self._random_float(15, 55)
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "capacity_factor_pct": round(cf, 1),
                "nameplate_capacity_mw": self._random_int(10, 2000),
                "availability_pct": self._random_float(85, 99),
                "capacity_factor_score": self._random_float(25, 95),
            }
        }
        return self._create_success_result(data)


class NatCatExposureExtractor(StubExtractor):
    """STUB: NatCat zone exposure (hail, wind, wildfire)."""
    SOURCE_NAME = "natcat_exposure"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_MONTHLY

    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "primary_natcat_peril": self._random_choice(["HAIL", "TORNADO", "HURRICANE", "WILDFIRE", "FLOOD", "NONE"]),
                "return_period_years": self._random_int(5, 100),
                "historical_events_10yr": self._random_int(0, 8),
                "natcat_zone_classification": self._random_choice(["LOW", "MODERATE", "HIGH", "EXTREME"]),
                "natcat_exposure_score": self._random_float(15, 90),
            }
        }
        return self._create_success_result(data)


class GridInterconnectionExtractor(StubExtractor):
    """STUB: Grid interconnection quality and reliability."""
    SOURCE_NAME = "grid_interconnection"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY

    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "grid_operator": self._random_choice(["ERCOT", "PJM", "CAISO", "MISO", "SPP", "NYISO", "OTHER"]),
                "interconnection_voltage_kv": self._random_choice([34.5, 69, 115, 138, 230, 345]),
                "curtailment_risk": self._random_choice(["LOW", "MODERATE", "HIGH"]),
                "interconnection_delay_months": self._random_int(0, 24),
                "grid_interconnection_score": self._random_float(30, 95),
            }
        }
        return self._create_success_result(data)


class PPAQualityExtractor(StubExtractor):
    """STUB: PPA/CFD contract quality and counterparty."""
    SOURCE_NAME = "ppa_quality"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_MONTHLY

    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "ppa_type": self._random_choice(["FIXED_PRICE", "CFD", "OREC", "MERCHANT", "HYBRID"]),
                "counterparty_credit": self._random_choice(["AAA", "AA", "A", "BBB", "BB", "UNRATED"]),
                "tenor_years_remaining": self._random_int(0, 25),
                "price_escalation": self._random_bool(0.6),
                "ppa_quality_score": self._random_float(20, 95),
            }
        }
        return self._create_success_result(data)


class DegradationRateExtractor(StubExtractor):
    """STUB: Performance degradation vs manufacturer curve."""
    SOURCE_NAME = "degradation_rate"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY

    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "annual_degradation_pct": self._random_float(0.2, 3.0),
                "manufacturer_warranted_pct": self._random_float(0.3, 0.8),
                "degradation_ratio": self._random_float(0.5, 3.0),
                "years_operating": self._random_int(0, 20),
                "degradation_rate_score": self._random_float(25, 95),
            }
        }
        return self._create_success_result(data)


class CommissioningDefectsExtractor(StubExtractor):
    """STUB: Defect density during commissioning phase."""
    SOURCE_NAME = "commissioning_defects"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY

    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "defects_per_mw": self._random_float(0.1, 5.0),
                "critical_defects": self._random_int(0, 10),
                "defect_resolution_days_avg": self._random_int(5, 90),
                "commissioning_defects_score": self._random_float(20, 95),
            }
        }
        return self._create_success_result(data)


class ConstructionPhaseExtractor(StubExtractor):
    """STUB: Project lifecycle phase (categorical)."""
    SOURCE_NAME = "construction_phase"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY

    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "construction_phase": self._random_choice(["PRE_CONSTRUCTION", "CONSTRUCTION", "COMMISSIONING", "EARLY_OPERATION", "MATURE_OPERATION"]),
            }
        }
        return self._create_success_result(data)


class EPCTrackRecordExtractor(StubExtractor):
    """STUB: EPC contractor historical project delivery."""
    SOURCE_NAME = "epc_track_record"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_MONTHLY

    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "total_projects_delivered": self._random_int(0, 100),
                "technology_specific_projects": self._random_int(0, 50),
                "avg_schedule_variance_pct": self._random_float(-20, 30),
                "liquidated_damages_events": self._random_int(0, 5),
                "epc_track_record_score": self._random_float(20, 95),
            }
        }
        return self._create_success_result(data)


class SupplyChainQualityExtractor(StubExtractor):
    """STUB: Component supply chain tier quality."""
    SOURCE_NAME = "supply_chain_quality"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_MONTHLY

    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "tier1_component_pct": self._random_float(30, 100),
                "single_source_risk": self._random_bool(0.3),
                "lead_time_weeks": self._random_int(4, 52),
                "supply_chain_quality_score": self._random_float(25, 90),
            }
        }
        return self._create_success_result(data)


# =============================================================================
# OFFSHORE WIND EXTRACTORS
# =============================================================================

class InstallationVesselQualityExtractor(StubExtractor):
    """STUB: WTI vessel quality and track record."""
    SOURCE_NAME = "installation_vessel"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY

    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "vessel_name": self._random_choice(["Seajacks Scylla", "Voltaire", "DEME Orion", "Fred Olsen Brave Tern", "Unknown"]),
                "vessel_type": self._random_choice(["JACK_UP", "HEAVY_LIFT", "CABLE_LAY", "SERVICE"]),
                "vessel_age_years": self._random_int(1, 20),
                "projects_completed": self._random_int(0, 30),
                "incident_history": self._random_int(0, 3),
                "installation_vessel_quality_score": self._random_float(25, 95),
            }
        }
        return self._create_success_result(data)


class FoundationTypeExtractor(StubExtractor):
    """STUB: Foundation type (categorical)."""
    SOURCE_NAME = "foundation_type"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_MONTHLY

    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "foundation_type": self._random_choice(["MONOPILE", "JACKET", "GRAVITY_BASE", "FLOATING_SPAR", "FLOATING_SEMI", "FLOATING_TLP"]),
            }
        }
        return self._create_success_result(data)


class TurbinePlatformGenerationExtractor(StubExtractor):
    """STUB: Turbine platform maturity assessment."""
    SOURCE_NAME = "turbine_platform"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_MONTHLY

    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "turbine_oem": self._random_choice(["Vestas", "Siemens Gamesa", "GE Haliade", "MingYang", "Goldwind"]),
                "nameplate_capacity_mw": self._random_choice([8, 10, 12, 14, 15, 17]),
                "platform_generation": self._random_choice(["GEN1", "GEN2", "GEN3", "NEXT_GEN"]),
                "global_installed_count": self._random_int(0, 5000),
                "turbine_platform_generation_score": self._random_float(20, 95),
            }
        }
        return self._create_success_result(data)


class CableRouteRiskExtractor(StubExtractor):
    """STUB: Export cable route complexity."""
    SOURCE_NAME = "cable_route"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_MONTHLY

    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "cable_length_km": self._random_int(20, 200),
                "crossings_count": self._random_int(0, 10),
                "burial_depth_target_m": self._random_float(1.0, 3.0),
                "seabed_condition": self._random_choice(["SAND", "CLAY", "ROCK", "MIXED"]),
                "cable_route_risk_score": self._random_float(20, 85),
            }
        }
        return self._create_success_result(data)


class MarineWeatherExposureExtractor(StubExtractor):
    """STUB: Weather window analysis for installation site."""
    SOURCE_NAME = "marine_weather"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_MONTHLY

    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "region": self._random_choice(["NORTH_SEA", "BALTIC", "US_ATLANTIC", "US_GULF", "APAC"]),
                "weather_window_days_yr": self._random_int(80, 250),
                "max_significant_wave_height_m": self._random_float(1.5, 6.0),
                "hurricane_exposure": self._random_bool(0.3),
                "marine_weather_exposure_score": self._random_float(20, 90),
            }
        }
        return self._create_success_result(data)


class CrewTransferSafetyExtractor(StubExtractor):
    """STUB: CTV/SOV safety record."""
    SOURCE_NAME = "crew_transfer"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY

    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "transfer_method": self._random_choice(["CTV", "SOV", "HELICOPTER", "WALK_TO_WORK"]),
                "transfers_per_year": self._random_int(100, 5000),
                "incidents_3yr": self._random_int(0, 5),
                "lti_3yr": self._random_int(0, 2),
                "crew_transfer_safety_score": self._random_float(30, 95),
            }
        }
        return self._create_success_result(data)


class OfftakeContractQualityExtractor(StubExtractor):
    """STUB: CFD/PPA/OREC contract quality and counterparty."""
    SOURCE_NAME = "offtake_contract"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_MONTHLY

    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "contract_type": self._random_choice(["CFD", "PPA", "OREC", "ROC", "MERCHANT"]),
                "counterparty_type": self._random_choice(["SOVEREIGN", "UTILITY", "CORPORATE", "UNCONTRACTED"]),
                "tenor_years": self._random_int(0, 25),
                "price_certainty": self._random_choice(["FIXED", "INDEXED", "MERCHANT"]),
                "offtake_contract_quality_score": self._random_float(20, 95),
            }
        }
        return self._create_success_result(data)


# =============================================================================
# ONSHORE RENEWABLE EXTRACTORS
# =============================================================================

class HailExposureExtractor(StubExtractor):
    """STUB: Hail map overlay for solar installations."""
    SOURCE_NAME = "hail_exposure"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_MONTHLY

    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "hail_zone": self._random_choice(["EXTREME", "HIGH", "MODERATE", "LOW", "MINIMAL"]),
                "hail_events_10yr": self._random_int(0, 20),
                "max_hailstone_diameter_in": self._random_float(0, 4.0),
                "hail_claims_3yr": self._random_int(0, 5),
                "hail_exposure_score": self._random_float(15, 90),
            }
        }
        return self._create_success_result(data)


class PanelTechnologyVintageExtractor(StubExtractor):
    """STUB: Panel/turbine model vintage and defect history."""
    SOURCE_NAME = "panel_vintage"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_MONTHLY

    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "panel_type": self._random_choice(["MONO_PERC", "BIFACIAL", "TOPCON", "HJT", "THIN_FILM"]),
                "manufacturer": self._random_choice(["JinkoSolar", "LONGi", "Trina", "Canadian Solar", "First Solar"]),
                "manufacture_year": self._random_int(2015, 2025),
                "known_defect_advisory": self._random_bool(0.15),
                "panel_technology_vintage_score": self._random_float(20, 90),
            }
        }
        return self._create_success_result(data)


class InverterReliabilityExtractor(StubExtractor):
    """STUB: Inverter manufacturer reliability data."""
    SOURCE_NAME = "inverter_reliability"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY

    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "inverter_oem": self._random_choice(["SMA", "Sungrow", "Huawei", "Power Electronics", "TMEIC"]),
                "failure_rate_pct": self._random_float(0.5, 8.0),
                "mtbf_hours": self._random_int(20000, 200000),
                "replacement_availability": self._random_choice(["IMMEDIATE", "WEEKS", "MONTHS", "DISCONTINUED"]),
                "inverter_reliability_score": self._random_float(20, 95),
            }
        }
        return self._create_success_result(data)


class CurtailmentRateExtractor(StubExtractor):
    """STUB: Historical grid curtailment rate."""
    SOURCE_NAME = "curtailment_rate"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY

    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "annual_curtailment_pct": self._random_float(0, 25),
                "curtailment_trend": self._random_choice(["DECREASING", "STABLE", "INCREASING"]),
                "grid_operator": self._random_choice(["ERCOT", "CAISO", "MISO", "SPP", "PJM", "OTHER"]),
                "economic_curtailment_pct": self._random_float(0, 15),
                "curtailment_rate_score": self._random_float(20, 95),
            }
        }
        return self._create_success_result(data)


class PortfolioGeographicSpreadExtractor(StubExtractor):
    """STUB: Geographic diversification across NatCat zones."""
    SOURCE_NAME = "geographic_spread"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_MONTHLY

    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "state_count": self._random_int(1, 30),
                "natcat_zone_count": self._random_int(1, 10),
                "hhi_concentration_index": self._random_float(500, 10000),
                "max_single_state_pct": self._random_float(10, 100),
                "portfolio_geographic_spread_score": self._random_float(15, 95),
            }
        }
        return self._create_success_result(data)


# =============================================================================
# STORAGE EXTRACTORS
# =============================================================================

class BatteryChemistryExtractor(StubExtractor):
    """STUB: Battery chemistry type (categorical)."""
    SOURCE_NAME = "battery_chemistry"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_MONTHLY

    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "battery_chemistry": self._random_choice(["LFP", "NMC", "NCA", "SODIUM_ION", "SOLID_STATE"]),
            }
        }
        return self._create_success_result(data)


class ThermalManagementSystemExtractor(StubExtractor):
    """STUB: Active/passive cooling, thermal monitoring."""
    SOURCE_NAME = "thermal_management"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY

    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "cooling_type": self._random_choice(["ACTIVE_LIQUID", "ACTIVE_AIR", "PASSIVE", "HYBRID"]),
                "air_gapped_modules": self._random_bool(0.5),
                "thermal_monitoring_granularity": self._random_choice(["CELL_LEVEL", "MODULE_LEVEL", "RACK_LEVEL", "CONTAINER_LEVEL"]),
                "thermal_events_history": self._random_int(0, 3),
                "thermal_management_system_score": self._random_float(15, 95),
            }
        }
        return self._create_success_result(data)


class FireSuppressionCapabilityExtractor(StubExtractor):
    """STUB: Suppression system type and effectiveness."""
    SOURCE_NAME = "fire_suppression"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY

    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "suppression_type": self._random_choice(["AEROSOL", "WATER_MIST", "INERT_GAS", "CLEAN_AGENT", "SPRINKLER", "NONE"]),
                "detection_type": self._random_choice(["SMOKE", "THERMAL", "GAS", "MULTI_SENSOR"]),
                "response_time_seconds": self._random_int(5, 120),
                "tested_to_ul9540a": self._random_bool(0.6),
                "fire_suppression_capability_score": self._random_float(20, 95),
            }
        }
        return self._create_success_result(data)


class BMSSophisticationExtractor(StubExtractor):
    """STUB: BMS capability and monitoring granularity."""
    SOURCE_NAME = "bms_sophistication"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY

    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "monitoring_level": self._random_choice(["CELL", "MODULE", "RACK", "STRING"]),
                "predictive_analytics": self._random_bool(0.5),
                "automatic_isolation": self._random_bool(0.7),
                "soc_soh_accuracy_pct": self._random_float(90, 99.9),
                "bms_sophistication_score": self._random_float(25, 95),
            }
        }
        return self._create_success_result(data)


class HydrogenStoragePressureExtractor(StubExtractor):
    """STUB: Storage pressure class for hydrogen."""
    SOURCE_NAME = "hydrogen_storage"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_MONTHLY

    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "storage_pressure_bar": self._random_choice([30, 200, 350, 700]),
                "storage_type": self._random_choice(["COMPRESSED", "LIQUID", "METAL_HYDRIDE", "PIPELINE"]),
                "storage_capacity_kg": self._random_int(100, 100000),
                "pressure_vessel_certification": self._random_bool(0.8),
                "hydrogen_storage_pressure_score": self._random_float(15, 90),
            }
        }
        return self._create_success_result(data)


class SafetyStandardComplianceExtractor(StubExtractor):
    """STUB: NFPA 855, UL 9540A, IEC 62619 compliance."""
    SOURCE_NAME = "safety_standards"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY

    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "nfpa_855_compliant": self._random_bool(0.7),
                "ul_9540a_tested": self._random_bool(0.6),
                "iec_62619_certified": self._random_bool(0.6),
                "fire_code_compliant": self._random_bool(0.8),
                "safety_standard_compliance_score": self._random_float(25, 95),
            }
        }
        return self._create_success_result(data)


class CellFormatMaturityExtractor(StubExtractor):
    """STUB: Cell format and manufacturer track record."""
    SOURCE_NAME = "cell_format"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_MONTHLY

    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "cell_format": self._random_choice(["PRISMATIC", "POUCH", "CYLINDRICAL"]),
                "cell_manufacturer": self._random_choice(["CATL", "BYD", "LG", "Samsung SDI", "EVE", "Gotion"]),
                "manufacturer_gwh_deployed": self._random_int(1, 500),
                "field_failure_rate_ppm": self._random_int(1, 100),
                "cell_format_maturity_score": self._random_float(25, 95),
            }
        }
        return self._create_success_result(data)


class ElectrolyserTechnologyExtractor(StubExtractor):
    """STUB: PEM vs alkaline vs SOEC electrolyser type."""
    SOURCE_NAME = "electrolyser_technology"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_MONTHLY

    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "electrolyser_type": self._random_choice(["PEM", "ALKALINE", "SOEC", "AEM"]),
                "oem": self._random_choice(["ITM Power", "Nel Hydrogen", "Siemens Energy", "Plug Power", "Unknown"]),
                "capacity_mw": self._random_int(1, 100),
                "technology_readiness_level": self._random_int(5, 9),
                "electrolyser_technology_score": self._random_float(15, 90),
            }
        }
        return self._create_success_result(data)
