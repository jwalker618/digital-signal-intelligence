"""
DSI Categorizers

Categorizers apply scoring/categorization logic to produce final values.

Implementation Status: PRODUCTION READY
    Categorizer TYPES are reusable across many signals.
    Logic is parameterized via params dict, not hardcoded.

Classes:
    ProductionCategorizer: Base class with scoring utilities

Usage:
    from signals.categorizers import ProductionCategorizer
    
    class ThresholdCategorizer(ProductionCategorizer):
        def categorize(self, data: dict, params: dict) -> CategorizerResult:
            value = self._get_value(data, params["field"])
            score = self._threshold_score(value, params["thresholds"])
            return self._create_score_result(score)
"""

from .base import ProductionCategorizer

__all__ = [
    "ProductionCategorizer",
]
