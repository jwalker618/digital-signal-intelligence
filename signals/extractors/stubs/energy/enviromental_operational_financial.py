"""
Energy Stub Extractors - Environmental, Operational, Financial

ENVIRONMENTAL COMPLIANCE signals:
- epa_violation: EPA violations (CAA, CWA, RCRA)
- spill_history: Oil/chemical spill history
- emissions_compliance: Air emissions compliance
- flaring: Flaring intensity from satellite
- methane: Methane emissions
- remediation: Environmental remediation obligations

OPERATIONAL TELEMETRY signals:
- production_consistency: Production volatility
- facility_activity: Satellite-derived activity
- well_integrity: Well integrity indicators
- maintenance_pattern: Turnarounds, maintenance
- operational_efficiency: Production per well, utilization

FINANCIAL STABILITY signals:
- leverage: Debt/equity ratio
- aro_coverage: ARO funding status
- capex_trend: Maintenance vs growth capital
- restructuring: Bankruptcy/restructuring history
"""

from typing import Any, Dict, List, Optional
import random

from ...base import StubExtractor, utcnow


# =============================================================================
# ENVIRONMENTAL COMPLIANCE EXTRACTORS
# =============================================================================

class EPAViolationExtractor(StubExtractor):
    """STUB: Simulates EPA violations lookup."""
    SOURCE_NAME = "epa_violations"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        caa = self._random_int(0, 5)
        cwa = self._random_int(0, 4)
        rcra = self._random_int(0, 3)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "caa_violations_5yr": caa,
                "cwa_violations_5yr": cwa,
                "rcra_violations_5yr": rcra,
                "total_violations": caa + cwa + rcra,
                "ongoing_enforcement": self._random_bool(0.1) if caa + cwa + rcra > 3 else False,
                "total_penalties": self._random_int(0, 2_000_000) if caa + cwa + rcra > 0 else 0,
                "epa_violation_score": max(0, 100 - (caa + cwa + rcra) * 8),
            }
        }
        return self._create_success_result(data)


class SpillHistoryExtractor(StubExtractor):
    """STUB: Simulates NRC and state spill records."""
    SOURCE_NAME = "spill_history"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        spill_count = self._random_int(0, 15)
        major_spills = self._random_int(0, min(2, spill_count))
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "total_spills_5yr": spill_count,
                "major_spills_5yr": major_spills,
                "total_volume_bbls": self._random_int(0, 10_000) if spill_count > 0 else 0,
                "offshore_spills": self._random_int(0, min(3, spill_count)),
                "spill_rate_per_well": self._random_float(0, 0.5),
                "spill_history_score": max(0, 100 - spill_count * 5 - major_spills * 20),
            }
        }
        return self._create_success_result(data)


class EmissionsComplianceExtractor(StubExtractor):
    """STUB: Simulates air emissions compliance."""
    SOURCE_NAME = "emissions_compliance"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        exceedances = self._random_int(0, 8)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "permit_exceedances_3yr": exceedances,
                "air_permit_status": self._random_choice(["CURRENT", "RENEWAL_PENDING", "VIOLATION"]),
                "voc_compliance": self._random_bool(0.85),
                "nox_compliance": self._random_bool(0.9),
                "emissions_trend": self._random_choice(["DECREASING", "STABLE", "INCREASING"]),
                "emissions_compliance_score": max(30, 100 - exceedances * 8),
            }
        }
        return self._create_success_result(data)


class FlaringIntensityExtractor(StubExtractor):
    """STUB: Simulates satellite-derived flaring data."""
    SOURCE_NAME = "flaring_satellite"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        flaring_intensity = self._random_float(0, 15)  # MCF per BOE
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "flaring_intensity": round(flaring_intensity, 2),
                "vs_basin_average": self._random_choice(["BELOW", "AVERAGE", "ABOVE"]),
                "flare_count": self._random_int(5, 100),
                "flaring_trend": self._random_choice(["DECREASING", "STABLE", "INCREASING"]),
                "zero_flare_commitment": self._random_bool(0.3),
                "flaring_score": max(20, 100 - flaring_intensity * 5),
            }
        }
        return self._create_success_result(data)


class MethaneEmissionsExtractor(StubExtractor):
    """STUB: Simulates methane emissions monitoring."""
    SOURCE_NAME = "methane_monitoring"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        intensity = self._random_float(0.5, 3.0)  # % of production
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "methane_intensity_pct": round(intensity, 2),
                "vs_basin_average": self._random_choice(["BELOW", "AVERAGE", "ABOVE"]),
                "ldar_program": self._random_bool(0.7),
                "ogmp_participant": self._random_bool(0.3),
                "aerial_survey_participation": self._random_bool(0.4),
                "methane_score": max(20, 100 - intensity * 25),
            }
        }
        return self._create_success_result(data)


class RemediationExtractor(StubExtractor):
    """STUB: Simulates environmental remediation obligations."""
    SOURCE_NAME = "remediation_obligations"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        sites = self._random_int(0, 10)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "active_remediation_sites": sites,
                "superfund_sites": self._random_int(0, 1),
                "estimated_liability": self._random_int(0, 50_000_000) if sites > 0 else 0,
                "adequately_reserved": self._random_bool(0.8) if sites > 0 else None,
                "remediation_score": max(30, 100 - sites * 7),
            }
        }
        return self._create_success_result(data)


# =============================================================================
# OPERATIONAL TELEMETRY EXTRACTORS
# =============================================================================

class ProductionConsistencyExtractor(StubExtractor):
    """STUB: Simulates production consistency analysis."""
    SOURCE_NAME = "production_telemetry"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        volatility = self._random_float(5, 30)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "production_volatility_pct": round(volatility, 1),
                "decline_rate": self._random_float(10, 40),
                "production_trend": self._random_choice(["GROWING", "STABLE", "DECLINING"]),
                "guidance_accuracy": self._random_float(85, 100),
                "production_consistency_score": max(30, 100 - volatility * 2),
            }
        }
        return self._create_success_result(data)


class FacilityActivityExtractor(StubExtractor):
    """STUB: Simulates satellite-derived facility activity."""
    SOURCE_NAME = "satellite_activity"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        activity_score = self._random_float(50, 100)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "facility_activity_index": round(activity_score, 1),
                "inactive_facilities_pct": self._random_float(0, 20),
                "new_construction_detected": self._random_bool(0.3),
                "activity_trend": self._random_choice(["INCREASING", "STABLE", "DECREASING"]),
                "facility_activity_score": activity_score,
            }
        }
        return self._create_success_result(data)


class WellIntegrityExtractor(StubExtractor):
    """STUB: Simulates well integrity indicators."""
    SOURCE_NAME = "well_integrity"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        shut_in_pct = self._random_float(5, 30)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "shut_in_percentage": round(shut_in_pct, 1),
                "workover_rate": self._random_float(5, 20),
                "pa_backlog": self._random_int(0, 50),
                "idle_well_count": self._random_int(0, 100),
                "mechanical_integrity_issues": self._random_int(0, 10),
                "well_integrity_score": max(30, 100 - shut_in_pct * 2),
            }
        }
        return self._create_success_result(data)


class MaintenancePatternExtractor(StubExtractor):
    """STUB: Simulates maintenance pattern analysis."""
    SOURCE_NAME = "maintenance_patterns"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "planned_turnarounds_3yr": self._random_int(1, 5),
                "unplanned_outages_3yr": self._random_int(0, 8),
                "average_turnaround_duration_days": self._random_int(14, 45),
                "maintenance_capex_trend": self._random_choice(["INCREASING", "STABLE", "DECREASING"]),
                "maintenance_pattern_score": self._random_float(50, 90),
            }
        }
        return self._create_success_result(data)


class OperationalEfficiencyExtractor(StubExtractor):
    """STUB: Simulates operational efficiency metrics."""
    SOURCE_NAME = "operational_efficiency"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "production_per_well_boed": self._random_int(50, 500),
                "vs_basin_average": self._random_choice(["ABOVE", "AVERAGE", "BELOW"]),
                "lifting_cost_per_boe": self._random_float(5, 25),
                "utilization_rate": self._random_float(70, 95),
                "operational_efficiency_score": self._random_float(50, 90),
            }
        }
        return self._create_success_result(data)


# =============================================================================
# FINANCIAL STABILITY EXTRACTORS
# =============================================================================

class LeverageExtractor(StubExtractor):
    """STUB: Simulates leverage analysis."""
    SOURCE_NAME = "leverage_analysis"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        debt_equity = self._random_float(0.2, 3.0)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "debt_to_equity": round(debt_equity, 2),
                "net_debt_to_ebitda": self._random_float(0.5, 5.0),
                "vs_peer_average": self._random_choice(["BETTER", "AVERAGE", "WORSE"]),
                "leverage_trend": self._random_choice(["DELEVERAGING", "STABLE", "INCREASING"]),
                "leverage_score": max(20, 100 - debt_equity * 25),
            }
        }
        return self._create_success_result(data)


class AROCoverageExtractor(StubExtractor):
    """STUB: Simulates ARO coverage analysis."""
    SOURCE_NAME = "aro_coverage"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        coverage_pct = self._random_float(50, 120)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "aro_liability": self._random_int(10_000_000, 500_000_000),
                "aro_funding_pct": round(coverage_pct, 1),
                "bonding_adequate": coverage_pct >= 100,
                "orphan_well_risk": self._random_bool(0.15),
                "aro_coverage_score": min(100, coverage_pct),
            }
        }
        return self._create_success_result(data)


class CapexTrendExtractor(StubExtractor):
    """STUB: Simulates capex trend analysis."""
    SOURCE_NAME = "capex_trends"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        maintenance_pct = self._random_float(20, 60)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "total_capex": self._random_int(50_000_000, 2_000_000_000),
                "maintenance_capex_pct": round(maintenance_pct, 1),
                "growth_capex_pct": round(100 - maintenance_pct, 1),
                "capex_trend_3yr": self._random_choice(["INCREASING", "STABLE", "DECREASING"]),
                "capex_discipline": self._random_choice(["HIGH", "MODERATE", "LOW"]),
                "capex_trend_score": self._random_float(50, 90),
            }
        }
        return self._create_success_result(data)


class RestructuringExtractor(StubExtractor):
    """STUB: Simulates bankruptcy/restructuring history."""
    SOURCE_NAME = "restructuring_history"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_MONTHLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_bankruptcy = self._random_bool(0.1)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "bankruptcy_10yr": has_bankruptcy,
                "years_since_emergence": self._random_float(1, 8) if has_bankruptcy else None,
                "debt_restructuring": self._random_bool(0.2),
                "distressed_exchange": self._random_bool(0.1),
                "restructuring_score": 50 if has_bankruptcy else 100,
            }
        }
        return self._create_success_result(data)
