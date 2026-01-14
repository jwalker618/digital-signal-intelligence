"""Backwards compatibility shim - re-exports from discovery package."""
from discovery import *
from discovery.website_discovery import (
    WebsiteDiscoveryEngine,
    DiscoveryResult,
    ConfidenceLevel,
    discover_website,
)
