"""
DSI Aggregators

Aggregators transform raw extractor data into normalized structures
optimized for scoring/categorization.

Implementation Status: PRODUCTION READY
    Aggregators must handle real data when extractors are upgraded.
    They gracefully handle missing/malformed data.

Classes:
    ProductionAggregator: Base class with normalization utilities

Usage:
    from signals.aggregators import ProductionAggregator
    
    class MyAggregator(ProductionAggregator):
        def aggregate(self, results: List[ExtractorResult]) -> AggregatorResult:
            raw = self._get_primary_data(results)
            normalized = {
                "count": self._normalize_int(raw.get("count")),
                "is_active": self._normalize_bool(raw.get("status") == "ACTIVE"),
            }
            return self._create_success_result(normalized)
"""

from .base import ProductionAggregator

__all__ = [
    "ProductionAggregator",
]
