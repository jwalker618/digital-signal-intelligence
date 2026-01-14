"""
Aerospace Aggregators - All Signal Groups

Production-ready aggregators for Aerospace coverage signals.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from ...base import ProductionAggregator
from ....types import AggregatorResult, ExtractorResult


# From network_authority.py
class AllianceMembershipAggregator(ProductionAggregator):
    """
    Transforms airline alliance data into scoring structure.
    
    Expected input (from AirlineAllianceExtractor):
        {
            "data": {
                "has_alliance_membership": bool,
                "alliance": {
                    "alliance_code": str,
                    "alliance_tier": int,
                    "membership_tier": str,
                    "is_founding_member": bool,
                    "join_date": str,
                    ...
                },
                "is_iata_member": bool,
            }
        }
    
    Output:
        {
            "has_alliance": bool,
            "alliance_code": str | None,
            "alliance_tier": int (1-3, 3 = global alliance),
            "membership_tier_score": int (0-100),
            "membership_years": int,
            "is_founding_member": bool,
            "is_iata_member": bool,
        }
    """
    
    MEMBERSHIP_TIER_SCORES = {
        "FOUNDING": 100,
        "FULL": 85,
        "CONNECTING_PARTNER": 60,
        "AFFILIATE": 40,
    }
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        
        if not raw:
            return self._create_error_result("No alliance data available")
        
        has_alliance = self._normalize_bool(raw.get("has_alliance_membership"))
        is_iata = self._normalize_bool(raw.get("is_iata_member"))
        
        if not has_alliance:
            return self._create_success_result({
                "has_alliance": False,
                "alliance_code": None,
                "alliance_tier": 0,
                "membership_tier_score": 0,
                "membership_years": 0,
                "is_founding_member": False,
                "is_iata_member": is_iata,
            }, extractor_results, warnings)
        
        alliance = raw.get("alliance", {})
        alliance_code = alliance.get("alliance_code")
        alliance_tier = self._normalize_int(alliance.get("alliance_tier"), 0)
        membership_tier = alliance.get("membership_tier", "FULL")
        is_founding = self._normalize_bool(alliance.get("is_founding_member"))
        
        # Calculate membership years
        join_date = alliance.get("join_date")
        membership_years = self._calculate_years_since(join_date)
        
        # Get tier score
        tier_score = self.MEMBERSHIP_TIER_SCORES.get(membership_tier, 50)
        
        return self._create_success_result({
            "has_alliance": True,
            "alliance_code": alliance_code,
            "alliance_tier": alliance_tier,
            "membership_tier_score": tier_score,
            "membership_years": membership_years,
            "is_founding_member": is_founding,
            "is_iata_member": is_iata,
        }, extractor_results, warnings)


class CodeshareQualityAggregator(ProductionAggregator):
    """
    Transforms codeshare partnership data into quality metrics.
    
    Expected input (from CodesharePartnershipExtractor):
        {
            "data": {
                "partner_count": int,
                "partners": [{quality_tier, safety_score, iosa_registered}, ...],
                "average_partner_safety_score": float,
                "tier1_partner_percentage": float,
                "iosa_registered_percentage": float,
            }
        }
    
    Output:
        {
            "partner_count": int,
            "average_partner_safety_score": float,
            "tier1_partner_pct": float,
            "iosa_coverage_pct": float,
            "has_major_partners": bool,
            "network_quality_score": float (0-100),
        }
    """
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        
        if not raw:
            return self._create_error_result("No codeshare data available")
        
        partner_count = self._normalize_int(raw.get("partner_count"), 0)
        avg_safety = self._normalize_float(raw.get("average_partner_safety_score"), 0)
        tier1_pct = self._normalize_float(raw.get("tier1_partner_percentage"), 0)
        iosa_pct = self._normalize_float(raw.get("iosa_registered_percentage"), 0)
        has_major = self._normalize_bool(raw.get("has_major_carrier_partnership"))
        
        # Calculate network quality score
        # Weighted: safety 40%, tier quality 30%, IOSA coverage 20%, having partners 10%
        if partner_count == 0:
            network_score = 30  # No partners is not great but not terrible
        else:
            safety_component = avg_safety * 0.40
            tier_component = tier1_pct * 0.30
            iosa_component = iosa_pct * 0.20
            partner_component = min(partner_count / 20, 1) * 10  # Cap at 20 partners
            
            network_score = safety_component + tier_component + iosa_component + partner_component
        
        return self._create_success_result({
            "partner_count": partner_count,
            "average_partner_safety_score": round(avg_safety, 1),
            "tier1_partner_pct": round(tier1_pct, 1),
            "iosa_coverage_pct": round(iosa_pct, 1),
            "has_major_partners": has_major,
            "network_quality_score": round(network_score, 1),
        }, extractor_results, warnings)


class LessorQualityAggregator(ProductionAggregator):
    """
    Transforms aircraft lessor data into quality metrics.
    
    Expected input (from AircraftLessorExtractor):
        {
            "data": {
                "owned_fleet_percentage": float,
                "leased_fleet_percentage": float,
                "lessor_count": int,
                "lessors": [{lessor_tier, lessor_credit_rating, fleet_percentage}, ...],
                "average_lessor_tier": float,
                "tier1_lessor_exposure_pct": float,
            }
        }
    
    Output:
        {
            "owned_pct": float,
            "leased_pct": float,
            "lessor_count": int,
            "average_lessor_tier": float,
            "tier1_exposure_pct": float,
            "lessor_quality_score": float (0-100),
        }
    """
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        
        if not raw:
            return self._create_error_result("No lessor data available")
        
        owned_pct = self._normalize_float(raw.get("owned_fleet_percentage"), 0)
        leased_pct = self._normalize_float(raw.get("leased_fleet_percentage"), 0)
        lessor_count = self._normalize_int(raw.get("lessor_count"), 0)
        avg_tier = self._normalize_float(raw.get("average_lessor_tier"), 3)
        tier1_pct = self._normalize_float(raw.get("tier1_lessor_exposure_pct"), 0)
        
        # Calculate quality score
        # High ownership is good, tier 1 lessors are good
        ownership_bonus = min(owned_pct, 50)  # Max 50 points for ownership
        
        if lessor_count == 0:
            lessor_score = 50 + ownership_bonus  # All owned
        else:
            # Tier scoring: tier 1 = 100, tier 2 = 70, tier 3 = 40
            tier_score = max(0, 100 - (avg_tier - 1) * 30)
            tier1_bonus = tier1_pct * 0.2  # Extra points for tier 1 exposure
            
            lessor_score = tier_score * 0.5 + tier1_bonus + ownership_bonus * 0.5
        
        return self._create_success_result({
            "owned_pct": round(owned_pct, 1),
            "leased_pct": round(leased_pct, 1),
            "lessor_count": lessor_count,
            "average_lessor_tier": round(avg_tier, 2),
            "tier1_exposure_pct": round(tier1_pct, 1),
            "lessor_quality_score": round(min(100, lessor_score), 1),
        }, extractor_results, warnings)


class OEMRelationshipAggregator(ProductionAggregator):
    """
    Transforms OEM relationship data into quality metrics.
    
    Expected input (from OEMRelationshipExtractor):
        {
            "data": {
                "oem_relationship_count": int,
                "oem_relationships": [{oem_tier, has_support_agreement, active_orders}, ...],
                "has_tier1_oem": bool,
                "has_comprehensive_support_agreement": bool,
                "total_active_orders": int,
            }
        }
    
    Output:
        {
            "oem_count": int,
            "has_tier1_oem": bool,
            "has_comprehensive_support": bool,
            "total_orders": int,
            "oem_relationship_score": float (0-100),
        }
    """
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        
        if not raw:
            return self._create_error_result("No OEM data available")
        
        oem_count = self._normalize_int(raw.get("oem_relationship_count"), 0)
        has_tier1 = self._normalize_bool(raw.get("has_tier1_oem"))
        has_comprehensive = self._normalize_bool(raw.get("has_comprehensive_support_agreement"))
        total_orders = self._normalize_int(raw.get("total_active_orders"), 0)
        
        # Calculate relationship score
        score = 40  # Base score for having any OEM
        
        if has_tier1:
            score += 30  # Major OEM relationship
        
        if has_comprehensive:
            score += 20  # Comprehensive support shows investment
        
        if total_orders > 0:
            # Orders show growth/investment
            order_bonus = min(total_orders / 50 * 10, 10)
            score += order_bonus
        
        return self._create_success_result({
            "oem_count": oem_count,
            "has_tier1_oem": has_tier1,
            "has_comprehensive_support": has_comprehensive,
            "total_orders": total_orders,
            "oem_relationship_score": round(min(100, score), 1),
        }, extractor_results, warnings)


class MROQualityAggregator(ProductionAggregator):
    """
    Transforms MRO provider data into quality metrics.
    
    Expected input (from MROProviderExtractor):
        {
            "data": {
                "mro_provider_count": int,
                "mro_providers": [{provider_tier, quality_rating, is_in_house}, ...],
                "has_in_house_mro": bool,
                "has_tier1_mro": bool,
                "average_mro_quality": float,
                "all_easa_certified": bool,
            }
        }
    
    Output:
        {
            "provider_count": int,
            "has_in_house": bool,
            "has_tier1_provider": bool,
            "average_quality": float,
            "all_certified": bool,
            "mro_quality_score": float (0-100),
        }
    """
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        
        if not raw:
            return self._create_error_result("No MRO data available")
        
        provider_count = self._normalize_int(raw.get("mro_provider_count"), 0)
        has_in_house = self._normalize_bool(raw.get("has_in_house_mro"))
        has_tier1 = self._normalize_bool(raw.get("has_tier1_mro"))
        avg_quality = self._normalize_float(raw.get("average_mro_quality"), 50)
        all_certified = self._normalize_bool(raw.get("all_easa_certified"))
        
        # Calculate MRO quality score
        # Base is average quality rating
        score = avg_quality * 0.6
        
        if has_tier1:
            score += 20
        
        if has_in_house:
            score += 10
        
        if all_certified:
            score += 10
        
        return self._create_success_result({
            "provider_count": provider_count,
            "has_in_house": has_in_house,
            "has_tier1_provider": has_tier1,
            "average_quality": round(avg_quality, 1),
            "all_certified": all_certified,
            "mro_quality_score": round(min(100, score), 1),
        }, extractor_results, warnings)

# From safety_record.py
class AviationSafetyAggregator(ProductionAggregator):
    """
    Transforms aviation safety database data into multiple signal metrics.
    
    This aggregator produces data for multiple signals from a single
    extractor (AviationSafetyDatabaseExtractor), as all safety metrics
    come from the same data source.
    
    Expected input (from AviationSafetyDatabaseExtractor):
        {
            "data": {
                "total_accidents": int,
                "accidents": [{category, fatalities, hull_loss, operator_cited}, ...],
                "fatal_accidents": int,
                "total_fatalities": int,
                "hull_losses": int,
                "total_incidents": int,
                "incidents": [{severity, ...}, ...],
                "serious_incidents": int,
                "accident_rate_per_million_departures": float,
                "industry_average_rate": float,
                "rate_vs_industry": float,
                "operator_cited_count": int,
            }
        }
    
    Output:
        Full normalized safety data for all 5 safety signals.
    """
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        
        if not raw:
            return self._create_error_result("No safety data available")
        
        # Extract raw values
        total_accidents = self._normalize_int(raw.get("total_accidents"), 0)
        fatal_accidents = self._normalize_int(raw.get("fatal_accidents"), 0)
        total_fatalities = self._normalize_int(raw.get("total_fatalities"), 0)
        hull_losses = self._normalize_int(raw.get("hull_losses"), 0)
        
        total_incidents = self._normalize_int(raw.get("total_incidents"), 0)
        serious_incidents = self._normalize_int(raw.get("serious_incidents"), 0)
        
        accident_rate = self._normalize_float(raw.get("accident_rate_per_million_departures"), 0)
        industry_rate = self._normalize_float(raw.get("industry_average_rate"), 0.18)
        rate_vs_industry = self._normalize_float(raw.get("rate_vs_industry"), 1.0)
        
        operator_cited = self._normalize_int(raw.get("operator_cited_count"), 0)
        
        # Calculate scores for each signal
        
        # 1. Accident History Score (0-100, higher = safer)
        accident_score = 100
        if hull_losses > 0:
            accident_score -= hull_losses * 25  # Major penalty for hull losses
        accident_score -= total_accidents * 10
        accident_score = max(0, accident_score)
        
        # 2. Incident History Score
        incident_score = 100
        incident_score -= serious_incidents * 8
        incident_score -= (total_incidents - serious_incidents) * 2
        incident_score = max(0, incident_score)
        
        # 3. Accident Rate Score (vs industry)
        if rate_vs_industry == 0 or accident_rate == 0:
            rate_score = 100  # No accidents
        elif rate_vs_industry <= 0.5:
            rate_score = 95  # Well below industry
        elif rate_vs_industry <= 0.8:
            rate_score = 85
        elif rate_vs_industry <= 1.0:
            rate_score = 75
        elif rate_vs_industry <= 1.5:
            rate_score = 55
        elif rate_vs_industry <= 2.0:
            rate_score = 40
        else:
            rate_score = 20  # Well above industry
        
        # 4. Fatality History Score
        if fatal_accidents == 0:
            fatality_score = 100
        elif fatal_accidents == 1 and total_fatalities <= 5:
            fatality_score = 50  # Single minor fatal
        elif fatal_accidents == 1:
            fatality_score = 35
        else:
            fatality_score = max(0, 50 - fatal_accidents * 20)
        
        # 5. Investigation Findings Score
        if total_accidents == 0:
            investigation_score = 100
        elif operator_cited == 0:
            investigation_score = 85  # Accidents but not at fault
        else:
            # Ratio of cited to total accidents
            cited_ratio = operator_cited / total_accidents
            investigation_score = max(0, 100 - cited_ratio * 60 - operator_cited * 10)
        
        return self._create_success_result({
            # Raw counts
            "total_accidents": total_accidents,
            "fatal_accidents": fatal_accidents,
            "total_fatalities": total_fatalities,
            "hull_losses": hull_losses,
            "total_incidents": total_incidents,
            "serious_incidents": serious_incidents,
            "operator_cited_count": operator_cited,
            
            # Rate metrics
            "accident_rate": round(accident_rate, 4),
            "industry_average_rate": industry_rate,
            "rate_vs_industry": round(rate_vs_industry, 2),
            
            # Signal scores (0-100)
            "accident_history_score": round(accident_score, 1),
            "incident_history_score": round(incident_score, 1),
            "accident_rate_score": round(rate_score, 1),
            "fatality_history_score": round(fatality_score, 1),
            "investigation_findings_score": round(investigation_score, 1),
            
            # Flags
            "has_hull_loss": hull_losses > 0,
            "has_fatalities": fatal_accidents > 0,
            "above_industry_rate": rate_vs_industry > 1.0,
            "clean_record": total_accidents == 0 and serious_incidents == 0,
        }, extractor_results, warnings)


# Individual aggregators that can use subsets of the data

class AccidentHistoryAggregator(ProductionAggregator):
    """
    Focused aggregator for accident_history signal only.
    Can use either AviationSafetyAggregator output or raw extractor data.
    """
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        
        if not raw:
            return self._create_error_result("No accident data available")
        
        total_accidents = self._normalize_int(raw.get("total_accidents"), 0)
        hull_losses = self._normalize_int(raw.get("hull_losses"), 0)
        
        # Score calculation
        score = 100
        score -= hull_losses * 25
        score -= total_accidents * 10
        
        return self._create_success_result({
            "total_accidents": total_accidents,
            "hull_losses": hull_losses,
            "accident_history_score": max(0, round(score, 1)),
            "has_hull_loss": hull_losses > 0,
        }, extractor_results, warnings)


class IncidentHistoryAggregator(ProductionAggregator):
    """Focused aggregator for incident_history signal."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        
        if not raw:
            return self._create_error_result("No incident data available")
        
        total_incidents = self._normalize_int(raw.get("total_incidents"), 0)
        serious_incidents = self._normalize_int(raw.get("serious_incidents"), 0)
        
        score = 100
        score -= serious_incidents * 8
        score -= (total_incidents - serious_incidents) * 2
        
        return self._create_success_result({
            "total_incidents": total_incidents,
            "serious_incidents": serious_incidents,
            "incident_history_score": max(0, round(score, 1)),
        }, extractor_results, warnings)


class AccidentRateAggregator(ProductionAggregator):
    """Focused aggregator for accident_rate signal."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        
        if not raw:
            return self._create_error_result("No rate data available")
        
        accident_rate = self._normalize_float(raw.get("accident_rate_per_million_departures"), 0)
        industry_rate = self._normalize_float(raw.get("industry_average_rate"), 0.18)
        rate_vs_industry = self._normalize_float(raw.get("rate_vs_industry"), 1.0)
        
        if rate_vs_industry == 0 or accident_rate == 0:
            score = 100
        elif rate_vs_industry <= 0.5:
            score = 95
        elif rate_vs_industry <= 0.8:
            score = 85
        elif rate_vs_industry <= 1.0:
            score = 75
        elif rate_vs_industry <= 1.5:
            score = 55
        elif rate_vs_industry <= 2.0:
            score = 40
        else:
            score = 20
        
        return self._create_success_result({
            "accident_rate": round(accident_rate, 4),
            "industry_rate": industry_rate,
            "rate_vs_industry": round(rate_vs_industry, 2),
            "accident_rate_score": score,
            "above_industry": rate_vs_industry > 1.0,
        }, extractor_results, warnings)


class FatalityHistoryAggregator(ProductionAggregator):
    """Focused aggregator for fatality_history signal."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        
        if not raw:
            return self._create_error_result("No fatality data available")
        
        fatal_accidents = self._normalize_int(raw.get("fatal_accidents"), 0)
        total_fatalities = self._normalize_int(raw.get("total_fatalities"), 0)
        
        if fatal_accidents == 0:
            score = 100
        elif fatal_accidents == 1 and total_fatalities <= 5:
            score = 50
        elif fatal_accidents == 1:
            score = 35
        else:
            score = max(0, 50 - fatal_accidents * 20)
        
        return self._create_success_result({
            "fatal_accidents": fatal_accidents,
            "total_fatalities": total_fatalities,
            "fatality_history_score": score,
            "has_fatalities": fatal_accidents > 0,
        }, extractor_results, warnings)


class InvestigationFindingsAggregator(ProductionAggregator):
    """Focused aggregator for investigation_findings signal."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        
        if not raw:
            return self._create_error_result("No investigation data available")
        
        total_accidents = self._normalize_int(raw.get("total_accidents"), 0)
        operator_cited = self._normalize_int(raw.get("operator_cited_count"), 0)
        
        if total_accidents == 0:
            score = 100
        elif operator_cited == 0:
            score = 85
        else:
            cited_ratio = operator_cited / total_accidents
            score = max(0, 100 - cited_ratio * 60 - operator_cited * 10)
        
        return self._create_success_result({
            "total_accidents": total_accidents,
            "operator_cited": operator_cited,
            "cited_ratio": round(operator_cited / total_accidents, 2) if total_accidents > 0 else 0,
            "investigation_findings_score": round(score, 1),
        }, extractor_results, warnings)

# From regulatory_compliance.py
class CertificateStatusAggregator(ProductionAggregator):
    """
    Transforms operating certificate data into compliance metrics.
    
    Expected input (from OperatingCertificateExtractor):
        {
            "data": {
                "primary_regulator": str,
                "regulator_tier": int,
                "certificate_status": str,
                "has_conditions": bool,
                "total_findings_2yr": int,
                "critical_findings_2yr": int,
                "is_suspended": bool,
                "is_revoked": bool,
            }
        }
    
    Output:
        {
            "regulator": str,
            "regulator_tier": int,
            "status": str,
            "has_conditions": bool,
            "certificate_score": float (0-100),
            "is_at_risk": bool,
        }
    """
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        
        if not raw:
            return self._create_error_result("No certificate data available")
        
        regulator = raw.get("primary_regulator", "UNKNOWN")
        tier = self._normalize_int(raw.get("regulator_tier"), 3)
        status = raw.get("certificate_status", "UNKNOWN")
        has_conditions = self._normalize_bool(raw.get("has_conditions"))
        findings = self._normalize_int(raw.get("total_findings_2yr"), 0)
        critical = self._normalize_int(raw.get("critical_findings_2yr"), 0)
        is_suspended = self._normalize_bool(raw.get("is_suspended"))
        is_revoked = self._normalize_bool(raw.get("is_revoked"))
        
        # Calculate score
        if is_revoked:
            score = 0
            warnings.append("Certificate has been revoked")
        elif is_suspended:
            score = 10
            warnings.append("Certificate is suspended")
        elif status == "ACTIVE_WITH_CONDITIONS":
            score = 60 - critical * 10 - findings * 2
        elif status == "ACTIVE":
            score = 100 - critical * 10 - findings * 2
        else:
            score = 30
        
        # Tier adjustment (tier 1 regulators are stricter, so score is more meaningful)
        # No adjustment needed - the score reflects compliance, not regulator quality
        
        score = max(0, min(100, score))
        
        return self._create_success_result({
            "regulator": regulator,
            "regulator_tier": tier,
            "status": status,
            "has_conditions": has_conditions,
            "total_findings_2yr": findings,
            "critical_findings_2yr": critical,
            "certificate_score": round(score, 1),
            "is_at_risk": is_suspended or is_revoked or critical > 0,
        }, extractor_results, warnings)


class IOSAAuditAggregator(ProductionAggregator):
    """
    Transforms IOSA registry data into audit compliance metrics.
    
    Expected input (from IOSARegistryExtractor):
        {
            "data": {
                "registration_status": str,
                "years_registered": int,
                "consecutive_renewals": int,
                "audit_findings_count": int,
                "critical_findings": int,
                ...
            }
        }
    
    Output:
        {
            "registration_status": str,
            "is_registered": bool,
            "years_registered": int,
            "audit_findings": int,
            "iosa_score": float (0-100),
        }
    """
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        
        if not raw:
            return self._create_error_result("No IOSA data available")
        
        status = raw.get("registration_status", "UNKNOWN")
        
        if status == "REGISTERED":
            years = self._normalize_int(raw.get("years_registered"), 0)
            renewals = self._normalize_int(raw.get("consecutive_renewals"), 0)
            findings = self._normalize_int(raw.get("audit_findings_count"), 0)
            critical = self._normalize_int(raw.get("critical_findings"), 0)
            
            # Base score for being registered
            score = 70
            
            # Bonus for longevity (up to 15 points)
            score += min(years, 10) * 1.5
            
            # Bonus for consecutive renewals
            score += min(renewals, 5) * 2
            
            # Penalties for findings
            score -= findings * 1
            score -= critical * 5
            
            score = max(50, min(100, score))  # Registered = at least 50
            
        elif status == "EXPIRED":
            score = 30
            warnings.append("IOSA registration has expired")
            years = 0
            findings = 0
            
        else:  # NEVER_REGISTERED
            applicable = self._normalize_bool(raw.get("applicable", True))
            if applicable:
                score = 25
            else:
                score = 50  # Not applicable (e.g., small operators)
            years = 0
            findings = 0
        
        return self._create_success_result({
            "registration_status": status,
            "is_registered": status == "REGISTERED",
            "years_registered": years,
            "audit_findings": findings if status == "REGISTERED" else None,
            "iosa_score": round(score, 1),
        }, extractor_results, warnings)


class RampInspectionAggregator(ProductionAggregator):
    """
    Transforms ramp inspection data into safety metrics.
    
    Expected input (from RampInspectionExtractor):
        {
            "data": {
                "total_inspections_3yr": int,
                "total_findings": int,
                "category_2_findings": int,
                "category_3_findings": int,
                "findings_per_inspection": float,
                "rate_vs_industry": float,
                "has_category_3_findings": bool,
                "ground_stop_events": int,
            }
        }
    
    Output:
        {
            "inspections_3yr": int,
            "findings_rate": float,
            "severe_findings": int,
            "ground_stops": int,
            "ramp_inspection_score": float (0-100),
        }
    """
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        
        if not raw:
            return self._create_error_result("No ramp inspection data available")
        
        inspections = self._normalize_int(raw.get("total_inspections_3yr"), 0)
        total_findings = self._normalize_int(raw.get("total_findings"), 0)
        cat2 = self._normalize_int(raw.get("category_2_findings"), 0)
        cat3 = self._normalize_int(raw.get("category_3_findings"), 0)
        findings_rate = self._normalize_float(raw.get("findings_per_inspection"), 0)
        rate_vs_industry = self._normalize_float(raw.get("rate_vs_industry"), 1.0)
        ground_stops = self._normalize_int(raw.get("ground_stop_events"), 0)
        
        # Calculate score
        # Start at 100, deduct for findings
        score = 100
        
        # Rate vs industry (main factor)
        if rate_vs_industry <= 0.5:
            score = 95
        elif rate_vs_industry <= 0.8:
            score = 85
        elif rate_vs_industry <= 1.0:
            score = 75
        elif rate_vs_industry <= 1.5:
            score = 60
        elif rate_vs_industry <= 2.0:
            score = 45
        else:
            score = 30
        
        # Category 3 findings are serious
        score -= cat3 * 15
        
        # Ground stops are very serious
        score -= ground_stops * 20
        
        if cat3 > 0:
            warnings.append(f"{cat3} Category 3 finding(s) - serious deficiencies")
        
        return self._create_success_result({
            "inspections_3yr": inspections,
            "total_findings": total_findings,
            "findings_rate": round(findings_rate, 2),
            "rate_vs_industry": round(rate_vs_industry, 2),
            "severe_findings": cat3,
            "ground_stops": ground_stops,
            "ramp_inspection_score": max(0, round(score, 1)),
        }, extractor_results, warnings)


class EUSafetyListAggregator(ProductionAggregator):
    """
    Transforms EU safety list data into risk indicator.
    
    Expected input (from EUSafetyListExtractor):
        {
            "data": {
                "is_on_safety_list": bool,
                "annex_a_banned": bool,
                "annex_b_restricted": bool,
                ...
            }
        }
    
    Output:
        {
            "is_on_list": bool,
            "is_banned": bool,
            "is_restricted": bool,
            "eu_safety_score": float (0-100),
        }
    """
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        
        if not raw:
            return self._create_error_result("No EU safety list data available")
        
        is_on_list = self._normalize_bool(raw.get("is_on_safety_list"))
        is_banned = self._normalize_bool(raw.get("annex_a_banned"))
        is_restricted = self._normalize_bool(raw.get("annex_b_restricted"))
        
        if is_banned:
            score = 0
            warnings.append("Operator is BANNED from EU airspace (Annex A)")
        elif is_restricted:
            score = 30
            warnings.append("Operator has RESTRICTIONS in EU (Annex B)")
        else:
            score = 100
        
        return self._create_success_result({
            "is_on_list": is_on_list,
            "is_banned": is_banned,
            "is_restricted": is_restricted,
            "eu_safety_score": score,
        }, extractor_results, warnings)


class StateSafetyAggregator(ProductionAggregator):
    """
    Transforms ICAO USOAP data into state oversight quality metrics.
    
    Expected input (from StateSafetyExtractor):
        {
            "data": {
                "state_code": str,
                "overall_effective_implementation": float,
                "global_average_ei": float,
                "has_significant_safety_concern": bool,
                "icao_tier": int,
                "area_scores": {LEG, ORG, PEL, OPS, AIR, ...},
            }
        }
    
    Output:
        {
            "state_code": str,
            "overall_ei": float,
            "vs_global_average": float,
            "has_ssc": bool,
            "state_safety_score": float (0-100),
        }
    """
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        
        if not raw:
            return self._create_error_result("No state safety data available")
        
        state = raw.get("state_code", "UNKNOWN")
        overall_ei = self._normalize_float(raw.get("overall_effective_implementation"), 65)
        global_avg = self._normalize_float(raw.get("global_average_ei"), 65)
        has_ssc = self._normalize_bool(raw.get("has_significant_safety_concern"))
        tier = self._normalize_int(raw.get("icao_tier"), 2)
        
        # Score is essentially the EI score, with SSC penalty
        score = overall_ei
        
        if has_ssc:
            score = min(score, 40)  # SSC caps the score
            warnings.append("State has Significant Safety Concerns")
        
        return self._create_success_result({
            "state_code": state,
            "overall_ei": round(overall_ei, 1),
            "global_average": global_avg,
            "vs_global_average": round(overall_ei - global_avg, 1),
            "has_significant_safety_concern": has_ssc,
            "icao_tier": tier,
            "state_safety_score": round(score, 1),
        }, extractor_results, warnings)

# From operational_and_others.py
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

