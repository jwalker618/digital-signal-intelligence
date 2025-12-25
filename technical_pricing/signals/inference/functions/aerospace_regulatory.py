"""
Aerospace Inference Functions - Regulatory Compliance Signal Group

Signal features:
- certificate_status: Operating certificate status (AOC/Part 121/135)
- enforcement_actions: Regulatory fines, penalties (5-year lookback)
- iosa_audit_status: IOSA registration and audit findings
- ramp_inspection: SAFA/SACA ramp inspection findings rate
- eu_safety_list: Presence on EU banned carrier list
- state_safety_rating: ICAO USOAP audit results for state
"""

import time
from typing import Dict, Any, Optional

from ...types import SignalResult, InferenceContext
from ...inference.registry import register_inference_function
from ...extractors.stubs.aerospace import (
    OperatingCertificateExtractor,
    IOSARegistryExtractor,
    RampInspectionExtractor,
    EUSafetyListExtractor,
    StateSafetyExtractor,
)
from ...extractors.stubs.common import RegulatoryEnforcementExtractor
from ...aggregators.implementations.aerospace import (
    CertificateStatusAggregator,
    IOSAAuditAggregator,
    RampInspectionAggregator,
    EUSafetyListAggregator,
    StateSafetyAggregator,
)
from ...aggregators.implementations.common import RegulatoryEnforcementAggregator


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


@register_inference_function("certifcate_status_basefunction")  # Note: typo matches YAML
def certificate_status_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """
    Inference function for certificate_status signal.
    
    Assesses operating certificate status and compliance.
    Score: 0-100 (100 = active with clean record, 0 = revoked)
    """
    start_time = time.time()
    
    try:
        extractor = OperatingCertificateExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(
                signal_id="certificate_status",
                score=50,
                confidence=0.3,
                error="Extraction failed"
            )
        
        aggregator = CertificateStatusAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        if not agg_result.success:
            return SignalResult(
                signal_id="certificate_status",
                score=50,
                confidence=0.5,
                error="Aggregation failed"
            )
        
        score = agg_result.data.get("certificate_score", 50)
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result(
            signal_id="certificate_status",
            score=round(score, 1),
            confidence=1.0,
            execution_time=execution_time,
            extract_result=extract_result,
            agg_result=agg_result,
            extractor_name="OperatingCertificateExtractor",
            aggregator_name="CertificateStatusAggregator",
        )
        
    except Exception as e:
        return SignalResult(
            signal_id="certificate_status",
            score=50,
            confidence=0.0,
            error=str(e)
        )


@register_inference_function("enforcement_action_basefunction")
def enforcement_action_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """
    Inference function for enforcement_actions signal.
    
    Assesses regulatory enforcement history.
    Score: 0-100 (100 = clean record, 0 = severe enforcement)
    """
    start_time = time.time()
    
    try:
        # Use common extractor with aviation regulator type
        extractor = RegulatoryEnforcementExtractor()
        extract_result = extractor.extract(entity_id, regulator_type="AVIATION", context=context)
        
        if not extract_result.success:
            return SignalResult(
                signal_id="enforcement_actions",
                score=70,  # Assume clean if no data
                confidence=0.3,
                error="Extraction failed"
            )
        
        aggregator = RegulatoryEnforcementAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        if not agg_result.success:
            return SignalResult(
                signal_id="enforcement_actions",
                score=70,
                confidence=0.5,
                error="Aggregation failed"
            )
        
        score = agg_result.data.get("enforcement_score", 70)
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result(
            signal_id="enforcement_actions",
            score=round(score, 1),
            confidence=1.0,
            execution_time=execution_time,
            extract_result=extract_result,
            agg_result=agg_result,
            extractor_name="RegulatoryEnforcementExtractor",
            aggregator_name="RegulatoryEnforcementAggregator",
        )
        
    except Exception as e:
        return SignalResult(
            signal_id="enforcement_actions",
            score=70,
            confidence=0.0,
            error=str(e)
        )


@register_inference_function("iosa_audit_basefunction")
def iosa_audit_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """
    Inference function for iosa_audit_status signal.
    
    Assesses IOSA registration and audit findings.
    Score: 0-100 (100 = long-standing registered with clean audits)
    """
    start_time = time.time()
    
    try:
        extractor = IOSARegistryExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(
                signal_id="iosa_audit_status",
                score=40,
                confidence=0.3,
                error="Extraction failed"
            )
        
        aggregator = IOSAAuditAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        if not agg_result.success:
            return SignalResult(
                signal_id="iosa_audit_status",
                score=40,
                confidence=0.5,
                error="Aggregation failed"
            )
        
        score = agg_result.data.get("iosa_score", 40)
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result(
            signal_id="iosa_audit_status",
            score=round(score, 1),
            confidence=1.0,
            execution_time=execution_time,
            extract_result=extract_result,
            agg_result=agg_result,
            extractor_name="IOSARegistryExtractor",
            aggregator_name="IOSAAuditAggregator",
        )
        
    except Exception as e:
        return SignalResult(
            signal_id="iosa_audit_status",
            score=40,
            confidence=0.0,
            error=str(e)
        )


@register_inference_function("ramp_inspection_basefunction")
def ramp_inspection_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """
    Inference function for ramp_inspection signal.
    
    Assesses SAFA/SACA ramp inspection results.
    Score: 0-100 (100 = below industry average findings rate)
    """
    start_time = time.time()
    
    try:
        extractor = RampInspectionExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(
                signal_id="ramp_inspection",
                score=60,
                confidence=0.3,
                error="Extraction failed"
            )
        
        aggregator = RampInspectionAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        if not agg_result.success:
            return SignalResult(
                signal_id="ramp_inspection",
                score=60,
                confidence=0.5,
                error="Aggregation failed"
            )
        
        score = agg_result.data.get("ramp_inspection_score", 60)
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result(
            signal_id="ramp_inspection",
            score=round(score, 1),
            confidence=1.0,
            execution_time=execution_time,
            extract_result=extract_result,
            agg_result=agg_result,
            extractor_name="RampInspectionExtractor",
            aggregator_name="RampInspectionAggregator",
        )
        
    except Exception as e:
        return SignalResult(
            signal_id="ramp_inspection",
            score=60,
            confidence=0.0,
            error=str(e)
        )


@register_inference_function("eu_safetylist_basefunction")
def eu_safetylist_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """
    Inference function for eu_safety_list signal.
    
    Checks presence on EU banned carrier list.
    Score: 0-100 (100 = not on list, 0 = banned)
    """
    start_time = time.time()
    
    try:
        extractor = EUSafetyListExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(
                signal_id="eu_safety_list",
                score=100,  # Assume not on list if can't check
                confidence=0.3,
                error="Extraction failed"
            )
        
        aggregator = EUSafetyListAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        if not agg_result.success:
            return SignalResult(
                signal_id="eu_safety_list",
                score=100,
                confidence=0.5,
                error="Aggregation failed"
            )
        
        score = agg_result.data.get("eu_safety_score", 100)
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result(
            signal_id="eu_safety_list",
            score=round(score, 1),
            confidence=1.0,
            execution_time=execution_time,
            extract_result=extract_result,
            agg_result=agg_result,
            extractor_name="EUSafetyListExtractor",
            aggregator_name="EUSafetyListAggregator",
        )
        
    except Exception as e:
        return SignalResult(
            signal_id="eu_safety_list",
            score=100,
            confidence=0.0,
            error=str(e)
        )


@register_inference_function("state_safety_basefunction")
def state_safety_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """
    Inference function for state_safety_rating signal.
    
    Assesses ICAO USOAP scores for state of registry.
    Score: 0-100 (100 = high effective implementation)
    """
    start_time = time.time()
    
    try:
        extractor = StateSafetyExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(
                signal_id="state_safety_rating",
                score=65,  # Global average
                confidence=0.3,
                error="Extraction failed"
            )
        
        aggregator = StateSafetyAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        if not agg_result.success:
            return SignalResult(
                signal_id="state_safety_rating",
                score=65,
                confidence=0.5,
                error="Aggregation failed"
            )
        
        score = agg_result.data.get("state_safety_score", 65)
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result(
            signal_id="state_safety_rating",
            score=round(score, 1),
            confidence=1.0,
            execution_time=execution_time,
            extract_result=extract_result,
            agg_result=agg_result,
            extractor_name="StateSafetyExtractor",
            aggregator_name="StateSafetyAggregator",
        )
        
    except Exception as e:
        return SignalResult(
            signal_id="state_safety_rating",
            score=65,
            confidence=0.0,
            error=str(e)
        )
