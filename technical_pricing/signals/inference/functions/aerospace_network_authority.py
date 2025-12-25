"""
Aerospace Inference Functions - Network Authority Signal Group

Signal features:
- alliance_membership: Airline alliance participation
- codeshare_quality: Quality of codeshare partners  
- lessor_quality: Quality of aircraft lessors
- oem_relationship: OEM relationships
- mro_quality: Quality of MRO providers
"""

import time
from typing import Dict, Any, Optional

from ...types import SignalResult, InferenceContext
from ...inference.registry import register_inference_function
from ...extractors.stubs.aerospace import (
    AirlineAllianceExtractor,
    CodesharePartnershipExtractor,
    AircraftLessorExtractor,
    OEMRelationshipExtractor,
    MROProviderExtractor,
)
from ...aggregators.implementations.aerospace import (
    AllianceMembershipAggregator,
    CodeshareQualityAggregator,
    LessorQualityAggregator,
    OEMRelationshipAggregator,
    MROQualityAggregator,
)


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


@register_inference_function("alliance_membership_basefunction")
def alliance_membership_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """
    Inference function for alliance_membership signal.
    
    Scores alliance membership quality:
    - Global alliance membership (Star, oneworld, SkyTeam)
    - Membership tier (founding, full, affiliate)
    - Years of membership
    
    Score: 0-100 (100 = founding member of major alliance)
    """
    start_time = time.time()
    
    try:
        # 1. Extract
        extractor = AirlineAllianceExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(
                signal_id="alliance_membership",
                score=30,  # No alliance data defaults to low-mid score
                confidence=0.3,
                error="Extraction failed"
            )
        
        # 2. Aggregate
        aggregator = AllianceMembershipAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        if not agg_result.success:
            return SignalResult(
                signal_id="alliance_membership",
                score=30,
                confidence=0.5,
                error="Aggregation failed"
            )
        
        # 3. Calculate score
        # Score components:
        # - Has alliance: base 50 points
        # - Membership tier: 0-40 points based on tier score
        # - Founding member bonus: 10 points
        # - Years bonus: up to 10 points
        
        data = agg_result.data
        if not data.get("has_alliance"):
            score = 20  # No alliance = low score but not zero
        else:
            score = 50  # Base for having alliance
            tier_score = data.get("membership_tier_score", 50)
            score += (tier_score / 100) * 30  # Up to 30 from tier
            
            if data.get("is_founding_member"):
                score += 10
            
            years = data.get("membership_years", 0)
            score += min(years, 10)  # Up to 10 points for longevity
        
        score = max(0, min(100, score))
        
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result(
            signal_id="alliance_membership",
            score=round(score, 1),
            confidence=1.0,
            execution_time=execution_time,
            extract_result=extract_result,
            agg_result=agg_result,
            extractor_name="AirlineAllianceExtractor",
            aggregator_name="AllianceMembershipAggregator",
        )
        
    except Exception as e:
        return SignalResult(
            signal_id="alliance_membership",
            score=30,
            confidence=0.0,
            error=str(e)
        )


@register_inference_function("codeshare_partner_basefunction")
def codeshare_partner_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """
    Inference function for codeshare_quality signal.
    
    Scores codeshare partner network quality.
    Score: 0-100
    """
    start_time = time.time()
    
    try:
        # 1. Extract
        extractor = CodesharePartnershipExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(
                signal_id="codeshare_quality",
                score=50,
                confidence=0.3,
                error="Extraction failed"
            )
        
        # 2. Aggregate
        aggregator = CodeshareQualityAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        if not agg_result.success:
            return SignalResult(
                signal_id="codeshare_quality",
                score=50,
                confidence=0.5,
                error="Aggregation failed"
            )
        
        # 3. Score is directly from aggregator
        score = agg_result.data.get("network_quality_score", 50)
        
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result(
            signal_id="codeshare_quality",
            score=round(score, 1),
            confidence=1.0,
            execution_time=execution_time,
            extract_result=extract_result,
            agg_result=agg_result,
            extractor_name="CodesharePartnershipExtractor",
            aggregator_name="CodeshareQualityAggregator",
        )
        
    except Exception as e:
        return SignalResult(
            signal_id="codeshare_quality",
            score=50,
            confidence=0.0,
            error=str(e)
        )


@register_inference_function("aircraft_lessor_basefunction")
def aircraft_lessor_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """
    Inference function for lessor_quality signal.
    
    Scores aircraft lessor relationship quality.
    Score: 0-100
    """
    start_time = time.time()
    
    try:
        extractor = AircraftLessorExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(
                signal_id="lessor_quality",
                score=50,
                confidence=0.3,
                error="Extraction failed"
            )
        
        aggregator = LessorQualityAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        if not agg_result.success:
            return SignalResult(
                signal_id="lessor_quality",
                score=50,
                confidence=0.5,
                error="Aggregation failed"
            )
        
        score = agg_result.data.get("lessor_quality_score", 50)
        
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result(
            signal_id="lessor_quality",
            score=round(score, 1),
            confidence=1.0,
            execution_time=execution_time,
            extract_result=extract_result,
            agg_result=agg_result,
            extractor_name="AircraftLessorExtractor",
            aggregator_name="LessorQualityAggregator",
        )
        
    except Exception as e:
        return SignalResult(
            signal_id="lessor_quality",
            score=50,
            confidence=0.0,
            error=str(e)
        )


@register_inference_function("oem_relationship_basefunction")
def oem_relationship_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """
    Inference function for oem_relationship signal.
    
    Scores OEM relationships (Boeing, Airbus, etc.).
    Score: 0-100
    """
    start_time = time.time()
    
    try:
        extractor = OEMRelationshipExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(
                signal_id="oem_relationship",
                score=50,
                confidence=0.3,
                error="Extraction failed"
            )
        
        aggregator = OEMRelationshipAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        if not agg_result.success:
            return SignalResult(
                signal_id="oem_relationship",
                score=50,
                confidence=0.5,
                error="Aggregation failed"
            )
        
        score = agg_result.data.get("oem_relationship_score", 50)
        
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result(
            signal_id="oem_relationship",
            score=round(score, 1),
            confidence=1.0,
            execution_time=execution_time,
            extract_result=extract_result,
            agg_result=agg_result,
            extractor_name="OEMRelationshipExtractor",
            aggregator_name="OEMRelationshipAggregator",
        )
        
    except Exception as e:
        return SignalResult(
            signal_id="oem_relationship",
            score=50,
            confidence=0.0,
            error=str(e)
        )


@register_inference_function("mro_quality_basefunction")
def mro_quality_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """
    Inference function for mro_quality signal.
    
    Scores MRO provider quality.
    Score: 0-100
    """
    start_time = time.time()
    
    try:
        extractor = MROProviderExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(
                signal_id="mro_quality",
                score=50,
                confidence=0.3,
                error="Extraction failed"
            )
        
        aggregator = MROQualityAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        if not agg_result.success:
            return SignalResult(
                signal_id="mro_quality",
                score=50,
                confidence=0.5,
                error="Aggregation failed"
            )
        
        score = agg_result.data.get("mro_quality_score", 50)
        
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result(
            signal_id="mro_quality",
            score=round(score, 1),
            confidence=1.0,
            execution_time=execution_time,
            extract_result=extract_result,
            agg_result=agg_result,
            extractor_name="MROProviderExtractor",
            aggregator_name="MROQualityAggregator",
        )
        
    except Exception as e:
        return SignalResult(
            signal_id="mro_quality",
            score=50,
            confidence=0.0,
            error=str(e)
        )
