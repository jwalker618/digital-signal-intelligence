"""
DSI Locale Detection (Phase 10)

Automatic locale detection from discovery results
for multi-locale pricing support.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


logger = logging.getLogger("dsi.orchestration.locale")


@dataclass
class LocaleMatch:
    """Result of locale detection."""
    locale: str
    confidence: float
    source: str  # tld, address, headquarters, etc.
    country_code: Optional[str] = None
    country_name: Optional[str] = None


@dataclass
class LocaleDetectorConfig:
    """Configuration for locale detection."""
    # TLD to locale mapping
    tld_mapping: Dict[str, str] = field(default_factory=lambda: {
        ".com": "US",
        ".co.uk": "UK",
        ".uk": "UK",
        ".de": "EU",
        ".fr": "EU",
        ".eu": "EU",
        ".ca": "CA",
        ".au": "AU",
        ".jp": "APAC",
        ".cn": "APAC",
        ".sg": "APAC",
        ".hk": "APAC",
    })

    # Country to locale mapping
    country_mapping: Dict[str, str] = field(default_factory=lambda: {
        "United States": "US",
        "USA": "US",
        "United Kingdom": "UK",
        "UK": "UK",
        "Great Britain": "UK",
        "England": "UK",
        "Germany": "EU",
        "France": "EU",
        "Netherlands": "EU",
        "Italy": "EU",
        "Spain": "EU",
        "Canada": "CA",
        "Australia": "AU",
        "Japan": "APAC",
        "China": "APAC",
        "Singapore": "APAC",
        "Hong Kong": "APAC",
    })

    # Priority of detection methods
    source_priority: List[str] = field(default_factory=lambda: [
        "headquarters",
        "registration_country",
        "primary_address",
        "tld",
        "fallback",
    ])

    # Default if nothing detected
    fallback_locale: str = "US"

    # Confidence thresholds
    high_confidence: float = 0.9
    medium_confidence: float = 0.7
    low_confidence: float = 0.5


class LocaleDetector:
    """
    Automatic locale detection from discovery results.

    Detection sources:
    - TLD: Domain extension (.co.uk -> UK)
    - Headquarters: Company HQ location
    - Registration: Country of registration
    - Address: Primary business address
    """

    def __init__(self, config: Optional[LocaleDetectorConfig] = None):
        """Initialize LocaleDetector with configuration."""
        self.config = config or LocaleDetectorConfig()

    def detect_locale(
        self,
        discovery_result: Any,
        return_all: bool = False,
    ) -> Optional[str]:
        """
        Detect locale from discovery result.

        Args:
            discovery_result: Discovery result with entity info
            return_all: If True, return all matches (for multi-locale)

        Returns:
            Best matching locale code or None
        """
        matches = self._detect_all_locales(discovery_result)

        if not matches:
            return self.config.fallback_locale if not return_all else None

        if return_all:
            return [m.locale for m in matches]

        # Return best match
        return matches[0].locale

    def detect_locales(
        self,
        discovery_result: Any,
        max_locales: int = 3,
    ) -> List[LocaleMatch]:
        """
        Detect all possible locales with confidence.

        Args:
            discovery_result: Discovery result
            max_locales: Maximum locales to return

        Returns:
            List of LocaleMatch objects sorted by confidence
        """
        matches = self._detect_all_locales(discovery_result)
        return matches[:max_locales]

    def _detect_all_locales(self, discovery_result: Any) -> List[LocaleMatch]:
        """Detect all possible locales from discovery."""
        matches: List[LocaleMatch] = []

        if discovery_result is None:
            return matches

        # Try each detection method
        for source in self.config.source_priority:
            match = self._detect_from_source(source, discovery_result)
            if match:
                matches.append(match)

        # Deduplicate and sort by confidence
        seen: Dict[str, LocaleMatch] = {}
        for match in matches:
            if match.locale not in seen or match.confidence > seen[match.locale].confidence:
                seen[match.locale] = match

        return sorted(seen.values(), key=lambda m: m.confidence, reverse=True)

    def _detect_from_source(
        self,
        source: str,
        discovery: Any,
    ) -> Optional[LocaleMatch]:
        """Detect locale from a specific source."""
        if source == "tld":
            return self._detect_from_tld(discovery)
        elif source == "headquarters":
            return self._detect_from_headquarters(discovery)
        elif source == "registration_country":
            return self._detect_from_registration(discovery)
        elif source == "primary_address":
            return self._detect_from_address(discovery)
        elif source == "fallback":
            return LocaleMatch(
                locale=self.config.fallback_locale,
                confidence=self.config.low_confidence,
                source="fallback",
            )
        return None

    def _detect_from_tld(self, discovery: Any) -> Optional[LocaleMatch]:
        """Detect locale from domain TLD."""
        domain = getattr(discovery, 'domain', None)
        if not domain:
            return None

        # Extract TLD
        tld = self._extract_tld(domain)
        if not tld:
            return None

        # Look up locale
        locale = self.config.tld_mapping.get(tld)
        if locale:
            return LocaleMatch(
                locale=locale,
                confidence=self.config.medium_confidence,
                source="tld",
            )

        # Check for country-specific subdomains
        for known_tld, mapped_locale in self.config.tld_mapping.items():
            if domain.endswith(known_tld):
                return LocaleMatch(
                    locale=mapped_locale,
                    confidence=self.config.medium_confidence,
                    source="tld",
                )

        return None

    def _detect_from_headquarters(self, discovery: Any) -> Optional[LocaleMatch]:
        """Detect locale from headquarters location."""
        # Try various attribute names
        hq = (
            getattr(discovery, 'headquarters', None) or
            getattr(discovery, 'hq_location', None) or
            getattr(discovery, 'main_office', None)
        )

        if not hq:
            # Try nested structure
            company_info = getattr(discovery, 'company_info', {})
            if isinstance(company_info, dict):
                hq = company_info.get('headquarters')

        if hq:
            locale = self._country_to_locale(hq)
            if locale:
                return LocaleMatch(
                    locale=locale,
                    confidence=self.config.high_confidence,
                    source="headquarters",
                    country_name=hq,
                )

        return None

    def _detect_from_registration(self, discovery: Any) -> Optional[LocaleMatch]:
        """Detect locale from registration country."""
        country = (
            getattr(discovery, 'registration_country', None) or
            getattr(discovery, 'country_of_incorporation', None) or
            getattr(discovery, 'jurisdiction', None)
        )

        if country:
            locale = self._country_to_locale(country)
            if locale:
                return LocaleMatch(
                    locale=locale,
                    confidence=self.config.high_confidence,
                    source="registration_country",
                    country_name=country,
                )

        return None

    def _detect_from_address(self, discovery: Any) -> Optional[LocaleMatch]:
        """Detect locale from primary address."""
        address = (
            getattr(discovery, 'address', None) or
            getattr(discovery, 'primary_address', None)
        )

        if not address:
            return None

        # Parse address for country
        if isinstance(address, dict):
            country = address.get('country') or address.get('country_name')
        elif isinstance(address, str):
            country = self._extract_country_from_address(address)
        else:
            return None

        if country:
            locale = self._country_to_locale(country)
            if locale:
                return LocaleMatch(
                    locale=locale,
                    confidence=self.config.medium_confidence,
                    source="primary_address",
                    country_name=country,
                )

        return None

    def _extract_tld(self, domain: str) -> Optional[str]:
        """Extract TLD from domain."""
        if not domain:
            return None

        domain = domain.lower().strip()

        # Remove protocol if present
        if "://" in domain:
            domain = domain.split("://")[1]

        # Remove path
        domain = domain.split("/")[0]

        # Check for compound TLDs first
        for tld in [".co.uk", ".com.au", ".co.jp"]:
            if domain.endswith(tld):
                return tld

        # Extract simple TLD
        match = re.search(r'\.[a-z]{2,}$', domain)
        if match:
            return match.group()

        return None

    def _country_to_locale(self, country: str) -> Optional[str]:
        """Map country name/code to locale."""
        if not country:
            return None

        country = country.strip()

        # Direct lookup
        if country in self.config.country_mapping:
            return self.config.country_mapping[country]

        # Case-insensitive lookup
        country_lower = country.lower()
        for key, locale in self.config.country_mapping.items():
            if key.lower() == country_lower:
                return locale

        # Partial match
        for key, locale in self.config.country_mapping.items():
            if key.lower() in country_lower or country_lower in key.lower():
                return locale

        return None

    def _extract_country_from_address(self, address: str) -> Optional[str]:
        """Extract country from address string."""
        if not address:
            return None

        # Common patterns
        # "123 Main St, New York, USA"
        # "London, United Kingdom"
        parts = [p.strip() for p in address.split(',')]

        # Check last parts for country
        for part in reversed(parts[-3:]):
            locale = self._country_to_locale(part)
            if locale:
                return part

        return None

    def get_locale_info(self, locale: str) -> Dict[str, Any]:
        """Get information about a locale."""
        locale_info = {
            "US": {
                "name": "United States",
                "currency": "USD",
                "timezone": "America/New_York",
                "regulatory_body": "State Insurance Commissioners",
            },
            "UK": {
                "name": "United Kingdom",
                "currency": "GBP",
                "timezone": "Europe/London",
                "regulatory_body": "FCA/PRA",
            },
            "EU": {
                "name": "European Union",
                "currency": "EUR",
                "timezone": "Europe/Paris",
                "regulatory_body": "EIOPA",
            },
            "CA": {
                "name": "Canada",
                "currency": "CAD",
                "timezone": "America/Toronto",
                "regulatory_body": "OSFI",
            },
            "AU": {
                "name": "Australia",
                "currency": "AUD",
                "timezone": "Australia/Sydney",
                "regulatory_body": "APRA",
            },
            "APAC": {
                "name": "Asia-Pacific",
                "currency": "USD",
                "timezone": "Asia/Singapore",
                "regulatory_body": "Various",
            },
        }
        return locale_info.get(locale, {"name": locale})
