"""
DSI Signal Architecture - Extractor Configuration

Manages configuration and API keys for production extractors.
Supports environment variables, config files, and programmatic configuration.
"""

import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ExtractorConfig:
    """
    Configuration for production extractors.

    Configuration sources (in order of precedence):
        1. Programmatic values passed to constructor
        2. Environment variables
        3. Default values

    Environment Variables:
        DSI_EXTRACTOR_MODE: 'production' | 'stub' | 'hybrid'
        DSI_SHODAN_API_KEY: Shodan API key
        DSI_CENSYS_API_ID: Censys API ID
        DSI_CENSYS_API_SECRET: Censys API secret
        DSI_SSL_LABS_EMAIL: Email for SSL Labs API v4
        DSI_HIBP_API_KEY: Have I Been Pwned API key
        DSI_BUILTWITH_API_KEY: BuiltWith API key
        DSI_SEC_USER_AGENT: User agent for SEC EDGAR (required)

    Usage:
        # Default config from environment
        config = ExtractorConfig()

        # Or with overrides
        config = ExtractorConfig(
            mode='production',
            shodan_api_key='your-key-here',
        )

        # Access values
        print(config.mode)
        print(config.shodan_api_key)
    """

    # Extraction mode
    mode: str = field(default_factory=lambda: os.getenv('DSI_EXTRACTOR_MODE', 'stub'))

    # Network scanning APIs
    shodan_api_key: Optional[str] = field(
        default_factory=lambda: os.getenv('DSI_SHODAN_API_KEY')
    )
    censys_api_id: Optional[str] = field(
        default_factory=lambda: os.getenv('DSI_CENSYS_API_ID')
    )
    censys_api_secret: Optional[str] = field(
        default_factory=lambda: os.getenv('DSI_CENSYS_API_SECRET')
    )

    # TLS/SSL APIs
    ssl_labs_email: Optional[str] = field(
        default_factory=lambda: os.getenv('DSI_SSL_LABS_EMAIL')
    )

    # Breach databases
    hibp_api_key: Optional[str] = field(
        default_factory=lambda: os.getenv('DSI_HIBP_API_KEY')
    )

    # Technology detection
    builtwith_api_key: Optional[str] = field(
        default_factory=lambda: os.getenv('DSI_BUILTWITH_API_KEY')
    )

    # SEC EDGAR (requires user agent with contact info)
    sec_user_agent: str = field(
        default_factory=lambda: os.getenv(
            'DSI_SEC_USER_AGENT',
            'DSI-Framework/1.0 (contact@example.com)'
        )
    )

    # Corporate data
    opencorporates_api_key: Optional[str] = field(
        default_factory=lambda: os.getenv('DSI_OPENCORPORATES_API_KEY')
    )

    # ESG data (premium)
    msci_api_key: Optional[str] = field(
        default_factory=lambda: os.getenv('DSI_MSCI_API_KEY')
    )

    # Credit ratings (premium)
    sp_api_key: Optional[str] = field(
        default_factory=lambda: os.getenv('DSI_SP_API_KEY')
    )

    # DNS resolver (optional custom resolver)
    dns_resolver: str = field(
        default_factory=lambda: os.getenv('DSI_DNS_RESOLVER', '8.8.8.8')
    )

    # Rate limiting defaults
    default_rate_limit: float = field(
        default_factory=lambda: float(os.getenv('DSI_DEFAULT_RATE_LIMIT', '1.0'))
    )

    # Timeouts
    default_timeout: int = field(
        default_factory=lambda: int(os.getenv('DSI_DEFAULT_TIMEOUT', '30'))
    )

    # Cache settings
    cache_enabled: bool = field(
        default_factory=lambda: os.getenv('DSI_CACHE_ENABLED', 'true').lower() == 'true'
    )

    def __post_init__(self):
        """Validate configuration after initialization."""
        valid_modes = {'production', 'stub', 'hybrid'}
        if self.mode not in valid_modes:
            raise ValueError(f"mode must be one of {valid_modes}, got '{self.mode}'")

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for extractor initialization."""
        return {
            'shodan_api_key': self.shodan_api_key,
            'censys_api_id': self.censys_api_id,
            'censys_api_secret': self.censys_api_secret,
            'ssl_labs_email': self.ssl_labs_email,
            'hibp_api_key': self.hibp_api_key,
            'builtwith_api_key': self.builtwith_api_key,
            'sec_user_agent': self.sec_user_agent,
            'opencorporates_api_key': self.opencorporates_api_key,
            'msci_api_key': self.msci_api_key,
            'sp_api_key': self.sp_api_key,
            'dns_resolver': self.dns_resolver,
            'timeout': self.default_timeout,
        }

    def has_api_key(self, service: str) -> bool:
        """Check if an API key is configured for a service."""
        key_map = {
            'shodan': self.shodan_api_key,
            'censys': self.censys_api_id and self.censys_api_secret,
            'ssl_labs': self.ssl_labs_email,
            'hibp': self.hibp_api_key,
            'builtwith': self.builtwith_api_key,
            'opencorporates': self.opencorporates_api_key,
            'msci': self.msci_api_key,
            'sp': self.sp_api_key,
        }
        return bool(key_map.get(service))

    def get_available_services(self) -> Dict[str, bool]:
        """Get a map of which services have API keys configured."""
        services = ['shodan', 'censys', 'ssl_labs', 'hibp', 'builtwith',
                    'opencorporates', 'msci', 'sp']
        return {svc: self.has_api_key(svc) for svc in services}


# Global config instance (can be overridden)
_global_config: Optional[ExtractorConfig] = None


def get_config() -> ExtractorConfig:
    """Get the global extractor configuration."""
    global _global_config
    if _global_config is None:
        _global_config = ExtractorConfig()
    return _global_config


def set_config(config: ExtractorConfig) -> None:
    """Set the global extractor configuration."""
    global _global_config
    _global_config = config
