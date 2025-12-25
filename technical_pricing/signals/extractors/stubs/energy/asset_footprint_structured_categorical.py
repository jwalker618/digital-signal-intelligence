"""
Energy Stub Extractors - Asset, Footprint, Structured, Categorical

ASSET PORTFOLIO signals:
- asset_age: Weighted average asset age
- concentration: Geographic/asset concentration
- complexity: Technology/complexity profile
- decommissioning: Decommissioning liability status
- permit_status: Operating permit compliance

CORPORATE FOOTPRINT signals:
- safety_communication: Safety culture communication
- esg_reporting: ESG/sustainability reporting
- technical_hiring: HSE/engineering hiring
- industry_presence: Conference presence
- disclosure_quality: Transparency quality
- hse_leadership: HSE leadership visibility

STRUCTURED DATA signals:
- esg_rating: Third-party ESG ratings
- benchmark: Industry benchmark data

CATEGORICAL signals:
- operator_type: Supermajor, major, independent, etc.
- operation_segment: Upstream, midstream, downstream
- geographic_focus: Geographic focus
"""

from typing import Any, Dict, List, Optional
import random

from ...base import StubExtractor, utcnow


# =============================================================================
# ASSET PORTFOLIO EXTRACTORS
# =============================================================================

class AssetAgeExtractor(StubExtractor):
    """STUB: Simulates asset age profile analysis."""
    SOURCE_NAME = "asset_age_profile"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        avg_age = self._random_float(5, 35)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "weighted_avg_age_years": round(avg_age, 1),
                "pct_over_20_years": self._random_float(10, 60),
                "pct_under_5_years": self._random_float(5, 40),
                "vs_peer_average": self._random_choice(["YOUNGER", "AVERAGE", "OLDER"]),
                "asset_age_score": max(30, 100 - avg_age * 2),
            }
        }
        return self._create_success_result(data)


class ConcentrationExtractor(StubExtractor):
    """STUB: Simulates geographic/asset concentration."""
    SOURCE_NAME = "concentration_analysis"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        top_asset_pct = self._random_float(15, 70)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "top_asset_pct_production": round(top_asset_pct, 1),
                "top_3_assets_pct": self._random_float(top_asset_pct, min(100, top_asset_pct + 40)),
                "basin_count": self._random_int(1, 10),
                "single_point_of_failure_risk": top_asset_pct > 50,
                "concentration_score": max(30, 100 - top_asset_pct),
            }
        }
        return self._create_success_result(data)


class TechnologyProfileExtractor(StubExtractor):
    """STUB: Simulates technology/complexity profile."""
    SOURCE_NAME = "technology_profile"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        complexity = self._random_choice(["LOW", "MODERATE", "HIGH", "VERY_HIGH"])
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "operational_complexity": complexity,
                "deepwater_operations": self._random_bool(0.2),
                "high_pressure_high_temp": self._random_bool(0.15),
                "sour_gas_operations": self._random_bool(0.25),
                "arctic_operations": self._random_bool(0.05),
                "technology_profile_score": {"LOW": 90, "MODERATE": 70, "HIGH": 50, "VERY_HIGH": 35}.get(complexity, 60),
            }
        }
        return self._create_success_result(data)


class DecommissioningExtractor(StubExtractor):
    """STUB: Simulates decommissioning liability status."""
    SOURCE_NAME = "decommissioning_status"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        liability = self._random_int(5_000_000, 500_000_000)
        funding_pct = self._random_float(40, 110)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "decommissioning_liability": liability,
                "funding_percentage": round(funding_pct, 1),
                "active_decommissioning_projects": self._random_int(0, 10),
                "backlog_wells": self._random_int(0, 200),
                "decommissioning_score": min(100, funding_pct),
            }
        }
        return self._create_success_result(data)


class PermitStatusExtractor(StubExtractor):
    """STUB: Simulates operating permit status."""
    SOURCE_NAME = "permit_status"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        violations = self._random_int(0, 5)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "active_permits": self._random_int(10, 500),
                "permit_violations_3yr": violations,
                "permits_under_review": self._random_int(0, 20),
                "permit_denial_3yr": self._random_bool(0.1),
                "permit_status_score": max(50, 100 - violations * 10),
            }
        }
        return self._create_success_result(data)


# =============================================================================
# CORPORATE FOOTPRINT EXTRACTORS
# =============================================================================

class SafetyCommunicationExtractor(StubExtractor):
    """STUB: Simulates safety culture communication."""
    SOURCE_NAME = "safety_communication"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "safety_page_present": self._random_bool(0.7),
                "safety_metrics_disclosed": self._random_bool(0.5),
                "safety_culture_messaging": self._random_choice(["STRONG", "MODERATE", "WEAK"]),
                "executive_safety_messaging": self._random_bool(0.6),
                "safety_communication_score": self._random_float(40, 90),
            }
        }
        return self._create_success_result(data)


class EnergyESGReportingExtractor(StubExtractor):
    """STUB: Simulates ESG/sustainability reporting."""
    SOURCE_NAME = "esg_reporting"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_report = self._random_bool(0.6)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "sustainability_report": has_report,
                "tcfd_aligned": self._random_bool(0.4) if has_report else False,
                "sasb_aligned": self._random_bool(0.5) if has_report else False,
                "net_zero_commitment": self._random_bool(0.3),
                "emissions_targets": self._random_bool(0.5) if has_report else False,
                "esg_reporting_score": 80 if has_report else 35,
            }
        }
        return self._create_success_result(data)


class TechnicalHiringExtractor(StubExtractor):
    """STUB: Simulates HSE/engineering hiring signals."""
    SOURCE_NAME = "technical_hiring"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "hse_positions_posted": self._random_int(0, 15),
                "engineering_positions_posted": self._random_int(0, 30),
                "hse_leadership_hiring": self._random_bool(0.2),
                "technical_team_growth": self._random_choice(["GROWING", "STABLE", "SHRINKING"]),
                "technical_hiring_score": self._random_float(40, 85),
            }
        }
        return self._create_success_result(data)


class IndustryPresenceExtractor(StubExtractor):
    """STUB: Simulates industry conference presence."""
    SOURCE_NAME = "industry_presence"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "conference_presentations_12m": self._random_int(0, 15),
                "major_conference_presence": self._random_bool(0.5),
                "technical_papers_published": self._random_int(0, 10),
                "industry_committee_roles": self._random_int(0, 5),
                "industry_presence_score": self._random_float(30, 85),
            }
        }
        return self._create_success_result(data)


class DisclosureQualityExtractor(StubExtractor):
    """STUB: Simulates disclosure quality analysis."""
    SOURCE_NAME = "disclosure_quality"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "disclosure_score": self._random_float(40, 95),
                "financial_transparency": self._random_choice(["HIGH", "MODERATE", "LOW"]),
                "operational_data_disclosed": self._random_bool(0.6),
                "reserves_disclosure_quality": self._random_choice(["COMPREHENSIVE", "STANDARD", "MINIMAL"]),
                "investor_communication_quality": self._random_choice(["EXCELLENT", "GOOD", "FAIR", "POOR"]),
            }
        }
        return self._create_success_result(data)


class HSELeadershipExtractor(StubExtractor):
    """STUB: Simulates HSE leadership visibility."""
    SOURCE_NAME = "hse_leadership"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_cso = self._random_bool(0.5)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "dedicated_cso_csho": has_cso,
                "hse_reports_to_board": self._random_bool(0.6),
                "hse_executive_visibility": self._random_choice(["HIGH", "MODERATE", "LOW"]),
                "hse_certifications": self._random_bool(0.7),
                "hse_leadership_score": 85 if has_cso else 50,
            }
        }
        return self._create_success_result(data)


# =============================================================================
# STRUCTURED DATA EXTRACTORS
# =============================================================================

class EnergyESGRatingExtractor(StubExtractor):
    """STUB: Simulates energy-specific ESG ratings."""
    SOURCE_NAME = "energy_esg_rating"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_rating = self._random_bool(0.5)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "has_esg_rating": has_rating,
                "msci_rating": self._random_choice(["AAA", "AA", "A", "BBB", "BB", "B", "CCC"]) if has_rating else None,
                "sustainalytics_risk": self._random_choice(["LOW", "MEDIUM", "HIGH", "SEVERE"]) if has_rating else None,
                "cdp_climate_score": self._random_choice(["A", "A-", "B", "B-", "C", "D", "F"]) if has_rating else None,
                "esg_rating_score": self._random_float(30, 85) if has_rating else 50,
            }
        }
        return self._create_success_result(data)


class BenchmarkExtractor(StubExtractor):
    """STUB: Simulates industry benchmark data."""
    SOURCE_NAME = "industry_benchmarks"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "safety_percentile": self._random_int(10, 95),
                "environmental_percentile": self._random_int(10, 95),
                "operational_percentile": self._random_int(10, 95),
                "overall_percentile": self._random_int(15, 90),
                "benchmark_score": self._random_float(40, 90),
            }
        }
        return self._create_success_result(data)


# =============================================================================
# CATEGORICAL EXTRACTORS
# =============================================================================

class OperatorTypeExtractor(StubExtractor):
    """STUB: Simulates operator type classification."""
    SOURCE_NAME = "operator_classification"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    TYPES = [
        "SUPERMAJOR", "MAJOR_INTEGRATED", "LARGE_INDEPENDENT", "MID_INDEPENDENT",
        "SMALL_INDEPENDENT", "NATIONAL_OIL", "MIDSTREAM_MAJOR", "DOWNSTREAM_MAJOR",
        "PRIVATE_EQUITY", "UNKNOWN"
    ]
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        op_type = self._random_choice(
            self.TYPES,
            weights=[0.05, 0.10, 0.15, 0.20, 0.15, 0.05, 0.08, 0.07, 0.10, 0.05]
        )
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "operator_type": op_type,
                "is_integrated": op_type in ["SUPERMAJOR", "MAJOR_INTEGRATED"],
                "is_national": op_type == "NATIONAL_OIL",
                "employee_count": self._random_int(50, 100_000),
                "market_cap": self._random_int(100_000_000, 500_000_000_000) if op_type != "PRIVATE_EQUITY" else None,
            }
        }
        return self._create_success_result(data)


class OperationSegmentExtractor(StubExtractor):
    """STUB: Simulates operation segment classification."""
    SOURCE_NAME = "operation_segment"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    SEGMENTS = [
        "UPSTREAM_CONVENTIONAL", "UPSTREAM_UNCONVENTIONAL", "UPSTREAM_OFFSHORE",
        "UPSTREAM_DEEPWATER", "MIDSTREAM_PIPELINE", "MIDSTREAM_PROCESSING",
        "MIDSTREAM_STORAGE", "DOWNSTREAM_REFINING", "DOWNSTREAM_PETROCHEMICAL",
        "POWER_GENERATION", "RENEWABLE", "MIXED"
    ]
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        segment = self._random_choice(
            self.SEGMENTS,
            weights=[0.15, 0.15, 0.10, 0.05, 0.10, 0.08, 0.05, 0.10, 0.05, 0.05, 0.05, 0.07]
        )
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "primary_segment": segment,
                "is_upstream": segment.startswith("UPSTREAM"),
                "is_offshore": "OFFSHORE" in segment or "DEEPWATER" in segment,
                "is_downstream": segment.startswith("DOWNSTREAM"),
                "diversification": self._random_choice(["FOCUSED", "DIVERSIFIED"]),
            }
        }
        return self._create_success_result(data)


class GeographicFocusExtractor(StubExtractor):
    """STUB: Simulates geographic focus classification."""
    SOURCE_NAME = "geographic_focus"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    REGIONS = [
        "US_ONSHORE", "US_GULF_SHELF", "US_GULF_DEEPWATER", "NORTH_SEA",
        "WEST_AFRICA", "MIDDLE_EAST", "ASIA_PACIFIC", "LATIN_AMERICA",
        "GLOBAL_DIVERSIFIED", "OTHER"
    ]
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        region = self._random_choice(
            self.REGIONS,
            weights=[0.25, 0.08, 0.07, 0.10, 0.08, 0.10, 0.10, 0.08, 0.10, 0.04]
        )
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "primary_geography": region,
                "is_us_focused": region.startswith("US"),
                "is_offshore_focused": "GULF" in region or "SEA" in region,
                "political_risk_rating": self._random_choice(["LOW", "MODERATE", "HIGH"]),
                "country_count": self._random_int(1, 30),
            }
        }
        return self._create_success_result(data)
