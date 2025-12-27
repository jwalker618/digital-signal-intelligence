"""
Marine Aggregators - All Signal Groups

Production-ready aggregators for Marine hull and liability coverage signals.
"""

from typing import Any, Dict, List
from ...base import ProductionAggregator
from ....types import AggregatorResult, ExtractorResult


# =============================================================================
# NETWORK AUTHORITY AGGREGATORS
# =============================================================================

class ClassificationSocietyAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        is_iacs = raw.get("is_iacs_member", False)
        years = raw.get("class_relationship_years", 0)
        changes = raw.get("class_changes_5yr", 0)
        score = 95 if is_iacs else 50
        score += min(10, years // 3) - changes * 10
        return self._create_success_result({"classification_society_score": max(0, min(100, score)), "is_iacs": is_iacs}, extractor_results)


class PIClubAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        is_ig = raw.get("is_international_group", False)
        years = raw.get("membership_years", 0)
        score = 90 if is_ig else 50
        score += min(10, years // 3)
        if raw.get("claims_history_flag"): score -= 15
        return self._create_success_result({"pi_club_score": max(0, min(100, score)), "is_ig_club": is_ig}, extractor_results)


class ChartererQualityAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        tier = raw.get("charterer_tier", 2)
        has_major = raw.get("has_oil_major_approval", False)
        score = 90 if tier == 1 else 60
        if has_major: score += 10
        return self._create_success_result({"charterer_quality_score": min(100, score), "has_oil_major_approval": has_major}, extractor_results)


class MarineBankingAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        tier = raw.get("lender_tier", 3)
        compliance = raw.get("covenant_compliance", "compliant")
        scores = {1: 90, 2: 70, 3: 50}
        score = scores.get(tier, 50)
        if compliance == "waiver": score -= 10
        elif compliance == "breach": score -= 25
        return self._create_success_result({"banking_relationship_score": max(0, score)}, extractor_results)


class FlagStateAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        status = raw.get("paris_mou_status", "GREY_LIST")
        scores = {"WHITE_LIST": 95, "GREY_LIST": 60, "BLACK_LIST": 25}
        return self._create_success_result({"flag_state_score": scores.get(status, 60), "mou_status": status}, extractor_results)


class MarineIndustryAssociationAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        count = raw.get("membership_count", 0)
        bimco = raw.get("bimco_member", False)
        score = min(100, 40 + count * 12 + (15 if bimco else 0))
        return self._create_success_result({"industry_association_score": score, "membership_count": count}, extractor_results)


class TechnicalManagerAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        is_third = raw.get("is_third_party_managed", False)
        tier = raw.get("manager_tier", 0)
        if not is_third: score = 75  # In-house management
        else: score = {1: 90, 2: 70, 3: 50}.get(tier, 60)
        if raw.get("iso_certified"): score += 10
        return self._create_success_result({"technical_manager_score": min(100, score)}, extractor_results)


class PortRelationshipAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        priority = raw.get("priority_berthing", False)
        familiarity = raw.get("port_state_familiarity", "moderate")
        scores = {"high": 85, "moderate": 65, "low": 45}
        score = scores.get(familiarity, 65)
        if priority: score += 10
        return self._create_success_result({"port_relationship_score": min(100, score)}, extractor_results)


# =============================================================================
# OPERATIONAL TELEMETRY AGGREGATORS
# =============================================================================

class AISComplianceAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        compliance = raw.get("ais_compliance_rate", 95)
        gaps = raw.get("gaps_detected_30d", 0)
        score = compliance - gaps * 1.5
        warnings = [f"AIS gaps detected: {gaps}"] if gaps > 5 else []
        return self._create_success_result({"ais_compliance_score": max(0, min(100, score)), "warnings": warnings}, extractor_results)


class DarkActivityAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        events = raw.get("dark_events_90d", 0)
        suspicious = raw.get("suspicious_dark_activity", False)
        spoofing = raw.get("spoofing_indicators", False)
        score = 100 - events * 8
        if suspicious: score -= 25
        if spoofing: score -= 30
        warnings = []
        if suspicious: warnings.append("Suspicious dark activity detected")
        if spoofing: warnings.append("AIS spoofing indicators")
        return self._create_success_result({"dark_activity_score": max(0, score), "warnings": warnings}, extractor_results)


class RouteRiskAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        high_risk = raw.get("high_risk_area_calls_90d", 0)
        jwc_pct = raw.get("jwc_listed_area_pct", 0)
        score = 100 - high_risk * 3 - jwc_pct * 1.5
        if raw.get("armed_guard_usage"): score += 10
        return self._create_success_result({"route_risk_score": max(0, min(100, score))}, extractor_results)


class PSCRegionAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        paris = raw.get("paris_mou_calls_pct", 30)
        tokyo = raw.get("tokyo_mou_calls_pct", 30)
        score = 50 + (paris + tokyo) * 0.3  # More regulated regions = better
        return self._create_success_result({"psc_region_score": min(100, score)}, extractor_results)


class OperationalEfficiencyAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        speed_score = raw.get("speed_optimization_score", 70)
        slow_steam = raw.get("slow_steaming_adoption", False)
        score = speed_score + (10 if slow_steam else 0)
        return self._create_success_result({"operational_efficiency_score": min(100, score)}, extractor_results)


class WeatherRoutingAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        has_service = raw.get("weather_routing_service", False)
        claims = raw.get("weather_damage_claims_3yr", 0)
        score = raw.get("risk_avoidance_score", 70)
        if has_service: score += 15
        score -= claims * 10
        return self._create_success_result({"weather_routing_score": max(0, min(100, score))}, extractor_results)


# =============================================================================
# SAFETY COMPLIANCE AGGREGATORS
# =============================================================================

class PSCDetentionAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        detentions = raw.get("detentions_36mo", 0)
        rate = raw.get("detention_rate_pct", 0)
        score = 100 - detentions * 20 - rate * 10
        warnings = [f"PSC detentions: {detentions}"] if detentions > 0 else []
        return self._create_success_result({"psc_detention_score": max(0, score), "warnings": warnings}, extractor_results)


class PSCDeficiencyAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        avg_def = raw.get("average_deficiencies", 2)
        trend = raw.get("deficiency_trend", "stable")
        score = 100 - avg_def * 8
        if trend == "increasing": score -= 10
        elif trend == "decreasing": score += 5
        return self._create_success_result({"psc_deficiency_score": max(0, min(100, score))}, extractor_results)


class ClassStatusAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        status = raw.get("class_status", "in_class")
        conditions = raw.get("conditions_outstanding", 0)
        scores = {"in_class": 95, "conditional": 60, "suspended": 20, "withdrawn": 5}
        score = scores.get(status, 60) - conditions * 5
        warnings = [f"Class status: {status}"] if status != "in_class" else []
        return self._create_success_result({"class_status_score": max(0, score), "warnings": warnings}, extractor_results)


class ISMComplianceAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        doc_valid = raw.get("doc_valid", True)
        smc_valid = raw.get("smc_valid", True)
        findings = raw.get("major_nc_count", 0)
        score = 100 if doc_valid and smc_valid else 30
        score -= findings * 15
        warnings = []
        if not doc_valid: warnings.append("DOC invalid/expired")
        if not smc_valid: warnings.append("SMC invalid/expired")
        return self._create_success_result({"ism_compliance_score": max(0, score), "warnings": warnings}, extractor_results)


class CasualtyHistoryAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        serious = raw.get("serious_casualties_5yr", 0)
        minor = raw.get("minor_casualties_5yr", 0)
        score = 100 - serious * 25 - minor * 8
        warnings = [f"Serious casualties: {serious}"] if serious > 0 else []
        return self._create_success_result({"casualty_history_score": max(0, score), "warnings": warnings}, extractor_results)


class TotalLossHistoryAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        total_losses = raw.get("total_losses_10yr", 0)
        ctls = raw.get("constructive_total_losses", 0)
        score = 100 - total_losses * 40 - ctls * 25
        warnings = [f"Total losses: {total_losses}"] if total_losses > 0 else []
        return self._create_success_result({"total_loss_score": max(0, score), "warnings": warnings}, extractor_results)


# =============================================================================
# FLEET PROFILE AGGREGATORS
# =============================================================================

class FleetAgeAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        avg_age = raw.get("average_fleet_age", 12)
        if avg_age <= 5: score = 95
        elif avg_age <= 10: score = 85
        elif avg_age <= 15: score = 70
        elif avg_age <= 20: score = 50
        else: score = 30
        return self._create_success_result({"fleet_age_score": score, "average_age": avg_age}, extractor_results)


class FleetStabilityAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        vessels = raw.get("vessel_count", 5)
        changes = raw.get("fleet_changes_12mo", 0)
        score = min(100, 60 + vessels * 2 - changes * 5)
        return self._create_success_result({"fleet_stability_score": max(0, score), "vessel_count": vessels}, extractor_results)


class VesselQualityAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        eco_vessels_pct = raw.get("eco_vessels_pct", 30)
        notations = raw.get("additional_notations_avg", 2)
        score = 50 + eco_vessels_pct * 0.3 + notations * 5
        return self._create_success_result({"vessel_quality_score": min(100, score)}, extractor_results)


class CrewCertificationAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        stcw_compliant = raw.get("stcw_compliant_pct", 95)
        training = raw.get("enhanced_training_pct", 50)
        score = stcw_compliant * 0.7 + training * 0.3
        return self._create_success_result({"crew_certification_score": min(100, score)}, extractor_results)


class ManagementConsistencyAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        years = raw.get("management_tenure_years", 5)
        changes = raw.get("management_changes_5yr", 0)
        score = min(100, 60 + years * 4 - changes * 15)
        return self._create_success_result({"management_consistency_score": max(0, score)}, extractor_results)


# =============================================================================
# SANCTIONS COMPLIANCE AGGREGATORS
# =============================================================================

class SanctionsStatusAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        listed = raw.get("sanctions_listed", False)
        score = 0 if listed else 100
        warnings = ["SANCTIONS LISTED - DECLINE"] if listed else []
        return self._create_success_result({"sanctions_status_score": score, "is_listed": listed, "warnings": warnings}, extractor_results)


class OwnershipTransparencyAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        transparency = raw.get("transparency_level", "moderate")
        shell_companies = raw.get("shell_company_layers", 0)
        scores = {"high": 95, "moderate": 70, "low": 40, "opaque": 15}
        score = scores.get(transparency, 70) - shell_companies * 10
        warnings = ["Ownership opacity concerns"] if transparency in ["low", "opaque"] else []
        return self._create_success_result({"ownership_transparency_score": max(0, score), "warnings": warnings}, extractor_results)


class JurisdictionRiskAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        high_risk = raw.get("high_risk_jurisdiction_exposure", False)
        sanctioned = raw.get("sanctioned_jurisdiction_calls", 0)
        score = 100 - sanctioned * 30
        if high_risk: score -= 25
        warnings = ["High-risk jurisdiction exposure"] if high_risk or sanctioned > 0 else []
        return self._create_success_result({"jurisdiction_risk_score": max(0, score), "warnings": warnings}, extractor_results)


class STSPatternAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        sts_count = raw.get("sts_operations_12mo", 0)
        suspicious = raw.get("suspicious_sts", False)
        score = 100 - sts_count * 5
        if suspicious: score -= 40
        warnings = ["Suspicious STS patterns"] if suspicious else []
        return self._create_success_result({"sts_pattern_score": max(0, score), "warnings": warnings}, extractor_results)


class HistoricalSanctionsAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        previous = raw.get("previously_sanctioned", False)
        connections = raw.get("sanctioned_entity_connections", 0)
        score = 100
        if previous: score -= 30
        score -= connections * 15
        return self._create_success_result({"historical_sanctions_score": max(0, score)}, extractor_results)


# =============================================================================
# ENVIRONMENTAL AGGREGATORS
# =============================================================================

class IMO2020ComplianceAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        compliant = raw.get("fleet_compliant_pct", 95)
        scrubber = raw.get("scrubber_fitted_pct", 30)
        score = compliant * 0.8 + scrubber * 0.2
        return self._create_success_result({"imo2020_compliance_score": min(100, score)}, extractor_results)


class BWMComplianceAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        compliant = raw.get("bwm_compliant_pct", 85)
        violations = raw.get("bwm_violations", 0)
        score = compliant - violations * 15
        return self._create_success_result({"bwm_compliance_score": max(0, min(100, score))}, extractor_results)


class CIIRatingAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        rating = raw.get("fleet_cii_rating", "C")
        scores = {"A": 100, "B": 85, "C": 65, "D": 40, "E": 15}
        return self._create_success_result({"cii_rating_score": scores.get(rating, 65), "cii_rating": rating}, extractor_results)


class EnvironmentalIncidentAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        incidents = raw.get("environmental_incidents_5yr", 0)
        fines = raw.get("environmental_fines_usd", 0)
        score = 100 - incidents * 20 - (fines / 100000)
        warnings = [f"Environmental incidents: {incidents}"] if incidents > 0 else []
        return self._create_success_result({"environmental_incident_score": max(0, min(100, score)), "warnings": warnings}, extractor_results)


# =============================================================================
# CORPORATE FOOTPRINT AGGREGATORS
# =============================================================================

class MarineWebsiteQualityAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        quality = raw.get("website_quality", "basic")
        scores = {"professional": 90, "adequate": 70, "basic": 50, "minimal": 30, "none": 10}
        return self._create_success_result({"website_quality_score": scores.get(quality, 50)}, extractor_results)


class FleetListDisclosureAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        disclosed = raw.get("fleet_list_public", False)
        detailed = raw.get("detailed_specs", False)
        score = 30 if not disclosed else 70 if not detailed else 95
        return self._create_success_result({"fleet_list_score": score, "publicly_disclosed": disclosed}, extractor_results)


class MarineSustainabilityAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        has_report = raw.get("sustainability_report", False)
        poseidon = raw.get("poseidon_principles", False)
        score = 30 + (30 if has_report else 0) + (25 if poseidon else 0)
        return self._create_success_result({"sustainability_reporting_score": min(100, score)}, extractor_results)


class SafetyCultureAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        visible = raw.get("safety_culture_visible", False)
        programs = raw.get("safety_programs", 0)
        score = 40 + (30 if visible else 0) + programs * 10
        return self._create_success_result({"safety_culture_score": min(100, score)}, extractor_results)


class CrewWelfareAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        commitment = raw.get("welfare_commitment", "moderate")
        scores = {"high": 90, "moderate": 65, "low": 40, "none": 20}
        return self._create_success_result({"crew_welfare_score": scores.get(commitment, 65)}, extractor_results)


class MarineIndustryPresenceAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        conferences = raw.get("conference_participation", 0)
        publications = raw.get("industry_publications", 0)
        score = min(100, 40 + conferences * 8 + publications * 10)
        return self._create_success_result({"industry_presence_score": score}, extractor_results)


# =============================================================================
# STRUCTURED DATA AGGREGATORS
# =============================================================================

class VettingAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        rightship = raw.get("rightship_score", 3)
        score = rightship * 20  # 1-5 scale to 0-100
        return self._create_success_result({"vetting_score": min(100, score), "rightship_stars": rightship}, extractor_results)


class MarineESGRatingAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        rating = raw.get("esg_rating", "B")
        scores = {"A": 95, "B": 75, "C": 55, "D": 35, "F": 15, "NR": 50}
        return self._create_success_result({"esg_rating_score": scores.get(rating, 50)}, extractor_results)


class MarineCreditRatingAggregator(ProductionAggregator):
    SCORES = {"AAA": 100, "AA": 90, "A": 80, "BBB": 65, "BB": 50, "B": 35, "CCC": 20, "NR": 50}
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        rating = raw.get("credit_rating", "NR")
        return self._create_success_result({"credit_rating_score": self.SCORES.get(rating, 50)}, extractor_results)


# =============================================================================
# CATEGORICAL AGGREGATORS
# =============================================================================

class OperatorClassificationAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        return self._create_success_result({"operator_type": raw.get("operator_type", "INDEPENDENT")}, extractor_results)


class VesselCategoryAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        return self._create_success_result({"vessel_category": raw.get("vessel_category", "GENERAL_CARGO")}, extractor_results)


class TradingPatternAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        return self._create_success_result({"trading_pattern": raw.get("trading_pattern", "MIXED")}, extractor_results)


class FlagStateQualityAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        return self._create_success_result({"flag_state_quality": raw.get("flag_state_quality", "GREY_LIST")}, extractor_results)


class FleetAgeBandAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        return self._create_success_result({"fleet_age_band": raw.get("fleet_age_band", "AGE_10_15")}, extractor_results)
