"""
Cyber Inference Functions - Structured Data Signal Group

Signal features:
- security_rating: Third-party security rating (BitSight, SecurityScorecard)
- esg_cyber: ESG cyber component
- credit_rating: Credit rating as organizational quality proxy (uses common)
"""

import time
from typing import Dict, Any, Optional

from ...types import SignalResult, InferenceContext
from ...inference.registry import register_inference_function
from ...extractors.stubs.cyber import (
    SecurityRatingExtractor,
    ESGCyberExtractor,
)
from ...extractors.stubs.common import CreditRatingExtractor
from ...aggregators.implementations.cyber import (
    SecurityRatingAggregator,
    ESGCyberAggregator,
)
from ...aggregators.implementations.common import CreditRatingAggregator


def _create_signal_result(
    signal_id: str,
    score: float,
    confidence: float,
    execution_time: float,
    extract_result,
    agg_result,
    extractor_name: str,
    aggregator_name: str,
) -> SignalResult:
    """Helper to create consistent SignalResult objects."""
    return SignalResult(
        signal_id=signal_id,
        score=score,
        confidence=confidence,
        execution_time_ms=execution_time,
        raw_data=extract_result.data if extract_result else None,
        aggregated_data=agg_result.data if agg_result else None,
        metadata={
            "extractor": extractor_name,
            "aggregator": aggregator_name,
            "from_cache": extract_result.from_cache if extract_result else False,
        }
    )


@register_inference_function("security_rating_basefunction")
def security_rating_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for security_rating signal."""
    start_time = time.time()
    
    try:
        extractor = SecurityRatingExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="security_rating", score=50, confidence=0.3, error="Extraction failed")
        
        aggregator = SecurityRatingAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("security_rating_score", 50) if agg_result.success else 50
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("security_rating", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "SecurityRatingExtractor", "SecurityRatingAggregator")
    except Exception as e:
        return SignalResult(signal_id="security_rating", score=50, confidence=0.0, error=str(e))


@register_inference_function("esg_cyber_basefunction")
def esg_cyber_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for esg_cyber signal."""
    start_time = time.time()
    
    try:
        extractor = ESGCyberExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="esg_cyber", score=50, confidence=0.3, error="Extraction failed")
        
        aggregator = ESGCyberAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("esg_cyber_score", 50) if agg_result.success else 50
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("esg_cyber", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "ESGCyberExtractor", "ESGCyberAggregator")
    except Exception as e:
        return SignalResult(signal_id="esg_cyber", score=50, confidence=0.0, error=str(e))


@register_inference_function("credit_rating_basefunction")
def credit_rating_cyber_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """
    Inference function for credit_rating signal (uses common extractor).
    
    Note: This reuses the common credit rating infrastructure but is registered
    under the cyber-specific function name from config.
    """
    start_time = time.time()
    
    try:
        extractor = CreditRatingExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="credit_rating", score=50, confidence=0.3, error="Extraction failed")
        
        aggregator = CreditRatingAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        # Use average rating score if available
        if agg_result.success and agg_result.data.get("has_rating"):
            score = agg_result.data.get("average_rating_score", 50)
        else:
            score = 50  # Neutral for no rating
        
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("credit_rating", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "CreditRatingExtractor", "CreditRatingAggregator")
    except Exception as e:
        return SignalResult(signal_id="credit_rating", score=50, confidence=0.0, error=str(e))
