"""
Aerospace Aggregators - Regulatory Compliance Signal Group

Aggregators for regulatory compliance signals.

Signals:
- certificate_status: Operating certificate status
- enforcement_actions: Regulatory fines and penalties
- iosa_audit_status: IOSA registration and audit findings
- ramp_inspection: SAFA/SACA ramp inspection results
- eu_safety_list: EU banned carrier list status
- state_safety_rating: ICAO USOAP scores for state of registry
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from ...base import ProductionAggregator
from ....types import AggregatorResult, ExtractorResult


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
