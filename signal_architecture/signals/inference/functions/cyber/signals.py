"""
Cyber Inference Functions - All Signal Groups

Maps YAML inference_utility_function names to pipeline orchestration.
Uses the extractor resolver for stub/production switching.
"""

import time
from ....types import SignalResult, InferenceContext
from ....inference.registry import register_inference_function
from ....extractors.resolver import get_extractor

# Import aggregators (these don't have production variants)
from ....aggregators.implementations.cyber import (
    CertificationAuthorityAggregator, CloudInfraAggregator, CustomerQualityAggregator,
    FinancialRelationshipAggregator, PartnerQualityAggregator, NetworkCentralityAggregator,
    SecondDegreeAggregator, DNSSECAggregator, TLSConfigAggregator, EmailAuthAggregator,
    SecurityHeadersAggregator, WAFPresenceAggregator, CDNUsageAggregator, SecurityTxtAggregator,
    BugBountyAggregator, CVEExposureAggregator, NetworkExposureAggregator, SoftwareCurrencyAggregator,
    CredentialExposureAggregator, DarkWebAggregator, SecurityPageAggregator, TechnicalContentAggregator,
    DeveloperResourcesAggregator, SecurityHiringAggregator, SecurityLeadershipAggregator,
    SecurityVendorAggregator, ComplianceBadgesAggregator, PrivacyPolicyAggregator,
    BreachHistoryAggregator, LitigationHistoryAggregator, SecurityRatingAggregator,
    ESGCyberAggregator, IndustryClassificationAggregator, CompanySizeAggregator, GeographyAggregator,
)
from ....aggregators.implementations.common import CreditRatingAggregator


def _run_pipeline(signal_id, extractor_name, aggregator, entity_id, context, score_field, default=50):
    start = time.time()
    try:
        extractor = get_extractor(extractor_name)
        ext = extractor.extract(entity_id, context=context)
        if not ext.success:
            return SignalResult(signal_id=signal_id, score=default, confidence=0.3, error="Extraction failed")
        agg = aggregator.aggregate([ext])
        score = agg.data.get(score_field, default) if agg.success else default
        return SignalResult(signal_id=signal_id, score=round(score, 1), confidence=1.0, execution_time_ms=(time.time()-start)*1000,
                          raw_data=ext.data, aggregated_data=agg.data, metadata={"extractor": type(extractor).__name__, "from_cache": ext.from_cache})
    except Exception as e:
        return SignalResult(signal_id=signal_id, score=default, confidence=0.0, error=str(e))


def _run_categorical(signal_id, extractor_name, aggregator, entity_id, context, cat_field, default):
    start = time.time()
    try:
        extractor = get_extractor(extractor_name)
        ext = extractor.extract(entity_id, context=context)
        if not ext.success:
            return SignalResult(signal_id=signal_id, category=default, confidence=0.3, error="Extraction failed")
        agg = aggregator.aggregate([ext])
        cat = agg.data.get(cat_field, default) if agg.success else default
        return SignalResult(signal_id=signal_id, category=cat, confidence=0.85, execution_time_ms=(time.time()-start)*1000,
                          raw_data=ext.data, aggregated_data=agg.data)
    except Exception as e:
        return SignalResult(signal_id=signal_id, category=default, confidence=0.0, error=str(e))


# CATEGORICAL
@register_inference_function("cyber_industry_classification_basefunction")
def f1(e, c): return _run_categorical("industry", "industry_classification", IndustryClassificationAggregator(), e, c, "industry_category", "OTHER")

@register_inference_function("company_size_basefunction")
def f2(e, c): return _run_categorical("company_size", "company_size", CompanySizeAggregator(), e, c, "size_category", "SMALL")

@register_inference_function("geography_basefunction")
def f3(e, c): return _run_categorical("geography", "operational_base", GeographyAggregator(), e, c, "primary_geography", "US")

# NETWORK AUTHORITY
@register_inference_function("certification_authority_basefunction")
def f4(e, c): return _run_pipeline("certification_authority", "certification_authority", CertificationAuthorityAggregator(), e, c, "certification_score", 40)

@register_inference_function("cloud_provider_basefunction")
def f5(e, c): return _run_pipeline("cloud_provider", "cloud_infra", CloudInfraAggregator(), e, c, "cloud_score", 50)

@register_inference_function("payment_processor_basefunction")
def f6(e, c): return _run_pipeline("payment_processor", "customer_quality", CustomerQualityAggregator(), e, c, "payment_score", 50)

@register_inference_function("financial_relationship_basefunction")
def f7(e, c): return _run_pipeline("financial_relationship", "financial_relationship", FinancialRelationshipAggregator(), e, c, "financial_score", 50)

@register_inference_function("industry_body_basefunction")
def f8(e, c): return _run_pipeline("industry_body", "partner_network", PartnerQualityAggregator(), e, c, "industry_body_score", 40)

@register_inference_function("network_centrality_basefunction")
def f9(e, c): return _run_pipeline("network_centrality", "network_centrality", NetworkCentralityAggregator(), e, c, "centrality_score", 50)

@register_inference_function("second_degree_basefunction")
def f10(e, c): return _run_pipeline("second_degree", "second_degree", SecondDegreeAggregator(), e, c, "second_degree_score", 50)

# TECHNICAL INFRASTRUCTURE
@register_inference_function("dns_security_basefunction")
def f11(e, c): return _run_pipeline("dns_security", "dnssec", DNSSECAggregator(), e, c, "dns_score", 50)

@register_inference_function("ssl_configuration_basefunction")
def f12(e, c): return _run_pipeline("ssl_configuration", "tls_config", TLSConfigAggregator(), e, c, "tls_score", 50)

@register_inference_function("email_security_basefunction")
def f13(e, c): return _run_pipeline("email_security", "email_auth", EmailAuthAggregator(), e, c, "email_score", 50)

@register_inference_function("cloud_infrastructure_basefunction")
def f14(e, c): return _run_pipeline("cloud_infrastructure", "cloud_infra", CloudInfraAggregator(), e, c, "cloud_infra_score", 50)

@register_inference_function("cdn_usage_basefunction")
def f15(e, c): return _run_pipeline("cdn_usage", "cdn_usage", CDNUsageAggregator(), e, c, "cdn_score", 50)

@register_inference_function("waf_detection_basefunction")
def f16(e, c): return _run_pipeline("waf_detection", "waf_presence", WAFPresenceAggregator(), e, c, "waf_score", 50)

@register_inference_function("security_headers_basefunction")
def f17(e, c): return _run_pipeline("security_headers", "security_headers", SecurityHeadersAggregator(), e, c, "headers_score", 50)

@register_inference_function("vulnerability_disclosure_basefunction")
def f18(e, c): return _run_pipeline("vulnerability_disclosure", "security_txt", SecurityTxtAggregator(), e, c, "security_txt_score", 40)

@register_inference_function("patch_cadence_basefunction")
def f19(e, c): return _run_pipeline("patch_cadence", "software_currency", SoftwareCurrencyAggregator(), e, c, "currency_score", 50)

@register_inference_function("tech_stack_basefunction")
def f20(e, c): return _run_pipeline("tech_stack", "cve_exposure", CVEExposureAggregator(), e, c, "cve_score", 50)

@register_inference_function("subdomain_hygiene_basefunction")
def f21(e, c): return _run_pipeline("subdomain_hygiene", "network_exposure", NetworkExposureAggregator(), e, c, "exposure_score", 60)

@register_inference_function("bug_bounty_basefunction")
def f22(e, c): return _run_pipeline("bug_bounty", "bug_bounty", BugBountyAggregator(), e, c, "bug_bounty_score", 30)

# CORPORATE FOOTPRINT
@register_inference_function("cyber_website_quality_basefunction")
def f23(e, c): return _run_pipeline("website_quality", "technical_content", TechnicalContentAggregator(), e, c, "content_score", 50)

@register_inference_function("security_page_basefunction")
def f24(e, c): return _run_pipeline("security_page", "security_page", SecurityPageAggregator(), e, c, "security_page_score", 40)

@register_inference_function("cyber_hiring_signals_basefunction")
def f25(e, c): return _run_pipeline("hiring_signals", "security_hiring", SecurityHiringAggregator(), e, c, "hiring_score", 50)

@register_inference_function("security_leadership_basefunction")
def f26(e, c): return _run_pipeline("security_leadership", "security_leadership", SecurityLeadershipAggregator(), e, c, "leadership_score", 50)

@register_inference_function("developer_resources_basefunction")
def f27(e, c): return _run_pipeline("developer_resources", "developer_resources", DeveloperResourcesAggregator(), e, c, "developer_score", 50)

@register_inference_function("security_vendor_basefunction")
def f28(e, c): return _run_pipeline("security_vendor", "security_vendor", SecurityVendorAggregator(), e, c, "vendor_score", 50)

@register_inference_function("compliance_badges_basefunction")
def f29(e, c): return _run_pipeline("compliance_badges", "compliance_badges", ComplianceBadgesAggregator(), e, c, "compliance_score", 50)

@register_inference_function("privacy_policy_basefunction")
def f30(e, c): return _run_pipeline("privacy_policy", "privacy_policy", PrivacyPolicyAggregator(), e, c, "privacy_score", 50)

# PUBLIC RECORD
@register_inference_function("breach_history_basefunction")
def f31(e, c): return _run_pipeline("breach_history", "breach_history", BreachHistoryAggregator(), e, c, "breach_score", 100)

@register_inference_function("cyber_regulatory_action_basefunction")
def f32(e, c): return _run_pipeline("regulatory_action", "credential_exposure", CredentialExposureAggregator(), e, c, "credential_score", 100)

@register_inference_function("litigation_history_basefunction")
def f33(e, c): return _run_pipeline("litigation_history", "litigation_history", LitigationHistoryAggregator(), e, c, "litigation_score", 100)

@register_inference_function("data_handling_basefunction")
def f34(e, c): return _run_pipeline("data_handling", "dark_web", DarkWebAggregator(), e, c, "dark_web_score", 70)

# STRUCTURED DATA
@register_inference_function("security_rating_basefunction")
def f35(e, c): return _run_pipeline("security_rating", "security_rating", SecurityRatingAggregator(), e, c, "security_rating_score", 50)

@register_inference_function("bitsight_score_basefunction")
def f36(e, c): return _run_pipeline("bitsight_score", "security_rating", SecurityRatingAggregator(), e, c, "bitsight_score", 50)

@register_inference_function("cyber_credit_rating_basefunction")
def f37(e, c): return _run_pipeline("credit_rating", "credit_rating", CreditRatingAggregator(), e, c, "average_rating_score", 50)

@register_inference_function("data_broker_presence_basefunction")
def f38(e, c): return _run_pipeline("data_broker_presence", "esg_cyber", ESGCyberAggregator(), e, c, "esg_score", 60)
