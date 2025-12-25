"""
Cyber Stub Extractors - Technical Infrastructure Signal Group

Extractors for technical security signals that assess observable
security implementation and vulnerability exposure.

Signals covered:
- tls_score: TLS/SSL configuration quality
- security_headers: HTTP security headers
- email_auth: Email authentication (SPF/DMARC/DKIM)
- dnssec: DNSSEC implementation
- exposure: Network exposure (open ports, services)
- software_currency: Software version freshness
- cve_exposure: Known vulnerability exposure
- cloud_infrastructure: Cloud provider and configuration
- waf_presence: Web Application Firewall detection
- cdn_usage: CDN usage (DDoS protection indicator)
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import random

from ...base import StubExtractor, utcnow


class TLSConfigExtractor(StubExtractor):
    """
    STUB: Simulates TLS/SSL configuration scanning.
    
    Real implementation would use SSL Labs methodology:
    - Certificate validity and chain
    - Protocol versions supported
    - Cipher suite quality
    - Key exchange strength
    - Known vulnerabilities (BEAST, POODLE, etc.)
    
    Source: SSL Labs API, direct TLS scanning
    """
    SOURCE_NAME = "ssl_labs_scan"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_tls = self._random_bool(0.95)
        
        if has_tls:
            grade = self._random_choice(["A+", "A", "A-", "B", "C", "D", "F"], 
                                        weights=[0.15, 0.25, 0.15, 0.20, 0.15, 0.07, 0.03])
            grade_scores = {"A+": 100, "A": 95, "A-": 90, "B": 75, "C": 60, "D": 40, "F": 20}
            score = grade_scores.get(grade, 50)
        else:
            grade = None
            score = 0
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "has_tls": has_tls,
                "ssl_labs_grade": grade,
                "ssl_labs_score": score,
                "certificate_valid": self._random_bool(0.95) if has_tls else False,
                "certificate_days_remaining": self._random_int(10, 365) if has_tls else 0,
                "supports_tls13": self._random_bool(0.6) if has_tls else False,
                "supports_tls12": self._random_bool(0.95) if has_tls else False,
                "supports_deprecated_protocols": self._random_bool(0.15) if has_tls else False,
                "has_weak_ciphers": self._random_bool(0.1) if has_tls else False,
                "has_forward_secrecy": self._random_bool(0.85) if has_tls else False,
                "has_hsts": self._random_bool(0.6) if has_tls else False,
                "certificate_type": self._random_choice(["EV", "OV", "DV"]) if has_tls else None,
                "known_vulnerabilities": self._random_int(0, 3) if has_tls else 0,
            }
        }
        return self._create_success_result(data)


class SecurityHeadersExtractor(StubExtractor):
    """
    STUB: Simulates HTTP security headers analysis.
    
    Real implementation would check:
    - HSTS (Strict-Transport-Security)
    - CSP (Content-Security-Policy)
    - X-Frame-Options
    - X-Content-Type-Options
    - X-XSS-Protection
    - Referrer-Policy
    - Permissions-Policy
    
    Source: HTTP response header analysis
    """
    SOURCE_NAME = "security_headers_scan"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    HEADERS = [
        "strict-transport-security",
        "content-security-policy",
        "x-frame-options",
        "x-content-type-options",
        "x-xss-protection",
        "referrer-policy",
        "permissions-policy"
    ]
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        # Randomly determine which headers are present
        headers_present = {}
        for header in self.HEADERS:
            headers_present[header] = self._random_bool(0.5)
        
        present_count = sum(headers_present.values())
        score = (present_count / len(self.HEADERS)) * 100
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "headers_present": headers_present,
                "total_headers_checked": len(self.HEADERS),
                "headers_present_count": present_count,
                "security_headers_score": round(score, 1),
                "has_hsts": headers_present.get("strict-transport-security", False),
                "has_csp": headers_present.get("content-security-policy", False),
                "has_xfo": headers_present.get("x-frame-options", False),
                "csp_quality": self._random_choice(["STRICT", "MODERATE", "BASIC", "NONE"]) if headers_present.get("content-security-policy") else "NONE",
                "grade": self._random_choice(["A", "B", "C", "D", "F"]),
            }
        }
        return self._create_success_result(data)


class EmailAuthExtractor(StubExtractor):
    """
    STUB: Simulates email authentication record analysis.
    
    Real implementation would check DNS for:
    - SPF record presence and strictness
    - DMARC record and policy
    - DKIM selector presence
    - MX record configuration
    
    Source: DNS lookups
    """
    SOURCE_NAME = "email_auth_scan"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_spf = self._random_bool(0.75)
        has_dmarc = self._random_bool(0.55)
        has_dkim = self._random_bool(0.60)
        
        # DMARC policies
        if has_dmarc:
            dmarc_policy = self._random_choice(["reject", "quarantine", "none"], weights=[0.3, 0.35, 0.35])
        else:
            dmarc_policy = None
        
        # SPF strictness
        if has_spf:
            spf_qualifier = self._random_choice(["-all", "~all", "?all"], weights=[0.4, 0.45, 0.15])
        else:
            spf_qualifier = None
        
        # Calculate score
        score = 0
        if has_spf:
            score += 30 if spf_qualifier == "-all" else 20
        if has_dmarc:
            if dmarc_policy == "reject":
                score += 40
            elif dmarc_policy == "quarantine":
                score += 30
            else:
                score += 15
        if has_dkim:
            score += 30
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "has_spf": has_spf,
                "spf_qualifier": spf_qualifier,
                "spf_valid": self._random_bool(0.9) if has_spf else False,
                "has_dmarc": has_dmarc,
                "dmarc_policy": dmarc_policy,
                "dmarc_pct": self._random_choice([100, 50, 25, 10]) if has_dmarc else None,
                "dmarc_rua_configured": self._random_bool(0.7) if has_dmarc else False,
                "has_dkim": has_dkim,
                "dkim_selectors_found": self._random_int(1, 3) if has_dkim else 0,
                "email_auth_score": min(100, score),
                "email_security_grade": self._random_choice(["A", "B", "C", "D", "F"]),
            }
        }
        return self._create_success_result(data)


class DNSSECExtractor(StubExtractor):
    """
    STUB: Simulates DNSSEC implementation check.
    
    Real implementation would check:
    - DNSSEC signed zone
    - DS record presence
    - RRSIG validity
    - Key algorithm strength
    
    Source: DNS lookups with DNSSEC validation
    """
    SOURCE_NAME = "dnssec_check"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_dnssec = self._random_bool(0.25)  # DNSSEC adoption is still relatively low
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "dnssec_enabled": has_dnssec,
                "ds_record_present": has_dnssec,
                "rrsig_valid": self._random_bool(0.95) if has_dnssec else False,
                "key_algorithm": self._random_choice(["RSASHA256", "ECDSAP256SHA256", "ED25519"]) if has_dnssec else None,
                "chain_valid": self._random_bool(0.9) if has_dnssec else False,
                "dnssec_score": 100 if has_dnssec and self._random_bool(0.9) else (0 if not has_dnssec else 50),
            }
        }
        return self._create_success_result(data)


class NetworkExposureExtractor(StubExtractor):
    """
    STUB: Simulates network exposure scanning (Shodan/Censys style).
    
    Real implementation would scan for:
    - Open ports and services
    - Exposed admin interfaces
    - Default credentials indicators
    - Unencrypted services
    - Database exposure
    
    Source: Shodan, Censys, direct scanning
    """
    SOURCE_NAME = "network_exposure_scan"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    RISKY_SERVICES = ["RDP", "VNC", "Telnet", "FTP", "SMB", "MongoDB", "Redis", "Elasticsearch"]
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        open_port_count = self._random_int(2, 30)
        risky_services = self._random_int(0, 5)
        
        # Calculate exposure score (higher = safer)
        base_score = 100
        base_score -= risky_services * 15
        base_score -= max(0, open_port_count - 5) * 2
        exposure_score = max(0, min(100, base_score))
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "total_open_ports": open_port_count,
                "risky_service_count": risky_services,
                "exposed_services": self._random_sample(self.RISKY_SERVICES, risky_services),
                "has_exposed_rdp": self._random_bool(0.1),
                "has_exposed_database": self._random_bool(0.08),
                "has_exposed_admin": self._random_bool(0.12),
                "has_default_credentials_indicator": self._random_bool(0.05),
                "unencrypted_service_count": self._random_int(0, 3),
                "ip_count": self._random_int(1, 50),
                "exposure_score": exposure_score,
                "exposure_rating": "CRITICAL" if exposure_score < 30 else "HIGH" if exposure_score < 50 else "MODERATE" if exposure_score < 70 else "LOW",
            }
        }
        return self._create_success_result(data)


class SoftwareCurrencyExtractor(StubExtractor):
    """
    STUB: Simulates software version freshness analysis.
    
    Real implementation would fingerprint:
    - Web server versions
    - CMS versions (WordPress, etc.)
    - JavaScript library versions
    - Framework versions
    
    Source: HTTP headers, HTML analysis, fingerprinting
    """
    SOURCE_NAME = "software_fingerprint"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        components_detected = self._random_int(3, 15)
        outdated_count = self._random_int(0, min(8, components_detected))
        severely_outdated = self._random_int(0, min(3, outdated_count))
        
        # Score based on outdated percentage
        outdated_pct = outdated_count / components_detected if components_detected > 0 else 0
        currency_score = max(0, 100 - (outdated_pct * 60) - (severely_outdated * 15))
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "components_detected": components_detected,
                "outdated_components": outdated_count,
                "severely_outdated_components": severely_outdated,
                "outdated_percentage": round(outdated_pct * 100, 1),
                "web_server_current": self._random_bool(0.7),
                "cms_current": self._random_bool(0.6),
                "js_libraries_current": self._random_bool(0.5),
                "oldest_component_age_days": self._random_int(0, 1000),
                "currency_score": round(currency_score, 1),
                "update_hygiene": self._random_choice(["EXCELLENT", "GOOD", "FAIR", "POOR", "CRITICAL"]),
            }
        }
        return self._create_success_result(data)


class CVEExposureExtractor(StubExtractor):
    """
    STUB: Simulates CVE exposure analysis.
    
    Real implementation would:
    - Match detected software versions to CVE database
    - Check for critical/high severity CVEs
    - Identify exploited-in-wild vulnerabilities
    - Calculate CVSS-based risk score
    
    Source: NVD, software fingerprinting, version matching
    """
    SOURCE_NAME = "cve_analysis"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        total_cves = self._random_int(0, 50)
        critical_cves = self._random_int(0, min(5, total_cves))
        high_cves = self._random_int(0, min(15, total_cves - critical_cves))
        exploited_in_wild = self._random_int(0, min(3, critical_cves + high_cves))
        
        # Score calculation (higher = safer)
        score = 100
        score -= critical_cves * 20
        score -= high_cves * 8
        score -= exploited_in_wild * 15
        cve_score = max(0, min(100, score))
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "total_cves_detected": total_cves,
                "critical_cves": critical_cves,
                "high_cves": high_cves,
                "medium_cves": self._random_int(0, 20),
                "low_cves": self._random_int(0, 15),
                "exploited_in_wild_count": exploited_in_wild,
                "kev_matches": exploited_in_wild,  # CISA KEV catalog
                "average_cvss": self._random_float(3.0, 9.0) if total_cves > 0 else 0,
                "max_cvss": self._random_float(7.0, 10.0) if critical_cves > 0 else self._random_float(4.0, 7.0) if total_cves > 0 else 0,
                "cve_exposure_score": round(cve_score, 1),
                "patch_urgency": "CRITICAL" if critical_cves > 0 else "HIGH" if high_cves > 2 else "MODERATE" if total_cves > 5 else "LOW",
            }
        }
        return self._create_success_result(data)


class CloudInfraExtractor(StubExtractor):
    """
    STUB: Simulates cloud infrastructure detection.
    
    Real implementation would detect:
    - Cloud provider (AWS, Azure, GCP)
    - S3/blob storage exposure
    - Cloud security configuration indicators
    - Multi-cloud usage
    
    Source: DNS analysis, IP ranges, HTTP headers
    """
    SOURCE_NAME = "cloud_detection"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    CLOUD_PROVIDERS = ["AWS", "Azure", "GCP", "DigitalOcean", "Cloudflare", "Heroku"]
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        uses_cloud = self._random_bool(0.85)
        
        if uses_cloud:
            primary_provider = self._random_choice(self.CLOUD_PROVIDERS[:3], weights=[0.5, 0.3, 0.2])
            provider_tier = 1 if primary_provider in ["AWS", "Azure", "GCP"] else 2
            multi_cloud = self._random_bool(0.3)
        else:
            primary_provider = None
            provider_tier = None
            multi_cloud = False
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "uses_cloud_hosting": uses_cloud,
                "primary_provider": primary_provider,
                "provider_tier": provider_tier,
                "is_multi_cloud": multi_cloud,
                "cloud_providers_detected": [primary_provider] + (self._random_sample(self.CLOUD_PROVIDERS, 1) if multi_cloud else []) if uses_cloud else [],
                "has_exposed_storage": self._random_bool(0.05),
                "serverless_detected": self._random_bool(0.3) if uses_cloud else False,
                "container_orchestration_detected": self._random_bool(0.25) if uses_cloud else False,
                "cloud_maturity_indicators": self._random_int(0, 5) if uses_cloud else 0,
                "cloud_security_score": self._random_float(50, 95) if uses_cloud else 50,
            }
        }
        return self._create_success_result(data)


class WAFPresenceExtractor(StubExtractor):
    """
    STUB: Simulates Web Application Firewall detection.
    
    Real implementation would detect:
    - WAF presence via response patterns
    - WAF provider identification
    - WAF configuration indicators
    
    Source: HTTP response analysis, fingerprinting
    """
    SOURCE_NAME = "waf_detection"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    WAF_PROVIDERS = ["Cloudflare", "AWS WAF", "Akamai", "Imperva", "F5", "Fortinet", "ModSecurity"]
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        has_waf = self._random_bool(0.45)
        
        if has_waf:
            provider = self._random_choice(self.WAF_PROVIDERS)
            tier = 1 if provider in ["Cloudflare", "AWS WAF", "Akamai", "Imperva"] else 2
        else:
            provider = None
            tier = None
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "waf_detected": has_waf,
                "waf_provider": provider,
                "waf_tier": tier,
                "blocking_mode_detected": self._random_bool(0.7) if has_waf else False,
                "bot_protection_detected": self._random_bool(0.6) if has_waf else False,
                "ddos_protection_indicator": self._random_bool(0.8) if has_waf else False,
                "waf_score": 100 if has_waf else 0,
            }
        }
        return self._create_success_result(data)


class CDNUsageExtractor(StubExtractor):
    """
    STUB: Simulates CDN detection.
    
    Real implementation would detect:
    - CDN provider
    - Geographic distribution
    - DDoS protection capabilities
    
    Source: DNS analysis, HTTP headers, response patterns
    """
    SOURCE_NAME = "cdn_detection"
    DEFAULT_TTL_SECONDS = StubExtractor.TTL_DAILY
    
    CDN_PROVIDERS = ["Cloudflare", "Akamai", "Fastly", "AWS CloudFront", "Azure CDN", "Google Cloud CDN"]
    
    def _do_extract(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        uses_cdn = self._random_bool(0.55)
        
        if uses_cdn:
            provider = self._random_choice(self.CDN_PROVIDERS)
            has_ddos_protection = provider in ["Cloudflare", "Akamai", "AWS CloudFront"]
        else:
            provider = None
            has_ddos_protection = False
        
        data = {
            "query_timestamp": utcnow().isoformat(),
            "entity_id": entity_id,
            "data": {
                "cdn_detected": uses_cdn,
                "cdn_provider": provider,
                "has_ddos_protection": has_ddos_protection,
                "geographic_distribution": self._random_choice(["GLOBAL", "REGIONAL", "SINGLE"]) if uses_cdn else None,
                "edge_locations_indicator": self._random_choice(["HIGH", "MEDIUM", "LOW"]) if uses_cdn else None,
                "cdn_score": 100 if uses_cdn else 0,
            }
        }
        return self._create_success_result(data)
