"""
Common Aggregators - Reusable Across Coverage Domains

These aggregators transform raw extractor data into normalized structures
for signals that are common across multiple coverage types.

Based on coverage_crosswalk.json common concepts:
- Credit Rating: All 7 coverages
- Leadership Stability: All 7 coverages  
- Public Reporting/Disclosure: All 7 coverages
- Regulatory Actions/Enforcement: All 7 coverages
- Incident/Breach History: All 7 coverages
- Industry Engagement: All 7 coverages

Each aggregator is PRODUCTION READY - no changes needed when extractors
are upgraded from stubs to real data sources.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from ..base import ProductionAggregator
from ...types import AggregatorResult, ExtractorResult


# =============================================================================
# CREDIT RATING AGGREGATOR
# =============================================================================

class CreditRatingAggregator(ProductionAggregator):
    """
    Transforms raw credit rating data into normalized scoring structure.
    
    Expected input (from CreditRatingExtractor):
        {
            "data": {
                "has_rating": bool,
                "ratings": [{agency, rating, outlook, is_investment_grade}, ...],
                "any_investment_grade": bool,
                "any_negative_outlook": bool,
            }
        }
    
    Output:
        {
            "has_rating": bool,
            "rating_count": int,
            "best_rating_score": int (0-100),
            "average_rating_score": float,
            "is_investment_grade": bool,
            "has_negative_outlook": bool,
            "outlook_score": int (0-100),
        }
    """
    
    # Rating score mapping (higher = better)
    RATING_SCORES = {
        # Investment Grade
        "AAA": 100, "Aaa": 100,
        "AA+": 95, "Aa1": 95,
        "AA": 90, "Aa2": 90,
        "AA-": 85, "Aa3": 85,
        "A+": 80, "A1": 80,
        "A": 75, "A2": 75,
        "A-": 70, "A3": 70,
        "BBB+": 65, "Baa1": 65,
        "BBB": 60, "Baa2": 60,
        "BBB-": 55, "Baa3": 55,
        # Non-Investment Grade
        "BB+": 50, "Ba1": 50,
        "BB": 45, "Ba2": 45,
        "BB-": 40, "Ba3": 40,
        "B+": 35, "B1": 35,
        "B": 30, "B2": 30,
        "B-": 25, "B3": 25,
        "CCC+": 20, "Caa1": 20,
        "CCC": 15, "Caa2": 15,
        "CCC-": 10, "Caa3": 10,
        "CC": 8, "Ca": 8,
        "C": 5,
        "D": 0,
    }
    
    OUTLOOK_SCORES = {
        "POSITIVE": 100,
        "WATCH_POSITIVE": 80,
        "STABLE": 70,
        "DEVELOPING": 50,
        "WATCH_NEGATIVE": 30,
        "NEGATIVE": 20,
    }
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        
        if not raw:
            return self._create_error_result("No credit rating data available")
        
        has_rating = self._normalize_bool(raw.get("has_rating"))
        ratings = self._normalize_list(raw.get("ratings"))
        
        if not has_rating or not ratings:
            return self._create_success_result({
                "has_rating": False,
                "rating_count": 0,
                "best_rating_score": None,
                "average_rating_score": None,
                "is_investment_grade": False,
                "has_negative_outlook": False,
                "outlook_score": 50,  # Neutral for no rating
            }, extractor_results, warnings)
        
        # Calculate rating scores
        rating_scores = []
        outlook_scores = []
        
        for r in ratings:
            rating = r.get("rating")
            outlook = r.get("outlook")
            
            if rating and rating in self.RATING_SCORES:
                rating_scores.append(self.RATING_SCORES[rating])
            
            if outlook and outlook in self.OUTLOOK_SCORES:
                outlook_scores.append(self.OUTLOOK_SCORES[outlook])
        
        best_score = max(rating_scores) if rating_scores else 0
        avg_score = sum(rating_scores) / len(rating_scores) if rating_scores else 0
        avg_outlook = sum(outlook_scores) / len(outlook_scores) if outlook_scores else 50
        
        is_investment_grade = self._normalize_bool(raw.get("any_investment_grade"))
        has_negative = self._normalize_bool(raw.get("any_negative_outlook"))
        
        return self._create_success_result({
            "has_rating": True,
            "rating_count": len(ratings),
            "best_rating_score": best_score,
            "average_rating_score": round(avg_score, 1),
            "is_investment_grade": is_investment_grade,
            "has_negative_outlook": has_negative,
            "outlook_score": round(avg_outlook, 1),
        }, extractor_results, warnings)


# =============================================================================
# CORPORATE GOVERNANCE AGGREGATOR
# =============================================================================

class CorporateGovernanceAggregator(ProductionAggregator):
    """
    Transforms corporate registry data into governance/stability metrics.
    
    Expected input (from CorporateRegistryExtractor):
        {
            "data": {
                "executives": [{role, tenure_years, ...}, ...],
                "ceo_tenure_years": int,
                "recent_executive_departures": int,
                "has_dedicated_safety_officer": bool,
                "board_size": int,
                "independent_directors_pct": float,
                "years_operating": int,
                ...
            }
        }
    
    Output:
        {
            "management_stability_score": float (0-100),
            "ceo_tenure_years": int,
            "avg_executive_tenure": float,
            "recent_turnover": int,
            "has_safety_officer": bool,
            "board_independence_score": float,
            "corporate_maturity_years": int,
        }
    """
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        
        if not raw:
            return self._create_error_result("No corporate data available")
        
        # Executive stability
        ceo_tenure = self._normalize_int(raw.get("ceo_tenure_years"), 0)
        executives = self._normalize_list(raw.get("executives"))
        recent_departures = self._normalize_int(raw.get("recent_executive_departures"), 0)
        
        # Calculate average executive tenure
        if executives:
            tenures = [e.get("tenure_years", 0) for e in executives]
            avg_tenure = sum(tenures) / len(tenures)
        else:
            avg_tenure = 0
        
        # Calculate stability score
        # CEO tenure: max 40 points for 10+ years
        ceo_score = min(ceo_tenure / 10 * 40, 40)
        # Average tenure: max 30 points for 5+ years average
        tenure_score = min(avg_tenure / 5 * 30, 30)
        # Recent turnover: penalty for departures
        turnover_penalty = min(recent_departures * 10, 30)
        
        stability_score = max(0, ceo_score + tenure_score + 30 - turnover_penalty)
        
        # Board metrics
        has_safety_officer = self._normalize_bool(raw.get("has_dedicated_safety_officer"))
        board_size = self._normalize_int(raw.get("board_size"), 0)
        independence_pct = self._normalize_float(raw.get("independent_directors_pct"))
        
        # Independence score (higher independence = better governance)
        if independence_pct is not None:
            board_independence_score = independence_pct * 100
        else:
            board_independence_score = 50  # Neutral for private companies
        
        years_operating = self._normalize_int(raw.get("years_operating"), 0)
        
        return self._create_success_result({
            "management_stability_score": round(stability_score, 1),
            "ceo_tenure_years": ceo_tenure,
            "avg_executive_tenure": round(avg_tenure, 1),
            "recent_turnover": recent_departures,
            "has_safety_officer": has_safety_officer,
            "board_size": board_size,
            "board_independence_score": round(board_independence_score, 1),
            "corporate_maturity_years": years_operating,
            "is_established": years_operating >= 10,
        }, extractor_results, warnings)


# =============================================================================
# REGULATORY ENFORCEMENT AGGREGATOR
# =============================================================================

class RegulatoryEnforcementAggregator(ProductionAggregator):
    """
    Transforms enforcement action data into compliance risk metrics.
    
    Expected input (from RegulatoryEnforcementExtractor):
        {
            "data": {
                "has_enforcement_history": bool,
                "total_actions": int,
                "actions": [{action_type, severity, fine_amount, is_resolved}, ...],
                "total_fines_usd": float,
                "severe_action_count": int,
                "pending_action_count": int,
                "has_license_action": bool,
            }
        }
    
    Output:
        {
            "has_enforcement_history": bool,
            "enforcement_score": float (0-100, higher = cleaner record),
            "total_actions": int,
            "severe_actions": int,
            "pending_actions": int,
            "total_fines_usd": float,
            "has_license_action": bool,
            "enforcement_trend": str,
        }
    """
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        
        if not raw:
            return self._create_error_result("No enforcement data available")
        
        has_history = self._normalize_bool(raw.get("has_enforcement_history"))
        total_actions = self._normalize_int(raw.get("total_actions"), 0)
        severe_actions = self._normalize_int(raw.get("severe_action_count"), 0)
        pending_actions = self._normalize_int(raw.get("pending_action_count"), 0)
        total_fines = self._normalize_float(raw.get("total_fines_usd"), 0)
        has_license_action = self._normalize_bool(raw.get("has_license_action"))
        
        # Calculate enforcement score (100 = clean record, 0 = severe issues)
        if not has_history:
            enforcement_score = 100
        else:
            # Start at 100, deduct for issues
            score = 100
            score -= min(total_actions * 5, 30)  # Max 30 point deduction for volume
            score -= min(severe_actions * 15, 30)  # Severe actions cost more
            score -= min(pending_actions * 10, 20)  # Pending matters
            if has_license_action:
                score -= 20  # License actions are serious
            # Fine-based deduction (logarithmic)
            if total_fines > 0:
                import math
                fine_deduction = min(math.log10(total_fines) * 3, 20)
                score -= fine_deduction
            
            enforcement_score = max(0, score)
        
        # Determine trend (simplified - would need time series in real implementation)
        if pending_actions > 0:
            trend = "DETERIORATING"
        elif not has_history:
            trend = "CLEAN"
        else:
            trend = "STABLE"
        
        return self._create_success_result({
            "has_enforcement_history": has_history,
            "enforcement_score": round(enforcement_score, 1),
            "total_actions": total_actions,
            "severe_actions": severe_actions,
            "pending_actions": pending_actions,
            "total_fines_usd": total_fines,
            "has_license_action": has_license_action,
            "enforcement_trend": trend,
        }, extractor_results, warnings)


# =============================================================================
# INDUSTRY ENGAGEMENT AGGREGATOR
# =============================================================================

class IndustryEngagementAggregator(ProductionAggregator):
    """
    Transforms industry association data into engagement metrics.
    
    Expected input (from IndustryAssociationExtractor):
        {
            "data": {
                "membership_count": int,
                "memberships": [{association_name, prestige_level, leadership_role, ...}, ...],
                "has_high_prestige_membership": bool,
                "has_leadership_role": bool,
                "has_committee_participation": bool,
            }
        }
    
    Output:
        {
            "membership_count": int,
            "engagement_score": float (0-100),
            "has_prestige_membership": bool,
            "has_leadership_role": bool,
            "has_committee_participation": bool,
            "engagement_level": str (NONE, LOW, MODERATE, HIGH, VERY_HIGH),
        }
    """
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        
        if not raw:
            return self._create_error_result("No industry association data available")
        
        membership_count = self._normalize_int(raw.get("membership_count"), 0)
        memberships = self._normalize_list(raw.get("memberships"))
        has_prestige = self._normalize_bool(raw.get("has_high_prestige_membership"))
        has_leadership = self._normalize_bool(raw.get("has_leadership_role"))
        has_committee = self._normalize_bool(raw.get("has_committee_participation"))
        
        # Calculate engagement score
        score = 0
        
        # Membership count (max 30 points)
        score += min(membership_count * 10, 30)
        
        # High prestige membership (25 points)
        if has_prestige:
            score += 25
        
        # Leadership role (25 points)
        if has_leadership:
            score += 25
        
        # Committee participation (20 points)
        if has_committee:
            score += 20
        
        engagement_score = min(score, 100)
        
        # Determine engagement level
        if engagement_score >= 80:
            level = "VERY_HIGH"
        elif engagement_score >= 60:
            level = "HIGH"
        elif engagement_score >= 40:
            level = "MODERATE"
        elif engagement_score >= 20:
            level = "LOW"
        else:
            level = "NONE"
        
        return self._create_success_result({
            "membership_count": membership_count,
            "engagement_score": round(engagement_score, 1),
            "has_prestige_membership": has_prestige,
            "has_leadership_role": has_leadership,
            "has_committee_participation": has_committee,
            "engagement_level": level,
        }, extractor_results, warnings)


# =============================================================================
# PUBLIC FINANCIALS AGGREGATOR
# =============================================================================

class PublicFinancialsAggregator(ProductionAggregator):
    """
    Transforms financial data into stability metrics.
    
    Expected input (from PublicFinancialsExtractor):
        {
            "data": {
                "is_public": bool,
                "revenue_usd": float,
                "net_income_margin": float,
                "debt_to_equity": float,
                "current_ratio": float,
                "is_profitable": bool,
                "consecutive_profitable_years": int,
                "audit_opinion": str,
                ...
            }
        }
    
    Output:
        {
            "is_public": bool,
            "financial_health_score": float (0-100),
            "profitability_score": float,
            "leverage_score": float,
            "liquidity_score": float,
            "size_tier": str,
            "is_profitable": bool,
            "audit_concern": bool,
        }
    """
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        
        if not raw:
            return self._create_error_result("No financial data available")
        
        is_public = self._normalize_bool(raw.get("is_public"))
        
        if not is_public:
            # Limited metrics for private companies
            return self._create_success_result({
                "is_public": False,
                "financial_health_score": 50,  # Neutral
                "profitability_score": 50,
                "leverage_score": 50,
                "liquidity_score": 50,
                "size_tier": raw.get("estimated_revenue_range", "UNKNOWN"),
                "is_profitable": None,
                "audit_concern": False,
                "data_quality": "LIMITED",
            }, extractor_results, warnings)
        
        # Public company metrics
        revenue = self._normalize_float(raw.get("revenue_usd"), 0)
        margin = self._normalize_float(raw.get("net_income_margin"), 0)
        debt_equity = self._normalize_float(raw.get("debt_to_equity"), 1)
        current_ratio = self._normalize_float(raw.get("current_ratio"), 1)
        is_profitable = self._normalize_bool(raw.get("is_profitable"))
        profitable_years = self._normalize_int(raw.get("consecutive_profitable_years"), 0)
        audit_opinion = raw.get("audit_opinion", "UNQUALIFIED")
        
        # Profitability score (0-100)
        if margin >= 0.15:
            profitability = 100
        elif margin >= 0.10:
            profitability = 85
        elif margin >= 0.05:
            profitability = 70
        elif margin >= 0:
            profitability = 55
        elif margin >= -0.05:
            profitability = 40
        else:
            profitability = 20
        
        # Bonus for consecutive profitability
        profitability = min(100, profitability + profitable_years * 2)
        
        # Leverage score (lower debt = better)
        if debt_equity <= 0.5:
            leverage = 100
        elif debt_equity <= 1.0:
            leverage = 80
        elif debt_equity <= 1.5:
            leverage = 60
        elif debt_equity <= 2.0:
            leverage = 40
        else:
            leverage = 20
        
        # Liquidity score
        if current_ratio >= 2.0:
            liquidity = 100
        elif current_ratio >= 1.5:
            liquidity = 80
        elif current_ratio >= 1.0:
            liquidity = 60
        elif current_ratio >= 0.75:
            liquidity = 40
        else:
            liquidity = 20
        
        # Overall health (weighted)
        health = profitability * 0.4 + leverage * 0.3 + liquidity * 0.3
        
        # Size tier
        if revenue >= 10e9:
            size_tier = "MEGA"
        elif revenue >= 1e9:
            size_tier = "LARGE"
        elif revenue >= 100e6:
            size_tier = "MEDIUM"
        elif revenue >= 10e6:
            size_tier = "SMALL"
        else:
            size_tier = "MICRO"
        
        # Audit concern
        audit_concern = audit_opinion in ["QUALIFIED", "ADVERSE"]
        if audit_concern:
            health = max(0, health - 20)
            warnings.append(f"Audit opinion: {audit_opinion}")
        
        return self._create_success_result({
            "is_public": True,
            "financial_health_score": round(health, 1),
            "profitability_score": round(profitability, 1),
            "leverage_score": round(leverage, 1),
            "liquidity_score": round(liquidity, 1),
            "size_tier": size_tier,
            "is_profitable": is_profitable,
            "audit_concern": audit_concern,
            "data_quality": "FULL",
        }, extractor_results, warnings)


# =============================================================================
# INCIDENT HISTORY AGGREGATOR
# =============================================================================

class IncidentHistoryAggregator(ProductionAggregator):
    """
    Transforms generic incident history into risk metrics.
    
    Expected input (from IncidentHistoryExtractor):
        {
            "data": {
                "has_incidents": bool,
                "total_incidents": int,
                "incidents": [{severity, operator_cited, fatalities, ...}, ...],
                "fatal_incident_count": int,
                "severe_incident_count": int,
                "operator_cited_count": int,
            }
        }
    
    Output:
        {
            "has_incidents": bool,
            "incident_score": float (0-100, higher = cleaner record),
            "total_incidents": int,
            "severe_incidents": int,
            "fatal_incidents": int,
            "operator_at_fault_count": int,
            "incident_severity_rating": str,
        }
    """
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        
        if not raw:
            return self._create_error_result("No incident data available")
        
        has_incidents = self._normalize_bool(raw.get("has_incidents"))
        total_incidents = self._normalize_int(raw.get("total_incidents"), 0)
        fatal_count = self._normalize_int(raw.get("fatal_incident_count"), 0)
        severe_count = self._normalize_int(raw.get("severe_incident_count"), 0)
        operator_cited = self._normalize_int(raw.get("operator_cited_count"), 0)
        
        # Calculate incident score
        if not has_incidents:
            incident_score = 100
        else:
            score = 100
            # Deductions
            score -= min(total_incidents * 3, 20)  # Volume penalty
            score -= fatal_count * 25  # Fatal incidents are very serious
            score -= severe_count * 10  # Severe incidents
            score -= operator_cited * 5  # Fault attribution
            
            incident_score = max(0, score)
        
        # Severity rating
        if fatal_count > 0:
            severity_rating = "CRITICAL"
        elif severe_count > 2:
            severity_rating = "HIGH"
        elif severe_count > 0 or total_incidents > 5:
            severity_rating = "MODERATE"
        elif total_incidents > 0:
            severity_rating = "LOW"
        else:
            severity_rating = "CLEAN"
        
        return self._create_success_result({
            "has_incidents": has_incidents,
            "incident_score": round(incident_score, 1),
            "total_incidents": total_incidents,
            "severe_incidents": severe_count,
            "fatal_incidents": fatal_count,
            "operator_at_fault_count": operator_cited,
            "incident_severity_rating": severity_rating,
        }, extractor_results, warnings)
