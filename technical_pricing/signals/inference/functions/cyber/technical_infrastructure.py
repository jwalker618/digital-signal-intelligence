"""
Cyber Inference Functions - Technical Infrastructure Signal Group

Signal features:
- tls_score: TLS/SSL configuration quality
- security_headers: HTTP security headers
- email_auth: Email authentication (SPF/DMARC/DKIM)
- dnssec: DNSSEC implementation
- exposure: Network exposure (open ports, services)
- software_currency: Software version freshness
- cve_exposure: Known vulnerability exposure
- cloud_infrastructure: Cloud provider and configuration
- waf_presence: Web Application Firewall detection
- cdn_usage: CDN usage (DDoS protection indicator)
"""

import time
from typing import Dict, Any, Optional

from ...types import SignalResult, InferenceContext
from ...inference.registry import register_inference_function
from ...extractors.stubs.cyber import (
    TLSConfigExtractor,
    SecurityHeadersExtractor,
    EmailAuthExtractor,
    DNSSECExtractor,
    NetworkExposureExtractor,
    SoftwareCurrencyExtractor,
    CVEExposureExtractor,
    CloudInfraExtractor,
    WAFPresenceExtractor,
    CDNUsageExtractor,
)
from ...aggregators.implementations.cyber import (
    TLSConfigAggregator,
    SecurityHeadersAggregator,
    EmailAuthAggregator,
    DNSSECAggregator,
    NetworkExposureAggregator,
    SoftwareCurrencyAggregator,
    CVEExposureAggregator,
    CloudInfraAggregator,
    WAFPresenceAggregator,
    CDNUsageAggregator,
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


@register_inference_function("tls_configuration_basefunction")
def tls_configuration_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for tls_score signal."""
    start_time = time.time()
    
    try:
        extractor = TLSConfigExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="tls_score", score=50, confidence=0.3, error="Extraction failed")
        
        aggregator = TLSConfigAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("tls_score", 50) if agg_result.success else 50
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("tls_score", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "TLSConfigExtractor", "TLSConfigAggregator")
    except Exception as e:
        return SignalResult(signal_id="tls_score", score=50, confidence=0.0, error=str(e))


@register_inference_function("security_headers_basefunction")
def security_headers_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for security_headers signal."""
    start_time = time.time()
    
    try:
        extractor = SecurityHeadersExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="security_headers", score=50, confidence=0.3, error="Extraction failed")
        
        aggregator = SecurityHeadersAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("security_headers_score", 50) if agg_result.success else 50
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("security_headers", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "SecurityHeadersExtractor", "SecurityHeadersAggregator")
    except Exception as e:
        return SignalResult(signal_id="security_headers", score=50, confidence=0.0, error=str(e))


@register_inference_function("email_authentication_basefunction")
def email_authentication_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for email_auth signal."""
    start_time = time.time()
    
    try:
        extractor = EmailAuthExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="email_auth", score=50, confidence=0.3, error="Extraction failed")
        
        aggregator = EmailAuthAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("email_auth_score", 50) if agg_result.success else 50
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("email_auth", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "EmailAuthExtractor", "EmailAuthAggregator")
    except Exception as e:
        return SignalResult(signal_id="email_auth", score=50, confidence=0.0, error=str(e))


@register_inference_function("dnssec_basefunction")
def dnssec_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for dnssec signal."""
    start_time = time.time()
    
    try:
        extractor = DNSSECExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="dnssec", score=0, confidence=0.3, error="Extraction failed")
        
        aggregator = DNSSECAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("dnssec_score", 0) if agg_result.success else 0
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("dnssec", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "DNSSECExtractor", "DNSSECAggregator")
    except Exception as e:
        return SignalResult(signal_id="dnssec", score=0, confidence=0.0, error=str(e))


@register_inference_function("network_exposure_basefunction")
def network_exposure_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for exposure signal."""
    start_time = time.time()
    
    try:
        extractor = NetworkExposureExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="exposure", score=50, confidence=0.3, error="Extraction failed")
        
        aggregator = NetworkExposureAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("network_exposure_score", 50) if agg_result.success else 50
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("exposure", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "NetworkExposureExtractor", "NetworkExposureAggregator")
    except Exception as e:
        return SignalResult(signal_id="exposure", score=50, confidence=0.0, error=str(e))


@register_inference_function("software_currency_basefunction")
def software_currency_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for software_currency signal."""
    start_time = time.time()
    
    try:
        extractor = SoftwareCurrencyExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="software_currency", score=50, confidence=0.3, error="Extraction failed")
        
        aggregator = SoftwareCurrencyAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("software_currency_score", 50) if agg_result.success else 50
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("software_currency", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "SoftwareCurrencyExtractor", "SoftwareCurrencyAggregator")
    except Exception as e:
        return SignalResult(signal_id="software_currency", score=50, confidence=0.0, error=str(e))


@register_inference_function("cve_exposure_basefunction")
def cve_exposure_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for cve_exposure signal."""
    start_time = time.time()
    
    try:
        extractor = CVEExposureExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="cve_exposure", score=50, confidence=0.3, error="Extraction failed")
        
        aggregator = CVEExposureAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("cve_exposure_score", 50) if agg_result.success else 50
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("cve_exposure", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "CVEExposureExtractor", "CVEExposureAggregator")
    except Exception as e:
        return SignalResult(signal_id="cve_exposure", score=50, confidence=0.0, error=str(e))


@register_inference_function("cloud_infrastructure_basefunction")
def cloud_infrastructure_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for cloud_infrastructure signal."""
    start_time = time.time()
    
    try:
        extractor = CloudInfraExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="cloud_infrastructure", score=50, confidence=0.3, error="Extraction failed")
        
        aggregator = CloudInfraAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("cloud_infrastructure_score", 50) if agg_result.success else 50
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("cloud_infrastructure", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "CloudInfraExtractor", "CloudInfraAggregator")
    except Exception as e:
        return SignalResult(signal_id="cloud_infrastructure", score=50, confidence=0.0, error=str(e))


@register_inference_function("waf_presence_basefunction")
def waf_presence_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for waf_presence signal."""
    start_time = time.time()
    
    try:
        extractor = WAFPresenceExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="waf_presence", score=0, confidence=0.3, error="Extraction failed")
        
        aggregator = WAFPresenceAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("waf_score", 0) if agg_result.success else 0
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("waf_presence", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "WAFPresenceExtractor", "WAFPresenceAggregator")
    except Exception as e:
        return SignalResult(signal_id="waf_presence", score=0, confidence=0.0, error=str(e))


@register_inference_function("cdn_usage_basefunction")
def cdn_usage_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for cdn_usage signal."""
    start_time = time.time()
    
    try:
        extractor = CDNUsageExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="cdn_usage", score=0, confidence=0.3, error="Extraction failed")
        
        aggregator = CDNUsageAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("cdn_score", 0) if agg_result.success else 0
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("cdn_usage", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "CDNUsageExtractor", "CDNUsageAggregator")
    except Exception as e:
        return SignalResult(signal_id="cdn_usage", score=0, confidence=0.0, error=str(e))
