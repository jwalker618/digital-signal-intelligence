"""
D&O Aggregators - All Signal Groups

Production-ready aggregators for D&O coverage signals.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from ...base import ProductionAggregator
from ....types import AggregatorResult, ExtractorResult


# =============================================================================
# NETWORK AUTHORITY AGGREGATORS
# =============================================================================

class AuditorQualityAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No auditor data")
        tier = self._normalize_int(raw.get("auditor_tier"), 3)
        score = {1: 95, 2: 75, 3: 50}.get(tier, 50)
        if raw.get("auditor_change_recent"):
            score -= 10
        return self._create_success_result({"auditor_tier": tier, "auditor_quality_score": max(0, score)}, extractor_results)


class LegalCounselAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No legal data")
        tier = self._normalize_int(raw.get("counsel_tier"), 3)
        return self._create_success_result({"counsel_tier": tier, "legal_counsel_score": {1: 95, 2: 75, 3: 50}.get(tier, 50)}, extractor_results)


class DOBankingRelationshipAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No banking data")
        has_rel = self._normalize_bool(raw.get("has_banking_relationship"))
        tier = self._normalize_int(raw.get("bank_tier"), 3) if has_rel else None
        score = {1: 90, 2: 70, 3: 55}.get(tier, 40) if has_rel else 40
        return self._create_success_result({"has_relationship": has_rel, "banking_relationship_score": score}, extractor_results)


class InvestorQualityAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No investor data")
        inst_pct = self._normalize_float(raw.get("institutional_ownership_pct"), 50)
        quality = self._normalize_float(raw.get("top_10_quality_score"), 50)
        return self._create_success_result({"institutional_pct": inst_pct, "investor_quality_score": round(inst_pct * 0.4 + quality * 0.6, 1)}, extractor_results)


class BoardNetworkAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No board network data")
        return self._create_success_result({"board_network_score": round(self._normalize_float(raw.get("network_quality_score"), 50), 1)}, extractor_results)


class IndexInclusionAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No index data")
        in_index = self._normalize_bool(raw.get("in_major_index"))
        tier = self._normalize_int(raw.get("index_tier"), 4) if in_index else 4
        return self._create_success_result({"in_major_index": in_index, "index_inclusion_score": {1: 100, 2: 80, 3: 60, 4: 30}.get(tier, 30)}, extractor_results)


class AnalystCoverageAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No analyst data")
        count = self._normalize_int(raw.get("analyst_count"), 0)
        tier1 = self._normalize_int(raw.get("tier1_analyst_count"), 0)
        return self._create_success_result({"analyst_count": count, "analyst_coverage_score": min(100, count * 3 + tier1 * 5 + 20)}, extractor_results)


# =============================================================================
# GOVERNANCE AGGREGATORS
# =============================================================================

class BoardIndependenceAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No independence data")
        pct = self._normalize_float(raw.get("independence_percentage"), 50)
        warnings = ["Board independence below 50%"] if pct < 50 else []
        return self._create_success_result({"independence_pct": pct, "board_independence_score": round(min(100, pct * 1.1), 1)}, extractor_results, warnings)


class BoardDiversityAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No diversity data")
        pct = self._normalize_float(raw.get("gender_diversity_pct"), 0)
        return self._create_success_result({"gender_diversity_pct": pct, "board_diversity_score": round(min(100, pct * 2 + 30), 1)}, extractor_results)


class CEOChairSeparationAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No separation data")
        separated = self._normalize_bool(raw.get("ceo_chair_separated"))
        lead_ind = self._normalize_bool(raw.get("has_lead_independent"))
        score = 100 if separated else (70 if lead_ind else 40)
        return self._create_success_result({"separated": separated, "ceo_chair_separation_score": score}, extractor_results)


class CommitteeStructureAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No committee data")
        score = 40
        if self._normalize_bool(raw.get("has_audit_committee")): score += 20
        if self._normalize_bool(raw.get("has_compensation_committee")): score += 15
        if self._normalize_bool(raw.get("has_nominating_committee")): score += 15
        if self._normalize_bool(raw.get("audit_financial_expert")): score += 10
        return self._create_success_result({"committee_structure_score": min(100, score)}, extractor_results)


class BoardRefreshmentAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No refreshment data")
        return self._create_success_result({"board_refreshment_score": round(self._normalize_float(raw.get("refreshment_score"), 50), 1)}, extractor_results)


class RelatedPartyAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No related party data")
        has_rpts = self._normalize_bool(raw.get("has_related_party_transactions"))
        concerns = self._normalize_bool(raw.get("material_rpt_concerns"))
        warnings = ["Material related party concerns"] if concerns else []
        score = 100 if not has_rpts else (30 if concerns else 70)
        return self._create_success_result({"related_party_score": score}, extractor_results, warnings)


class CompensationStructureAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No compensation data")
        say_on_pay = self._normalize_float(raw.get("say_on_pay_support_pct"), 70)
        perf_pct = self._normalize_float(raw.get("performance_based_pct"), 50)
        return self._create_success_result({"compensation_structure_score": round(say_on_pay * 0.6 + perf_pct * 0.4, 1)}, extractor_results)


class ShareholderRightsAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No rights data")
        return self._create_success_result({"shareholder_rights_score": round(self._normalize_float(raw.get("shareholder_friendly_score"), 50), 1)}, extractor_results)


# =============================================================================
# FINANCIAL AGGREGATORS
# =============================================================================

class AuditOpinionAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No audit data")
        score = self._normalize_int(raw.get("opinion_score"), 50)
        warnings = []
        if raw.get("has_going_concern"):
            score = min(score, 20)
            warnings.append("Going concern opinion")
        return self._create_success_result({"audit_opinion_score": score}, extractor_results, warnings)


class InternalControlsAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No controls data")
        warnings = ["Material weakness in internal controls"] if raw.get("material_weakness") else []
        return self._create_success_result({"internal_controls_score": self._normalize_int(raw.get("controls_score"), 50)}, extractor_results, warnings)


class RestatementAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No restatement data")
        warnings = ["Financial restatement history"] if raw.get("has_restatement_5yr") else []
        return self._create_success_result({"restatement_score": self._normalize_int(raw.get("restatement_score"), 100)}, extractor_results, warnings)


class FilingTimelinessAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No filing data")
        return self._create_success_result({"filing_timeliness_score": self._normalize_int(raw.get("timeliness_score"), 100)}, extractor_results)


class RevenueRecognitionAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No revenue data")
        return self._create_success_result({"revenue_recognition_score": self._normalize_int(raw.get("revenue_risk_score"), 70)}, extractor_results)


class DebtCovenantAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No covenant data")
        return self._create_success_result({"debt_covenant_score": self._normalize_int(raw.get("covenant_score"), 100)}, extractor_results)


class StockVolatilityAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No volatility data")
        return self._create_success_result({"stock_volatility_score": self._normalize_int(raw.get("volatility_score"), 50)}, extractor_results)


class ShortInterestAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No short interest data")
        return self._create_success_result({"short_interest_score": self._normalize_int(raw.get("short_interest_score"), 70)}, extractor_results)


# =============================================================================
# LITIGATION AGGREGATORS
# =============================================================================

class SecuritiesLitigationAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No litigation data")
        warnings = ["Active securities litigation"] if raw.get("active_case") else []
        return self._create_success_result({"securities_litigation_score": self._normalize_int(raw.get("litigation_score"), 100)}, extractor_results, warnings)


class DerivativeLitigationAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No derivative data")
        return self._create_success_result({"derivative_litigation_score": self._normalize_int(raw.get("derivative_score"), 100)}, extractor_results)


class SECEnforcementAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No SEC data")
        warnings = ["Active SEC investigation"] if raw.get("active_investigation") else []
        return self._create_success_result({"sec_enforcement_score": self._normalize_int(raw.get("enforcement_score"), 100)}, extractor_results, warnings)


class DORegulatoryActionAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No regulatory data")
        return self._create_success_result({"regulatory_action_score": self._normalize_int(raw.get("regulatory_score"), 100)}, extractor_results)


class PendingLitigationAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No pending litigation data")
        return self._create_success_result({"pending_litigation_score": self._normalize_int(raw.get("pending_score"), 100)}, extractor_results)


class WhistleblowerAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No whistleblower data")
        return self._create_success_result({"whistleblower_score": self._normalize_int(raw.get("whistleblower_score"), 100)}, extractor_results)


# =============================================================================
# EXECUTIVE AGGREGATORS
# =============================================================================

class ExecutiveStabilityAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No stability data")
        return self._create_success_result({"executive_stability_score": round(self._normalize_float(raw.get("stability_score"), 50), 1)}, extractor_results)


class CFOQualityAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No CFO data")
        return self._create_success_result({"cfo_quality_score": round(self._normalize_float(raw.get("cfo_quality_score"), 50), 1)}, extractor_results)


class InsiderTradingAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No trading data")
        warnings = ["Unusual insider trading pattern"] if raw.get("cluster_selling") or raw.get("unusual_timing") else []
        return self._create_success_result({"insider_trading_score": self._normalize_int(raw.get("insider_trading_score"), 70)}, extractor_results, warnings)


class ExecutiveBackgroundAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No background data")
        warnings = ["Executive background concerns"] if raw.get("background_issues_found") else []
        return self._create_success_result({"executive_background_score": self._normalize_int(raw.get("background_score"), 100)}, extractor_results, warnings)


class TradingPlanAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No trading plan data")
        return self._create_success_result({"trading_plan_score": self._normalize_int(raw.get("trading_plan_score"), 50)}, extractor_results)


# =============================================================================
# CORPORATE FOOTPRINT AGGREGATORS
# =============================================================================

class InvestorRelationsAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No IR data")
        return self._create_success_result({"investor_relations_score": round(self._normalize_float(raw.get("ir_quality_score"), 50), 1)}, extractor_results)


class GovernancePageAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No governance page data")
        return self._create_success_result({"governance_page_score": round(self._normalize_float(raw.get("governance_page_score"), 30), 1)}, extractor_results)


class ESGReportingAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No ESG reporting data")
        return self._create_success_result({"esg_reporting_score": round(self._normalize_float(raw.get("esg_reporting_score"), 30), 1)}, extractor_results)


class PressReleaseAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No press data")
        return self._create_success_result({"press_release_score": self._normalize_int(raw.get("press_release_score"), 50)}, extractor_results)


class LeadershipVisibilityAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No visibility data")
        return self._create_success_result({"leadership_visibility_score": round(self._normalize_float(raw.get("visibility_score"), 50), 1)}, extractor_results)


class HiringSignalsAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No hiring data")
        return self._create_success_result({"hiring_signals_score": round(self._normalize_float(raw.get("hiring_signals_score"), 50), 1)}, extractor_results)


# =============================================================================
# STRUCTURED DATA AGGREGATORS
# =============================================================================

class ESGRatingAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No ESG rating data")
        return self._create_success_result({"esg_rating_score": self._normalize_int(raw.get("esg_rating_score"), 50)}, extractor_results)


class GovernanceRatingAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No governance rating data")
        return self._create_success_result({"governance_rating_score": round(self._normalize_float(raw.get("governance_score"), 50), 1)}, extractor_results)


class ISSGovernanceAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No ISS data")
        return self._create_success_result({"iss_governance_score": self._normalize_int(raw.get("iss_governance_score"), 50)}, extractor_results)


# =============================================================================
# CATEGORICAL AGGREGATORS
# =============================================================================

class CompanyTypeAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No company type data")
        return self._create_success_result({"company_type": raw.get("company_type"), "is_public": raw.get("is_public"), "market_cap": raw.get("market_cap")}, extractor_results)


class DOIndustryAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No industry data")
        return self._create_success_result({"primary_industry": raw.get("primary_industry"), "is_high_risk": raw.get("is_high_risk_industry")}, extractor_results)


class StockExchangeAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No exchange data")
        return self._create_success_result({"primary_exchange": raw.get("primary_exchange"), "is_listed": raw.get("is_listed")}, extractor_results)
