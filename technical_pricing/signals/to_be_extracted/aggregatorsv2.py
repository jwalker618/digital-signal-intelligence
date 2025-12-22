"""
aggregators_v2.py - DSI Technical Pricing Data Aggregation Framework

Complete aggregator implementation for all 322 signals across 7 coverage lines.
"""

from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Type

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

AGGREGATOR_REGISTRY: Dict[str, Type["DataAggregator"]] = {}

def register_aggregator(cls: Type["DataAggregator"]) -> Type["DataAggregator"]:
    AGGREGATOR_REGISTRY[cls.__name__] = cls
    return cls

@dataclass
class SignalOutput:
    signal_name: str
    categorizer_type: str
    data: Dict[str, Any]
    confidence: float = 1.0
    source_extractors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AggregationResult:
    entity_id: str
    signals: Dict[str, SignalOutput]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    errors: List[str] = field(default_factory=list)

class DataAggregator(ABC):
    required_extractors: List[str] = []
    optional_extractors: List[str] = []

    def __init__(self, entity_id: str = ""):
        self.entity_id = entity_id

    @abstractmethod
    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        raise NotImplementedError

    def _get(self, data: Dict, *keys: str, default: Any = None) -> Any:
        current = data
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
                if current is None:
                    return default
            else:
                return default
        return current

    def _count_to_state(self, count: int, thresholds: List[tuple], default: str = "HIGH") -> str:
        for max_count, state in thresholds:
            if count <= max_count:
                return state
        return default

    def _value_to_state(self, value: float, thresholds: List[tuple], default: str = "UNKNOWN") -> str:
        for max_val, state in thresholds:
            if value <= max_val:
                return state
        return default

    def _make_signal(self, name: str, cat_type: str, data: Dict[str, Any], extractors: List[str], confidence: float = 1.0, **metadata) -> SignalOutput:
        return SignalOutput(signal_name=name, categorizer_type=cat_type, data=data, confidence=confidence, source_extractors=extractors, metadata=metadata)


# MARINE COVERAGE - 48 SIGNALS

@register_aggregator
class MarineSafetyComplianceAggregator(DataAggregator):
    required_extractors = ["PSCInspectionExtractor", "ClassificationSocietyExtractor", "ISMComplianceExtractor"]
    optional_extractors = ["CasualtyHistoryExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        psc = extractions.get("PSCInspectionExtractor", {})
        class_data = extractions.get("ClassificationSocietyExtractor", {})
        ism = extractions.get("ISMComplianceExtractor", {})
        casualty = extractions.get("CasualtyHistoryExtractor", {})
        
        detentions = self._get(psc, "detentions_3yr", default=0)
        signals["psc_detention"] = self._make_signal("psc_detention", "scoring_logic", {"state": self._count_to_state(detentions, [(0, "CLEAN"), (1, "SINGLE"), (2, "MULTIPLE")], "FREQUENT")}, ["PSCInspectionExtractor"])
        signals["psc_deficiency"] = self._make_signal("psc_deficiency", "threshold_bucket", {"value": self._get(psc, "deficiency_rate", default=0.0)}, ["PSCInspectionExtractor"])
        
        class_raw = self._get(class_data, "class_status", default="UNKNOWN")
        conditions = self._get(class_data, "conditions_of_class", default=0)
        class_state = "IN_CLASS_CLEAN" if class_raw == "IN_CLASS" and conditions == 0 else "IN_CLASS_CONDITIONS" if class_raw == "IN_CLASS" else class_raw if class_raw in ["SUSPENDED", "WITHDRAWN"] else "NO_CLASS"
        signals["class_status"] = self._make_signal("class_status", "scoring_logic", {"state": class_state}, ["ClassificationSocietyExtractor"])
        
        doc = self._get(ism, "doc_status", default="UNKNOWN")
        smc = self._get(ism, "smc_status", default="UNKNOWN")
        ism_state = "COMPLIANT" if doc == "VALID" and smc == "VALID" else "PARTIAL" if doc == "VALID" or smc == "VALID" else "NON_COMPLIANT"
        signals["ism_compliance"] = self._make_signal("ism_compliance", "scoring_logic", {"state": ism_state}, ["ISMComplianceExtractor"])
        
        signals["casualty_history"] = self._make_signal("casualty_history", "scoring_logic", {"state": self._count_to_state(self._get(casualty, "incidents_5yr", default=0), [(0, "CLEAN"), (1, "SINGLE"), (3, "MULTIPLE")], "SIGNIFICANT")}, ["CasualtyHistoryExtractor"])
        losses = self._get(casualty, "total_losses", default=0)
        signals["total_loss"] = self._make_signal("total_loss", "scoring_logic", {"state": "CLEAN" if losses == 0 else "SINGLE" if losses == 1 else "MULTIPLE"}, ["CasualtyHistoryExtractor"])
        overdue = self._get(class_data, "surveys_overdue", default=0)
        signals["survey_compliance"] = self._make_signal("survey_compliance", "scoring_logic", {"state": "CURRENT" if overdue == 0 else "MINOR_OVERDUE" if overdue <= 2 else "MAJOR_OVERDUE"}, ["ClassificationSocietyExtractor"])
        
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class MarineSanctionsComplianceAggregator(DataAggregator):
    required_extractors = ["SanctionsScreeningExtractor"]
    optional_extractors = ["AISTrackingExtractor", "OwnershipExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        sanctions = extractions.get("SanctionsScreeningExtractor", {})
        ais = extractions.get("AISTrackingExtractor", {})
        ownership = extractions.get("OwnershipExtractor", {})
        
        signals["sanctions_status"] = self._make_signal("sanctions_status", "scoring_logic", {"state": self._get(sanctions, "screening_status", default="UNKNOWN")}, ["SanctionsScreeningExtractor"])
        signals["ownership_transparency"] = self._make_signal("ownership_transparency", "scoring_logic", {"state": self._get(ownership, "transparency_level", default="UNKNOWN")}, ["OwnershipExtractor"])
        signals["jurisdiction_risk"] = self._make_signal("jurisdiction_risk", "scoring_logic", {"state": self._get(ownership, "jurisdiction_risk", default="UNKNOWN")}, ["OwnershipExtractor"])
        sts = self._get(ais, "sts_events_12m", default=0)
        signals["sts_pattern"] = self._make_signal("sts_pattern", "scoring_logic", {"state": self._count_to_state(sts, [(0, "NONE"), (2, "OCCASIONAL"), (5, "FREQUENT")], "HIGH_FREQUENCY")}, ["AISTrackingExtractor"])
        hist = self._get(sanctions, "historical_matches", default=0)
        signals["historical_sanctions"] = self._make_signal("historical_sanctions", "scoring_logic", {"state": "CLEAN" if hist == 0 else "HISTORICAL" if hist <= 2 else "MULTIPLE_HISTORICAL"}, ["SanctionsScreeningExtractor"])
        
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class MarineOperationalTelemetryAggregator(DataAggregator):
    required_extractors = ["AISTrackingExtractor"]
    optional_extractors = ["RouteRiskExtractor", "OperationsMetricsExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        ais = extractions.get("AISTrackingExtractor", {})
        route = extractions.get("RouteRiskExtractor", {})
        ops = extractions.get("OperationsMetricsExtractor", {})
        
        signals["ais_compliance"] = self._make_signal("ais_compliance", "threshold_bucket", {"value": self._get(ais, "compliance_rate", default=0.0) * 100}, ["AISTrackingExtractor"])
        dark = self._get(ais, "dark_hours_30d", default=0)
        signals["dark_activity"] = self._make_signal("dark_activity", "scoring_logic", {"state": self._count_to_state(dark, [(0, "CLEAN"), (24, "MINOR"), (72, "CONCERNING")], "HIGH_RISK")}, ["AISTrackingExtractor"])
        signals["route_risk"] = self._make_signal("route_risk", "scoring_logic", {"state": self._get(route, "risk_level", default="UNKNOWN")}, ["RouteRiskExtractor"])
        hr_pct = self._get(route, "high_risk_region_pct", default=0.0)
        signals["psc_region_exposure"] = self._make_signal("psc_region_exposure", "scoring_logic", {"state": self._value_to_state(hr_pct, [(10, "LOW"), (30, "MODERATE"), (50, "ELEVATED")], "HIGH")}, ["RouteRiskExtractor"])
        signals["operational_efficiency"] = self._make_signal("operational_efficiency", "threshold_bucket", {"value": self._get(ops, "utilization_rate", default=0.0) * 100}, ["OperationsMetricsExtractor"])
        signals["weather_routing"] = self._make_signal("weather_routing", "scoring_logic", {"state": "ACTIVE" if self._get(ops, "weather_routing", default=False) else "NOT_USED"}, ["OperationsMetricsExtractor"])
        signals["trading_pattern"] = self._make_signal("trading_pattern", "enumeration", {"category": self._get(route, "trading_pattern", default="UNKNOWN")}, ["RouteRiskExtractor"])
        
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class MarineFleetQualityAggregator(DataAggregator):
    required_extractors = ["EquasisOperatorExtractor"]
    optional_extractors = ["VesselValuationExtractor", "CrewCertificationExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        equasis = extractions.get("EquasisOperatorExtractor", {})
        valuation = extractions.get("VesselValuationExtractor", {})
        crew = extractions.get("CrewCertificationExtractor", {})
        
        avg_age = self._get(equasis, "average_fleet_age", default=0.0)
        signals["fleet_age"] = self._make_signal("fleet_age", "threshold_bucket", {"value": avg_age}, ["EquasisOperatorExtractor"])
        band = "YOUNG" if avg_age <= 5 else "MODERN" if avg_age <= 10 else "MATURE" if avg_age <= 15 else "AGING" if avg_age <= 20 else "OLD"
        signals["fleet_age_band"] = self._make_signal("fleet_age_band", "enumeration", {"category": band}, ["EquasisOperatorExtractor"])
        churn = self._get(equasis, "fleet_churn_rate", default=0.0)
        stability = "STABLE" if churn <= 5 else "MODERATE" if churn <= 15 else "VOLATILE" if churn <= 30 else "HIGHLY_VOLATILE"
        signals["fleet_stability"] = self._make_signal("fleet_stability", "scoring_logic", {"state": stability}, ["EquasisOperatorExtractor"])
        signals["vessel_quality"] = self._make_signal("vessel_quality", "threshold_bucket", {"value": self._get(valuation, "quality_score", default=50)}, ["VesselValuationExtractor"])
        signals["vessel_category"] = self._make_signal("vessel_category", "enumeration", {"category": self._get(equasis, "primary_vessel_type", default="UNKNOWN")}, ["EquasisOperatorExtractor"])
        signals["crew_certification"] = self._make_signal("crew_certification", "scoring_logic", {"state": self._get(crew, "certification_compliance", default="UNKNOWN")}, ["CrewCertificationExtractor"])
        mgmt = self._get(equasis, "management_changes_3yr", default=0)
        signals["management_consistency"] = self._make_signal("management_consistency", "scoring_logic", {"state": "STABLE" if mgmt == 0 else "MINOR_CHANGES" if mgmt <= 1 else "FREQUENT_CHANGES"}, ["EquasisOperatorExtractor"])
        
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class MarineClassificationQualityAggregator(DataAggregator):
    required_extractors = ["ClassificationSocietyExtractor", "FlagStatePerformanceExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        class_data = extractions.get("ClassificationSocietyExtractor", {})
        flag_data = extractions.get("FlagStatePerformanceExtractor", {})
        
        signals["classification_society"] = self._make_signal("classification_society", "quality_tier", {"entity": self._get(class_data, "society_name", default="UNKNOWN")}, ["ClassificationSocietyExtractor"])
        signals["flag_state"] = self._make_signal("flag_state", "scoring_logic", {"state": self._get(flag_data, "paris_mou_status", default="UNKNOWN")}, ["FlagStatePerformanceExtractor"])
        signals["flag_state_quality"] = self._make_signal("flag_state_quality", "quality_tier", {"entity": self._get(flag_data, "flag_code", default="UNKNOWN")}, ["FlagStatePerformanceExtractor"])
        
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class MarinePIQualityAggregator(DataAggregator):
    required_extractors = ["PIClubExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        pi = extractions.get("PIClubExtractor", {})
        
        signals["pi_club"] = self._make_signal("pi_club", "quality_tier", {"entity": self._get(pi, "club_name", default="UNKNOWN")}, ["PIClubExtractor"])
        claims = self._get(pi, "claims_5yr", default=0)
        signals["pi_claims_history"] = self._make_signal("pi_claims_history", "scoring_logic", {"state": self._count_to_state(claims, [(0, "CLEAN"), (2, "LOW"), (5, "MODERATE")], "HIGH")}, ["PIClubExtractor"])
        
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class MarineFinancialStabilityAggregator(DataAggregator):
    required_extractors = ["MarineFinancialExtractor"]
    optional_extractors = ["CreditRatingExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        fin = extractions.get("MarineFinancialExtractor", {})
        credit = extractions.get("CreditRatingExtractor", {})
        
        signals["credit_rating"] = self._make_signal("credit_rating", "scoring_logic", {"state": self._get(credit, "rating", default=self._get(fin, "credit_rating", default="NR"))}, ["CreditRatingExtractor"])
        signals["banking_relationship"] = self._make_signal("banking_relationship", "quality_tier", {"entity": self._get(fin, "primary_bank_tier", default="UNKNOWN")}, ["MarineFinancialExtractor"])
        signals["charterer_quality"] = self._make_signal("charterer_quality", "quality_tier", {"entity": self._get(fin, "primary_charterer", default="UNKNOWN")}, ["MarineFinancialExtractor"])
        
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class MarineManagementQualityAggregator(DataAggregator):
    required_extractors = ["EquasisOperatorExtractor"]
    optional_extractors = ["IndustryAssociationExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        equasis = extractions.get("EquasisOperatorExtractor", {})
        assoc = extractions.get("IndustryAssociationExtractor", {})
        
        signals["technical_manager"] = self._make_signal("technical_manager", "quality_tier", {"entity": self._get(equasis, "technical_manager", default="UNKNOWN")}, ["EquasisOperatorExtractor"])
        memberships = self._get(assoc, "memberships", default=[])
        assoc_state = "TIER_1" if any(m in ["BIMCO", "INTERTANKO", "INTERCARGO"] for m in memberships) else "TIER_2" if memberships else "NONE"
        signals["industry_association"] = self._make_signal("industry_association", "scoring_logic", {"state": assoc_state}, ["IndustryAssociationExtractor"])
        signals["port_relationship"] = self._make_signal("port_relationship", "scoring_logic", {"state": self._get(equasis, "port_relationship_quality", default="UNKNOWN")}, ["EquasisOperatorExtractor"])
        signals["operator_type"] = self._make_signal("operator_type", "enumeration", {"category": self._get(equasis, "operator_type", default="UNKNOWN")}, ["EquasisOperatorExtractor"])
        
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class MarineEnvironmentalAggregator(DataAggregator):
    required_extractors = ["MarineEnvironmentalExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        env = extractions.get("MarineEnvironmentalExtractor", {})
        
        signals["imo2020_compliance"] = self._make_signal("imo2020_compliance", "scoring_logic", {"state": self._get(env, "imo2020_status", default="UNKNOWN")}, ["MarineEnvironmentalExtractor"])
        signals["bwm_compliance"] = self._make_signal("bwm_compliance", "scoring_logic", {"state": self._get(env, "bwm_status", default="UNKNOWN")}, ["MarineEnvironmentalExtractor"])
        signals["cii_rating"] = self._make_signal("cii_rating", "scoring_logic", {"state": self._get(env, "cii_rating", default="UNKNOWN")}, ["MarineEnvironmentalExtractor"])
        incidents = self._get(env, "environmental_incidents_5yr", default=0)
        signals["environmental_incident"] = self._make_signal("environmental_incident", "scoring_logic", {"state": self._count_to_state(incidents, [(0, "CLEAN"), (1, "SINGLE"), (3, "MULTIPLE")], "SIGNIFICANT")}, ["MarineEnvironmentalExtractor"])
        
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class MarineCorporateFootprintAggregator(DataAggregator):
    required_extractors = ["CompanyProfileExtractor"]
    optional_extractors = ["MarineVettingExtractor", "ESGMetricsExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        profile = extractions.get("CompanyProfileExtractor", {})
        vetting = extractions.get("MarineVettingExtractor", {})
        esg = extractions.get("ESGMetricsExtractor", {})
        
        web_score = self._get(profile, "website_quality_score", default=50)
        signals["website_quality"] = self._make_signal("website_quality", "scoring_logic", {"state": self._value_to_state(web_score, [(30, "POOR"), (50, "BASIC"), (70, "GOOD")], "EXCELLENT")}, ["CompanyProfileExtractor"])
        signals["fleet_disclosure"] = self._make_signal("fleet_disclosure", "scoring_logic", {"state": self._get(profile, "fleet_disclosure_level", default="UNKNOWN")}, ["CompanyProfileExtractor"])
        signals["sustainability_reporting"] = self._make_signal("sustainability_reporting", "scoring_logic", {"state": self._get(profile, "sustainability_reporting", default="NONE")}, ["CompanyProfileExtractor"])
        signals["safety_communication"] = self._make_signal("safety_communication", "scoring_logic", {"state": self._get(profile, "safety_communication", default="UNKNOWN")}, ["CompanyProfileExtractor"])
        signals["crew_welfare"] = self._make_signal("crew_welfare", "scoring_logic", {"state": self._get(profile, "crew_welfare_commitment", default="UNKNOWN")}, ["CompanyProfileExtractor"])
        signals["industry_presence"] = self._make_signal("industry_presence", "scoring_logic", {"state": self._get(profile, "industry_presence", default="UNKNOWN")}, ["CompanyProfileExtractor"])
        signals["vetting"] = self._make_signal("vetting", "threshold_bucket", {"value": self._get(vetting, "average_score", default=0)}, ["MarineVettingExtractor"])
        signals["esg_rating"] = self._make_signal("esg_rating", "scoring_logic", {"state": self._get(esg, "overall_rating", default="NOT_RATED")}, ["ESGMetricsExtractor"])
        
        return AggregationResult(entity_id=self.entity_id, signals=signals)


# AEROSPACE COVERAGE - 46 SIGNALS

@register_aggregator
class AerospaceSafetyRecordAggregator(DataAggregator):
    required_extractors = ["AviationSafetyExtractor"]
    optional_extractors = ["IATAOperatorExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        safety = extractions.get("AviationSafetyExtractor", {})
        iata = extractions.get("IATAOperatorExtractor", {})
        
        accidents = self._get(safety, "accidents_10yr", default=0)
        signals["accident_history"] = self._make_signal("accident_history", "scoring_logic", {"state": self._count_to_state(accidents, [(0, "CLEAN"), (1, "SINGLE"), (2, "MULTIPLE")], "SIGNIFICANT")}, ["AviationSafetyExtractor"])
        signals["accident_rate"] = self._make_signal("accident_rate", "threshold_bucket", {"value": self._get(safety, "accident_rate_per_million", default=0.0)}, ["AviationSafetyExtractor"])
        fatalities = self._get(safety, "fatal_accidents_10yr", default=0)
        signals["fatality_history"] = self._make_signal("fatality_history", "scoring_logic", {"state": "CLEAN" if fatalities == 0 else "SINGLE" if fatalities == 1 else "MULTIPLE"}, ["AviationSafetyExtractor"])
        incidents = self._get(safety, "serious_incidents_5yr", default=0)
        signals["incident_history"] = self._make_signal("incident_history", "scoring_logic", {"state": self._count_to_state(incidents, [(0, "CLEAN"), (2, "LOW"), (5, "MODERATE")], "HIGH")}, ["AviationSafetyExtractor"])
        findings = self._get(safety, "adverse_findings_5yr", default=0)
        signals["investigation_findings"] = self._make_signal("investigation_findings", "scoring_logic", {"state": self._count_to_state(findings, [(0, "CLEAN"), (1, "MINOR"), (3, "MODERATE")], "SIGNIFICANT")}, ["AviationSafetyExtractor"])
        signals["eu_safety_list"] = self._make_signal("eu_safety_list", "scoring_logic", {"state": self._get(safety, "eu_safety_list_status", default="CLEAR")}, ["AviationSafetyExtractor"])
        signals["state_safety_rating"] = self._make_signal("state_safety_rating", "scoring_logic", {"state": self._get(safety, "state_safety_rating", default="UNKNOWN")}, ["AviationSafetyExtractor"])
        signals["safety_leadership"] = self._make_signal("safety_leadership", "scoring_logic", {"state": self._get(iata, "safety_leadership", default="UNKNOWN")}, ["IATAOperatorExtractor"])
        signals["safety_reporting"] = self._make_signal("safety_reporting", "scoring_logic", {"state": self._get(iata, "safety_reporting_culture", default="UNKNOWN")}, ["IATAOperatorExtractor"])
        
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class AerospaceRegulatoryComplianceAggregator(DataAggregator):
    required_extractors = ["IATAOperatorExtractor", "FAARegistryExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        iata = extractions.get("IATAOperatorExtractor", {})
        faa = extractions.get("FAARegistryExtractor", {})
        
        signals["iosa_status"] = self._make_signal("iosa_status", "scoring_logic", {"state": "REGISTERED" if self._get(iata, "iosa_registered", default=False) else "NOT_REGISTERED"}, ["IATAOperatorExtractor"])
        audit_findings = self._get(iata, "iosa_findings", default=0)
        signals["iosa_audit_status"] = self._make_signal("iosa_audit_status", "scoring_logic", {"state": self._count_to_state(audit_findings, [(0, "CLEAN"), (2, "MINOR_FINDINGS"), (5, "MODERATE_FINDINGS")], "SIGNIFICANT_FINDINGS")}, ["IATAOperatorExtractor"])
        signals["certificate_status"] = self._make_signal("certificate_status", "scoring_logic", {"state": self._get(faa, "certificate_status", default="UNKNOWN")}, ["FAARegistryExtractor"])
        signals["aoc_status"] = self._make_signal("aoc_status", "scoring_logic", {"state": self._get(faa, "aoc_status", default="UNKNOWN")}, ["FAARegistryExtractor"])
        enforcements = self._get(faa, "enforcement_actions_5yr", default=0)
        signals["enforcement_actions"] = self._make_signal("enforcement_actions", "scoring_logic", {"state": self._count_to_state(enforcements, [(0, "CLEAN"), (1, "SINGLE"), (3, "MULTIPLE")], "SIGNIFICANT")}, ["FAARegistryExtractor"])
        signals["regulatory_framework"] = self._make_signal("regulatory_framework", "enumeration", {"category": self._get(faa, "regulatory_framework", default="UNKNOWN")}, ["FAARegistryExtractor"])
        ramp = self._get(faa, "ramp_inspection_findings", default=0)
        signals["ramp_inspection"] = self._make_signal("ramp_inspection", "scoring_logic", {"state": self._count_to_state(ramp, [(0, "CLEAN"), (2, "MINOR"), (5, "MODERATE")], "SIGNIFICANT")}, ["FAARegistryExtractor"])
        
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class AerospaceFleetQualityAggregator(DataAggregator):
    required_extractors = ["AircraftFleetExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        fleet = extractions.get("AircraftFleetExtractor", {})
        
        signals["fleet_size"] = self._make_signal("fleet_size", "threshold_bucket", {"value": self._get(fleet, "total_aircraft", default=0)}, ["AircraftFleetExtractor"])
        signals["fleet_age"] = self._make_signal("fleet_age", "threshold_bucket", {"value": self._get(fleet, "average_age", default=0.0)}, ["AircraftFleetExtractor"])
        signals["fleet_category"] = self._make_signal("fleet_category", "enumeration", {"category": self._get(fleet, "primary_category", default="UNKNOWN")}, ["AircraftFleetExtractor"])
        type_count = self._get(fleet, "aircraft_type_count", default=1)
        homogeneity = "HOMOGENEOUS" if type_count <= 2 else "MODERATE" if type_count <= 5 else "DIVERSE"
        signals["fleet_homogeneity"] = self._make_signal("fleet_homogeneity", "scoring_logic", {"state": homogeneity}, ["AircraftFleetExtractor"])
        signals["aircraft_generation"] = self._make_signal("aircraft_generation", "scoring_logic", {"state": self._get(fleet, "technology_generation", default="UNKNOWN")}, ["AircraftFleetExtractor"])
        signals["lessor_quality"] = self._make_signal("lessor_quality", "quality_tier", {"entity": self._get(fleet, "primary_lessor", default="UNKNOWN")}, ["AircraftFleetExtractor"])
        signals["oem_relationship"] = self._make_signal("oem_relationship", "scoring_logic", {"state": self._get(fleet, "oem_relationship", default="UNKNOWN")}, ["AircraftFleetExtractor"])
        signals["order_backlog"] = self._make_signal("order_backlog", "threshold_bucket", {"value": self._get(fleet, "order_backlog", default=0)}, ["AircraftFleetExtractor"])
        
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class AerospaceOperationalQualityAggregator(DataAggregator):
    required_extractors = ["OperationalPerformanceExtractor"]
    optional_extractors = ["RouteRiskExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        ops = extractions.get("OperationalPerformanceExtractor", {})
        route = extractions.get("RouteRiskExtractor", {})
        
        signals["otp_score"] = self._make_signal("otp_score", "threshold_bucket", {"value": self._get(ops, "on_time_performance", default=0.0)}, ["OperationalPerformanceExtractor"])
        signals["dispatch_reliability"] = self._make_signal("dispatch_reliability", "threshold_bucket", {"value": self._get(ops, "dispatch_reliability", default=0.0)}, ["OperationalPerformanceExtractor"])
        signals["operational_complexity"] = self._make_signal("operational_complexity", "scoring_logic", {"state": self._get(ops, "complexity_level", default="UNKNOWN")}, ["OperationalPerformanceExtractor"])
        chall_pct = self._get(route, "challenging_airport_pct", default=0.0)
        signals["challenging_airports"] = self._make_signal("challenging_airports", "scoring_logic", {"state": self._value_to_state(chall_pct, [(5, "LOW"), (15, "MODERATE"), (30, "ELEVATED")], "HIGH")}, ["RouteRiskExtractor"])
        signals["terrain_exposure"] = self._make_signal("terrain_exposure", "scoring_logic", {"state": self._get(route, "terrain_exposure", default="UNKNOWN")}, ["RouteRiskExtractor"])
        signals["weather_exposure"] = self._make_signal("weather_exposure", "scoring_logic", {"state": self._get(route, "weather_exposure", default="UNKNOWN")}, ["RouteRiskExtractor"])
        hr_pct = self._get(route, "high_risk_destination_pct", default=0.0)
        signals["high_risk_destinations"] = self._make_signal("high_risk_destinations", "scoring_logic", {"state": self._value_to_state(hr_pct, [(5, "LOW"), (15, "MODERATE"), (30, "ELEVATED")], "HIGH")}, ["RouteRiskExtractor"])
        signals["conflict_zone_exposure"] = self._make_signal("conflict_zone_exposure", "scoring_logic", {"state": self._get(route, "conflict_zone_exposure", default="NONE")}, ["RouteRiskExtractor"])
        
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class AerospaceMaintenanceQualityAggregator(DataAggregator):
    required_extractors = ["MROProviderExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        mro = extractions.get("MROProviderExtractor", {})
        
        signals["mro_quality"] = self._make_signal("mro_quality", "quality_tier", {"entity": self._get(mro, "primary_mro", default="UNKNOWN")}, ["MROProviderExtractor"])
        maint_score = self._get(mro, "maintenance_quality_score", default=50)
        signals["maintenance_indicators"] = self._make_signal("maintenance_indicators", "scoring_logic", {"state": self._value_to_state(maint_score, [(40, "POOR"), (60, "ADEQUATE"), (80, "GOOD")], "EXCELLENT")}, ["MROProviderExtractor"])
        ad_overdue = self._get(mro, "ad_overdue_count", default=0)
        signals["ad_compliance"] = self._make_signal("ad_compliance", "scoring_logic", {"state": "COMPLIANT" if ad_overdue == 0 else "MINOR_OVERDUE" if ad_overdue <= 2 else "SIGNIFICANT_OVERDUE"}, ["MROProviderExtractor"])
        
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class AerospaceCrewQualityAggregator(DataAggregator):
    required_extractors = ["CrewTrainingExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        crew = extractions.get("CrewTrainingExtractor", {})
        
        avg_hours = self._get(crew, "average_flight_hours", default=0)
        signals["crew_experience"] = self._make_signal("crew_experience", "scoring_logic", {"state": self._value_to_state(avg_hours, [(2000, "LOW"), (5000, "MODERATE"), (10000, "HIGH")], "VERY_HIGH")}, ["CrewTrainingExtractor"])
        signals["training_indicators"] = self._make_signal("training_indicators", "scoring_logic", {"state": self._get(crew, "training_program_quality", default="UNKNOWN")}, ["CrewTrainingExtractor"])
        
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class AerospaceFinancialStabilityAggregator(DataAggregator):
    required_extractors = ["AviationFinancialExtractor"]
    optional_extractors = ["CreditRatingExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        fin = extractions.get("AviationFinancialExtractor", {})
        credit = extractions.get("CreditRatingExtractor", {})
        
        signals["credit_rating"] = self._make_signal("credit_rating", "scoring_logic", {"state": self._get(credit, "rating", default=self._get(fin, "credit_rating", default="NR"))}, ["CreditRatingExtractor"])
        signals["public_financials"] = self._make_signal("public_financials", "scoring_logic", {"state": self._get(fin, "financial_health", default="UNKNOWN")}, ["AviationFinancialExtractor"])
        signals["government_support"] = self._make_signal("government_support", "scoring_logic", {"state": self._get(fin, "government_support", default="NONE")}, ["AviationFinancialExtractor"])
        signals["growth_rate"] = self._make_signal("growth_rate", "threshold_bucket", {"value": self._get(fin, "revenue_growth_rate", default=0.0)}, ["AviationFinancialExtractor"])
        
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class AerospaceNetworkQualityAggregator(DataAggregator):
    required_extractors = ["IATAOperatorExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        iata = extractions.get("IATAOperatorExtractor", {})
        
        signals["alliance_membership"] = self._make_signal("alliance_membership", "scoring_logic", {"state": self._get(iata, "alliance", default="NONE")}, ["IATAOperatorExtractor"])
        signals["codeshare_quality"] = self._make_signal("codeshare_quality", "scoring_logic", {"state": self._get(iata, "codeshare_quality", default="UNKNOWN")}, ["IATAOperatorExtractor"])
        signals["market_position"] = self._make_signal("market_position", "scoring_logic", {"state": self._get(iata, "market_position", default="UNKNOWN")}, ["IATAOperatorExtractor"])
        signals["industry_engagement"] = self._make_signal("industry_engagement", "scoring_logic", {"state": self._get(iata, "industry_engagement", default="UNKNOWN")}, ["IATAOperatorExtractor"])
        
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class AerospaceManagementQualityAggregator(DataAggregator):
    required_extractors = ["IATAOperatorExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        iata = extractions.get("IATAOperatorExtractor", {})
        
        mgmt_changes = self._get(iata, "ceo_changes_5yr", default=0)
        signals["management_stability"] = self._make_signal("management_stability", "scoring_logic", {"state": "STABLE" if mgmt_changes == 0 else "MINOR_CHANGES" if mgmt_changes <= 1 else "FREQUENT_CHANGES"}, ["IATAOperatorExtractor"])
        signals["corporate_structure"] = self._make_signal("corporate_structure", "scoring_logic", {"state": self._get(iata, "corporate_structure", default="UNKNOWN")}, ["IATAOperatorExtractor"])
        signals["operator_type"] = self._make_signal("operator_type", "enumeration", {"category": self._get(iata, "operator_type", default="UNKNOWN")}, ["IATAOperatorExtractor"])
        
        return AggregationResult(entity_id=self.entity_id, signals=signals)


# CYBER COVERAGE - 38 SIGNALS

@register_aggregator
class CyberTechnicalInfrastructureAggregator(DataAggregator):
    required_extractors = ["SecurityScorecardExtractor", "TechnicalScanExtractor"]
    optional_extractors = ["ThreatIntelligenceExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        scorecard = extractions.get("SecurityScorecardExtractor", {})
        tech = extractions.get("TechnicalScanExtractor", {})
        threat = extractions.get("ThreatIntelligenceExtractor", {})
        
        signals["security_rating"] = self._make_signal("security_rating", "threshold_bucket", {"value": self._get(scorecard, "overall_score", default=0)}, ["SecurityScorecardExtractor"])
        signals["tls_score"] = self._make_signal("tls_score", "scoring_logic", {"state": self._get(tech, "tls_grade", default="UNKNOWN")}, ["TechnicalScanExtractor"])
        signals["email_auth"] = self._make_signal("email_auth", "scoring_logic", {"state": self._get(tech, "email_auth_status", default="UNKNOWN")}, ["TechnicalScanExtractor"])
        signals["security_headers"] = self._make_signal("security_headers", "scoring_logic", {"state": self._get(tech, "security_headers_status", default="UNKNOWN")}, ["TechnicalScanExtractor"])
        signals["dnssec"] = self._make_signal("dnssec", "boolean_flag", {"flag": self._get(tech, "dnssec_enabled", default=False)}, ["TechnicalScanExtractor"])
        signals["waf_presence"] = self._make_signal("waf_presence", "boolean_flag", {"flag": self._get(tech, "waf_detected", default=False)}, ["TechnicalScanExtractor"])
        signals["cdn_usage"] = self._make_signal("cdn_usage", "boolean_flag", {"flag": self._get(tech, "cdn_detected", default=False)}, ["TechnicalScanExtractor"])
        signals["cloud_infrastructure"] = self._make_signal("cloud_infrastructure", "scoring_logic", {"state": self._get(tech, "cloud_provider", default="UNKNOWN")}, ["TechnicalScanExtractor"])
        signals["software_currency"] = self._make_signal("software_currency", "scoring_logic", {"state": self._get(tech, "software_currency_status", default="UNKNOWN")}, ["TechnicalScanExtractor"])
        cves = self._get(scorecard, "critical_cves", default=0)
        signals["cve_exposure"] = self._make_signal("cve_exposure", "scoring_logic", {"state": self._count_to_state(cves, [(0, "CLEAN"), (2, "LOW"), (5, "MODERATE")], "HIGH")}, ["SecurityScorecardExtractor"])
        signals["credential_exposure"] = self._make_signal("credential_exposure", "scoring_logic", {"state": self._get(threat, "credential_exposure", default="UNKNOWN")}, ["ThreatIntelligenceExtractor"])
        signals["dark_web"] = self._make_signal("dark_web", "scoring_logic", {"state": self._get(threat, "dark_web_presence", default="UNKNOWN")}, ["ThreatIntelligenceExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class CyberPublicRecordAggregator(DataAggregator):
    required_extractors = ["BreachDatabaseExtractor"]
    optional_extractors = ["CyberInsuranceHistoryExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        breach = extractions.get("BreachDatabaseExtractor", {})
        insurance = extractions.get("CyberInsuranceHistoryExtractor", {})
        breaches = self._get(breach, "breaches_5yr", default=0)
        signals["breach_history"] = self._make_signal("breach_history", "scoring_logic", {"state": self._count_to_state(breaches, [(0, "CLEAN"), (1, "SINGLE"), (2, "MULTIPLE")], "SIGNIFICANT")}, ["BreachDatabaseExtractor"])
        litigation = self._get(breach, "cyber_litigation_count", default=0)
        signals["litigation_history"] = self._make_signal("litigation_history", "scoring_logic", {"state": self._count_to_state(litigation, [(0, "CLEAN"), (1, "SINGLE"), (2, "MULTIPLE")], "SIGNIFICANT")}, ["BreachDatabaseExtractor"])
        signals["regulatory_action"] = self._make_signal("regulatory_action", "scoring_logic", {"state": self._get(breach, "regulatory_actions", default="NONE")}, ["BreachDatabaseExtractor"])
        signals["compliance_badges"] = self._make_signal("compliance_badges", "scoring_logic", {"state": self._get(insurance, "compliance_certifications", default="NONE")}, ["CyberInsuranceHistoryExtractor"])
        signals["bug_bounty"] = self._make_signal("bug_bounty", "boolean_flag", {"flag": self._get(insurance, "bug_bounty_program", default=False)}, ["CyberInsuranceHistoryExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class CyberGovernanceAggregator(DataAggregator):
    required_extractors = ["CyberGovernanceExtractor"]
    optional_extractors = ["CompanyProfileExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        gov = extractions.get("CyberGovernanceExtractor", {})
        profile = extractions.get("CompanyProfileExtractor", {})
        signals["security_leadership"] = self._make_signal("security_leadership", "scoring_logic", {"state": self._get(gov, "security_leadership_level", default="UNKNOWN")}, ["CyberGovernanceExtractor"])
        signals["ciso_present"] = self._make_signal("ciso_present", "boolean_flag", {"flag": self._get(gov, "has_ciso", default=False)}, ["CyberGovernanceExtractor"])
        signals["security_page"] = self._make_signal("security_page", "boolean_flag", {"flag": self._get(profile, "has_security_page", default=False)}, ["CompanyProfileExtractor"])
        signals["privacy_policy"] = self._make_signal("privacy_policy", "scoring_logic", {"state": self._get(profile, "privacy_policy_quality", default="UNKNOWN")}, ["CompanyProfileExtractor"])
        signals["security_txt"] = self._make_signal("security_txt", "boolean_flag", {"flag": self._get(profile, "has_security_txt", default=False)}, ["CompanyProfileExtractor"])
        signals["security_hiring"] = self._make_signal("security_hiring", "scoring_logic", {"state": self._get(gov, "security_hiring_activity", default="UNKNOWN")}, ["CyberGovernanceExtractor"])
        signals["developer_resources"] = self._make_signal("developer_resources", "scoring_logic", {"state": self._get(profile, "developer_resources_quality", default="UNKNOWN")}, ["CompanyProfileExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class CyberVendorManagementAggregator(DataAggregator):
    required_extractors = ["VendorSecurityExtractor"]
    optional_extractors = ["CreditRatingExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        vendor = extractions.get("VendorSecurityExtractor", {})
        credit = extractions.get("CreditRatingExtractor", {})
        signals["vendor_risk_program"] = self._make_signal("vendor_risk_program", "scoring_logic", {"state": self._get(vendor, "vendor_risk_program_maturity", default="UNKNOWN")}, ["VendorSecurityExtractor"])
        signals["partner_quality"] = self._make_signal("partner_quality", "scoring_logic", {"state": self._get(vendor, "partner_security_quality", default="UNKNOWN")}, ["VendorSecurityExtractor"])
        signals["customer_quality"] = self._make_signal("customer_quality", "scoring_logic", {"state": self._get(vendor, "customer_concentration_risk", default="UNKNOWN")}, ["VendorSecurityExtractor"])
        signals["financial_relationship"] = self._make_signal("financial_relationship", "quality_tier", {"entity": self._get(credit, "primary_bank", default="UNKNOWN")}, ["CreditRatingExtractor"])
        signals["certification_authority"] = self._make_signal("certification_authority", "scoring_logic", {"state": self._get(vendor, "certification_status", default="UNKNOWN")}, ["VendorSecurityExtractor"])
        signals["security_vendor"] = self._make_signal("security_vendor", "quality_tier", {"entity": self._get(vendor, "primary_security_vendor", default="UNKNOWN")}, ["VendorSecurityExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class CyberIncidentResponseAggregator(DataAggregator):
    required_extractors = ["IncidentResponseExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        ir = extractions.get("IncidentResponseExtractor", {})
        signals["ir_capabilities"] = self._make_signal("ir_capabilities", "scoring_logic", {"state": self._get(ir, "ir_maturity", default="UNKNOWN")}, ["IncidentResponseExtractor"])
        signals["exposure"] = self._make_signal("exposure", "threshold_bucket", {"value": self._get(ir, "exposure_score", default=0)}, ["IncidentResponseExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class CyberNetworkAggregator(DataAggregator):
    required_extractors = ["SecurityScorecardExtractor"]
    optional_extractors = ["IndustryAssociationExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        scorecard = extractions.get("SecurityScorecardExtractor", {})
        assoc = extractions.get("IndustryAssociationExtractor", {})
        signals["network_centrality"] = self._make_signal("network_centrality", "scoring_logic", {"state": self._get(scorecard, "network_centrality", default="UNKNOWN")}, ["SecurityScorecardExtractor"])
        signals["second_degree"] = self._make_signal("second_degree", "scoring_logic", {"state": self._get(scorecard, "second_degree_risk", default="UNKNOWN")}, ["SecurityScorecardExtractor"])
        signals["industry_body"] = self._make_signal("industry_body", "scoring_logic", {"state": self._get(assoc, "cyber_industry_membership", default="NONE")}, ["IndustryAssociationExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class CyberClassificationAggregator(DataAggregator):
    required_extractors = ["CompanyProfileExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        profile = extractions.get("CompanyProfileExtractor", {})
        signals["geography"] = self._make_signal("geography", "enumeration", {"category": self._get(profile, "headquarters_region", default="UNKNOWN")}, ["CompanyProfileExtractor"])
        signals["industry_classification"] = self._make_signal("industry_classification", "enumeration", {"category": self._get(profile, "industry_sector", default="UNKNOWN")}, ["CompanyProfileExtractor"])
        signals["size_band"] = self._make_signal("size_band", "enumeration", {"category": self._get(profile, "company_size_band", default="UNKNOWN")}, ["CompanyProfileExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class CyberFinancialAggregator(DataAggregator):
    required_extractors = ["CreditRatingExtractor"]
    optional_extractors = ["ESGMetricsExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        credit = extractions.get("CreditRatingExtractor", {})
        esg = extractions.get("ESGMetricsExtractor", {})
        signals["credit_rating"] = self._make_signal("credit_rating", "scoring_logic", {"state": self._get(credit, "rating", default="NR")}, ["CreditRatingExtractor"])
        signals["esg_cyber"] = self._make_signal("esg_cyber", "scoring_logic", {"state": self._get(esg, "cyber_governance_rating", default="NOT_RATED")}, ["ESGMetricsExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class CyberContentAggregator(DataAggregator):
    required_extractors = ["CompanyProfileExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        profile = extractions.get("CompanyProfileExtractor", {})
        signals["technical_content"] = self._make_signal("technical_content", "scoring_logic", {"state": self._get(profile, "technical_content_quality", default="UNKNOWN")}, ["CompanyProfileExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

# D&O COVERAGE - 48 SIGNALS

@register_aggregator
class DOGovernanceAggregator(DataAggregator):
    required_extractors = ["ProxyStatementExtractor"]
    optional_extractors = ["ESGMetricsExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        proxy = extractions.get("ProxyStatementExtractor", {})
        esg = extractions.get("ESGMetricsExtractor", {})
        signals["board_independence"] = self._make_signal("board_independence", "threshold_bucket", {"value": self._get(proxy, "independent_director_pct", default=0)}, ["ProxyStatementExtractor"])
        signals["board_diversity"] = self._make_signal("board_diversity", "scoring_logic", {"state": self._get(proxy, "board_diversity_status", default="UNKNOWN")}, ["ProxyStatementExtractor"])
        signals["board_refreshment"] = self._make_signal("board_refreshment", "scoring_logic", {"state": self._get(proxy, "board_refreshment_status", default="UNKNOWN")}, ["ProxyStatementExtractor"])
        signals["ceo_chair_separation"] = self._make_signal("ceo_chair_separation", "boolean_flag", {"flag": self._get(proxy, "ceo_chair_separated", default=False)}, ["ProxyStatementExtractor"])
        signals["committee_structure"] = self._make_signal("committee_structure", "scoring_logic", {"state": self._get(proxy, "committee_structure_quality", default="UNKNOWN")}, ["ProxyStatementExtractor"])
        signals["board_network"] = self._make_signal("board_network", "scoring_logic", {"state": self._get(proxy, "board_network_quality", default="UNKNOWN")}, ["ProxyStatementExtractor"])
        signals["compensation_structure"] = self._make_signal("compensation_structure", "scoring_logic", {"state": self._get(proxy, "compensation_alignment", default="UNKNOWN")}, ["ProxyStatementExtractor"])
        signals["shareholder_rights"] = self._make_signal("shareholder_rights", "scoring_logic", {"state": self._get(proxy, "shareholder_rights_status", default="UNKNOWN")}, ["ProxyStatementExtractor"])
        signals["governance_rating"] = self._make_signal("governance_rating", "scoring_logic", {"state": self._get(esg, "governance_rating", default="NOT_RATED")}, ["ESGMetricsExtractor"])
        signals["iss_governance"] = self._make_signal("iss_governance", "scoring_logic", {"state": self._get(proxy, "iss_governance_score", default="UNKNOWN")}, ["ProxyStatementExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class DOFinancialAggregator(DataAggregator):
    required_extractors = ["SECEdgarExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        sec = extractions.get("SECEdgarExtractor", {})
        signals["audit_opinion"] = self._make_signal("audit_opinion", "scoring_logic", {"state": self._get(sec, "audit_opinion", default="UNKNOWN")}, ["SECEdgarExtractor"])
        signals["auditor_quality"] = self._make_signal("auditor_quality", "quality_tier", {"entity": self._get(sec, "auditor_name", default="UNKNOWN")}, ["SECEdgarExtractor"])
        restatements = self._get(sec, "restatements_5yr", default=0)
        signals["restatement"] = self._make_signal("restatement", "scoring_logic", {"state": self._count_to_state(restatements, [(0, "CLEAN"), (1, "SINGLE"), (2, "MULTIPLE")], "SIGNIFICANT")}, ["SECEdgarExtractor"])
        signals["revenue_recognition"] = self._make_signal("revenue_recognition", "scoring_logic", {"state": self._get(sec, "revenue_recognition_risk", default="UNKNOWN")}, ["SECEdgarExtractor"])
        signals["internal_controls"] = self._make_signal("internal_controls", "scoring_logic", {"state": self._get(sec, "internal_controls_status", default="UNKNOWN")}, ["SECEdgarExtractor"])
        signals["filing_timeliness"] = self._make_signal("filing_timeliness", "scoring_logic", {"state": self._get(sec, "filing_timeliness", default="UNKNOWN")}, ["SECEdgarExtractor"])
        signals["debt_covenant"] = self._make_signal("debt_covenant", "scoring_logic", {"state": self._get(sec, "debt_covenant_status", default="UNKNOWN")}, ["SECEdgarExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class DOLitigationAggregator(DataAggregator):
    required_extractors = ["DOLitigationExtractor"]
    optional_extractors = ["SECEnforcementExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        lit = extractions.get("DOLitigationExtractor", {})
        enf = extractions.get("SECEnforcementExtractor", {})
        sec_lit = self._get(lit, "securities_litigation_5yr", default=0)
        signals["securities_litigation"] = self._make_signal("securities_litigation", "scoring_logic", {"state": self._count_to_state(sec_lit, [(0, "CLEAN"), (1, "SINGLE"), (2, "MULTIPLE")], "SIGNIFICANT")}, ["DOLitigationExtractor"])
        deriv = self._get(lit, "derivative_actions_5yr", default=0)
        signals["derivative_litigation"] = self._make_signal("derivative_litigation", "scoring_logic", {"state": self._count_to_state(deriv, [(0, "CLEAN"), (1, "SINGLE"), (2, "MULTIPLE")], "SIGNIFICANT")}, ["DOLitigationExtractor"])
        signals["pending_litigation"] = self._make_signal("pending_litigation", "scoring_logic", {"state": self._get(lit, "pending_litigation_status", default="UNKNOWN")}, ["DOLitigationExtractor"])
        signals["sec_enforcement"] = self._make_signal("sec_enforcement", "scoring_logic", {"state": self._get(enf, "enforcement_status", default="CLEAN")}, ["SECEnforcementExtractor"])
        signals["regulatory_action"] = self._make_signal("regulatory_action", "scoring_logic", {"state": self._get(enf, "regulatory_action_status", default="CLEAN")}, ["SECEnforcementExtractor"])
        signals["whistleblower"] = self._make_signal("whistleblower", "scoring_logic", {"state": self._get(lit, "whistleblower_status", default="NONE")}, ["DOLitigationExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class DOExecutiveAggregator(DataAggregator):
    required_extractors = ["ProxyStatementExtractor"]
    optional_extractors = ["CompanyProfileExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        proxy = extractions.get("ProxyStatementExtractor", {})
        profile = extractions.get("CompanyProfileExtractor", {})
        exec_changes = self._get(proxy, "executive_changes_3yr", default=0)
        signals["executive_stability"] = self._make_signal("executive_stability", "scoring_logic", {"state": "STABLE" if exec_changes == 0 else "MINOR_CHANGES" if exec_changes <= 2 else "SIGNIFICANT_CHANGES"}, ["ProxyStatementExtractor"])
        signals["executive_background"] = self._make_signal("executive_background", "scoring_logic", {"state": self._get(proxy, "executive_background_quality", default="UNKNOWN")}, ["ProxyStatementExtractor"])
        signals["cfo_quality"] = self._make_signal("cfo_quality", "scoring_logic", {"state": self._get(proxy, "cfo_quality", default="UNKNOWN")}, ["ProxyStatementExtractor"])
        signals["leadership_visibility"] = self._make_signal("leadership_visibility", "scoring_logic", {"state": self._get(profile, "leadership_visibility", default="UNKNOWN")}, ["CompanyProfileExtractor"])
        signals["hiring_signals"] = self._make_signal("hiring_signals", "scoring_logic", {"state": self._get(profile, "executive_hiring_activity", default="UNKNOWN")}, ["CompanyProfileExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class DOMarketAggregator(DataAggregator):
    required_extractors = ["InsiderActivityExtractor"]
    optional_extractors = ["SECEdgarExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        insider = extractions.get("InsiderActivityExtractor", {})
        sec = extractions.get("SECEdgarExtractor", {})
        signals["stock_volatility"] = self._make_signal("stock_volatility", "threshold_bucket", {"value": self._get(insider, "stock_volatility_90d", default=0)}, ["InsiderActivityExtractor"])
        signals["short_interest"] = self._make_signal("short_interest", "threshold_bucket", {"value": self._get(insider, "short_interest_pct", default=0)}, ["InsiderActivityExtractor"])
        signals["insider_trading"] = self._make_signal("insider_trading", "scoring_logic", {"state": self._get(insider, "insider_trading_pattern", default="UNKNOWN")}, ["InsiderActivityExtractor"])
        signals["trading_plan"] = self._make_signal("trading_plan", "boolean_flag", {"flag": self._get(insider, "has_10b5_plan", default=False)}, ["InsiderActivityExtractor"])
        signals["analyst_coverage"] = self._make_signal("analyst_coverage", "scoring_logic", {"state": self._get(sec, "analyst_coverage_level", default="UNKNOWN")}, ["SECEdgarExtractor"])
        signals["index_inclusion"] = self._make_signal("index_inclusion", "scoring_logic", {"state": self._get(sec, "index_membership", default="NONE")}, ["SECEdgarExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class DORelationshipAggregator(DataAggregator):
    required_extractors = ["DOFinancialExtractor"]
    optional_extractors = ["IndustryAssociationExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        fin = extractions.get("DOFinancialExtractor", {})
        assoc = extractions.get("IndustryAssociationExtractor", {})
        signals["banking_relationship"] = self._make_signal("banking_relationship", "quality_tier", {"entity": self._get(fin, "primary_bank", default="UNKNOWN")}, ["DOFinancialExtractor"])
        signals["legal_counsel"] = self._make_signal("legal_counsel", "quality_tier", {"entity": self._get(fin, "primary_legal_counsel", default="UNKNOWN")}, ["DOFinancialExtractor"])
        signals["investor_quality"] = self._make_signal("investor_quality", "scoring_logic", {"state": self._get(fin, "institutional_investor_quality", default="UNKNOWN")}, ["DOFinancialExtractor"])
        signals["investor_relations"] = self._make_signal("investor_relations", "scoring_logic", {"state": self._get(fin, "investor_relations_quality", default="UNKNOWN")}, ["DOFinancialExtractor"])
        signals["industry_association"] = self._make_signal("industry_association", "scoring_logic", {"state": self._get(assoc, "industry_association_membership", default="NONE")}, ["IndustryAssociationExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class DOCorporateAggregator(DataAggregator):
    required_extractors = ["CompanyProfileExtractor"]
    optional_extractors = ["ESGMetricsExtractor", "SECEdgarExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        profile = extractions.get("CompanyProfileExtractor", {})
        esg = extractions.get("ESGMetricsExtractor", {})
        sec = extractions.get("SECEdgarExtractor", {})
        signals["governance_page"] = self._make_signal("governance_page", "boolean_flag", {"flag": self._get(profile, "has_governance_page", default=False)}, ["CompanyProfileExtractor"])
        signals["press_release"] = self._make_signal("press_release", "scoring_logic", {"state": self._get(profile, "press_release_quality", default="UNKNOWN")}, ["CompanyProfileExtractor"])
        signals["related_party"] = self._make_signal("related_party", "scoring_logic", {"state": self._get(sec, "related_party_risk", default="UNKNOWN")}, ["SECEdgarExtractor"])
        signals["esg_rating"] = self._make_signal("esg_rating", "scoring_logic", {"state": self._get(esg, "overall_rating", default="NOT_RATED")}, ["ESGMetricsExtractor"])
        signals["esg_reporting"] = self._make_signal("esg_reporting", "scoring_logic", {"state": self._get(esg, "reporting_quality", default="NONE")}, ["ESGMetricsExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class DOClassificationAggregator(DataAggregator):
    required_extractors = ["SECEdgarExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        sec = extractions.get("SECEdgarExtractor", {})
        signals["company_type"] = self._make_signal("company_type", "enumeration", {"category": self._get(sec, "company_type", default="UNKNOWN")}, ["SECEdgarExtractor"])
        signals["industry"] = self._make_signal("industry", "enumeration", {"category": self._get(sec, "sic_industry", default="UNKNOWN")}, ["SECEdgarExtractor"])
        signals["stock_exchange"] = self._make_signal("stock_exchange", "enumeration", {"category": self._get(sec, "stock_exchange", default="UNKNOWN")}, ["SECEdgarExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class DOCreditAggregator(DataAggregator):
    required_extractors = ["CreditRatingExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        credit = extractions.get("CreditRatingExtractor", {})
        signals["credit_rating"] = self._make_signal("credit_rating", "scoring_logic", {"state": self._get(credit, "rating", default="NR")}, ["CreditRatingExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

# ENERGY COVERAGE - 47 SIGNALS

@register_aggregator
class EnergySafetyPerformanceAggregator(DataAggregator):
    required_extractors = ["OSHASafetyExtractor"]
    optional_extractors = ["CompanyProfileExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        osha = extractions.get("OSHASafetyExtractor", {})
        profile = extractions.get("CompanyProfileExtractor", {})
        signals["osha_trir"] = self._make_signal("osha_trir", "threshold_bucket", {"value": self._get(osha, "trir", default=0.0)}, ["OSHASafetyExtractor"])
        violations = self._get(osha, "violations_3yr", default=0)
        signals["osha_violations"] = self._make_signal("osha_violations", "scoring_logic", {"state": self._count_to_state(violations, [(0, "CLEAN"), (2, "LOW"), (5, "MODERATE")], "HIGH")}, ["OSHASafetyExtractor"])
        fatalities = self._get(osha, "fatalities_5yr", default=0)
        signals["fatality"] = self._make_signal("fatality", "scoring_logic", {"state": "CLEAN" if fatalities == 0 else "SINGLE" if fatalities == 1 else "MULTIPLE"}, ["OSHASafetyExtractor"])
        signals["near_miss"] = self._make_signal("near_miss", "scoring_logic", {"state": self._get(osha, "near_miss_reporting", default="UNKNOWN")}, ["OSHASafetyExtractor"])
        signals["process_safety"] = self._make_signal("process_safety", "scoring_logic", {"state": self._get(osha, "process_safety_status", default="UNKNOWN")}, ["OSHASafetyExtractor"])
        major = self._get(osha, "major_incidents_5yr", default=0)
        signals["major_incident"] = self._make_signal("major_incident", "scoring_logic", {"state": self._count_to_state(major, [(0, "CLEAN"), (1, "SINGLE"), (2, "MULTIPLE")], "SIGNIFICANT")}, ["OSHASafetyExtractor"])
        bsee = self._get(osha, "bsee_incidents_3yr", default=0)
        signals["bsee_incident"] = self._make_signal("bsee_incident", "scoring_logic", {"state": self._count_to_state(bsee, [(0, "CLEAN"), (2, "LOW"), (5, "MODERATE")], "HIGH")}, ["OSHASafetyExtractor"])
        signals["hse_leadership"] = self._make_signal("hse_leadership", "scoring_logic", {"state": self._get(profile, "hse_leadership_quality", default="UNKNOWN")}, ["CompanyProfileExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class EnergyEnvironmentalComplianceAggregator(DataAggregator):
    required_extractors = ["EPAComplianceExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        epa = extractions.get("EPAComplianceExtractor", {})
        violations = self._get(epa, "violations_5yr", default=0)
        signals["epa_violation"] = self._make_signal("epa_violation", "scoring_logic", {"state": self._count_to_state(violations, [(0, "CLEAN"), (2, "LOW"), (5, "MODERATE")], "HIGH")}, ["EPAComplianceExtractor"])
        spills = self._get(epa, "reportable_spills_5yr", default=0)
        signals["spill_history"] = self._make_signal("spill_history", "scoring_logic", {"state": self._count_to_state(spills, [(0, "CLEAN"), (2, "LOW"), (5, "MODERATE")], "HIGH")}, ["EPAComplianceExtractor"])
        signals["emissions_compliance"] = self._make_signal("emissions_compliance", "scoring_logic", {"state": self._get(epa, "emissions_compliance_status", default="UNKNOWN")}, ["EPAComplianceExtractor"])
        signals["flaring"] = self._make_signal("flaring", "scoring_logic", {"state": self._get(epa, "flaring_status", default="UNKNOWN")}, ["EPAComplianceExtractor"])
        signals["methane"] = self._make_signal("methane", "scoring_logic", {"state": self._get(epa, "methane_management", default="UNKNOWN")}, ["EPAComplianceExtractor"])
        signals["remediation"] = self._make_signal("remediation", "scoring_logic", {"state": self._get(epa, "remediation_status", default="UNKNOWN")}, ["EPAComplianceExtractor"])
        signals["permit_status"] = self._make_signal("permit_status", "scoring_logic", {"state": self._get(epa, "permit_compliance", default="UNKNOWN")}, ["EPAComplianceExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class EnergyOperationalQualityAggregator(DataAggregator):
    required_extractors = ["ProductionDataExtractor"]
    optional_extractors = ["WellIntegrityExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        prod = extractions.get("ProductionDataExtractor", {})
        well = extractions.get("WellIntegrityExtractor", {})
        signals["operational_efficiency"] = self._make_signal("operational_efficiency", "threshold_bucket", {"value": self._get(prod, "operational_efficiency_pct", default=0)}, ["ProductionDataExtractor"])
        signals["production_consistency"] = self._make_signal("production_consistency", "scoring_logic", {"state": self._get(prod, "production_consistency", default="UNKNOWN")}, ["ProductionDataExtractor"])
        signals["maintenance_pattern"] = self._make_signal("maintenance_pattern", "scoring_logic", {"state": self._get(prod, "maintenance_pattern", default="UNKNOWN")}, ["ProductionDataExtractor"])
        signals["well_integrity"] = self._make_signal("well_integrity", "scoring_logic", {"state": self._get(well, "integrity_status", default="UNKNOWN")}, ["WellIntegrityExtractor"])
        signals["facility_activity"] = self._make_signal("facility_activity", "scoring_logic", {"state": self._get(prod, "facility_activity_level", default="UNKNOWN")}, ["ProductionDataExtractor"])
        signals["contractor_quality"] = self._make_signal("contractor_quality", "scoring_logic", {"state": self._get(prod, "contractor_quality", default="UNKNOWN")}, ["ProductionDataExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class EnergyAssetQualityAggregator(DataAggregator):
    required_extractors = ["ReserveDataExtractor"]
    optional_extractors = ["ProductionDataExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        reserve = extractions.get("ReserveDataExtractor", {})
        prod = extractions.get("ProductionDataExtractor", {})
        signals["asset_age"] = self._make_signal("asset_age", "threshold_bucket", {"value": self._get(reserve, "average_asset_age", default=0)}, ["ReserveDataExtractor"])
        signals["complexity"] = self._make_signal("complexity", "scoring_logic", {"state": self._get(reserve, "operational_complexity", default="UNKNOWN")}, ["ReserveDataExtractor"])
        signals["concentration"] = self._make_signal("concentration", "scoring_logic", {"state": self._get(reserve, "asset_concentration", default="UNKNOWN")}, ["ReserveDataExtractor"])
        signals["decommissioning"] = self._make_signal("decommissioning", "scoring_logic", {"state": self._get(reserve, "decommissioning_liability_status", default="UNKNOWN")}, ["ReserveDataExtractor"])
        signals["benchmark"] = self._make_signal("benchmark", "scoring_logic", {"state": self._get(prod, "production_benchmark", default="UNKNOWN")}, ["ProductionDataExtractor"])
        signals["aro_coverage"] = self._make_signal("aro_coverage", "scoring_logic", {"state": self._get(reserve, "aro_funding_status", default="UNKNOWN")}, ["ReserveDataExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class EnergyFinancialStabilityAggregator(DataAggregator):
    required_extractors = ["EnergyFinancialExtractor"]
    optional_extractors = ["CreditRatingExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        fin = extractions.get("EnergyFinancialExtractor", {})
        credit = extractions.get("CreditRatingExtractor", {})
        signals["credit_rating"] = self._make_signal("credit_rating", "scoring_logic", {"state": self._get(credit, "rating", default=self._get(fin, "credit_rating", default="NR"))}, ["CreditRatingExtractor"])
        signals["leverage"] = self._make_signal("leverage", "threshold_bucket", {"value": self._get(fin, "debt_to_ebitda", default=0)}, ["EnergyFinancialExtractor"])
        signals["capex_trend"] = self._make_signal("capex_trend", "scoring_logic", {"state": self._get(fin, "capex_trend", default="UNKNOWN")}, ["EnergyFinancialExtractor"])
        signals["restructuring"] = self._make_signal("restructuring", "scoring_logic", {"state": self._get(fin, "restructuring_status", default="NONE")}, ["EnergyFinancialExtractor"])
        signals["insurance_history"] = self._make_signal("insurance_history", "scoring_logic", {"state": self._get(fin, "insurance_claims_history", default="UNKNOWN")}, ["EnergyFinancialExtractor"])
        signals["credit"] = self._make_signal("credit", "scoring_logic", {"state": self._get(fin, "credit_facility_status", default="UNKNOWN")}, ["EnergyFinancialExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class EnergyESGAggregator(DataAggregator):
    required_extractors = ["ESGMetricsExtractor"]
    optional_extractors = ["CompanyProfileExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        esg = extractions.get("ESGMetricsExtractor", {})
        profile = extractions.get("CompanyProfileExtractor", {})
        signals["esg_rating"] = self._make_signal("esg_rating", "scoring_logic", {"state": self._get(esg, "overall_rating", default="NOT_RATED")}, ["ESGMetricsExtractor"])
        signals["esg_reporting"] = self._make_signal("esg_reporting", "scoring_logic", {"state": self._get(esg, "reporting_quality", default="NONE")}, ["ESGMetricsExtractor"])
        signals["disclosure_quality"] = self._make_signal("disclosure_quality", "scoring_logic", {"state": self._get(profile, "disclosure_quality", default="UNKNOWN")}, ["CompanyProfileExtractor"])
        signals["safety_communication"] = self._make_signal("safety_communication", "scoring_logic", {"state": self._get(profile, "safety_communication_quality", default="UNKNOWN")}, ["CompanyProfileExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class EnergyRelationshipAggregator(DataAggregator):
    required_extractors = ["EnergyFinancialExtractor"]
    optional_extractors = ["IndustryAssociationExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        fin = extractions.get("EnergyFinancialExtractor", {})
        assoc = extractions.get("IndustryAssociationExtractor", {})
        signals["banking_relationship"] = self._make_signal("banking_relationship", "quality_tier", {"entity": self._get(fin, "primary_bank", default="UNKNOWN")}, ["EnergyFinancialExtractor"])
        signals["partner_quality"] = self._make_signal("partner_quality", "scoring_logic", {"state": self._get(fin, "jv_partner_quality", default="UNKNOWN")}, ["EnergyFinancialExtractor"])
        signals["customer_quality"] = self._make_signal("customer_quality", "scoring_logic", {"state": self._get(fin, "offtake_counterparty_quality", default="UNKNOWN")}, ["EnergyFinancialExtractor"])
        signals["regulator_relationship"] = self._make_signal("regulator_relationship", "scoring_logic", {"state": self._get(fin, "regulator_relationship", default="UNKNOWN")}, ["EnergyFinancialExtractor"])
        signals["industry_association"] = self._make_signal("industry_association", "scoring_logic", {"state": self._get(assoc, "api_membership", default="NONE")}, ["IndustryAssociationExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class EnergyCorporateAggregator(DataAggregator):
    required_extractors = ["CompanyProfileExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        profile = extractions.get("CompanyProfileExtractor", {})
        signals["industry_presence"] = self._make_signal("industry_presence", "scoring_logic", {"state": self._get(profile, "industry_presence", default="UNKNOWN")}, ["CompanyProfileExtractor"])
        signals["technical_hiring"] = self._make_signal("technical_hiring", "scoring_logic", {"state": self._get(profile, "technical_hiring_activity", default="UNKNOWN")}, ["CompanyProfileExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class EnergyClassificationAggregator(DataAggregator):
    required_extractors = ["ProductionDataExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        prod = extractions.get("ProductionDataExtractor", {})
        signals["operator_type"] = self._make_signal("operator_type", "enumeration", {"category": self._get(prod, "operator_type", default="UNKNOWN")}, ["ProductionDataExtractor"])
        signals["operation_segment"] = self._make_signal("operation_segment", "enumeration", {"category": self._get(prod, "operation_segment", default="UNKNOWN")}, ["ProductionDataExtractor"])
        signals["geographic_focus"] = self._make_signal("geographic_focus", "enumeration", {"category": self._get(prod, "geographic_focus", default="UNKNOWN")}, ["ProductionDataExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)


# FINANCIAL INSTITUTIONS COVERAGE - 51 SIGNALS

@register_aggregator
class FIRegulatoryComplianceAggregator(DataAggregator):
    required_extractors = ["BankRegulatoryExtractor"]
    optional_extractors = ["BSAAMLExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        reg = extractions.get("BankRegulatoryExtractor", {})
        bsa = extractions.get("BSAAMLExtractor", {})
        signals["examination_rating"] = self._make_signal("examination_rating", "scoring_logic", {"state": self._get(reg, "examination_rating", default="UNKNOWN")}, ["BankRegulatoryExtractor"])
        signals["enforcement_action"] = self._make_signal("enforcement_action", "scoring_logic", {"state": self._get(reg, "enforcement_action_status", default="CLEAN")}, ["BankRegulatoryExtractor"])
        signals["informal_action"] = self._make_signal("informal_action", "scoring_logic", {"state": self._get(reg, "informal_action_status", default="CLEAN")}, ["BankRegulatoryExtractor"])
        signals["bsa_aml"] = self._make_signal("bsa_aml", "scoring_logic", {"state": self._get(bsa, "bsa_aml_status", default="UNKNOWN")}, ["BSAAMLExtractor"])
        signals["consumer_compliance"] = self._make_signal("consumer_compliance", "scoring_logic", {"state": self._get(reg, "consumer_compliance_rating", default="UNKNOWN")}, ["BankRegulatoryExtractor"])
        signals["fair_lending"] = self._make_signal("fair_lending", "scoring_logic", {"state": self._get(reg, "fair_lending_status", default="UNKNOWN")}, ["BankRegulatoryExtractor"])
        signals["cra_rating"] = self._make_signal("cra_rating", "scoring_logic", {"state": self._get(reg, "cra_rating", default="UNKNOWN")}, ["BankRegulatoryExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class FIFinancialConditionAggregator(DataAggregator):
    required_extractors = ["FFIECCallReportExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        call = extractions.get("FFIECCallReportExtractor", {})
        signals["capital_ratio"] = self._make_signal("capital_ratio", "threshold_bucket", {"value": self._get(call, "tier1_capital_ratio", default=0)}, ["FFIECCallReportExtractor"])
        signals["liquidity"] = self._make_signal("liquidity", "scoring_logic", {"state": self._get(call, "liquidity_status", default="UNKNOWN")}, ["FFIECCallReportExtractor"])
        signals["earnings"] = self._make_signal("earnings", "scoring_logic", {"state": self._get(call, "earnings_quality", default="UNKNOWN")}, ["FFIECCallReportExtractor"])
        signals["interest_rate_risk"] = self._make_signal("interest_rate_risk", "scoring_logic", {"state": self._get(call, "interest_rate_risk", default="UNKNOWN")}, ["FFIECCallReportExtractor"])
        signals["growth_rate"] = self._make_signal("growth_rate", "threshold_bucket", {"value": self._get(call, "asset_growth_rate", default=0)}, ["FFIECCallReportExtractor"])
        signals["peer_benchmark"] = self._make_signal("peer_benchmark", "scoring_logic", {"state": self._get(call, "peer_comparison", default="UNKNOWN")}, ["FFIECCallReportExtractor"])
        signals["concentration"] = self._make_signal("concentration", "scoring_logic", {"state": self._get(call, "concentration_risk", default="UNKNOWN")}, ["FFIECCallReportExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class FICreditQualityAggregator(DataAggregator):
    required_extractors = ["CreditPortfolioExtractor"]
    optional_extractors = ["CreditRatingExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        portfolio = extractions.get("CreditPortfolioExtractor", {})
        credit = extractions.get("CreditRatingExtractor", {})
        signals["asset_quality"] = self._make_signal("asset_quality", "scoring_logic", {"state": self._get(portfolio, "asset_quality_status", default="UNKNOWN")}, ["CreditPortfolioExtractor"])
        signals["credit_rating"] = self._make_signal("credit_rating", "scoring_logic", {"state": self._get(credit, "rating", default="NR")}, ["CreditRatingExtractor"])
        signals["credit_rating_structured"] = self._make_signal("credit_rating_structured", "scoring_logic", {"state": self._get(credit, "structured_rating", default="NR")}, ["CreditRatingExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class FIOperationalRiskAggregator(DataAggregator):
    required_extractors = ["FIOperationalRiskExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        ops = extractions.get("FIOperationalRiskExtractor", {})
        incidents = self._get(ops, "operational_incidents_3yr", default=0)
        signals["operational_incident"] = self._make_signal("operational_incident", "scoring_logic", {"state": self._count_to_state(incidents, [(0, "CLEAN"), (2, "LOW"), (5, "MODERATE")], "HIGH")}, ["FIOperationalRiskExtractor"])
        signals["network_exposure"] = self._make_signal("network_exposure", "scoring_logic", {"state": self._get(ops, "network_exposure_level", default="UNKNOWN")}, ["FIOperationalRiskExtractor"])
        signals["clearing_relationship"] = self._make_signal("clearing_relationship", "quality_tier", {"entity": self._get(ops, "clearing_bank", default="UNKNOWN")}, ["FIOperationalRiskExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class FICybersecurityAggregator(DataAggregator):
    required_extractors = ["FICyberExtractor"]
    optional_extractors = ["TechnicalScanExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        cyber = extractions.get("FICyberExtractor", {})
        tech = extractions.get("TechnicalScanExtractor", {})
        signals["security_rating"] = self._make_signal("security_rating", "threshold_bucket", {"value": self._get(cyber, "security_score", default=0)}, ["FICyberExtractor"])
        signals["tls_score"] = self._make_signal("tls_score", "scoring_logic", {"state": self._get(tech, "tls_grade", default="UNKNOWN")}, ["TechnicalScanExtractor"])
        signals["email_auth"] = self._make_signal("email_auth", "scoring_logic", {"state": self._get(tech, "email_auth_status", default="UNKNOWN")}, ["TechnicalScanExtractor"])
        signals["security_headers"] = self._make_signal("security_headers", "scoring_logic", {"state": self._get(tech, "security_headers_status", default="UNKNOWN")}, ["TechnicalScanExtractor"])
        signals["security_page"] = self._make_signal("security_page", "boolean_flag", {"flag": self._get(cyber, "has_security_page", default=False)}, ["FICyberExtractor"])
        signals["vulnerability"] = self._make_signal("vulnerability", "scoring_logic", {"state": self._get(cyber, "vulnerability_status", default="UNKNOWN")}, ["FICyberExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class FIGovernanceAggregator(DataAggregator):
    required_extractors = ["FIGovernanceExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        gov = extractions.get("FIGovernanceExtractor", {})
        signals["board_independence"] = self._make_signal("board_independence", "threshold_bucket", {"value": self._get(gov, "independent_director_pct", default=0)}, ["FIGovernanceExtractor"])
        signals["board_expertise"] = self._make_signal("board_expertise", "scoring_logic", {"state": self._get(gov, "board_expertise_level", default="UNKNOWN")}, ["FIGovernanceExtractor"])
        signals["audit_committee"] = self._make_signal("audit_committee", "scoring_logic", {"state": self._get(gov, "audit_committee_quality", default="UNKNOWN")}, ["FIGovernanceExtractor"])
        signals["risk_committee"] = self._make_signal("risk_committee", "scoring_logic", {"state": self._get(gov, "risk_committee_quality", default="UNKNOWN")}, ["FIGovernanceExtractor"])
        exec_changes = self._get(gov, "executive_changes_3yr", default=0)
        signals["executive_stability"] = self._make_signal("executive_stability", "scoring_logic", {"state": "STABLE" if exec_changes == 0 else "MINOR_CHANGES" if exec_changes <= 2 else "SIGNIFICANT_CHANGES"}, ["FIGovernanceExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class FILitigationAggregator(DataAggregator):
    required_extractors = ["FILitigationExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        lit = extractions.get("FILitigationExtractor", {})
        cases = self._get(lit, "litigation_cases_5yr", default=0)
        signals["litigation"] = self._make_signal("litigation", "scoring_logic", {"state": self._count_to_state(cases, [(0, "CLEAN"), (2, "LOW"), (5, "MODERATE")], "HIGH")}, ["FILitigationExtractor"])
        cfpb = self._get(lit, "cfpb_complaints_12m", default=0)
        signals["cfpb_complaint"] = self._make_signal("cfpb_complaint", "scoring_logic", {"state": self._count_to_state(cfpb, [(10, "LOW"), (50, "MODERATE"), (100, "ELEVATED")], "HIGH")}, ["FILitigationExtractor"])
        bbb = self._get(lit, "bbb_complaints_12m", default=0)
        signals["bbb_complaint"] = self._make_signal("bbb_complaint", "scoring_logic", {"state": self._count_to_state(bbb, [(5, "LOW"), (20, "MODERATE"), (50, "ELEVATED")], "HIGH")}, ["FILitigationExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class FIRelationshipAggregator(DataAggregator):
    required_extractors = ["FFIECCallReportExtractor"]
    optional_extractors = ["IndustryAssociationExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        call = extractions.get("FFIECCallReportExtractor", {})
        assoc = extractions.get("IndustryAssociationExtractor", {})
        signals["correspondent_quality"] = self._make_signal("correspondent_quality", "quality_tier", {"entity": self._get(call, "correspondent_bank", default="UNKNOWN")}, ["FFIECCallReportExtractor"])
        signals["fhlb_membership"] = self._make_signal("fhlb_membership", "boolean_flag", {"flag": self._get(call, "fhlb_member", default=False)}, ["FFIECCallReportExtractor"])
        signals["legal_counsel"] = self._make_signal("legal_counsel", "quality_tier", {"entity": self._get(call, "primary_legal_counsel", default="UNKNOWN")}, ["FFIECCallReportExtractor"])
        signals["investor_relations"] = self._make_signal("investor_relations", "scoring_logic", {"state": self._get(call, "investor_relations_quality", default="UNKNOWN")}, ["FFIECCallReportExtractor"])
        signals["industry_association"] = self._make_signal("industry_association", "scoring_logic", {"state": self._get(assoc, "aba_membership", default="NONE")}, ["IndustryAssociationExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class FICorporateAggregator(DataAggregator):
    required_extractors = ["CompanyProfileExtractor"]
    optional_extractors = ["BreachDatabaseExtractor", "SECEdgarExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        profile = extractions.get("CompanyProfileExtractor", {})
        breach = extractions.get("BreachDatabaseExtractor", {})
        sec = extractions.get("SECEdgarExtractor", {})
        signals["disclosure_quality"] = self._make_signal("disclosure_quality", "scoring_logic", {"state": self._get(profile, "disclosure_quality", default="UNKNOWN")}, ["CompanyProfileExtractor"])
        signals["community_presence"] = self._make_signal("community_presence", "scoring_logic", {"state": self._get(profile, "community_presence", default="UNKNOWN")}, ["CompanyProfileExtractor"])
        signals["hiring_signals"] = self._make_signal("hiring_signals", "scoring_logic", {"state": self._get(profile, "hiring_activity", default="UNKNOWN")}, ["CompanyProfileExtractor"])
        signals["related_party"] = self._make_signal("related_party", "scoring_logic", {"state": self._get(sec, "related_party_risk", default="UNKNOWN")}, ["SECEdgarExtractor"])
        breaches = self._get(breach, "breaches_5yr", default=0)
        signals["breach_history"] = self._make_signal("breach_history", "scoring_logic", {"state": self._count_to_state(breaches, [(0, "CLEAN"), (1, "SINGLE"), (2, "MULTIPLE")], "SIGNIFICANT")}, ["BreachDatabaseExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class FIESGAggregator(DataAggregator):
    required_extractors = ["ESGMetricsExtractor"]
    optional_extractors = ["SECEdgarExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        esg = extractions.get("ESGMetricsExtractor", {})
        sec = extractions.get("SECEdgarExtractor", {})
        signals["esg_rating"] = self._make_signal("esg_rating", "scoring_logic", {"state": self._get(esg, "overall_rating", default="NOT_RATED")}, ["ESGMetricsExtractor"])
        signals["esg_reporting"] = self._make_signal("esg_reporting", "scoring_logic", {"state": self._get(esg, "reporting_quality", default="NONE")}, ["ESGMetricsExtractor"])
        signals["auditor_quality"] = self._make_signal("auditor_quality", "quality_tier", {"entity": self._get(sec, "auditor_name", default="UNKNOWN")}, ["SECEdgarExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class FIClassificationAggregator(DataAggregator):
    required_extractors = ["FFIECCallReportExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        call = extractions.get("FFIECCallReportExtractor", {})
        signals["institution_type"] = self._make_signal("institution_type", "enumeration", {"category": self._get(call, "institution_type", default="UNKNOWN")}, ["FFIECCallReportExtractor"])
        signals["asset_size_band"] = self._make_signal("asset_size_band", "enumeration", {"category": self._get(call, "asset_size_band", default="UNKNOWN")}, ["FFIECCallReportExtractor"])
        signals["publicly_traded"] = self._make_signal("publicly_traded", "boolean_flag", {"flag": self._get(call, "publicly_traded", default=False)}, ["FFIECCallReportExtractor"])
        signals["regulatory_framework"] = self._make_signal("regulatory_framework", "enumeration", {"category": self._get(call, "primary_regulator", default="UNKNOWN")}, ["FFIECCallReportExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)


# PROFESSIONAL INDEMNITY COVERAGE - 44 SIGNALS

@register_aggregator
class PIRegulatoryStandingAggregator(DataAggregator):
    required_extractors = ["StateBarExtractor"]
    optional_extractors = ["PeerReviewExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        bar = extractions.get("StateBarExtractor", {})
        peer = extractions.get("PeerReviewExtractor", {})
        signals["license_status"] = self._make_signal("license_status", "scoring_logic", {"state": self._get(bar, "license_status", default="UNKNOWN")}, ["StateBarExtractor"])
        disciplinary = self._get(bar, "disciplinary_actions", default=0)
        signals["disciplinary_history"] = self._make_signal("disciplinary_history", "scoring_logic", {"state": self._count_to_state(disciplinary, [(0, "CLEAN"), (1, "SINGLE"), (2, "MULTIPLE")], "SIGNIFICANT")}, ["StateBarExtractor"])
        malpractice = self._get(bar, "malpractice_judgments", default=0)
        signals["malpractice_record"] = self._make_signal("malpractice_record", "scoring_logic", {"state": self._count_to_state(malpractice, [(0, "CLEAN"), (1, "SINGLE"), (2, "MULTIPLE")], "SIGNIFICANT")}, ["StateBarExtractor"])
        signals["ce_compliance"] = self._make_signal("ce_compliance", "scoring_logic", {"state": self._get(bar, "ce_compliance_status", default="UNKNOWN")}, ["StateBarExtractor"])
        signals["specialty_certification"] = self._make_signal("specialty_certification", "scoring_logic", {"state": self._get(bar, "specialty_certification", default="NONE")}, ["StateBarExtractor"])
        signals["peer_review"] = self._make_signal("peer_review", "scoring_logic", {"state": self._get(peer, "peer_review_status", default="UNKNOWN")}, ["PeerReviewExtractor"])
        signals["pcaob_standing"] = self._make_signal("pcaob_standing", "scoring_logic", {"state": self._get(peer, "pcaob_standing", default="NOT_APPLICABLE")}, ["PeerReviewExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class PIClaimsHistoryAggregator(DataAggregator):
    required_extractors = ["MalpracticeClaimsExtractor"]
    optional_extractors = ["StateRegulatoryExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        claims = extractions.get("MalpracticeClaimsExtractor", {})
        reg = extractions.get("StateRegulatoryExtractor", {})
        suits = self._get(claims, "malpractice_suits_5yr", default=0)
        signals["malpractice_suits"] = self._make_signal("malpractice_suits", "scoring_logic", {"state": self._count_to_state(suits, [(0, "CLEAN"), (1, "SINGLE"), (2, "MULTIPLE")], "SIGNIFICANT")}, ["MalpracticeClaimsExtractor"])
        complaints = self._get(claims, "complaints_3yr", default=0)
        signals["complaint_history"] = self._make_signal("complaint_history", "scoring_logic", {"state": self._count_to_state(complaints, [(0, "CLEAN"), (2, "LOW"), (5, "MODERATE")], "HIGH")}, ["MalpracticeClaimsExtractor"])
        fee_disputes = self._get(claims, "fee_disputes_3yr", default=0)
        signals["fee_dispute"] = self._make_signal("fee_dispute", "scoring_logic", {"state": self._count_to_state(fee_disputes, [(0, "CLEAN"), (2, "LOW"), (5, "MODERATE")], "HIGH")}, ["MalpracticeClaimsExtractor"])
        fee_lit = self._get(claims, "fee_dispute_litigation", default=0)
        signals["fee_disputes_litigation"] = self._make_signal("fee_disputes_litigation", "scoring_logic", {"state": self._count_to_state(fee_lit, [(0, "CLEAN"), (1, "SINGLE"), (2, "MULTIPLE")], "SIGNIFICANT")}, ["MalpracticeClaimsExtractor"])
        civil = self._get(claims, "civil_litigation_5yr", default=0)
        signals["civil_litigation"] = self._make_signal("civil_litigation", "scoring_logic", {"state": self._count_to_state(civil, [(0, "CLEAN"), (1, "SINGLE"), (3, "MULTIPLE")], "SIGNIFICANT")}, ["MalpracticeClaimsExtractor"])
        signals["regulatory_enforcement"] = self._make_signal("regulatory_enforcement", "scoring_logic", {"state": self._get(reg, "enforcement_status", default="CLEAN")}, ["StateRegulatoryExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class PIFirmStabilityAggregator(DataAggregator):
    required_extractors = ["FirmStabilityExtractor"]
    optional_extractors = ["PIFinancialExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        firm = extractions.get("FirmStabilityExtractor", {})
        fin = extractions.get("PIFinancialExtractor", {})
        partner_turnover = self._get(firm, "partner_turnover_3yr", default=0)
        signals["partner_stability"] = self._make_signal("partner_stability", "scoring_logic", {"state": self._value_to_state(partner_turnover, [(5, "STABLE"), (15, "MODERATE"), (25, "VOLATILE")], "HIGHLY_VOLATILE")}, ["FirmStabilityExtractor"])
        signals["staff_retention"] = self._make_signal("staff_retention", "scoring_logic", {"state": self._get(firm, "staff_retention_status", default="UNKNOWN")}, ["FirmStabilityExtractor"])
        signals["office_stability"] = self._make_signal("office_stability", "scoring_logic", {"state": self._get(firm, "office_stability", default="UNKNOWN")}, ["FirmStabilityExtractor"])
        signals["tenure"] = self._make_signal("tenure", "threshold_bucket", {"value": self._get(firm, "average_partner_tenure", default=0)}, ["FirmStabilityExtractor"])
        signals["succession_planning"] = self._make_signal("succession_planning", "scoring_logic", {"state": self._get(firm, "succession_planning_status", default="UNKNOWN")}, ["FirmStabilityExtractor"])
        signals["financial_stability"] = self._make_signal("financial_stability", "scoring_logic", {"state": self._get(fin, "financial_health", default="UNKNOWN")}, ["PIFinancialExtractor"])
        signals["bankruptcy"] = self._make_signal("bankruptcy", "boolean_flag", {"flag": self._get(fin, "bankruptcy_history", default=False)}, ["PIFinancialExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class PIQualityManagementAggregator(DataAggregator):
    required_extractors = ["QualityManagementExtractor"]
    optional_extractors = ["CompanyProfileExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        quality = extractions.get("QualityManagementExtractor", {})
        profile = extractions.get("CompanyProfileExtractor", {})
        signals["work_quality"] = self._make_signal("work_quality", "scoring_logic", {"state": self._get(quality, "work_quality_rating", default="UNKNOWN")}, ["QualityManagementExtractor"])
        signals["outcome_patterns"] = self._make_signal("outcome_patterns", "scoring_logic", {"state": self._get(quality, "case_outcome_pattern", default="UNKNOWN")}, ["QualityManagementExtractor"])
        signals["practice_clarity"] = self._make_signal("practice_clarity", "scoring_logic", {"state": self._get(quality, "practice_area_clarity", default="UNKNOWN")}, ["QualityManagementExtractor"])
        signals["diversity"] = self._make_signal("diversity", "scoring_logic", {"state": self._get(profile, "diversity_status", default="UNKNOWN")}, ["CompanyProfileExtractor"])
        signals["bio_completeness"] = self._make_signal("bio_completeness", "scoring_logic", {"state": self._get(profile, "bio_completeness", default="UNKNOWN")}, ["CompanyProfileExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class PIClientQualityAggregator(DataAggregator):
    required_extractors = ["ClientQualityExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        client = extractions.get("ClientQualityExtractor", {})
        signals["client_quality"] = self._make_signal("client_quality", "scoring_logic", {"state": self._get(client, "client_quality_tier", default="UNKNOWN")}, ["ClientQualityExtractor"])
        signals["client_reviews"] = self._make_signal("client_reviews", "scoring_logic", {"state": self._get(client, "client_review_sentiment", default="UNKNOWN")}, ["ClientQualityExtractor"])
        signals["referral_network"] = self._make_signal("referral_network", "scoring_logic", {"state": self._get(client, "referral_network_strength", default="UNKNOWN")}, ["ClientQualityExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class PINetworkAuthorityAggregator(DataAggregator):
    required_extractors = ["PINetworkAuthorityExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        network = extractions.get("PINetworkAuthorityExtractor", {})
        signals["peer_ranking"] = self._make_signal("peer_ranking", "scoring_logic", {"state": self._get(network, "peer_ranking_tier", default="UNKNOWN")}, ["PINetworkAuthorityExtractor"])
        signals["association_leadership"] = self._make_signal("association_leadership", "scoring_logic", {"state": self._get(network, "association_leadership", default="NONE")}, ["PINetworkAuthorityExtractor"])
        signals["thought_leadership"] = self._make_signal("thought_leadership", "scoring_logic", {"state": self._get(network, "thought_leadership_level", default="UNKNOWN")}, ["PINetworkAuthorityExtractor"])
        signals["publications"] = self._make_signal("publications", "scoring_logic", {"state": self._get(network, "publication_activity", default="NONE")}, ["PINetworkAuthorityExtractor"])
        signals["panel_membership"] = self._make_signal("panel_membership", "scoring_logic", {"state": self._get(network, "panel_membership_status", default="NONE")}, ["PINetworkAuthorityExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class PIProfessionalDevelopmentAggregator(DataAggregator):
    required_extractors = ["ProfessionalDevelopmentExtractor"]
    optional_extractors = ["CompanyProfileExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        dev = extractions.get("ProfessionalDevelopmentExtractor", {})
        profile = extractions.get("CompanyProfileExtractor", {})
        signals["community_involvement"] = self._make_signal("community_involvement", "scoring_logic", {"state": self._get(dev, "community_involvement_level", default="UNKNOWN")}, ["ProfessionalDevelopmentExtractor"])
        web_score = self._get(profile, "website_quality_score", default=50)
        signals["website_quality"] = self._make_signal("website_quality", "scoring_logic", {"state": self._value_to_state(web_score, [(30, "POOR"), (50, "BASIC"), (70, "GOOD")], "EXCELLENT")}, ["CompanyProfileExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class PICybersecurityAggregator(DataAggregator):
    required_extractors = ["TechnicalScanExtractor"]
    optional_extractors = ["BreachDatabaseExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        tech = extractions.get("TechnicalScanExtractor", {})
        breach = extractions.get("BreachDatabaseExtractor", {})
        signals["tls_score"] = self._make_signal("tls_score", "scoring_logic", {"state": self._get(tech, "tls_grade", default="UNKNOWN")}, ["TechnicalScanExtractor"])
        signals["email_auth"] = self._make_signal("email_auth", "scoring_logic", {"state": self._get(tech, "email_auth_status", default="UNKNOWN")}, ["TechnicalScanExtractor"])
        signals["security_headers"] = self._make_signal("security_headers", "scoring_logic", {"state": self._get(tech, "security_headers_status", default="UNKNOWN")}, ["TechnicalScanExtractor"])
        signals["portal_security"] = self._make_signal("portal_security", "scoring_logic", {"state": self._get(tech, "client_portal_security", default="UNKNOWN")}, ["TechnicalScanExtractor"])
        breaches = self._get(breach, "breaches_5yr", default=0)
        signals["breach_history"] = self._make_signal("breach_history", "scoring_logic", {"state": self._count_to_state(breaches, [(0, "CLEAN"), (1, "SINGLE"), (2, "MULTIPLE")], "SIGNIFICANT")}, ["BreachDatabaseExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

@register_aggregator
class PIClassificationAggregator(DataAggregator):
    required_extractors = ["FirmStabilityExtractor"]

    def aggregate(self, extractions: Dict[str, Dict[str, Any]]) -> AggregationResult:
        signals = {}
        firm = extractions.get("FirmStabilityExtractor", {})
        signals["profession_type"] = self._make_signal("profession_type", "enumeration", {"category": self._get(firm, "profession_type", default="UNKNOWN")}, ["FirmStabilityExtractor"])
        signals["sub_profession_type"] = self._make_signal("sub_profession_type", "enumeration", {"category": self._get(firm, "sub_profession_type", default="UNKNOWN")}, ["FirmStabilityExtractor"])
        signals["firm_size"] = self._make_signal("firm_size", "enumeration", {"category": self._get(firm, "firm_size_band", default="UNKNOWN")}, ["FirmStabilityExtractor"])
        signals["revenue_size"] = self._make_signal("revenue_size", "enumeration", {"category": self._get(firm, "revenue_band", default="UNKNOWN")}, ["FirmStabilityExtractor"])
        return AggregationResult(entity_id=self.entity_id, signals=signals)

# VERIFICATION

def get_all_signal_names() -> Dict[str, List[str]]:
    coverage_signals = {"marine": [], "aerospace": [], "cyber": [], "d_and_o": [], "energy": [], "financial_institutions": [], "professional_indemnity": []}
    for agg_name, agg_class in AGGREGATOR_REGISTRY.items():
        if agg_name.startswith("Marine"): coverage = "marine"
        elif agg_name.startswith("Aerospace"): coverage = "aerospace"
        elif agg_name.startswith("Cyber"): coverage = "cyber"
        elif agg_name.startswith("DO"): coverage = "d_and_o"
        elif agg_name.startswith("Energy"): coverage = "energy"
        elif agg_name.startswith("FI"): coverage = "financial_institutions"
        elif agg_name.startswith("PI"): coverage = "professional_indemnity"
        else: continue
        try:
            agg = agg_class(entity_id="test")
            result = agg.aggregate({})
            coverage_signals[coverage].extend(result.signals.keys())
        except Exception as e:
            print(f"Error with {agg_name}: {e}")
    return coverage_signals

if __name__ == "__main__":
    signals = get_all_signal_names()
    total = 0
    for coverage, sigs in signals.items():
        count = len(sigs)
        total += count
        print(f"{coverage.upper()}: {count} signals")
    print(f"\nTOTAL: {total} signals")
