"""
Signal Collection Module for Digital Signal Intelligence
Extracts and analyzes corporate website content for insurance pricing
"""

from .collectors import (
    CollectionResult,
    CyberSignalCollector,
    EnergySignalCollector,
    FinancialInstitutionSignalCollector,
    SignalCollector,
    SignalMatch,
)
from .config import CollectionConfig, CyberConfig, EnergyConfig, FinancialConfig
from .crawler import CrawledPage, WebsiteCrawler
from .extractors import DocumentExtractor, HTMLArticle, HTMLExtractor, PDFExtractor

__all__ = [
    "SignalCollector",
    "CyberSignalCollector",
    "EnergySignalCollector",
    "FinancialInstitutionSignalCollector",
    "SignalMatch",
    "CollectionResult",
    "WebsiteCrawler",
    "CrawledPage",
    "DocumentExtractor",
    "HTMLExtractor",
    "HTMLArticle",
    "PDFExtractor",
    "CollectionConfig",
    "CyberConfig",
    "EnergyConfig",
    "FinancialConfig",
]
