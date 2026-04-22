"""
D&O Inference Functions - All Signal Groups

Maps YAML inference_utility_function names to pipeline orchestration.
Each function: Extractor → Aggregator → SignalResult

Signal Groups:
- Categorical: company_type, industry, stock_exchange
- network_authority: 8 signals
- governance: 8 signals
- financial: 8 signals
- litigation: 6 signals
- executive: 5 signals
- corporate_footprint: 6 signals
- structured_data: 4 signals (1 uses common)
"""

import time
from typing import Dict, Any

from ....types import SignalResult, InferenceContext
from ....inference.registry import register_inference_function

# Import all extractors

# Import all aggregators

# V6/E10 neutral stand-ins — real extractor wiring lands via the
# D-series production extractors (Stage 6). Until then every call
# returns a neutral SignalResult(score=50, confidence=0.5).

def _run_pipeline(signal_id, *args, default=50.0, **kwargs):
    """Neutral scoring stand-in. Accepts the legacy
    (signal_id, extractor, aggregator, entity_id, context, ...)
    signature but ignores the extractor + aggregator args."""
    return SignalResult(
        signal_id=signal_id,
        score=float(default),
        confidence=0.5,
        execution_time_ms=0.0,
    )


def _run_categorical(signal_id, *args, default="OTHER", **kwargs):
    """Neutral categorical stand-in — see _run_pipeline."""
    return SignalResult(
        signal_id=signal_id,
        category=default,
        confidence=0.5,
        execution_time_ms=0.0,
    )


def _run_pipeline(signal_id: str, extractor, aggregator, entity_id: str, context, score_field: str, default: float = 50, **extract_kwargs) -> SignalResult:
    """Helper to run standard Extractor → Aggregator pipeline."""
    start_time = time.time()
    try:
        ext_result = extractor.extract(entity_id, context=context, **extract_kwargs)
        if not ext_result.success:
            return SignalResult(signal_id=signal_id, score=default, confidence=0.3, error="Extraction failed")
        
        agg_result = aggregator.aggregate([ext_result])
        score = agg_result.data.get(score_field, default) if agg_result.success else default
        execution_time = (time.time() - start_time) * 1000
        
        return SignalResult(
            signal_id=signal_id, score=round(score, 1), confidence=1.0,
            execution_time_ms=execution_time, raw_data=ext_result.data,
            aggregated_data=agg_result.data,
            metadata={"extractor": type(extractor).__name__, "aggregator": type(aggregator).__name__, "from_cache": ext_result.from_cache}
        )
    except Exception as e:
        return SignalResult(signal_id=signal_id, score=default, confidence=0.0, error=str(e))


def _run_categorical(signal_id: str, extractor, aggregator, entity_id: str, context, cat_field: str, default: str) -> SignalResult:
    """Helper for categorical inference functions."""
    start_time = time.time()
    try:
        ext_result = extractor.extract(entity_id, context=context)
        if not ext_result.success:
            return SignalResult(signal_id=signal_id, category=default, confidence=0.3, error="Extraction failed")
        
        agg_result = aggregator.aggregate([ext_result])
        category = agg_result.data.get(cat_field, default) if agg_result.success else default
        execution_time = (time.time() - start_time) * 1000
        
        return SignalResult(
            signal_id=signal_id, category=category, confidence=0.85,
            execution_time_ms=execution_time, raw_data=ext_result.data, aggregated_data=agg_result.data,
            metadata={"extractor": type(extractor).__name__, "aggregator": type(aggregator).__name__}
        )
    except Exception as e:
        return SignalResult(signal_id=signal_id, category=default, confidence=0.0, error=str(e))


# =============================================================================
# CATEGORICAL FUNCTIONS
# =============================================================================

@register_inference_function("company_type_basefunction")
def company_type_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_categorical("company_type", None, None, entity_id, context, "company_type", "PRIVATE_OTHER")


@register_inference_function("do_industry_classification_basefunction")
def do_industry_classification_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_categorical("industry", None, None, entity_id, context, "primary_industry", "OTHER")


@register_inference_function("stock_exchange_basefunction")
def stock_exchange_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_categorical("stock_exchange", None, None, entity_id, context, "primary_exchange", "NONE")


# =============================================================================
# NETWORK AUTHORITY FUNCTIONS
# =============================================================================

@register_inference_function("auditor_quality_basefunction")
def auditor_quality_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("auditor_quality", None, None, entity_id, context, "auditor_quality_score", 50)


@register_inference_function("legal_counsel_basefunction")
def legal_counsel_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("legal_counsel", None, None, entity_id, context, "legal_counsel_score", 50)


@register_inference_function("bankinbg_relationship_basefunction")
def banking_relationship_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("banking_relationship", None, None, entity_id, context, "banking_relationship_score", 40)


@register_inference_function("investor_quality_basefunction")
def investor_quality_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("investor_quality", None, None, entity_id, context, "investor_quality_score", 50)


@register_inference_function("board_network_basefunction")
def board_network_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("board_network", None, None, entity_id, context, "board_network_score", 50)


@register_inference_function("index_inclusion_basefunction")
def index_inclusion_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("index_inclusion", None, None, entity_id, context, "index_inclusion_score", 30)


@register_inference_function("analyst_coverage_basefunction")
def analyst_coverage_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("analyst_coverage", None, None, entity_id, context, "analyst_coverage_score", 30)


@register_inference_function("industry_association_basefunction")
def industry_association_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("industry_association", None, None, entity_id, context, "engagement_score", 40, industry="CORPORATE")


# =============================================================================
# GOVERNANCE FUNCTIONS
# =============================================================================

@register_inference_function("board_independance_basefunction")
def board_independence_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("board_independence", None, None, entity_id, context, "board_independence_score", 50)


@register_inference_function("board_diversity_basefunction")
def board_diversity_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("board_diversity", None, None, entity_id, context, "board_diversity_score", 40)


@register_inference_function("ceo_chairseperation_basefunction")
def ceo_chair_separation_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("ceo_chair_separation", None, None, entity_id, context, "ceo_chair_separation_score", 50)


@register_inference_function("committee_structure_basefunction")
def committee_structure_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("committee_structure", None, None, entity_id, context, "committee_structure_score", 60)


@register_inference_function("board_refreshment_basefunction")
def board_refreshment_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("board_refreshment", None, None, entity_id, context, "board_refreshment_score", 50)


@register_inference_function("related_party_basefunction")
def related_party_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("related_party", None, None, entity_id, context, "related_party_score", 70)


@register_inference_function("compensation_structure_basefunction")
def compensation_structure_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("compensation_structure", None, None, entity_id, context, "compensation_structure_score", 60)


@register_inference_function("shareholder_rights_basefunction")
def shareholder_rights_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("shareholder_rights", None, None, entity_id, context, "shareholder_rights_score", 50)


# =============================================================================
# FINANCIAL FUNCTIONS
# =============================================================================

@register_inference_function("audit_opinion_basefunction")
def audit_opinion_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("audit_opinion", None, None, entity_id, context, "audit_opinion_score", 80)


@register_inference_function("internal_controls_basefunction")
def internal_controls_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("internal_controls", None, None, entity_id, context, "internal_controls_score", 70)


@register_inference_function("restatement_basefunction")
def restatement_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("restatement", None, None, entity_id, context, "restatement_score", 100)


@register_inference_function("filing_timelienness_basefunction")
def filing_timeliness_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("filing_timeliness", None, None, entity_id, context, "filing_timeliness_score", 90)


@register_inference_function("revenue_recognition_basefunction")
def revenue_recognition_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("revenue_recognition", None, None, entity_id, context, "revenue_recognition_score", 70)


@register_inference_function("devt_covernent_basefunction")
def debt_covenant_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("debt_covenant", None, None, entity_id, context, "debt_covenant_score", 90)


@register_inference_function("stock_volaitlity_basefunction")
def stock_volatility_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("stock_volatility", None, None, entity_id, context, "stock_volatility_score", 50)


@register_inference_function("short_interest_basefunction")
def short_interest_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("short_interest", None, None, entity_id, context, "short_interest_score", 70)


# =============================================================================
# LITIGATION FUNCTIONS
# =============================================================================

@register_inference_function("securities_litigation_basefunction")
def securities_litigation_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("securities_litigation", None, None, entity_id, context, "securities_litigation_score", 100)


@register_inference_function("derivitaive_litigation_basefunction")
def derivative_litigation_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("derivative_litigation", None, None, entity_id, context, "derivative_litigation_score", 100)


@register_inference_function("sec_enforcement_basefunction")
def sec_enforcement_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("sec_enforcement", None, None, entity_id, context, "sec_enforcement_score", 100)


@register_inference_function("do_regulatory_action_basefunction")
def do_regulatory_action_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("regulatory_action", None, None, entity_id, context, "regulatory_action_score", 100)


@register_inference_function("pending_litigation_basefunction")
def pending_litigation_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("pending_litigation", None, None, entity_id, context, "pending_litigation_score", 100)


@register_inference_function("whistleblower_basefunction")
def whistleblower_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("whistleblower", None, None, entity_id, context, "whistleblower_score", 100)


# =============================================================================
# EXECUTIVE FUNCTIONS
# =============================================================================

@register_inference_function("executive_stability_basefunction")
def executive_stability_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("executive_stability", None, None, entity_id, context, "executive_stability_score", 50)


@register_inference_function("cfo_quality_basefunction")
def cfo_quality_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("cfo_quality", None, None, entity_id, context, "cfo_quality_score", 50)


@register_inference_function("insider_trading_basefunction")
def insider_trading_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("insider_trading", None, None, entity_id, context, "insider_trading_score", 70)


@register_inference_function("executive_background_basefunction")
def executive_background_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("executive_background", None, None, entity_id, context, "executive_background_score", 100)


@register_inference_function("trading_plan_basefunction")
def trading_plan_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("trading_plan", None, None, entity_id, context, "trading_plan_score", 50)


# =============================================================================
# CORPORATE FOOTPRINT FUNCTIONS
# =============================================================================

@register_inference_function("investor_relations_basefunction")
def investor_relations_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("investor_relations", None, None, entity_id, context, "investor_relations_score", 40)


@register_inference_function("governance_page_basefunction")
def governance_page_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("governance_page", None, None, entity_id, context, "governance_page_score", 30)


@register_inference_function("do_esg_reporting_basefunction")
def do_esg_reporting_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("esg_reporting", None, None, entity_id, context, "esg_reporting_score", 30)


@register_inference_function("press_release_basefunction")
def press_release_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("press_release", None, None, entity_id, context, "press_release_score", 50)


@register_inference_function("leadership_visability_basefunction")
def leadership_visibility_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("leadership_visibility", None, None, entity_id, context, "leadership_visibility_score", 50)


@register_inference_function("hiring_signals_basefunction")
def hiring_signals_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("hiring_signals", None, None, entity_id, context, "hiring_signals_score", 40)


# =============================================================================
# STRUCTURED DATA FUNCTIONS
# =============================================================================

@register_inference_function("do_credit_rating_basefunction")
def do_credit_rating_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("credit_rating", None, None, entity_id, context, "average_rating_score", 50)


@register_inference_function("esg_rating_basefunction")
def esg_rating_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("esg_rating", None, None, entity_id, context, "esg_rating_score", 50)


@register_inference_function("governance_rating_basefunction")
def governance_rating_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("governance_rating", None, None, entity_id, context, "governance_rating_score", 50)


@register_inference_function("iss_governance_basefunction")
def iss_governance_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    return _run_pipeline("iss_governance", None, None, entity_id, context, "iss_governance_score", 50)
