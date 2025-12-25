"""
Cyber Inference Functions - Categorical Groups

These inference functions determine categorical classifications for cyber risk.
Each function orchestrates: Extractor → Aggregator → Category Result

Categorical Groups:
- industry_classification: Industry type (TECHNOLOGY, HEALTHCARE, etc.)
- size_band: Company size (MICRO, SMALL, MEDIUM, LARGE, ENTERPRISE)
- geography: Primary operational geography (US, UK, EU, APAC, OTHER)
"""

import time
from typing import Dict, Any, Optional

from ...types import SignalResult, InferenceContext
from ...inference.registry import register_inference_function
from ...extractors.stubs.cyber import (
    IndustryClassificationExtractor,
    CompanySizeExtractor,
    OperationalBaseExtractor,
)
from ...aggregators.implementations.cyber import (
    IndustryClassificationAggregator,
    CompanySizeAggregator,
    GeographyAggregator,
)


@register_inference_function("industry_classification_basefunction")
def industry_classification_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """
    Inference function for industry_classification categorical group.
    
    Categories: TECHNOLOGY, FINANCIAL_SERVICES, HEALTHCARE, RETAIL,
                MANUFACTURING, PROFESSIONAL_SERVICES, EDUCATION,
                GOVERNMENT, ENERGY, OTHER
    """
    start_time = time.time()
    
    try:
        # Extract
        extractor = IndustryClassificationExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(
                signal_id="industry_classification",
                category="OTHER",
                confidence=0.3,
                error="Extraction failed"
            )
        
        # Aggregate
        aggregator = IndustryClassificationAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        if not agg_result.success:
            return SignalResult(
                signal_id="industry_classification",
                category="OTHER",
                confidence=0.5,
                error="Aggregation failed"
            )
        
        category = agg_result.data.get("primary_industry", "OTHER")
        execution_time = (time.time() - start_time) * 1000
        
        return SignalResult(
            signal_id="industry_classification",
            category=category,
            confidence=0.85,
            execution_time_ms=execution_time,
            raw_data=extract_result.data,
            aggregated_data=agg_result.data,
            metadata={
                "extractor": "IndustryClassificationExtractor",
                "aggregator": "IndustryClassificationAggregator",
                "from_cache": extract_result.from_cache,
            }
        )
        
    except Exception as e:
        return SignalResult(
            signal_id="industry_classification",
            category="OTHER",
            confidence=0.0,
            error=str(e)
        )


@register_inference_function("company_size_basefunction")
def company_size_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """
    Inference function for size_band categorical group.
    
    Categories: MICRO, SMALL, MEDIUM, LARGE, ENTERPRISE
    """
    start_time = time.time()
    
    try:
        # Extract
        extractor = CompanySizeExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(
                signal_id="size_band",
                category="MEDIUM",
                confidence=0.3,
                error="Extraction failed"
            )
        
        # Aggregate
        aggregator = CompanySizeAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        if not agg_result.success:
            return SignalResult(
                signal_id="size_band",
                category="MEDIUM",
                confidence=0.5,
                error="Aggregation failed"
            )
        
        category = agg_result.data.get("size_band", "MEDIUM")
        execution_time = (time.time() - start_time) * 1000
        
        return SignalResult(
            signal_id="size_band",
            category=category,
            confidence=0.80,
            execution_time_ms=execution_time,
            raw_data=extract_result.data,
            aggregated_data=agg_result.data,
            metadata={
                "extractor": "CompanySizeExtractor",
                "aggregator": "CompanySizeAggregator",
                "from_cache": extract_result.from_cache,
            }
        )
        
    except Exception as e:
        return SignalResult(
            signal_id="size_band",
            category="MEDIUM",
            confidence=0.0,
            error=str(e)
        )


@register_inference_function("operational_base_basefunction")
def operational_base_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """
    Inference function for geography categorical group.
    
    Categories: US, UK, EU, APAC, OTHER
    """
    start_time = time.time()
    
    try:
        # Extract
        extractor = OperationalBaseExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(
                signal_id="geography",
                category="US",
                confidence=0.3,
                error="Extraction failed"
            )
        
        # Aggregate
        aggregator = GeographyAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        if not agg_result.success:
            return SignalResult(
                signal_id="geography",
                category="US",
                confidence=0.5,
                error="Aggregation failed"
            )
        
        category = agg_result.data.get("primary_geography", "US")
        execution_time = (time.time() - start_time) * 1000
        
        return SignalResult(
            signal_id="geography",
            category=category,
            confidence=0.85,
            execution_time_ms=execution_time,
            raw_data=extract_result.data,
            aggregated_data=agg_result.data,
            metadata={
                "extractor": "OperationalBaseExtractor",
                "aggregator": "GeographyAggregator",
                "from_cache": extract_result.from_cache,
            }
        )
        
    except Exception as e:
        return SignalResult(
            signal_id="geography",
            category="US",
            confidence=0.0,
            error=str(e)
        )
