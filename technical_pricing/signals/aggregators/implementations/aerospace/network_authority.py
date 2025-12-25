"""
Aerospace Aggregators - Network Authority Signal Group

Aggregators for network authority signals that assess the quality of
an airline's business relationships and partnerships.

Signals:
- alliance_membership: Airline alliance participation
- codeshare_quality: Quality of codeshare partners
- lessor_quality: Quality of aircraft lessors
- oem_relationship: OEM relationships (Boeing, Airbus, etc.)
- mro_quality: Quality of MRO providers
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from ...base import ProductionAggregator
from ....types import AggregatorResult, ExtractorResult


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
