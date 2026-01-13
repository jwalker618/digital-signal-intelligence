"""
Energy Aggregators - All Signal Groups

Production-ready aggregators for Energy coverage signals.
"""

from typing import Any, Dict, List, Optional
from ...base import ProductionAggregator
from ....types import AggregatorResult, ExtractorResult


# =============================================================================
# NETWORK AUTHORITY AGGREGATORS
# =============================================================================

class EnergyPartnerQualityAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No partner data")
        return self._create_success_result({"partner_quality_score": round(self._normalize_float(raw.get("partner_quality_score"), 50), 1)}, extractor_results)


class ContractorQualityAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No contractor data")
        return self._create_success_result({"contractor_quality_score": round(self._normalize_float(raw.get("contractor_quality_score"), 50), 1)}, extractor_results)


class EnergyBankingRelationshipAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No banking data")
        return self._create_success_result({"banking_relationship_score": round(self._normalize_float(raw.get("banking_relationship_score"), 50), 1)}, extractor_results)


class InsuranceHistoryAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No insurance data")
        return self._create_success_result({"insurance_history_score": self._normalize_int(raw.get("insurance_history_score"), 70)}, extractor_results)


class RegulatorRelationshipAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No regulator data")
        return self._create_success_result({"regulator_relationship_score": self._normalize_int(raw.get("regulator_relationship_score"), 60)}, extractor_results)


class OfftakeQualityAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No offtake data")
        return self._create_success_result({"offtake_quality_score": round(self._normalize_float(raw.get("offtake_quality_score"), 60), 1)}, extractor_results)


# =============================================================================
# SAFETY PERFORMANCE AGGREGATORS
# =============================================================================

class OSHATRIRAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No TRIR data")
        return self._create_success_result({"osha_trir_score": round(self._normalize_float(raw.get("trir_score"), 50), 1)}, extractor_results)


class OSHAViolationsAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        if not raw:
            return self._create_error_result("No OSHA violations data")
        if raw.get("willful_violations_5yr", 0) > 0:
            warnings.append("Willful OSHA violations")
        return self._create_success_result({"osha_violations_score": self._normalize_int(raw.get("osha_violations_score"), 70)}, extractor_results, warnings)


class BSEEIncidentAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No BSEE data")
        return self._create_success_result({"bsee_incident_score": self._normalize_int(raw.get("bsee_score"), 100)}, extractor_results)


class ProcessSafetyAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        if not raw:
            return self._create_error_result("No process safety data")
        if raw.get("tier1_events_3yr", 0) > 0:
            warnings.append("Tier 1 process safety events")
        return self._create_success_result({"process_safety_score": self._normalize_int(raw.get("process_safety_score"), 70)}, extractor_results, warnings)


class FatalityHistoryAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        if not raw:
            return self._create_error_result("No fatality data")
        if raw.get("fatalities_5yr", 0) > 0:
            warnings.append(f"Fatality history: {raw.get('fatalities_5yr')} in 5 years")
        return self._create_success_result({"fatality_score": self._normalize_int(raw.get("fatality_score"), 100)}, extractor_results, warnings)


class MajorIncidentAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        if not raw:
            return self._create_error_result("No major incident data")
        if raw.get("major_incidents_10yr", 0) > 0:
            warnings.append("Major incident history")
        return self._create_success_result({"major_incident_score": self._normalize_int(raw.get("major_incident_score"), 100)}, extractor_results, warnings)


class NearMissReportingAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No near-miss data")
        return self._create_success_result({"near_miss_score": self._normalize_int(raw.get("near_miss_score"), 50)}, extractor_results)


# =============================================================================
# ENVIRONMENTAL COMPLIANCE AGGREGATORS
# =============================================================================

class EPAViolationAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        if not raw:
            return self._create_error_result("No EPA data")
        if raw.get("ongoing_enforcement"):
            warnings.append("Ongoing EPA enforcement")
        return self._create_success_result({"epa_violation_score": self._normalize_int(raw.get("epa_violation_score"), 70)}, extractor_results, warnings)


class SpillHistoryAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        if not raw:
            return self._create_error_result("No spill data")
        if raw.get("major_spills_5yr", 0) > 0:
            warnings.append("Major spill history")
        return self._create_success_result({"spill_history_score": self._normalize_int(raw.get("spill_history_score"), 80)}, extractor_results, warnings)


class EmissionsComplianceAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No emissions data")
        return self._create_success_result({"emissions_compliance_score": self._normalize_int(raw.get("emissions_compliance_score"), 70)}, extractor_results)


class FlaringIntensityAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No flaring data")
        return self._create_success_result({"flaring_score": round(self._normalize_float(raw.get("flaring_score"), 60), 1)}, extractor_results)


class MethaneEmissionsAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No methane data")
        return self._create_success_result({"methane_score": round(self._normalize_float(raw.get("methane_score"), 60), 1)}, extractor_results)


class RemediationAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No remediation data")
        return self._create_success_result({"remediation_score": self._normalize_int(raw.get("remediation_score"), 80)}, extractor_results)


# =============================================================================
# OPERATIONAL TELEMETRY AGGREGATORS
# =============================================================================

class ProductionConsistencyAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No production data")
        return self._create_success_result({"production_consistency_score": self._normalize_int(raw.get("production_consistency_score"), 70)}, extractor_results)


class FacilityActivityAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No facility data")
        return self._create_success_result({"facility_activity_score": round(self._normalize_float(raw.get("facility_activity_score"), 70), 1)}, extractor_results)


class WellIntegrityAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No well integrity data")
        return self._create_success_result({"well_integrity_score": self._normalize_int(raw.get("well_integrity_score"), 70)}, extractor_results)


class MaintenancePatternAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No maintenance data")
        return self._create_success_result({"maintenance_pattern_score": round(self._normalize_float(raw.get("maintenance_pattern_score"), 70), 1)}, extractor_results)


class OperationalEfficiencyAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No efficiency data")
        return self._create_success_result({"operational_efficiency_score": round(self._normalize_float(raw.get("operational_efficiency_score"), 70), 1)}, extractor_results)


# =============================================================================
# FINANCIAL STABILITY AGGREGATORS
# =============================================================================

class LeverageAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No leverage data")
        return self._create_success_result({"leverage_score": round(self._normalize_float(raw.get("leverage_score"), 50), 1)}, extractor_results)


class AROCoverageAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        if not raw:
            return self._create_error_result("No ARO data")
        if raw.get("aro_funding_pct", 100) < 80:
            warnings.append("ARO underfunding")
        return self._create_success_result({"aro_coverage_score": round(self._normalize_float(raw.get("aro_coverage_score"), 70), 1)}, extractor_results, warnings)


class CapexTrendAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No capex data")
        return self._create_success_result({"capex_trend_score": round(self._normalize_float(raw.get("capex_trend_score"), 70), 1)}, extractor_results)


class RestructuringAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        if not raw:
            return self._create_error_result("No restructuring data")
        if raw.get("bankruptcy_10yr"):
            warnings.append("Bankruptcy history")
        return self._create_success_result({"restructuring_score": self._normalize_int(raw.get("restructuring_score"), 100)}, extractor_results, warnings)


# =============================================================================
# ASSET PORTFOLIO AGGREGATORS
# =============================================================================

class AssetAgeAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No asset age data")
        return self._create_success_result({"asset_age_score": round(self._normalize_float(raw.get("asset_age_score"), 60), 1)}, extractor_results)


class ConcentrationAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No concentration data")
        return self._create_success_result({"concentration_score": round(self._normalize_float(raw.get("concentration_score"), 60), 1)}, extractor_results)


class TechnologyProfileAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No technology data")
        return self._create_success_result({"technology_profile_score": self._normalize_int(raw.get("technology_profile_score"), 70)}, extractor_results)


class DecommissioningAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No decommissioning data")
        return self._create_success_result({"decommissioning_score": round(self._normalize_float(raw.get("decommissioning_score"), 70), 1)}, extractor_results)


class PermitStatusAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No permit data")
        return self._create_success_result({"permit_status_score": self._normalize_int(raw.get("permit_status_score"), 80)}, extractor_results)


# =============================================================================
# CORPORATE FOOTPRINT AGGREGATORS
# =============================================================================

class SafetyCommunicationAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No safety comms data")
        return self._create_success_result({"safety_communication_score": round(self._normalize_float(raw.get("safety_communication_score"), 50), 1)}, extractor_results)


class EnergyESGReportingAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No ESG reporting data")
        return self._create_success_result({"esg_reporting_score": self._normalize_int(raw.get("esg_reporting_score"), 50)}, extractor_results)


class TechnicalHiringAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No hiring data")
        return self._create_success_result({"technical_hiring_score": round(self._normalize_float(raw.get("technical_hiring_score"), 50), 1)}, extractor_results)


class IndustryPresenceAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No presence data")
        return self._create_success_result({"industry_presence_score": round(self._normalize_float(raw.get("industry_presence_score"), 50), 1)}, extractor_results)


class DisclosureQualityAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No disclosure data")
        return self._create_success_result({"disclosure_quality_score": round(self._normalize_float(raw.get("disclosure_score"), 60), 1)}, extractor_results)


class HSELeadershipAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No HSE leadership data")
        return self._create_success_result({"hse_leadership_score": self._normalize_int(raw.get("hse_leadership_score"), 50)}, extractor_results)


# =============================================================================
# STRUCTURED DATA AGGREGATORS
# =============================================================================

class EnergyESGRatingAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No ESG rating data")
        return self._create_success_result({"esg_rating_score": round(self._normalize_float(raw.get("esg_rating_score"), 50), 1)}, extractor_results)


class BenchmarkAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No benchmark data")
        return self._create_success_result({"benchmark_score": round(self._normalize_float(raw.get("benchmark_score"), 60), 1)}, extractor_results)


# =============================================================================
# CATEGORICAL AGGREGATORS
# =============================================================================

class OperatorTypeAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No operator type data")
        return self._create_success_result({"operator_type": raw.get("operator_type"), "is_integrated": raw.get("is_integrated")}, extractor_results)


class OperationSegmentAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No segment data")
        return self._create_success_result({"primary_segment": raw.get("primary_segment"), "is_offshore": raw.get("is_offshore")}, extractor_results)


class GeographicFocusAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No geographic data")
        return self._create_success_result({"primary_geography": raw.get("primary_geography"), "is_us_focused": raw.get("is_us_focused")}, extractor_results)
