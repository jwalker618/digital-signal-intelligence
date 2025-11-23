"""
Configuration classes for signal collection

Defines what to collect for each pricing model
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class CollectionConfig:
    """Base configuration for signal collection"""

    # URLs to prioritize
    priority_urls: List[str] = field(default_factory=list)

    # Document types to find
    document_types: List[str] = field(default_factory=list)

    # Keywords to search for
    keywords: List[str] = field(default_factory=list)

    # Time window (in months)
    time_window_months: int = 12

    # Max pages to crawl
    max_pages: int = 50

    # Max depth for crawling
    max_depth: int = 3

    # Follow external links
    follow_external: bool = False


@dataclass
class CyberConfig(CollectionConfig):
    """Configuration for cyber insurance signal collection"""

    priority_urls: List[str] = field(
        default_factory=lambda: [
            "/blog",
            "/news",
            "/security",
            "/press",
            "/careers",
            "/team",
            "/about",
        ]
    )

    document_types: List[str] = field(
        default_factory=lambda: [
            "security policy",
            "privacy policy",
            "incident report",
            "security update",
            "press release",
        ]
    )

    keywords: List[str] = field(
        default_factory=lambda: [
            # Security incidents
            "breach",
            "incident",
            "security",
            "cyber attack",
            "ransomware",
            "data leak",
            "vulnerability",
            "patch",
            # IT hires
            "chief information security officer",
            "ciso",
            "chief technology officer",
            "cto",
            "head of security",
            "security engineer",
            "it director",
            # Security improvements
            "iso 27001",
            "soc 2",
            "penetration test",
            "security audit",
            "encryption",
            "multi-factor authentication",
            "mfa",
        ]
    )

    # Cyber-specific: Look for blog posts in last 12 months
    time_window_months: int = 12

    # Categories to track
    incident_keywords: List[str] = field(
        default_factory=lambda: [
            "breach",
            "incident",
            "attack",
            "ransomware",
            "compromise",
        ]
    )

    hire_keywords: List[str] = field(
        default_factory=lambda: [
            "appointed",
            "hired",
            "joins",
            "welcome",
            "new ciso",
            "new cto",
        ]
    )

    certification_keywords: List[str] = field(
        default_factory=lambda: [
            "iso 27001",
            "soc 2",
            "certified",
            "certification",
            "accredited",
        ]
    )


@dataclass
class FinancialConfig(CollectionConfig):
    """Configuration for financial institutions signal collection"""

    priority_urls: List[str] = field(
        default_factory=lambda: [
            "/investor",
            "/investors",
            "/annual-report",
            "/reports",
            "/governance",
            "/esg",
            "/sustainability",
            "/press",
            "/news",
        ]
    )

    document_types: List[str] = field(
        default_factory=lambda: [
            "annual report",
            "integrated report",
            "sustainability report",
            "esg report",
            "governance report",
            "financial statements",
            "proxy statement",
        ]
    )

    keywords: List[str] = field(
        default_factory=lambda: [
            # Financial metrics
            "total assets",
            "assets under management",
            "aum",
            "revenue",
            "net income",
            "return on equity",
            "roe",
            # Governance
            "board of directors",
            "independent directors",
            "audit committee",
            "risk committee",
            "compliance",
            # Regulatory
            "regulatory capital",
            "tier 1 capital",
            "capital ratio",
            "stress test",
            "regulatory examination",
            # ESG
            "esg score",
            "sustainability",
            "carbon emissions",
            "diversity",
        ]
    )

    # Financial: Look for annual reports (typically published yearly)
    time_window_months: int = 24

    # Key metrics to extract
    required_metrics: List[str] = field(
        default_factory=lambda: [
            "total_assets",
            "revenue",
            "capital_ratio",
            "independent_directors_pct",
        ]
    )


@dataclass
class EnergyConfig(CollectionConfig):
    """Configuration for energy sector signal collection"""

    priority_urls: List[str] = field(
        default_factory=lambda: [
            "/safety",
            "/sustainability",
            "/esg",
            "/operations",
            "/news",
            "/press",
            "/investor",
            "/responsibility",
        ]
    )

    document_types: List[str] = field(
        default_factory=lambda: [
            "sustainability report",
            "safety report",
            "incident report",
            "esg report",
            "annual report",
        ]
    )

    keywords: List[str] = field(
        default_factory=lambda: [
            # Safety
            "safety record",
            "incident rate",
            "lost time injury",
            "lti",
            "safety performance",
            "zero harm",
            # Environmental
            "emissions",
            "carbon footprint",
            "environmental compliance",
            "spill",
            "environmental incident",
            # Operational
            "production",
            "capacity",
            "reserves",
            "uptime",
            "reliability",
            # ESG
            "esg rating",
            "sustainability",
            "climate risk",
        ]
    )

    # Energy: Look for safety/incident reports
    time_window_months: int = 24

    # Incident tracking
    incident_types: List[str] = field(
        default_factory=lambda: [
            "oil spill",
            "gas leak",
            "explosion",
            "fire",
            "safety incident",
            "environmental violation",
        ]
    )


def get_config_for_model(model_type: str) -> CollectionConfig:
    """
    Get collection configuration for a specific pricing model.

    Args:
        model_type: Type of pricing model (cyber, energy, financial)

    Returns:
        Appropriate configuration object
    """
    configs = {
        "cyber": CyberConfig(),
        "energy": EnergyConfig(),
        "financial": FinancialConfig(),
        "financial_institutions": FinancialConfig(),
    }

    return configs.get(model_type.lower(), CollectionConfig())
