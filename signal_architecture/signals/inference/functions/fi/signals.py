"""
FI Inference Functions - All Signal Groups

Maps YAML inference_utility_function names to pipeline orchestration.
47 signals + 4 categorical = 51 total functions
"""

import time
from ....types import SignalResult, InferenceContext
from ....inference.registry import register_inference_function

# V6/E10 neutral stand-ins — real extractor wiring lands via the
# D-series production extractors (Stage 6). Until then every call
# returns a neutral SignalResult(score=50, confidence=0.5).

async def _run_pipeline(signal_id, *args, default=50.0, **kwargs):
    """Neutral scoring stand-in. Accepts the legacy
    (signal_id, extractor, aggregator, entity_id, context, ...)
    signature but ignores the extractor + aggregator args."""
    return SignalResult(
        signal_id=signal_id,
        score=float(default),
        confidence=0.5,
        execution_time_ms=0.0,
    )


async def _run_categorical(signal_id, *args, default="OTHER", **kwargs):
    """Neutral categorical stand-in — see _run_pipeline."""
    return SignalResult(
        signal_id=signal_id,
        category=default,
        confidence=0.5,
        execution_time_ms=0.0,
    )


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


# =============================================================================
# CATEGORICAL (4)
# =============================================================================

@register_inference_function("institution_type_basefunction")
def f1(e, c): return _run_categorical("institution_type", InstitutionTypeExtractor(), InstitutionTypeAggregator(), e, c, "institution_type", "OTHER")

@register_inference_function("regulatory_authority_basefunction")
def f2(e, c): return _run_categorical("regulatory_framework", RegulatoryAuthorityExtractor(), RegulatoryAuthorityAggregator(), e, c, "regulatory_framework", "STATE")

@register_inference_function("asset_size_basefunction")
def f3(e, c): return _run_categorical("asset_size_band", AssetSizeExtractor(), AssetSizeAggregator(), e, c, "asset_size_band", "COMMUNITY")

@register_inference_function("publically_traded_basefunction")
def f4(e, c): return _run_categorical("publicly_traded", PubliclyTradedExtractor(), PubliclyTradedAggregator(), e, c, "publicly_traded", "PRIVATE")


# =============================================================================
# NETWORK AUTHORITY (7)
# =============================================================================

@register_inference_function("correspondent_quality_basefunction")
def f5(e, c): return _run_pipeline("correspondent_quality", CorrespondentQualityExtractor(), CorrespondentQualityAggregator(), e, c, "correspondent_quality_score", 50)

@register_inference_function("fhlb_membership_basefunction")
def f6(e, c): return _run_pipeline("fhlb_membership", FHLBMembershipExtractor(), FHLBMembershipAggregator(), e, c, "fhlb_membership_score", 50)

@register_inference_function("clearing_relationship_basefunction")
def f7(e, c): return _run_pipeline("clearing_relationship", ClearingRelationshipExtractor(), ClearingRelationshipAggregator(), e, c, "clearing_relationship_score", 50)

@register_inference_function("fi_auditor_quality_basefunction")
def f8(e, c): return _run_pipeline("auditor_quality", FIAuditorQualityExtractor(), FIAuditorQualityAggregator(), e, c, "auditor_quality_score", 50)

@register_inference_function("legal_counsel_basefunction")
def f9(e, c): return _run_pipeline("legal_counsel", LegalCounselExtractor(), LegalCounselAggregator(), e, c, "legal_counsel_score", 50)

@register_inference_function("fi_industry_association_basefunction")
def f10(e, c): return _run_pipeline("industry_association", FIIndustryAssociationExtractor(), FIIndustryAssociationAggregator(), e, c, "industry_association_score", 40)

@register_inference_function("fi_credit_rating_basefunction")
def f11(e, c): return _run_pipeline("credit_rating", FICreditRatingExtractor(), FICreditRatingAggregator(), e, c, "credit_rating_score", 50)


# =============================================================================
# REGULATORY COMPLIANCE (7)
# =============================================================================

@register_inference_function("examination_rating_basefunction")
def f12(e, c): return _run_pipeline("examination_rating", ExaminationRatingExtractor(), ExaminationRatingAggregator(), e, c, "examination_rating_score", 60)

@register_inference_function("enforcement_action_basefunction")
def f13(e, c): return _run_pipeline("enforcement_action", EnforcementActionExtractor(), EnforcementActionAggregator(), e, c, "enforcement_action_score", 100)

@register_inference_function("informal_action_basefunction")
def f14(e, c): return _run_pipeline("informal_action", InformalActionExtractor(), InformalActionAggregator(), e, c, "informal_action_score", 90)

@register_inference_function("cra_rating_basefunction")
def f15(e, c): return _run_pipeline("cra_rating", CRARatingExtractor(), CRARatingAggregator(), e, c, "cra_rating_score", 75)

@register_inference_function("bsa_aml_basefunction")
def f16(e, c): return _run_pipeline("bsa_aml", BSAAMLExtractor(), BSAAMLAggregator(), e, c, "bsa_aml_score", 75)

@register_inference_function("fair_lending_basefunction")
def f17(e, c): return _run_pipeline("fair_lending", FairLendingExtractor(), FairLendingAggregator(), e, c, "fair_lending_score", 85)

@register_inference_function("consumer_compliance_basefunction")
def f18(e, c): return _run_pipeline("consumer_compliance", ConsumerComplianceExtractor(), ConsumerComplianceAggregator(), e, c, "consumer_compliance_score", 75)


# =============================================================================
# FINANCIAL CONDITION (7)
# =============================================================================

@register_inference_function("capital_ratio_basefunction")
def f19(e, c): return _run_pipeline("capital_ratio", CapitalRatioExtractor(), CapitalRatioAggregator(), e, c, "capital_ratio_score", 70)

@register_inference_function("asset_quality_basefunction")
def f20(e, c): return _run_pipeline("asset_quality", AssetQualityExtractor(), AssetQualityAggregator(), e, c, "asset_quality_score", 70)

@register_inference_function("liquidity_basefunction")
def f21(e, c): return _run_pipeline("liquidity", LiquidityExtractor(), LiquidityAggregator(), e, c, "liquidity_score", 70)

@register_inference_function("earnings_basefunction")
def f22(e, c): return _run_pipeline("earnings", EarningsExtractor(), EarningsAggregator(), e, c, "earnings_score", 70)

@register_inference_function("fi_concentration_basefunction")
def f23(e, c): return _run_pipeline("concentration", ConcentrationExtractor(), ConcentrationAggregator(), e, c, "concentration_score", 70)

@register_inference_function("interest_rate_basefunction")
def f24(e, c): return _run_pipeline("interest_rate_risk", InterestRateRiskExtractor(), InterestRateRiskAggregator(), e, c, "interest_rate_risk_score", 70)

@register_inference_function("growth_rate_basefunction")
def f25(e, c): return _run_pipeline("growth_rate", GrowthRateExtractor(), GrowthRateAggregator(), e, c, "growth_rate_score", 80)


# =============================================================================
# GOVERNANCE (6)
# =============================================================================

@register_inference_function("fi_board_independance_basefunction")
def f26(e, c): return _run_pipeline("board_independence", FIBoardIndependenceExtractor(), FIBoardIndependenceAggregator(), e, c, "board_independence_score", 60)

@register_inference_function("board_expertise_basefunction")
def f27(e, c): return _run_pipeline("board_expertise", BoardExpertiseExtractor(), BoardExpertiseAggregator(), e, c, "board_expertise_score", 60)

@register_inference_function("fi_executive_stability_basefunction")
def f28(e, c): return _run_pipeline("executive_stability", FIExecutiveStabilityExtractor(), FIExecutiveStabilityAggregator(), e, c, "executive_stability_score", 70)

@register_inference_function("risk_committee_basefunction")
def f29(e, c): return _run_pipeline("risk_committee", RiskCommitteeExtractor(), RiskCommitteeAggregator(), e, c, "risk_committee_score", 50)

@register_inference_function("audit_committee_basefunction")
def f30(e, c): return _run_pipeline("audit_committee", AuditCommitteeExtractor(), AuditCommitteeAggregator(), e, c, "audit_committee_score", 70)

@register_inference_function("related_party_basefunction")
def f31(e, c): return _run_pipeline("related_party", RelatedPartyExtractor(), RelatedPartyAggregator(), e, c, "related_party_score", 80)


# =============================================================================
# OPERATIONAL RISK (5)
# =============================================================================

@register_inference_function("cfpb_compliant_basefunction")
def f32(e, c): return _run_pipeline("cfpb_complaint", CFPBComplaintExtractor(), CFPBComplaintAggregator(), e, c, "cfpb_complaint_score", 50)

@register_inference_function("bbb_compliant_basefunction")
def f33(e, c): return _run_pipeline("bbb_complaint", BBBComplaintExtractor(), BBBComplaintAggregator(), e, c, "bbb_complaint_score", 60)

@register_inference_function("fi_litigation_basefunction")
def f34(e, c): return _run_pipeline("litigation", FILitigationExtractor(), FILitigationAggregator(), e, c, "litigation_score", 100)

@register_inference_function("fi_breach_history_basefunction")
def f35(e, c): return _run_pipeline("breach_history", FIBreachHistoryExtractor(), FIBreachHistoryAggregator(), e, c, "breach_history_score", 100)

@register_inference_function("operational_incidents_basefunction")
def f36(e, c): return _run_pipeline("operational_incident", OperationalIncidentExtractor(), OperationalIncidentAggregator(), e, c, "operational_incident_score", 85)


# =============================================================================
# CYBER SECURITY (6)
# =============================================================================

@register_inference_function("tls_configuration_basefunction")
def f37(e, c): return _run_pipeline("tls_score", FITLSConfigExtractor(), FITLSConfigAggregator(), e, c, "tls_score", 65)

@register_inference_function("email_authentication_basefunction")
def f38(e, c): return _run_pipeline("email_auth", FIEmailAuthExtractor(), FIEmailAuthAggregator(), e, c, "email_auth_score", 50)

@register_inference_function("fi_security_headers_basefunction")
def f39(e, c): return _run_pipeline("security_headers", FISecurityHeadersExtractor(), FISecurityHeadersAggregator(), e, c, "security_headers_score", 55)

@register_inference_function("fi_network_exposure_basefunction")
def f40(e, c): return _run_pipeline("network_exposure", FINetworkExposureExtractor(), FINetworkExposureAggregator(), e, c, "network_exposure_score", 70)

@register_inference_function("fi_cve_exposure_basefunction")
def f41(e, c): return _run_pipeline("vulnerability", FICVEExposureExtractor(), FICVEExposureAggregator(), e, c, "cve_exposure_score", 80)

@register_inference_function("fi_security_rating_basefunction")
def f42(e, c): return _run_pipeline("security_rating", FISecurityRatingExtractor(), FISecurityRatingAggregator(), e, c, "security_rating_score", 50)


# =============================================================================
# CORPORATE FOOTPRINT (6)
# =============================================================================

@register_inference_function("investor_relations_basefunction")
def f43(e, c): return _run_pipeline("investor_relations", InvestorRelationsExtractor(), InvestorRelationsAggregator(), e, c, "investor_relations_score", 50)

@register_inference_function("fi_disclosure_quality_basefunction")
def f44(e, c): return _run_pipeline("disclosure_quality", FIDisclosureQualityExtractor(), FIDisclosureQualityAggregator(), e, c, "disclosure_quality_score", 75)

@register_inference_function("fi_security_page_basefunction")
def f45(e, c): return _run_pipeline("security_page", FISecurityPageExtractor(), FISecurityPageAggregator(), e, c, "security_page_score", 40)

@register_inference_function("fi_hiring_signals_basefunction")
def f46(e, c): return _run_pipeline("hiring_signals", FIHiringSignalsExtractor(), FIHiringSignalsAggregator(), e, c, "hiring_signals_score", 50)

@register_inference_function("fi_esg_reporting_basefunction")
def f47(e, c): return _run_pipeline("esg_reporting", FIESGReportingExtractor(), FIESGReportingAggregator(), e, c, "esg_reporting_score", 40)

@register_inference_function("community_presence_basefunction")
def f48(e, c): return _run_pipeline("community_presence", CommunityPresenceExtractor(), CommunityPresenceAggregator(), e, c, "community_presence_score", 60)


# =============================================================================
# STRUCTURED DATA (3)
# =============================================================================

@register_inference_function("fi_esg_rating_basefunction")
def f49(e, c): return _run_pipeline("esg_rating", FIESGRatingExtractor(), FIESGRatingAggregator(), e, c, "esg_rating_score", 50)

@register_inference_function("peer_benchmark_basefunction")
def f50(e, c): return _run_pipeline("peer_benchmark", PeerBenchmarkExtractor(), PeerBenchmarkAggregator(), e, c, "peer_benchmark_score", 50)

# Note: credit_rating_structured uses same as credit_rating in network_authority
@register_inference_function("fi_credit_rating_structured_basefunction")
def f51(e, c): return _run_pipeline("credit_rating_structured", FICreditRatingExtractor(), FICreditRatingAggregator(), e, c, "credit_rating_score", 50)