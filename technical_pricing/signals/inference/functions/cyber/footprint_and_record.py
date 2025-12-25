"""
Cyber Inference Functions - Corporate Footprint & Public Record Signal Groups

CORPORATE FOOTPRINT signals:
- security_page: Security/trust page presence and quality
- privacy_policy: Privacy policy quality
- security_txt: RFC 9116 security.txt file
- bug_bounty: Bug bounty program presence
- security_hiring: Security job postings
- technical_content: Security-focused blog content
- developer_resources: API docs and developer portal
- security_leadership: CISO/security leadership visibility
- compliance_badges: Displayed certifications

PUBLIC RECORD signals:
- breach_history: Historical data breaches
- regulatory_action: Regulatory enforcement (uses common)
- litigation_history: Privacy/data breach lawsuits
- credential_exposure: Corporate credential exposure
- dark_web: Dark web data exposure
"""

import time
from typing import Dict, Any, Optional

from ...types import SignalResult, InferenceContext
from ...inference.registry import register_inference_function

# Corporate Footprint Extractors
from ...extractors.stubs.cyber import (
    SecurityPageExtractor,
    PrivacyPolicyExtractor,
    SecurityTxtExtractor,
    BugBountyExtractor,
    SecurityHiringExtractor,
    TechnicalContentExtractor,
    DeveloperResourcesExtractor,
    SecurityLeadershipExtractor,
    ComplianceBadgesExtractor,
)

# Public Record Extractors
from ...extractors.stubs.cyber import (
    BreachHistoryExtractor,
    LitigationHistoryExtractor,
    CredentialExposureExtractor,
    DarkWebExtractor,
)
from ...extractors.stubs.common import RegulatoryEnforcementExtractor

# Corporate Footprint Aggregators
from ...aggregators.implementations.cyber import (
    SecurityPageAggregator,
    PrivacyPolicyAggregator,
    SecurityTxtAggregator,
    BugBountyAggregator,
    SecurityHiringAggregator,
    TechnicalContentAggregator,
    DeveloperResourcesAggregator,
    SecurityLeadershipAggregator,
    ComplianceBadgesAggregator,
)

# Public Record Aggregators
from ...aggregators.implementations.cyber import (
    BreachHistoryAggregator,
    LitigationHistoryAggregator,
    CredentialExposureAggregator,
    DarkWebAggregator,
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


# =============================================================================
# CORPORATE FOOTPRINT SIGNALS
# =============================================================================

@register_inference_function("security_page_basefunction")
def security_page_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for security_page signal."""
    start_time = time.time()
    
    try:
        extractor = SecurityPageExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="security_page", score=30, confidence=0.3, error="Extraction failed")
        
        aggregator = SecurityPageAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("security_page_score", 30) if agg_result.success else 30
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("security_page", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "SecurityPageExtractor", "SecurityPageAggregator")
    except Exception as e:
        return SignalResult(signal_id="security_page", score=30, confidence=0.0, error=str(e))


@register_inference_function("privacy_policy_basefunction")
def privacy_policy_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for privacy_policy signal."""
    start_time = time.time()
    
    try:
        extractor = PrivacyPolicyExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="privacy_policy", score=50, confidence=0.3, error="Extraction failed")
        
        aggregator = PrivacyPolicyAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("privacy_policy_score", 50) if agg_result.success else 50
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("privacy_policy", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "PrivacyPolicyExtractor", "PrivacyPolicyAggregator")
    except Exception as e:
        return SignalResult(signal_id="privacy_policy", score=50, confidence=0.0, error=str(e))


@register_inference_function("security_txt_basefunction")
def security_txt_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for security_txt signal."""
    start_time = time.time()
    
    try:
        extractor = SecurityTxtExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="security_txt", score=0, confidence=0.3, error="Extraction failed")
        
        aggregator = SecurityTxtAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("security_txt_score", 0) if agg_result.success else 0
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("security_txt", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "SecurityTxtExtractor", "SecurityTxtAggregator")
    except Exception as e:
        return SignalResult(signal_id="security_txt", score=0, confidence=0.0, error=str(e))


@register_inference_function("bug_bounty_basefunction")
def bug_bounty_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for bug_bounty signal."""
    start_time = time.time()
    
    try:
        extractor = BugBountyExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="bug_bounty", score=0, confidence=0.3, error="Extraction failed")
        
        aggregator = BugBountyAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("bug_bounty_score", 0) if agg_result.success else 0
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("bug_bounty", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "BugBountyExtractor", "BugBountyAggregator")
    except Exception as e:
        return SignalResult(signal_id="bug_bounty", score=0, confidence=0.0, error=str(e))


@register_inference_function("security_hiring_basefunction")
def security_hiring_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for security_hiring signal."""
    start_time = time.time()
    
    try:
        extractor = SecurityHiringExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="security_hiring", score=30, confidence=0.3, error="Extraction failed")
        
        aggregator = SecurityHiringAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("security_hiring_score", 30) if agg_result.success else 30
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("security_hiring", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "SecurityHiringExtractor", "SecurityHiringAggregator")
    except Exception as e:
        return SignalResult(signal_id="security_hiring", score=30, confidence=0.0, error=str(e))


@register_inference_function("technical_quality_basefunction")
def technical_quality_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for technical_content signal."""
    start_time = time.time()
    
    try:
        extractor = TechnicalContentExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="technical_content", score=30, confidence=0.3, error="Extraction failed")
        
        aggregator = TechnicalContentAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("technical_content_score", 30) if agg_result.success else 30
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("technical_content", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "TechnicalContentExtractor", "TechnicalContentAggregator")
    except Exception as e:
        return SignalResult(signal_id="technical_content", score=30, confidence=0.0, error=str(e))


@register_inference_function("developer_resources_basefunction")
def developer_resources_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for developer_resources signal."""
    start_time = time.time()
    
    try:
        extractor = DeveloperResourcesExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="developer_resources", score=30, confidence=0.3, error="Extraction failed")
        
        aggregator = DeveloperResourcesAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("developer_resources_score", 30) if agg_result.success else 30
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("developer_resources", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "DeveloperResourcesExtractor", "DeveloperResourcesAggregator")
    except Exception as e:
        return SignalResult(signal_id="developer_resources", score=30, confidence=0.0, error=str(e))


@register_inference_function("security_leadership_basefunction")
def security_leadership_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for security_leadership signal."""
    start_time = time.time()
    
    try:
        extractor = SecurityLeadershipExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="security_leadership", score=30, confidence=0.3, error="Extraction failed")
        
        aggregator = SecurityLeadershipAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("security_leadership_score", 30) if agg_result.success else 30
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("security_leadership", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "SecurityLeadershipExtractor", "SecurityLeadershipAggregator")
    except Exception as e:
        return SignalResult(signal_id="security_leadership", score=30, confidence=0.0, error=str(e))


@register_inference_function("compliance_badges_basefunction")
def compliance_badges_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for compliance_badges signal."""
    start_time = time.time()
    
    try:
        extractor = ComplianceBadgesExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="compliance_badges", score=30, confidence=0.3, error="Extraction failed")
        
        aggregator = ComplianceBadgesAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("compliance_badges_score", 30) if agg_result.success else 30
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("compliance_badges", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "ComplianceBadgesExtractor", "ComplianceBadgesAggregator")
    except Exception as e:
        return SignalResult(signal_id="compliance_badges", score=30, confidence=0.0, error=str(e))


# =============================================================================
# PUBLIC RECORD SIGNALS
# =============================================================================

@register_inference_function("breach_history_basefunction")
def breach_history_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for breach_history signal."""
    start_time = time.time()
    
    try:
        extractor = BreachHistoryExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="breach_history", score=100, confidence=0.3, error="Extraction failed")
        
        aggregator = BreachHistoryAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("breach_history_score", 100) if agg_result.success else 100
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("breach_history", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "BreachHistoryExtractor", "BreachHistoryAggregator")
    except Exception as e:
        return SignalResult(signal_id="breach_history", score=100, confidence=0.0, error=str(e))


@register_inference_function("regulatory_action_basefunction")
def regulatory_action_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for regulatory_action signal (uses common extractor)."""
    start_time = time.time()
    
    try:
        extractor = RegulatoryEnforcementExtractor()
        extract_result = extractor.extract(entity_id, regulator_type="DATA_PRIVACY", context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="regulatory_action", score=100, confidence=0.3, error="Extraction failed")
        
        aggregator = RegulatoryEnforcementAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("enforcement_score", 100) if agg_result.success else 100
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("regulatory_action", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "RegulatoryEnforcementExtractor", "RegulatoryEnforcementAggregator")
    except Exception as e:
        return SignalResult(signal_id="regulatory_action", score=100, confidence=0.0, error=str(e))


@register_inference_function("litigation_history_basefunction")
def litigation_history_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for litigation_history signal."""
    start_time = time.time()
    
    try:
        extractor = LitigationHistoryExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="litigation_history", score=100, confidence=0.3, error="Extraction failed")
        
        aggregator = LitigationHistoryAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("litigation_score", 100) if agg_result.success else 100
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("litigation_history", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "LitigationHistoryExtractor", "LitigationHistoryAggregator")
    except Exception as e:
        return SignalResult(signal_id="litigation_history", score=100, confidence=0.0, error=str(e))


@register_inference_function("credential_exposure_basefunction")
def credential_exposure_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for credential_exposure signal."""
    start_time = time.time()
    
    try:
        extractor = CredentialExposureExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="credential_exposure", score=70, confidence=0.3, error="Extraction failed")
        
        aggregator = CredentialExposureAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("credential_exposure_score", 70) if agg_result.success else 70
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("credential_exposure", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "CredentialExposureExtractor", "CredentialExposureAggregator")
    except Exception as e:
        return SignalResult(signal_id="credential_exposure", score=70, confidence=0.0, error=str(e))


@register_inference_function("dark_web_basefunction")
def dark_web_basefunction(entity_id: str, context: InferenceContext) -> SignalResult:
    """Inference function for dark_web signal."""
    start_time = time.time()
    
    try:
        extractor = DarkWebExtractor()
        extract_result = extractor.extract(entity_id, context=context)
        
        if not extract_result.success:
            return SignalResult(signal_id="dark_web", score=100, confidence=0.3, error="Extraction failed")
        
        aggregator = DarkWebAggregator()
        agg_result = aggregator.aggregate([extract_result])
        
        score = agg_result.data.get("dark_web_score", 100) if agg_result.success else 100
        execution_time = (time.time() - start_time) * 1000
        
        return _create_signal_result("dark_web", round(score, 1), 1.0, execution_time,
                                     extract_result, agg_result, "DarkWebExtractor", "DarkWebAggregator")
    except Exception as e:
        return SignalResult(signal_id="dark_web", score=100, confidence=0.0, error=str(e))
