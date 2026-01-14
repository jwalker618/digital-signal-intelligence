"""
PI Extractors - Technical Infrastructure, Corporate Footprint, Litigation, Categorical

Stub extractors for Professional Indemnity coverage signals.
"""

import random
from datetime import datetime, timedelta
from typing import Any, Dict, List

from ...base import StubExtractor


# =============================================================================
# TECHNICAL INFRASTRUCTURE EXTRACTORS
# =============================================================================

class PITLSScoreExtractor(StubExtractor):
    """Extract TLS/SSL configuration quality."""
    
    DEFAULT_TTL_SECONDS = 86400  # Daily
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        grade = random.choices(
            ["A+", "A", "A-", "B", "C", "F"],
            weights=[0.15, 0.25, 0.2, 0.25, 0.1, 0.05]
        )[0]
        
        return {
            "entity_id": entity_id,
            "ssl_labs_grade": grade,
            "tls_version": random.choice(["1.3", "1.2", "1.2", "1.1"]),
            "certificate_valid": random.random() > 0.02,
            "certificate_days_remaining": random.randint(10, 365),
            "hsts_enabled": random.random() > 0.5,
            "perfect_forward_secrecy": random.random() > 0.7,
            "data_source": "ssl_labs_scan",
            "extracted_at": datetime.utcnow().isoformat()
        }


class PIEmailAuthExtractor(StubExtractor):
    """Extract email authentication configuration."""
    
    DEFAULT_TTL_SECONDS = 86400  # Daily
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        return {
            "entity_id": entity_id,
            "spf_configured": random.random() > 0.3,
            "spf_policy": random.choice(["strict", "soft", "neutral", "none"]),
            "dkim_configured": random.random() > 0.4,
            "dmarc_configured": random.random() > 0.35,
            "dmarc_policy": random.choice(["reject", "quarantine", "none"]) if random.random() > 0.35 else "none",
            "data_source": "dns_email_scan",
            "extracted_at": datetime.utcnow().isoformat()
        }


class PISecurityHeadersExtractor(StubExtractor):
    """Extract HTTP security headers."""
    
    DEFAULT_TTL_SECONDS = 86400  # Daily
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        grade = random.choices(
            ["A", "B", "C", "D", "F"],
            weights=[0.1, 0.25, 0.35, 0.2, 0.1]
        )[0]
        
        return {
            "entity_id": entity_id,
            "headers_grade": grade,
            "content_security_policy": random.random() > 0.3,
            "x_frame_options": random.random() > 0.5,
            "x_content_type_options": random.random() > 0.6,
            "referrer_policy": random.random() > 0.4,
            "permissions_policy": random.random() > 0.25,
            "data_source": "security_headers_scan",
            "extracted_at": datetime.utcnow().isoformat()
        }


class PortalSecurityExtractor(StubExtractor):
    """Extract client portal security if applicable."""
    
    DEFAULT_TTL_SECONDS = 86400  # Daily
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_portal = random.random() > 0.4
        
        return {
            "entity_id": entity_id,
            "has_client_portal": has_portal,
            "portal_ssl_grade": random.choice(["A", "A-", "B", "C"]) if has_portal else None,
            "mfa_available": random.random() > 0.6 if has_portal else None,
            "mfa_required": random.random() > 0.3 if has_portal else None,
            "session_timeout": random.randint(15, 120) if has_portal else None,
            "encryption_at_rest": random.random() > 0.7 if has_portal else None,
            "data_source": "portal_analysis",
            "extracted_at": datetime.utcnow().isoformat()
        }


class PIBreachHistoryExtractor(StubExtractor):
    """Extract historical data breaches."""
    
    DEFAULT_TTL_SECONDS = 86400  # Daily - important
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_breach = random.random() < 0.08
        
        return {
            "entity_id": entity_id,
            "has_breach_history": has_breach,
            "breach_count_5yr": random.randint(1, 2) if has_breach else 0,
            "records_exposed": random.randint(100, 50000) if has_breach else 0,
            "pii_exposed": has_breach and random.random() > 0.3,
            "client_data_exposed": has_breach and random.random() > 0.4,
            "regulatory_notification_required": has_breach and random.random() > 0.5,
            "most_recent_breach_years": random.randint(1, 5) if has_breach else None,
            "data_source": "breach_databases",
            "extracted_at": datetime.utcnow().isoformat()
        }


# =============================================================================
# CORPORATE FOOTPRINT EXTRACTORS
# =============================================================================

class PIWebsiteQualityExtractor(StubExtractor):
    """Extract website professionalism."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        quality = random.choices(
            ["professional", "adequate", "basic", "minimal", "none"],
            weights=[0.3, 0.35, 0.2, 0.1, 0.05]
        )[0]
        
        return {
            "entity_id": entity_id,
            "website_quality": quality,
            "mobile_responsive": random.random() > 0.7,
            "last_update_days": random.randint(7, 365),
            "blog_active": random.random() > 0.4,
            "contact_forms": random.random() > 0.6,
            "chat_feature": random.random() > 0.2,
            "page_speed_score": random.randint(30, 100),
            "data_source": "website_analysis",
            "extracted_at": datetime.utcnow().isoformat()
        }


class BioCompletenessExtractor(StubExtractor):
    """Extract professional bio quality."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        return {
            "entity_id": entity_id,
            "bios_present": random.random() > 0.85,
            "bio_completeness_pct": round(random.uniform(40, 100), 1),
            "education_listed": random.random() > 0.9,
            "experience_detailed": random.random() > 0.7,
            "credentials_listed": random.random() > 0.8,
            "practice_areas_clear": random.random() > 0.75,
            "headshots_professional": random.random() > 0.6,
            "data_source": "website_analysis",
            "extracted_at": datetime.utcnow().isoformat()
        }


class PracticeClarityExtractor(StubExtractor):
    """Extract practice area clarity."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        return {
            "entity_id": entity_id,
            "practice_areas_defined": random.random() > 0.85,
            "practice_area_count": random.randint(1, 15),
            "service_descriptions": random.random() > 0.7,
            "industry_focus_clear": random.random() > 0.5,
            "case_studies": random.random() > 0.3,
            "representative_matters": random.random() > 0.4,
            "data_source": "website_analysis",
            "extracted_at": datetime.utcnow().isoformat()
        }


class PublicationsExtractor(StubExtractor):
    """Extract thought leadership content."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        return {
            "entity_id": entity_id,
            "blog_posts_yr": random.randint(0, 50),
            "articles_published": random.randint(0, 30),
            "white_papers": random.randint(0, 10),
            "newsletters": random.random() > 0.4,
            "podcast_host": random.random() > 0.1,
            "webinars_yr": random.randint(0, 12),
            "content_freshness_days": random.randint(7, 365),
            "data_source": "website_content_analysis",
            "extracted_at": datetime.utcnow().isoformat()
        }


class CommunityInvolvementExtractor(StubExtractor):
    """Extract pro bono and community service."""
    
    DEFAULT_TTL_SECONDS = 86400 * 30  # Monthly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        return {
            "entity_id": entity_id,
            "pro_bono_program": random.random() > 0.5,
            "pro_bono_hours_visible": random.random() > 0.3,
            "legal_aid_partnership": random.random() > 0.3,
            "nonprofit_board_service": random.randint(0, 5),
            "community_events": random.randint(0, 10),
            "charitable_foundation": random.random() > 0.15,
            "data_source": "website_news_analysis",
            "extracted_at": datetime.utcnow().isoformat()
        }


class DiversityExtractor(StubExtractor):
    """Extract diversity signals and commitment."""
    
    DEFAULT_TTL_SECONDS = 86400 * 30  # Monthly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        return {
            "entity_id": entity_id,
            "diversity_statement": random.random() > 0.5,
            "diversity_committee": random.random() > 0.3,
            "diversity_awards": random.randint(0, 3),
            "mansfield_certified": random.random() > 0.15,
            "diverse_partner_pct_visible": random.random() > 0.25,
            "affinity_groups": random.random() > 0.3,
            "data_source": "website_news_analysis",
            "extracted_at": datetime.utcnow().isoformat()
        }


# =============================================================================
# LITIGATION HISTORY EXTRACTORS
# =============================================================================

class MalpracticeSuitsExtractor(StubExtractor):
    """Extract professional negligence suits filed."""
    
    DEFAULT_TTL_SECONDS = 86400  # Daily - critical
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_suits = random.random() < 0.12
        
        return {
            "entity_id": entity_id,
            "has_malpractice_suits": has_suits,
            "active_suits": random.randint(0, 2) if has_suits else 0,
            "suits_5yr": random.randint(1, 4) if has_suits else 0,
            "suits_resolved_favorably": random.randint(0, 2) if has_suits else 0,
            "settlements": random.randint(0, 2) if has_suits else 0,
            "judgments_against": random.randint(0, 1) if has_suits else 0,
            "data_source": "court_records",
            "extracted_at": datetime.utcnow().isoformat()
        }


class FeeDisputesLitigationExtractor(StubExtractor):
    """Extract fee-related litigation and arbitration."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_disputes = random.random() < 0.1
        
        return {
            "entity_id": entity_id,
            "has_fee_litigation": has_disputes,
            "fee_suits_5yr": random.randint(0, 3) if has_disputes else 0,
            "arbitrations_5yr": random.randint(0, 5) if has_disputes else 0,
            "collection_suits_filed": random.randint(0, 10) if has_disputes else 0,
            "quantum_meruit_claims": random.randint(0, 2) if has_disputes else 0,
            "data_source": "court_arbitration_records",
            "extracted_at": datetime.utcnow().isoformat()
        }


class RegulatoryEnforcementExtractor(StubExtractor):
    """Extract regulatory enforcement actions."""
    
    DEFAULT_TTL_SECONDS = 86400  # Daily - critical
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_enforcement = random.random() < 0.08
        
        return {
            "entity_id": entity_id,
            "has_enforcement_history": has_enforcement,
            "enforcement_actions_5yr": random.randint(1, 3) if has_enforcement else 0,
            "active_investigations": random.randint(0, 1) if has_enforcement else 0,
            "fines_paid": random.randint(5000, 100000) if has_enforcement else 0,
            "consent_orders": random.randint(0, 2) if has_enforcement else 0,
            "license_restrictions": random.random() < 0.3 if has_enforcement else False,
            "data_source": "regulatory_records",
            "extracted_at": datetime.utcnow().isoformat()
        }


class CivilLitigationExtractor(StubExtractor):
    """Extract other civil suits as defendant."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_civil = random.random() < 0.15
        
        return {
            "entity_id": entity_id,
            "has_civil_litigation": has_civil,
            "civil_suits_5yr": random.randint(1, 5) if has_civil else 0,
            "employment_suits": random.randint(0, 2) if has_civil else 0,
            "contract_disputes": random.randint(0, 3) if has_civil else 0,
            "landlord_tenant": random.randint(0, 2) if has_civil else 0,
            "pending_suits": random.randint(0, 2) if has_civil else 0,
            "data_source": "court_records",
            "extracted_at": datetime.utcnow().isoformat()
        }


class BankruptcyExtractor(StubExtractor):
    """Extract firm or principal bankruptcy."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_bankruptcy = random.random() < 0.04
        
        return {
            "entity_id": entity_id,
            "has_bankruptcy_history": has_bankruptcy,
            "firm_bankruptcy": has_bankruptcy and random.random() < 0.3,
            "principal_bankruptcy": has_bankruptcy and random.random() > 0.3,
            "chapter": random.choice([7, 11, 13]) if has_bankruptcy else None,
            "years_since_discharge": random.randint(1, 10) if has_bankruptcy else None,
            "current_bankruptcy": has_bankruptcy and random.random() < 0.2,
            "data_source": "pacer_bankruptcy_records",
            "extracted_at": datetime.utcnow().isoformat()
        }


# =============================================================================
# CATEGORICAL EXTRACTORS
# =============================================================================

class ProfessionClassificationExtractor(StubExtractor):
    """Extract primary profession type."""
    
    DEFAULT_TTL_SECONDS = 86400 * 30  # Monthly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        professions = ["LAW_FIRM", "ACCOUNTING_FIRM", "ARCHITECTURE", "ENGINEERING",
                      "MANAGEMENT_CONSULTING", "IT_CONSULTING", "HR_CONSULTING",
                      "REAL_ESTATE", "INSURANCE_BROKER", "FINANCIAL_PLANNING",
                      "HEALTHCARE_ADMIN", "APPRAISAL_VALUATION", "ENVIRONMENTAL_CONSULTING", "OTHER"]
        
        profession = random.choices(
            professions,
            weights=[0.25, 0.15, 0.08, 0.1, 0.08, 0.08, 0.03, 0.06, 0.05, 0.04, 0.03, 0.02, 0.02, 0.01]
        )[0]
        
        return {
            "entity_id": entity_id,
            "profession_type": profession,
            "naics_code": random.choice(["541110", "541211", "541310", "541330", "541611", "541512"]),
            "sic_code": random.choice(["8111", "8721", "8712", "8711", "8748", "7371"]),
            "data_source": "business_classification",
            "extracted_at": datetime.utcnow().isoformat()
        }


class FirmSizeExtractor(StubExtractor):
    """Extract firm size by professional headcount."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        professional_count = random.choices(
            [1, 3, 12, 50, 200, 800],
            weights=[0.25, 0.25, 0.2, 0.15, 0.1, 0.05]
        )[0] + random.randint(-1, 5)
        
        if professional_count <= 1: band = "SOLO"
        elif professional_count <= 5: band = "MICRO"
        elif professional_count <= 20: band = "SMALL"
        elif professional_count <= 100: band = "MEDIUM"
        elif professional_count <= 500: band = "LARGE"
        else: band = "MAJOR"
        
        return {
            "entity_id": entity_id,
            "firm_size": band,
            "professional_count": max(1, professional_count),
            "total_employees": max(1, professional_count) + random.randint(0, professional_count),
            "offices": random.randint(1, 10) if band in ["MEDIUM", "LARGE", "MAJOR"] else random.randint(1, 3),
            "data_source": "linkedin_business_records",
            "extracted_at": datetime.utcnow().isoformat()
        }


class AnnualRevenueExtractor(StubExtractor):
    """Extract annual revenue classification."""
    
    DEFAULT_TTL_SECONDS = 86400 * 30  # Monthly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        revenue_mm = random.choices(
            [0.3, 0.7, 2.5, 12, 50, 250, 800],
            weights=[0.2, 0.2, 0.25, 0.15, 0.1, 0.07, 0.03]
        )[0] * random.uniform(0.8, 1.2)
        
        if revenue_mm < 0.5: band = "UNDER_500K"
        elif revenue_mm < 1: band = "R_500K_1M"
        elif revenue_mm < 5: band = "R_1M_5M"
        elif revenue_mm < 25: band = "R_5M_25M"
        elif revenue_mm < 100: band = "R_25M_100M"
        elif revenue_mm < 500: band = "R_100M_500M"
        else: band = "OVER_500M"
        
        return {
            "entity_id": entity_id,
            "revenue_size": band,
            "estimated_revenue_mm": round(revenue_mm, 2),
            "revenue_trend": random.choice(["growing", "stable", "declining"]),
            "revenue_per_professional": round(revenue_mm * 1000000 / random.randint(5, 50), 0),
            "data_source": "business_financials",
            "extracted_at": datetime.utcnow().isoformat()
        }
