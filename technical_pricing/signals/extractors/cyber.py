"""
extractors/#coverage#.py - Coverage Inference Functions
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from .framework import (
    TTLCategory,
    TTLConfig,
    DataSource,
    SignalResult,
    ExtractionResult,
    MissingSignalStrategy,
    SignalWeightConfig,
    DataExtractor,

    EXTRACTOR_REGISTRY,

    register_extractor
)

logger = logging.getLogger(__name__)

# =============================================================================
# CYBER EXTRACTORS
# =============================================================================

@register_extractor
class SecurityScorecardExtractor(DataExtractor):
    """
    SecurityScorecard/BitSight - External security ratings.
    
    Signals: security_rating, tls_score, email_auth, exposure
    
    Alternative Sources:
    - BitSight: ratings/company
    - SecurityScorecard: companies/score
    - RiskRecon: ratings
    """
    source_name = "security_scorecard"
    coverage = "cyber"
    signals = ["security_rating", "tls_score", "email_auth", "exposure", "software_currency"]
    ttl_config = TTLConfig.semi_static("Security ratings updated weekly")
    
    alternative_sources = [
        DataSource("api", "bitsight", "ratings/company", priority=1),
        DataSource("api", "securityscorecard", "companies/score", priority=1),
        DataSource("api", "riskrecon", "ratings", priority=2),
    ]

    def extract(self) -> ExtractionResult:
        overall_score = self._weighted_choice([
            (self._rng.randint(85, 100), 0.20), (self._rng.randint(70, 84), 0.40),
            (self._rng.randint(55, 69), 0.25), (self._rng.randint(30, 54), 0.15)
        ])
        
        grade_map = {range(90, 101): "A", range(80, 90): "B", range(70, 80): "C", 
                    range(60, 70): "D", range(0, 60): "F"}
        grade = next((g for r, g in grade_map.items() if overall_score in r), "F")
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("CO", 10)),
            "overall_rating": {
                "score": overall_score,
                "grade": grade,
                "trend": self._weighted_choice([("Improving", 0.30), ("Stable", 0.50), ("Declining", 0.20)]),
                "last_updated": self._random_date(7, 0),
            },
            "factor_scores": {
                "network_security": self._rng.randint(50, 100),
                "dns_health": self._rng.randint(60, 100),
                "patching_cadence": self._rng.randint(40, 100),
                "endpoint_security": self._rng.randint(50, 100),
                "ip_reputation": self._rng.randint(60, 100),
                "application_security": self._rng.randint(50, 100),
                "cubit_score": self._rng.randint(50, 100),
                "hacker_chatter": self._rng.randint(70, 100),
                "information_leak": self._rng.randint(60, 100),
                "social_engineering": self._rng.randint(60, 100),
            },
            "issues": {
                "critical": self._rng.randint(0, 5),
                "high": self._rng.randint(0, 15),
                "medium": self._rng.randint(0, 30),
                "low": self._rng.randint(0, 50),
            },
            "peer_comparison": {
                "industry_rank_pct": self._rng.randint(10, 90),
                "industry_average_score": self._rng.randint(65, 80),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "score": overall_score,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class TechnicalScanExtractor(DataExtractor):
    """
    Technical Security Scans - TLS, headers, DNS, exposed services.
    
    Signals: tls_score, security_headers, dnssec, waf_presence, cdn_usage
    
    Alternative Sources:
    - SSL Labs: analyze
    - SecurityHeaders.com: scan
    - Shodan: host/search
    - Censys: hosts/search
    """
    source_name = "technical_scan"
    coverage = "cyber"
    signals = ["tls_score", "security_headers", "dnssec", "waf_presence", "cdn_usage", "cloud_infrastructure"]
    ttl_config = TTLConfig.dynamic("Technical scans refreshed daily")
    
    alternative_sources = [
        DataSource("scan", "ssllabs", "analyze", priority=1),
        DataSource("scan", "securityheaders.com", "scan", priority=1),
        DataSource("api", "shodan", "host/search", priority=2),
        DataSource("api", "censys", "hosts/search", priority=2),
        DataSource("dns", "internal", "dnssec_validator", priority=1),
    ]

    def extract(self) -> ExtractionResult:
        tls_grade = self._weighted_choice([
            ("A+", 0.15), ("A", 0.30), ("A-", 0.15), ("B", 0.20), ("C", 0.12), ("D", 0.05), ("F", 0.03)
        ])
        
        headers_present = []
        all_headers = ["HSTS", "X-Content-Type-Options", "X-Frame-Options", "CSP", "X-XSS-Protection", "Referrer-Policy"]
        for h in all_headers:
            if self._rng.random() > 0.30:
                headers_present.append(h)
        
        raw_data = {
            "domain": self.kwargs.get("domain", f"example-{self._random_id().lower()}.com"),
            "tls_analysis": {
                "grade": tls_grade,
                "protocol_support": {
                    "tls13": self._rng.random() > 0.30,
                    "tls12": True,
                    "tls11": self._rng.random() < 0.20,
                    "tls10": self._rng.random() < 0.10,
                },
                "certificate": {
                    "valid": True,
                    "days_to_expiry": self._rng.randint(10, 365),
                    "issuer": self._weighted_choice([
                        ("Let's Encrypt", 0.40), ("DigiCert", 0.20), ("Comodo", 0.15),
                        ("GlobalSign", 0.10), ("Other", 0.15)
                    ]),
                },
                "vulnerabilities": {
                    "heartbleed": False,
                    "poodle": self._rng.random() < 0.05,
                    "beast": self._rng.random() < 0.08,
                },
            },
            "security_headers": {
                "present": headers_present,
                "missing": [h for h in all_headers if h not in headers_present],
                "score": len(headers_present) / len(all_headers) * 100,
            },
            "dns_security": {
                "dnssec_enabled": self._rng.random() > 0.60,
                "caa_record": self._rng.random() > 0.50,
            },
            "email_security": {
                "spf": self._weighted_choice([("Pass", 0.80), ("Softfail", 0.10), ("Fail", 0.05), ("None", 0.05)]),
                "dkim": self._rng.random() > 0.70,
                "dmarc": self._weighted_choice([("Reject", 0.25), ("Quarantine", 0.30), ("None", 0.30), ("Not Set", 0.15)]),
            },
            "infrastructure": {
                "waf_detected": self._rng.random() > 0.40,
                "waf_vendor": self._weighted_choice([
                    ("Cloudflare", 0.30), ("AWS WAF", 0.20), ("Akamai", 0.15),
                    ("Imperva", 0.10), ("Other", 0.15), (None, 0.10)
                ]) if self._rng.random() > 0.40 else None,
                "cdn_detected": self._rng.random() > 0.50,
                "cdn_vendor": self._weighted_choice([
                    ("Cloudflare", 0.35), ("AWS CloudFront", 0.25), ("Akamai", 0.15),
                    ("Fastly", 0.10), ("Other", 0.15)
                ]) if self._rng.random() > 0.50 else None,
                "cloud_provider": self._weighted_choice([
                    ("AWS", 0.40), ("Azure", 0.25), ("GCP", 0.15),
                    ("On-Premise", 0.15), ("Other", 0.05)
                ]),
            },
            "exposed_services": {
                "total_open_ports": self._rng.randint(2, 20),
                "high_risk_ports": self._rng.randint(0, 3),
                "exposed_admin_panels": self._rng.random() < 0.10,
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="scan",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "tls_grade": tls_grade,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class CVEExposureExtractor(DataExtractor):
    """
    CVE Exposure Analysis - Known vulnerabilities in detected software.
    
    Signals: cve_exposure, software_currency
    
    Alternative Sources:
    - NVD: cves/search
    - VulnDB: vulnerabilities/by_product
    - Wappalyzer: lookup
    """
    source_name = "cve_exposure"
    coverage = "cyber"
    signals = ["cve_exposure", "software_currency"]
    ttl_config = TTLConfig.dynamic("CVE data updated daily")
    
    alternative_sources = [
        DataSource("api", "nvd", "cves/search", priority=1),
        DataSource("api", "vulndb", "vulnerabilities/by_product", priority=2),
        DataSource("api", "wappalyzer", "lookup", priority=3),
        DataSource("correlation", "internal", "version_to_cve_mapper", priority=4),
    ]

    def extract(self) -> ExtractionResult:
        num_critical = self._weighted_choice([(0, 0.60), (1, 0.20), (2, 0.12), (self._rng.randint(3, 8), 0.08)])
        num_high = self._weighted_choice([(0, 0.40), (self._rng.randint(1, 5), 0.35), (self._rng.randint(6, 15), 0.25)])
        
        technologies = [
            {"name": "Apache", "version": f"2.4.{self._rng.randint(40, 58)}", "category": "Web Server"},
            {"name": "nginx", "version": f"1.{self._rng.randint(18, 25)}.{self._rng.randint(0, 5)}", "category": "Web Server"},
            {"name": "PHP", "version": f"{self._rng.choice([7, 8])}.{self._rng.randint(0, 4)}.{self._rng.randint(0, 30)}", "category": "Runtime"},
            {"name": "WordPress", "version": f"6.{self._rng.randint(0, 4)}", "category": "CMS"},
            {"name": "jQuery", "version": f"3.{self._rng.randint(5, 7)}.{self._rng.randint(0, 1)}", "category": "JavaScript"},
        ]
        
        detected = self._rng.sample(technologies, self._rng.randint(2, 5))
        
        raw_data = {
            "domain": self.kwargs.get("domain", f"example-{self._random_id().lower()}.com"),
            "vulnerability_summary": {
                "critical": num_critical,
                "high": num_high,
                "medium": self._rng.randint(0, 20),
                "low": self._rng.randint(0, 50),
                "total": num_critical + num_high + self._rng.randint(0, 70),
            },
            "detected_technologies": detected,
            "outdated_software": {
                "count": self._rng.randint(0, len(detected)),
                "components": [t["name"] for t in detected if self._rng.random() < 0.30],
            },
            "patching_analysis": {
                "mean_time_to_patch_days": self._rng.randint(7, 90),
                "unpatched_critical_days": self._rng.randint(0, 60) if num_critical > 0 else 0,
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "critical_cves": num_critical,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class BreachDatabaseExtractor(DataExtractor):
    """
    Breach Database - Historical breaches, regulatory notifications.
    
    Signals: breach_history, regulatory_action, credential_exposure
    
    Alternative Sources:
    - HHS Breach Portal: breaches/search
    - PrivacyRights: breaches/search
    - HaveIBeenPwned: breaches/domain
    - GDPR Tracker: fines/search
    """
    source_name = "breach_database"
    coverage = "cyber"
    signals = ["breach_history", "regulatory_action", "credential_exposure"]
    ttl_config = TTLConfig.dynamic("Breach data updated daily")
    
    alternative_sources = [
        DataSource("api", "hhs_breach_portal", "breaches/search", priority=1),
        DataSource("api", "privacyrights", "breaches/search", priority=1),
        DataSource("api", "haveibeenpwned", "breaches/domain", priority=2),
        DataSource("api", "gdpr_tracker", "fines/search", priority=3),
        DataSource("news", "gdelt", "data breach {company}", priority=4),
    ]

    def extract(self) -> ExtractionResult:
        num_breaches = self._weighted_choice([(0, 0.70), (1, 0.18), (2, 0.08), (self._rng.randint(3, 5), 0.04)])
        
        breaches = []
        total_records = 0
        
        for _ in range(num_breaches):
            records = self._weighted_choice([
                (self._rng.randint(100, 10000), 0.50),
                (self._rng.randint(10000, 100000), 0.30),
                (self._rng.randint(100000, 1000000), 0.15),
                (self._rng.randint(1000000, 10000000), 0.05),
            ])
            total_records += records
            
            breaches.append({
                "date": self._random_date(1825, 30),
                "records_exposed": records,
                "data_types": self._rng.sample(
                    ["Email", "Password", "SSN", "Credit Card", "Medical", "Financial", "PII"],
                    self._rng.randint(1, 4)
                ),
                "cause": self._weighted_choice([
                    ("External Attack", 0.50), ("Insider", 0.15),
                    ("Lost Device", 0.10), ("Misconfiguration", 0.15), ("Vendor", 0.10)
                ]),
                "notification_required": self._rng.random() > 0.30,
                "regulatory_fine_usd": self._rng.randint(0, 5000000) if self._rng.random() < 0.20 else 0,
            })
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("CO", 10)),
            "breach_history": {
                "total_breaches_5yr": num_breaches,
                "total_records_exposed": total_records,
                "breaches": sorted(breaches, key=lambda x: x["date"], reverse=True),
            },
            "regulatory_actions": {
                "total_fines_usd": sum(b["regulatory_fine_usd"] for b in breaches),
                "consent_decrees": sum(1 for b in breaches if b["regulatory_fine_usd"] > 100000),
                "ftc_actions": self._rng.randint(0, 1) if num_breaches > 0 else 0,
                "state_ag_actions": self._rng.randint(0, 2) if num_breaches > 0 else 0,
            },
            "credential_exposure": {
                "domain_in_breach": self._rng.random() < 0.40,
                "exposed_accounts": self._rng.randint(0, 500) if self._rng.random() < 0.40 else 0,
                "password_exposure": self._rng.random() < 0.20,
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "breaches": num_breaches,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class CyberGovernanceExtractor(DataExtractor):
    """
    Cyber Governance Data - CISO, certifications, policies.
    
    Signals: security_leadership, compliance_badges, security_page, bug_bounty
    
    Alternative Sources:
    - LinkedIn: people/search (CISO)
    - SOC2 Registry: reports/search
    - HackerOne: programs/search
    - Bugcrowd: programs/search
    - Company website scraping
    """
    source_name = "cyber_governance"
    coverage = "cyber"
    signals = ["security_leadership", "compliance_badges", "security_page", "bug_bounty"]
    ttl_config = TTLConfig.semi_static("Governance data updated weekly")
    
    alternative_sources = [
        DataSource("api", "linkedin", "people/search", {"title": ["CISO", "VP Security"]}, priority=1),
        DataSource("api", "soc2_registry", "reports/search", priority=2),
        DataSource("api", "hackerone", "programs/search", priority=3),
        DataSource("api", "bugcrowd", "programs/search", priority=3),
        DataSource("scrape", "company_website", "/security", priority=4),
    ]

    def extract(self) -> ExtractionResult:
        has_ciso = self._rng.random() > 0.35
        
        certifications = []
        all_certs = ["SOC 2 Type II", "SOC 2 Type I", "ISO 27001", "PCI DSS", "HIPAA", "FedRAMP", "GDPR"]
        for cert in all_certs:
            if self._rng.random() > 0.60:
                certifications.append({
                    "certification": cert,
                    "status": self._weighted_choice([("Current", 0.85), ("Expired", 0.10), ("In Progress", 0.05)]),
                    "scope": self._weighted_choice([("Enterprise-wide", 0.60), ("Product/Service", 0.30), ("Partial", 0.10)]),
                    "last_audit": self._random_date(365, 0),
                })
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("CO", 10)),
            "leadership": {
                "has_ciso": has_ciso,
                "ciso_tenure_years": self._rng.randint(1, 10) if has_ciso else None,
                "ciso_reports_to": self._weighted_choice([("CEO", 0.40), ("CIO", 0.35), ("CFO", 0.15), ("Board", 0.10)]) if has_ciso else None,
                "board_cyber_oversight": self._rng.random() > 0.50,
                "security_team_size": self._rng.randint(1, 50) if has_ciso else self._rng.randint(0, 5),
            },
            "certifications": certifications,
            "policies": {
                "security_page_exists": self._rng.random() > 0.40,
                "privacy_policy_comprehensive": self._rng.random() > 0.60,
                "security_txt_present": self._rng.random() > 0.25,
                "bug_bounty_program": self._rng.random() > 0.20,
                "bug_bounty_platform": self._weighted_choice([
                    ("HackerOne", 0.40), ("Bugcrowd", 0.30), ("Internal", 0.30)
                ]) if self._rng.random() > 0.20 else None,
                "incident_response_plan": self._rng.random() > 0.65,
                "business_continuity_plan": self._rng.random() > 0.70,
                "security_awareness_training": self._rng.random() > 0.75,
            },
            "maturity": {
                "level": self._weighted_choice([(1, 0.10), (2, 0.25), (3, 0.40), (4, 0.20), (5, 0.05)]),
                "framework": self._weighted_choice([
                    ("NIST CSF", 0.40), ("ISO 27001", 0.25), ("CIS", 0.15), ("Custom", 0.15), ("None", 0.05)
                ]),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "has_ciso": has_ciso,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class VendorSecurityExtractor(DataExtractor):
    """
    Vendor Security / Third-Party Risk - VRM program, vendor assessment.
    
    Signals: vendor_risk_program, second_degree risk
    
    Alternative Sources:
    - Company disclosures
    - Security questionnaires
    """
    source_name = "vendor_security"
    coverage = "cyber"
    signals = ["vendor_risk_program", "second_degree_risk"]
    ttl_config = TTLConfig.semi_static("Vendor risk data updated weekly")
    
    alternative_sources = [
        DataSource("scrape", "company_website", "/security", priority=1),
        DataSource("api", "clearbit", "company/customers", priority=2),
    ]

    def extract(self) -> ExtractionResult:
        vrm_exists = self._rng.random() > 0.40
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("CO", 10)),
            "program_maturity": {
                "vrm_program_exists": vrm_exists,
                "dedicated_vrm_team": vrm_exists and self._rng.random() > 0.50,
                "automated_monitoring": vrm_exists and self._rng.random() > 0.30,
                "continuous_monitoring": vrm_exists and self._rng.random() > 0.25,
            },
            "assessment_coverage": {
                "vendors_with_data_access": self._rng.randint(20, 200),
                "assessed_12mo_pct": self._rng.randint(40, 100) if vrm_exists else self._rng.randint(0, 30),
                "critical_assessed_pct": self._rng.randint(70, 100) if vrm_exists else self._rng.randint(20, 60),
            },
            "vendor_inventory": {
                "total": self._rng.randint(50, 500),
                "critical": self._rng.randint(5, 30),
                "high_risk": self._rng.randint(10, 50),
                "by_category": {
                    "Cloud/SaaS": self._rng.randint(20, 100),
                    "Data Processors": self._rng.randint(5, 30),
                    "Professional Services": self._rng.randint(10, 50),
                    "Other": self._rng.randint(15, 100),
                },
            },
            "incident_history": {
                "vendor_breaches_3yr": self._weighted_choice([(0, 0.70), (1, 0.20), (2, 0.10)]),
                "supply_chain_incidents": self._weighted_choice([(0, 0.80), (1, 0.15), (2, 0.05)]),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "vrm_exists": vrm_exists,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class IncidentResponseExtractor(DataExtractor):
    """
    Incident Response Capabilities - IR plan, SOC, retainers.
    
    Signals: ir_capabilities, soc_capabilities
    """
    source_name = "incident_response"
    coverage = "cyber"
    signals = ["ir_capabilities", "soc_capabilities"]
    ttl_config = TTLConfig.semi_static("IR capabilities assessed periodically")
    
    alternative_sources = [
        DataSource("scrape", "company_website", "/security", priority=1),
    ]

    def extract(self) -> ExtractionResult:
        has_soc = self._rng.random() > 0.45
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("CO", 10)),
            "ir_capabilities": {
                "ir_plan_documented": self._rng.random() > 0.60,
                "ir_plan_tested_12mo": self._rng.random() > 0.40,
                "tabletop_exercises_12mo": self._rng.randint(0, 4),
                "ir_retainer": self._rng.random() > 0.35,
                "ir_provider": self._weighted_choice([
                    ("CrowdStrike", 0.25), ("Mandiant", 0.20), ("Secureworks", 0.15),
                    ("Kroll", 0.15), ("Other", 0.20), (None, 0.05)
                ]) if self._rng.random() > 0.35 else None,
            },
            "soc_capabilities": {
                "has_soc": has_soc,
                "soc_type": self._weighted_choice([
                    ("In-House", 0.30), ("Managed (MSSP)", 0.50), ("Hybrid", 0.20)
                ]) if has_soc else None,
                "24x7_coverage": has_soc and self._rng.random() > 0.40,
                "siem_deployed": has_soc and self._rng.random() > 0.80,
                "edr_deployed": self._rng.random() > 0.60,
                "xdr_deployed": self._rng.random() > 0.25,
            },
            "response_metrics": {
                "mttd_hours": self._rng.randint(1, 168),
                "mttr_hours": self._rng.randint(4, 336),
                "incidents_12mo": self._rng.randint(0, 50),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "has_soc": has_soc,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class ThreatIntelligenceExtractor(DataExtractor):
    """
    Threat Intelligence - Dark web monitoring, credential exposure.
    
    Signals: dark_web, credential_exposure
    
    Alternative Sources:
    - Recorded Future: darkweb/search
    - Flashpoint: exposure/search
    - SpyCloud: breach/domain
    """
    source_name = "threat_intelligence"
    coverage = "cyber"
    signals = ["dark_web", "credential_exposure"]
    ttl_config = TTLConfig.dynamic("Threat intel updated daily")
    
    alternative_sources = [
        DataSource("api", "recorded_future", "darkweb/search", priority=1),
        DataSource("api", "flashpoint", "exposure/search", priority=2),
        DataSource("api", "spycloud", "breach/domain", priority=3),
    ]

    def extract(self) -> ExtractionResult:
        mentions = self._weighted_choice([(0, 0.50), (self._rng.randint(1, 20), 0.35), (self._rng.randint(21, 100), 0.15)])
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("CO", 10)),
            "dark_web_monitoring": {
                "mentions_90d": mentions,
                "data_for_sale": self._rng.random() < 0.08,
                "credential_dumps": self._rng.randint(0, 5) if mentions > 10 else 0,
                "threat_actor_interest": self._weighted_choice([
                    ("Low", 0.70), ("Medium", 0.20), ("High", 0.08), ("Critical", 0.02)
                ]),
            },
            "credential_exposure": {
                "total_exposed_credentials": self._rng.randint(0, 1000),
                "executives_exposed": self._rng.randint(0, 10),
                "recent_exposure_30d": self._rng.random() < 0.15,
            },
            "brand_monitoring": {
                "phishing_domains_detected": self._rng.randint(0, 20),
                "lookalike_domains": self._rng.randint(0, 50),
                "social_media_impersonation": self._rng.random() < 0.10,
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="api",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "mentions": mentions,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class CyberInsuranceHistoryExtractor(DataExtractor):
    """
    Cyber Insurance History - Prior coverage, claims.
    
    Signals: insurance_history, claims_history
    """
    source_name = "cyber_insurance_history"
    coverage = "cyber"
    signals = ["insurance_history", "claims_history"]
    ttl_config = TTLConfig.semi_static("Insurance history updated periodically")
    
    alternative_sources = [
        DataSource("internal", "placement_history", priority=1),
    ]

    def extract(self) -> ExtractionResult:
        years_coverage = self._weighted_choice([(0, 0.20), (self._rng.randint(1, 3), 0.40), (self._rng.randint(4, 10), 0.40)])
        
        claims = []
        num_claims = self._weighted_choice([(0, 0.75), (1, 0.15), (2, 0.07), (self._rng.randint(3, 5), 0.03)])
        
        for _ in range(num_claims):
            claims.append({
                "year": self._rng.randint(2018, 2024),
                "type": self._weighted_choice([
                    ("Ransomware", 0.35), ("Data Breach", 0.30),
                    ("BEC", 0.15), ("System Failure", 0.10), ("Other", 0.10)
                ]),
                "incurred_usd": self._weighted_choice([
                    (self._rng.randint(10000, 100000), 0.50),
                    (self._rng.randint(100000, 500000), 0.30),
                    (self._rng.randint(500000, 2000000), 0.15),
                    (self._rng.randint(2000000, 10000000), 0.05),
                ]),
                "status": self._weighted_choice([("Closed", 0.70), ("Open", 0.30)]),
            })
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("CO", 10)),
            "coverage_history": {
                "years_with_coverage": years_coverage,
                "current_limit_usd": self._rng.choice([1000000, 2000000, 5000000, 10000000, 25000000]) if years_coverage > 0 else 0,
                "current_retention_usd": self._rng.choice([10000, 25000, 50000, 100000, 250000]) if years_coverage > 0 else 0,
                "coverage_continuous": years_coverage > 2 and self._rng.random() > 0.10,
            },
            "claims_history": {
                "total_claims_5yr": num_claims,
                "total_incurred_usd": sum(c["incurred_usd"] for c in claims),
                "claims": claims,
                "loss_ratio": round(sum(c["incurred_usd"] for c in claims) / max(years_coverage * 50000, 1), 3),
            },
        }
        
        self._last_fetch = datetime.now()
        return ExtractionResult(
            source=self.source_name,
            source_type="internal",
            timestamp=datetime.now().isoformat(),
            raw_data=raw_data,
            ttl_config=self.ttl_config,
            metadata={
                "claims": num_claims,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )
