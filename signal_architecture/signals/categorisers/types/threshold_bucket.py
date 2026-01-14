"""
Threshold Bucket Categorizer

Maps a numeric value to a score based on threshold buckets.
Useful for signals where score depends on falling within certain ranges.

Examples:
    - Fleet age: 0-5 years = 100, 5-10 years = 80, 10-15 years = 60, etc.
    - Incident count: 0 = 100, 1-2 = 75, 3-5 = 50, etc.
    - Years of experience: thresholds for scoring tenure
"""

from typing import Any, Dict, List, Optional

from ..base import ProductionCategorizer
from ...types import CategorizerResult


class ThresholdBucketCategorizer(ProductionCategorizer):
    """
    Maps a numeric value to a score based on threshold buckets.
    
    Params Schema:
        {
            "value_field": str,           # Field in aggregated_data to evaluate
            "buckets": [                  # List of threshold buckets (evaluated in order)
                {
                    "max": float,         # Maximum value for this bucket (inclusive)
                    "score": float        # Score to assign if value <= max
                },
                ...
            ],
            "default_score": float,       # Score if value exceeds all buckets (default: 50)
            "null_score": float,          # Score if value is None (default: 50)
            "null_confidence": float,     # Confidence when value is None (default: 0.0)
            "ascending": bool             # If True, lower values = higher scores (default: True)
        }
    
    Example:
        # Score fleet age (lower is better)
        params = {
            "value_field": "average_fleet_age",
            "buckets": [
                {"max": 5, "score": 100},    # 0-5 years: excellent
                {"max": 10, "score": 80},    # 5-10 years: good
                {"max": 15, "score": 60},    # 10-15 years: average
                {"max": 20, "score": 40},    # 15-20 years: below average
            ],
            "default_score": 20              # >20 years: poor
        }
    """
    
    def categorize(
        self,
        aggregated_data: Dict[str, Any],
        params: Dict[str, Any]
    ) -> CategorizerResult:
        """
        Apply threshold bucket scoring to aggregated data.
        
        Args:
            aggregated_data: Data containing the field to evaluate
            params: Configuration with buckets and field name
        
        Returns:
            CategorizerResult with score based on matching bucket
        """
        # Get parameters
        value_field = self._get_param(params, "value_field", required=True)
        buckets = self._get_param(params, "buckets", required=True)
        default_score = self._get_param(params, "default_score", default=50)
        null_score = self._get_param(params, "null_score", default=50)
        null_confidence = self._get_param(params, "null_confidence", default=0.0)
        
        # Get value from data
        value = self._get_value(aggregated_data, value_field)
        
        # Handle null/missing value
        if value is None:
            return self._create_score_result(
                score=null_score,
                confidence=null_confidence,
                reasoning=f"No value for {value_field}"
            )
        
        # Try to convert to numeric
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            return self._create_error_result(
                f"Cannot convert {value_field} value '{value}' to numeric"
            )
        
        # Find matching bucket
        score = self._threshold_score(numeric_value, buckets, default_score)
        
        # Build reasoning
        reasoning = f"{value_field}={numeric_value} → score={score}"
        
        return self._create_score_result(
            score=score,
            confidence=1.0,
            reasoning=reasoning
        )


class InverseThresholdBucketCategorizer(ProductionCategorizer):
    """
    Maps a numeric value to a score where higher values = LOWER scores.
    
    Useful for metrics where higher is worse (incident count, age, risk factors).
    
    Params Schema:
        Same as ThresholdBucketCategorizer, but buckets define score for
        values GREATER THAN OR EQUAL to the threshold.
        
        {
            "value_field": str,
            "buckets": [
                {
                    "min": float,         # Minimum value for this bucket (inclusive)
                    "score": float        # Score to assign if value >= min
                },
                ...
            ],
            "default_score": float,       # Score if value below all buckets (default: 100)
            "null_score": float,
            "null_confidence": float
        }
    
    Example:
        # Score incident count (higher is worse)
        params = {
            "value_field": "incident_count",
            "buckets": [
                {"min": 10, "score": 0},     # 10+ incidents: terrible
                {"min": 5, "score": 25},     # 5-9 incidents: poor
                {"min": 3, "score": 50},     # 3-4 incidents: below average
                {"min": 1, "score": 75},     # 1-2 incidents: acceptable
            ],
            "default_score": 100             # 0 incidents: excellent
        }
    """
    
    def categorize(
        self,
        aggregated_data: Dict[str, Any],
        params: Dict[str, Any]
    ) -> CategorizerResult:
        """Apply inverse threshold scoring (higher value = lower score)."""
        value_field = self._get_param(params, "value_field", required=True)
        buckets = self._get_param(params, "buckets", required=True)
        default_score = self._get_param(params, "default_score", default=100)
        null_score = self._get_param(params, "null_score", default=50)
        null_confidence = self._get_param(params, "null_confidence", default=0.0)
        
        value = self._get_value(aggregated_data, value_field)
        
        if value is None:
            return self._create_score_result(
                score=null_score,
                confidence=null_confidence,
                reasoning=f"No value for {value_field}"
            )
        
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            return self._create_error_result(
                f"Cannot convert {value_field} value '{value}' to numeric"
            )
        
        # Sort buckets by min value descending (highest first)
        sorted_buckets = sorted(buckets, key=lambda x: x["min"], reverse=True)
        
        # Find first bucket where value >= min
        score = default_score
        for bucket in sorted_buckets:
            if numeric_value >= bucket["min"]:
                score = bucket["score"]
                break
        
        return self._create_score_result(
            score=score,
            confidence=1.0,
            reasoning=f"{value_field}={numeric_value} → score={score}"
        )
