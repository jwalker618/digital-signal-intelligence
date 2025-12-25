"""
Cyber Inference Functions - Network Authority Signal Group

Signal features:
- customer_quality: Customer quality from case studies, logos
- partner_quality: Technology partner network quality
- security_vendor: Tier-1 security vendor relationships
- industry_body: Industry body membership (uses common extractor)
- certification_authority: Quality of audit/certification firms
- financial_relationship: Banking/financial relationships
- network_centrality: Position in industry relationship graph
- second_degree: Quality of partners' partners
"""

import time
from typing import Dict, Any, Optional

from ...types import SignalResult, InferenceContext
from ...inference.registry import register_inference_function
from ...extractors.stubs.cyber import (
    CustomerQualityExtractor,
    PartnerNetworkExtractor,
    SecurityVendorExtractor,
    CertificationAuthorityExtractor,
    FinancialRelationshipExtractor,
    NetworkCentralityExtractor,
    SecondDegreeExtractor,
)
from ...extractors.stubs.common import IndustryAssociationExtractor
from ...aggregators.implementations.cyber import (
    CustomerQualityAggregator,
    PartnerQualityAggregator,
    SecurityVendorAggregator,
    CertificationAuthorityAggregator,
    FinancialRelationshipAggregator,
    NetworkCentralityAggregator,
    SecondDegreeAggregator,
)
from ...aggregators.implementations.common import IndustryEngagementAggregator


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


@register_inference_function("customer_quality_basefunction")
def customer_quality_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for customer_quality signal."""
    start_time = time.time()
    
    try:
        extractor = CustomerQualityExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="customer_quality", score=50, confidence=0.3, error="Extraction failed")
        
        aggregator = CustomerQualityAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("customer_quality_score", 50) if agg_result.success else 50
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("customer_quality", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "CustomerQualityExtractor", "CustomerQualityAggregator")
    except Exception as e:
        return SignalResult(signal_id="customer_quality", score=50, confidence=0.0, error=str(e))


@register_inference_function("partner_quality_basefunction")
def partner_quality_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for partner_quality signal."""
    start_time = time.time()
    
    try:
        extractor = PartnerNetworkExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="partner_quality", score=50, confidence=0.3, error="Extraction failed")
        
        aggregator = PartnerQualityAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("partner_quality_score", 50) if agg_result.success else 50
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("partner_quality", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "PartnerNetworkExtractor", "PartnerQualityAggregator")
    except Exception as e:
        return SignalResult(signal_id="partner_quality", score=50, confidence=0.0, error=str(e))


@register_inference_function("security_vendor_basefunction")
def security_vendor_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for security_vendor signal."""
    start_time = time.time()
    
    try:
        extractor = SecurityVendorExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="security_vendor", score=40, confidence=0.3, error="Extraction failed")
        
        aggregator = SecurityVendorAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("security_vendor_score", 40) if agg_result.success else 40
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("security_vendor", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "SecurityVendorExtractor", "SecurityVendorAggregator")
    except Exception as e:
        return SignalResult(signal_id="security_vendor", score=40, confidence=0.0, error=str(e))


@register_inference_function("industry_body_basefunction")
def industry_body_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for industry_body signal (uses common extractor)."""
    start_time = time.time()
    
    try:
        extractor = IndustryAssociationExtractor()
        extract_result = extractor.extract(entity_id, industry="TECHNOLOGY", context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="industry_body", score=40, confidence=0.3, error="Extraction failed")
        
        aggregator = IndustryEngagementAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("engagement_score", 40) if agg_result.success else 40
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("industry_body", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "IndustryAssociationExtractor", "IndustryEngagementAggregator")
    except Exception as e:
        return SignalResult(signal_id="industry_body", score=40, confidence=0.0, error=str(e))


@register_inference_function("certification_authority_basefunction")
def certification_authority_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for certification_authority signal."""
    start_time = time.time()
    
    try:
        extractor = CertificationAuthorityExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="certification_authority", score=50, confidence=0.3, error="Extraction failed")
        
        aggregator = CertificationAuthorityAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("certification_authority_score", 50) if agg_result.success else 50
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("certification_authority", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "CertificationAuthorityExtractor", "CertificationAuthorityAggregator")
    except Exception as e:
        return SignalResult(signal_id="certification_authority", score=50, confidence=0.0, error=str(e))


@register_inference_function("financial_relationship_basefunction")
def financial_relationship_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for financial_relationship signal."""
    start_time = time.time()
    
    try:
        extractor = FinancialRelationshipExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="financial_relationship", score=50, confidence=0.3, error="Extraction failed")
        
        aggregator = FinancialRelationshipAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("financial_relationship_score", 50) if agg_result.success else 50
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("financial_relationship", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "FinancialRelationshipExtractor", "FinancialRelationshipAggregator")
    except Exception as e:
        return SignalResult(signal_id="financial_relationship", score=50, confidence=0.0, error=str(e))


@register_inference_function("network_centrality_basefunction")
def network_centrality_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for network_centrality signal."""
    start_time = time.time()
    
    try:
        extractor = NetworkCentralityExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="network_centrality", score=50, confidence=0.3, error="Extraction failed")
        
        aggregator = NetworkCentralityAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("network_centrality_score", 50) if agg_result.success else 50
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("network_centrality", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "NetworkCentralityExtractor", "NetworkCentralityAggregator")
    except Exception as e:
        return SignalResult(signal_id="network_centrality", score=50, confidence=0.0, error=str(e))


@register_inference_function("second_degree_basefunction")
def second_degree_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for second_degree signal."""
    start_time = time.time()
    
    try:
        extractor = SecondDegreeExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="second_degree", score=50, confidence=0.3, error="Extraction failed")
        
        aggregator = SecondDegreeAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("second_degree_score", 50) if agg_result.success else 50
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("second_degree", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "SecondDegreeExtractor", "SecondDegreeAggregator")
    except Exception as e:
        return SignalResult(signal_id="second_degree", score=50, confidence=0.0, error=str(e))
