"""
PI Aggregators - All Signal Groups

Production-ready aggregators for Professional Indemnity coverage signals.
"""

from typing import Any, Dict, List
from ...base import ProductionAggregator
from ....types import AggregatorResult, ExtractorResult


# =============================================================================
# NETWORK AUTHORITY AGGREGATORS
# =============================================================================

class PeerRankingAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        count = raw.get("rankings_count", 0)
        top_tier = raw.get("top_tier_rankings", 0)
        score = min(100, 30 + count * 15 + top_tier * 10)
        return self._create_success_result({"peer_ranking_score": score, "rankings_count": count}, extractor_results)


class ClientQualityAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        score = 40
        if raw.get("fortune_500_clients"): score += 25
        if raw.get("public_company_clients"): score += 15
        if raw.get("government_clients"): score += 10
        score += raw.get("institutional_clients_pct", 0) * 0.1
        return self._create_success_result({"client_quality_score": min(100, score)}, extractor_results)


class ReferralQualityAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        score = raw.get("referral_quality_score", 60)
        if raw.get("reciprocal_referrals"): score += 10
        return self._create_success_result({"referral_network_score": min(100, score)}, extractor_results)


class AssociationLeadershipAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        memberships = raw.get("association_memberships", 0)
        leadership = raw.get("leadership_positions", 0)
        score = min(100, 30 + memberships * 8 + leadership * 15)
        return self._create_success_result({"association_leadership_score": score}, extractor_results)


class ThoughtLeadershipAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        pubs = raw.get("publications_count", 0)
        speaking = raw.get("speaking_engagements_yr", 0)
        cle = raw.get("cle_presentations", 0)
        score = min(100, 30 + min(30, pubs) + speaking * 2 + cle * 3)
        return self._create_success_result({"thought_leadership_score": score}, extractor_results)


class PanelMembershipAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        panels = raw.get("panel_memberships", 0)
        preferred = raw.get("preferred_counsel_status", False)
        score = min(100, 40 + panels * 15 + (20 if preferred else 0))
        return self._create_success_result({"panel_membership_score": score}, extractor_results)


# =============================================================================
# REGULATORY STANDING AGGREGATORS
# =============================================================================

class LicenseStatusAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        status = raw.get("license_status", "active")
        scores = {"active": 100, "inactive": 40, "probation": 30, "suspended": 10}
        score = scores.get(status, 50)
        if raw.get("license_restrictions"): score -= 15
        warnings = [f"License status: {status}"] if status != "active" else []
        return self._create_success_result({"license_status_score": max(0, score), "warnings": warnings}, extractor_results)


class DisciplinaryHistoryAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw.get("has_disciplinary_history"): return self._create_success_result({"disciplinary_history_score": 100}, extractor_results)
        sanctions = raw.get("sanctions_count", 0)
        suspensions = raw.get("suspensions", 0)
        severity = raw.get("severity", "minor")
        score = 70 - sanctions * 10 - suspensions * 25
        if severity == "serious": score -= 20
        warnings = [f"Disciplinary history: {sanctions} sanctions"]
        return self._create_success_result({"disciplinary_history_score": max(0, score), "warnings": warnings}, extractor_results)


class MalpracticeRecordAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw.get("has_malpractice_record"): return self._create_success_result({"malpractice_record_score": 100}, extractor_results)
        judgments = raw.get("public_judgments", 0)
        settlements = raw.get("disclosed_settlements", 0)
        score = 80 - judgments * 25 - settlements * 10
        warnings = ["Malpractice record on file"]
        return self._create_success_result({"malpractice_record_score": max(0, score), "warnings": warnings}, extractor_results)


class CEComplianceAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        compliant = raw.get("ce_compliant", True)
        streak = raw.get("compliance_streak_years", 0)
        score = 95 if compliant else 40
        score += min(5, streak // 3)
        return self._create_success_result({"ce_compliance_score": min(100, score)}, extractor_results)


class SpecialtyCertificationAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        count = raw.get("certification_count", 0)
        board = raw.get("board_certified", False)
        score = min(100, 40 + count * 15 + (25 if board else 0))
        return self._create_success_result({"specialty_certification_score": score}, extractor_results)


class PeerReviewAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        rating = raw.get("peer_review_rating", "not_applicable")
        scores = {"pass": 95, "pass_with_deficiencies": 60, "fail": 15, "not_applicable": 70}
        score = scores.get(rating, 70)
        warnings = ["Peer review failed"] if rating == "fail" else []
        return self._create_success_result({"peer_review_score": score, "warnings": warnings}, extractor_results)


class PCAOBStandingAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw.get("pcaob_registered"): return self._create_success_result({"pcaob_standing_score": 70}, extractor_results)
        deficiencies = raw.get("inspection_deficiencies", 0)
        enforcement = raw.get("enforcement_actions", 0)
        score = 90 - deficiencies * 5 - enforcement * 30
        return self._create_success_result({"pcaob_standing_score": max(0, score)}, extractor_results)


# =============================================================================
# FIRM STABILITY AGGREGATORS
# =============================================================================

class YearsInPracticeAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        years = raw.get("years_established", 1)
        if years >= 25: score = 95
        elif years >= 15: score = 85
        elif years >= 10: score = 75
        elif years >= 5: score = 60
        else: score = 45
        if not raw.get("continuous_operation"): score -= 10
        return self._create_success_result({"years_in_practice_score": max(0, score), "years": years}, extractor_results)


class PartnerStabilityAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        turnover = raw.get("turnover_rate", 10)
        tenure = raw.get("avg_partner_tenure_years", 5)
        score = 80 - turnover * 2 + min(20, tenure)
        if raw.get("founding_partners_remaining"): score += 5
        warnings = ["High partner turnover"] if turnover > 20 else []
        return self._create_success_result({"partner_stability_score": max(0, min(100, score)), "warnings": warnings}, extractor_results)


class StaffRetentionAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        turnover = raw.get("turnover_rate_pct", 20)
        glassdoor = raw.get("glassdoor_rating", 3.5)
        score = 80 - turnover + glassdoor * 5
        return self._create_success_result({"staff_retention_score": max(0, min(100, score))}, extractor_results)


class OfficeStabilityAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        primary_years = raw.get("primary_office_years", 5)
        changes = raw.get("office_changes_5yr", 0)
        score = min(100, 60 + primary_years * 2 - changes * 10)
        if raw.get("virtual_only"): score -= 10
        return self._create_success_result({"office_stability_score": max(0, score)}, extractor_results)


class PIFinancialStabilityAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        credit = raw.get("credit_score_proxy", "good")
        scores = {"excellent": 95, "good": 80, "fair": 55, "poor": 30}
        score = scores.get(credit, 60)
        if raw.get("bankruptcy_history"): score -= 25
        if raw.get("tax_liens"): score -= 15
        score -= raw.get("liens_judgments", 0) * 8
        warnings = ["Financial stability concerns"] if score < 50 else []
        return self._create_success_result({"financial_stability_score": max(0, score), "warnings": warnings}, extractor_results)


class SuccessionPlanningAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        score = 50
        if raw.get("visible_succession_plan"): score += 25
        if raw.get("next_gen_partners", 0) > 0: score += 15
        if raw.get("partnership_track_visible"): score += 10
        return self._create_success_result({"succession_planning_score": min(100, score)}, extractor_results)


# =============================================================================
# PRACTICE QUALITY AGGREGATORS
# =============================================================================

class OutcomePatternsAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        win_rate = raw.get("case_win_rate", 65)
        completion = raw.get("transaction_completion_rate", 90)
        score = win_rate * 0.5 + completion * 0.5
        return self._create_success_result({"outcome_patterns_score": min(100, score)}, extractor_results)


class ClientReviewsAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        rating = raw.get("average_rating", 3.5)
        review_count = raw.get("review_count", 10)
        score = rating * 18 + min(10, review_count / 10)
        return self._create_success_result({"client_reviews_score": min(100, score)}, extractor_results)


class WorkQualityAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        sanctions = raw.get("sanctions_for_work_quality", 0)
        awards = raw.get("quality_awards", 0)
        score = 70 - sanctions * 20 + awards * 8
        if raw.get("pro_bono_recognition"): score += 5
        return self._create_success_result({"work_quality_score": max(0, min(100, score))}, extractor_results)


class FeeDisputeAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw.get("has_fee_disputes"): return self._create_success_result({"fee_dispute_score": 95}, extractor_results)
        arbitrations = raw.get("arbitration_filings_5yr", 0)
        suits = raw.get("fee_suits_filed", 0) + raw.get("fee_suits_against", 0)
        score = 70 - arbitrations * 5 - suits * 10
        return self._create_success_result({"fee_dispute_score": max(0, score)}, extractor_results)


class ComplaintHistoryAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw.get("has_complaint_history"): return self._create_success_result({"complaint_history_score": 100}, extractor_results)
        substantiated = raw.get("complaints_substantiated", 0)
        pending = raw.get("pending_complaints", 0)
        score = 70 - substantiated * 15 - pending * 10
        return self._create_success_result({"complaint_history_score": max(0, score)}, extractor_results)


# =============================================================================
# TECHNICAL INFRASTRUCTURE AGGREGATORS
# =============================================================================

class PITLSScoreAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        grade = raw.get("ssl_labs_grade", "B")
        scores = {"A+": 100, "A": 90, "A-": 80, "B": 65, "C": 45, "F": 15}
        return self._create_success_result({"tls_score": scores.get(grade, 50)}, extractor_results)


class PIEmailAuthAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        score = 30
        if raw.get("spf_configured"): score += 20
        if raw.get("dkim_configured"): score += 20
        if raw.get("dmarc_configured"): score += 20
        if raw.get("dmarc_policy") == "reject": score += 10
        return self._create_success_result({"email_auth_score": min(100, score)}, extractor_results)


class PISecurityHeadersAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        grade = raw.get("headers_grade", "C")
        scores = {"A": 95, "B": 75, "C": 55, "D": 35, "F": 15}
        return self._create_success_result({"security_headers_score": scores.get(grade, 55)}, extractor_results)


class PortalSecurityAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw.get("has_client_portal"): return self._create_success_result({"portal_security_score": 60}, extractor_results)
        score = 50
        if raw.get("mfa_required"): score += 25
        elif raw.get("mfa_available"): score += 15
        if raw.get("encryption_at_rest"): score += 15
        return self._create_success_result({"portal_security_score": min(100, score)}, extractor_results)


class PIBreachHistoryAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw.get("has_breach_history"): return self._create_success_result({"breach_history_score": 100}, extractor_results)
        count = raw.get("breach_count_5yr", 0)
        client_data = raw.get("client_data_exposed", False)
        score = 50 - count * 20 - (20 if client_data else 0)
        warnings = ["Data breach history"]
        return self._create_success_result({"breach_history_score": max(0, score), "warnings": warnings}, extractor_results)


# =============================================================================
# CORPORATE FOOTPRINT AGGREGATORS
# =============================================================================

class PIWebsiteQualityAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        quality = raw.get("website_quality", "adequate")
        scores = {"professional": 90, "adequate": 70, "basic": 50, "minimal": 30, "none": 10}
        score = scores.get(quality, 50)
        if raw.get("mobile_responsive"): score += 5
        if raw.get("blog_active"): score += 5
        return self._create_success_result({"website_quality_score": min(100, score)}, extractor_results)


class BioCompletenessAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw.get("bios_present"): return self._create_success_result({"bio_completeness_score": 30}, extractor_results)
        completeness = raw.get("bio_completeness_pct", 60)
        score = completeness * 0.7 + 20
        if raw.get("headshots_professional"): score += 10
        return self._create_success_result({"bio_completeness_score": min(100, score)}, extractor_results)


class PracticeClarityAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        score = 40
        if raw.get("practice_areas_defined"): score += 25
        if raw.get("service_descriptions"): score += 15
        if raw.get("industry_focus_clear"): score += 10
        if raw.get("case_studies"): score += 10
        return self._create_success_result({"practice_clarity_score": min(100, score)}, extractor_results)


class PublicationsAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        posts = raw.get("blog_posts_yr", 0)
        articles = raw.get("articles_published", 0)
        webinars = raw.get("webinars_yr", 0)
        score = min(100, 30 + min(25, posts) + articles * 2 + webinars * 3)
        return self._create_success_result({"publications_score": score}, extractor_results)


class CommunityInvolvementAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        score = 30
        if raw.get("pro_bono_program"): score += 25
        if raw.get("legal_aid_partnership"): score += 15
        score += raw.get("nonprofit_board_service", 0) * 5
        if raw.get("charitable_foundation"): score += 15
        return self._create_success_result({"community_involvement_score": min(100, score)}, extractor_results)


class DiversityAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        score = 30
        if raw.get("diversity_statement"): score += 15
        if raw.get("diversity_committee"): score += 15
        if raw.get("mansfield_certified"): score += 20
        score += raw.get("diversity_awards", 0) * 8
        return self._create_success_result({"diversity_score": min(100, score)}, extractor_results)


# =============================================================================
# LITIGATION HISTORY AGGREGATORS
# =============================================================================

class MalpracticeSuitsAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw.get("has_malpractice_suits"): return self._create_success_result({"malpractice_suits_score": 100}, extractor_results)
        active = raw.get("active_suits", 0)
        judgments = raw.get("judgments_against", 0)
        score = 60 - active * 20 - judgments * 25
        warnings = ["Active malpractice suits"] if active > 0 else []
        return self._create_success_result({"malpractice_suits_score": max(0, score), "warnings": warnings}, extractor_results)


class FeeDisputesLitigationAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw.get("has_fee_litigation"): return self._create_success_result({"fee_disputes_litigation_score": 95}, extractor_results)
        suits = raw.get("fee_suits_5yr", 0)
        arbs = raw.get("arbitrations_5yr", 0)
        score = 70 - suits * 10 - arbs * 5
        return self._create_success_result({"fee_disputes_litigation_score": max(0, score)}, extractor_results)


class PIRegulatoryEnforcementAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw.get("has_enforcement_history"): return self._create_success_result({"regulatory_enforcement_score": 100}, extractor_results)
        actions = raw.get("enforcement_actions_5yr", 0)
        active_inv = raw.get("active_investigations", 0)
        score = 50 - actions * 15 - active_inv * 25
        warnings = ["Regulatory enforcement history"]
        return self._create_success_result({"regulatory_enforcement_score": max(0, score), "warnings": warnings}, extractor_results)


class CivilLitigationAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw.get("has_civil_litigation"): return self._create_success_result({"civil_litigation_score": 95}, extractor_results)
        suits = raw.get("civil_suits_5yr", 0)
        pending = raw.get("pending_suits", 0)
        score = 75 - suits * 5 - pending * 10
        return self._create_success_result({"civil_litigation_score": max(0, score)}, extractor_results)


class BankruptcyAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw.get("has_bankruptcy_history"): return self._create_success_result({"bankruptcy_score": 100}, extractor_results)
        current = raw.get("current_bankruptcy", False)
        years = raw.get("years_since_discharge", 10)
        score = 20 if current else min(80, 40 + years * 5)
        warnings = ["Bankruptcy history"]
        return self._create_success_result({"bankruptcy_score": score, "warnings": warnings}, extractor_results)


# =============================================================================
# CATEGORICAL AGGREGATORS
# =============================================================================

class ProfessionClassificationAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        return self._create_success_result({"profession_type": raw.get("profession_type", "OTHER")}, extractor_results)


class FirmSizeAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        return self._create_success_result({"firm_size": raw.get("firm_size", "SMALL"), "professional_count": raw.get("professional_count", 10)}, extractor_results)


class AnnualRevenueAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        return self._create_success_result({"revenue_size": raw.get("revenue_size", "R_1M_5M")}, extractor_results)
