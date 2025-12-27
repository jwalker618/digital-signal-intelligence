"""
FI Extractors - Operational Risk, Cyber, Corporate Footprint, Structured Data, Categorical

Stub extractors for financial institution signals.
"""

import random
from datetime import datetime, timedelta
from typing import Any, Dict

from ...base import StubExtractor


# =============================================================================
# OPERATIONAL RISK EXTRACTORS
# =============================================================================

class CFPBComplaintExtractor(StubExtractor):
    """Extract CFPB complaint data and analysis."""
    
    DEFAULT_TTL_SECONDS = 86400  # Daily
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        complaint_count = random.randint(10, 5000)
        
        return {
            "entity_id": entity_id,
            "complaint_count_12mo": complaint_count,
            "complaints_per_billion_assets": round(complaint_count / random.uniform(1, 100), 2),
            "peer_percentile": random.randint(10, 95),
            "complaint_trend": random.choice(["decreasing", "stable", "increasing"]),
            "top_categories": random.sample([
                "mortgage", "credit_card", "checking_account", "credit_reporting",
                "debt_collection", "student_loan", "auto_loan", "personal_loan"
            ], k=3),
            "timely_response_rate": round(random.uniform(90, 100), 1),
            "disputed_rate": round(random.uniform(5, 30), 1),
            "relief_rate": round(random.uniform(10, 50), 1),
            "data_source": "cfpb_complaint_database",
            "extracted_at": datetime.utcnow().isoformat()
        }


class BBBComplaintExtractor(StubExtractor):
    """Extract Better Business Bureau complaint patterns."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        return {
            "entity_id": entity_id,
            "bbb_rating": random.choice(["A+", "A", "A-", "B+", "B", "B-", "C", "NR"]),
            "complaint_count_3yr": random.randint(5, 500),
            "complaints_resolved": round(random.uniform(70, 98), 1),
            "average_resolution_days": random.randint(7, 45),
            "customer_reviews_avg": round(random.uniform(1.5, 4.8), 1),
            "review_count": random.randint(10, 1000),
            "accredited": random.random() > 0.6,
            "data_source": "bbb_api",
            "extracted_at": datetime.utcnow().isoformat()
        }


class FILitigationExtractor(StubExtractor):
    """Extract litigation history for financial institutions."""
    
    DEFAULT_TTL_SECONDS = 86400  # Daily
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_material = random.random() < 0.15
        
        litigation_types = ["class_action", "regulatory", "employment", "contract", "securities", "consumer"]
        
        return {
            "entity_id": entity_id,
            "material_litigation_pending": has_material,
            "class_actions_pending": random.randint(0, 3) if has_material else 0,
            "regulatory_suits_pending": random.randint(0, 2) if has_material else 0,
            "securities_litigation": has_material and random.random() > 0.7,
            "total_litigation_reserve_mm": random.randint(1, 500) if has_material else random.randint(0, 50),
            "litigation_settlements_3yr_mm": random.randint(0, 200),
            "pending_matters_count": random.randint(0, 20),
            "litigation_types": random.sample(litigation_types, k=random.randint(1, 4)) if has_material else [],
            "data_source": "pacer_sec_filings",
            "extracted_at": datetime.utcnow().isoformat()
        }


class FIBreachHistoryExtractor(StubExtractor):
    """Extract data breach history for financial institutions."""
    
    DEFAULT_TTL_SECONDS = 86400  # Daily - critical
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_breach = random.random() < 0.12
        
        breaches = []
        if has_breach:
            for _ in range(random.randint(1, 3)):
                breaches.append({
                    "date": (datetime.utcnow() - timedelta(days=random.randint(90, 1825))).strftime("%Y-%m-%d"),
                    "type": random.choice(["unauthorized_access", "phishing", "malware", "insider", "third_party"]),
                    "records_affected": random.randint(1000, 5000000),
                    "pii_involved": random.random() > 0.3,
                    "financial_data_involved": random.random() > 0.4,
                    "regulatory_notification": True,
                    "class_action_filed": random.random() > 0.3
                })
        
        return {
            "entity_id": entity_id,
            "has_breach_history": has_breach,
            "breach_count_5yr": len(breaches),
            "breaches": breaches,
            "total_records_exposed": sum(b.get("records_affected", 0) for b in breaches),
            "most_recent_breach_days_ago": min([
                (datetime.utcnow() - datetime.strptime(b["date"], "%Y-%m-%d")).days
                for b in breaches
            ]) if breaches else None,
            "data_source": "hhs_breach_portal_state_ags",
            "extracted_at": datetime.utcnow().isoformat()
        }


class OperationalIncidentExtractor(StubExtractor):
    """Extract operational incident and outage history."""
    
    DEFAULT_TTL_SECONDS = 86400  # Daily
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        incidents = random.randint(0, 8)
        
        return {
            "entity_id": entity_id,
            "operational_incidents_12mo": incidents,
            "system_outages_12mo": random.randint(0, 5),
            "significant_outages": random.randint(0, 2),
            "average_outage_duration_hrs": round(random.uniform(0.5, 12), 1) if incidents > 0 else 0,
            "customer_impacting_incidents": random.randint(0, incidents),
            "regulatory_reported_incidents": random.randint(0, min(2, incidents)),
            "incident_trend": random.choice(["improving", "stable", "worsening"]),
            "disaster_recovery_tested": random.random() > 0.8,
            "business_continuity_incidents": random.randint(0, 2),
            "data_source": "sec_8k_news_monitoring",
            "extracted_at": datetime.utcnow().isoformat()
        }


# =============================================================================
# CYBER SECURITY EXTRACTORS
# =============================================================================

class FITLSConfigExtractor(StubExtractor):
    """Extract TLS/SSL configuration for FI web properties."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        return {
            "entity_id": entity_id,
            "ssl_labs_grade": random.choices(["A+", "A", "A-", "B", "C", "F"], weights=[0.2, 0.35, 0.2, 0.15, 0.08, 0.02])[0],
            "tls_version_min": random.choice(["TLS 1.3", "TLS 1.2", "TLS 1.2", "TLS 1.1", "TLS 1.0"]),
            "certificate_issuer": random.choice(["DigiCert", "Entrust", "Comodo", "GoDaddy", "Let's Encrypt"]),
            "certificate_days_remaining": random.randint(30, 365),
            "hsts_enabled": random.random() > 0.7,
            "hsts_preload": random.random() > 0.4,
            "perfect_forward_secrecy": random.random() > 0.8,
            "vulnerable_protocols": random.random() < 0.1,
            "ev_certificate": random.random() > 0.5,
            "data_source": "ssl_labs_api",
            "extracted_at": datetime.utcnow().isoformat()
        }


class FIEmailAuthExtractor(StubExtractor):
    """Extract email authentication configuration."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        return {
            "entity_id": entity_id,
            "spf_configured": random.random() > 0.9,
            "spf_policy": random.choice(["strict", "soft", "neutral", "none"]),
            "dkim_configured": random.random() > 0.85,
            "dmarc_configured": random.random() > 0.75,
            "dmarc_policy": random.choice(["reject", "quarantine", "none", "none"]),
            "dmarc_pct": random.choice([100, 100, 50, 25, 0]),
            "dmarc_rua_configured": random.random() > 0.6,
            "bimi_configured": random.random() > 0.2,
            "email_security_score": random.randint(40, 100),
            "data_source": "dns_email_auth_check",
            "extracted_at": datetime.utcnow().isoformat()
        }


class FISecurityHeadersExtractor(StubExtractor):
    """Extract HTTP security headers configuration."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        return {
            "entity_id": entity_id,
            "content_security_policy": random.random() > 0.6,
            "x_frame_options": random.random() > 0.85,
            "x_content_type_options": random.random() > 0.8,
            "x_xss_protection": random.random() > 0.75,
            "referrer_policy": random.random() > 0.65,
            "permissions_policy": random.random() > 0.4,
            "cache_control_secure": random.random() > 0.7,
            "security_headers_score": random.randint(30, 100),
            "headers_grade": random.choices(["A", "B", "C", "D", "F"], weights=[0.2, 0.3, 0.25, 0.15, 0.1])[0],
            "data_source": "securityheaders_api",
            "extracted_at": datetime.utcnow().isoformat()
        }


class FINetworkExposureExtractor(StubExtractor):
    """Extract network exposure and attack surface."""
    
    DEFAULT_TTL_SECONDS = 86400  # Daily
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        return {
            "entity_id": entity_id,
            "public_ips_count": random.randint(5, 200),
            "open_ports_count": random.randint(2, 50),
            "high_risk_ports_exposed": random.randint(0, 5),
            "rdp_exposed": random.random() < 0.05,
            "ssh_exposed": random.random() < 0.15,
            "database_ports_exposed": random.random() < 0.03,
            "subdomains_count": random.randint(10, 500),
            "dangling_dns_records": random.randint(0, 10),
            "cloud_assets_discovered": random.randint(5, 100),
            "shadow_it_indicators": random.randint(0, 15),
            "attack_surface_score": random.randint(30, 95),
            "data_source": "shodan_censys_analysis",
            "extracted_at": datetime.utcnow().isoformat()
        }


class FICVEExposureExtractor(StubExtractor):
    """Extract known vulnerability exposure."""
    
    DEFAULT_TTL_SECONDS = 86400  # Daily - critical
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        critical_cves = random.randint(0, 5)
        
        return {
            "entity_id": entity_id,
            "critical_cves_detected": critical_cves,
            "high_cves_detected": random.randint(0, 15),
            "medium_cves_detected": random.randint(0, 30),
            "low_cves_detected": random.randint(0, 50),
            "cves_with_exploit": random.randint(0, min(3, critical_cves)),
            "oldest_unpatched_days": random.randint(0, 365) if critical_cves > 0 else 0,
            "patch_cadence_score": random.randint(40, 100),
            "vulnerable_software_detected": random.sample([
                "Apache", "nginx", "OpenSSL", "jQuery", "WordPress", "PHP", "Java", "Exchange"
            ], k=random.randint(0, 4)),
            "data_source": "vulnerability_scanner_apis",
            "extracted_at": datetime.utcnow().isoformat()
        }


class FISecurityRatingExtractor(StubExtractor):
    """Extract third-party security ratings."""
    
    DEFAULT_TTL_SECONDS = 86400  # Daily
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        bitsight = random.randint(400, 900)
        
        return {
            "entity_id": entity_id,
            "bitsight_score": bitsight,
            "bitsight_grade": "A" if bitsight >= 740 else "B" if bitsight >= 640 else "C" if bitsight >= 540 else "D",
            "securityscorecard_score": random.randint(40, 100),
            "securityscorecard_grade": random.choice(["A", "B", "C", "D", "F"]),
            "upguard_score": random.randint(400, 950),
            "riskrecon_rating": random.choice(["A", "B", "C", "D", "F"]),
            "rating_trend": random.choice(["improving", "stable", "declining"]),
            "industry_percentile": random.randint(20, 95),
            "data_source": "security_rating_apis",
            "extracted_at": datetime.utcnow().isoformat()
        }


# =============================================================================
# CORPORATE FOOTPRINT EXTRACTORS
# =============================================================================

class InvestorRelationsExtractor(StubExtractor):
    """Extract investor relations quality indicators."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        is_public = random.random() > 0.4
        
        return {
            "entity_id": entity_id,
            "is_publicly_traded": is_public,
            "ir_website_quality": random.choice(["excellent", "good", "adequate", "poor"]) if is_public else "n/a",
            "earnings_call_frequency": "quarterly" if is_public else "n/a",
            "investor_presentations_annual": random.randint(2, 12) if is_public else 0,
            "analyst_coverage_count": random.randint(0, 25) if is_public else 0,
            "investor_day_annual": random.random() > 0.6 if is_public else False,
            "shareholder_communication_quality": random.choice(["excellent", "good", "adequate"]) if is_public else "n/a",
            "proxy_accessibility": random.choice(["excellent", "good", "adequate"]) if is_public else "n/a",
            "data_source": "company_website_sec_analysis",
            "extracted_at": datetime.utcnow().isoformat()
        }


class FIDisclosureQualityExtractor(StubExtractor):
    """Extract disclosure quality indicators."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        return {
            "entity_id": entity_id,
            "call_report_timeliness": random.choice(["early", "on_time", "on_time", "late"]),
            "sec_filing_timeliness": random.choice(["early", "on_time", "on_time", "late", "n/a"]),
            "disclosure_completeness": random.choice(["comprehensive", "adequate", "limited"]),
            "risk_disclosure_quality": random.choice(["excellent", "good", "adequate", "generic"]),
            "material_event_timeliness": random.choice(["prompt", "adequate", "delayed"]),
            "restatements_5yr": random.randint(0, 2),
            "late_filings_5yr": random.randint(0, 3),
            "comment_letters_received": random.randint(0, 5),
            "data_source": "sec_edgar_ffiec_analysis",
            "extracted_at": datetime.utcnow().isoformat()
        }


class FISecurityPageExtractor(StubExtractor):
    """Extract security/trust page presence and quality."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_page = random.random() > 0.3
        
        return {
            "entity_id": entity_id,
            "security_page_exists": has_page,
            "security_certifications_displayed": has_page and random.random() > 0.4,
            "fraud_prevention_content": has_page and random.random() > 0.7,
            "security_contact_provided": has_page and random.random() > 0.5,
            "vulnerability_disclosure_policy": has_page and random.random() > 0.3,
            "privacy_policy_current": random.random() > 0.9,
            "security_awareness_content": has_page and random.random() > 0.6,
            "trust_center_quality": random.choice(["excellent", "good", "basic", "none"]),
            "data_source": "website_analysis",
            "extracted_at": datetime.utcnow().isoformat()
        }


class FIHiringSignalsExtractor(StubExtractor):
    """Extract risk, compliance, and security hiring signals."""
    
    DEFAULT_TTL_SECONDS = 86400 * 3  # Every 3 days
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        return {
            "entity_id": entity_id,
            "risk_positions_open": random.randint(0, 20),
            "compliance_positions_open": random.randint(0, 15),
            "security_positions_open": random.randint(0, 10),
            "audit_positions_open": random.randint(0, 8),
            "bsa_aml_positions_open": random.randint(0, 6),
            "total_positions_open": random.randint(10, 200),
            "risk_compliance_as_pct": round(random.uniform(5, 25), 1),
            "hiring_trend": random.choice(["expanding", "stable", "contracting"]),
            "senior_risk_hiring": random.random() > 0.3,
            "cro_cco_search": random.random() < 0.1,
            "data_source": "linkedin_indeed_analysis",
            "extracted_at": datetime.utcnow().isoformat()
        }


class FIESGReportingExtractor(StubExtractor):
    """Extract ESG reporting indicators."""
    
    DEFAULT_TTL_SECONDS = 86400 * 30  # Monthly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_esg = random.random() > 0.4
        
        return {
            "entity_id": entity_id,
            "esg_report_published": has_esg,
            "sustainability_report": has_esg and random.random() > 0.5,
            "tcfd_aligned": has_esg and random.random() > 0.4,
            "sasb_aligned": has_esg and random.random() > 0.3,
            "gri_aligned": has_esg and random.random() > 0.35,
            "cdp_participant": has_esg and random.random() > 0.25,
            "net_zero_commitment": has_esg and random.random() > 0.3,
            "dei_reporting": has_esg and random.random() > 0.6,
            "community_investment_disclosed": random.random() > 0.7,
            "esg_report_frequency": random.choice(["annual", "biennial", "none"]) if has_esg else "none",
            "data_source": "company_website_esg_databases",
            "extracted_at": datetime.utcnow().isoformat()
        }


class CommunityPresenceExtractor(StubExtractor):
    """Extract community involvement and local presence."""
    
    DEFAULT_TTL_SECONDS = 86400 * 30  # Monthly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        return {
            "entity_id": entity_id,
            "branch_count": random.randint(1, 500),
            "states_served": random.randint(1, 50),
            "community_foundation": random.random() > 0.4,
            "charitable_giving_disclosed": random.random() > 0.6,
            "volunteer_programs": random.random() > 0.7,
            "financial_literacy_programs": random.random() > 0.5,
            "cdfi_certified": random.random() > 0.1,
            "community_development_lending": random.random() > 0.6,
            "local_board_involvement": random.randint(0, 10),
            "community_awards": random.randint(0, 5),
            "data_source": "company_website_news_analysis",
            "extracted_at": datetime.utcnow().isoformat()
        }


# =============================================================================
# STRUCTURED DATA EXTRACTORS
# =============================================================================

class FIESGRatingExtractor(StubExtractor):
    """Extract ESG ratings from major providers."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        return {
            "entity_id": entity_id,
            "msci_esg_rating": random.choice(["AAA", "AA", "A", "BBB", "BB", "B", "CCC", "NR"]),
            "sustainalytics_score": random.randint(10, 50),
            "sustainalytics_risk": random.choice(["negligible", "low", "medium", "high", "severe"]),
            "cdp_climate_score": random.choice(["A", "A-", "B", "B-", "C", "C-", "D", "D-", "F", "NR"]),
            "iss_esg_score": random.randint(1, 10),
            "refinitiv_esg_score": random.randint(20, 90),
            "bloomberg_esg_score": round(random.uniform(20, 80), 1),
            "data_source": "esg_rating_providers",
            "extracted_at": datetime.utcnow().isoformat()
        }


class PeerBenchmarkExtractor(StubExtractor):
    """Extract peer group benchmarking data."""
    
    DEFAULT_TTL_SECONDS = 86400  # Daily
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        return {
            "entity_id": entity_id,
            "peer_group": random.choice(["money_center", "regional", "community", "credit_union", "thrift"]),
            "asset_size_percentile": random.randint(10, 95),
            "roa_percentile": random.randint(15, 90),
            "roe_percentile": random.randint(15, 90),
            "efficiency_percentile": random.randint(10, 90),
            "capital_percentile": random.randint(20, 95),
            "asset_quality_percentile": random.randint(15, 90),
            "growth_percentile": random.randint(10, 95),
            "overall_peer_ranking": random.randint(1, 100),
            "peer_group_size": random.randint(20, 500),
            "data_source": "ffiec_ubpr_snl",
            "extracted_at": datetime.utcnow().isoformat()
        }


# =============================================================================
# CATEGORICAL EXTRACTORS
# =============================================================================

class InstitutionTypeExtractor(StubExtractor):
    """Extract institution type classification."""
    
    DEFAULT_TTL_SECONDS = 86400 * 30  # Monthly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        inst_types = [
            "MONEY_CENTER_BANK", "REGIONAL_BANK", "COMMUNITY_BANK", "CREDIT_UNION",
            "SAVINGS_INSTITUTION", "BROKER_DEALER", "INVESTMENT_ADVISER", "INSURANCE_COMPANY",
            "ASSET_MANAGER", "FINTECH", "MORTGAGE_COMPANY", "PAYMENT_PROCESSOR", "OTHER"
        ]
        weights = [0.02, 0.08, 0.35, 0.20, 0.05, 0.05, 0.08, 0.03, 0.04, 0.04, 0.03, 0.02, 0.01]
        
        return {
            "entity_id": entity_id,
            "institution_type": random.choices(inst_types, weights=weights)[0],
            "charter_type": random.choice(["national", "state_member", "state_nonmember", "federal_cu", "state_cu", "other"]),
            "holding_company": random.random() > 0.4,
            "fhc_status": random.random() > 0.3,
            "fdic_insured": random.random() > 0.85,
            "ncua_insured": random.random() > 0.15,
            "data_source": "ffiec_nic_database",
            "extracted_at": datetime.utcnow().isoformat()
        }


class RegulatoryAuthorityExtractor(StubExtractor):
    """Extract primary regulatory authority."""
    
    DEFAULT_TTL_SECONDS = 86400 * 30  # Monthly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        regulators = ["OCC", "FDIC", "FED", "NCUA", "SEC", "FINRA", "STATE", "MULTI"]
        weights = [0.15, 0.25, 0.15, 0.15, 0.08, 0.07, 0.10, 0.05]
        
        primary = random.choices(regulators, weights=weights)[0]
        
        return {
            "entity_id": entity_id,
            "primary_regulator": primary,
            "secondary_regulators": random.sample(["CFPB", "State", "FINRA", "SEC", "OCC"], k=random.randint(0, 3)),
            "functional_regulators": random.randint(1, 5),
            "g_sib_designation": primary == "FED" and random.random() < 0.1,
            "d_sib_designation": random.random() < 0.05,
            "ccar_participant": random.random() < 0.15,
            "data_source": "ffiec_nic_database",
            "extracted_at": datetime.utcnow().isoformat()
        }


class AssetSizeExtractor(StubExtractor):
    """Extract asset size classification."""
    
    DEFAULT_TTL_SECONDS = 86400  # Daily
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        bands = ["MEGA", "LARGE", "MID", "SMALL", "COMMUNITY"]
        weights = [0.02, 0.05, 0.10, 0.25, 0.58]
        
        band = random.choices(bands, weights=weights)[0]
        
        asset_ranges = {
            "MEGA": (250000, 3000000),
            "LARGE": (50000, 250000),
            "MID": (10000, 50000),
            "SMALL": (1000, 10000),
            "COMMUNITY": (50, 1000)
        }
        
        low, high = asset_ranges[band]
        assets = random.randint(low, high)
        
        return {
            "entity_id": entity_id,
            "asset_size_band": band,
            "total_assets_mm": assets,
            "total_deposits_mm": int(assets * random.uniform(0.7, 0.9)),
            "total_loans_mm": int(assets * random.uniform(0.55, 0.75)),
            "asset_growth_1yr_pct": round(random.uniform(-5, 25), 2),
            "data_source": "ffiec_call_reports",
            "extracted_at": datetime.utcnow().isoformat()
        }


class PubliclyTradedExtractor(StubExtractor):
    """Extract publicly traded status."""
    
    DEFAULT_TTL_SECONDS = 86400 * 7  # Weekly
    
    def _generate_stub_data(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        is_public = random.random() > 0.6
        
        return {
            "entity_id": entity_id,
            "publicly_traded": "PUBLIC" if is_public else "PRIVATE",
            "exchange": random.choice(["NYSE", "NASDAQ", "OTC"]) if is_public else None,
            "ticker": f"FI{random.randint(100, 999)}" if is_public else None,
            "market_cap_mm": random.randint(100, 500000) if is_public else None,
            "sec_reporting": is_public,
            "institutional_ownership_pct": round(random.uniform(20, 85), 1) if is_public else None,
            "insider_ownership_pct": round(random.uniform(2, 40), 1) if is_public else None,
            "data_source": "sec_edgar_exchange_data",
            "extracted_at": datetime.utcnow().isoformat()
        }
