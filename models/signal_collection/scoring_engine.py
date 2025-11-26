"""
Digital Signal Intelligence - Signal Scoring Engine
====================================================

This module provides the CRITICAL missing bridge between raw data collection
and the numerical scores (0-100) that pricing models require.

Each signal category has explicit scoring rubrics that transform observations
into actuarially meaningful scores.

Author: John Walker
Date: November 2025
Version: 1.0
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import re
import json


class SignalConfidence(Enum):
   """Confidence level in a signal score"""
   HIGH = "high"          # Direct measurement, authoritative source
   MEDIUM = "medium"      # Inferred from multiple indicators
   LOW = "low"            # Single indicator or heuristic
   UNAVAILABLE = "unavailable"  # Could not determine


@dataclass
class ScoredSignal:
   """A signal with its score, confidence, and evidence"""
   signal_name: str
   raw_value: Any
   score: float  # 0-100
   confidence: SignalConfidence
   evidence: List[str]
   scoring_method: str
   timestamp: datetime = field(default_factory=datetime.now)
   
   def to_dict(self) -> Dict:
       return {
           "signal_name": self.signal_name,
           "raw_value": str(self.raw_value),
           "score": self.score,
           "confidence": self.confidence.value,
           "evidence": self.evidence,
           "scoring_method": self.scoring_method,
           "timestamp": self.timestamp.isoformat()
       }


class SSLScorer:
   """
   Scores SSL/TLS implementation quality
   
   Scoring Rubric:
   - Grade A+ (TLS 1.3, HSTS, perfect config): 95-100
   - Grade A (TLS 1.3 or 1.2, good config): 85-94
   - Grade B (TLS 1.2, minor issues): 70-84
   - Grade C (older TLS, some vulnerabilities): 50-69
   - Grade D/E (significant vulnerabilities): 25-49
   - Grade F or no HTTPS: 0-24
   """
   
   GRADE_SCORES = {
       "A+": 98,
       "A": 90,
       "A-": 85,
       "B+": 80,
       "B": 75,
       "B-": 70,
       "C+": 65,
       "C": 55,
       "C-": 50,
       "D": 35,
       "E": 20,
       "F": 5,
       "T": 0,  # Trust issues
   }
   
   TLS_VERSION_SCORES = {
       "TLSv1.3": 100,
       "TLSv1.2": 85,
       "TLSv1.1": 40,  # Deprecated
       "TLSv1.0": 20,  # Deprecated
       "SSLv3": 5,     # Insecure
       "SSLv2": 0,     # Critical vulnerability
   }
   
   def score_from_ssl_labs(self, ssl_labs_result: Dict) -> ScoredSignal:
       """Score from SSL Labs API response"""
       evidence = []
       
       # Extract grade
       grade = ssl_labs_result.get("grade", "F")
       base_score = self.GRADE_SCORES.get(grade, 0)
       evidence.append(f"SSL Labs Grade: {grade}")
       
       # Adjust for protocol support
       protocols = ssl_labs_result.get("protocols", [])
       if "TLSv1.3" in protocols:
           base_score = min(100, base_score + 5)
           evidence.append("TLS 1.3 supported")
       if "TLSv1.0" in protocols or "SSLv3" in protocols:
           base_score = max(0, base_score - 15)
           evidence.append("Legacy protocols still enabled (penalty)")
       
       # Check for HSTS
       if ssl_labs_result.get("hstsPolicy", {}).get("status") == "present":
           base_score = min(100, base_score + 3)
           evidence.append("HSTS enabled")
       
       # Check for known vulnerabilities
       vulns = ssl_labs_result.get("vulnerabilities", {})
       if vulns.get("heartbleed"):
           base_score = max(0, base_score - 50)
           evidence.append("CRITICAL: Heartbleed vulnerable")
       if vulns.get("poodle"):
           base_score = max(0, base_score - 20)
           evidence.append("POODLE vulnerable")
       
       return ScoredSignal(
           signal_name="ssl_certificate",
           raw_value=grade,
           score=base_score,
           confidence=SignalConfidence.HIGH,
           evidence=evidence,
           scoring_method="ssl_labs_api"
       )
   
   def score_from_headers(self, headers: Dict[str, str], url: str) -> ScoredSignal:
       """Score based on observed headers when SSL Labs unavailable"""
       evidence = []
       score = 50  # Base score for having HTTPS
       
       if not url.startswith("https://"):
           return ScoredSignal(
               signal_name="ssl_certificate",
               raw_value="no_https",
               score=0,
               confidence=SignalConfidence.HIGH,
               evidence=["Site does not use HTTPS"],
               scoring_method="header_analysis"
           )
       
       evidence.append("HTTPS enabled")
       
       # Check HSTS
       hsts = headers.get("strict-transport-security", "")
       if hsts:
           score += 15
           evidence.append(f"HSTS present: {hsts[:50]}...")
           if "max-age=31536000" in hsts or int(re.search(r'max-age=(\d+)', hsts).group(1) if re.search(r'max-age=(\d+)', hsts) else 0) >= 31536000:
               score += 5
               evidence.append("HSTS max-age >= 1 year")
           if "includeSubDomains" in hsts:
               score += 5
               evidence.append("HSTS includes subdomains")
       
       return ScoredSignal(
           signal_name="ssl_certificate",
           raw_value="https_with_headers",
           score=min(100, score),
           confidence=SignalConfidence.MEDIUM,
           evidence=evidence,
           scoring_method="header_analysis"
       )


class SecurityHeadersScorer:
   """
   Scores security header implementation
   
   Scoring Rubric (each header contributes points):
   - Content-Security-Policy: 0-25 points
   - X-Frame-Options: 0-10 points
   - X-Content-Type-Options: 0-10 points
   - Referrer-Policy: 0-10 points
   - Permissions-Policy: 0-15 points
   - X-XSS-Protection: 0-5 points (deprecated but shows awareness)
   - Strict-Transport-Security: 0-15 points
   - Cache-Control (security): 0-10 points
   """
   
   def score(self, headers: Dict[str, str]) -> ScoredSignal:
       """Score security headers"""
       evidence = []
       total_score = 0
       headers_lower = {k.lower(): v for k, v in headers.items()}
       
       # Content-Security-Policy (25 points max)
       csp = headers_lower.get("content-security-policy", "")
       if csp:
           csp_score = 15  # Base for having CSP
           if "default-src" in csp:
               csp_score += 5
           if "'unsafe-inline'" not in csp and "'unsafe-eval'" not in csp:
               csp_score += 5
           total_score += csp_score
           evidence.append(f"CSP present (+{csp_score})")
       else:
           evidence.append("CSP missing (0)")
       
       # X-Frame-Options (10 points)
       xfo = headers_lower.get("x-frame-options", "")
       if xfo:
           if xfo.upper() in ["DENY", "SAMEORIGIN"]:
               total_score += 10
               evidence.append(f"X-Frame-Options: {xfo} (+10)")
           else:
               total_score += 5
               evidence.append(f"X-Frame-Options: {xfo} (+5)")
       else:
           evidence.append("X-Frame-Options missing (0)")
       
       # X-Content-Type-Options (10 points)
       xcto = headers_lower.get("x-content-type-options", "")
       if xcto and "nosniff" in xcto.lower():
           total_score += 10
           evidence.append("X-Content-Type-Options: nosniff (+10)")
       else:
           evidence.append("X-Content-Type-Options missing (0)")
       
       # Referrer-Policy (10 points)
       rp = headers_lower.get("referrer-policy", "")
       if rp:
           secure_policies = ["no-referrer", "strict-origin", "strict-origin-when-cross-origin", "same-origin"]
           if any(p in rp.lower() for p in secure_policies):
               total_score += 10
               evidence.append(f"Referrer-Policy: {rp} (+10)")
           else:
               total_score += 5
               evidence.append(f"Referrer-Policy: {rp} (+5)")
       else:
           evidence.append("Referrer-Policy missing (0)")
       
       # Permissions-Policy (15 points)
       pp = headers_lower.get("permissions-policy", "") or headers_lower.get("feature-policy", "")
       if pp:
           total_score += 15
           evidence.append(f"Permissions-Policy present (+15)")
       else:
           evidence.append("Permissions-Policy missing (0)")
       
       # HSTS (15 points - also counted in SSL but important here)
       hsts = headers_lower.get("strict-transport-security", "")
       if hsts:
           total_score += 15
           evidence.append(f"HSTS present (+15)")
       else:
           evidence.append("HSTS missing (0)")
       
       # X-XSS-Protection (5 points - deprecated but shows security awareness)
       xxss = headers_lower.get("x-xss-protection", "")
       if xxss and "1" in xxss:
           total_score += 5
           evidence.append("X-XSS-Protection enabled (+5)")
       
       # Cache-Control for sensitive pages (10 points)
       cc = headers_lower.get("cache-control", "")
       if "no-store" in cc.lower() or "private" in cc.lower():
           total_score += 10
           evidence.append("Secure Cache-Control (+10)")
       
       return ScoredSignal(
           signal_name="security_headers",
           raw_value=len([h for h in headers_lower if h in [
               "content-security-policy", "x-frame-options", 
               "x-content-type-options", "strict-transport-security"
           ]]),
           score=total_score,
           confidence=SignalConfidence.HIGH,
           evidence=evidence,
           scoring_method="header_analysis"
       )


class VulnerabilityScorer:
   """
   Scores vulnerability exposure (inverse - fewer vulnerabilities = higher score)
   
   Scoring Rubric:
   - 0 critical CVEs, 0 high: 95-100
   - 0 critical, 1-2 high: 80-94
   - 1 critical or 3+ high: 60-79
   - 2-3 critical: 40-59
   - 4+ critical or known exploits in wild: 0-39
   
   Also considers:
   - Exposed databases (Shodan)
   - Leaked credentials (HIBP)
   - Open ports beyond standard web
   """
   
   def score_from_vulnerability_data(
       self,
       critical_cves: int = 0,
       high_cves: int = 0,
       medium_cves: int = 0,
       exposed_databases: bool = False,
       leaked_credentials: bool = False,
       unusual_open_ports: int = 0,
       known_exploited: bool = False
   ) -> ScoredSignal:
       """Calculate vulnerability score from multiple sources"""
       evidence = []
       score = 100
       
       # Critical CVEs
       if critical_cves == 0:
           evidence.append("No critical CVEs")
       elif critical_cves <= 2:
           score -= critical_cves * 20
           evidence.append(f"{critical_cves} critical CVE(s) (-{critical_cves * 20})")
       else:
           score -= 50 + (critical_cves - 2) * 10
           evidence.append(f"{critical_cves} critical CVEs (severe penalty)")
       
       # High CVEs
       if high_cves <= 2:
           score -= high_cves * 5
           if high_cves > 0:
               evidence.append(f"{high_cves} high severity CVE(s) (-{high_cves * 5})")
       else:
           score -= 15 + (high_cves - 2) * 3
           evidence.append(f"{high_cves} high severity CVEs")
       
       # Medium CVEs (minor impact)
       if medium_cves > 5:
           score -= min(10, (medium_cves - 5))
           evidence.append(f"{medium_cves} medium severity CVEs")
       
       # Exposed databases - critical
       if exposed_databases:
           score -= 35
           evidence.append("CRITICAL: Exposed database detected (-35)")
       
       # Leaked credentials
       if leaked_credentials:
           score -= 25
           evidence.append("Leaked credentials found in breach databases (-25)")
       
       # Unusual open ports
       if unusual_open_ports > 0:
           port_penalty = min(15, unusual_open_ports * 3)
           score -= port_penalty
           evidence.append(f"{unusual_open_ports} unusual open port(s) (-{port_penalty})")
       
       # Known exploited vulnerabilities (CISA KEV)
       if known_exploited:
           score -= 30
           evidence.append("CRITICAL: Known exploited vulnerability (-30)")
       
       return ScoredSignal(
           signal_name="known_vulnerabilities",
           raw_value={
               "critical": critical_cves,
               "high": high_cves,
               "exposed_db": exposed_databases,
               "leaked_creds": leaked_credentials
           },
           score=max(0, score),
           confidence=SignalConfidence.HIGH if critical_cves > 0 or exposed_databases else SignalConfidence.MEDIUM,
           evidence=evidence,
           scoring_method="vulnerability_aggregation"
       )


class GovernanceTransparencyScorer:
   """
   Scores governance and transparency based on website content analysis
   
   Scoring Components:
   - Board/Leadership disclosure: 0-20 points
   - Financial reporting visibility: 0-20 points
   - Risk committee/governance structure: 0-15 points
   - ESG/Sustainability reporting: 0-15 points
   - Regulatory compliance statements: 0-15 points
   - Incident/breach notification history: 0-15 points
   """
   
   GOVERNANCE_KEYWORDS = {
       "board_disclosure": [
           "board of directors", "independent director", "audit committee",
           "compensation committee", "nominating committee", "governance committee",
           "board composition", "director biography", "board members"
       ],
       "financial_reporting": [
           "annual report", "10-k", "10-q", "quarterly report", "financial statements",
           "investor relations", "sec filings", "earnings", "financial results"
       ],
       "risk_governance": [
           "risk committee", "risk management", "chief risk officer", "cro",
           "enterprise risk", "risk oversight", "internal audit", "compliance officer"
       ],
       "esg_sustainability": [
           "sustainability report", "esg", "environmental", "social responsibility",
           "carbon", "climate", "diversity", "inclusion", "dei report"
       ],
       "regulatory_compliance": [
           "compliance", "regulatory", "sox", "sarbanes-oxley", "gdpr", "ccpa",
           "hipaa", "pci dss", "iso 27001", "soc 2", "certified"
       ],
       "incident_transparency": [
           "incident response", "breach notification", "security incident",
           "data protection", "privacy policy", "cookie policy"
       ]
   }
   
   def score_from_content(self, page_content: str, pages_analyzed: int = 1) -> ScoredSignal:
       """Score governance based on website content"""
       content_lower = page_content.lower()
       evidence = []
       scores = {}
       
       for category, keywords in self.GOVERNANCE_KEYWORDS.items():
           found = [kw for kw in keywords if kw in content_lower]
           if category == "board_disclosure":
               max_points = 20
           elif category == "financial_reporting":
               max_points = 20
           elif category == "risk_governance":
               max_points = 15
           elif category == "esg_sustainability":
               max_points = 15
           elif category == "regulatory_compliance":
               max_points = 15
           else:
               max_points = 15
           
           # Score based on keyword coverage
           coverage = len(found) / len(keywords)
           category_score = min(max_points, int(coverage * max_points * 1.5))
           scores[category] = category_score
           
           if found:
               evidence.append(f"{category}: found {len(found)} indicators (+{category_score})")
           else:
               evidence.append(f"{category}: no indicators found (0)")
       
       total_score = sum(scores.values())
       
       # Confidence based on pages analyzed
       if pages_analyzed >= 10:
           confidence = SignalConfidence.HIGH
       elif pages_analyzed >= 5:
           confidence = SignalConfidence.MEDIUM
       else:
           confidence = SignalConfidence.LOW
       
       return ScoredSignal(
           signal_name="governance_disclosure",
           raw_value=scores,
           score=total_score,
           confidence=confidence,
           evidence=evidence,
           scoring_method="content_keyword_analysis"
       )


class TechnologyStackScorer:
   """
   Scores technology stack modernity and security
   
   Factors:
   - Framework/CMS currency (up-to-date vs outdated)
   - Known vulnerable versions
   - Security-focused technologies
   - Cloud provider quality
   """
   
   MODERN_TECHNOLOGIES = {
       "frameworks": ["react", "vue", "angular", "next.js", "nuxt", "svelte"],
       "security": ["cloudflare", "akamai", "fastly", "aws shield", "recaptcha"],
       "cloud": ["aws", "azure", "google cloud", "gcp"],
       "modern_cms": ["wordpress 6", "drupal 10", "contentful", "strapi"]
   }
   
   OUTDATED_TECHNOLOGIES = {
       "legacy_frameworks": ["jquery 1.", "angular.js", "backbone"],
       "outdated_cms": ["wordpress 4", "drupal 7", "joomla 2"],
       "insecure": ["flash", "silverlight", "java applet"],
       "deprecated": ["php 5", "python 2", "node 12", "node 10"]
   }
   
   def score_from_tech_stack(self, technologies: List[str]) -> ScoredSignal:
       """Score based on detected technologies"""
       evidence = []
       score = 50  # Neutral baseline
       tech_lower = [t.lower() for t in technologies]
       
       # Check for modern technologies
       for category, techs in self.MODERN_TECHNOLOGIES.items():
           found = [t for t in techs if any(t in tech for tech in tech_lower)]
           if found:
               bonus = min(15, len(found) * 5)
               score += bonus
               evidence.append(f"Modern {category}: {', '.join(found)} (+{bonus})")
       
       # Check for outdated/insecure technologies
       for category, techs in self.OUTDATED_TECHNOLOGIES.items():
           found = [t for t in techs if any(t in tech for tech in tech_lower)]
           if found:
               penalty = min(25, len(found) * 10)
               score -= penalty
               evidence.append(f"Outdated {category}: {', '.join(found)} (-{penalty})")
       
       return ScoredSignal(
           signal_name="tech_stack_modernity",
           raw_value=technologies,
           score=max(0, min(100, score)),
           confidence=SignalConfidence.MEDIUM,
           evidence=evidence,
           scoring_method="technology_detection"
       )


class DomainAuthorityScorer:
   """
   Scores domain authority and network position
   
   Uses Moz/Ahrefs-style metrics:
   - Domain Authority (DA): 0-100
   - Trust Flow
   - Citation Flow
   - Referring domains quality
   """
   
   def score_from_seo_metrics(
       self,
       domain_authority: int = 0,
       referring_domains: int = 0,
       trust_flow: int = 0,
       spam_score: int = 0
   ) -> ScoredSignal:
       """Score from SEO tool metrics"""
       evidence = []
       
       # Base score from domain authority
       score = domain_authority
       evidence.append(f"Domain Authority: {domain_authority}")
       
       # Adjust for referring domains
       if referring_domains > 10000:
           score = min(100, score + 10)
           evidence.append(f"Strong backlink profile: {referring_domains:,} referring domains (+10)")
       elif referring_domains > 1000:
           score = min(100, score + 5)
           evidence.append(f"Good backlink profile: {referring_domains:,} referring domains (+5)")
       elif referring_domains < 100:
           score = max(0, score - 10)
           evidence.append(f"Limited backlinks: {referring_domains} referring domains (-10)")
       
       # Trust flow bonus
       if trust_flow > 50:
           score = min(100, score + 5)
           evidence.append(f"High trust flow: {trust_flow} (+5)")
       
       # Spam score penalty
       if spam_score > 30:
           penalty = min(20, spam_score - 30)
           score = max(0, score - penalty)
           evidence.append(f"Elevated spam score: {spam_score} (-{penalty})")
       
       return ScoredSignal(
           signal_name="domain_authority",
           raw_value=domain_authority,
           score=score,
           confidence=SignalConfidence.HIGH,
           evidence=evidence,
           scoring_method="seo_metrics"
       )


class UpdateFrequencyScorer:
   """
   Scores website maintenance discipline based on update patterns
   
   Uses Wayback Machine or content freshness indicators
   """
   
   def score_from_wayback_analysis(
       self,
       snapshots_per_year: int,
       days_since_last_change: int,
       major_redesigns_5yr: int
   ) -> ScoredSignal:
       """Score based on Internet Archive analysis"""
       evidence = []
       score = 50
       
       # Update frequency
       if snapshots_per_year > 100:
           score += 25
           evidence.append(f"Very active: {snapshots_per_year} snapshots/year (+25)")
       elif snapshots_per_year > 50:
           score += 15
           evidence.append(f"Active: {snapshots_per_year} snapshots/year (+15)")
       elif snapshots_per_year > 20:
           score += 5
           evidence.append(f"Moderate activity: {snapshots_per_year} snapshots/year (+5)")
       elif snapshots_per_year < 5:
           score -= 20
           evidence.append(f"Low activity: {snapshots_per_year} snapshots/year (-20)")
       
       # Recency of changes
       if days_since_last_change < 7:
           score += 15
           evidence.append("Updated within past week (+15)")
       elif days_since_last_change < 30:
           score += 10
           evidence.append("Updated within past month (+10)")
       elif days_since_last_change > 180:
           score -= 15
           evidence.append(f"No updates in {days_since_last_change} days (-15)")
       elif days_since_last_change > 365:
           score -= 25
           evidence.append("No updates in over a year (-25)")
       
       # Investment in redesigns
       if major_redesigns_5yr >= 2:
           score += 10
           evidence.append(f"{major_redesigns_5yr} redesigns in 5 years (+10)")
       
       return ScoredSignal(
           signal_name="update_frequency",
           raw_value={
               "snapshots_per_year": snapshots_per_year,
               "days_since_change": days_since_last_change
           },
           score=max(0, min(100, score)),
           confidence=SignalConfidence.MEDIUM,
           evidence=evidence,
           scoring_method="wayback_analysis"
       )


class ComprehensiveSignalScorer:
   """
   Unified scoring engine that combines all signal scorers
   """
   
   def __init__(self):
       self.ssl_scorer = SSLScorer()
       self.headers_scorer = SecurityHeadersScorer()
       self.vulnerability_scorer = VulnerabilityScorer()
       self.governance_scorer = GovernanceTransparencyScorer()
       self.tech_scorer = TechnologyStackScorer()
       self.domain_scorer = DomainAuthorityScorer()
       self.update_scorer = UpdateFrequencyScorer()
   
   def score_all_signals(
       self,
       ssl_labs_result: Optional[Dict] = None,
       headers: Optional[Dict[str, str]] = None,
       url: str = "",
       vulnerability_data: Optional[Dict] = None,
       page_content: str = "",
       pages_analyzed: int = 1,
       technologies: Optional[List[str]] = None,
       seo_metrics: Optional[Dict] = None,
       wayback_data: Optional[Dict] = None
   ) -> Dict[str, ScoredSignal]:
       """
       Score all available signals and return comprehensive results
       """
       results = {}
       
       # SSL/TLS
       if ssl_labs_result:
           results["ssl_certificate"] = self.ssl_scorer.score_from_ssl_labs(ssl_labs_result)
       elif headers and url:
           results["ssl_certificate"] = self.ssl_scorer.score_from_headers(headers, url)
       
       # Security Headers
       if headers:
           results["security_headers"] = self.headers_scorer.score(headers)
       
       # Vulnerabilities
       if vulnerability_data:
           results["known_vulnerabilities"] = self.vulnerability_scorer.score_from_vulnerability_data(
               **vulnerability_data
           )
       
       # Governance/Transparency
       if page_content:
           results["governance_disclosure"] = self.governance_scorer.score_from_content(
               page_content, pages_analyzed
           )
       
       # Technology Stack
       if technologies:
           results["tech_stack_modernity"] = self.tech_scorer.score_from_tech_stack(technologies)
       
       # Domain Authority
       if seo_metrics:
           results["domain_authority"] = self.domain_scorer.score_from_seo_metrics(**seo_metrics)
       
       # Update Frequency
       if wayback_data:
           results["update_frequency"] = self.update_scorer.score_from_wayback_analysis(**wayback_data)
       
       return results
   
   def calculate_composite_score(
       self,
       signals: Dict[str, ScoredSignal],
       weights: Optional[Dict[str, float]] = None
   ) -> Tuple[float, float]:
       """
       Calculate weighted composite score
       Returns: (score, confidence_weighted_score)
       """
       if not signals:
           return 0.0, 0.0
       
       default_weights = {
           "ssl_certificate": 0.15,
           "security_headers": 0.12,
           "known_vulnerabilities": 0.20,
           "governance_disclosure": 0.15,
           "tech_stack_modernity": 0.10,
           "domain_authority": 0.13,
           "update_frequency": 0.15
       }
       
       weights = weights or default_weights
       
       total_weight = 0
       weighted_sum = 0
       confidence_weighted_sum = 0
       
       confidence_multipliers = {
           SignalConfidence.HIGH: 1.0,
           SignalConfidence.MEDIUM: 0.85,
           SignalConfidence.LOW: 0.65,
           SignalConfidence.UNAVAILABLE: 0.0
       }
       
       for signal_name, signal in signals.items():
           if signal_name in weights:
               weight = weights[signal_name]
               total_weight += weight
               weighted_sum += signal.score * weight
               
               conf_mult = confidence_multipliers.get(signal.confidence, 0.5)
               confidence_weighted_sum += signal.score * weight * conf_mult
       
       if total_weight == 0:
           return 0.0, 0.0
       
       composite = (weighted_sum / total_weight) * 10  # Scale to 0-1000
       confidence_adjusted = (confidence_weighted_sum / total_weight) * 10
       
       return composite, confidence_adjusted
   
   def export_to_model_format(
       self,
       signals: Dict[str, ScoredSignal],
       model_type: str = "cyber"
   ) -> Dict[str, float]:
       """
       Export scored signals in format expected by pricing models
       """
       if model_type == "cyber":
           return {
               "ssl_certificate": signals.get("ssl_certificate", ScoredSignal("", "", 0, SignalConfidence.UNAVAILABLE, [], "")).score,
               "security_headers": signals.get("security_headers", ScoredSignal("", "", 0, SignalConfidence.UNAVAILABLE, [], "")).score,
               "known_vulnerabilities": signals.get("known_vulnerabilities", ScoredSignal("", "", 0, SignalConfidence.UNAVAILABLE, [], "")).score,
               "tls_version": signals.get("ssl_certificate", ScoredSignal("", "", 0, SignalConfidence.UNAVAILABLE, [], "")).score,  # Derived from SSL
               # Map to other cyber signals...
           }
       elif model_type == "energy":
           return {
               "ssl_score": signals.get("ssl_certificate", ScoredSignal("", "", 0, SignalConfidence.UNAVAILABLE, [], "")).score,
               "security_headers": signals.get("security_headers", ScoredSignal("", "", 0, SignalConfidence.UNAVAILABLE, [], "")).score,
               "governance_disclosure": signals.get("governance_disclosure", ScoredSignal("", "", 0, SignalConfidence.UNAVAILABLE, [], "")).score,
               "update_frequency": signals.get("update_frequency", ScoredSignal("", "", 0, SignalConfidence.UNAVAILABLE, [], "")).score,
               "domain_authority": signals.get("domain_authority", ScoredSignal("", "", 0, SignalConfidence.UNAVAILABLE, [], "")).score,
               "tech_stack_modernity": signals.get("tech_stack_modernity", ScoredSignal("", "", 0, SignalConfidence.UNAVAILABLE, [], "")).score,
           }
       
       # Default: return raw scores
       return {name: s.score for name, s in signals.items()}


# Example usage and testing
if __name__ == "__main__":
   print("=" * 80)
   print("DSI SIGNAL SCORING ENGINE - TEST SUITE")
   print("=" * 80)
   
   scorer = ComprehensiveSignalScorer()
   
   # Test SSL scoring
   print("\n1. SSL/TLS Scoring Test")
   print("-" * 40)
   ssl_result = {
       "grade": "A",
       "protocols": ["TLSv1.2", "TLSv1.3"],
       "hstsPolicy": {"status": "present"},
       "vulnerabilities": {}
   }
   ssl_signal = scorer.ssl_scorer.score_from_ssl_labs(ssl_result)
   print(f"Score: {ssl_signal.score}")
   print(f"Evidence: {ssl_signal.evidence}")
   
   # Test security headers
   print("\n2. Security Headers Scoring Test")
   print("-" * 40)
   headers = {
       "Content-Security-Policy": "default-src 'self'; script-src 'self'",
       "X-Frame-Options": "DENY",
       "X-Content-Type-Options": "nosniff",
       "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
       "Referrer-Policy": "strict-origin-when-cross-origin"
   }
   header_signal = scorer.headers_scorer.score(headers)
   print(f"Score: {header_signal.score}")
   print(f"Evidence: {header_signal.evidence}")
   
   # Test vulnerability scoring
   print("\n3. Vulnerability Scoring Test")
   print("-" * 40)
   vuln_signal = scorer.vulnerability_scorer.score_from_vulnerability_data(
       critical_cves=0,
       high_cves=2,
       exposed_databases=False,
       leaked_credentials=True
   )
   print(f"Score: {vuln_signal.score}")
   print(f"Evidence: {vuln_signal.evidence}")
   
   # Test composite scoring
   print("\n4. Composite Score Calculation")
   print("-" * 40)
   all_signals = {
       "ssl_certificate": ssl_signal,
       "security_headers": header_signal,
       "known_vulnerabilities": vuln_signal
   }
   composite, confidence_adjusted = scorer.calculate_composite_score(all_signals)
   print(f"Composite Score: {composite:.0f}/1000")
   print(f"Confidence-Adjusted Score: {confidence_adjusted:.0f}/1000")
