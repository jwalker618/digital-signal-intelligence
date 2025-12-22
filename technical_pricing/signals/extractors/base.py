"""
extractors/#coverage#.py - Coverage Inference Functions
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from .base import (
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
# CROSS-COVERAGE EXTRACTORS
# =============================================================================

@register_extractor
class CreditRatingExtractor(DataExtractor):
    """
    Credit Rating Data - S&P, Moody's, Fitch ratings.
    
    Signals: credit_rating
    
    Used across: Marine, Aerospace, D&O, FI, Energy
    """
    source_name = "credit_rating"
    coverage = "cross_coverage"
    signals = ["credit_rating"]
    ttl_config = TTLConfig.semi_static("Credit ratings updated weekly")
    
    alternative_sources = [
        DataSource("api", "sp_global", "ratings", priority=1),
        DataSource("api", "moodys", "ratings", priority=1),
        DataSource("api", "fitch", "ratings", priority=2),
        DataSource("api", "kroll", "ratings", priority=3),
    ]

    def extract(self) -> ExtractionResult:
        has_rating = self._rng.random() > 0.40
        
        sp_scale = ["AAA", "AA+", "AA", "AA-", "A+", "A", "A-", "BBB+", "BBB", "BBB-",
                   "BB+", "BB", "BB-", "B+", "B", "B-", "CCC+", "CCC", "CCC-", "CC", "C", "D"]
        moodys_scale = ["Aaa", "Aa1", "Aa2", "Aa3", "A1", "A2", "A3", "Baa1", "Baa2", "Baa3",
                       "Ba1", "Ba2", "Ba3", "B1", "B2", "B3", "Caa1", "Caa2", "Caa3", "Ca", "C"]
        
        rating_idx = self._weighted_choice([
            (self._rng.randint(0, 3), 0.10),   # AAA to AA-
            (self._rng.randint(4, 9), 0.35),   # A+ to BBB-
            (self._rng.randint(10, 15), 0.40), # BB+ to B-
            (self._rng.randint(16, 21), 0.15), # CCC+ to D
        ])
        
        raw_data = {
            "entity_id": self.kwargs.get("entity_id", self._random_id("ENT", 10)),
            "has_rating": has_rating,
            "ratings": {
                "sp": sp_scale[rating_idx] if has_rating else None,
                "moodys": moodys_scale[min(rating_idx, len(moodys_scale) - 1)] if has_rating else None,
                "fitch": sp_scale[rating_idx] if has_rating and self._rng.random() > 0.30 else None,
            },
            "outlook": self._weighted_choice([
                ("Stable", 0.55), ("Positive", 0.15), ("Negative", 0.25), ("Watch Negative", 0.05)
            ]) if has_rating else None,
            "investment_grade": rating_idx <= 9 if has_rating else None,
            "last_action": {
                "date": self._random_date(365, 0) if has_rating else None,
                "type": self._weighted_choice([("Affirmed", 0.60), ("Upgraded", 0.15), ("Downgraded", 0.20), ("New", 0.05)]) if has_rating else None,
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
                "has_rating": has_rating,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )


@register_extractor
class CompanyProfileExtractor(DataExtractor):
    """
    Company Profile Data - Basic company information, D&B data.
    
    Signals: company_type, size_band, geography, industry
    
    Used across all coverages
    """
    source_name = "company_profile"
    coverage = "cross_coverage"
    signals = ["company_type", "size_band", "geography", "industry"]
    ttl_config = TTLConfig.semi_static("Company profile updated weekly")
    
    alternative_sources = [
        DataSource("api", "dnb", "company/profile", priority=1),
        DataSource("api", "pitchbook", "companies/profile", priority=2),
        DataSource("api", "linkedin", "company/about", priority=3),
        DataSource("scrape", "company_website", "/about", priority=4),
    ]

    def extract(self) -> ExtractionResult:
        company_type = self._weighted_choice([
            ("Public", 0.30), ("Private", 0.50), ("PE-Backed", 0.15), ("Non-Profit", 0.05)
        ])
        
        employees = self._weighted_choice([
            (self._rng.randint(10, 50), 0.25),
            (self._rng.randint(50, 250), 0.30),
            (self._rng.randint(250, 1000), 0.25),
            (self._rng.randint(1000, 10000), 0.15),
            (self._rng.randint(10000, 100000), 0.05),
        ])
        
        raw_data = {
            "company_id": self.kwargs.get("company_id", self._random_id("CO", 10)),
            "basic_info": {
                "company_name": self.kwargs.get("company_name", self._random_company_name("Corp")),
                "company_type": company_type,
                "year_founded": self._rng.randint(1900, 2020),
                "employees": employees,
            },
            "size_classification": {
                "size_band": self._classify_size(employees),
                "revenue_band": self._weighted_choice([
                    ("Under $10M", 0.25), ("$10M-$50M", 0.25), ("$50M-$250M", 0.25),
                    ("$250M-$1B", 0.15), ("Over $1B", 0.10)
                ]),
            },
            "geography": {
                "headquarters_country": self._weighted_choice([
                    ("United States", 0.40), ("United Kingdom", 0.10), ("Germany", 0.08),
                    ("Canada", 0.07), ("France", 0.05), ("Other", 0.30)
                ]),
                "headquarters_state": self._rng.choice(["California", "New York", "Texas", "Florida", "Illinois"]),
                "operating_countries": self._rng.randint(1, 50),
            },
            "industry": {
                "primary_sic": str(self._rng.randint(1000, 9999)),
                "primary_naics": str(self._rng.randint(100000, 999999)),
                "industry_description": self._weighted_choice([
                    "Technology", "Healthcare", "Financial Services", "Manufacturing",
                    "Retail", "Energy", "Professional Services", "Transportation"
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
                "company_type": company_type,
                "alternative_sources": [str(s) for s in self.alternative_sources]
            }
        )
    
    def _classify_size(self, employees: int) -> str:
        if employees < 50: return "Small"
        elif employees < 250: return "Medium"
        elif employees < 1000: return "Large"
        else: return "Enterprise"


@register_extractor  
class NewsMediaExtractor(DataExtractor):
    """
    News & Media Monitoring - GDELT, news APIs for reputation signals.
    
    Signals: media_sentiment, news_mentions
    
    Used across all coverages
    """
    source_name = "news_media"
    coverage = "cross_coverage"
    signals = ["media_sentiment", "news_mentions"]
    ttl_config = TTLConfig.dynamic("News monitored continuously")
    
    alternative_sources = [
        DataSource("news", "gdelt", "query", priority=1),
        DataSource("api", "businesswire", "releases/company", priority=2),
        DataSource("api", "prnewswire", "releases/company", priority=3),
    ]

    def extract(self) -> ExtractionResult:
        mentions = self._rng.randint(0, 500)
        
        raw_data = {
            "entity_id": self.kwargs.get("entity_id", self._random_id("ENT", 10)),
            "news_coverage": {
                "mentions_30d": mentions,
                "mentions_90d": mentions * 3,
                "trend": self._weighted_choice([("Increasing", 0.30), ("Stable", 0.50), ("Decreasing", 0.20)]),
            },
            "sentiment": {
                "overall": self._weighted_choice([
                    ("Very Positive", 0.10), ("Positive", 0.30), ("Neutral", 0.40),
                    ("Negative", 0.15), ("Very Negative", 0.05)
                ]),
                "positive_pct": self._rng.randint(20, 60),
                "negative_pct": self._rng.randint(5, 30),
            },
            "key_topics": self._rng.sample([
                "Financial Results", "Product Launch", "Leadership Change",
                "Regulatory", "M&A", "Partnership", "Controversy", "Award"
            ], self._rng.randint(2, 5)),
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

