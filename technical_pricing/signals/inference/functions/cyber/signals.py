"""
Cyber Inference Functions - All Signal Groups

Maps YAML inference_utility_function names to pipeline orchestration.
"""

import time
from ....types import SignalResult, InferenceContext
from ....inference.registry import register_inference_function

# Import extractors
from ....extractors.stubs.cyber import (
    CertificationAuthorityExtractor, CloudInfraExtractor, CustomerQualityExtractor,
    FinancialRelationshipExtractor, PartnerNetworkExtractor, NetworkCentralityExtractor,
    SecondDegreeExtractor, DNSSECExtractor, TLSConfigExtractor, EmailAuthExtractor,
    SecurityHeadersExtractor, WAFPresenceExtractor, CDNUsageExtractor, SecurityTxtExtractor,
    BugBountyExtractor, CVEExposureExtractor, NetworkExposureExtractor, SoftwareCurrencyExtractor,
    CredentialExposureExtractor, DarkWebExtractor, SecurityPageExtractor, TechnicalContentExtractor,
    DeveloperResourcesExtractor, SecurityHiringExtractor, SecurityLeadershipExtractor,
    SecurityVendorExtractor, ComplianceBadgesExtractor, PrivacyPolicyExtractor,
    BreachHistoryExtractor, LitigationHistoryExtractor, SecurityRatingExtractor,
    ESGCyberExtractor, IndustryClassificationExtractor, CompanySizeExtractor, OperationalBaseExtractor,
)
from ....extractors.stubs.common import CreditRatingExtractor

# Import aggregators
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


def _run_pipeline(signal_id, extractor, aggregator, entity_id, context, score_field, default=50):
    start = time.time()
    try:
        ext = extractor.extract(entity_id, context=context)
        if not ext.success:
            return SignalResult(signal_id=signal_id, score=default, confidence=0.3, error="Extraction failed")
        agg = aggregator.aggregate([ext])
        score = agg.data.get(score_field, default) if agg.success else default
        return SignalResult(signal_id=signal_id, score=round(score, 1), confidence=1.0, execution_time_ms=(time.time()-start)*1000,
                          raw_data=ext.data, aggregated_data=agg.data, metadata={"extractor": type(extractor).__name__, "from_cache": ext.from_cache})
    except Exception as e:
        return SignalResult(signal_id=signal_id, score=default, confidence=0.0, error=str(e))


def _run_categorical(signal_id, extractor, aggregator, entity_id, context, cat_field, default):
    start = time.time()
    try:
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
def f1(e, c): return _run_categorical("industry", IndustryClassificationExtractor(), IndustryClassificationAggregator(), e, c, "industry_category", "OTHER")

@register_inference_function("company_size_basefunction")
def f2(e, c): return _run_categorical("company_size", CompanySizeExtractor(), CompanySizeAggregator(), e, c, "size_category", "SMALL")

@register_inference_function("geography_basefunction")
def f3(e, c): return _run_categorical("geography", OperationalBaseExtractor(), GeographyAggregator(), e, c, "primary_geography", "US")

# NETWORK AUTHORITY
@register_inference_function("certification_authority_basefunction")
def f4(e, c): return _run_pipeline("certification_authority", CertificationAuthorityExtractor(), CertificationAuthorityAggregator(), e, c, "certification_score", 40)

@register_inference_function("cloud_provider_basefunction")
def f5(e, c): return _run_pipeline("cloud_provider", CloudInfraExtractor(), CloudInfraAggregator(), e, c, "cloud_score", 50)

@register_inference_function("payment_processor_basefunction")
def f6(e, c): return _run_pipeline("payment_processor", CustomerQualityExtractor(), CustomerQualityAggregator(), e, c, "payment_score", 50)

@register_inference_function("financial_relationship_basefunction")
def f7(e, c): return _run_pipeline("financial_relationship", FinancialRelationshipExtractor(), FinancialRelationshipAggregator(), e, c, "financial_score", 50)

@register_inference_function("industry_body_basefunction")
def f8(e, c): return _run_pipeline("industry_body", PartnerNetworkExtractor(), PartnerQualityAggregator(), e, c, "industry_body_score", 40)

@register_inference_function("network_centrality_basefunction")
def f9(e, c): return _run_pipeline("network_centrality", NetworkCentralityExtractor(), NetworkCentralityAggregator(), e, c, "centrality_score", 50)

@register_inference_function("second_degree_basefunction")
def f10(e, c): return _run_pipeline("second_degree", SecondDegreeExtractor(), SecondDegreeAggregator(), e, c, "second_degree_score", 50)

# TECHNICAL INFRASTRUCTURE
@register_inference_function("dns_security_basefunction")
def f11(e, c): return _run_pipeline("dns_security", DNSSECExtractor(), DNSSECAggregator(), e, c, "dns_score", 50)

@register_inference_function("ssl_configuration_basefunction")
def f12(e, c): return _run_pipeline("ssl_configuration", TLSConfigExtractor(), TLSConfigAggregator(), e, c, "tls_score", 50)

@register_inference_function("email_security_basefunction")
def f13(e, c): return _run_pipeline("email_security", EmailAuthExtractor(), EmailAuthAggregator(), e, c, "email_score", 50)

@register_inference_function("cloud_infrastructure_basefunction")
def f14(e, c): return _run_pipeline("cloud_infrastructure", CloudInfraExtractor(), CloudInfraAggregator(), e, c, "cloud_infra_score", 50)

@register_inference_function("cdn_usage_basefunction")
def f15(e, c): return _run_pipeline("cdn_usage", CDNUsageExtractor(), CDNUsageAggregator(), e, c, "cdn_score", 50)

@register_inference_function("waf_detection_basefunction")
def f16(e, c): return _run_pipeline("waf_detection", WAFPresenceExtractor(), WAFPresenceAggregator(), e, c, "waf_score", 50)

@register_inference_function("security_headers_basefunction")
def f17(e, c): return _run_pipeline("security_headers", SecurityHeadersExtractor(), SecurityHeadersAggregator(), e, c, "headers_score", 50)

@register_inference_function("vulnerability_disclosure_basefunction")
def f18(e, c): return _run_pipeline("vulnerability_disclosure", SecurityTxtExtractor(), SecurityTxtAggregator(), e, c, "security_txt_score", 40)

@register_inference_function("patch_cadence_basefunction")
def f19(e, c): return _run_pipeline("patch_cadence", SoftwareCurrencyExtractor(), SoftwareCurrencyAggregator(), e, c, "currency_score", 50)

@register_inference_function("tech_stack_basefunction")
def f20(e, c): return _run_pipeline("tech_stack", CVEExposureExtractor(), CVEExposureAggregator(), e, c, "cve_score", 50)

@register_inference_function("subdomain_hygiene_basefunction")
def f21(e, c): return _run_pipeline("subdomain_hygiene", NetworkExposureExtractor(), NetworkExposureAggregator(), e, c, "exposure_score", 60)

@register_inference_function("bug_bounty_basefunction")
def f22(e, c): return _run_pipeline("bug_bounty", BugBountyExtractor(), BugBountyAggregator(), e, c, "bug_bounty_score", 30)

# CORPORATE FOOTPRINT
@register_inference_function("cyber_website_quality_basefunction")
def f23(e, c): return _run_pipeline("website_quality", TechnicalContentExtractor(), TechnicalContentAggregator(), e, c, "content_score", 50)

@register_inference_function("security_page_basefunction")
def f24(e, c): return _run_pipeline("security_page", SecurityPageExtractor(), SecurityPageAggregator(), e, c, "security_page_score", 40)

@register_inference_function("cyber_hiring_signals_basefunction")
def f25(e, c): return _run_pipeline("hiring_signals", SecurityHiringExtractor(), SecurityHiringAggregator(), e, c, "hiring_score", 50)

@register_inference_function("security_leadership_basefunction")
def f26(e, c): return _run_pipeline("security_leadership", SecurityLeadershipExtractor(), SecurityLeadershipAggregator(), e, c, "leadership_score", 50)

@register_inference_function("developer_resources_basefunction")
def f27(e, c): return _run_pipeline("developer_resources", DeveloperResourcesExtractor(), DeveloperResourcesAggregator(), e, c, "developer_score", 50)

@register_inference_function("security_vendor_basefunction")
def f28(e, c): return _run_pipeline("security_vendor", SecurityVendorExtractor(), SecurityVendorAggregator(), e, c, "vendor_score", 50)

@register_inference_function("compliance_badges_basefunction")
def f29(e, c): return _run_pipeline("compliance_badges", ComplianceBadgesExtractor(), ComplianceBadgesAggregator(), e, c, "compliance_score", 50)

@register_inference_function("privacy_policy_basefunction")
def f30(e, c): return _run_pipeline("privacy_policy", PrivacyPolicyExtractor(), PrivacyPolicyAggregator(), e, c, "privacy_score", 50)

# PUBLIC RECORD
@register_inference_function("breach_history_basefunction")
def f31(e, c): return _run_pipeline("breach_history", BreachHistoryExtractor(), BreachHistoryAggregator(), e, c, "breach_score", 100)

@register_inference_function("cyber_regulatory_action_basefunction")
def f32(e, c): return _run_pipeline("regulatory_action", CredentialExposureExtractor(), CredentialExposureAggregator(), e, c, "credential_score", 100)

@register_inference_function("litigation_history_basefunction")
def f33(e, c): return _run_pipeline("litigation_history", LitigationHistoryExtractor(), LitigationHistoryAggregator(), e, c, "litigation_score", 100)

@register_inference_function("data_handling_basefunction")
def f34(e, c): return _run_pipeline("data_handling", DarkWebExtractor(), DarkWebAggregator(), e, c, "dark_web_score", 70)

# STRUCTURED DATA
@register_inference_function("security_rating_basefunction")
def f35(e, c): return _run_pipeline("security_rating", SecurityRatingExtractor(), SecurityRatingAggregator(), e, c, "security_rating_score", 50)

@register_inference_function("bitsight_score_basefunction")
def f36(e, c): return _run_pipeline("bitsight_score", SecurityRatingExtractor(), SecurityRatingAggregator(), e, c, "bitsight_score", 50)

@register_inference_function("cyber_credit_rating_basefunction")
def f37(e, c): return _run_pipeline("credit_rating", CreditRatingExtractor(), CreditRatingAggregator(), e, c, "average_rating_score", 50)

@register_inference_function("data_broker_presence_basefunction")
def f38(e, c): return _run_pipeline("data_broker_presence", ESGCyberExtractor(), ESGCyberAggregator(), e, c, "esg_score", 60)
