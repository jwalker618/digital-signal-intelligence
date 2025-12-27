"""
PI Inference Functions - All Signal Groups

Maps YAML inference_utility_function names to pipeline orchestration.
40 signals + 3 categorical = 43 total functions
"""

import time
from ....types import SignalResult, InferenceContext
from ....inference.registry import register_inference_function

from ....extractors.stubs.pi import (
    # Network Authority
    PeerRankingExtractor, ClientQualityExtractor, ReferralQualityExtractor,
    AssociationLeadershipExtractor, ThoughtLeadershipExtractor, PanelMembershipExtractor,
    # Regulatory Standing
    LicenseStatusExtractor, DisciplinaryHistoryExtractor, MalpracticeRecordExtractor,
    CEComplianceExtractor, SpecialtyCertificationExtractor, PeerReviewExtractor, PCAOBStandingExtractor,
    # Firm Stability
    YearsInPracticeExtractor, PartnerStabilityExtractor, StaffRetentionExtractor,
    OfficeStabilityExtractor, PIFinancialStabilityExtractor, SuccessionPlanningExtractor,
    # Practice Quality
    OutcomePatternsExtractor, ClientReviewsExtractor, WorkQualityExtractor,
    FeeDisputeExtractor, ComplaintHistoryExtractor,
    # Technical Infrastructure
    PITLSScoreExtractor, PIEmailAuthExtractor, PISecurityHeadersExtractor,
    PortalSecurityExtractor, PIBreachHistoryExtractor,
    # Corporate Footprint
    PIWebsiteQualityExtractor, BioCompletenessExtractor, PracticeClarityExtractor,
    PublicationsExtractor, CommunityInvolvementExtractor, DiversityExtractor,
    # Litigation History
    MalpracticeSuitsExtractor, FeeDisputesLitigationExtractor, RegulatoryEnforcementExtractor,
    CivilLitigationExtractor, BankruptcyExtractor,
    # Categorical
    ProfessionClassificationExtractor, FirmSizeExtractor, AnnualRevenueExtractor,
)

from ....aggregators.implementations.pi import (
    # Network Authority
    PeerRankingAggregator, ClientQualityAggregator, ReferralQualityAggregator,
    AssociationLeadershipAggregator, ThoughtLeadershipAggregator, PanelMembershipAggregator,
    # Regulatory Standing
    LicenseStatusAggregator, DisciplinaryHistoryAggregator, MalpracticeRecordAggregator,
    CEComplianceAggregator, SpecialtyCertificationAggregator, PeerReviewAggregator, PCAOBStandingAggregator,
    # Firm Stability
    YearsInPracticeAggregator, PartnerStabilityAggregator, StaffRetentionAggregator,
    OfficeStabilityAggregator, PIFinancialStabilityAggregator, SuccessionPlanningAggregator,
    # Practice Quality
    OutcomePatternsAggregator, ClientReviewsAggregator, WorkQualityAggregator,
    FeeDisputeAggregator, ComplaintHistoryAggregator,
    # Technical Infrastructure
    PITLSScoreAggregator, PIEmailAuthAggregator, PISecurityHeadersAggregator,
    PortalSecurityAggregator, PIBreachHistoryAggregator,
    # Corporate Footprint
    PIWebsiteQualityAggregator, BioCompletenessAggregator, PracticeClarityAggregator,
    PublicationsAggregator, CommunityInvolvementAggregator, DiversityAggregator,
    # Litigation History
    MalpracticeSuitsAggregator, FeeDisputesLitigationAggregator, PIRegulatoryEnforcementAggregator,
    CivilLitigationAggregator, BankruptcyAggregator,
    # Categorical
    ProfessionClassificationAggregator, FirmSizeAggregator, AnnualRevenueAggregator,
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
# CATEGORICAL (3)
# =============================================================================

@register_inference_function("primaryprofessional_classification_basefunction")
def f1(e, c): return _run_categorical("profession_type", ProfessionClassificationExtractor(), ProfessionClassificationAggregator(), e, c, "profession_type", "OTHER")

@register_inference_function("firm_size_basefunction")
def f2(e, c): return _run_categorical("firm_size", FirmSizeExtractor(), FirmSizeAggregator(), e, c, "firm_size", "SMALL")

@register_inference_function("annualrevenue_classification_basefunction")
def f3(e, c): return _run_categorical("revenue_size", AnnualRevenueExtractor(), AnnualRevenueAggregator(), e, c, "revenue_size", "R_1M_5M")


# =============================================================================
# NETWORK AUTHORITY (6)
# =============================================================================

@register_inference_function("peer_ranking_basefunction")
def f4(e, c): return _run_pipeline("peer_ranking", PeerRankingExtractor(), PeerRankingAggregator(), e, c, "peer_ranking_score", 50)

@register_inference_function("client_quality_basefunction")
def f5(e, c): return _run_pipeline("client_quality", ClientQualityExtractor(), ClientQualityAggregator(), e, c, "client_quality_score", 50)

@register_inference_function("referral_quality_basefunction")
def f6(e, c): return _run_pipeline("referral_network", ReferralQualityExtractor(), ReferralQualityAggregator(), e, c, "referral_network_score", 50)

@register_inference_function("association_leadership_basefunction")
def f7(e, c): return _run_pipeline("association_leadership", AssociationLeadershipExtractor(), AssociationLeadershipAggregator(), e, c, "association_leadership_score", 40)

@register_inference_function("thought_leadership_basefunction")
def f8(e, c): return _run_pipeline("thought_leadership", ThoughtLeadershipExtractor(), ThoughtLeadershipAggregator(), e, c, "thought_leadership_score", 40)

@register_inference_function("panel_membership_basefunction")
def f9(e, c): return _run_pipeline("panel_membership", PanelMembershipExtractor(), PanelMembershipAggregator(), e, c, "panel_membership_score", 40)


# =============================================================================
# REGULATORY STANDING (7)
# =============================================================================

@register_inference_function("license_status_basefunction")
def f10(e, c): return _run_pipeline("license_status", LicenseStatusExtractor(), LicenseStatusAggregator(), e, c, "license_status_score", 100)

@register_inference_function("disciplianry_history_basefunction")
def f11(e, c): return _run_pipeline("disciplinary_history", DisciplinaryHistoryExtractor(), DisciplinaryHistoryAggregator(), e, c, "disciplinary_history_score", 100)

@register_inference_function("malpractice_record_basefunction")
def f12(e, c): return _run_pipeline("malpractice_record", MalpracticeRecordExtractor(), MalpracticeRecordAggregator(), e, c, "malpractice_record_score", 100)

@register_inference_function("ce_compliance_basefunction")
def f13(e, c): return _run_pipeline("ce_compliance", CEComplianceExtractor(), CEComplianceAggregator(), e, c, "ce_compliance_score", 90)

@register_inference_function("speciality_certifications_basefunction")
def f14(e, c): return _run_pipeline("specialty_certification", SpecialtyCertificationExtractor(), SpecialtyCertificationAggregator(), e, c, "specialty_certification_score", 50)

@register_inference_function("peer_review_basefunction")
def f15(e, c): return _run_pipeline("peer_review", PeerReviewExtractor(), PeerReviewAggregator(), e, c, "peer_review_score", 70)

@register_inference_function("pcaob_standing_basefunction")
def f16(e, c): return _run_pipeline("pcaob_standing", PCAOBStandingExtractor(), PCAOBStandingAggregator(), e, c, "pcaob_standing_score", 70)


# =============================================================================
# FIRM STABILITY (6)
# =============================================================================

@register_inference_function("years_inpractice_basefunction")
def f17(e, c): return _run_pipeline("tenure", YearsInPracticeExtractor(), YearsInPracticeAggregator(), e, c, "years_in_practice_score", 60)

@register_inference_function("partner_stability_basefunction")
def f18(e, c): return _run_pipeline("partner_stability", PartnerStabilityExtractor(), PartnerStabilityAggregator(), e, c, "partner_stability_score", 70)

@register_inference_function("staff_retention_basefunction")
def f19(e, c): return _run_pipeline("staff_retention", StaffRetentionExtractor(), StaffRetentionAggregator(), e, c, "staff_retention_score", 65)

@register_inference_function("office_stability_basefunction")
def f20(e, c): return _run_pipeline("office_stability", OfficeStabilityExtractor(), OfficeStabilityAggregator(), e, c, "office_stability_score", 70)

@register_inference_function("financial_stability_basefunction")
def f21(e, c): return _run_pipeline("financial_stability", PIFinancialStabilityExtractor(), PIFinancialStabilityAggregator(), e, c, "financial_stability_score", 70)

@register_inference_function("succession_planning_basefunction")
def f22(e, c): return _run_pipeline("succession_planning", SuccessionPlanningExtractor(), SuccessionPlanningAggregator(), e, c, "succession_planning_score", 50)


# =============================================================================
# PRACTICE QUALITY (5)
# =============================================================================

@register_inference_function("outcome_patterns_basefunction")
def f23(e, c): return _run_pipeline("outcome_patterns", OutcomePatternsExtractor(), OutcomePatternsAggregator(), e, c, "outcome_patterns_score", 70)

@register_inference_function("client_reviews_basefunction")
def f24(e, c): return _run_pipeline("client_reviews", ClientReviewsExtractor(), ClientReviewsAggregator(), e, c, "client_reviews_score", 70)

@register_inference_function("work_quality_basefunction")
def f25(e, c): return _run_pipeline("work_quality", WorkQualityExtractor(), WorkQualityAggregator(), e, c, "work_quality_score", 70)

@register_inference_function("fee_dispute_basefunction")
def f26(e, c): return _run_pipeline("fee_dispute", FeeDisputeExtractor(), FeeDisputeAggregator(), e, c, "fee_dispute_score", 90)

@register_inference_function("complaint_history_basefunction")
def f27(e, c): return _run_pipeline("complaint_history", ComplaintHistoryExtractor(), ComplaintHistoryAggregator(), e, c, "complaint_history_score", 100)


# =============================================================================
# TECHNICAL INFRASTRUCTURE (5)
# =============================================================================

@register_inference_function("tls_score_basefunction")
def f28(e, c): return _run_pipeline("tls_score", PITLSScoreExtractor(), PITLSScoreAggregator(), e, c, "tls_score", 65)

@register_inference_function("email_authentication_basefunction")
def f29(e, c): return _run_pipeline("email_auth", PIEmailAuthExtractor(), PIEmailAuthAggregator(), e, c, "email_auth_score", 50)

@register_inference_function("security_headers_basefunction")
def f30(e, c): return _run_pipeline("security_headers", PISecurityHeadersExtractor(), PISecurityHeadersAggregator(), e, c, "security_headers_score", 55)

@register_inference_function("portal_security_basefunction")
def f31(e, c): return _run_pipeline("portal_security", PortalSecurityExtractor(), PortalSecurityAggregator(), e, c, "portal_security_score", 60)

@register_inference_function("breach_history_basefunction")
def f32(e, c): return _run_pipeline("breach_history", PIBreachHistoryExtractor(), PIBreachHistoryAggregator(), e, c, "breach_history_score", 100)


# =============================================================================
# CORPORATE FOOTPRINT (6)
# =============================================================================

@register_inference_function("website_quality_basefunction")
def f33(e, c): return _run_pipeline("website_quality", PIWebsiteQualityExtractor(), PIWebsiteQualityAggregator(), e, c, "website_quality_score", 60)

@register_inference_function("bio_completness_basefunction")
def f34(e, c): return _run_pipeline("bio_completeness", BioCompletenessExtractor(), BioCompletenessAggregator(), e, c, "bio_completeness_score", 60)

@register_inference_function("practice_clarity_basefunction")
def f35(e, c): return _run_pipeline("practice_clarity", PracticeClarityExtractor(), PracticeClarityAggregator(), e, c, "practice_clarity_score", 60)

@register_inference_function("publications_basefunction")
def f36(e, c): return _run_pipeline("publications", PublicationsExtractor(), PublicationsAggregator(), e, c, "publications_score", 40)

@register_inference_function("community_involvement_basefunction")
def f37(e, c): return _run_pipeline("community_involvement", CommunityInvolvementExtractor(), CommunityInvolvementAggregator(), e, c, "community_involvement_score", 50)

@register_inference_function("diversity_basefunction")
def f38(e, c): return _run_pipeline("diversity", DiversityExtractor(), DiversityAggregator(), e, c, "diversity_score", 40)


# =============================================================================
# LITIGATION HISTORY (5)
# =============================================================================

@register_inference_function("malpractice_suits_basefunction")
def f39(e, c): return _run_pipeline("malpractice_suits", MalpracticeSuitsExtractor(), MalpracticeSuitsAggregator(), e, c, "malpractice_suits_score", 100)

@register_inference_function("fee_disputes_basefunction")
def f40(e, c): return _run_pipeline("fee_disputes_litigation", FeeDisputesLitigationExtractor(), FeeDisputesLitigationAggregator(), e, c, "fee_disputes_litigation_score", 95)

@register_inference_function("regulatory_enforcement_basefunction")
def f41(e, c): return _run_pipeline("regulatory_enforcement", RegulatoryEnforcementExtractor(), PIRegulatoryEnforcementAggregator(), e, c, "regulatory_enforcement_score", 100)

@register_inference_function("civil_litigation_basefunction")
def f42(e, c): return _run_pipeline("civil_litigation", CivilLitigationExtractor(), CivilLitigationAggregator(), e, c, "civil_litigation_score", 95)

@register_inference_function("bankruptcy_basefunction")
def f43(e, c): return _run_pipeline("bankruptcy", BankruptcyExtractor(), BankruptcyAggregator(), e, c, "bankruptcy_score", 100)
