"""
FI Aggregators - All Signal Groups

Production-ready aggregators for Financial Institutions coverage signals.
"""

from typing import Any, Dict, List
from datetime import datetime

from ...base import ProductionAggregator
from ....types import AggregatorResult, ExtractorResult


# =============================================================================
# NETWORK AUTHORITY AGGREGATORS
# =============================================================================

class CorrespondentQualityAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        tier = data.get("correspondent_tier", 3)
        years = data.get("relationship_years", 0)
        tier_scores = {1: 90, 2: 70, 3: 50}
        score = tier_scores.get(tier, 50) + min(10, years // 3)
        return AggregatorResult(success=True, data={"correspondent_quality_score": min(100, score), "correspondent_tier": tier})


class FHLBMembershipAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        is_member = data.get("is_member", False)
        years = data.get("membership_years", 0)
        score = min(100, 70 + (years // 5) * 5) if is_member else 30
        return AggregatorResult(success=True, data={"fhlb_membership_score": score, "is_member": is_member})


class ClearingRelationshipAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        tier = data.get("clearing_tier", 3)
        tier_scores = {1: 90, 2: 70, 3: 50}
        score = tier_scores.get(tier, 50)
        if data.get("fed_member"): score += 5
        if data.get("dtc_participant"): score += 5
        return AggregatorResult(success=True, data={"clearing_relationship_score": min(100, score), "clearing_tier": tier})


class FIAuditorQualityAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        tier = data.get("auditor_tier", 4)
        tier_scores = {1: 95, 2: 80, 3: 65, 4: 45}
        score = tier_scores.get(tier, 45)
        if data.get("material_weakness_disclosed"): score -= 20
        if data.get("auditor_change_recent"): score -= 10
        warnings = ["Material weakness disclosed"] if data.get("material_weakness_disclosed") else []
        return AggregatorResult(success=True, data={"auditor_quality_score": max(0, score), "auditor_tier": tier, "warnings": warnings})


class LegalCounselAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        tier = data.get("counsel_tier", 4)
        tier_scores = {1: 95, 2: 80, 3: 65, 4: 45}
        score = tier_scores.get(tier, 45)
        if data.get("banking_specialty"): score += 10
        return AggregatorResult(success=True, data={"legal_counsel_score": min(100, score), "counsel_tier": tier})


class FIIndustryAssociationAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        count = data.get("membership_count", 0)
        leadership = data.get("leadership_roles", 0)
        score = min(100, 40 + count * 15 + leadership * 10)
        return AggregatorResult(success=True, data={"industry_association_score": score, "membership_count": count})


class FICreditRatingAggregator(ProductionAggregator):
    SCORES = {"AAA": 100, "Aaa": 100, "AA+": 95, "Aa1": 95, "AA": 90, "Aa2": 90, "AA-": 85, "Aa3": 85,
              "A+": 80, "A1": 80, "A": 75, "A2": 75, "A-": 70, "A3": 70, "BBB+": 65, "Baa1": 65,
              "BBB": 60, "Baa2": 60, "BBB-": 55, "Baa3": 55, "BB+": 45, "Ba1": 45, "BB": 40, "Ba2": 40,
              "BB-": 35, "Ba3": 35, "B+": 30, "B1": 30, "B": 25, "B2": 25, "NR": 50}
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        moodys = self.SCORES.get(data.get("moodys_rating", "NR"), 50)
        sp = self.SCORES.get(data.get("sp_rating", "NR"), 50)
        return AggregatorResult(success=True, data={"credit_rating_score": round((moodys + sp) / 2, 1), "is_investment_grade": data.get("is_investment_grade", False)})


# =============================================================================
# REGULATORY COMPLIANCE AGGREGATORS
# =============================================================================

class ExaminationRatingAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        composite = data.get("inferred_composite", 3)
        scores = {1: 95, 2: 80, 3: 60, 4: 35, 5: 15}
        warnings = [f"Weak examination indicators (composite {composite})"] if composite >= 4 else []
        return AggregatorResult(success=True, data={"examination_rating_score": scores.get(composite, 60), "inferred_composite": composite, "warnings": warnings})


class EnforcementActionAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        has_action = data.get("has_enforcement_action", False)
        active = data.get("active_actions", 0)
        score = 100 if not has_action else max(0, 30 - active * 10) if active > 0 else 60
        warnings = [f"Active enforcement actions: {active}"] if active > 0 else []
        return AggregatorResult(success=True, data={"enforcement_action_score": score, "has_enforcement_action": has_action, "warnings": warnings})


class InformalActionAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        has_informal = data.get("has_informal_action", False)
        mras = data.get("matters_requiring_attention", 0)
        mrias = data.get("matters_requiring_immediate_attention", 0)
        score = 100 if not has_informal else max(30, 80 - mras * 5 - mrias * 15)
        return AggregatorResult(success=True, data={"informal_action_score": score, "has_informal_action": has_informal})


class CRARatingAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        rating = data.get("cra_rating", "Satisfactory")
        scores = {"Outstanding": 100, "Satisfactory": 75, "Needs to Improve": 35, "Substantial Noncompliance": 10}
        return AggregatorResult(success=True, data={"cra_rating_score": scores.get(rating, 75), "cra_rating": rating})


class BSAAMLAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        program = data.get("bsa_compliance_program", "satisfactory")
        has_enforcement = data.get("has_bsa_enforcement", False)
        program_scores = {"strong": 95, "satisfactory": 75, "needs_improvement": 45, "deficient": 20}
        score = program_scores.get(program, 75)
        if has_enforcement: score = min(score, 25)
        warnings = ["BSA/AML enforcement action"] if has_enforcement else []
        return AggregatorResult(success=True, data={"bsa_aml_score": score, "has_enforcement": has_enforcement, "warnings": warnings})


class FairLendingAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        result = data.get("fair_lending_exam_result", "satisfactory")
        scores = {"satisfactory": 85, "needs_attention": 50, "violation": 20}
        score = scores.get(result, 85)
        if data.get("doj_referral"): score = min(score, 15)
        return AggregatorResult(success=True, data={"fair_lending_score": score, "exam_result": result})


class ConsumerComplianceAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        rating = data.get("consumer_compliance_rating", 2)
        scores = {1: 95, 2: 80, 3: 60, 4: 35, 5: 15}
        violations = data.get("udaap_violations", 0) + data.get("tila_violations", 0)
        score = max(0, scores.get(rating, 60) - violations * 10)
        return AggregatorResult(success=True, data={"consumer_compliance_score": score, "rating": rating})


# =============================================================================
# FINANCIAL CONDITION AGGREGATORS
# =============================================================================

class CapitalRatioAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        cet1 = data.get("cet1_ratio", 10)
        category = data.get("capital_category", "well_capitalized")
        if category == "well_capitalized": score = min(100, 70 + (cet1 - 6.5) * 3)
        elif category == "adequately_capitalized": score = 55
        elif category == "undercapitalized": score = 25
        else: score = 10
        warnings = [f"Capital category: {category}"] if category != "well_capitalized" else []
        return AggregatorResult(success=True, data={"capital_ratio_score": max(0, min(100, score)), "cet1_ratio": cet1, "category": category, "warnings": warnings})


class AssetQualityAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        npl = data.get("npl_ratio", 1.5)
        texas = data.get("texas_ratio", 20)
        score = 100 - npl * 15 - max(0, texas - 20) * 0.5
        warnings = [f"Elevated NPL ratio: {npl}%"] if npl > 3 else []
        if texas > 50: warnings.append(f"High Texas ratio: {texas}")
        return AggregatorResult(success=True, data={"asset_quality_score": max(0, min(100, score)), "npl_ratio": npl, "warnings": warnings})


class LiquidityAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        ltd = data.get("loan_to_deposit_ratio", 80)
        core = data.get("core_deposits_ratio", 70)
        score = 70 + (100 - ltd) * 0.3 + (core - 50) * 0.4
        warnings = [f"High loan-to-deposit ratio: {ltd}%"] if ltd > 95 else []
        return AggregatorResult(success=True, data={"liquidity_score": max(0, min(100, score)), "loan_to_deposit": ltd, "warnings": warnings})


class EarningsAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        roa = data.get("roa", 1.0)
        efficiency = data.get("efficiency_ratio", 65)
        score = 50 + roa * 30 - max(0, efficiency - 60) * 0.5
        return AggregatorResult(success=True, data={"earnings_score": max(0, min(100, score)), "roa": roa, "efficiency_ratio": efficiency})


class ConcentrationAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        cre = data.get("cre_concentration", 200)
        top10 = data.get("top_10_borrowers_pct", 30)
        score = 100 - max(0, cre - 100) * 0.15 - max(0, top10 - 25) * 1.5
        warnings = [f"High CRE concentration: {cre}% of capital"] if cre > 300 else []
        return AggregatorResult(success=True, data={"concentration_score": max(0, min(100, score)), "cre_concentration": cre, "warnings": warnings})


class InterestRateRiskAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        eve_sens = abs(data.get("eve_sensitivity_up200", -10))
        score = 100 - eve_sens * 2
        warnings = [f"High EVE sensitivity: {eve_sens}%"] if eve_sens > 15 else []
        return AggregatorResult(success=True, data={"interest_rate_risk_score": max(0, min(100, score)), "warnings": warnings})


class GrowthRateAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        growth = data.get("asset_growth_1yr", 5)
        rapid = data.get("rapid_growth_flag", False)
        score = 80 if 0 <= growth <= 15 else 60 if growth < 0 else 50
        warnings = ["Rapid growth flag (>20%)"] if rapid else []
        return AggregatorResult(success=True, data={"growth_rate_score": score, "asset_growth": growth, "warnings": warnings})


# =============================================================================
# GOVERNANCE AGGREGATORS
# =============================================================================

class FIBoardIndependenceAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        ratio = data.get("independence_ratio", 0.6)
        ind_chair = data.get("independent_chair", False)
        score = ratio * 80 + (20 if ind_chair else 0)
        return AggregatorResult(success=True, data={"board_independence_score": min(100, score), "independence_ratio": ratio})


class BoardExpertiseAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        banking = data.get("banking_experience_count", 2)
        risk = data.get("risk_management_experience", 1)
        audit = data.get("audit_financial_experts", 2)
        score = min(100, 40 + banking * 8 + risk * 10 + audit * 8)
        return AggregatorResult(success=True, data={"board_expertise_score": score, "banking_experience": banking})


class FIExecutiveStabilityAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        ceo_tenure = data.get("ceo_tenure_years", 5)
        turnover = data.get("c_suite_turnover_3yr", 1)
        score = min(100, 50 + ceo_tenure * 4 - turnover * 10)
        warnings = ["Recent CEO change"] if data.get("ceo_change_recent") else []
        return AggregatorResult(success=True, data={"executive_stability_score": max(0, score), "ceo_tenure": ceo_tenure, "warnings": warnings})


class RiskCommitteeAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        has_committee = data.get("has_risk_committee", False)
        if not has_committee: return AggregatorResult(success=True, data={"risk_committee_score": 30, "has_committee": False})
        score = 60
        if data.get("risk_committee_independent"): score += 15
        if data.get("risk_expert_chair"): score += 15
        if data.get("cro_reports_to_committee"): score += 10
        return AggregatorResult(success=True, data={"risk_committee_score": min(100, score), "has_committee": True})


class AuditCommitteeAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        experts = data.get("financial_experts", 1)
        all_ind = data.get("all_independent", False)
        meetings = data.get("meetings_per_year", 6)
        score = 50 + experts * 10 + (20 if all_ind else 0) + min(20, meetings * 2)
        return AggregatorResult(success=True, data={"audit_committee_score": min(100, score), "financial_experts": experts})


class RelatedPartyAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        has_rpt = data.get("related_party_transactions", False)
        policy = data.get("rpt_policy_exists", False)
        reg_o = data.get("reg_o_compliance", True)
        score = 90 if not has_rpt else 70 if policy and reg_o else 50
        warnings = ["Reg O compliance issues"] if not reg_o else []
        return AggregatorResult(success=True, data={"related_party_score": score, "warnings": warnings})


# =============================================================================
# OPERATIONAL RISK AGGREGATORS
# =============================================================================

class CFPBComplaintAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        percentile = data.get("peer_percentile", 50)
        trend = data.get("complaint_trend", "stable")
        score = 100 - percentile
        if trend == "increasing": score -= 10
        elif trend == "decreasing": score += 5
        return AggregatorResult(success=True, data={"cfpb_complaint_score": max(0, min(100, score)), "peer_percentile": percentile})


class BBBComplaintAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        rating = data.get("bbb_rating", "B")
        scores = {"A+": 100, "A": 90, "A-": 80, "B+": 70, "B": 60, "B-": 50, "C": 35, "NR": 50}
        return AggregatorResult(success=True, data={"bbb_complaint_score": scores.get(rating, 50), "bbb_rating": rating})


class FILitigationAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        material = data.get("material_litigation_pending", False)
        class_actions = data.get("class_actions_pending", 0)
        score = 100 if not material else max(20, 70 - class_actions * 15)
        warnings = [f"Class actions pending: {class_actions}"] if class_actions > 0 else []
        return AggregatorResult(success=True, data={"litigation_score": score, "material_pending": material, "warnings": warnings})


class FIBreachHistoryAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        has_breach = data.get("has_breach_history", False)
        count = data.get("breach_count_5yr", 0)
        score = 100 if not has_breach else max(20, 80 - count * 20)
        warnings = [f"Data breaches in past 5 years: {count}"] if count > 0 else []
        return AggregatorResult(success=True, data={"breach_history_score": score, "breach_count": count, "warnings": warnings})


class OperationalIncidentAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        incidents = data.get("operational_incidents_12mo", 0)
        significant = data.get("significant_outages", 0)
        score = max(0, 100 - incidents * 5 - significant * 15)
        return AggregatorResult(success=True, data={"operational_incident_score": score, "incidents_12mo": incidents})


# =============================================================================
# CYBER SECURITY AGGREGATORS
# =============================================================================

class FITLSConfigAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        grade = data.get("ssl_labs_grade", "B")
        scores = {"A+": 100, "A": 90, "A-": 80, "B": 65, "C": 45, "F": 15}
        return AggregatorResult(success=True, data={"tls_score": scores.get(grade, 50), "ssl_grade": grade})


class FIEmailAuthAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        score = 30
        if data.get("spf_configured"): score += 20
        if data.get("dkim_configured"): score += 20
        if data.get("dmarc_configured"): score += 20
        if data.get("dmarc_policy") == "reject": score += 10
        return AggregatorResult(success=True, data={"email_auth_score": min(100, score)})


class FISecurityHeadersAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        grade = data.get("headers_grade", "C")
        scores = {"A": 95, "B": 75, "C": 55, "D": 35, "F": 15}
        return AggregatorResult(success=True, data={"security_headers_score": scores.get(grade, 55)})


class FINetworkExposureAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        high_risk = data.get("high_risk_ports_exposed", 0)
        rdp = data.get("rdp_exposed", False)
        score = data.get("attack_surface_score", 70)
        if rdp: score -= 20
        score -= high_risk * 10
        warnings = ["RDP exposed to internet"] if rdp else []
        return AggregatorResult(success=True, data={"network_exposure_score": max(0, score), "warnings": warnings})


class FICVEExposureAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        critical = data.get("critical_cves_detected", 0)
        high = data.get("high_cves_detected", 0)
        score = max(0, 100 - critical * 20 - high * 5)
        warnings = [f"Critical CVEs detected: {critical}"] if critical > 0 else []
        return AggregatorResult(success=True, data={"cve_exposure_score": score, "critical_cves": critical, "warnings": warnings})


class FISecurityRatingAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        bitsight = data.get("bitsight_score", 650)
        score = max(0, min(100, (bitsight - 400) / 5))
        return AggregatorResult(success=True, data={"security_rating_score": round(score, 1), "bitsight_score": bitsight})


# =============================================================================
# CORPORATE FOOTPRINT AGGREGATORS
# =============================================================================

class InvestorRelationsAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        if not data.get("is_publicly_traded"): return AggregatorResult(success=True, data={"investor_relations_score": 50, "is_public": False})
        quality = data.get("ir_website_quality", "adequate")
        scores = {"excellent": 95, "good": 80, "adequate": 60, "poor": 35}
        return AggregatorResult(success=True, data={"investor_relations_score": scores.get(quality, 60), "is_public": True})


class FIDisclosureQualityAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        timeliness = data.get("call_report_timeliness", "on_time")
        restatements = data.get("restatements_5yr", 0)
        scores = {"early": 90, "on_time": 75, "late": 45}
        score = scores.get(timeliness, 75) - restatements * 15
        return AggregatorResult(success=True, data={"disclosure_quality_score": max(0, score)})


class FISecurityPageAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        exists = data.get("security_page_exists", False)
        score = 30 if not exists else 60
        if exists:
            if data.get("security_certifications_displayed"): score += 15
            if data.get("vulnerability_disclosure_policy"): score += 15
            if data.get("fraud_prevention_content"): score += 10
        return AggregatorResult(success=True, data={"security_page_score": min(100, score), "page_exists": exists})


class FIHiringSignalsAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        risk_pct = data.get("risk_compliance_as_pct", 10)
        trend = data.get("hiring_trend", "stable")
        score = 50 + risk_pct * 2
        if trend == "expanding": score += 10
        return AggregatorResult(success=True, data={"hiring_signals_score": min(100, score), "risk_compliance_pct": risk_pct})


class FIESGReportingAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        has_esg = data.get("esg_report_published", False)
        score = 30 if not has_esg else 60
        if has_esg:
            if data.get("tcfd_aligned"): score += 15
            if data.get("sasb_aligned"): score += 15
            if data.get("dei_reporting"): score += 10
        return AggregatorResult(success=True, data={"esg_reporting_score": min(100, score), "has_esg_report": has_esg})


class CommunityPresenceAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        branches = data.get("branch_count", 10)
        programs = 0
        if data.get("community_foundation"): programs += 1
        if data.get("financial_literacy_programs"): programs += 1
        if data.get("volunteer_programs"): programs += 1
        score = min(100, 40 + min(30, branches // 5) + programs * 10)
        return AggregatorResult(success=True, data={"community_presence_score": score, "branch_count": branches})


# =============================================================================
# STRUCTURED DATA AGGREGATORS
# =============================================================================

class FIESGRatingAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        msci = data.get("msci_esg_rating", "BBB")
        scores = {"AAA": 100, "AA": 90, "A": 80, "BBB": 65, "BB": 50, "B": 35, "CCC": 20, "NR": 50}
        return AggregatorResult(success=True, data={"esg_rating_score": scores.get(msci, 50), "msci_rating": msci})


class PeerBenchmarkAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        overall = data.get("overall_peer_ranking", 50)
        percentile = 100 - overall
        return AggregatorResult(success=True, data={"peer_benchmark_score": max(0, min(100, percentile)), "peer_ranking": overall})


# =============================================================================
# CATEGORICAL AGGREGATORS
# =============================================================================

class InstitutionTypeAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        return AggregatorResult(success=True, data={"institution_type": data.get("institution_type", "OTHER")})


class RegulatoryAuthorityAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        return AggregatorResult(success=True, data={"regulatory_framework": data.get("primary_regulator", "STATE")})


class AssetSizeAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        return AggregatorResult(success=True, data={"asset_size_band": data.get("asset_size_band", "COMMUNITY"), "total_assets_mm": data.get("total_assets_mm", 500)})


class PubliclyTradedAggregator(ProductionAggregator):
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        data = self._get_primary_data(extractor_results, "data")
        return AggregatorResult(success=True, data={"publicly_traded": data.get("publicly_traded", "PRIVATE")})
