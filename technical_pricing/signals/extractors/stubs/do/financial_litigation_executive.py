"""
D&O Stub Extractors - Financial, Litigation, Executive Signal Groups

FINANCIAL signals:
- audit_opinion: Type of audit opinion
- internal_controls: SOX 404 assessment
- restatement: Financial restatement history
- filing_timeliness: SEC filing timeliness
- revenue_recognition: Revenue recognition risk
- debt_covenant: Debt covenant compliance
- stock_volatility: Stock price volatility
- short_interest: Short interest percentage

LITIGATION signals:
- securities_litigation: Securities class actions
- derivative_litigation: Shareholder derivative suits
- sec_enforcement: SEC enforcement actions
- regulatory_action: Other regulatory actions
- pending_litigation: Material pending litigation
- whistleblower: Whistleblower activity

EXECUTIVE signals:
- executive_stability: CEO/CFO tenure and turnover
- cfo_quality: CFO experience and credentials
- insider_trading: Form 4 trading patterns
- executive_background: Executive background checks
- trading_plan: 10b5-1 plan usage
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import random

from ...base import StubExtractor, utcnow


# =============================================================================
# FINANCIAL EXTRACTORS
# =============================================================================

class AuditOpinionExtractor(StubExtractor):
    """
    STUB: Simulates audit opinion lookup.
    
    Source: 10-K filings
    """
    SOURCE_NAME = "audit_opinion"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        opinion = self._random_choice(
            ["UNQUALIFIED", "UNQUALIFIED_EMPHASIS", "QUALIFIED", "ADVERSE", "DISCLAIMER"],
            weights=[0.85, 0.08, 0.04, 0.02, 0.01]
        )
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "audit_opinion": opinion,
                "is_clean_opinion": opinion == "UNQUALIFIED",
                "has_going_concern": self._random_bool(0.05),
                "has_emphasis_of_matter": opinion == "UNQUALIFIED_EMPHASIS",
                "opinion_score": {"UNQUALIFIED": 100, "UNQUALIFIED_EMPHASIS": 80, "QUALIFIED": 40, "ADVERSE": 10, "DISCLAIMER": 5}.get(opinion, 50),
            }
        }
        return self._create_success_result(data)


class InternalControlsExtractor(StubExtractor):
    """
    STUB: Simulates SOX 404 internal controls assessment.
    
    Source: 10-K filings
    """
    SOURCE_NAME = "internal_controls"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_weakness = self._random_bool(0.08)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "internal_controls_effective": not has_weakness,
                "material_weakness": has_weakness,
                "significant_deficiencies": self._random_int(0, 3),
                "remediation_in_progress": has_weakness and self._random_bool(0.7),
                "sox404_exempt": self._random_bool(0.15),  # Smaller companies
                "controls_score": 30 if has_weakness else self._random_int(75, 100),
            }
        }
        return self._create_success_result(data)


class RestatementExtractor(StubExtractor):
    """
    STUB: Simulates financial restatement history lookup.
    
    Source: SEC filings, Audit Analytics
    """
    SOURCE_NAME = "restatement_history"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_restatement = self._random_bool(0.12)
        
        if has_restatement:
            restatement_count = self._random_int(1, 3)
            severity = self._random_choice(["MATERIAL", "IMMATERIAL"], weights=[0.4, 0.6])
            years_since = self._random_float(0.5, 5)
        else:
            restatement_count = 0
            severity = None
            years_since = None
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "has_restatement_5yr": has_restatement,
                "restatement_count": restatement_count,
                "most_recent_severity": severity,
                "years_since_restatement": years_since,
                "fraud_related": self._random_bool(0.1) if has_restatement else False,
                "restatement_score": 100 if not has_restatement else (40 if severity == "MATERIAL" else 70),
            }
        }
        return self._create_success_result(data)


class FilingTimelinessExtractor(StubExtractor):
    """
    STUB: Simulates SEC filing timeliness check.
    
    Source: SEC EDGAR
    """
    SOURCE_NAME = "filing_timeliness"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        late_filings = self._random_int(0, 3)
        nt_filings = self._random_int(0, 2)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "late_filings_3yr": late_filings,
                "nt_filings_3yr": nt_filings,
                "always_timely": late_filings == 0 and nt_filings == 0,
                "filer_status": self._random_choice(["LARGE_ACCELERATED", "ACCELERATED", "NON_ACCELERATED", "SMALLER_REPORTING"]),
                "timeliness_score": max(0, 100 - late_filings * 20 - nt_filings * 15),
            }
        }
        return self._create_success_result(data)


class RevenueRecognitionExtractor(StubExtractor):
    """
    STUB: Simulates revenue recognition risk assessment.
    
    Source: 10-K, revenue policy analysis
    """
    SOURCE_NAME = "revenue_recognition"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        complexity = self._random_choice(["LOW", "MODERATE", "HIGH"], weights=[0.4, 0.4, 0.2])
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "revenue_complexity": complexity,
                "has_long_term_contracts": self._random_bool(0.4),
                "has_multiple_elements": self._random_bool(0.5),
                "has_significant_estimates": self._random_bool(0.3),
                "deferred_revenue_significant": self._random_bool(0.35),
                "revenue_risk_score": {"LOW": 90, "MODERATE": 65, "HIGH": 40}.get(complexity, 50),
            }
        }
        return self._create_success_result(data)


class DebtCovenantExtractor(StubExtractor):
    """
    STUB: Simulates debt covenant compliance analysis.
    
    Source: 10-K, credit agreements
    """
    SOURCE_NAME = "debt_covenant"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_debt = self._random_bool(0.7)
        
        if has_debt:
            in_compliance = self._random_bool(0.92)
            headroom_pct = self._random_float(5, 50) if in_compliance else self._random_float(-10, 5)
        else:
            in_compliance = None
            headroom_pct = None
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "has_material_debt": has_debt,
                "covenant_compliant": in_compliance,
                "covenant_headroom_pct": headroom_pct,
                "near_breach": headroom_pct is not None and headroom_pct < 15,
                "waiver_obtained": self._random_bool(0.1) if has_debt else False,
                "covenant_score": 100 if not has_debt else (90 if in_compliance and headroom_pct > 20 else 60 if in_compliance else 20),
            }
        }
        return self._create_success_result(data)


class StockVolatilityExtractor(StubExtractor):
    """
    STUB: Simulates stock price volatility analysis.
    
    Source: Market data
    """
    SOURCE_NAME = "stock_volatility"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        volatility = self._random_float(15, 80)
        beta = self._random_float(0.5, 2.5)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "volatility_252d": round(volatility, 1),
                "beta": round(beta, 2),
                "max_drawdown_1yr": self._random_float(10, 60),
                "vs_sector_volatility": self._random_choice(["LOWER", "SIMILAR", "HIGHER"]),
                "volatility_score": max(0, 100 - volatility),
            }
        }
        return self._create_success_result(data)


class ShortInterestExtractor(StubExtractor):
    """
    STUB: Simulates short interest analysis.
    
    Source: FINRA, exchange data
    """
    SOURCE_NAME = "short_interest"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        short_pct = self._random_float(1, 30)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "short_interest_pct": round(short_pct, 1),
                "days_to_cover": self._random_float(1, 15),
                "short_interest_change_30d": self._random_float(-20, 30),
                "is_heavily_shorted": short_pct > 15,
                "short_interest_score": max(0, 100 - short_pct * 3),
            }
        }
        return self._create_success_result(data)


# =============================================================================
# LITIGATION EXTRACTORS
# =============================================================================

class SecuritiesLitigationExtractor(StubExtractor):
    """
    STUB: Simulates securities class action history lookup.
    
    Source: SCAS, PACER, news
    """
    SOURCE_NAME = "securities_litigation"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_litigation = self._random_bool(0.15)
        
        if has_litigation:
            case_count = self._random_int(1, 3)
            active = self._random_bool(0.4)
            years_since = self._random_float(0.1, 5)
        else:
            case_count = 0
            active = False
            years_since = None
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "has_securities_litigation_5yr": has_litigation,
                "case_count": case_count,
                "active_case": active,
                "years_since_last": years_since,
                "total_settlements": self._random_int(0, 100_000_000) if has_litigation else 0,
                "litigation_score": 100 if not has_litigation else (25 if active else 60),
            }
        }
        return self._create_success_result(data)


class DerivativeLitigationExtractor(StubExtractor):
    """
    STUB: Simulates derivative litigation history.
    
    Source: PACER, news
    """
    SOURCE_NAME = "derivative_litigation"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_derivative = self._random_bool(0.10)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "has_derivative_litigation_5yr": has_derivative,
                "case_count": self._random_int(1, 2) if has_derivative else 0,
                "demand_refused": self._random_bool(0.6) if has_derivative else False,
                "active_case": self._random_bool(0.3) if has_derivative else False,
                "derivative_score": 100 if not has_derivative else 65,
            }
        }
        return self._create_success_result(data)


class SECEnforcementExtractor(StubExtractor):
    """
    STUB: Simulates SEC enforcement history.
    
    Source: SEC enforcement database
    """
    SOURCE_NAME = "sec_enforcement"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_enforcement = self._random_bool(0.08)
        
        if has_enforcement:
            action_type = self._random_choice(["CEASE_DESIST", "CIVIL_PENALTY", "FRAUD", "DISCLOSURE"])
            penalty = self._random_int(100_000, 50_000_000)
            active = self._random_bool(0.3)
        else:
            action_type = None
            penalty = 0
            active = False
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "has_sec_enforcement_5yr": has_enforcement,
                "action_type": action_type,
                "penalty_amount": penalty,
                "active_investigation": active,
                "officer_named": self._random_bool(0.4) if has_enforcement else False,
                "enforcement_score": 100 if not has_enforcement else (20 if active else 55),
            }
        }
        return self._create_success_result(data)


class RegulatoryActionExtractor(StubExtractor):
    """
    STUB: Simulates non-SEC regulatory action history.
    
    Source: DOJ, state AG, CFPB databases
    """
    SOURCE_NAME = "regulatory_action"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_action = self._random_bool(0.12)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "has_regulatory_action_5yr": has_action,
                "action_count": self._random_int(1, 3) if has_action else 0,
                "agencies_involved": self._random_sample(["DOJ", "FTC", "CFPB", "STATE_AG", "EPA", "OSHA"], self._random_int(1, 2)) if has_action else [],
                "total_fines": self._random_int(100_000, 25_000_000) if has_action else 0,
                "criminal_charges": self._random_bool(0.1) if has_action else False,
                "regulatory_score": 100 if not has_action else 60,
            }
        }
        return self._create_success_result(data)


class PendingLitigationExtractor(StubExtractor):
    """
    STUB: Simulates material pending litigation analysis.
    
    Source: 10-K, 10-Q disclosures
    """
    SOURCE_NAME = "pending_litigation"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_pending = self._random_bool(0.25)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "has_material_pending": has_pending,
                "matter_count": self._random_int(1, 5) if has_pending else 0,
                "estimated_exposure": self._random_int(1_000_000, 100_000_000) if has_pending else 0,
                "accrual_recorded": self._random_bool(0.6) if has_pending else False,
                "types": self._random_sample(["PRODUCT_LIABILITY", "EMPLOYMENT", "IP", "CONTRACT", "ENVIRONMENTAL"], self._random_int(1, 2)) if has_pending else [],
                "pending_score": 100 if not has_pending else 65,
            }
        }
        return self._create_success_result(data)


class WhistleblowerExtractor(StubExtractor):
    """
    STUB: Simulates whistleblower activity indicators.
    
    Source: SEC tips, news, Glassdoor
    """
    SOURCE_NAME = "whistleblower"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_activity = self._random_bool(0.05)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "whistleblower_activity_detected": has_activity,
                "sec_tip_indicator": self._random_bool(0.5) if has_activity else False,
                "retaliation_claims": self._random_bool(0.3) if has_activity else False,
                "glassdoor_ethics_concerns": self._random_bool(0.15),
                "whistleblower_score": 100 if not has_activity else 50,
            }
        }
        return self._create_success_result(data)


# =============================================================================
# EXECUTIVE EXTRACTORS
# =============================================================================

class ExecutiveStabilityExtractor(StubExtractor):
    """
    STUB: Simulates executive team stability analysis.
    
    Source: Proxy statements, 8-K filings
    """
    SOURCE_NAME = "executive_stability"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        ceo_tenure = self._random_float(0.5, 20)
        cfo_tenure = self._random_float(0.5, 15)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "ceo_tenure_years": round(ceo_tenure, 1),
                "cfo_tenure_years": round(cfo_tenure, 1),
                "ceo_change_3yr": self._random_bool(0.25),
                "cfo_change_3yr": self._random_bool(0.35),
                "c_suite_turnover_rate": self._random_float(0, 40),
                "stability_score": min(100, (ceo_tenure + cfo_tenure) * 5),
            }
        }
        return self._create_success_result(data)


class CFOQualityExtractor(StubExtractor):
    """
    STUB: Simulates CFO quality assessment.
    
    Source: Proxy, LinkedIn, background
    """
    SOURCE_NAME = "cfo_quality"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "cfo_big4_background": self._random_bool(0.45),
                "cfo_public_company_experience": self._random_bool(0.7),
                "cfo_industry_experience_years": self._random_int(5, 30),
                "cpa_certified": self._random_bool(0.6),
                "cfo_prior_cfo_roles": self._random_int(0, 4),
                "cfo_quality_score": self._random_float(40, 95),
            }
        }
        return self._create_success_result(data)


class InsiderTradingExtractor(StubExtractor):
    """
    STUB: Simulates Form 4 insider trading analysis.
    
    Source: SEC Form 4 filings
    """
    SOURCE_NAME = "insider_trading"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        net_direction = self._random_choice(["NET_BUYER", "NEUTRAL", "NET_SELLER"], weights=[0.2, 0.5, 0.3])
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "net_insider_activity": net_direction,
                "insider_buys_12m": self._random_int(0, 20),
                "insider_sells_12m": self._random_int(0, 50),
                "cluster_selling": self._random_bool(0.1),
                "unusual_timing": self._random_bool(0.08),
                "insider_trading_score": {"NET_BUYER": 85, "NEUTRAL": 70, "NET_SELLER": 55}.get(net_direction, 60),
            }
        }
        return self._create_success_result(data)


class ExecutiveBackgroundExtractor(StubExtractor):
    """
    STUB: Simulates executive background check.
    
    Source: Background databases, news
    """
    SOURCE_NAME = "executive_background"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_MONTHLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_issues = self._random_bool(0.08)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "background_issues_found": has_issues,
                "bankruptcy_history": self._random_bool(0.05),
                "prior_enforcement_action": self._random_bool(0.03),
                "litigation_named_defendant": self._random_bool(0.1),
                "credential_verified": self._random_bool(0.95),
                "background_score": 100 if not has_issues else 50,
            }
        }
        return self._create_success_result(data)


class TradingPlanExtractor(StubExtractor):
    """
    STUB: Simulates 10b5-1 trading plan usage analysis.
    
    Source: Form 4, 8-K disclosures
    """
    SOURCE_NAME = "trading_plan"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_WEEKLY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_plans = self._random_bool(0.5)
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "has_10b5_1_plans": has_plans,
                "plan_coverage_pct": self._random_float(30, 90) if has_plans else 0,
                "plan_modifications_12m": self._random_int(0, 5) if has_plans else 0,
                "compliant_cooling_off": self._random_bool(0.8) if has_plans else None,
                "trading_plan_score": 80 if has_plans else 50,
            }
        }
        return self._create_success_result(data)
