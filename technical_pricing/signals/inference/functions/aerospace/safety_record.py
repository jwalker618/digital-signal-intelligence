"""
Aerospace Inference Functions - Safety Record Signal Group

Signal features:
- accident_history: Hull loss and major accidents (10-year lookback)
- incident_history: Serious incidents, runway excursions, near-misses
- accident_rate: Accidents per million departures vs industry average
- fatality_history: Fatal accident history (10-year lookback)
- investigation_findings: Operator cited as causal factor in investigations
"""

import time
from typing import Dict, Any, Optional

from ...types import SignalResult, InferenceContext
from ...inference.registry import register_inference_function
from ...extractors.stubs.aerospace import AviationSafetyDatabaseExtractor
from ...aggregators.implementations.aerospace import AviationSafetyAggregator


def _create_safety_result(
    signal_id: str,
    score: float,
    confidence: float,
    execution_time: float,
    extract_result,
    agg_result,
) -> SignalResult:
    """Helper to create consistent SignalResult for safety signals."""
    return SignalResult(
        signal_id=signal_id,
        score=score,
        confidence=confidence,
        execution_time_ms=execution_time,
        raw_data=extract_result.data if extract_result else None,
        aggregated_data=agg_result.data if agg_result else None,
        metadata={
            "extractor": "AviationSafetyDatabaseExtractor",
            "aggregator": "AviationSafetyAggregator",
            "from_cache": extract_result.from_cache if extract_result else False,
        }
    )


def _get_safety_data(entity_id: str, context: InferenceContext):
    """
    Shared extraction and aggregation for all safety signals.
    All safety signals use the same extractor/aggregator.
    """
    extractor = AviationSafetyDatabaseExtractor()
    extract_result = extractor.extract(entity_id, context=context)
    
    if not extract_result.success:
        return None, None, "Extraction failed"
    
    aggregator = AviationSafetyAggregator()
    agg_result = aggregator.aggregate([extract_result])
    
    if not agg_result.success:
        return extract_result, None, "Aggregation failed"
    
    return extract_result, agg_result, None


@register_inference_function("accident_history_basefunction")
def accident_history_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """
    Inference function for accident_history signal.
    
    Assesses hull loss and major accident history over 10-year lookback.
    Score: 0-100 (100 = no accidents, 0 = multiple hull losses)
    """
    start_time = time.time()
    
    try:
        extract_result, agg_result, error = _get_safety_data(entity_id, context)
        
        if error:
            return SignalResult(
                signal_id="accident_history",
                score=50,
                confidence=0.3 if extract_result else 0.0,
                error=error
            )
        
        score = agg_result.data.get("accident_history_score", 50)
        execution_time = (time.time() - start_time) * 1000
        
        return _create_safety_result(
            signal_id="accident_history",
            score=round(score, 1),
            confidence=1.0,
            execution_time=execution_time,
            extract_result=extract_result,
            agg_result=agg_result,
        )
        
    except Exception as e:
        return SignalResult(
            signal_id="accident_history",
            score=50,
            confidence=0.0,
            error=str(e)
        )


@register_inference_function("incident_history_basefunction")
def incident_history_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """
    Inference function for incident_history signal.
    
    Assesses serious incidents, runway excursions, near-misses.
    Score: 0-100 (100 = no serious incidents)
    """
    start_time = time.time()
    
    try:
        extract_result, agg_result, error = _get_safety_data(entity_id, context)
        
        if error:
            return SignalResult(
                signal_id="incident_history",
                score=50,
                confidence=0.3 if extract_result else 0.0,
                error=error
            )
        
        score = agg_result.data.get("incident_history_score", 50)
        execution_time = (time.time() - start_time) * 1000
        
        return _create_safety_result(
            signal_id="incident_history",
            score=round(score, 1),
            confidence=1.0,
            execution_time=execution_time,
            extract_result=extract_result,
            agg_result=agg_result,
        )
        
    except Exception as e:
        return SignalResult(
            signal_id="incident_history",
            score=50,
            confidence=0.0,
            error=str(e)
        )


@register_inference_function("accident_rate_basefunction")
def accident_rate_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """
    Inference function for accident_rate signal.
    
    Compares accident rate per million departures to industry average.
    Score: 0-100 (100 = well below industry average)
    """
    start_time = time.time()
    
    try:
        extract_result, agg_result, error = _get_safety_data(entity_id, context)
        
        if error:
            return SignalResult(
                signal_id="accident_rate",
                score=50,
                confidence=0.3 if extract_result else 0.0,
                error=error
            )
        
        score = agg_result.data.get("accident_rate_score", 50)
        execution_time = (time.time() - start_time) * 1000
        
        return _create_safety_result(
            signal_id="accident_rate",
            score=round(score, 1),
            confidence=1.0,
            execution_time=execution_time,
            extract_result=extract_result,
            agg_result=agg_result,
        )
        
    except Exception as e:
        return SignalResult(
            signal_id="accident_rate",
            score=50,
            confidence=0.0,
            error=str(e)
        )


@register_inference_function("fatality_history_basefunction")
def fatality_history_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """
    Inference function for fatality_history signal.
    
    Assesses fatal accident history over 10-year lookback.
    Score: 0-100 (100 = no fatal accidents)
    """
    start_time = time.time()
    
    try:
        extract_result, agg_result, error = _get_safety_data(entity_id, context)
        
        if error:
            return SignalResult(
                signal_id="fatality_history",
                score=50,
                confidence=0.3 if extract_result else 0.0,
                error=error
            )
        
        score = agg_result.data.get("fatality_history_score", 50)
        execution_time = (time.time() - start_time) * 1000
        
        return _create_safety_result(
            signal_id="fatality_history",
            score=round(score, 1),
            confidence=1.0,
            execution_time=execution_time,
            extract_result=extract_result,
            agg_result=agg_result,
        )
        
    except Exception as e:
        return SignalResult(
            signal_id="fatality_history",
            score=50,
            confidence=0.0,
            error=str(e)
        )


@register_inference_function("investigation_finding_basefunction")
def investigation_finding_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """
    Inference function for investigation_findings signal.
    
    Assesses whether operator was cited as causal factor in investigations.
    Score: 0-100 (100 = never cited as cause)
    """
    start_time = time.time()
    
    try:
        extract_result, agg_result, error = _get_safety_data(entity_id, context)
        
        if error:
            return SignalResult(
                signal_id="investigation_findings",
                score=50,
                confidence=0.3 if extract_result else 0.0,
                error=error
            )
        
        score = agg_result.data.get("investigation_findings_score", 50)
        execution_time = (time.time() - start_time) * 1000
        
        return _create_safety_result(
            signal_id="investigation_findings",
            score=round(score, 1),
            confidence=1.0,
            execution_time=execution_time,
            extract_result=extract_result,
            agg_result=agg_result,
        )
        
    except Exception as e:
        return SignalResult(
            signal_id="investigation_findings",
            score=50,
            confidence=0.0,
            error=str(e)
        )
