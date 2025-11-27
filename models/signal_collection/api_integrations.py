"""
Digital Signal Intelligence - External API Integrations
========================================================

Production-ready integrations with external security and intelligence APIs.
Provides real-time signal collection from authoritative sources.

Supported APIs:
- SSL Labs (SSL/TLS grading)
- SecurityHeaders.com (header analysis)
- Shodan (exposed services, vulnerabilities)
- Have I Been Pwned (credential leaks)
- BuiltWith (technology detection)
- Internet Archive Wayback Machine (historical analysis)
- Common Crawl (web archive data)

Author: John Walker
Date: November 2025
Version: 1.0
"""

import json
import time
import hashlib
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class APIResponse:
   """Standardized API response container"""
   success: bool
   data: Optional[Dict[str, Any]]
   error: Optional[str] = None
   source: str = ""
   cached: bool = False
   timestamp: datetime = field(default_factory=datetime.now)
   rate_limited: bool = False
   
   def to_dict(self) -> Dict:
       return {
           "success": self.success,
           "data": self.data,
           "error": self.error,
           "source": self.source,
           "cached": self.cached,
           "timestamp": self.timestamp.isoformat(),
           "rate_limited": self.rate_limited
       }


class SimpleCache:
   """Simple in-memory cache with TTL"""
   
   def __init__(self, default_ttl: int = 3600):
       self._cache: Dict[str, Dict] = {}
       self.default_ttl = default_ttl
   
   def _make_key(self, prefix: str, identifier: str) -> str:
       return f"{prefix}:{hashlib.md5(identifier.encode()).hexdigest()}"
   
   def get(self, prefix: str, identifier: str) -> Optional[Any]:
       key = self._make_key(prefix, identifier)
       if key in self._cache:
           entry = self._cache[key]
           if datetime.now() < entry["expires"]:
               return entry["value"]
           else:
               del self._cache[key]
       return None
   
   def set(self, prefix: str, identifier: str, value: Any, ttl: Optional[int] = None):
       key = self._make_key(prefix, identifier)
       self._cache[key] = {
           "value": value,
           "expires": datetime.now() + timedelta(seconds=ttl or self.default_ttl)
       }
   
   def clear(self):
       self._cache.clear()


class BaseAPIClient(ABC):
   """Base class for all API integrations"""
   
   def __init__(
       self,
       api_key: Optional[str] = None,
       cache: Optional[SimpleCache] = None,
       timeout: int = 30,
       max_retries: int = 3
   ):
       self.api_key = api_key
       self.cache = cache or SimpleCache()
       self.timeout = timeout
       
       # Configure session with retries
       self.session = requests.Session()
       retry_strategy = Retry(
           total=max_retries,
           backoff_factor=1,
           status_forcelist=[429, 500, 502, 503, 504]
       )
       adapter = HTTPAdapter(max_retries=retry_strategy)
       self.session.mount("http://", adapter)
       self.session.mount("https://", adapter)
   
   @abstractmethod
   def get_source_name(self) -> str:
       """Return the name of this data source"""
       pass
   
   @abstractmethod
   def fetch(self, identifier: str) -> APIResponse:
       """Fetch data for the given identifier"""
       pass
   
   def _get_cached(self, identifier: str) -> Optional[APIResponse]:
       """Check cache for existing result"""
       cached = self.cache.get(self.get_source_name(), identifier)
       if cached:
           return APIResponse(
               success=True,
               data=cached,
               source=self.get_source_name(),
               cached=True
           )
       return None


class SSLLabsClient(BaseAPIClient):
   """
   SSL Labs API Client
   
   Free API for SSL/TLS analysis
   Rate limits: 1 new assessment per minute, cached results available immediately
   
   Documentation: https://github.com/ssllabs/ssllabs-scan/blob/master/ssllabs-api-docs-v3.md
   """
   
   BASE_URL = "https://api.ssllabs.com/api/v3/"
   
   def get_source_name(self) -> str:
       return "ssl_labs"
   
   def fetch(self, domain: str) -> APIResponse:
       """
       Analyze SSL/TLS configuration for a domain
       
       Args:
           domain: Domain to analyze (e.g., "example.com")
       
       Returns:
           APIResponse with SSL Labs grading data
       """
       # Check cache first
       cached = self._get_cached(domain)
       if cached:
           logger.info(f"SSL Labs: Using cached result for {domain}")
           return cached
       
       try:
           # Start or get analysis
           params = {
               "host": domain,
               "fromCache": "on",  # Use cached results if available
               "all": "done",
               "maxAge": 24  # Accept results up to 24 hours old
           }
           
           url = urljoin(self.BASE_URL, "analyze")
           response = self.session.get(url, params=params, timeout=self.timeout)
           
           if response.status_code == 429:
               return APIResponse(
                   success=False,
                   data=None,
                   error="Rate limited - too many requests",
                   source=self.get_source_name(),
                   rate_limited=True
               )
           
           response.raise_for_status()
           data = response.json()
           
           # Check if analysis is still in progress
           status = data.get("status")
           if status == "IN_PROGRESS":
               # Poll until complete (max 5 minutes)
               for _ in range(30):  # 30 * 10s = 5 minutes
                   time.sleep(10)
                   response = self.session.get(url, params=params, timeout=self.timeout)
                   data = response.json()
                   if data.get("status") in ["READY", "ERROR"]:
                       break
           
           if data.get("status") == "ERROR":
               return APIResponse(
                   success=False,
                   data=None,
                   error=data.get("statusMessage", "Unknown error"),
                   source=self.get_source_name()
               )
           
           # Extract relevant data
           result = self._parse_result(data)
           
           # Cache the result
           self.cache.set(self.get_source_name(), domain, result, ttl=86400)  # 24 hours
           
           return APIResponse(
               success=True,
               data=result,
               source=self.get_source_name()
           )
           
       except requests.exceptions.RequestException as e:
           logger.error(f"SSL Labs API error for {domain}: {str(e)}")
           return APIResponse(
               success=False,
               data=None,
               error=str(e),
               source=self.get_source_name()
           )
   
   def _parse_result(self, data: Dict) -> Dict:
       """Parse SSL Labs response into standardized format"""
       endpoints = data.get("endpoints", [])
       
       if not endpoints:
           return {
               "grade": "T",  # Trust issue / unreachable
               "protocols": [],
               "vulnerabilities": {},
               "hstsPolicy": {}
           }
       
       # Use first endpoint (usually the main one)
       endpoint = endpoints[0]
       details = endpoint.get("details", {})
       
       # Extract protocols
       protocols = []
       for proto in details.get("protocols", []):
           protocols.append(f"{proto.get('name', '')}{proto.get('version', '')}")
       
       # Check vulnerabilities
       vulnerabilities = {
           "heartbleed": details.get("heartbleed", False),
           "poodle": details.get("poodle", False),
           "freak": details.get("freak", False),
           "logjam": details.get("logjam", False),
           "drownVulnerable": details.get("drownVulnerable", False),
           "ticketbleed": details.get("ticketbleed", 0) > 0,
           "bleichenbacher": details.get("bleichenbacher", 0) > 0,
           "zombiePoodle": details.get("zombiePoodle", 0) > 0,
           "goldenDoodle": details.get("goldenDoodle", 0) > 0,
       }
       
       return {
           "grade": endpoint.get("grade", "T"),
           "gradeTrustIgnored": endpoint.get("gradeTrustIgnored", "T"),
           "protocols": protocols,
           "vulnerabilities": vulnerabilities,
           "hstsPolicy": details.get("hstsPolicy", {}),
           "supportsAlpn": details.get("supportsAlpn", False),
           "sessionResumption": details.get("sessionResumption", 0),
           "ocspStapling": details.get("ocspStapling", False),
           "forwardSecrecy": details.get("forwardSecrecy", 0),
           "certChains": len(details.get("certChains", [])),
           "serverSignature": details.get("serverSignature", ""),
           "testTime": data.get("testTime", 0)
       }


class ShodanClient(BaseAPIClient):
   """
   Shodan API Client
   
   Requires API key (free tier available)
   Rate limits vary by plan
   
   Documentation: https://developer.shodan.io/api
   """
   
   BASE_URL = "https://api.shodan.io/"
   
   def __init__(self, api_key: str, **kwargs):
       super().__init__(api_key=api_key, **kwargs)
       if not api_key:
           raise ValueError("Shodan requires an API key")
   
   def get_source_name(self) -> str:
       return "shodan"
   
   def fetch(self, ip_or_domain: str) -> APIResponse:
       """
       Fetch Shodan data for IP or domain
       
       Args:
           ip_or_domain: IP address or domain to query
       
       Returns:
           APIResponse with exposed services and vulnerabilities
       """
       cached = self._get_cached(ip_or_domain)
       if cached:
           return cached
       
       try:
           # Determine if IP or domain
           if self._is_ip(ip_or_domain):
               url = urljoin(self.BASE_URL, f"shodan/host/{ip_or_domain}")
           else:
               # Resolve domain to IP first
               url = urljoin(self.BASE_URL, f"dns/resolve")
               response = self.session.get(
                   url,
                   params={"hostnames": ip_or_domain, "key": self.api_key},
                   timeout=self.timeout
               )
               response.raise_for_status()
               dns_data = response.json()
               ip = dns_data.get(ip_or_domain)
               if not ip:
                   return APIResponse(
                       success=False,
                       data=None,
                       error=f"Could not resolve {ip_or_domain}",
                       source=self.get_source_name()
                   )
               url = urljoin(self.BASE_URL, f"shodan/host/{ip}")
           
           response = self.session.get(
               url,
               params={"key": self.api_key},
               timeout=self.timeout
           )
           
           if response.status_code == 404:
               # No data found - not necessarily an error
               result = {"found": False, "ports": [], "vulns": [], "services": []}
               self.cache.set(self.get_source_name(), ip_or_domain, result, ttl=3600)
               return APIResponse(
                   success=True,
                   data=result,
                   source=self.get_source_name()
               )
           
           response.raise_for_status()
           data = response.json()
           
           result = self._parse_result(data)
           self.cache.set(self.get_source_name(), ip_or_domain, result, ttl=3600)
           
           return APIResponse(
               success=True,
               data=result,
               source=self.get_source_name()
           )
           
       except requests.exceptions.RequestException as e:
           logger.error(f"Shodan API error for {ip_or_domain}: {str(e)}")
           return APIResponse(
               success=False,
               data=None,
               error=str(e),
               source=self.get_source_name()
           )
   
   def _is_ip(self, value: str) -> bool:
       """Check if value is an IP address"""
       parts = value.split(".")
       if len(parts) != 4:
           return False
       try:
           return all(0 <= int(part) <= 255 for part in parts)
       except ValueError:
           return False
   
   def _parse_result(self, data: Dict) -> Dict:
       """Parse Shodan response into standardized format"""
       return {
           "found": True,
           "ip": data.get("ip_str", ""),
           "organization": data.get("org", ""),
           "isp": data.get("isp", ""),
           "asn": data.get("asn", ""),
           "ports": data.get("ports", []),
           "vulns": data.get("vulns", []),
           "services": [
               {
                   "port": svc.get("port"),
                   "protocol": svc.get("transport", ""),
                   "product": svc.get("product", ""),
                   "version": svc.get("version", ""),
                   "cpe": svc.get("cpe", []),
                   "vulns": list(svc.get("vulns", {}).keys())
               }
               for svc in data.get("data", [])
           ],
           "hostnames": data.get("hostnames", []),
           "domains": data.get("domains", []),
           "os": data.get("os", ""),
           "tags": data.get("tags", []),
           "last_update": data.get("last_update", "")
       }


class HIBPClient(BaseAPIClient):
   """
   Have I Been Pwned API Client
   
   Checks if a domain has appeared in data breaches
   Requires API key for domain search
   
   Documentation: https://haveibeenpwned.com/API/v3
   """
   
   BASE_URL = "https://haveibeenpwned.com/api/v3/"
   
   def __init__(self, api_key: str, **kwargs):
       super().__init__(api_key=api_key, **kwargs)
       self.session.headers.update({
           "hibp-api-key": api_key,
           "user-agent": "DSI-Signal-Collector"
       })
   
   def get_source_name(self) -> str:
       return "hibp"
   
   def fetch(self, domain: str) -> APIResponse:
       """
       Check domain for breach exposure
       
       Args:
           domain: Domain to check
       
       Returns:
           APIResponse with breach information
       """
       cached = self._get_cached(domain)
       if cached:
           return cached
       
       try:
           url = urljoin(self.BASE_URL, f"breaches")
           params = {"domain": domain}
           
           response = self.session.get(url, params=params, timeout=self.timeout)
           
           if response.status_code == 404:
               # No breaches found
               result = {"breaches": [], "total_pwned": 0, "has_breaches": False}
               self.cache.set(self.get_source_name(), domain, result, ttl=86400)
               return APIResponse(
                   success=True,
                   data=result,
                   source=self.get_source_name()
               )
           
           if response.status_code == 429:
               return APIResponse(
                   success=False,
                   data=None,
                   error="Rate limited",
                   source=self.get_source_name(),
                   rate_limited=True
               )
           
           response.raise_for_status()
           breaches = response.json()
           
           result = self._parse_result(breaches)
           self.cache.set(self.get_source_name(), domain, result, ttl=86400)
           
           return APIResponse(
               success=True,
               data=result,
               source=self.get_source_name()
           )
           
       except requests.exceptions.RequestException as e:
           logger.error(f"HIBP API error for {domain}: {str(e)}")
           return APIResponse(
               success=False,
               data=None,
               error=str(e),
               source=self.get_source_name()
           )
   
   def _parse_result(self, breaches: List[Dict]) -> Dict:
       """Parse HIBP response"""
       if not breaches:
           return {"breaches": [], "total_pwned": 0, "has_breaches": False}
       
       # Filter to relevant breaches for the domain
       total_pwned = sum(b.get("PwnCount", 0) for b in breaches)
       
       return {
           "has_breaches": True,
           "total_pwned": total_pwned,
           "breach_count": len(breaches),
           "breaches": [
               {
                   "name": b.get("Name", ""),
                   "title": b.get("Title", ""),
                   "domain": b.get("Domain", ""),
                   "breach_date": b.get("BreachDate", ""),
                   "added_date": b.get("AddedDate", ""),
                   "pwn_count": b.get("PwnCount", 0),
                   "description": b.get("Description", "")[:200],
                   "data_classes": b.get("DataClasses", []),
                   "is_verified": b.get("IsVerified", False),
                   "is_sensitive": b.get("IsSensitive", False),
               }
               for b in breaches[:10]  # Limit to 10 most relevant
           ],
           "most_recent_breach": max(
               (b.get("BreachDate", "") for b in breaches),
               default=""
           ),
           "data_types_exposed": list(set(
               dt for b in breaches for dt in b.get("DataClasses", [])
           ))
       }


class WaybackClient(BaseAPIClient):
   """
   Internet Archive Wayback Machine API Client
   
   Free API for historical website snapshots
   No authentication required
   
   Documentation: https://archive.org/help/wayback_api.php
   """
   
   CDX_URL = "https://web.archive.org/cdx/search/cdx"
   AVAILABILITY_URL = "https://archive.org/wayback/available"
   
   def get_source_name(self) -> str:
       return "wayback"
   
   def fetch(self, domain: str) -> APIResponse:
       """
       Get historical snapshot data for domain
       
       Args:
           domain: Domain to analyze
       
       Returns:
           APIResponse with historical snapshot data
       """
       cached = self._get_cached(domain)
       if cached:
           return cached
       
       try:
           # Get snapshot count and timeline
           params = {
               "url": domain,
               "output": "json",
               "fl": "timestamp,statuscode,digest",
               "collapse": "digest",  # Dedupe by content
               "from": (datetime.now() - timedelta(days=365*5)).strftime("%Y"),
               "to": datetime.now().strftime("%Y")
           }
           
           response = self.session.get(self.CDX_URL, params=params, timeout=self.timeout)
           response.raise_for_status()
           
           # Parse CDX response (first row is headers)
           lines = response.text.strip().split("\n")
           if len(lines) <= 1:
               result = {
                   "found": False,
                   "snapshot_count": 0,
                   "first_snapshot": None,
                   "last_snapshot": None
               }
           else:
               snapshots = [json.loads(line) if line.startswith("[") else line.split() for line in lines[1:]]
               
               # Parse timestamps
               timestamps = [s[0] if isinstance(s, list) else s.get("timestamp", "") for s in snapshots]
               timestamps = [t for t in timestamps if t]
               
               result = self._analyze_snapshots(domain, timestamps)
           
           self.cache.set(self.get_source_name(), domain, result, ttl=86400)
           
           return APIResponse(
               success=True,
               data=result,
               source=self.get_source_name()
           )
           
       except requests.exceptions.RequestException as e:
           logger.error(f"Wayback API error for {domain}: {str(e)}")
           return APIResponse(
               success=False,
               data=None,
               error=str(e),
               source=self.get_source_name()
           )
   
   def _analyze_snapshots(self, domain: str, timestamps: List[str]) -> Dict:
       """Analyze snapshot history"""
       if not timestamps:
           return {
               "found": False,
               "snapshot_count": 0,
               "snapshots_per_year": 0,
               "first_snapshot": None,
               "last_snapshot": None,
               "days_since_last_snapshot": 999,
               "major_changes_detected": 0
           }
       
       # Parse timestamps (format: YYYYMMDDhhmmss)
       def parse_ts(ts):
           try:
               return datetime.strptime(ts[:8], "%Y%m%d")
           except:
               return None
       
       dates = [parse_ts(ts) for ts in timestamps]
       dates = [d for d in dates if d]
       
       if not dates:
           return {
               "found": True,
               "snapshot_count": len(timestamps),
               "snapshots_per_year": len(timestamps) / 5,
               "first_snapshot": timestamps[0] if timestamps else None,
               "last_snapshot": timestamps[-1] if timestamps else None,
               "days_since_last_snapshot": 0,
               "major_changes_detected": 0
           }
       
       dates.sort()
       
       # Calculate metrics
       years_covered = max(1, (dates[-1] - dates[0]).days / 365)
       snapshots_per_year = len(dates) / years_covered
       days_since_last = (datetime.now() - dates[-1]).days
       
       # Estimate major changes (gaps > 6 months could indicate redesigns)
       major_changes = 0
       for i in range(1, len(dates)):
           gap = (dates[i] - dates[i-1]).days
           if gap > 180:  # 6 month gap
               major_changes += 1
       
       return {
           "found": True,
           "snapshot_count": len(timestamps),
           "snapshots_per_year": round(snapshots_per_year, 1),
           "first_snapshot": dates[0].isoformat() if dates else None,
           "last_snapshot": dates[-1].isoformat() if dates else None,
           "days_since_last_snapshot": days_since_last,
           "years_archived": round(years_covered, 1),
           "major_changes_detected": major_changes,
           "update_consistency": "high" if snapshots_per_year > 50 else "medium" if snapshots_per_year > 20 else "low"
       }


class BuiltWithClient(BaseAPIClient):
   """
   BuiltWith API Client
   
   Detects technology stack of websites
   Requires API key
   
   Documentation: https://api.builtwith.com/
   """
   
   BASE_URL = "https://api.builtwith.com/v21/api.json"
   
   def __init__(self, api_key: str, **kwargs):
       super().__init__(api_key=api_key, **kwargs)
   
   def get_source_name(self) -> str:
       return "builtwith"
   
   def fetch(self, domain: str) -> APIResponse:
       """
       Detect technology stack for domain
       
       Args:
           domain: Domain to analyze
       
       Returns:
           APIResponse with technology stack data
       """
       cached = self._get_cached(domain)
       if cached:
           return cached
       
       try:
           params = {
               "KEY": self.api_key,
               "LOOKUP": domain
           }
           
           response = self.session.get(self.BASE_URL, params=params, timeout=self.timeout)
           response.raise_for_status()
           data = response.json()
           
           result = self._parse_result(data)
           self.cache.set(self.get_source_name(), domain, result, ttl=86400)
           
           return APIResponse(
               success=True,
               data=result,
               source=self.get_source_name()
           )
           
       except requests.exceptions.RequestException as e:
           logger.error(f"BuiltWith API error for {domain}: {str(e)}")
           return APIResponse(
               success=False,
               data=None,
               error=str(e),
               source=self.get_source_name()
           )
   
   def _parse_result(self, data: Dict) -> Dict:
       """Parse BuiltWith response"""
       results = data.get("Results", [])
       if not results:
           return {"technologies": [], "categories": {}}
       
       result = results[0]
       paths = result.get("Result", {}).get("Paths", [])
       
       technologies = []
       categories = {}
       
       for path in paths:
           for tech in path.get("Technologies", []):
               tech_name = tech.get("Name", "")
               category = tech.get("Categories", ["Unknown"])[0] if tech.get("Categories") else "Unknown"
               
               technologies.append({
                   "name": tech_name,
                   "category": category,
                   "first_detected": tech.get("FirstDetected", ""),
                   "last_detected": tech.get("LastDetected", "")
               })
               
               if category not in categories:
                   categories[category] = []
               categories[category].append(tech_name)
       
       return {
           "technologies": technologies,
           "categories": categories,
           "technology_count": len(technologies),
           "has_cdn": any("CDN" in cat for cat in categories),
           "has_waf": any("WAF" in cat or "Security" in cat for cat in categories),
           "cms": categories.get("CMS", []),
           "frameworks": categories.get("JavaScript Frameworks", []) + categories.get("Web Frameworks", []),
           "analytics": categories.get("Analytics", []),
           "hosting": categories.get("Hosting", [])
       }


class SecurityHeadersIOClient(BaseAPIClient):
   """
   SecurityHeaders.com API Client
   
   Free API for security header analysis
   Rate limited
   
   Note: This is an unofficial API - use sparingly
   """
   
   BASE_URL = "https://securityheaders.com/"
   
   def get_source_name(self) -> str:
       return "securityheaders"
   
   def fetch(self, url: str) -> APIResponse:
       """
       Analyze security headers for URL
       
       Args:
           url: Full URL to analyze
       
       Returns:
           APIResponse with header analysis
       """
       cached = self._get_cached(url)
       if cached:
           return cached
       
       try:
           # SecurityHeaders.com provides a JSON API
           params = {
               "q": url,
               "followRedirects": "on"
           }
           headers = {"Accept": "application/json"}
           
           response = self.session.get(
               self.BASE_URL,
               params=params,
               headers=headers,
               timeout=self.timeout
           )
           
           if response.status_code == 429:
               return APIResponse(
                   success=False,
                   data=None,
                   error="Rate limited",
                   source=self.get_source_name(),
                   rate_limited=True
               )
           
           # Try to parse as JSON, fall back to scraping grade
           try:
               data = response.json()
               result = self._parse_json_result(data)
           except json.JSONDecodeError:
               # Fallback: just fetch headers directly
               result = self._fetch_headers_directly(url)
           
           if result:
               self.cache.set(self.get_source_name(), url, result, ttl=3600)
           
           return APIResponse(
               success=True,
               data=result,
               source=self.get_source_name()
           )
           
       except requests.exceptions.RequestException as e:
           logger.error(f"SecurityHeaders API error for {url}: {str(e)}")
           return APIResponse(
               success=False,
               data=None,
               error=str(e),
               source=self.get_source_name()
           )
   
   def _fetch_headers_directly(self, url: str) -> Dict:
       """Fetch and analyze headers directly"""
       try:
           response = self.session.head(url, timeout=10, allow_redirects=True)
           headers = dict(response.headers)
           
           # Analyze headers
           security_headers = [
               "content-security-policy",
               "x-frame-options",
               "x-content-type-options",
               "strict-transport-security",
               "referrer-policy",
               "permissions-policy",
               "x-xss-protection"
           ]
           
           present = []
           missing = []
           
           headers_lower = {k.lower(): v for k, v in headers.items()}
           
           for header in security_headers:
               if header in headers_lower:
                   present.append(header)
               else:
                   missing.append(header)
           
           # Calculate grade
           score = len(present) / len(security_headers) * 100
           if score >= 85:
               grade = "A"
           elif score >= 70:
               grade = "B"
           elif score >= 55:
               grade = "C"
           elif score >= 40:
               grade = "D"
           else:
               grade = "F"
           
           return {
               "grade": grade,
               "score": score,
               "headers_present": present,
               "headers_missing": missing,
               "raw_headers": headers_lower
           }
           
       except Exception as e:
           return {"error": str(e), "grade": "?"}
   
   def _parse_json_result(self, data: Dict) -> Dict:
       """Parse JSON response if available"""
       return {
           "grade": data.get("grade", "?"),
           "score": data.get("score", 0),
           "headers_present": data.get("present", []),
           "headers_missing": data.get("missing", [])
       }


class IntegratedSignalCollector:
   """
   Unified signal collector that orchestrates all API clients
   """
   
   def __init__(
       self,
       shodan_api_key: Optional[str] = None,
       hibp_api_key: Optional[str] = None,
       builtwith_api_key: Optional[str] = None
   ):
       self.cache = SimpleCache(default_ttl=3600)
       
       # Initialize clients
       self.ssl_labs = SSLLabsClient(cache=self.cache)
       self.wayback = WaybackClient(cache=self.cache)
       self.security_headers = SecurityHeadersIOClient(cache=self.cache)
       
       # API key required clients
       self.shodan = ShodanClient(api_key=shodan_api_key, cache=self.cache) if shodan_api_key else None
       self.hibp = HIBPClient(api_key=hibp_api_key, cache=self.cache) if hibp_api_key else None
       self.builtwith = BuiltWithClient(api_key=builtwith_api_key, cache=self.cache) if builtwith_api_key else None
   
   def collect_all_signals(self, domain: str, url: Optional[str] = None) -> Dict[str, APIResponse]:
       """
       Collect signals from all available sources
       
       Args:
           domain: Domain to analyze (e.g., "example.com")
           url: Full URL if different from domain
       
       Returns:
           Dict mapping source name to APIResponse
       """
       if url is None:
           url = f"https://{domain}"
       
       results = {}
       
       # SSL Labs (free)
       logger.info(f"Fetching SSL Labs data for {domain}...")
       results["ssl_labs"] = self.ssl_labs.fetch(domain)
       
       # Security Headers (free)
       logger.info(f"Fetching security headers for {url}...")
       results["security_headers"] = self.security_headers.fetch(url)
       
       # Wayback Machine (free)
       logger.info(f"Fetching Wayback data for {domain}...")
       results["wayback"] = self.wayback.fetch(domain)
       
       # Shodan (requires API key)
       if self.shodan:
           logger.info(f"Fetching Shodan data for {domain}...")
           results["shodan"] = self.shodan.fetch(domain)
       
       # HIBP (requires API key)
       if self.hibp:
           logger.info(f"Fetching HIBP data for {domain}...")
           results["hibp"] = self.hibp.fetch(domain)
       
       # BuiltWith (requires API key)
       if self.builtwith:
           logger.info(f"Fetching BuiltWith data for {domain}...")
           results["builtwith"] = self.builtwith.fetch(domain)
       
       return results
   
   def get_collection_summary(self, results: Dict[str, APIResponse]) -> Dict:
       """Generate summary of collection results"""
       return {
           "sources_queried": len(results),
           "successful": sum(1 for r in results.values() if r.success),
           "failed": sum(1 for r in results.values() if not r.success),
           "cached": sum(1 for r in results.values() if r.cached),
           "rate_limited": sum(1 for r in results.values() if r.rate_limited),
           "details": {
               name: {
                   "success": r.success,
                   "cached": r.cached,
                   "error": r.error
               }
               for name, r in results.items()
           }
       }


# Example usage
if __name__ == "__main__":
   print("=" * 80)
   print("DSI EXTERNAL API INTEGRATIONS - TEST SUITE")
   print("=" * 80)
   
   # Test with free APIs only
   collector = IntegratedSignalCollector()
   
   test_domain = "google.com"
   print(f"\nTesting collection for: {test_domain}")
   print("-" * 40)
   
   # Test individual clients
   print("\n1. Wayback Machine Test (free):")
   wayback_result = collector.wayback.fetch(test_domain)
   print(f"   Success: {wayback_result.success}")
   if wayback_result.success:
       data = wayback_result.data
       print(f"   Snapshots: {data.get('snapshot_count', 0)}")
       print(f"   Per year: {data.get('snapshots_per_year', 0)}")
   
   print("\n2. Security Headers Test (free):")
   headers_result = collector.security_headers.fetch(f"https://{test_domain}")
   print(f"   Success: {headers_result.success}")
   if headers_result.success:
       data = headers_result.data
       print(f"   Grade: {data.get('grade', '?')}")
       print(f"   Present: {data.get('headers_present', [])}")
   
   print("\n" + "=" * 80)
   print("Note: SSL Labs test skipped (takes 2-5 minutes)")
   print("Note: Shodan, HIBP, BuiltWith require API keys")
   print("=" * 80)
