"""
Cyber Aggregators - All Signal Groups

Production-ready aggregators for cyber coverage signals.
Transforms raw extractor data into normalized scoring structures.

Signal Groups:
- network_authority: Customer quality, partners, security vendors, etc.
- technical_infrastructure: TLS, headers, email auth, exposure, CVEs
- corporate_footprint: Security page, policies, bug bounty, leadership
- public_record: Breach history, credentials, dark web, litigation
- structured_data: Security ratings, ESG cyber

All aggregators output scores 0-100 (higher = better for insurance).
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from ...base import ProductionAggregator
from ....types import AggregatorResult, ExtractorResult


# =============================================================================
# NETWORK AUTHORITY AGGREGATORS
# =============================================================================

class CustomerQualityAggregator(ProductionAggregator):
    """Aggregates customer quality signals into score."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No customer data")
        
        has_customers = self._normalize_bool(raw.get("has_visible_customers"))
        enterprise_count = self._normalize_int(raw.get("enterprise_customer_count"), 0)
        f500_count = self._normalize_int(raw.get("fortune_500_count"), 0)
        case_studies = self._normalize_int(raw.get("case_study_count"), 0)
        
        if not has_customers:
            score = 30
        else:
            score = 40
            score += min(enterprise_count * 5, 30)
            score += min(f500_count * 8, 20)
            score += min(case_studies * 2, 10)
        
        return self._create_success_result({
            "has_customers": has_customers,
            "enterprise_count": enterprise_count,
            "customer_quality_score": round(min(100, score), 1),
        }, extractor_results)


class PartnerQualityAggregator(ProductionAggregator):
    """Aggregates partner network quality."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No partner data")
        
        has_partners = self._normalize_bool(raw.get("has_partner_program"))
        tier1 = self._normalize_int(raw.get("tier1_partners"), 0)
        integrations = self._normalize_int(raw.get("integration_count"), 0)
        
        if not has_partners:
            score = 30
        else:
            score = 40
            score += min(tier1 * 10, 30)
            score += min(integrations, 30)
        
        return self._create_success_result({
            "has_partners": has_partners,
            "tier1_partners": tier1,
            "partner_quality_score": round(min(100, score), 1),
        }, extractor_results)


class SecurityVendorAggregator(ProductionAggregator):
    """Aggregates security vendor relationship quality."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No security vendor data")
        
        has_vendors = self._normalize_bool(raw.get("has_security_vendors"))
        tier1 = self._normalize_int(raw.get("tier1_vendor_count"), 0)
        maturity = raw.get("security_stack_maturity", "UNKNOWN")
        
        maturity_scores = {"ENTERPRISE": 30, "MATURE": 25, "DEVELOPING": 15, "BASIC": 5, "MINIMAL": 0, "UNKNOWN": 10}
        
        if not has_vendors:
            score = 20
        else:
            score = 40
            score += min(tier1 * 15, 30)
            score += maturity_scores.get(maturity, 10)
        
        return self._create_success_result({
            "has_security_vendors": has_vendors,
            "tier1_vendors": tier1,
            "security_vendor_score": round(min(100, score), 1),
        }, extractor_results)


class CertificationAuthorityAggregator(ProductionAggregator):
    """Aggregates certification/auditor quality."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No certification data")
        
        has_certs = self._normalize_bool(raw.get("has_visible_certifications"))
        is_big4 = self._normalize_bool(raw.get("is_big4_audited"))
        tier = self._normalize_int(raw.get("auditor_tier"), 3)
        
        if not has_certs:
            score = 30
        elif is_big4:
            score = 95
        elif tier == 2:
            score = 75
        else:
            score = 55
        
        return self._create_success_result({
            "has_certifications": has_certs,
            "is_big4_audited": is_big4,
            "certification_authority_score": round(score, 1),
        }, extractor_results)


class FinancialRelationshipAggregator(ProductionAggregator):
    """Aggregates financial relationship quality."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No financial data")
        
        has_banking = self._normalize_bool(raw.get("has_visible_banking_relationship"))
        has_vc = self._normalize_bool(raw.get("has_vc_funding"))
        tier1_vc = self._normalize_bool(raw.get("tier1_vc_backed"))
        is_public = self._normalize_bool(raw.get("is_publicly_traded"))
        
        score = 40
        if has_banking:
            score += 15
        if has_vc:
            score += 15
        if tier1_vc:
            score += 15
        if is_public:
            score += 15
        
        return self._create_success_result({
            "has_banking": has_banking,
            "has_vc": has_vc,
            "financial_relationship_score": round(min(100, score), 1),
        }, extractor_results)


class NetworkCentralityAggregator(ProductionAggregator):
    """Aggregates network centrality metrics."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No centrality data")
        
        score = self._normalize_float(raw.get("centrality_score"), 50)
        influence = raw.get("industry_influence_tier", "UNKNOWN")
        
        influence_bonus = {"LEADER": 20, "ESTABLISHED": 15, "GROWING": 10, "EMERGING": 5, "UNKNOWN": 0}
        final_score = min(100, score * 0.7 + influence_bonus.get(influence, 0) + 10)
        
        return self._create_success_result({
            "centrality_score": score,
            "network_centrality_score": round(final_score, 1),
        }, extractor_results)


class SecondDegreeAggregator(ProductionAggregator):
    """Aggregates second-degree relationship quality."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No supply chain data")
        
        has_visibility = self._normalize_bool(raw.get("has_supply_chain_visibility"))
        avg_quality = self._normalize_float(raw.get("average_partner_quality_score"), 50)
        concentration = raw.get("concentration_risk", "UNKNOWN")
        
        concentration_penalty = {"LOW": 0, "MODERATE": 10, "HIGH": 25, "CRITICAL": 40, "UNKNOWN": 15}
        
        score = avg_quality - concentration_penalty.get(concentration, 15)
        
        return self._create_success_result({
            "has_visibility": has_visibility,
            "second_degree_score": round(max(0, min(100, score)), 1),
        }, extractor_results)


# =============================================================================
# TECHNICAL INFRASTRUCTURE AGGREGATORS
# =============================================================================

class TLSConfigAggregator(ProductionAggregator):
    """Aggregates TLS/SSL configuration quality."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No TLS data")
        
        score = self._normalize_int(raw.get("ssl_labs_score"), 50)
        grade = raw.get("ssl_labs_grade")
        
        return self._create_success_result({
            "ssl_grade": grade,
            "tls_score": score,
        }, extractor_results)


class SecurityHeadersAggregator(ProductionAggregator):
    """Aggregates HTTP security headers."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No headers data")
        
        score = self._normalize_float(raw.get("security_headers_score"), 50)
        
        return self._create_success_result({
            "headers_present": raw.get("headers_present_count", 0),
            "security_headers_score": round(score, 1),
        }, extractor_results)


class EmailAuthAggregator(ProductionAggregator):
    """Aggregates email authentication quality."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No email auth data")
        
        score = self._normalize_int(raw.get("email_auth_score"), 50)
        
        return self._create_success_result({
            "has_spf": raw.get("has_spf"),
            "has_dmarc": raw.get("has_dmarc"),
            "has_dkim": raw.get("has_dkim"),
            "email_auth_score": score,
        }, extractor_results)


class DNSSECAggregator(ProductionAggregator):
    """Aggregates DNSSEC implementation."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No DNSSEC data")
        
        enabled = self._normalize_bool(raw.get("dnssec_enabled"))
        score = self._normalize_int(raw.get("dnssec_score"), 0)
        
        return self._create_success_result({
            "dnssec_enabled": enabled,
            "dnssec_score": score,
        }, extractor_results)


class NetworkExposureAggregator(ProductionAggregator):
    """Aggregates network exposure risk."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        if not raw:
            return self._create_error_result("No exposure data")
        
        score = self._normalize_int(raw.get("exposure_score"), 50)
        rating = raw.get("exposure_rating", "UNKNOWN")
        
        if rating in ["CRITICAL", "HIGH"]:
            warnings.append(f"Network exposure rating: {rating}")
        
        return self._create_success_result({
            "open_ports": raw.get("total_open_ports"),
            "risky_services": raw.get("risky_service_count"),
            "exposure_rating": rating,
            "network_exposure_score": score,
        }, extractor_results, warnings)


class SoftwareCurrencyAggregator(ProductionAggregator):
    """Aggregates software version freshness."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No software data")
        
        score = self._normalize_float(raw.get("currency_score"), 50)
        
        return self._create_success_result({
            "outdated_pct": raw.get("outdated_percentage"),
            "software_currency_score": round(score, 1),
        }, extractor_results)


class CVEExposureAggregator(ProductionAggregator):
    """Aggregates CVE exposure risk."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        if not raw:
            return self._create_error_result("No CVE data")
        
        score = self._normalize_float(raw.get("cve_exposure_score"), 50)
        critical = self._normalize_int(raw.get("critical_cves"), 0)
        
        if critical > 0:
            warnings.append(f"{critical} critical CVEs detected")
        
        return self._create_success_result({
            "total_cves": raw.get("total_cves_detected"),
            "critical_cves": critical,
            "cve_exposure_score": round(score, 1),
        }, extractor_results, warnings)


class CloudInfraAggregator(ProductionAggregator):
    """Aggregates cloud infrastructure quality."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No cloud data")
        
        uses_cloud = self._normalize_bool(raw.get("uses_cloud_hosting"))
        tier = self._normalize_int(raw.get("provider_tier"), 2)
        
        if uses_cloud:
            score = 90 if tier == 1 else 70
        else:
            score = 50
        
        return self._create_success_result({
            "uses_cloud": uses_cloud,
            "provider": raw.get("primary_provider"),
            "cloud_infrastructure_score": score,
        }, extractor_results)


class WAFPresenceAggregator(ProductionAggregator):
    """Aggregates WAF presence."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No WAF data")
        
        has_waf = self._normalize_bool(raw.get("waf_detected"))
        score = raw.get("waf_score", 0) if has_waf else 0
        
        return self._create_success_result({
            "waf_detected": has_waf,
            "waf_score": score,
        }, extractor_results)


class CDNUsageAggregator(ProductionAggregator):
    """Aggregates CDN usage."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No CDN data")
        
        has_cdn = self._normalize_bool(raw.get("cdn_detected"))
        score = raw.get("cdn_score", 0) if has_cdn else 0
        
        return self._create_success_result({
            "cdn_detected": has_cdn,
            "has_ddos_protection": raw.get("has_ddos_protection"),
            "cdn_score": score,
        }, extractor_results)


# =============================================================================
# CORPORATE FOOTPRINT AGGREGATORS
# =============================================================================

class SecurityPageAggregator(ProductionAggregator):
    """Aggregates security page presence and quality."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No security page data")
        
        score = self._normalize_int(raw.get("security_page_score"), 0)
        
        return self._create_success_result({
            "has_page": raw.get("has_security_page"),
            "quality": raw.get("page_quality"),
            "security_page_score": score,
        }, extractor_results)


class PrivacyPolicyAggregator(ProductionAggregator):
    """Aggregates privacy policy quality."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No privacy policy data")
        
        score = self._normalize_int(raw.get("privacy_policy_score"), 30)
        
        return self._create_success_result({
            "has_policy": raw.get("has_privacy_policy"),
            "comprehensiveness": raw.get("comprehensiveness"),
            "privacy_policy_score": score,
        }, extractor_results)


class SecurityTxtAggregator(ProductionAggregator):
    """Aggregates security.txt presence."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No security.txt data")
        
        score = self._normalize_float(raw.get("security_txt_score"), 0)
        
        return self._create_success_result({
            "has_security_txt": raw.get("has_security_txt"),
            "security_txt_score": round(score, 1),
        }, extractor_results)


class BugBountyAggregator(ProductionAggregator):
    """Aggregates bug bounty program presence."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No bug bounty data")
        
        score = self._normalize_int(raw.get("bug_bounty_score"), 0)
        
        return self._create_success_result({
            "has_bug_bounty": raw.get("has_bug_bounty"),
            "platform": raw.get("platform"),
            "bug_bounty_score": score,
        }, extractor_results)


class SecurityHiringAggregator(ProductionAggregator):
    """Aggregates security hiring activity."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No hiring data")
        
        score = self._normalize_int(raw.get("security_hiring_score"), 0)
        
        return self._create_success_result({
            "has_security_jobs": raw.get("has_security_job_postings"),
            "is_hiring_ciso": raw.get("is_hiring_ciso"),
            "security_hiring_score": score,
        }, extractor_results)


class TechnicalContentAggregator(ProductionAggregator):
    """Aggregates technical blog quality."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No content data")
        
        score = self._normalize_int(raw.get("technical_content_score"), 0)
        
        return self._create_success_result({
            "has_security_content": raw.get("has_security_content"),
            "technical_content_score": min(100, score),
        }, extractor_results)


class DeveloperResourcesAggregator(ProductionAggregator):
    """Aggregates developer resources quality."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No developer data")
        
        score = self._normalize_int(raw.get("developer_resources_score"), 0)
        
        return self._create_success_result({
            "has_api_docs": raw.get("has_api_documentation"),
            "developer_resources_score": min(100, score),
        }, extractor_results)


class SecurityLeadershipAggregator(ProductionAggregator):
    """Aggregates security leadership visibility."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No leadership data")
        
        score = self._normalize_int(raw.get("security_leadership_score"), 0)
        
        return self._create_success_result({
            "has_ciso": raw.get("has_ciso"),
            "ciso_visibility": raw.get("ciso_visibility"),
            "security_leadership_score": min(100, score),
        }, extractor_results)


class ComplianceBadgesAggregator(ProductionAggregator):
    """Aggregates compliance certifications."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No compliance data")
        
        score = self._normalize_int(raw.get("compliance_badges_score"), 0)
        
        return self._create_success_result({
            "has_soc2": raw.get("has_soc2"),
            "has_iso27001": raw.get("has_iso27001"),
            "total_certs": raw.get("total_certifications"),
            "compliance_badges_score": min(100, score),
        }, extractor_results)


# =============================================================================
# PUBLIC RECORD AGGREGATORS
# =============================================================================

class BreachHistoryAggregator(ProductionAggregator):
    """Aggregates breach history."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        if not raw:
            return self._create_error_result("No breach data")
        
        score = self._normalize_float(raw.get("breach_history_score"), 100)
        has_breach = self._normalize_bool(raw.get("has_breach_history"))
        
        if has_breach:
            warnings.append("Breach history detected")
        
        return self._create_success_result({
            "has_breach": has_breach,
            "breach_count": raw.get("breach_count"),
            "breach_history_score": round(score, 1),
        }, extractor_results, warnings)


class LitigationHistoryAggregator(ProductionAggregator):
    """Aggregates privacy litigation history."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No litigation data")
        
        score = self._normalize_float(raw.get("litigation_score"), 100)
        
        return self._create_success_result({
            "has_litigation": raw.get("has_privacy_litigation"),
            "case_count": raw.get("case_count"),
            "litigation_score": round(score, 1),
        }, extractor_results)


class CredentialExposureAggregator(ProductionAggregator):
    """Aggregates credential exposure."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No credential data")
        
        score = self._normalize_float(raw.get("credential_exposure_score"), 50)
        
        return self._create_success_result({
            "has_exposure": raw.get("has_credential_exposure"),
            "emails_exposed": raw.get("total_emails_exposed"),
            "credential_exposure_score": round(score, 1),
        }, extractor_results)


class DarkWebAggregator(ProductionAggregator):
    """Aggregates dark web exposure."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        warnings = []
        if not raw:
            return self._create_error_result("No dark web data")
        
        score = self._normalize_float(raw.get("dark_web_score"), 100)
        has_presence = self._normalize_bool(raw.get("has_dark_web_presence"))
        
        if has_presence:
            warnings.append("Dark web presence detected")
        
        return self._create_success_result({
            "has_presence": has_presence,
            "data_for_sale": raw.get("data_for_sale"),
            "dark_web_score": round(score, 1),
        }, extractor_results, warnings)


# =============================================================================
# STRUCTURED DATA AGGREGATORS
# =============================================================================

class SecurityRatingAggregator(ProductionAggregator):
    """Aggregates third-party security ratings."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No rating data")
        
        score = self._normalize_float(raw.get("security_rating_score"), 50)
        
        return self._create_success_result({
            "has_rating": raw.get("has_security_rating"),
            "bitsight_score": raw.get("bitsight_score"),
            "security_rating_score": round(score, 1),
        }, extractor_results)


class ESGCyberAggregator(ProductionAggregator):
    """Aggregates ESG cyber component."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No ESG data")
        
        score = self._normalize_int(raw.get("esg_cyber_score"), 50)
        
        return self._create_success_result({
            "has_esg_rating": raw.get("has_esg_rating"),
            "esg_cyber_score": score,
        }, extractor_results)


# =============================================================================
# CATEGORICAL AGGREGATORS
# =============================================================================

class IndustryClassificationAggregator(ProductionAggregator):
    """Aggregates industry classification."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No industry data")
        
        return self._create_success_result({
            "primary_industry": raw.get("primary_industry"),
            "is_regulated": raw.get("is_regulated_industry"),
            "is_high_data_volume": raw.get("is_high_data_volume"),
        }, extractor_results)


class CompanySizeAggregator(ProductionAggregator):
    """Aggregates company size classification."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No size data")
        
        return self._create_success_result({
            "size_band": raw.get("size_band"),
            "employee_count": raw.get("employee_count_estimate"),
            "revenue_estimate": raw.get("revenue_estimate_usd"),
        }, extractor_results)


class GeographyAggregator(ProductionAggregator):
    """Aggregates operational geography."""
    
    def aggregate(self, extractor_results: List[ExtractorResult], **kwargs) -> AggregatorResult:
        raw = self._get_primary_data(extractor_results, "data")
        if not raw:
            return self._create_error_result("No geography data")
        
        return self._create_success_result({
            "primary_geography": raw.get("primary_geography"),
            "gdpr_applicable": raw.get("gdpr_applicable"),
            "ccpa_applicable": raw.get("ccpa_applicable"),
        }, extractor_results)
